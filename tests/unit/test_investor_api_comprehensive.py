"""
StockInvestorAPI 포괄적 단위 테스트

커버리지 목표: 70% 이상
- get_stock_investor
- get_stock_member
- get_member_transaction
- get_frgnmem_pchs_trend
- get_foreign_broker_net_buy
- _get_foreign_broker_historical
- _get_foreign_broker_current
- get_frgnmem_trade_estimate
- get_frgnmem_trade_trend
- get_investor_program_trade_today
- get_investor_trade_by_stock_daily
- get_investor_trend_estimate

생성일: 2026-01-04
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from kis_agent.stock.investor_api import StockInvestorAPI


class TestGetStockInvestor:
    """get_stock_investor 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_get_stock_investor_success(self):
        """투자자별 매매동향 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "stck_bsop_date": "20260104",
                "prsn_ntby_qty": "100000",
                "frgn_ntby_qty": "-50000",
                "orgn_ntby_qty": "-50000",
            },
        }

        result = self.api.get_stock_investor(ticker="005930")

        assert result is not None
        assert result["rt_cd"] == "0"

    def test_get_stock_investor_params(self):
        """투자자별 매매동향 - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_stock_investor(ticker="035420")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "035420"
        assert params["FID_COND_MRKT_DIV_CODE"] == "J"

    def test_get_stock_investor_retries_ignored(self):
        """투자자별 매매동향 - retries 파라미터 (호환성)"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # retries는 호환성을 위해 유지되지만 사용되지 않음
        result = self.api.get_stock_investor(ticker="005930", retries=5)

        assert result is not None


class TestGetStockMember:
    """get_stock_member 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_get_stock_member_success(self):
        """거래원별 매매 정보 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "seln_mbcr_name1": "메리츠증권",
                "shnu_mbcr_name1": "미래에셋증권",
            },
        }

        result = self.api.get_stock_member(ticker="005930")

        assert result is not None
        assert result["rt_cd"] == "0"

    def test_get_stock_member_params(self):
        """거래원별 매매 정보 - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_stock_member(ticker="035420")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "035420"


class TestGetMemberTransaction:
    """get_member_transaction 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_get_member_transaction_success(self):
        """특정 거래원 매매 내역 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"transaction_data": "test"},
        }

        result = self.api.get_member_transaction(code="005930", mem_code="99999")

        assert result is not None

    def test_get_member_transaction_params(self):
        """특정 거래원 매매 내역 - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_member_transaction(code="035420", mem_code="12345")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "035420"
        assert params["FID_INPUT_MEM_CODE"] == "12345"


class TestGetFrgnmemPchsTrend:
    """get_frgnmem_pchs_trend 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_get_frgnmem_pchs_trend_success(self):
        """외국인 매수 추이 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"trend_data": "test"},
        }

        result = self.api.get_frgnmem_pchs_trend(code="005930")

        assert result is not None

    def test_get_frgnmem_pchs_trend_params(self):
        """외국인 매수 추이 - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_frgnmem_pchs_trend(code="035420")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "035420"
        assert params["fid_input_iscd_2"] == "99999"


