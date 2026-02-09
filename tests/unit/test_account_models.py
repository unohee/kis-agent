"""
Account Models 모듈 테스트

pykis/account/models.py의 데이터 모델들을 테스트합니다.
"""

from datetime import datetime

import pytest

from pykis.account.models import (
    OrderExecutionItem,
    OrderExecutionResponse,
    OrderExecutionSummary,
)


class TestOrderExecutionItem:
    """OrderExecutionItem 데이터 모델 테스트"""

    @pytest.fixture
    def buy_order(self):
        """매수 주문 fixture"""
        return OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567890",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="100",
            ord_unpr="70000",
            ord_tmd="093015",
            tot_ccld_qty="100",
            avg_prvs="70000",
            tot_ccld_amt="7000000",
            cncl_yn="N",
        )

    @pytest.fixture
    def sell_order(self):
        """매도 주문 fixture"""
        return OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567891",
            orgn_odno="",
            ord_dvsn_name="시장가",
            sll_buy_dvsn_cd="01",
            sll_buy_dvsn_cd_name="매도",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="50",
            ord_unpr="0",
            ord_tmd="140530",
            tot_ccld_qty="50",
            avg_prvs="71000",
            tot_ccld_amt="3550000",
            cncl_yn="N",
        )

    @pytest.fixture
    def cancelled_order(self):
        """취소된 주문 fixture"""
        return OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567892",
            orgn_odno="1234567890",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="035420",
            prdt_name="NAVER",
            ord_qty="10",
            ord_unpr="200000",
            ord_tmd="101500",
            tot_ccld_qty="0",
            avg_prvs="0",
            tot_ccld_amt="0",
            cncl_yn="Y",
        )

    @pytest.fixture
    def partial_order(self):
        """부분 체결 주문 fixture"""
        return OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567893",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="100",
            ord_unpr="69500",
            ord_tmd="093500",
            tot_ccld_qty="30",
            avg_prvs="69500",
            tot_ccld_amt="2085000",
            cncl_yn="N",
        )

    def test_is_buy_property(self, buy_order, sell_order):
        """is_buy 속성 테스트"""
        assert buy_order.is_buy is True
        assert sell_order.is_buy is False

    def test_is_sell_property(self, buy_order, sell_order):
        """is_sell 속성 테스트"""
        assert sell_order.is_sell is True
        assert buy_order.is_sell is False

    def test_is_executed_property(self, buy_order, cancelled_order):
        """is_executed 속성 테스트"""
        assert buy_order.is_executed is True
        assert cancelled_order.is_executed is False

    def test_is_executed_with_invalid_values(self):
        """is_executed 속성 - 잘못된 값 처리"""
        order = OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="123",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="100",
            ord_unpr="70000",
            ord_tmd="093015",
            tot_ccld_qty="invalid",  # 잘못된 값
            avg_prvs="70000",
            tot_ccld_amt="7000000",
            cncl_yn="N",
        )
        assert order.is_executed is False

    def test_is_cancelled_property(self, buy_order, cancelled_order):
        """is_cancelled 속성 테스트"""
        assert cancelled_order.is_cancelled is True
        assert buy_order.is_cancelled is False

    def test_execution_rate_full(self, buy_order):
        """execution_rate - 전량 체결"""
        assert buy_order.execution_rate == 100.0

    def test_execution_rate_partial(self, partial_order):
        """execution_rate - 부분 체결"""
        assert partial_order.execution_rate == 30.0

    def test_execution_rate_none(self, cancelled_order):
        """execution_rate - 미체결"""
        assert cancelled_order.execution_rate == 0.0

    def test_execution_rate_invalid_values(self):
        """execution_rate - 잘못된 값 처리"""
        order = OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="123",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="invalid",  # 잘못된 값
            ord_unpr="70000",
            ord_tmd="093015",
            tot_ccld_qty="50",
            avg_prvs="70000",
            tot_ccld_amt="3500000",
            cncl_yn="N",
        )
        assert order.execution_rate == 0.0

    def test_execution_rate_zero_order_qty(self):
        """execution_rate - 주문수량 0"""
        order = OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="123",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="0",  # 0
            ord_unpr="70000",
            ord_tmd="093015",
            tot_ccld_qty="0",
            avg_prvs="0",
            tot_ccld_amt="0",
            cncl_yn="N",
        )
        assert order.execution_rate == 0.0

    def test_get_order_datetime(self, buy_order):
        """get_order_datetime 메서드 테스트"""
        dt = buy_order.get_order_datetime()
        assert dt is not None
        assert isinstance(dt, datetime)
        assert dt.year == 2023
        assert dt.month == 12
        assert dt.day == 15
        assert dt.hour == 9
        assert dt.minute == 30
        assert dt.second == 15

    def test_get_order_datetime_invalid(self):
        """get_order_datetime - 잘못된 값"""
        order = OrderExecutionItem(
            ord_dt="invalid_date",
            ord_gno_brno="91234",
            odno="123",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="100",
            ord_unpr="70000",
            ord_tmd="invalid_time",
            tot_ccld_qty="100",
            avg_prvs="70000",
            tot_ccld_amt="7000000",
            cncl_yn="N",
        )
        assert order.get_order_datetime() is None

    def test_to_dict(self, buy_order):
        """to_dict 메서드 테스트"""
        result = buy_order.to_dict()
        assert isinstance(result, dict)
        assert result["ord_dt"] == "20231215"
        assert result["pdno"] == "005930"
        assert result["ord_qty"] == "100"
        # None 값은 포함되지 않아야 함
        assert "loan_dt" not in result

    def test_to_dict_with_optional_fields(self, buy_order):
        """to_dict - 선택적 필드 포함"""
        buy_order.loan_dt = "20231210"
        buy_order.ordr_empno = "12345"
        result = buy_order.to_dict()
        assert result["loan_dt"] == "20231210"
        assert result["ordr_empno"] == "12345"


