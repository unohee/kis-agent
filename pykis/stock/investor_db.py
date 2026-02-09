"""
investor_db.py - 투자자 포지션 데이터 저장소

이 모듈은 투자자별 매매 데이터의 영구 저장 및 조회를 담당합니다:
- SQLite 기반 일별 포지션 데이터 저장
- 30일 이동 윈도우 효율적 조회
- 데이터 무결성 검증
- 자동 백업 및 복구

 의존:
- sqlite3: 데이터베이스 엔진
- datetime: 날짜 계산
- logging: 로깅

 연관 모듈:
- investor.py: 투자자 포지션 분석기
- core/config: 설정 관리

 사용 예시:
db = InvestorPositionDB()
db.save_daily_position(position_data)
positions = db.get_30day_positions("005930")
"""

import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class InvestorPositionRecord:
    """투자자 포지션 레코드"""

    stock_code: str
    date: str  # YYYYMMDD
    foreign_buy_vol: int = 0
    foreign_sell_vol: int = 0
    foreign_net_vol: int = 0
    foreign_buy_amt: int = 0
    foreign_sell_amt: int = 0
    foreign_net_amt: int = 0
    institution_buy_vol: int = 0
    institution_sell_vol: int = 0
    institution_net_vol: int = 0
    institution_buy_amt: int = 0
    institution_sell_amt: int = 0
    institution_net_amt: int = 0
    individual_buy_vol: int = 0
    individual_sell_vol: int = 0
    individual_net_vol: int = 0
    individual_buy_amt: int = 0
    individual_sell_amt: int = 0
    individual_net_amt: int = 0
    current_price: int = 0
    trading_volume: int = 0
    updated_at: str = ""