class TestGetForeignBrokerNetBuy:
    """get_foreign_broker_net_buy 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_get_foreign_broker_current_day(self):
        """외국계 순매수 - 당일"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "seln_mbcr_name1": "모건스탠리",
                "seln_mbcr_glob_yn_1": "Y",
                "total_seln_qty1": "10000",
                "shnu_mbcr_name1": "골드만삭스",
                "shnu_mbcr_glob_yn_1": "Y",
                "total_shnu_qty1": "15000",
            },
        }

        # 날짜 없이 호출 (당일)
        result = self.api.get_foreign_broker_net_buy(code="005930")

        assert result is not None
        net_buy, details = result
        assert net_buy == 5000  # 15000 - 10000
        assert details["buy_total"] == 15000
        assert details["sell_total"] == 10000

    @patch("pykis.stock.investor_api.datetime")
    def test_get_foreign_broker_historical(self, mock_datetime):
        """외국계 순매수 - 과거 날짜"""
        mock_datetime.now.return_value.strftime.return_value = "20260104"

        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20260102",
                    "frgn_ntby_qty": "50000",
                    "frgn_shnu_vol": "100000",
                    "frgn_seln_vol": "50000",
                },
            ],
        }

        result = self.api.get_foreign_broker_net_buy(code="005930", date="20260102")

        assert result is not None
        net_buy, details = result
        assert net_buy == 50000
        assert details["api_method"] == "stock_investor"

    def test_get_foreign_broker_no_member_data(self):
        """외국계 순매수 - 거래원 데이터 없음"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "1",
            "msg1": "데이터 없음",
        }

        result = self.api.get_foreign_broker_net_buy(code="005930")

        assert result is None


class TestGetForeignBrokerHistorical:
    """_get_foreign_broker_historical 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_historical_success(self):
        """과거 외국인 순매수 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20260102",
                    "frgn_ntby_qty": "100000",
                    "frgn_shnu_vol": "150000",
                    "frgn_seln_vol": "50000",
                },
            ],
        }

        result = self.api._get_foreign_broker_historical(code="005930", date="20260102")

        assert result is not None
        net_buy, details = result
        assert net_buy == 100000

    def test_historical_date_not_found(self):
        """과거 외국인 순매수 - 날짜 없음"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"stck_bsop_date": "20260103", "frgn_ntby_qty": "50000"},
            ],
        }

        result = self.api._get_foreign_broker_historical(code="005930", date="20260101")

        assert result is None

    def test_historical_no_output(self):
        """과거 외국인 순매수 - output 없음"""
        self.mock_client.make_request.return_value = {"rt_cd": "0"}

        result = self.api._get_foreign_broker_historical(code="005930", date="20260102")

        assert result is None

    def test_historical_single_dict_output(self):
        """과거 외국인 순매수 - output이 dict인 경우"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "stck_bsop_date": "20260102",
                "frgn_ntby_qty": "75000",
                "frgn_shnu_vol": "100000",
                "frgn_seln_vol": "25000",
            },
        }

        result = self.api._get_foreign_broker_historical(code="005930", date="20260102")

        assert result is not None
        net_buy, _ = result
        assert net_buy == 75000

    def test_historical_exception(self):
        """과거 외국인 순매수 - 예외 발생"""
        self.mock_client.make_request.side_effect = Exception("API 오류")

        result = self.api._get_foreign_broker_historical(code="005930", date="20260102")

        assert result is None


class TestGetForeignBrokerCurrent:
    """_get_foreign_broker_current 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_current_multiple_foreign_brokers(self):
        """당일 외국계 순매수 - 여러 외국계 증권사"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                # 매도 외국계
                "seln_mbcr_name1": "모건스탠리",
                "seln_mbcr_glob_yn_1": "Y",
                "total_seln_qty1": "10000",
                "seln_mbcr_name2": "골드만삭스",
                "seln_mbcr_glob_yn_2": "Y",
                "total_seln_qty2": "5000",
                # 매수 외국계
                "shnu_mbcr_name1": "JP모건",
                "shnu_mbcr_glob_yn_1": "Y",
                "total_shnu_qty1": "20000",
                "shnu_mbcr_name2": "UBS",
                "shnu_mbcr_glob_yn_2": "Y",
                "total_shnu_qty2": "8000",
            },
        }

        result = self.api._get_foreign_broker_current(code="005930")

        assert result is not None
        net_buy, details = result
        # 매수: 20000 + 8000 = 28000
        # 매도: 10000 + 5000 = 15000
        assert net_buy == 13000
        assert len(details["brokers"]) == 4

    def test_current_no_foreign_brokers(self):
        """당일 외국계 순매수 - 외국계 증권사 없음"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "seln_mbcr_name1": "삼성증권",
                "seln_mbcr_glob_yn_1": "N",
                "total_seln_qty1": "10000",
                "shnu_mbcr_name1": "미래에셋",
                "shnu_mbcr_glob_yn_1": "N",
                "total_shnu_qty1": "15000",
            },
        }

        result = self.api._get_foreign_broker_current(code="005930")

        assert result is not None
        net_buy, details = result
        assert net_buy == 0
        assert len(details["brokers"]) == 0

    def test_current_empty_broker_name(self):
        """당일 외국계 순매수 - 빈 거래원명"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "seln_mbcr_name1": "",  # 빈 이름
                "seln_mbcr_glob_yn_1": "Y",
                "total_seln_qty1": "10000",
            },
        }

        result = self.api._get_foreign_broker_current(code="005930")

        assert result is not None
        _, details = result
        assert len(details["brokers"]) == 0  # 빈 이름은 무시

    def test_current_zero_volume(self):
        """당일 외국계 순매수 - 거래량 0"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "seln_mbcr_name1": "모건스탠리",
                "seln_mbcr_glob_yn_1": "Y",
                "total_seln_qty1": "0",  # 거래량 0
            },
        }

        result = self.api._get_foreign_broker_current(code="005930")

        assert result is not None
        _, details = result
        assert len(details["brokers"]) == 0  # 거래량 0은 무시

    def test_current_no_output(self):
        """당일 외국계 순매수 - output 없음"""
        self.mock_client.make_request.return_value = {"rt_cd": "0"}

        result = self.api._get_foreign_broker_current(code="005930")

        assert result is None

    def test_current_exception(self):
        """당일 외국계 순매수 - 예외 발생"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"invalid": "data"},  # 예상치 못한 구조
        }
        # 정상적인 경우 예외 없이 처리됨
        result = self.api._get_foreign_broker_current(code="005930")

        assert result is not None


class TestGetFrgnmemTradeEstimate:
    """get_frgnmem_trade_estimate 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_trade_estimate_success(self):
        """외국계 매매종목 가집계 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"estimate_data": "test"},
        }

        result = self.api.get_frgnmem_trade_estimate()

        assert result is not None

    def test_trade_estimate_custom_params(self):
        """외국계 매매종목 가집계 - 커스텀 파라미터"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_frgnmem_trade_estimate(
            fid_cond_mrkt_div_code="J",
            fid_cond_scr_div_code="16441",
            fid_input_iscd="1001",  # 코스피
            fid_rank_sort_cls_code="1",  # 수량순
            fid_rank_sort_cls_code_2="1",  # 매도순
        )

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "1001"
        assert params["FID_RANK_SORT_CLS_CODE"] == "1"


