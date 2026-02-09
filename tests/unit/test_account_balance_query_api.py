"""
AccountBalanceQueryAPI 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상: pykis/account/balance_query_api.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestAccountBalanceQueryAPI:
    """AccountBalanceQueryAPI 클래스 테스트"""

    @pytest.fixture
    def mock_client(self):
        """모의 클라이언트"""
        client = MagicMock()
        client.make_request.return_value = {"rt_cd": "0", "output": {}}
        client.is_real = True
        return client

    @pytest.fixture
    def account_info(self):
        """계좌 정보"""
        return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    @pytest.fixture
    def balance_api(self, mock_client, account_info):
        """AccountBalanceQueryAPI 인스턴스"""
        from kis_agent.account.balance_query_api import AccountBalanceQueryAPI

        return AccountBalanceQueryAPI(
            client=mock_client,
            account_info=account_info,
            enable_cache=False,
            _from_agent=True,
        )

    # ===== get_account_balance 테스트 =====

    def test_get_account_balance_success(self, balance_api, mock_client):
        """계좌 잔고 조회 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output1": [
                {"pdno": "005930", "prdt_name": "삼성전자", "hldg_qty": "100"},
                {"pdno": "035420", "prdt_name": "NAVER", "hldg_qty": "50"},
            ],
            "output2": {
                "dnca_tot_amt": "10000000",
                "tot_evlu_amt": "15000000",
                "nass_amt": "15000000",
            },
        }

        # Act
        result = balance_api.get_account_balance()

        # Assert
        assert result is not None
        assert result["rt_cd"] == "0"
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8434R"
        assert call_args[1]["params"]["CANO"] == "12345678"

    # ===== get_cash_available 테스트 =====

    def test_get_cash_available_success(self, balance_api, mock_client):
        """매수 가능 금액 조회 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "ord_psbl_cash": "5000000",
                "max_buy_qty": "71",
            },
        }

        # Act
        result = balance_api.get_cash_available("005930")

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8908R"
        assert call_args[1]["params"]["PDNO"] == "005930"

    def test_get_cash_available_json_decode_error(self, balance_api, mock_client):
        """JSON 디코드 에러 시 디버깅 정보 추가"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "JSON_DECODE_ERROR",
            "status_code": 500,
        }

        # Act
        result = balance_api.get_cash_available("005930")

        # Assert
        assert result is not None
        assert "디버깅_정보" in result

    # ===== get_total_asset 테스트 =====

    def test_get_total_asset_success(self, balance_api, mock_client):
        """총 자산 조회 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output2": {
                "tot_asst_amt": "50000000",
                "evlu_pfls_smtl_amt": "5000000",
            },
        }

        # Act
        result = balance_api.get_total_asset()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "CTRP6548R"

    def test_get_total_asset_json_decode_error(self, balance_api, mock_client):
        """총 자산 조회 JSON 디코드 에러 처리"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "JSON_DECODE_ERROR",
            "status_code": 400,
        }

        # Act
        result = balance_api.get_total_asset()

        # Assert
        assert result is not None
        assert "디버깅_정보" in result

    # ===== get_account_order_quantity 테스트 =====

    def test_get_account_order_quantity_success(self, balance_api, mock_client):
        """종목별 주문 가능 수량 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_qty": "100"},
        }

        # Act
        result = balance_api.get_account_order_quantity("005930")

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["params"]["PDNO"] == "005930"

    def test_get_account_order_quantity_exception(self, balance_api, mock_client):
        """종목별 주문 가능 수량 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = balance_api.get_account_order_quantity("005930")

        # Assert
        assert result is None

    # ===== get_possible_order_amount 테스트 =====

    def test_get_possible_order_amount_success(self, balance_api, mock_client):
        """주문 가능 금액 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_amt": "10000000"},
        }

        # Act
        result = balance_api.get_possible_order_amount()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8908R"

    def test_get_possible_order_amount_exception(self, balance_api, mock_client):
        """주문 가능 금액 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = balance_api.get_possible_order_amount()

        # Assert
        assert result is None

    # ===== inquire_balance_rlz_pl 테스트 =====

    def test_inquire_balance_rlz_pl_success(self, balance_api, mock_client):
        """실현 손익 잔고 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output1": [
                {"pdno": "005930", "rlzt_pfls": "500000"},
            ],
        }

        # Act
        result = balance_api.inquire_balance_rlz_pl()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8494R"

    def test_inquire_balance_rlz_pl_exception(self, balance_api, mock_client):
        """실현 손익 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = balance_api.inquire_balance_rlz_pl()

        # Assert
        assert result is None

    # ===== inquire_psbl_sell 테스트 =====

    def test_inquire_psbl_sell_success(self, balance_api, mock_client):
        """매도 가능 수량 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"psbl_sell_qty": "100"},
        }

        # Act
        result = balance_api.inquire_psbl_sell("005930")

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8408R"
        assert call_args[1]["params"]["PDNO"] == "005930"

    def test_inquire_psbl_sell_exception(self, balance_api, mock_client):
        """매도 가능 수량 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = balance_api.inquire_psbl_sell("005930")

        # Assert
        assert result is None

    # ===== inquire_intgr_margin 테스트 =====

    def test_inquire_intgr_margin_success(self, balance_api, mock_client):
        """통합 증거금 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"intgr_mgn_amt": "5000000"},
        }

        # Act
        result = balance_api.inquire_intgr_margin()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0869R"

    def test_inquire_intgr_margin_exception(self, balance_api, mock_client):
        """통합 증거금 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = balance_api.inquire_intgr_margin()

        # Assert
        assert result is None

    # ===== inquire_psbl_order 테스트 =====

    def test_inquire_psbl_order_success(self, balance_api, mock_client):
        """매수 가능 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "ord_psbl_cash": "5000000",
                "max_buy_qty": "71",
                "ord_psbl_qty": "71",
            },
        }

        # Act
        result = balance_api.inquire_psbl_order(price=70000, pdno="005930")

        # Assert
        assert result is not None
        assert result["ord_psbl_cash"] == "5000000"

    def test_inquire_psbl_order_mock_account(self, balance_api, mock_client):
        """모의 계좌 매수 가능 조회"""
        # Arrange
        mock_client.is_real = False
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_qty": "100"},
        }

        # Act
        result = balance_api.inquire_psbl_order(price=70000)

        # Assert
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "VTTC8908R"

    def test_inquire_psbl_order_failure(self, balance_api, mock_client):
        """매수 가능 조회 실패"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "1",
            "msg1": "조회 실패",
        }

        # Act
        result = balance_api.inquire_psbl_order(price=70000)

        # Assert
        assert result is None

    def test_inquire_psbl_order_exception(self, balance_api, mock_client):
        """매수 가능 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = balance_api.inquire_psbl_order(price=70000)

        # Assert
        assert result is None

    # ===== inquire_credit_psamount 테스트 =====

    def test_inquire_credit_psamount_success(self, balance_api, mock_client):
        """신용 매수 가능 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "crdt_buy_psbl_amt": "10000000",
                "max_buy_qty": "142",
            },
        }

        # Act
        result = balance_api.inquire_credit_psamount("005930")

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8909R"
        assert call_args[1]["params"]["CRDT_TYPE"] == "21"

    def test_inquire_credit_psamount_exception(self, balance_api, mock_client):
        """신용 매수 가능 조회 예외 처리"""
        # Arrange
        mock_client.make_request.side_effect = Exception("신용 조회 실패")

        # Act
        result = balance_api.inquire_credit_psamount("005930")

        # Assert
        assert result is None