class InvestorPositionDB:
    """투자자 포지션 데이터베이스 관리"""

    def __init__(self, db_path: str = None):
        """
        데이터베이스 초기화

        Args:
            db_path: 데이터베이스 파일 경로 (기본값: STONKS/db/investor_positions.db)
        """
        if db_path is None:
            base_dir = "/home/unohee/STONKS"
            db_dir = os.path.join(base_dir, "db")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "investor_positions.db")

        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._initialize_database()

    def _initialize_database(self):
        """데이터베이스 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 투자자 포지션 테이블 생성
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS investor_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    foreign_buy_vol INTEGER DEFAULT 0,
                    foreign_sell_vol INTEGER DEFAULT 0,
                    foreign_net_vol INTEGER DEFAULT 0,
                    foreign_buy_amt INTEGER DEFAULT 0,
                    foreign_sell_amt INTEGER DEFAULT 0,
                    foreign_net_amt INTEGER DEFAULT 0,
                    institution_buy_vol INTEGER DEFAULT 0,
                    institution_sell_vol INTEGER DEFAULT 0,
                    institution_net_vol INTEGER DEFAULT 0,
                    institution_buy_amt INTEGER DEFAULT 0,
                    institution_sell_amt INTEGER DEFAULT 0,
                    institution_net_amt INTEGER DEFAULT 0,
                    individual_buy_vol INTEGER DEFAULT 0,
                    individual_sell_vol INTEGER DEFAULT 0,
                    individual_net_vol INTEGER DEFAULT 0,
                    individual_buy_amt INTEGER DEFAULT 0,
                    individual_sell_amt INTEGER DEFAULT 0,
                    individual_net_amt INTEGER DEFAULT 0,
                    current_price INTEGER DEFAULT 0,
                    trading_volume INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, date)
                )
                """
                )

                # 인덱스 생성
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_stock_date ON investor_positions(stock_code, date)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_date ON investor_positions(date)"
                )

                # 시장 전체 동향 테이블 생성
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS market_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    market_type TEXT NOT NULL,  -- 'KOSPI', 'KOSDAQ'
                    foreign_net_amt INTEGER DEFAULT 0,
                    institution_net_amt INTEGER DEFAULT 0,
                    individual_net_amt INTEGER DEFAULT 0,
                    total_trading_value INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, market_type)
                )
                """
                )

                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_market_date ON market_trends(date, market_type)"
                )

                conn.commit()
                self.logger.info(
                    f"투자자 포지션 데이터베이스 초기화 완료: {self.db_path}"
                )

        except sqlite3.Error as e:
            self.logger.error(f"데이터베이스 초기화 실패: {e}")
            raise

    def save_daily_position(self, record: InvestorPositionRecord) -> bool:
        """일별 포지션 데이터 저장"""
        try:
            # 현재 시간 설정
            if not record.updated_at:
                record.updated_at = datetime.now().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # UPSERT 구문 사용 (INSERT OR REPLACE)
                cursor.execute(
                    """
                INSERT OR REPLACE INTO investor_positions (
                    stock_code, date,
                    foreign_buy_vol, foreign_sell_vol, foreign_net_vol,
                    foreign_buy_amt, foreign_sell_amt, foreign_net_amt,
                    institution_buy_vol, institution_sell_vol, institution_net_vol,
                    institution_buy_amt, institution_sell_amt, institution_net_amt,
                    individual_buy_vol, individual_sell_vol, individual_net_vol,
                    individual_buy_amt, individual_sell_amt, individual_net_amt,
                    current_price, trading_volume, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                    (
                        record.stock_code,
                        record.date,
                        record.foreign_buy_vol,
                        record.foreign_sell_vol,
                        record.foreign_net_vol,
                        record.foreign_buy_amt,
                        record.foreign_sell_amt,
                        record.foreign_net_amt,
                        record.institution_buy_vol,
                        record.institution_sell_vol,
                        record.institution_net_vol,
                        record.institution_buy_amt,
                        record.institution_sell_amt,
                        record.institution_net_amt,
                        record.individual_buy_vol,
                        record.individual_sell_vol,
                        record.individual_net_vol,
                        record.individual_buy_amt,
                        record.individual_sell_amt,
                        record.individual_net_amt,
                        record.current_price,
                        record.trading_volume,
                        record.updated_at,
                    ),
                )

                conn.commit()
                self.logger.debug(
                    f"포지션 데이터 저장 완료: {record.stock_code} ({record.date})"
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(
                f"포지션 데이터 저장 실패 ({record.stock_code}, {record.date}): {e}"
            )
            return False

    def get_30day_positions(
        self, stock_code: str, end_date: str = None
    ) -> List[InvestorPositionRecord]:
        """30일간 포지션 데이터 조회"""
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")

            # 30일 전 날짜 계산
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            start_dt = end_dt - timedelta(days=45)  # 주말 고려해서 45일 전부터
            start_date = start_dt.strftime("%Y%m%d")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                SELECT * FROM investor_positions
                WHERE stock_code = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
                LIMIT 30
                """,
                    (stock_code, start_date, end_date),
                )

                rows = cursor.fetchall()

                # 결과를 InvestorPositionRecord 객체로 변환
                records = []
                for row in rows:
                    record = InvestorPositionRecord(
                        stock_code=row[1],
                        date=row[2],
                        foreign_buy_vol=row[3],
                        foreign_sell_vol=row[4],
                        foreign_net_vol=row[5],
                        foreign_buy_amt=row[6],
                        foreign_sell_amt=row[7],
                        foreign_net_amt=row[8],
                        institution_buy_vol=row[9],
                        institution_sell_vol=row[10],
                        institution_net_vol=row[11],
                        institution_buy_amt=row[12],
                        institution_sell_amt=row[13],
                        institution_net_amt=row[14],
                        individual_buy_vol=row[15],
                        individual_sell_vol=row[16],
                        individual_net_vol=row[17],
                        individual_buy_amt=row[18],
                        individual_sell_amt=row[19],
                        individual_net_amt=row[20],
                        current_price=row[21],
                        trading_volume=row[22],
                        updated_at=row[23],
                    )
                    records.append(record)

                self.logger.debug(
                    f"30일 포지션 데이터 조회 완료: {stock_code} ({len(records)}건)"
                )
                return records

        except (sqlite3.Error, ValueError) as e:
            self.logger.error(f"30일 포지션 데이터 조회 실패 ({stock_code}): {e}")
            return []

    def get_position_by_date(
        self, stock_code: str, date: str
    ) -> Optional[InvestorPositionRecord]:
        """특정 날짜 포지션 데이터 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                SELECT * FROM investor_positions
                WHERE stock_code = ? AND date = ?
                """,
                    (stock_code, date),
                )

                row = cursor.fetchone()

                if row:
                    record = InvestorPositionRecord(
                        stock_code=row[1],
                        date=row[2],
                        foreign_buy_vol=row[3],
                        foreign_sell_vol=row[4],
                        foreign_net_vol=row[5],
                        foreign_buy_amt=row[6],
                        foreign_sell_amt=row[7],
                        foreign_net_amt=row[8],
                        institution_buy_vol=row[9],
                        institution_sell_vol=row[10],
                        institution_net_vol=row[11],
                        institution_buy_amt=row[12],
                        institution_sell_amt=row[13],
                        institution_net_amt=row[14],
                        individual_buy_vol=row[15],
                        individual_sell_vol=row[16],
                        individual_net_vol=row[17],
                        individual_buy_amt=row[18],
                        individual_sell_amt=row[19],
                        individual_net_amt=row[20],
                        current_price=row[21],
                        trading_volume=row[22],
                        updated_at=row[23],
                    )
                    return record

                return None

        except sqlite3.Error as e:
            self.logger.error(f"특정 날짜 포지션 조회 실패 ({stock_code}, {date}): {e}")
            return None

    def save_market_trend(
        self, date: str, market_type: str, trend_data: Dict[str, Any]
    ) -> bool:
        """시장 전체 동향 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                INSERT OR REPLACE INTO market_trends (
                    date, market_type,
                    foreign_net_amt, institution_net_amt, individual_net_amt,
                    total_trading_value, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        date,
                        market_type,
                        trend_data.get("foreign_net_amt", 0),
                        trend_data.get("institution_net_amt", 0),
                        trend_data.get("individual_net_amt", 0),
                        trend_data.get("total_trading_value", 0),
                        datetime.now().isoformat(),
                    ),
                )

                conn.commit()
                self.logger.debug(f"시장 동향 저장 완료: {market_type} ({date})")
                return True

        except sqlite3.Error as e:
            self.logger.error(f"시장 동향 저장 실패 ({market_type}, {date}): {e}")
            return False

    def get_market_summary(self, date: str) -> Dict[str, Any]:
        """특정 날짜 시장 동향 요약"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # KOSPI + KOSDAQ 동향 조회
                cursor.execute(
                    """
                SELECT market_type, foreign_net_amt, institution_net_amt,
                       individual_net_amt, total_trading_value
                FROM market_trends
                WHERE date = ?
                """,
                    (date,),
                )

                rows = cursor.fetchall()

                summary = {
                    "date": date,
                    "kospi": {},
                    "kosdaq": {},
                    "total": {
                        "foreign_net_amt": 0,
                        "institution_net_amt": 0,
                        "individual_net_amt": 0,
                        "total_trading_value": 0,
                    },
                }

                for row in rows:
                    market_type = row[0].lower()
                    market_data = {
                        "foreign_net_amt": row[1],
                        "institution_net_amt": row[2],
                        "individual_net_amt": row[3],
                        "total_trading_value": row[4],
                    }

                    summary[market_type] = market_data

                    # 전체 합계 계산
                    for key in [
                        "foreign_net_amt",
                        "institution_net_amt",
                        "individual_net_amt",
                        "total_trading_value",
                    ]:
                        summary["total"][key] += market_data[key]

                return summary

        except sqlite3.Error as e:
            self.logger.error(f"시장 요약 조회 실패 ({date}): {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """오래된 데이터 정리 (기본 90일 보관)"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime(
                "%Y%m%d"
            )

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 오래된 포지션 데이터 삭제
                cursor.execute(
                    "DELETE FROM investor_positions WHERE date < ?", (cutoff_date,)
                )
                position_deleted = cursor.rowcount

                # 오래된 시장 동향 데이터 삭제
                cursor.execute(
                    "DELETE FROM market_trends WHERE date < ?", (cutoff_date,)
                )
                trend_deleted = cursor.rowcount

                conn.commit()

                self.logger.info(
                    f"오래된 데이터 정리 완료: 포지션 {position_deleted}건, 시장동향 {trend_deleted}건 삭제"
                )
                return True

        except sqlite3.Error as e:
            self.logger.error(f"데이터 정리 실패: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 정보"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 포지션 데이터 통계
                cursor.execute("SELECT COUNT(*) FROM investor_positions")
                position_count = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(DISTINCT stock_code) FROM investor_positions"
                )
                unique_stocks = cursor.fetchone()[0]

                cursor.execute("SELECT MIN(date), MAX(date) FROM investor_positions")
                date_range = cursor.fetchone()

                # 시장 동향 데이터 통계
                cursor.execute("SELECT COUNT(*) FROM market_trends")
                trend_count = cursor.fetchone()[0]

                # 파일 크기
                file_size = (
                    os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                )

                stats = {
                    "db_path": self.db_path,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "position_records": position_count,
                    "unique_stocks": unique_stocks,
                    "date_range": {
                        "start": date_range[0] if date_range[0] else None,
                        "end": date_range[1] if date_range[1] else None,
                    },
                    "market_trend_records": trend_count,
                }

                return stats

        except (sqlite3.Error, OSError) as e:
            self.logger.error(f"데이터베이스 통계 조회 실패: {e}")
            return {}

    def export_data(
        self, stock_code: str = None, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        """데이터 내보내기 (JSON 형태)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 조건에 따른 쿼리 생성
                conditions = []
                params = []

                if stock_code:
                    conditions.append("stock_code = ?")
                    params.append(stock_code)

                if start_date:
                    conditions.append("date >= ?")
                    params.append(start_date)

                if end_date:
                    conditions.append("date <= ?")
                    params.append(end_date)

                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

                query = f"""
                SELECT * FROM investor_positions
                {where_clause}
                ORDER BY stock_code, date
                """

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # 컬럼명 가져오기
                columns = [description[0] for description in cursor.description]

                # 딕셔너리 형태로 변환
                data = []
                for row in rows:
                    record = dict(zip(columns, row))
                    data.append(record)

                self.logger.info(f"데이터 내보내기 완료: {len(data)}건")
                return data

        except sqlite3.Error as e:
            self.logger.error(f"데이터 내보내기 실패: {e}")
            return []

    def backup_database(self, backup_path: str = None) -> bool:
        """데이터베이스 백업"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.db_path}.backup_{timestamp}"

            import shutil

            shutil.copy2(self.db_path, backup_path)

            self.logger.info(f"데이터베이스 백업 완료: {backup_path}")
            return True

        except (OSError, shutil.Error) as e:
            self.logger.error(f"데이터베이스 백업 실패: {e}")
            return False
