"""
Stock API Improved 모듈 테스트

pykis/stock/api_improved.py의 StockAPI (deprecated/experimental) 테스트
"""

import warnings
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pykis.core.exceptions import APIException, ValidationException


class TestStockAPIImproved:
    """api_improved.StockAPI 테스트 (deprecated 모듈)"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient fixture"""
        client = MagicMock()
        return client

    @pytest.fixture
    def valid_account(self):
        """유효한 계좌 정보"""
        return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    @pytest.fixture
    def stock_api(self, mock_client, valid_account):
        """StockAPI 인스턴스 fixture (DeprecationWarning 무시)"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from pykis.stock.api_improved import StockAPI

            return StockAPI(mock_client, valid_account)

    def test_init_deprecation_warning(self, mock_client, valid_account):
        """초기화 시 DeprecationWarning 발생"""
        from pykis.stock.api_improved import StockAPI

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            StockAPI(mock_client, valid_account)

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_init_with_none_client(self, valid_account):
        """client가 None인 경우 ValidationException"""
        from pykis.stock.api_improved import StockAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationException):
                StockAPI(None, valid_account)

    def test_init_with_none_account(self, mock_client):
        """account가 None인 경우 ValidationException"""
        from pykis.stock.api_improved import StockAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationException):
                StockAPI(mock_client, None)

    def test_init_with_invalid_account_type(self, mock_client):
        """account가 dict가 아닌 경우 ValidationException"""
        from pykis.stock.api_improved import StockAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationException):
                StockAPI(mock_client, "invalid_account")

    def test_init_with_missing_cano(self, mock_client):
        """account에 CANO가 없는 경우 ValidationException"""
        from pykis.stock.api_improved import StockAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationException):
                StockAPI(mock_client, {"ACNT_PRDT_CD": "01"})

    def test_init_with_missing_acnt_prdt_cd(self, mock_client):
        """account에 ACNT_PRDT_CD가 없는 경우 ValidationException"""
        from pykis.stock.api_improved import StockAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValidationException):
                StockAPI(mock_client, {"CANO": "12345678"})


class TestGetStockPrice(TestStockAPIImproved):
    """get_stock_price 메서드 테스트"""

    def test_get_stock_price_success(self, stock_api, mock_client):
        """정상 현재가 조회"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다.",
            "output": {"stck_prpr": "70000", "prdy_vrss": "1000"},
        }

        result = stock_api.get_stock_price("005930")

        assert result["rt_cd"] == "0"
        assert "output" in result
        mock_client.make_request.assert_called_once()

    def test_get_stock_price_with_none_code(self, stock_api):
        """종목코드가 None인 경우"""
        with pytest.raises(ValidationException):
            stock_api.get_stock_price(None)

    def test_get_stock_price_with_invalid_code_length(self, stock_api):
        """종목코드가 6자리가 아닌 경우"""
        with pytest.raises(ValidationException):
            stock_api.get_stock_price("00593")  # 5자리

    def test_get_stock_price_api_error(self, stock_api, mock_client):
        """API 오류 응답 처리"""
        mock_client.make_request.return_value = {
            "rt_cd": "1",
            "msg1": "종목코드 오류",
        }

        with pytest.raises(APIException):
            stock_api.get_stock_price("999999")


