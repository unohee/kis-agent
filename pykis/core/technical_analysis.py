"""
기술적 분석 모듈

분봉 데이터 수집, 매물대 분석, 지지/저항선 계산 등
기술적 분석 관련 기능을 제공합니다.

Created: 2026-01-03
Purpose: agent.py에서 추출한 기술 분석 로직
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


class TechnicalAnalysisMixin:
    """
    기술적 분석 기능을 제공하는 Mixin 클래스.

    Agent 클래스에서 상속받아 사용합니다.
    - 분봉 데이터 수집 및 캐싱
    - 매물대 분석 (지지/저항선)
    - 피벗 포인트, VWAP 계산
    - DB/CSV 데이터 관리
    """

    # ===== DB/캐시 관리 =====

    def init_minute_db(self, db_path: str = "db/stonks_candles.db") -> bool:
        """분봉 데이터용 DB 및 테이블 생성 (최초 1회)"""
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS minute_data (
                    code TEXT,
                    date TEXT,
                    tm TEXT,
                    stck_cntg_hour TEXT,
                    stck_prpr REAL,
                    stck_oprc REAL,
                    stck_hgpr REAL,
                    stck_lwpr REAL,
                    cntg_vol INTEGER,
                    acml_tr_pbmn REAL,
                    stck_bsop_date TEXT,
                    PRIMARY KEY (code, date, stck_cntg_hour)
                )
            """
            )
            conn.close()
            return True
        except Exception as e:
            logging.error(f"분봉 DB 초기화 실패: {e}")
            return False

    def migrate_minute_csv_to_db(
        self, code: str, db_path: str = "db/stonks_candles.db"
    ) -> bool:
        """기존 csv 분봉 데이터를 DB로 이관 (한 번만)"""
        cache_dir = "cache"
        csv_file_path = os.path.join(cache_dir, f"{code}_minute_data.csv")
        if not os.path.exists(csv_file_path):
            logging.info(f"CSV 파일이 존재하지 않음: {csv_file_path}")
            return True  # 파일이 없는 것은 오류가 아님
        try:
            import pandas as pd  # 지역 import로 로딩 시간 단축

            df = pd.read_csv(csv_file_path)
            if df.empty:
                logging.info(f"CSV 파일이 비어있음: {csv_file_path}")
                return True  # 빈 파일도 오류가 아님
            # code, date 컬럼 추가
            today = datetime.now().strftime("%Y%m%d")
            df["code"] = code
            df["date"] = today
            # DB에 저장
            conn = sqlite3.connect(db_path)
            df.to_sql("minute_data", conn, if_exists="append", index=False)
            conn.close()
            # 이관 완료 후 csv 파일 삭제
            os.remove(csv_file_path)
            logging.info(f"CSV to DB 마이그레이션 완료: {code}")
            return True
        except Exception as e:
            logging.error(f"CSV to DB migration failed: {e}")
            return False

    def _get_last_business_day(self, date_str: str = None) -> str:
        """
        가장 최근 영업일 계산 (휴장일 제외)

        Args:
            date_str (str): 기준 날짜 (YYYYMMDD 형식, 없으면 오늘)

        Returns:
            str: 가장 최근 영업일 (YYYYMMDD 형식)
        """
        current_date = (
            datetime.strptime(date_str, "%Y%m%d") if date_str else datetime.now()
        )

        # 최대 10일까지만 확인 (무한 루프 방지)
        for i in range(10):
            check_date = current_date - timedelta(days=i)
            check_date_str = check_date.strftime("%Y%m%d")

            # 주말 체크
            if check_date.weekday() >= 5:  # 토요일(5), 일요일(6)
                continue

            # 휴장일 체크
            try:
                is_holiday_result = self.is_holiday(check_date_str)
                if is_holiday_result is False:  # 영업일
                    return check_date_str
            except Exception:
                # API 호출 실패 시 주말만 제외하고 반환
                return check_date_str

        # 영업일을 찾지 못했을 경우 오늘 날짜 반환
        return current_date.strftime("%Y%m%d")

    # ===== 분봉 데이터 수집 =====

    def fetch_minute_data(
        self, code: str, date: str | None = None, cache_dir: str = "cache"
    ) -> pd.DataFrame:
        """
        분봉 데이터 수집 (4번 호출 방식으로 효율적 수집)

        Args:
            code (str): 종목코드
            date (str): 날짜 (YYYYMMDD 형식)
                      - None: 당일 또는 가장 최근 영업일 + 전일 분봉
                      - 특정 날짜: 해당 날짜의 분봉만 수집
            cache_dir (str): 캐시 디렉토리

        Returns:
            pandas.DataFrame: 분봉 데이터
        """
        import pandas as pd

        os.makedirs(cache_dir, exist_ok=True)
        now = datetime.now()

        # 날짜 결정 로직
        if date is None:
            # 인자가 없으면 최근 영업일 + 전일 분봉 수집
            today_str = now.strftime("%Y%m%d")
            last_business_day = self._get_last_business_day(today_str)

            # 현재 시간이 장 시작 전이면 전일 데이터만
            market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now < market_open_time:
                target_dates = [last_business_day]
                logging.info(
                    f"[{code}] 장 시작 전: 최근 영업일 분봉 수집 ({last_business_day})"
                )
            else:
                # 장 시작 후면 최근 영업일 + 전일 분봉
                prev_business_day = self._get_last_business_day(
                    (
                        datetime.strptime(last_business_day, "%Y%m%d")
                        - timedelta(days=1)
                    ).strftime("%Y%m%d")
                )
                target_dates = (
                    [last_business_day, prev_business_day]
                    if prev_business_day != last_business_day
                    else [last_business_day]
                )
                logging.info(f"[{code}] 최근 영업일 + 전일 분봉 수집 ({target_dates})")
        else:
            # 특정 날짜 지정
            target_dates = [date]
            logging.info(f"[{code}] 특정 날짜 분봉 수집 ({date})")

        all_data_frames = []

        for target_date in target_dates:
            csv_file_path = os.path.join(
                cache_dir, f"{code}_minute_data_{target_date}.csv"
            )

            # 캐시 확인
            cached_df = self._check_cache(csv_file_path, target_date, now)
            if cached_df is not None:
                logging.info(f"[{code}] 캐시된 분봉 데이터 사용 ({target_date})")
                all_data_frames.append(cached_df)
                continue

            # 새로 수집
            logging.info(f"[{code}] 분봉 데이터 API 수집 시작 ({target_date})")
            result = self.stock_api.get_intraday_price(code, target_date)

            if result and result.get("rt_cd") == "0":
                minute_data = result.get("output2", [])
                if minute_data:
                    df = pd.DataFrame(minute_data)
                    df["code"] = code
                    df["date"] = target_date

                    # 시간 포맷 정규화
                    if "stck_cntg_hour" in df.columns:
                        df["stck_cntg_hour"] = df["stck_cntg_hour"].apply(
                            lambda x: int(target_date + str(x).zfill(6)[-6:])
                        )

                    # CSV 저장
                    df.to_csv(csv_file_path, index=False)
                    logging.info(
                        f"[{code}] 분봉 데이터 수집 완료: {len(df)}건, CSV 저장됨 ({target_date})"
                    )

                    # DB 저장 시도
                    self._save_to_db(df, code, target_date)

                    all_data_frames.append(df)
                else:
                    logging.warning(f"[{code}] 분봉 데이터 없음 ({target_date})")
            else:
                logging.warning(f"[{code}] 분봉 데이터 수집 실패 ({target_date})")

        # 모든 데이터 합치기
        if all_data_frames:
            combined_df = pd.concat(all_data_frames, ignore_index=True)
            # 시간 순서로 정렬 (최신 순)
            if "stck_cntg_hour" in combined_df.columns:
                combined_df = combined_df.sort_values("stck_cntg_hour", ascending=False)
            logging.info(f"[{code}] 전체 분봉 데이터 수집 완료: {len(combined_df)}건")
            return combined_df
        else:
            logging.warning(f"[{code}] 분봉 데이터 수집 실패: 모든 API 응답 없음")
            return pd.DataFrame()

    def _check_cache(
        self, csv_file_path: str, target_date: str, now: datetime
    ) -> pd.DataFrame | None:
        """
        캐시 파일 유효성 확인

        Args:
            csv_file_path (str): 캐시 파일 경로
            target_date (str): 대상 날짜
            now (datetime): 현재 시간

        Returns:
            pd.DataFrame: 유효한 캐시 데이터 또는 None
        """
        import pandas as pd

        if not os.path.exists(csv_file_path):
            return None

        try:
            # 파일 수정 시간 확인
            file_mtime = datetime.fromtimestamp(os.path.getmtime(csv_file_path))

            # 과거 날짜는 캐시 유효
            target_datetime = datetime.strptime(target_date, "%Y%m%d")
            if target_datetime.date() < now.date():
                cached_df = pd.read_csv(csv_file_path)
                if not cached_df.empty:
                    return cached_df

            # 당일 데이터는 시간 기반 갱신
            market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)

            if market_open_time <= now <= market_close_time:
                # 장중: 5분마다 갱신
                refresh_interval = timedelta(minutes=5)
            else:
                # 장외: 30분마다 갱신
                refresh_interval = timedelta(minutes=30)

            if now - file_mtime < refresh_interval:
                cached_df = pd.read_csv(csv_file_path)
                if not cached_df.empty:
                    return cached_df

        except Exception as e:
            logging.warning(f"캐시 파일 로드 실패: {e}")

        return None

    def _save_to_db(self, df: pd.DataFrame, code: str, date: str) -> None:
        """
        DB에 분봉 데이터 저장

        Args:
            df (pd.DataFrame): 분봉 데이터
            code (str): 종목코드
            date (str): 날짜
        """
        try:
            db_path = "db/stonks_candles.db"
            conn = sqlite3.connect(db_path)
            # 기존 해당 날짜 데이터 삭제 후 새로 저장
            conn.execute(
                "DELETE FROM minute_data WHERE code = ? AND date = ?", (code, date)
            )
            df.to_sql("minute_data", conn, if_exists="append", index=False)
            conn.close()
            logging.info(f"[{code}] {date} 분봉 데이터 DB 저장 완료")
        except Exception as e:
            logging.warning(f"DB 저장 실패: {e}")

    # ===== 매물대 분석 =====

    def calculate_support_resistance(
        self, code: str, date: str = None, price_bins: int = 50
    ) -> dict:
        """
        매물대 분석 - 지지선과 저항선 계산

        Args:
            code (str): 종목코드
            date (str): 분석 날짜 (YYYYMMDD, None이면 최근 데이터)
            price_bins (int): 가격대 구간 수 (기본값: 50)

        Returns:
            dict: 매물대 분석 결과
        """
        import pandas as pd

        # 분봉 데이터 가져오기
        df = self.fetch_minute_data(code, date)

        if df.empty:
            logging.warning(f"[{code}] 분봉 데이터가 없어 매물대 계산 불가")
            return {}

        # 숫자형 변환
        numeric_columns = [
            "stck_oprc",
            "stck_hgpr",
            "stck_lwpr",
            "stck_prpr",
            "cntg_vol",
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 기본 통계
        price_min = df["stck_lwpr"].min()
        price_max = df["stck_hgpr"].max()
        price_range = price_max - price_min

        # 1. 가격대별 거래량 분석
        volume_profile = self._calculate_volume_profile(df, price_bins)

        # 2. 피벗 포인트 계산
        pivot_points = self._calculate_pivot_points(df)

        # 3. VWAP 계산
        vwap = self._calculate_vwap(df)

        # 4. 지지/저항선 감지
        support_levels = self._detect_support_levels(df, volume_profile)
        resistance_levels = self._detect_resistance_levels(df, volume_profile)

        # 5. 매물대 강도 계산
        support_strength = self._calculate_level_strength(df, support_levels)
        resistance_strength = self._calculate_level_strength(df, resistance_levels)

        result = {
            "code": code,
            "analysis_date": date or df["date"].iloc[0],
            "price_range": {
                "min": float(price_min),
                "max": float(price_max),
                "range": float(price_range),
            },
            "volume_profile": volume_profile,
            "pivot_points": pivot_points,
            "vwap": float(vwap),
            "support_levels": [
                {"price": float(level), "strength": float(strength)}
                for level, strength in zip(support_levels, support_strength)
            ],
            "resistance_levels": [
                {"price": float(level), "strength": float(strength)}
                for level, strength in zip(resistance_levels, resistance_strength)
            ],
            "current_price": float(df["stck_prpr"].iloc[0]),
            "total_volume": int(df["cntg_vol"].sum()),
            "data_points": len(df),
        }

        logging.info(
            f"[{code}] 매물대 분석 완료: "
            f"지지선 {len(support_levels)}개, 저항선 {len(resistance_levels)}개"
        )
        return result

    def _calculate_volume_profile(self, df: pd.DataFrame, bins: int = 50) -> list:
        """가격대별 거래량 분포 계산"""
        import numpy as np

        price_min = df["stck_lwpr"].min()
        price_max = df["stck_hgpr"].max()

        # 가격대 구간 생성
        price_bins = np.linspace(price_min, price_max, bins + 1)

        # 각 분봉에 대해 가격대별 거래량 분배
        volume_profile = np.zeros(bins)

        for _, row in df.iterrows():
            low, high = row["stck_lwpr"], row["stck_hgpr"]
            volume = row["cntg_vol"]

            # 해당 분봉의 가격 범위에 포함되는 구간들에 거래량 분배
            for i in range(bins):
                bin_low = price_bins[i]
                bin_high = price_bins[i + 1]

                # 겹치는 구간 계산
                overlap_low = max(low, bin_low)
                overlap_high = min(high, bin_high)

                if overlap_low < overlap_high:
                    # 겹치는 비율만큼 거래량 분배
                    overlap_ratio = (
                        (overlap_high - overlap_low) / (high - low) if high > low else 1
                    )
                    volume_profile[i] += volume * overlap_ratio

        # 결과 반환
        return [
            {
                "price": float((price_bins[i] + price_bins[i + 1]) / 2),
                "volume": float(volume_profile[i]),
            }
            for i in range(bins)
        ]

    def _calculate_pivot_points(self, df: pd.DataFrame) -> dict:
        """피벗 포인트 계산"""
        high = df["stck_hgpr"].max()
        low = df["stck_lwpr"].min()
        close = df["stck_prpr"].iloc[0]  # 최근 종가

        # 피벗 포인트 계산
        pivot = (high + low + close) / 3

        # 지지선과 저항선
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return {
            "pivot": float(pivot),
            "resistance": {"r1": float(r1), "r2": float(r2), "r3": float(r3)},
            "support": {"s1": float(s1), "s2": float(s2), "s3": float(s3)},
        }

    def _calculate_vwap(self, df: pd.DataFrame) -> float:
        """거래량 가중 평균 가격 계산"""
        typical_price = (df["stck_hgpr"] + df["stck_lwpr"] + df["stck_prpr"]) / 3
        volume = df["cntg_vol"]

        vwap = (typical_price * volume).sum() / volume.sum()
        return vwap

    def _detect_support_levels(self, df: pd.DataFrame, volume_profile: list) -> list:
        """지지선 감지"""
        import numpy as np

        # 거래량 기준 상위 20% 구간에서 지지선 후보 추출
        volumes = [vp["volume"] for vp in volume_profile]
        volume_threshold = np.percentile(volumes, 80)

        support_candidates = []
        for vp in volume_profile:
            if vp["volume"] >= volume_threshold:
                # 해당 가격대에서 저가 터치 횟수 확인
                touch_count = len(
                    df[df["stck_lwpr"] <= vp["price"] * 1.002]
                )  # 0.2% 오차 허용
                if touch_count >= 2:  # 최소 2회 이상 터치
                    support_candidates.append(vp["price"])

        # 가격 순으로 정렬하여 상위 5개 반환
        return sorted(support_candidates)[:5]

    def _detect_resistance_levels(self, df: pd.DataFrame, volume_profile: list) -> list:
        """저항선 감지"""
        import numpy as np

        # 거래량 기준 상위 20% 구간에서 저항선 후보 추출
        volumes = [vp["volume"] for vp in volume_profile]
        volume_threshold = np.percentile(volumes, 80)

        resistance_candidates = []
        for vp in volume_profile:
            if vp["volume"] >= volume_threshold:
                # 해당 가격대에서 고가 터치 횟수 확인
                touch_count = len(
                    df[df["stck_hgpr"] >= vp["price"] * 0.998]
                )  # 0.2% 오차 허용
                if touch_count >= 2:  # 최소 2회 이상 터치
                    resistance_candidates.append(vp["price"])

        # 가격 순으로 정렬하여 상위 5개 반환
        return sorted(resistance_candidates, reverse=True)[:5]

    def _calculate_level_strength(self, df: pd.DataFrame, levels: list) -> list:
        """매물대 강도 계산"""
        strengths = []

        for level in levels:
            # 해당 가격대 근처(±0.5%) 거래량 합계
            price_range = level * 0.005
            nearby_volume = df[
                (df["stck_lwpr"] <= level + price_range)
                & (df["stck_hgpr"] >= level - price_range)
            ]["cntg_vol"].sum()

            # 터치 횟수 (고가 또는 저가가 해당 가격대 근처)
            touch_count = len(
                df[
                    (
                        (df["stck_hgpr"] >= level - price_range)
                        & (df["stck_hgpr"] <= level + price_range)
                    )
                    | (
                        (df["stck_lwpr"] >= level - price_range)
                        & (df["stck_lwpr"] <= level + price_range)
                    )
                ]
            )

            # 강도 = 거래량 가중치 * 터치 횟수
            strength = nearby_volume * touch_count
            strengths.append(strength)

        # 정규화 (0-100 스케일)
        if strengths:
            max_strength = max(strengths)
            strengths = [
                s / max_strength * 100 if max_strength > 0 else 0 for s in strengths
            ]

        return strengths
