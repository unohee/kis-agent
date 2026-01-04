"""
Stock API Facade 모듈 테스트

Facade Pattern이 적용된 주식 API 통합 인터페이스를 테스트합니다.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from pykis.core.client import KISClient
from pykis.stock.api_facade import StockAPI, StockAPIFacade


class TestStockAPIFacade(unittest.TestCase):
    """StockAPI Facade 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"account_no": "12345", "account_code": "01"}

        with patch("pykis.stock.api_facade.StockPriceAPI"), patch(
            "pykis.stock.api_facade.StockMarketAPI"
        ), patch("pykis.stock.api_facade.StockInvestorAPI"):
            self.api = StockAPI(
                client=self.mock_client,
                account_info=self.account_info,
                enable_cache=False,
            )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account, self.account_info)

        # 하위 시스템이 생성되었는지 확인
        self.assertIsNotNone(self.api.price_api)
        self.assertIsNotNone(self.api.market_api)
        self.assertIsNotNone(self.api.investor_api)

    def test_init_without_account_info(self):
        """계좌 정보 없이 초기화"""
        with patch("pykis.stock.api_facade.StockPriceAPI"), patch(
            "pykis.stock.api_facade.StockMarketAPI"
        ), patch("pykis.stock.api_facade.StockInvestorAPI"):
            api = StockAPI(client=self.mock_client)
            self.assertEqual(api.client, self.mock_client)
            self.assertIsNone(api.account)

    def test_get_stock_price_delegation(self):
        """get_stock_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.api.price_api.get_stock_price = Mock(return_value=expected_result)

        result = self.api.get_stock_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_stock_price.assert_called_once_with("005930")

    def test_inquire_daily_price_delegation(self):
        """inquire_daily_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_bsop_date": "20231215"}]}
        self.api.price_api.inquire_daily_price = Mock(return_value=expected_result)

        result = self.api.inquire_daily_price("005930", period="W", org_adj_prc="0")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_daily_price.assert_called_once_with(
            "005930", "W", "0"
        )

    def test_inquire_daily_price_default_params(self):
        """inquire_daily_price 기본 파라미터 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.price_api.inquire_daily_price = Mock(return_value=expected_result)

        result = self.api.inquire_daily_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_daily_price.assert_called_once_with(
            "005930", "D", "1"
        )

    def test_get_orderbook_delegation(self):
        """get_orderbook 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"askp1": "70100"}}
        self.api.price_api.get_orderbook = Mock(return_value=expected_result)

        result = self.api.get_orderbook("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_orderbook.assert_called_once_with("005930")

    def test_get_orderbook_raw_delegation(self):
        """get_orderbook_raw 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"raw": "data"}}
        self.api.price_api.get_orderbook_raw = Mock(return_value=expected_result)

        result = self.api.get_orderbook_raw("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_orderbook_raw.assert_called_once_with("005930")

    def test_get_minute_price_delegation(self):
        """get_minute_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_cntg_hour": "153000"}]}
        self.api.price_api.get_minute_price = Mock(return_value=expected_result)

        result = self.api.get_minute_price("005930", hour="120000")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_minute_price.assert_called_once_with("005930", "120000")

    def test_get_minute_price_default_hour(self):
        """get_minute_price 기본 시간 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.price_api.get_minute_price = Mock(return_value=expected_result)

        result = self.api.get_minute_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_minute_price.assert_called_once_with("005930", "153000")

    def test_get_daily_minute_price_delegation(self):
        """get_daily_minute_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_bsop_date": "20231215"}]}
        self.api.price_api.get_daily_minute_price = Mock(return_value=expected_result)

        result = self.api.get_daily_minute_price("005930", "20231215", hour="090000")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_minute_price.assert_called_once_with(
            "005930", "20231215", "090000"
        )

    def test_get_daily_minute_price_default_hour(self):
        """get_daily_minute_price 기본 시간 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.price_api.get_daily_minute_price = Mock(return_value=expected_result)

        result = self.api.get_daily_minute_price("005930", "20231215")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_minute_price.assert_called_once_with(
            "005930", "20231215", "153000"
        )

    def test_get_market_fluctuation_delegation(self):
        """get_market_fluctuation 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"market_data": "test"}}
        self.api.market_api.get_market_fluctuation = Mock(return_value=expected_result)

        result = self.api.get_market_fluctuation()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_market_fluctuation.assert_called_once()

    def test_get_market_rankings_delegation(self):
        """get_market_rankings 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"rank": 1}]}
        self.api.market_api.get_market_rankings = Mock(return_value=expected_result)

        result = self.api.get_market_rankings(volume=10000000)

        self.assertEqual(result, expected_result)
        self.api.market_api.get_market_rankings.assert_called_once_with(10000000)

    def test_get_market_rankings_default_volume(self):
        """get_market_rankings 기본 거래량 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.market_api.get_market_rankings = Mock(return_value=expected_result)

        result = self.api.get_market_rankings()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_market_rankings.assert_called_once_with(5000000)

    def test_get_volume_power_delegation(self):
        """get_volume_power 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"code": "005930"}]}
        self.api.market_api.get_volume_power = Mock(return_value=expected_result)

        result = self.api.get_volume_power(volume=1000000)

        self.assertEqual(result, expected_result)
        self.api.market_api.get_volume_power.assert_called_once_with(1000000)

    def test_get_volume_power_default_volume(self):
        """get_volume_power 기본 거래량 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.market_api.get_volume_power = Mock(return_value=expected_result)

        result = self.api.get_volume_power()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_volume_power.assert_called_once_with(0)

    def test_get_stock_info_delegation(self):
        """get_stock_info 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"name": "삼성전자"}}
        self.api.market_api.get_stock_info = Mock(return_value=expected_result)

        result = self.api.get_stock_info("005930")

        self.assertEqual(result, expected_result)
        self.api.market_api.get_stock_info.assert_called_once_with("005930")

    def test_get_stock_investor_delegation(self):
        """get_stock_investor 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"investor_data": "test"}}
        self.api.investor_api.get_stock_investor = Mock(return_value=expected_result)

        result = self.api.get_stock_investor(
            ticker="005930", retries=5, force_refresh=True
        )

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_investor.assert_called_once_with(
            "005930", 5, True
        )

    def test_get_stock_investor_default_params(self):
        """get_stock_investor 기본 파라미터 테스트"""
        expected_result = {"rt_cd": "0", "output": {}}
        self.api.investor_api.get_stock_investor = Mock(return_value=expected_result)

        result = self.api.get_stock_investor()

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_investor.assert_called_once_with("", 10, False)

    def test_get_stock_member_delegation(self):
        """get_stock_member 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"member_data": "test"}}
        self.api.investor_api.get_stock_member = Mock(return_value=expected_result)

        result = self.api.get_stock_member("005930", retries=5)

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_member.assert_called_once_with("005930", 5)

    def test_get_stock_member_default_retries(self):
        """get_stock_member 기본 재시도 횟수 테스트"""
        expected_result = {"rt_cd": "0", "output": {}}
        self.api.investor_api.get_stock_member = Mock(return_value=expected_result)

        result = self.api.get_stock_member("005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_member.assert_called_once_with("005930", 10)

    def test_get_member_transaction_delegation(self):
        """get_member_transaction 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"transaction_data": "test"}}
        self.api.investor_api.get_member_transaction = Mock(
            return_value=expected_result
        )

        result = self.api.get_member_transaction("005930", "001")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_member_transaction.assert_called_once_with(
            "005930", "001"
        )

    def test_get_frgnmem_pchs_trend_delegation(self):
        """get_frgnmem_pchs_trend 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"trend_data": "test"}}
        self.api.investor_api.get_frgnmem_pchs_trend = Mock(
            return_value=expected_result
        )

        result = self.api.get_frgnmem_pchs_trend("005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_frgnmem_pchs_trend.assert_called_once_with("005930")

    def test_get_foreign_broker_net_buy_delegation(self):
        """get_foreign_broker_net_buy 메서드 위임 테스트"""
        expected_result = ("broker_data", {"net_buy": 1000})
        self.api.investor_api.get_foreign_broker_net_buy = Mock(
            return_value=expected_result
        )

        foreign_brokers = ["morgan", "goldman"]
        result = self.api.get_foreign_broker_net_buy(
            "005930", foreign_brokers, "20231215"
        )

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_foreign_broker_net_buy.assert_called_once_with(
            "005930", foreign_brokers, "20231215"
        )

    def test_get_foreign_broker_net_buy_default_params(self):
        """get_foreign_broker_net_buy 기본 파라미터 테스트"""
        expected_result = ("data", {})
        self.api.investor_api.get_foreign_broker_net_buy = Mock(
            return_value=expected_result
        )

        result = self.api.get_foreign_broker_net_buy("005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_foreign_broker_net_buy.assert_called_once_with(
            "005930", None, None
        )

    def test_facade_pattern_integration(self):
        """Facade 패턴 통합 테스트"""
        # 각 하위 시스템의 응답 설정
        price_response = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        market_response = {"rt_cd": "0", "output": {"market_data": "test"}}
        investor_response = {"rt_cd": "0", "output": {"investor_data": "test"}}

        self.api.price_api.get_stock_price = Mock(return_value=price_response)
        self.api.market_api.get_market_fluctuation = Mock(return_value=market_response)
        self.api.investor_api.get_stock_investor = Mock(return_value=investor_response)

        # 각 하위 시스템 호출
        price_result = self.api.get_stock_price("005930")
        market_result = self.api.get_market_fluctuation()
        investor_result = self.api.get_stock_investor("005930")

        # 결과 검증
        self.assertEqual(price_result, price_response)
        self.assertEqual(market_result, market_response)
        self.assertEqual(investor_result, investor_response)

        # 각 하위 시스템이 호출되었는지 확인
        self.api.price_api.get_stock_price.assert_called_once()
        self.api.market_api.get_market_fluctuation.assert_called_once()
        self.api.investor_api.get_stock_investor.assert_called_once()

    def test_stock_api_facade_alias(self):
        """StockAPIFacade 별칭 테스트"""
        self.assertIs(StockAPIFacade, StockAPI)

    # ===== 추가 Price API 위임 테스트 =====

    def test_inquire_daily_itemchartprice_delegation(self):
        """inquire_daily_itemchartprice 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_bsop_date": "20231201"}]}
        self.api.price_api.inquire_daily_itemchartprice = Mock(
            return_value=expected_result
        )

        result = self.api.inquire_daily_itemchartprice(
            "005930", start_date="20231201", end_date="20231215", period="D"
        )

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_daily_itemchartprice.assert_called_once_with(
            "005930", "20231201", "20231215", "D", "1"
        )

    def test_inquire_price_delegation(self):
        """inquire_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.api.price_api.inquire_price = Mock(return_value=expected_result)

        result = self.api.inquire_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_price.assert_called_once_with("005930", "J")

    def test_inquire_price_2_delegation(self):
        """inquire_price_2 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.api.price_api.inquire_price_2 = Mock(return_value=expected_result)

        result = self.api.inquire_price_2("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_price_2.assert_called_once_with("005930", "J")

    def test_inquire_ccnl_delegation(self):
        """inquire_ccnl 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_cntg_hour": "100000"}]}
        self.api.price_api.inquire_ccnl = Mock(return_value=expected_result)

        result = self.api.inquire_ccnl("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_ccnl.assert_called_once_with("005930", "J")

    def test_inquire_time_itemconclusion_delegation(self):
        """inquire_time_itemconclusion 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_cntg_hour": "120000"}]}
        self.api.price_api.inquire_time_itemconclusion = Mock(
            return_value=expected_result
        )

        result = self.api.inquire_time_itemconclusion("005930", hour="120000")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_time_itemconclusion.assert_called_once_with(
            "005930", "120000", "J"
        )

    def test_inquire_index_price_delegation(self):
        """inquire_index_price 메서드 위임 테스트 (deprecated)"""
        expected_result = {"rt_cd": "0", "output": {"bstp_nmix_prpr": "2500.00"}}
        self.api.price_api.inquire_index_price = Mock(return_value=expected_result)

        result = self.api.inquire_index_price("0001")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_index_price.assert_called_once_with("0001", "U")

    def test_inquire_index_tickprice_delegation(self):
        """inquire_index_tickprice 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"bstp_nmix_prpr": "2500.00"}]}
        self.api.price_api.inquire_index_tickprice = Mock(return_value=expected_result)

        result = self.api.inquire_index_tickprice("0001")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_index_tickprice.assert_called_once_with("0001", "U")

    def test_inquire_index_timeprice_delegation(self):
        """inquire_index_timeprice 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"bstp_nmix_prpr": "2500.00"}]}
        self.api.price_api.inquire_index_timeprice = Mock(return_value=expected_result)

        result = self.api.inquire_index_timeprice("0001", time_div="1")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_index_timeprice.assert_called_once_with(
            "0001", "U", "1"
        )

    def test_inquire_index_category_price_delegation(self):
        """inquire_index_category_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"bstp_nmix_prpr": "2500.00"}]}
        self.api.price_api.inquire_index_category_price = Mock(
            return_value=expected_result
        )

        result = self.api.inquire_index_category_price("0001")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_index_category_price.assert_called_once_with(
            "0001", "20214", "K", "0", "U"
        )

    def test_inquire_daily_overtimeprice_delegation(self):
        """inquire_daily_overtimeprice 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_prpr": "70000"}]}
        self.api.price_api.inquire_daily_overtimeprice = Mock(
            return_value=expected_result
        )

        result = self.api.inquire_daily_overtimeprice("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_daily_overtimeprice.assert_called_once_with(
            "005930", "J"
        )

    def test_inquire_elw_price_delegation(self):
        """inquire_elw_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"elw_prpr": "1000"}}
        self.api.price_api.inquire_elw_price = Mock(return_value=expected_result)

        result = self.api.inquire_elw_price("580001")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_elw_price.assert_called_once_with("580001", "W")

    def test_inquire_overtime_asking_price_delegation(self):
        """inquire_overtime_asking_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"askp1": "70100"}}
        self.api.price_api.inquire_overtime_asking_price = Mock(
            return_value=expected_result
        )

        result = self.api.inquire_overtime_asking_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_overtime_asking_price.assert_called_once_with(
            "005930", "J"
        )

    def test_inquire_overtime_price_delegation(self):
        """inquire_overtime_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.api.price_api.inquire_overtime_price = Mock(return_value=expected_result)

        result = self.api.inquire_overtime_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_overtime_price.assert_called_once_with("005930", "J")

    def test_inquire_vi_status_delegation(self):
        """inquire_vi_status 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.inquire_vi_status = Mock(return_value=expected_result)

        result = self.api.inquire_vi_status()

        self.assertEqual(result, expected_result)
        self.api.price_api.inquire_vi_status.assert_called_once()

    def test_get_intraday_price_delegation(self):
        """get_intraday_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_cntg_hour": "090100"}]}
        self.api.price_api.get_intraday_price = Mock(return_value=expected_result)

        result = self.api.get_intraday_price("005930", "20231215")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_intraday_price.assert_called_once_with(
            "005930", "20231215"
        )

    def test_get_stock_ccnl_delegation(self):
        """get_stock_ccnl 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_cntg_hour": "090000"}]}
        self.api.price_api.get_stock_ccnl = Mock(return_value=expected_result)

        result = self.api.get_stock_ccnl("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_stock_ccnl.assert_called_once_with("005930", 10)

    def test_daily_credit_balance_delegation(self):
        """daily_credit_balance 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"crdt_rate": "10.5"}]}
        self.api.price_api.daily_credit_balance = Mock(return_value=expected_result)

        result = self.api.daily_credit_balance("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.daily_credit_balance.assert_called_once_with(
            "005930", "J", "20476", ""
        )

    def test_disparity_delegation(self):
        """disparity 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.disparity = Mock(return_value=expected_result)

        result = self.api.disparity()

        self.assertEqual(result, expected_result)
        self.api.price_api.disparity.assert_called_once()

    def test_dividend_rate_delegation(self):
        """dividend_rate 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.dividend_rate = Mock(return_value=expected_result)

        result = self.api.dividend_rate()

        self.assertEqual(result, expected_result)
        self.api.price_api.dividend_rate.assert_called_once()

    def test_fluctuation_delegation(self):
        """fluctuation 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.fluctuation = Mock(return_value=expected_result)

        result = self.api.fluctuation()

        self.assertEqual(result, expected_result)
        self.api.price_api.fluctuation.assert_called_once()

    def test_foreign_institution_total_delegation(self):
        """foreign_institution_total 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"frgn_ntby_qty": "1000"}]}
        self.api.price_api.foreign_institution_total = Mock(
            return_value=expected_result
        )

        result = self.api.foreign_institution_total()

        self.assertEqual(result, expected_result)
        self.api.price_api.foreign_institution_total.assert_called_once()

    def test_intstock_multprice_delegation(self):
        """intstock_multprice 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_prpr": "70000"}]}
        self.api.price_api.intstock_multprice = Mock(return_value=expected_result)

        result = self.api.intstock_multprice("005930,035420")

        self.assertEqual(result, expected_result)
        self.api.price_api.intstock_multprice.assert_called_once_with(
            "005930,035420", "J"
        )

    def test_market_cap_delegation(self):
        """market_cap 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.market_cap = Mock(return_value=expected_result)

        result = self.api.market_cap()

        self.assertEqual(result, expected_result)
        self.api.price_api.market_cap.assert_called_once()

    def test_market_time_delegation(self):
        """market_time 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"opng_time": "090000"}}
        self.api.price_api.market_time = Mock(return_value=expected_result)

        result = self.api.market_time()

        self.assertEqual(result, expected_result)
        self.api.price_api.market_time.assert_called_once()

    def test_market_value_delegation(self):
        """market_value 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"mrkt_value": "1000000000000"}}
        self.api.price_api.market_value = Mock(return_value=expected_result)

        result = self.api.market_value("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.market_value.assert_called_once_with("005930", "J")

    def test_news_title_delegation(self):
        """news_title 메서드 위임 테스트"""
        expected_result = {
            "rt_cd": "0",
            "output": [{"news_title": "삼성전자 실적발표"}],
        }
        self.api.price_api.news_title = Mock(return_value=expected_result)

        result = self.api.news_title("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.news_title.assert_called_once()

    def test_profit_asset_index_delegation(self):
        """profit_asset_index 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"bstp_nmix_prpr": "2500.00"}}
        self.api.price_api.profit_asset_index = Mock(return_value=expected_result)

        result = self.api.profit_asset_index("0001")

        self.assertEqual(result, expected_result)
        self.api.price_api.profit_asset_index.assert_called_once_with("0001", "U")

    def test_search_stock_info_delegation(self):
        """search_stock_info 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"std_pdno": "005930"}}
        self.api.price_api.search_stock_info = Mock(return_value=expected_result)

        result = self.api.search_stock_info("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.search_stock_info.assert_called_once_with("005930", "300")

    def test_short_sale_delegation(self):
        """short_sale 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.short_sale = Mock(return_value=expected_result)

        result = self.api.short_sale()

        self.assertEqual(result, expected_result)
        self.api.price_api.short_sale.assert_called_once()

    def test_volume_rank_delegation(self):
        """volume_rank 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.price_api.volume_rank = Mock(return_value=expected_result)

        result = self.api.volume_rank()

        self.assertEqual(result, expected_result)
        self.api.price_api.volume_rank.assert_called_once()

    # ===== 추가 Investor API 위임 테스트 =====

    def test_get_frgnmem_trade_estimate_delegation(self):
        """get_frgnmem_trade_estimate 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"frgn_ntby_qty": "1000"}]}
        self.api.investor_api.get_frgnmem_trade_estimate = Mock(
            return_value=expected_result
        )

        result = self.api.get_frgnmem_trade_estimate()

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_frgnmem_trade_estimate.assert_called_once()

    def test_get_frgnmem_trade_trend_delegation(self):
        """get_frgnmem_trade_trend 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"frgn_ntby_qty": "1000"}]}
        self.api.investor_api.get_frgnmem_trade_trend = Mock(
            return_value=expected_result
        )

        result = self.api.get_frgnmem_trade_trend()

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_frgnmem_trade_trend.assert_called_once()

    def test_get_investor_program_trade_today_delegation(self):
        """get_investor_program_trade_today 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"prgm_ntby_qty": "5000"}]}
        self.api.investor_api.get_investor_program_trade_today = Mock(
            return_value=expected_result
        )

        result = self.api.get_investor_program_trade_today()

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_investor_program_trade_today.assert_called_once_with(
            "1"
        )

    def test_get_investor_trade_by_stock_daily_delegation(self):
        """get_investor_trade_by_stock_daily 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"frgn_ntby_qty": "1000"}]}
        self.api.investor_api.get_investor_trade_by_stock_daily = Mock(
            return_value=expected_result
        )

        result = self.api.get_investor_trade_by_stock_daily(fid_input_iscd="005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_investor_trade_by_stock_daily.assert_called_once()

    def test_get_investor_trend_estimate_delegation(self):
        """get_investor_trend_estimate 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"frgn_ntby_qty": "1000"}}
        self.api.investor_api.get_investor_trend_estimate = Mock(
            return_value=expected_result
        )

        result = self.api.get_investor_trend_estimate("005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_investor_trend_estimate.assert_called_once_with(
            "005930"
        )

    # ===== 추가 Market API 위임 테스트 =====

    def test_get_holiday_info_delegation(self):
        """get_holiday_info 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"bass_dt": "20231225"}]}
        self.api.market_api.get_holiday_info = Mock(return_value=expected_result)

        result = self.api.get_holiday_info("20231201")

        self.assertEqual(result, expected_result)
        self.api.market_api.get_holiday_info.assert_called_once_with("20231201")

    def test_is_holiday_delegation(self):
        """is_holiday 메서드 위임 테스트"""
        self.api.market_api.is_holiday = Mock(return_value=True)

        result = self.api.is_holiday("20231225")

        self.assertTrue(result)
        self.api.market_api.is_holiday.assert_called_once_with("20231225")

    def test_get_pbar_tratio_delegation(self):
        """get_pbar_tratio 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"pbar_data": "test"}}
        self.api.market_api.get_pbar_tratio = Mock(return_value=expected_result)

        result = self.api.get_pbar_tratio("005930")

        self.assertEqual(result, expected_result)
        self.api.market_api.get_pbar_tratio.assert_called_once_with("005930", 10)

    def test_get_fluctuation_rank_delegation(self):
        """get_fluctuation_rank 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.market_api.get_fluctuation_rank = Mock(return_value=expected_result)

        result = self.api.get_fluctuation_rank()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_fluctuation_rank.assert_called_once()

    def test_get_volume_power_rank_delegation(self):
        """get_volume_power_rank 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.market_api.get_volume_power_rank = Mock(return_value=expected_result)

        result = self.api.get_volume_power_rank()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_volume_power_rank.assert_called_once()

    def test_get_volume_rank_market_api_delegation(self):
        """get_volume_rank (Market API) 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_shrn_iscd": "005930"}]}
        self.api.market_api.get_volume_rank = Mock(return_value=expected_result)

        result = self.api.get_volume_rank()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_volume_rank.assert_called_once()

    # ===== 직접 구현 메서드 테스트 =====

    def test_get_index_minute_data_direct(self):
        """get_index_minute_data 직접 구현 테스트"""
        expected_result = {
            "output1": {"bstp_nmix_prpr": "2500.00"},
            "output2": [{"stck_cntg_hour": "120000"}],
        }
        self.mock_client.make_request.return_value = expected_result

        result = self.api.get_index_minute_data("0001")

        self.assertIn("rt_cd", result)
        self.assertIn("msg1", result)
        self.mock_client.make_request.assert_called_once()

    def test_get_index_timeprice_delegation(self):
        """get_index_timeprice 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output1": {}, "output2": []}
        self.api.price_api.get_index_timeprice = Mock(return_value=expected_result)

        result = self.api.get_index_timeprice("1029")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_index_timeprice.assert_called_once_with(
            "1029", "600", "U"
        )

    def test_get_future_option_price_delegation(self):
        """get_future_option_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"fuop_prpr": "350.00"}}
        self.api.price_api.get_future_option_price = Mock(return_value=expected_result)

        result = self.api.get_future_option_price("F")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_future_option_price.assert_called_once_with("F", None)

    # ===== __getattr__ 동적 위임 테스트 =====

    def test_getattr_price_api_delegation(self):
        """__getattr__를 통한 price_api 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"test": "data"}}
        self.api.price_api.some_undelegated_method = Mock(return_value=expected_result)

        result = self.api.some_undelegated_method()

        self.assertEqual(result, expected_result)
        self.api.price_api.some_undelegated_method.assert_called_once()

    def test_getattr_market_api_delegation(self):
        """__getattr__를 통한 market_api 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"test": "market_data"}}

        # price_api에 없는 메서드
        del self.api.price_api.market_only_method
        self.api.market_api.market_only_method = Mock(return_value=expected_result)

        result = self.api.market_only_method()

        self.assertEqual(result, expected_result)
        self.api.market_api.market_only_method.assert_called_once()

    def test_getattr_checks_all_apis(self):
        """__getattr__가 모든 하위 API를 순서대로 확인하는지 테스트"""
        # price_api에 메서드가 있으면 그것을 사용
        expected_result = {"rt_cd": "0", "output": {"from": "price_api"}}
        self.api.price_api.test_method = Mock(return_value=expected_result)

        result = self.api.test_method()

        self.assertEqual(result, expected_result)
        self.api.price_api.test_method.assert_called_once()


if __name__ == "__main__":
    unittest.main()
