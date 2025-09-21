"""
새로 추가된 StockAPI 주문 관련 메서드들에 대한 단위 테스트
"""

import pytest
from unittest.mock import Mock, patch
from pykis.stock.api import StockAPI
from pykis.core.client import KISClient


class TestStockOrderAPI:
    """StockAPI 주문 관련 메서드 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient 생성"""
        client = Mock(spec=KISClient)
        client.is_mock = False
        return client

    @pytest.fixture
    def stock_api(self, mock_client):
        """StockAPI 인스턴스 생성"""
        account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        return StockAPI(mock_client, account_info, enable_cache=False)

    def test_order_cash_buy_success(self, stock_api, mock_client):
        """현금 매수 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117057", "ord_tmd": "103422"},
        }
        mock_client.make_request.return_value = expected_response

        # When
        result = stock_api.order_cash(
            ord_dv="buy", pdno="005930", ord_dvsn="00", ord_qty="1", ord_unpr="70000"
        )

        # Then
        assert result == expected_response
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["tr_id"] == "TTTC0012U"  # 실전 매수
        assert call_args[1]["params"]["PDNO"] == "005930"
        assert call_args[1]["params"]["ORD_DVSN"] == "00"

    def test_order_cash_sell_success(self, stock_api, mock_client):
        """현금 매도 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117058", "ord_tmd": "103523"},
        }
        mock_client.make_request.return_value = expected_response

        # When
        result = stock_api.order_cash(
            ord_dv="sell", pdno="005930", ord_dvsn="01", ord_qty="1", ord_unpr="0"
        )

        # Then
        assert result == expected_response
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0011U"  # 실전 매도

    def test_order_cash_mock_mode(self, stock_api, mock_client):
        """모의투자 모드에서 현금 주문 테스트"""
        # Given
        mock_client.is_mock = True
        expected_response = {"rt_cd": "0", "msg1": "모의투자 주문 성공"}
        mock_client.make_request.return_value = expected_response

        # When
        result = stock_api.order_cash(
            ord_dv="buy", pdno="005930", ord_dvsn="00", ord_qty="1", ord_unpr="70000"
        )

        # Then
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "VTTC0012U"  # 모의 매수

    def test_order_cash_invalid_params(self, stock_api):
        """현금 주문 잘못된 파라미터 테스트"""
        # Given & When & Then
        with pytest.raises(ValueError, match="ord_dv must be 'buy' or 'sell'"):
            stock_api.order_cash("invalid", "005930", "00", "1", "70000")

        with pytest.raises(ValueError, match="pdno \\(종목코드\\) is required"):
            stock_api.order_cash("buy", "", "00", "1", "70000")

    def test_order_credit_buy_success(self, stock_api, mock_client):
        """신용 매수 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "신용주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117059", "ord_tmd": "103624"},
        }
        mock_client.make_request.return_value = expected_response

        # When
        result = stock_api.order_credit(
            ord_dv="buy",
            pdno="005930",
            crdt_type="21",
            loan_dt="20250911",
            ord_dvsn="00",
            ord_qty="1",
            ord_unpr="70000",
        )

        # Then
        assert result == expected_response
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["tr_id"] == "TTTC0052U"  # 신용 매수
        assert call_args[1]["params"]["CRDT_TYPE"] == "21"

    def test_order_credit_sell_success(self, stock_api, mock_client):
        """신용 매도 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "신용주문이 정상적으로 접수되었습니다.",
        }
        mock_client.make_request.return_value = expected_response

        # When
        result = stock_api.order_credit(
            ord_dv="sell",
            pdno="005930",
            crdt_type="25",
            loan_dt="20250901",
            ord_dvsn="00",
            ord_qty="1",
            ord_unpr="70000",
        )

        # Then
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0051U"  # 신용 매도

    def test_order_credit_mock_mode_error(self, stock_api, mock_client):
        """모의투자에서 신용 주문 시 에러 테스트"""
        # Given
        mock_client.is_mock = True

        # When & Then
        with pytest.raises(
            ValueError, match="신용거래는 모의투자에서 지원되지 않습니다"
        ):
            stock_api.order_credit(
                ord_dv="buy",
                pdno="005930",
                crdt_type="21",
                loan_dt="20250911",
                ord_dvsn="00",
                ord_qty="1",
                ord_unpr="70000",
            )

    def test_inquire_psbl_order_success(self, stock_api, mock_client):
        """매수가능조회 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "ord_psbl_cash": "1000000",
                "max_buy_qty": "14",
                "ord_psbl_qty": "14",
            },
        }

        with patch.object(
            stock_api, "_make_request_dict", return_value=expected_response
        ):
            # When
            result = stock_api.inquire_psbl_order("005930", "70000")

            # Then
            assert result == expected_response
            stock_api._make_request_dict.assert_called_once()
            call_args = stock_api._make_request_dict.call_args
            assert call_args[1]["tr_id"] == "TTTC8908R"
            assert call_args[1]["params"]["PDNO"] == "005930"
            assert call_args[1]["params"]["ORD_UNPR"] == "70000"

    def test_inquire_credit_psamount_success(self, stock_api, mock_client):
        """신용매수가능조회 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "crdt_buy_psbl_amt": "2000000",
                "max_buy_qty": "28",
                "crdt_psbl_qty": "28",
            },
        }

        with patch.object(
            stock_api, "_make_request_dict", return_value=expected_response
        ):
            # When
            result = stock_api.inquire_credit_psamount("005930", "70000")

            # Then
            assert result == expected_response
            stock_api._make_request_dict.assert_called_once()
            call_args = stock_api._make_request_dict.call_args
            assert call_args[1]["tr_id"] == "TTTC8909R"
            assert call_args[1]["params"]["CRDT_TYPE"] == "21"

    def test_inquire_psbl_order_no_account(self, mock_client):
        """계좌 정보 없이 매수가능조회 시 에러 테스트"""
        # Given
        stock_api = StockAPI(mock_client, account_info=None, enable_cache=False)

        # When & Then
        with pytest.raises(ValueError, match="Account information is required"):
            stock_api.inquire_psbl_order("005930", "70000")

    def test_inquire_credit_psamount_no_account(self, mock_client):
        """계좌 정보 없이 신용매수가능조회 시 에러 테스트"""
        # Given
        stock_api = StockAPI(mock_client, account_info=None, enable_cache=False)

        # When & Then
        with pytest.raises(ValueError, match="Account information is required"):
            stock_api.inquire_credit_psamount("005930", "70000")

    def test_order_cash_no_account(self, mock_client):
        """계좌 정보 없이 주문 시 에러 테스트"""
        # Given
        stock_api = StockAPI(mock_client, account_info=None, enable_cache=False)

        # When & Then
        with pytest.raises(ValueError, match="Account information is required"):
            stock_api.order_cash("buy", "005930", "00", "1", "70000")

    def test_order_credit_no_account(self, mock_client):
        """계좌 정보 없이 신용주문 시 에러 테스트"""
        # Given
        stock_api = StockAPI(mock_client, account_info=None, enable_cache=False)

        # When & Then
        with pytest.raises(ValueError, match="Account information is required"):
            stock_api.order_credit(
                "buy", "005930", "21", "20250911", "00", "1", "70000"
            )