class TestOrderExecutionSummary:
    """OrderExecutionSummary 데이터 모델 테스트"""

    @pytest.fixture
    def summary(self):
        """요약 데이터 fixture"""
        return OrderExecutionSummary(
            tot_ord_qty="150",
            tot_ccld_qty="130",
            tot_ccld_amt="9050000",
            prsm_tlex_smtl="23150",
            pchs_avg_pric="69615.38",
        )

    def test_total_order_qty(self, summary):
        """total_order_qty 속성 테스트"""
        assert summary.total_order_qty == 150

    def test_total_order_qty_invalid(self):
        """total_order_qty - 잘못된 값"""
        summary = OrderExecutionSummary(
            tot_ord_qty="invalid",
            tot_ccld_qty="100",
            tot_ccld_amt="7000000",
            prsm_tlex_smtl="20000",
            pchs_avg_pric="70000",
        )
        assert summary.total_order_qty == 0

    def test_total_executed_qty(self, summary):
        """total_executed_qty 속성 테스트"""
        assert summary.total_executed_qty == 130

    def test_total_executed_qty_invalid(self):
        """total_executed_qty - 잘못된 값"""
        summary = OrderExecutionSummary(
            tot_ord_qty="150",
            tot_ccld_qty="invalid",
            tot_ccld_amt="7000000",
            prsm_tlex_smtl="20000",
            pchs_avg_pric="70000",
        )
        assert summary.total_executed_qty == 0

    def test_total_executed_amount(self, summary):
        """total_executed_amount 속성 테스트"""
        assert summary.total_executed_amount == 9050000.0

    def test_total_executed_amount_invalid(self):
        """total_executed_amount - 잘못된 값"""
        summary = OrderExecutionSummary(
            tot_ord_qty="150",
            tot_ccld_qty="130",
            tot_ccld_amt="invalid",
            prsm_tlex_smtl="20000",
            pchs_avg_pric="70000",
        )
        assert summary.total_executed_amount == 0.0

    def test_estimated_fees(self, summary):
        """estimated_fees 속성 테스트"""
        assert summary.estimated_fees == 23150.0

    def test_estimated_fees_invalid(self):
        """estimated_fees - 잘못된 값"""
        summary = OrderExecutionSummary(
            tot_ord_qty="150",
            tot_ccld_qty="130",
            tot_ccld_amt="9050000",
            prsm_tlex_smtl="invalid",
            pchs_avg_pric="70000",
        )
        assert summary.estimated_fees == 0.0

    def test_average_price(self, summary):
        """average_price 속성 테스트"""
        assert summary.average_price == 69615.38

    def test_average_price_invalid(self):
        """average_price - 잘못된 값"""
        summary = OrderExecutionSummary(
            tot_ord_qty="150",
            tot_ccld_qty="130",
            tot_ccld_amt="9050000",
            prsm_tlex_smtl="23150",
            pchs_avg_pric="invalid",
        )
        assert summary.average_price == 0.0

    def test_to_dict(self, summary):
        """to_dict 메서드 테스트"""
        result = summary.to_dict()
        assert isinstance(result, dict)
        assert result["tot_ord_qty"] == "150"
        assert result["tot_ccld_qty"] == "130"
        assert result["tot_ccld_amt"] == "9050000"


