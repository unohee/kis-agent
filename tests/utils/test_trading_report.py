"""
거래내역 리포트 생성 테스트
==========================

생성일: 2024-08-22
목적: TradingReportGenerator 클래스 테스트
의존성: pytest, pandas, openpyxl
테스트 상태: 완료
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from pykis.account.api import AccountAPI
from pykis.core.client import KISClient
from pykis.utils.trading_report import TradingReportGenerator, generate_trading_report


@pytest.fixture
def mock_client():
    """모의 KIS 클라이언트"""
    return Mock(spec=KISClient)


@pytest.fixture
def account_info():
    """테스트용 계좌 정보"""
    return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


@pytest.fixture
def sample_trading_data():
    """샘플 거래 데이터"""
    return pd.DataFrame(
        {
            "ord_dt": ["20250120", "20250119", "20250118"],
            "ord_tmd": ["093000", "143000", "103000"],
            "pdno": ["005930", "000660", "005930"],
            "prdt_name": ["삼성전자", "SK하이닉스", "삼성전자"],
            "sll_buy_dvsn_cd_name": ["현금매수", "현금매도", "현금매수"],
            "ord_qty": ["10", "5", "20"],
            "ord_unpr": ["75000", "150000", "74000"],
            "tot_ccld_qty": ["10", "5", "20"],
            "avg_prvs": ["75000", "150000", "74000"],
            "ccld_amt": ["750000", "750000", "1480000"],
            "rt_cd": "0",
            "msg_cd": "APBK0013",
            "msg1": "정상처리되었습니다",
        }
    )


@pytest.fixture
def generator(mock_client, account_info):
    """TradingReportGenerator 인스턴스"""
    return TradingReportGenerator(mock_client, account_info)


class TestTradingReportGenerator:
    """TradingReportGenerator 테스트"""

    def test_init(self, generator, mock_client, account_info):
        """초기화 테스트"""
        assert generator.client == mock_client
        assert generator.account_info == account_info
        assert isinstance(generator.account_api, AccountAPI)

    def test_get_trading_history_success(self, generator, sample_trading_data):
        """거래내역 조회 성공 테스트"""
        # AccountAPI.inquire_daily_ccld 모킹
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.return_value = sample_trading_data

            # 전체 거래내역 조회
            df = generator.get_trading_history("20250101", "20250131")

            assert not df.empty
            assert len(df) == 3
            mock_inquire.assert_called_once_with(
                start_date="20250101", end_date="20250131", pdno=""
            )

    def test_get_trading_history_with_ticker(self, generator, sample_trading_data):
        """특정 종목 거래내역 조회 테스트"""
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            # 삼성전자만 필터링
            samsung_data = sample_trading_data[sample_trading_data["pdno"] == "005930"]
            mock_inquire.return_value = samsung_data

            df = generator.get_trading_history("20250101", "20250131", ticker="005930")

            assert not df.empty
            assert all(df["pdno"] == "005930")
            mock_inquire.assert_called_with(
                start_date="20250101", end_date="20250131", pdno="005930"
            )

    def test_get_trading_history_only_executed(self, generator, sample_trading_data):
        """체결된 거래만 필터링 테스트"""
        # 미체결 거래 추가
        data_with_unexecuted = sample_trading_data.copy()
        data_with_unexecuted.loc[len(data_with_unexecuted)] = {
            "ord_dt": "20250117",
            "ord_tmd": "093000",
            "pdno": "035720",
            "prdt_name": "카카오",
            "sll_buy_dvsn_cd_name": "현금매수",
            "ord_qty": "10",
            "ord_unpr": "50000",
            "tot_ccld_qty": "0",  # 미체결
            "avg_prvs": "0",
            "ccld_amt": "0",
            "rt_cd": "0",
            "msg_cd": "APBK0013",
            "msg1": "정상처리되었습니다",
        }

        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.return_value = data_with_unexecuted

            # 체결된 거래만
            df = generator.get_trading_history(
                "20250101", "20250131", only_executed=True
            )

            assert len(df) == 3  # 미체결 제외
            assert all(pd.to_numeric(df["tot_ccld_qty"]) > 0)

    def test_get_trading_history_empty(self, generator):
        """빈 거래내역 처리 테스트"""
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.return_value = pd.DataFrame()

            df = generator.get_trading_history("20250101", "20250131")

            assert df.empty

    def test_export_to_excel_basic(self, generator, sample_trading_data):
        """기본 Excel 내보내기 테스트"""
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.return_value = sample_trading_data

            # 임시 파일로 내보내기
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                output_path = generator.export_to_excel(
                    "20250101", "20250131", output_path=tmp_path
                )

                assert os.path.exists(output_path)
                assert output_path == tmp_path

                # Excel 파일 읽기 테스트
                df = pd.read_excel(output_path, sheet_name="거래내역")
                assert not df.empty
                assert "주문일자" in df.columns
                assert "종목명" in df.columns

            finally:
                # 임시 파일 삭제
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_export_to_excel_with_tickers(self, generator, sample_trading_data):
        """특정 종목 Excel 내보내기 테스트"""
        with patch.object(generator, "get_trading_history") as mock_get:
            # 종목별로 다른 데이터 반환
            def side_effect(start, end, ticker=None, only_executed=True):
                if ticker == "005930":
                    return sample_trading_data[sample_trading_data["pdno"] == "005930"]
                elif ticker == "000660":
                    return sample_trading_data[sample_trading_data["pdno"] == "000660"]
                return pd.DataFrame()

            mock_get.side_effect = side_effect

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                output_path = generator.export_to_excel(
                    "20250101",
                    "20250131",
                    output_path=tmp_path,
                    tickers=["005930", "000660"],
                )

                assert os.path.exists(output_path)

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_export_to_excel_separate_sheets(self, generator, sample_trading_data):
        """종목별 시트 분리 테스트"""
        with patch.object(generator, "get_trading_history") as mock_get:

            def side_effect(start, end, ticker=None, only_executed=True):
                if ticker:
                    return sample_trading_data[sample_trading_data["pdno"] == ticker]
                return sample_trading_data

            mock_get.side_effect = side_effect

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                output_path = generator.export_to_excel(
                    "20250101",
                    "20250131",
                    output_path=tmp_path,
                    tickers=["005930", "000660"],
                    separate_sheets=True,
                )

                assert os.path.exists(output_path)

                # 시트 확인
                xl_file = pd.ExcelFile(output_path)
                sheet_names = xl_file.sheet_names

                # 종목별 시트와 요약 시트가 있어야 함
                assert "요약" in sheet_names
                assert any("005930" in name for name in sheet_names)
                assert any("000660" in name for name in sheet_names)

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_export_to_excel_auto_filename(self, generator, sample_trading_data):
        """자동 파일명 생성 테스트"""
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.return_value = sample_trading_data

            output_path = generator.export_to_excel(
                "20250101",
                "20250131",
                output_path=None,  # 자동 생성
            )

            try:
                assert output_path is not None
                assert "trading_history" in output_path
                assert "20250101" in output_path
                assert "20250131" in output_path
                assert output_path.endswith(".xlsx")

            finally:
                # 생성된 파일 삭제
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_export_to_excel_error_handling(self, generator):
        """Excel 내보내기 오류 처리 테스트"""
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.side_effect = Exception("API 오류")

            # 오류가 발생해도 빈 DataFrame을 반환하고 정상 처리됨
            output_path = "test.xlsx"
            try:
                result = generator.export_to_excel(
                    "20250101", "20250131", output_path=output_path
                )
                # 빈 데이터로 파일이 생성되어야 함
                assert result == output_path
                assert os.path.exists(output_path)
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_export_to_excel_writer_exception(self, generator, sample_trading_data):
        """Excel 파일 생성 중 예외 발생 테스트"""
        with patch.object(generator.account_api, "inquire_daily_ccld") as mock_inquire:
            mock_inquire.return_value = sample_trading_data

        # ExcelWriter 생성 시 오류 발생 시뮬레이션
        with patch("pandas.ExcelWriter") as mock_writer:
            mock_writer.side_effect = Exception("파일 쓰기 오류")

            with pytest.raises(Exception) as exc_info:
                generator.export_to_excel(
                    "20250101", "20250131", output_path="/invalid/path/test.xlsx"
                )

            assert "파일 쓰기 오류" in str(exc_info.value)


class TestGenerateTradingReport:
    """generate_trading_report 함수 테스트"""

    def test_generate_trading_report_function(
        self, mock_client, account_info, sample_trading_data
    ):
        """간편 함수 테스트"""
        with patch("pykis.utils.trading_report.AccountAPI") as MockAccountAPI:
            mock_api = MockAccountAPI.return_value
            mock_api.inquire_daily_ccld.return_value = sample_trading_data

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                output_path = generate_trading_report(
                    client=mock_client,
                    account_info=account_info,
                    start_date="20250101",
                    end_date="20250131",
                    output_path=tmp_path,
                    only_executed=True,
                )

                assert output_path == tmp_path
                assert os.path.exists(output_path)

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_generate_trading_report_with_options(
        self, mock_client, account_info, sample_trading_data
    ):
        """다양한 옵션으로 간편 함수 테스트"""
        with patch("pykis.utils.trading_report.AccountAPI") as MockAccountAPI:
            mock_api = MockAccountAPI.return_value
            mock_api.inquire_daily_ccld.return_value = sample_trading_data

            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                output_path = generate_trading_report(
                    client=mock_client,
                    account_info=account_info,
                    start_date="20250101",
                    end_date="20250131",
                    output_path=tmp_path,
                    tickers=["005930", "000660"],
                    only_executed=True,
                    separate_sheets=True,
                )

                assert output_path == tmp_path

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
