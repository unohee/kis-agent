"""
AccountOrderAPI 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상: pykis/account/order_api.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestAccountOrderAPI:
    """AccountOrderAPI 클래스 테스트"""

    @pytest.fixture
    def mock_client(self):
        """모의 클라이언트"""
        client = MagicMock()
        client.make_request.return_value = {"rt_cd": "0", "output": {"odno": "12345"}}
        client.is_real = True
        return client

    @pytest.fixture
    def account_info(self):
        """계좌 정보"""
        return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    @pytest.fixture
    def order_api(self, mock_client, account_info):
        """AccountOrderAPI 인스턴스"""
        from pykis.account.order_api import AccountOrderAPI

        return AccountOrderAPI(
            client=mock_client,
            account_info=account_info,
            enable_cache=False,
            _from_agent=True,
        )

    # ===== order_cash 테스트 =====

    def test_order_cash_buy_success(self, order_api, mock_client):
        """현금 매수 주문 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "주문 완료",
            "output": {"odno": "0000117057"},
        }

        # Act
        result = order_api.order_cash(
            pdno="005930", qty=10, price=70000, buy_sell="BUY", order_type="00"
        )

        # Assert
        assert result is not None
        assert result["rt_cd"] == "0"
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0012U"  # 매수
        assert call_args[1]["params"]["PDNO"] == "005930"
        assert call_args[1]["params"]["ORD_QTY"] == "10"
        assert call_args[1]["params"]["ORD_UNPR"] == "70000"

    def test_order_cash_sell_success(self, order_api, mock_client):
        """현금 매도 주문 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0000117058"},
        }

        # Act
        result = order_api.order_cash(
            pdno="005930", qty=5, price=72000, buy_sell="SELL", order_type="00"
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0011U"  # 매도

    def test_order_cash_market_order(self, order_api, mock_client):
        """시장가 주문 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_cash(
            pdno="005930", qty=10, price=0, buy_sell="BUY", order_type="01"
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["params"]["ORD_DVSN"] == "01"
        assert call_args[1]["params"]["ORD_UNPR"] == "0"

    def test_order_cash_with_exchange_sor(self, order_api, mock_client):
        """SOR 거래소 주문 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_cash(
            pdno="005930", qty=10, price=70000, buy_sell="BUY", exchange="SOR"
        )

        # Assert
        call_args = mock_client.make_request.call_args
        assert call_args[1]["params"]["EXCG_ID_DVSN_CD"] == "SOR"

    def test_order_cash_exception_handling(self, order_api, mock_client):
        """현금 주문 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("API 오류")

        # Act
        result = order_api.order_cash(
            pdno="005930", qty=10, price=70000, buy_sell="BUY"
        )

        # Assert
        assert result is None

    # ===== order_cash_sor 테스트 =====

    def test_order_cash_sor_success(self, order_api, mock_client):
        """SOR 최유리지정가 주문 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_cash_sor(pdno="005930", qty=10, buy_sell="BUY")

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["params"]["ORD_DVSN"] == "03"  # 최유리지정가
        assert call_args[1]["params"].get("EXCG_ID_DVSN_CD") == "SOR"

    # ===== order_credit 테스트 =====

    def test_order_credit_success(self, order_api, mock_client):
        """신용 주문 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0000117059"},
        }

        # Act
        result = order_api.order_credit(
            code="005930", qty=10, price=70000, order_type="00"
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0052U"
        assert call_args[1]["params"]["CRDT_TYPE"] == "21"

    def test_order_credit_exception_handling(self, order_api, mock_client):
        """신용 주문 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("신용 한도 초과")

        # Act
        result = order_api.order_credit(
            code="005930", qty=10, price=70000, order_type="00"
        )

        # Assert
        assert result is None

    # ===== order_credit_buy 테스트 =====

    def test_order_credit_buy_success(self, order_api, mock_client):
        """신용 매수 주문 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0000117060"},
        }

        # Act
        result = order_api.order_credit_buy(
            pdno="005930",
            qty=10,
            price=70000,
            order_type="00",
            credit_type="21",
            loan_dt="20260104",
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0052U"
        assert call_args[1]["params"]["CRDT_TYPE"] == "21"
        assert call_args[1]["params"]["LOAN_DT"] == "20260104"

    def test_order_credit_buy_auto_loan_date(self, order_api, mock_client):
        """자기융자 시 대출일자 자동 설정 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_credit_buy(
            pdno="005930",
            qty=10,
            price=70000,
            credit_type="22",  # 자기융자
            loan_dt="",  # 빈 값
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        # 자기융자(22)일 때 loan_dt가 자동 설정됨
        assert call_args[1]["params"]["LOAN_DT"] != ""

    def test_order_credit_buy_with_sor(self, order_api, mock_client):
        """신용 매수 SOR 거래소 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_credit_buy(
            pdno="005930", qty=10, price=70000, exchange="SOR"
        )

        # Assert
        call_args = mock_client.make_request.call_args
        assert call_args[1]["params"]["EXCG_ID_DVSN_CD"] == "SOR"

    def test_order_credit_buy_exception_handling(self, order_api, mock_client):
        """신용 매수 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("신용매수 실패")

        # Act
        result = order_api.order_credit_buy(pdno="005930", qty=10, price=70000)

        # Assert
        assert result is None

    # ===== order_credit_sell 테스트 =====

    def test_order_credit_sell_success(self, order_api, mock_client):
        """신용 매도 주문 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0000117061"},
        }

        # Act
        result = order_api.order_credit_sell(
            pdno="005930", qty=5, price=72000, order_type="00", credit_type="11"
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0051U"
        assert call_args[1]["params"]["CRDT_TYPE"] == "11"

    def test_order_credit_sell_exception_handling(self, order_api, mock_client):
        """신용 매도 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("신용매도 실패")

        # Act
        result = order_api.order_credit_sell(pdno="005930", qty=5, price=72000)

        # Assert
        assert result is None

    # ===== order_rvsecncl 테스트 =====

    def test_order_rvsecncl_modify_success(self, order_api, mock_client):
        """주문 정정 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0000117062"},
        }

        # Act
        result = order_api.order_rvsecncl(
            org_order_no="0000117057",
            qty=5,
            price=71000,
            order_type="00",
            cncl_type="정정",
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0013U"
        assert call_args[1]["params"]["ORGN_ODNO"] == "0000117057"
        assert call_args[1]["params"]["RVSE_CNCL_DVSN_CD"] == "정정"

    def test_order_rvsecncl_cancel_success(self, order_api, mock_client):
        """주문 취소 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_rvsecncl(
            org_order_no="0000117057",
            qty=10,
            price=0,
            order_type="00",
            cncl_type="취소",
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["params"]["RVSE_CNCL_DVSN_CD"] == "취소"
        assert call_args[1]["params"]["QTY_ALL_ORD_YN"] == "Y"

    def test_order_rvsecncl_exception_handling(self, order_api, mock_client):
        """정정/취소 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("정정/취소 실패")

        # Act
        result = order_api.order_rvsecncl(
            org_order_no="0000117057",
            qty=5,
            price=71000,
            order_type="00",
            cncl_type="정정",
        )

        # Assert
        assert result is None

    # ===== inquire_psbl_rvsecncl 테스트 =====

    def test_inquire_psbl_rvsecncl_success(self, order_api, mock_client):
        """정정/취소 가능 주문 목록 조회 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"odno": "0000117057", "ord_qty": "10", "ccld_qty": "0"},
                {"odno": "0000117058", "ord_qty": "5", "ccld_qty": "2"},
            ],
        }

        # Act
        result = order_api.inquire_psbl_rvsecncl()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC8036R"
        assert call_args[1]["params"]["INQR_DVSN_1"] == "1"

    def test_inquire_psbl_rvsecncl_exception_handling(self, order_api, mock_client):
        """정정/취소 가능 조회 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = order_api.inquire_psbl_rvsecncl()

        # Assert
        assert result is None

    # ===== order_resv 테스트 =====

    def test_order_resv_success(self, order_api, mock_client):
        """예약 주문 등록 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"rsvn_ord_seq": "0000000001"},
        }

        # Act
        result = order_api.order_resv(
            code="005930", qty=10, price=70000, order_type="00"
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "CTSC0008U"
        assert call_args[1]["params"]["PDNO"] == "005930"
        assert call_args[1]["params"]["SLL_BUY_DVSN_CD"] == "02"

    def test_order_resv_exception_handling(self, order_api, mock_client):
        """예약 주문 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("예약 주문 실패")

        # Act
        result = order_api.order_resv(
            code="005930", qty=10, price=70000, order_type="00"
        )

        # Assert
        assert result is None

    # ===== order_resv_rvsecncl 테스트 =====

    def test_order_resv_rvsecncl_success(self, order_api, mock_client):
        """예약 주문 정정/취소 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # Act
        result = order_api.order_resv_rvsecncl(
            seq=1, qty=5, price=71000, order_type="00"
        )

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "CTSC0013U"
        assert call_args[1]["params"]["RSVN_ORD_SEQ"] == "1"

    def test_order_resv_rvsecncl_exception_handling(self, order_api, mock_client):
        """예약 주문 정정/취소 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("예약 정정 실패")

        # Act
        result = order_api.order_resv_rvsecncl(
            seq=1, qty=5, price=71000, order_type="00"
        )

        # Assert
        assert result is None

    # ===== order_resv_ccnl 테스트 =====

    def test_order_resv_ccnl_success(self, order_api, mock_client):
        """예약 주문 내역 조회 성공 테스트"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"rsvn_ord_seq": "1", "pdno": "005930", "ord_qty": "10"},
                {"rsvn_ord_seq": "2", "pdno": "035420", "ord_qty": "5"},
            ],
        }

        # Act
        result = order_api.order_resv_ccnl()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "CTSC0004R"
        assert call_args[1]["params"]["CNCL_YN"] == "Y"

    def test_order_resv_ccnl_exception_handling(self, order_api, mock_client):
        """예약 주문 조회 예외 처리 테스트"""
        # Arrange
        mock_client.make_request.side_effect = Exception("조회 실패")

        # Act
        result = order_api.order_resv_ccnl()

        # Assert
        assert result is None
