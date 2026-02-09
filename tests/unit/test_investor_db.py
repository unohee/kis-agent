"""
투자자 데이터베이스 모듈 테스트
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from kis_agent.stock.investor_db import InvestorPositionDB, InvestorPositionRecord


class TestInvestorPositionRecord:
    """InvestorPositionRecord 데이터클래스 테스트"""

    def test_record_creation_with_defaults(self):
        """기본값으로 레코드 생성"""
        record = InvestorPositionRecord(stock_code="005930", date="20250127")

        assert record.stock_code == "005930"
        assert record.date == "20250127"
        assert record.foreign_buy_vol == 0
        assert record.institution_net_amt == 0
        assert record.individual_buy_vol == 0

    def test_record_creation_with_values(self):
        """값을 지정하여 레코드 생성"""
        record = InvestorPositionRecord(
            stock_code="000660",
            date="20250127",
            foreign_buy_vol=1000,
            foreign_sell_vol=800,
            foreign_net_vol=200,
        )

        assert record.stock_code == "000660"
        assert record.foreign_buy_vol == 1000
        assert record.foreign_sell_vol == 800
        assert record.foreign_net_vol == 200


class TestInvestorPositionDB:
    """InvestorPositionDB 테스트"""

    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스 픽스처"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = InvestorPositionDB(db_path)
        yield db

        # 정리
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_db_initialization(self, temp_db):
        """데이터베이스 초기화 테스트"""
        assert os.path.exists(temp_db.db_path)

        # 테이블 존재 확인
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

        assert "investor_positions" in tables
        assert "market_trends" in tables

    def test_save_daily_position_success(self, temp_db):
        """일별 포지션 저장 성공"""
        record = InvestorPositionRecord(
            stock_code="005930",
            date="20250127",
            foreign_buy_vol=1000,
            foreign_net_vol=200,
        )

        result = temp_db.save_daily_position(record)
        assert result is True

        # 저장된 데이터 확인
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT stock_code, foreign_buy_vol FROM investor_positions WHERE date = ?",
                ("20250127",),
            )
            row = cursor.fetchone()

        assert row is not None
        assert row[0] == "005930"
        assert row[1] == 1000

    def test_save_daily_position_duplicate(self, temp_db):
        """중복 데이터 저장 시 업데이트"""
        record1 = InvestorPositionRecord(
            stock_code="005930", date="20250127", foreign_buy_vol=1000
        )
        record2 = InvestorPositionRecord(
            stock_code="005930", date="20250127", foreign_buy_vol=1500
        )

        temp_db.save_daily_position(record1)
        temp_db.save_daily_position(record2)

        # 업데이트된 값 확인
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT foreign_buy_vol FROM investor_positions WHERE stock_code = ? AND date = ?",
                ("005930", "20250127"),
            )
            row = cursor.fetchone()

        assert row[0] == 1500

    def test_save_daily_position_error(self, temp_db):
        """데이터베이스 오류 처리"""
        # 데이터베이스 오류 시뮬레이션 (실제 DB 파일 권한 변경으로 오류 발생)
        with patch.object(temp_db, "logger") as mock_logger, patch(
            "sqlite3.connect",
            side_effect=sqlite3.OperationalError("database error"),
        ):
            record = InvestorPositionRecord("005930", "20250127")
            result = temp_db.save_daily_position(record)

            assert result is False
            mock_logger.error.assert_called()

    def test_get_30day_positions_success(self, temp_db):
        """30일 포지션 조회 성공"""
        # 테스트 데이터 삽입
        today = datetime.now()
        for i in range(5):
            date_str = (today - timedelta(days=i)).strftime("%Y%m%d")
            record = InvestorPositionRecord(
                stock_code="005930", date=date_str, foreign_buy_vol=1000 + i * 100
            )
            temp_db.save_daily_position(record)

        # 조회 실행
        results = temp_db.get_30day_positions("005930")

        assert len(results) == 5
        # 결과는 InvestorPositionRecord 객체로 반환됨
        assert results[0].stock_code == "005930"
        assert results[0].foreign_buy_vol >= 1000

    def test_get_30day_positions_no_data(self, temp_db):
        """데이터 없는 경우 빈 리스트 반환"""
        results = temp_db.get_30day_positions("999999")
        assert results == []

    def test_save_market_trends_success(self, temp_db):
        """시장 동향 저장 성공"""
        market_data = {
            "market_type": "KOSPI",
            "date": "20250127",
            "foreign_net_amt": 1000000,
            "institution_net_amt": -500000,
            "individual_net_amt": -500000,
            "total_trading_value": 10000000000,
        }

        result = temp_db.save_market_trend(
            date="20250127", market_type="KOSPI", trend_data=market_data
        )
        assert result is True

        # 저장된 데이터 확인
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT market_type, foreign_net_amt FROM market_trends WHERE date = ?",
                ("20250127",),
            )
            row = cursor.fetchone()

        assert row[0] == "KOSPI"
        assert row[1] == 1000000

    def test_get_market_summary_success(self, temp_db):
        """시장 요약 조회 성공"""
        # 테스트 데이터 삽입
        kospi_data = {
            "market_type": "KOSPI",
            "date": "20250127",
            "foreign_net_amt": 1000000,
            "institution_net_amt": -500000,
            "individual_net_amt": -500000,
            "total_trading_value": 5000000000,
        }
        kosdaq_data = {
            "market_type": "KOSDAQ",
            "date": "20250127",
            "foreign_net_amt": 500000,
            "institution_net_amt": -200000,
            "individual_net_amt": -300000,
            "total_trading_value": 2000000000,
        }

        temp_db.save_market_trend("20250127", "KOSPI", kospi_data)
        temp_db.save_market_trend("20250127", "KOSDAQ", kosdaq_data)

        # Dictionary 형태로 조회
        result_dict = temp_db.get_market_summary("20250127")

        assert result_dict is not None
        assert result_dict["date"] == "20250127"
        assert "kospi" in result_dict
        assert "kosdaq" in result_dict
        assert "total" in result_dict

        # TOTAL 합계 확인
        assert result_dict["total"]["foreign_net_amt"] == 1500000  # 1000000 + 500000
        assert result_dict["total"]["total_trading_value"] == 7000000000  # 5B + 2B

    def test_get_database_stats_success(self, temp_db):
        """데이터베이스 통계 조회 성공"""
        # 테스트 데이터 삽입
        record = InvestorPositionRecord("005930", "20250127")
        temp_db.save_daily_position(record)

        market_data = {
            "market_type": "KOSPI",
            "date": "20250127",
            "foreign_net_amt": 1000000,
        }
        temp_db.save_market_trend("20250127", "KOSPI", market_data)

        # 통계 조회
        stats_dict = temp_db.get_database_stats()

        assert stats_dict is not None
        assert isinstance(stats_dict, dict)

        # 특정 메트릭 확인 (dictionary 형태로 반환)
        assert "position_records" in stats_dict
        assert stats_dict["position_records"] >= 1
        assert "market_trend_records" in stats_dict
        assert stats_dict["market_trend_records"] >= 1

    def test_cleanup_old_data_success(self, temp_db):
        """오래된 데이터 정리 성공"""
        # 최신 데이터와 오래된 데이터 삽입
        recent_date = datetime.now().strftime("%Y%m%d")
        old_date = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")

        recent_record = InvestorPositionRecord("005930", recent_date)
        old_record = InvestorPositionRecord("000660", old_date)

        temp_db.save_daily_position(recent_record)
        temp_db.save_daily_position(old_record)

        # 정리 실행 (30일 보관)
        result = temp_db.cleanup_old_data(days_to_keep=30)
        assert result is True

        # 데이터 확인
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM investor_positions")
            count = cursor.fetchone()[0]

        assert count == 1  # 최신 데이터만 남음

    @patch("os.path.getsize")
    def test_get_database_stats_file_size(self, mock_getsize, temp_db):
        """파일 크기 계산 테스트"""
        mock_getsize.return_value = 1024 * 1024  # 1MB

        stats_dict = temp_db.get_database_stats()

        assert "file_size_mb" in stats_dict
        assert stats_dict["file_size_mb"] == 1.0

    def test_export_data_no_filters(self, temp_db):
        """필터 없이 전체 데이터 내보내기"""
        # 테스트 데이터 삽입
        record = InvestorPositionRecord("005930", "20250127", foreign_buy_vol=1000)
        temp_db.save_daily_position(record)

        # 내보내기 실행
        exported_data = temp_db.export_data()

        assert len(exported_data) == 1
        assert exported_data[0]["stock_code"] == "005930"
        assert exported_data[0]["foreign_buy_vol"] == 1000

    def test_export_data_with_filters(self, temp_db):
        """필터로 특정 데이터만 내보내기"""
        # 여러 테스트 데이터 삽입
        record1 = InvestorPositionRecord("005930", "20250127")
        record2 = InvestorPositionRecord("000660", "20250126")
        record3 = InvestorPositionRecord("005930", "20250125")

        temp_db.save_daily_position(record1)
        temp_db.save_daily_position(record2)
        temp_db.save_daily_position(record3)

        # 특정 종목만 내보내기
        exported_data = temp_db.export_data(stock_code="005930")

        assert len(exported_data) == 2
        for item in exported_data:
            assert item["stock_code"] == "005930"

    def test_database_error_handling(self, temp_db):
        """데이터베이스 오류 처리 테스트"""
        # 잘못된 경로로 새 DB 인스턴스 생성 시뮬레이션
        with patch.object(temp_db, "logger") as mock_logger, patch(
            "sqlite3.connect",
            side_effect=sqlite3.OperationalError("database error"),
        ):
            record = InvestorPositionRecord("005930", "20250127")
            result = temp_db.save_daily_position(record)

            assert result is False
            mock_logger.error.assert_called()