class TestGetFrgnmemTradeTrend:
    """get_frgnmem_trade_trend 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_trade_trend_success(self):
        """회원사 실시간 매매동향 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"trend_data": "test"},
        }

        result = self.api.get_frgnmem_trade_trend(fid_input_iscd="005930")

        assert result is not None

    def test_trade_trend_custom_params(self):
        """회원사 실시간 매매동향 - 커스텀 파라미터"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_frgnmem_trade_trend(
            fid_cond_scr_div_code="20432",
            fid_cond_mrkt_div_code="J",
            fid_input_iscd="035420",
            fid_input_iscd_2="12345",
            fid_mrkt_cls_code="K",  # 코스피
            fid_vol_cnt="10000",
        )

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "035420"
        assert params["FID_MRKT_CLS_CODE"] == "K"


class TestGetInvestorProgramTradeToday:
    """get_investor_program_trade_today 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_program_trade_kospi(self):
        """프로그램매매 투자자매매동향 - 코스피"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"program_data": "test"},
        }

        result = self.api.get_investor_program_trade_today(mrkt_div_cls_code="1")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["MRKT_DIV_CLS_CODE"] == "1"

    def test_program_trade_kosdaq(self):
        """프로그램매매 투자자매매동향 - 코스닥"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        result = self.api.get_investor_program_trade_today(mrkt_div_cls_code="4")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["MRKT_DIV_CLS_CODE"] == "4"


class TestGetInvestorTradeByStockDaily:
    """get_investor_trade_by_stock_daily 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_trade_by_stock_daily_success(self):
        """종목별 투자자매매동향(일별) - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"daily_data": "test"},
        }

        result = self.api.get_investor_trade_by_stock_daily(
            fid_input_iscd="005930", fid_input_date_1="20260104"
        )

        assert result is not None

    def test_trade_by_stock_daily_params(self):
        """종목별 투자자매매동향(일별) - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_investor_trade_by_stock_daily(
            fid_cond_mrkt_div_code="J",
            fid_input_iscd="035420",
            fid_input_date_1="20260103",
            fid_org_adj_prc="0",
            fid_etc_cls_code="",
        )

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "035420"
        assert params["FID_INPUT_DATE_1"] == "20260103"


class TestGetInvestorTrendEstimate:
    """get_investor_trend_estimate 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockInvestorAPI(client=self.mock_client, enable_cache=False)

    def test_trend_estimate_success(self):
        """외국인/기관 추정가집계 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"estimate_data": "test"},
        }

        result = self.api.get_investor_trend_estimate(mksc_shrn_iscd="005930")

        assert result is not None

    def test_trend_estimate_params(self):
        """외국인/기관 추정가집계 - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_investor_trend_estimate(mksc_shrn_iscd="035420")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["MKSC_SHRN_ISCD"] == "035420"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