class TestOrderExecutionResponse:
    """OrderExecutionResponse 데이터 모델 테스트"""

    @pytest.fixture
    def sample_items(self):
        """샘플 주문 항목 리스트"""
        buy_order = OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567890",
            orgn_odno="",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="100",
            ord_unpr="70000",
            ord_tmd="093015",
            tot_ccld_qty="100",
            avg_prvs="70000",
            tot_ccld_amt="7000000",
            cncl_yn="N",
        )
        sell_order = OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567891",
            orgn_odno="",
            ord_dvsn_name="시장가",
            sll_buy_dvsn_cd="01",
            sll_buy_dvsn_cd_name="매도",
            pdno="005930",
            prdt_name="삼성전자",
            ord_qty="50",
            ord_unpr="0",
            ord_tmd="140530",
            tot_ccld_qty="50",
            avg_prvs="71000",
            tot_ccld_amt="3550000",
            cncl_yn="N",
        )
        cancelled_order = OrderExecutionItem(
            ord_dt="20231215",
            ord_gno_brno="91234",
            odno="1234567892",
            orgn_odno="1234567890",
            ord_dvsn_name="지정가",
            sll_buy_dvsn_cd="02",
            sll_buy_dvsn_cd_name="매수",
            pdno="035420",
            prdt_name="NAVER",
            ord_qty="10",
            ord_unpr="200000",
            ord_tmd="101500",
            tot_ccld_qty="0",
            avg_prvs="0",
            tot_ccld_amt="0",
            cncl_yn="Y",
        )
        return [buy_order, sell_order, cancelled_order]

    @pytest.fixture
    def sample_summary(self):
        """샘플 요약 데이터"""
        return OrderExecutionSummary(
            tot_ord_qty="160",
            tot_ccld_qty="150",
            tot_ccld_amt="10550000",
            prsm_tlex_smtl="27000",
            pchs_avg_pric="70333.33",
        )

    @pytest.fixture
    def success_response(self, sample_items, sample_summary):
        """성공 응답 fixture"""
        return OrderExecutionResponse(
            rt_cd="0",
            msg_cd="KIOK0001",
            msg1="정상 처리되었습니다.",
            output1=sample_items,
            output2=sample_summary,
        )

    @pytest.fixture
    def error_response(self):
        """오류 응답 fixture"""
        return OrderExecutionResponse(
            rt_cd="1",
            msg_cd="KIOK9999",
            msg1="시스템 오류가 발생했습니다.",
            output1=[],
        )

    def test_is_success_true(self, success_response):
        """is_success - 성공 응답"""
        assert success_response.is_success is True

    def test_is_success_false(self, error_response):
        """is_success - 오류 응답"""
        assert error_response.is_success is False

    def test_has_more_data_false(self, success_response):
        """has_more_data - 연속조회 키 없음"""
        assert success_response.has_more_data is False

    def test_has_more_data_true(self, sample_items):
        """has_more_data - 연속조회 키 있음"""
        response = OrderExecutionResponse(
            rt_cd="0",
            msg_cd="KIOK0001",
            msg1="정상 처리되었습니다.",
            output1=sample_items,
            ctx_area_fk100="NEXT_KEY_123",
        )
        assert response.has_more_data is True

    def test_total_items(self, success_response):
        """total_items 속성 테스트"""
        assert success_response.total_items == 3

    def test_total_items_empty(self, error_response):
        """total_items - 빈 리스트"""
        assert error_response.total_items == 0

    def test_get_buy_orders(self, success_response):
        """get_buy_orders 메서드 테스트"""
        buy_orders = success_response.get_buy_orders()
        assert len(buy_orders) == 2  # 매수 1 + 취소된 매수 1
        for order in buy_orders:
            assert order.is_buy is True

    def test_get_sell_orders(self, success_response):
        """get_sell_orders 메서드 테스트"""
        sell_orders = success_response.get_sell_orders()
        assert len(sell_orders) == 1
        assert sell_orders[0].is_sell is True

    def test_get_executed_orders(self, success_response):
        """get_executed_orders 메서드 테스트"""
        executed_orders = success_response.get_executed_orders()
        assert len(executed_orders) == 2  # 취소된 주문 제외
        for order in executed_orders:
            assert order.is_executed is True

    def test_get_cancelled_orders(self, success_response):
        """get_cancelled_orders 메서드 테스트"""
        cancelled_orders = success_response.get_cancelled_orders()
        assert len(cancelled_orders) == 1
        assert cancelled_orders[0].is_cancelled is True

    def test_get_orders_by_stock(self, success_response):
        """get_orders_by_stock 메서드 테스트"""
        samsung_orders = success_response.get_orders_by_stock("005930")
        assert len(samsung_orders) == 2  # 삼성전자 매수 + 매도

        naver_orders = success_response.get_orders_by_stock("035420")
        assert len(naver_orders) == 1  # NAVER 취소 주문

        kakao_orders = success_response.get_orders_by_stock("035720")
        assert len(kakao_orders) == 0  # 카카오 없음

    def test_from_api_response(self):
        """from_api_response 클래스 메서드 테스트"""
        api_response = {
            "rt_cd": "0",
            "msg_cd": "KIOK0001",
            "msg1": "정상 처리되었습니다.",
            "output1": [
                {
                    "ord_dt": "20231215",
                    "ord_gno_brno": "91234",
                    "odno": "1234567890",
                    "orgn_odno": "",
                    "ord_dvsn_name": "지정가",
                    "sll_buy_dvsn_cd": "02",
                    "sll_buy_dvsn_cd_name": "매수",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "ord_qty": "100",
                    "ord_unpr": "70000",
                    "ord_tmd": "093015",
                    "tot_ccld_qty": "100",
                    "avg_prvs": "70000",
                    "tot_ccld_amt": "7000000",
                    "cncl_yn": "N",
                }
            ],
            "output2": {
                "tot_ord_qty": "100",
                "tot_ccld_qty": "100",
                "tot_ccld_amt": "7000000",
                "prsm_tlex_smtl": "18000",
                "pchs_avg_pric": "70000",
            },
            "CTX_AREA_FK100": "NEXT_KEY",
            "CTX_AREA_NK100": "",
        }

        response = OrderExecutionResponse.from_api_response(api_response)

        assert response.is_success is True
        assert response.msg1 == "정상 처리되었습니다."
        assert response.total_items == 1
        assert response.output1[0].pdno == "005930"
        assert response.output2 is not None
        assert response.output2.total_order_qty == 100
        assert response.ctx_area_fk100 == "NEXT_KEY"
        assert response.has_more_data is True

    def test_from_api_response_without_output2(self):
        """from_api_response - output2 없는 응답"""
        api_response = {
            "rt_cd": "0",
            "msg_cd": "KIOK0001",
            "msg1": "정상 처리되었습니다.",
            "output1": [],
        }

        response = OrderExecutionResponse.from_api_response(api_response)

        assert response.is_success is True
        assert response.output2 is None
        assert response.total_items == 0

    def test_from_api_response_empty_dict(self):
        """from_api_response - 빈 딕셔너리"""
        api_response = {}

        response = OrderExecutionResponse.from_api_response(api_response)

        assert response.rt_cd == ""
        assert response.msg_cd == ""
        assert response.msg1 == ""
        assert response.total_items == 0