class TestGetDailyPrice(TestStockAPIImproved):
    """get_daily_price 메서드 테스트"""

    def test_get_daily_price_success(self, stock_api, mock_client):
        """정상 일별 시세 조회"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다.",
            "output": [
                {"stck_bsop_date": "20231215", "stck_clpr": "70000"},
                {"stck_bsop_date": "20231214", "stck_clpr": "69500"},
            ],
        }

        result = stock_api.get_daily_price("005930")

        assert result["rt_cd"] == "0"
        assert "output" in result

    def test_get_daily_price_with_period_week(self, stock_api, mock_client):
        """주봉 조회"""
        mock_client.make_request.return_value = {"rt_cd": "0", "output": []}

        result = stock_api.get_daily_price("005930", period="W")

        assert result["rt_cd"] == "0"

    def test_get_daily_price_with_invalid_period(self, stock_api):
        """잘못된 기간구분"""
        with pytest.raises(ValidationException):
            stock_api.get_daily_price("005930", period="X")

    def test_get_daily_price_with_invalid_org_adj_prc(self, stock_api):
        """잘못된 수정주가구분"""
        with pytest.raises(ValidationException):
            stock_api.get_daily_price("005930", org_adj_prc="2")


class TestGetStockMember(TestStockAPIImproved):
    """get_stock_member 메서드 테스트"""

    def test_get_stock_member_success(self, stock_api, mock_client):
        """정상 회원사 정보 조회"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"scrs_corp_name": "한국투자증권", "seln_qty": "10000"},
            ],
        }

        result = stock_api.get_stock_member("005930")

        assert result["rt_cd"] == "0"
        assert "output" in result

    def test_get_stock_member_empty_output(self, stock_api, mock_client):
        """회원사 정보 없음"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [],
        }

        result = stock_api.get_stock_member("005930")

        assert result["output"] == []

    def test_get_stock_member_with_none_ticker(self, stock_api):
        """종목코드가 None인 경우"""
        with pytest.raises(ValidationException):
            stock_api.get_stock_member(None)

    def test_get_stock_member_retry_on_failure(self, stock_api, mock_client):
        """재시도 로직 테스트"""
        # 처음 2번 실패, 3번째 성공
        mock_client.make_request.side_effect = [
            Exception("첫 번째 실패"),
            Exception("두 번째 실패"),
            {"rt_cd": "0", "output": [{"scrs_corp_name": "테스트"}]},
        ]

        result = stock_api.get_stock_member("005930", retries=3)

        assert result["rt_cd"] == "0"
        assert mock_client.make_request.call_count == 3

    def test_get_stock_member_all_retries_failed(self, stock_api, mock_client):
        """모든 재시도 실패"""
        mock_client.make_request.side_effect = Exception("API 실패")

        with pytest.raises(APIException):
            stock_api.get_stock_member("005930", retries=3)


class TestGetForeignNetBuy(TestStockAPIImproved):
    """get_foreign_net_buy 메서드 테스트"""

    def test_get_foreign_net_buy_invalid_date_format(self, stock_api):
        """잘못된 날짜 형식"""
        with pytest.raises(ValidationException):
            stock_api.get_foreign_net_buy("005930", "2023-12-15")


class TestGetHolidays(TestStockAPIImproved):
    """get_holidays 메서드 테스트"""

    def test_get_holidays_invalid_year(self, stock_api):
        """잘못된 연도 형식"""
        with pytest.raises(ValidationException):
            stock_api.get_holidays("23")

    def test_get_holidays_non_numeric_year(self, stock_api):
        """숫자가 아닌 연도"""
        with pytest.raises(ValidationException):
            stock_api.get_holidays("abcd")


class TestMakeRequestDict(TestStockAPIImproved):
    """_make_request_dict 메서드 테스트"""

    def test_make_request_dict_no_response(self, stock_api, mock_client):
        """응답 없음"""
        mock_client.make_request.return_value = None

        with pytest.raises(APIException):
            stock_api._make_request_dict(
                endpoint="/test",
                tr_id="TEST001",
                params={},
            )

    def test_make_request_dict_error_response(self, stock_api, mock_client):
        """오류 응답"""
        mock_client.make_request.return_value = {
            "rt_cd": "1",
            "msg1": "시스템 오류",
        }

        with pytest.raises(APIException) as exc_info:
            stock_api._make_request_dict(
                endpoint="/test",
                tr_id="TEST001",
                params={},
            )

        assert "시스템 오류" in str(exc_info.value)


class TestMakeRequestDataframe(TestStockAPIImproved):
    """_make_request_dataframe 메서드 테스트"""

    def test_make_request_dataframe_dict_output(self, stock_api, mock_client):
        """output이 dict인 경우"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"key": "value"},
        }

        result = stock_api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST001",
            params={},
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_make_request_dataframe_list_output(self, stock_api, mock_client):
        """output이 list인 경우"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"key": "value1"}, {"key": "value2"}],
        }

        result = stock_api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST001",
            params={},
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_make_request_dataframe_empty_output(self, stock_api, mock_client):
        """output이 빈 리스트인 경우"""
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [],
        }

        result = stock_api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST001",
            params={},
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestExampleUsage:
    """example_usage 함수 테스트"""

    def test_example_usage_importable(self):
        """example_usage 함수 import 가능"""
        from pykis.stock.api_improved import example_usage

        assert callable(example_usage)

    def test_module_all_exports(self):
        """__all__ 내보내기 확인"""
        from pykis.stock import api_improved

        assert "StockAPI" in api_improved.__all__
        assert "example_usage" in api_improved.__all__
