"""
Futures Historical Data - 선물 과거 데이터 조회 모듈

월물 코드 재구성 + 페이지네이션을 통해 과거 선물 분봉 데이터를 연속 조회합니다.

Features:
- 월물 코드 자동 생성 (날짜 → 근월물 코드)
- 페이지네이션으로 102건씩 연속 조회
- 월물 전환 자동 처리 (만기일 기준)
- 여러 월물 데이터 병합
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS

logger = logging.getLogger(__name__)


class FuturesContractCode:
    """
    KOSPI200 선물 월물 코드 생성기

    종목코드 체계: 101 + 시리즈(1자리) + 만기월(2자리)
    - 시리즈: S(3월), M(6월), U(9월), Z(12월)
    - 만기월: 03, 06, 09, 12

    예: 101S03 = KOSPI200 3월물

    만기일: 각 분기 두 번째 목요일
    """

    # 시리즈 코드 매핑 (FuturesCodeGenerator와 동일)
    SERIES_MAP = {3: "S", 6: "M", 9: "U", 12: "Z"}
    # 역매핑
    SERIES_TO_MONTH = {"S": 3, "M": 6, "U": 9, "Z": 12}
    # 정기물 월 리스트
    CONTRACT_MONTHS = [3, 6, 9, 12]

    @classmethod
    def get_series_code(cls, month: int) -> str:
        """만기월을 시리즈 코드로 변환"""
        if month not in cls.SERIES_MAP:
            raise ValueError(f"Invalid contract month: {month}. Must be 3, 6, 9, or 12")
        return cls.SERIES_MAP[month]

    @classmethod
    def get_expiry_date(cls, year: int, month: int) -> datetime:
        """
        해당 월물의 만기일 계산 (두 번째 목요일)

        Args:
            year: 연도
            month: 월 (3, 6, 9, 12)

        Returns:
            만기일 datetime
        """
        # 해당 월 1일
        first_day = datetime(year, month, 1)
        # 첫 번째 목요일 찾기 (weekday: 0=월, 3=목)
        days_until_thursday = (3 - first_day.weekday()) % 7
        first_thursday = first_day + timedelta(days=days_until_thursday)
        # 두 번째 목요일
        second_thursday = first_thursday + timedelta(days=7)
        return second_thursday

    @classmethod
    def get_front_month_contract(cls, date: datetime) -> Tuple[int, int]:
        """
        주어진 날짜의 근월물(front month) 계산

        Args:
            date: 조회 기준 날짜

        Returns:
            (year, month) 튜플
        """
        year = date.year
        month = date.month

        # 현재 또는 다음 정기물 월 찾기
        for contract_month in cls.CONTRACT_MONTHS:
            if contract_month >= month:
                # 해당 월물의 만기일 확인
                expiry = cls.get_expiry_date(year, contract_month)
                # 만기일 이전이면 이 월물이 근월물
                if date.date() <= expiry.date():
                    return (year, contract_month)

        # 올해 정기물이 모두 만기되었으면 내년 3월물
        return (year + 1, 3)

    @classmethod
    def generate_code(cls, year: int, month: int) -> str:
        """
        월물 코드 생성

        Args:
            year: 연도 (사용되지 않음 - 호환성 유지)
            month: 월 (3, 6, 9, 12)

        Returns:
            종목코드 (예: "101S03")

        Note:
            한국투자증권 선물 코드는 연도를 포함하지 않습니다.
            같은 시리즈(월)는 항상 같은 코드를 사용합니다.
        """
        if month not in cls.SERIES_MAP:
            raise ValueError(f"Invalid contract month: {month}. Must be 3, 6, 9, or 12")

        series_code = cls.SERIES_MAP[month]
        return f"101{series_code}{month:02d}"

    @classmethod
    def get_code_for_date(cls, date: datetime) -> str:
        """
        주어진 날짜의 근월물 코드 반환

        Args:
            date: 조회 기준 날짜

        Returns:
            종목코드
        """
        year, month = cls.get_front_month_contract(date)
        return cls.generate_code(year, month)

    @classmethod
    def get_previous_contract(cls, year: int, month: int) -> Tuple[int, int]:
        """
        이전 월물 계산

        Args:
            year: 현재 월물 연도
            month: 현재 월물 월

        Returns:
            (year, month) 이전 월물
        """
        idx = cls.CONTRACT_MONTHS.index(month)
        if idx == 0:
            return (year - 1, 12)
        else:
            return (year, cls.CONTRACT_MONTHS[idx - 1])

    @classmethod
    def parse_code(cls, code: str) -> Tuple[int, int]:
        """
        종목코드 파싱

        Args:
            code: 종목코드 (예: "101S03")

        Returns:
            (year, month) 튜플 - year는 현재 연도 기준

        Note:
            한국투자증권 선물 코드는 연도 정보가 없으므로
            현재 연도를 기준으로 반환합니다.
        """
        if len(code) != 6 or not code.startswith("101"):
            raise ValueError(f"Invalid futures code format: {code}")

        series_code = code[3]
        # month_str = code[4:6]  # 형식 검증용 (현재 미사용)

        if series_code not in cls.SERIES_TO_MONTH:
            raise ValueError(f"Invalid series code: {series_code}")

        month = cls.SERIES_TO_MONTH[series_code]
        current_year = datetime.now().year

        return (current_year, month)


class FuturesHistoricalAPI(BaseAPI):
    """
    선물 과거 분봉 데이터 조회 API

    월물 코드 재구성 + 페이지네이션으로 과거 데이터를 연속 조회합니다.
    """

    def get_minute_bars(
        self,
        start_date: str,
        end_date: str = "",
        interval: str = "1",
        max_bars: int = 1000,
        include_night: bool = True,
    ) -> List[Dict]:
        """
        과거 분봉 데이터 조회 (월물 자동 전환)

        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD, 기본값: 오늘)
            interval: 분봉 간격 (1:1분, 3:3분, 5:5분, 10:10분, 30:30분, 60:60분)
            max_bars: 최대 조회 건수 (기본값: 1000)
            include_night: 야간 데이터 포함 여부

        Returns:
            분봉 데이터 리스트 (시간 오름차순)

        Example:
            >>> api = FuturesHistoricalAPI(client, account_info)
            >>> bars = api.get_minute_bars("20250101", "20250131", interval="60")
            >>> for bar in bars[:5]:
            ...     print(f"{bar['date']} {bar['time']}: {bar['close']}")
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")

        all_bars = []
        current_date = end_dt
        current_time = "153000"  # 장마감 시간부터 역순 조회

        bars_collected = 0

        while current_date >= start_dt and bars_collected < max_bars:
            # 해당 날짜의 근월물 코드
            contract_code = FuturesContractCode.get_code_for_date(current_date)

            logger.info(
                f"조회 중: {contract_code}, 날짜: {current_date.strftime('%Y%m%d')}"
            )

            # 페이지네이션으로 해당 날짜 데이터 조회
            page_bars, next_date, next_time = self._fetch_page(
                code=contract_code,
                date=current_date.strftime("%Y%m%d"),
                hour=current_time,
                interval=interval,
                include_past=True,
            )

            if page_bars:
                # 시작일 이전 데이터 필터링
                filtered_bars = [
                    bar for bar in page_bars if bar.get("date", "") >= start_date
                ]
                all_bars.extend(filtered_bars)
                bars_collected += len(filtered_bars)

                logger.info(f"  {len(filtered_bars)}건 수집 (총 {bars_collected}건)")

                # 다음 페이지로
                if next_date and next_time:
                    current_date = datetime.strptime(next_date, "%Y%m%d")
                    current_time = next_time
                else:
                    # 이전 날짜로
                    current_date -= timedelta(days=1)
                    current_time = "153000"
            else:
                # 데이터 없으면 이전 날짜로
                current_date -= timedelta(days=1)
                current_time = "153000"

            # 주말/공휴일 건너뛰기 (토=5, 일=6)
            while current_date.weekday() >= 5 and current_date >= start_dt:
                current_date -= timedelta(days=1)

        # 시간 오름차순 정렬
        all_bars.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))

        return all_bars[:max_bars]

    def _fetch_page(
        self,
        code: str,
        date: str,
        hour: str,
        interval: str = "1",
        include_past: bool = True,
    ) -> Tuple[List[Dict], Optional[str], Optional[str]]:
        """
        단일 페이지 분봉 데이터 조회

        Args:
            code: 종목코드
            date: 조회일자 (YYYYMMDD)
            hour: 조회시간 (HHMMSS)
            interval: 분봉 간격
            include_past: 과거 데이터 포함 여부

        Returns:
            (데이터 리스트, 다음 조회 날짜, 다음 조회 시간)
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "F",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_HOUR_1": hour,
            "FID_PW_DATA_INCU_YN": "Y" if include_past else "N",
            "FID_TICK_RANGE": interval,
        }

        result = self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_TIME_FUOPCHARTPRICE"],
            tr_id="FHKIF03020200",
            params=params,
            use_cache=False,
        )

        if not result or result.get("rt_cd") != "0":
            logger.warning(f"API 오류: {result.get('msg1') if result else 'None'}")
            return [], None, None

        output2 = result.get("output2", [])
        if not output2:
            return [], None, None

        # 데이터 정규화
        bars = []
        for item in output2:
            bar = {
                "date": item.get("stck_bsop_date", date),
                "time": item.get("stck_cntg_hour", ""),
                "open": item.get("fuop_oprc", ""),
                "high": item.get("fuop_hgpr", ""),
                "low": item.get("fuop_lwpr", ""),
                "close": item.get("fuop_prpr", ""),
                "volume": item.get("cntg_vol", ""),
                "contract": code,
            }
            bars.append(bar)

        # 다음 페이지 정보 (가장 오래된 데이터 기준)
        if bars:
            oldest = bars[-1]
            next_date = oldest.get("date")
            next_time = oldest.get("time")
            # 1분 이전으로 설정
            if next_time:
                try:
                    t = datetime.strptime(f"{next_date}{next_time}", "%Y%m%d%H%M%S")
                    t -= timedelta(minutes=1)
                    next_date = t.strftime("%Y%m%d")
                    next_time = t.strftime("%H%M%S")
                except ValueError:
                    # 날짜 파싱 실패 시 기존 값 유지하고 로깅
                    logger.warning(
                        f"날짜 파싱 실패: {next_date}{next_time}, 기존 값 유지"
                    )
            return bars, next_date, next_time

        return bars, None, None

    def get_contract_history(
        self,
        code: str,
        start_date: str,
        end_date: str = "",
        interval: str = "1",
        max_bars: int = 1000,
    ) -> List[Dict]:
        """
        특정 월물의 분봉 데이터 조회 (단일 월물)

        Args:
            code: 종목코드 (예: "1016C")
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            interval: 분봉 간격
            max_bars: 최대 조회 건수

        Returns:
            분봉 데이터 리스트
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        all_bars = []
        current_date = end_date
        current_time = "153000"

        while len(all_bars) < max_bars:
            bars, next_date, next_time = self._fetch_page(
                code=code,
                date=current_date,
                hour=current_time,
                interval=interval,
                include_past=True,
            )

            if not bars:
                break

            # 시작일 이전 데이터 필터링
            filtered = [b for b in bars if b.get("date", "") >= start_date]
            all_bars.extend(filtered)

            # 시작일 도달하면 종료
            if bars[-1].get("date", "") < start_date:
                break

            if next_date and next_time:
                current_date = next_date
                current_time = next_time
            else:
                break

        all_bars.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))
        return all_bars[:max_bars]


# 편의 함수
def get_futures_code(date: datetime) -> str:
    """주어진 날짜의 KOSPI200 선물 근월물 코드 반환"""
    return FuturesContractCode.get_code_for_date(date)


def generate_futures_code(year: int, month: int) -> str:
    """연도/월로 KOSPI200 선물 종목코드 생성"""
    return FuturesContractCode.generate_code(year, month)
