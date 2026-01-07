"""
OverseasRankingAPI 단위 테스트

해외주식 순위 API의 동작을 검증합니다.
"""

import unittest
from unittest.mock import MagicMock, Mock

import pytest


class TestOverseasRankingAPIInit(unittest.TestCase):
    """OverseasRankingAPI 초기화 테스트"""

    def test_init_with_client(self):
        """클라이언트만으로 초기화"""
        from pykis.overseas.ranking_api import OverseasRankingAPI

        mock_client = MagicMock()
        api = OverseasRankingAPI(client=mock_client)
        self.assertEqual(api.client, mock_client)
        self.assertIsNone(api.account)

    def test_init_with_account(self):
        """계좌 정보와 함께 초기화"""
        from pykis.overseas.ranking_api import OverseasRankingAPI

        mock_client = MagicMock()
        account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        api = OverseasRankingAPI(client=mock_client, account_info=account_info)
        self.assertEqual(api.account, account_info)


class TestTradeVolumeRanking(unittest.TestCase):
    """거래량순위 테스트"""

    def setUp(self):
        """테스트 설정"""
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_trade_volume_ranking_success(self):
        """거래량순위 조회 성공"""
        expected_result = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상 처리되었습니다.",
            "output1": {"nrec": "20"},
            "output2": [
                {
                    "symb": "AAPL",
                    "name": "APPLE INC",
                    "tvol": "50000000",
                    "last": "185.00",
                },
                {
                    "symb": "NVDA",
                    "name": "NVIDIA CORP",
                    "tvol": "45000000",
                    "last": "450.00",
                },
            ],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.trade_volume_ranking("NAS")

        self.assertEqual(result, expected_result)
        self.api._make_request_dict.assert_called_once()
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76310010")
        self.assertEqual(call_args.kwargs["params"]["EXCD"], "NAS")

    def test_trade_volume_ranking_with_params(self):
        """거래량순위 조회 - 파라미터 포함"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.trade_volume_ranking(excd="NYS", nday="3", vol_rang="2")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["EXCD"], "NYS")
        self.assertEqual(call_args.kwargs["params"]["NDAY"], "3")
        self.assertEqual(call_args.kwargs["params"]["VOL_RANG"], "2")

    def test_trade_volume_ranking_exception(self):
        """거래량순위 조회 - 예외 발생 시 None 반환"""
        self.api._make_request_dict = Mock(side_effect=Exception("API Error"))

        result = self.api.trade_volume_ranking("NAS")

        self.assertIsNone(result)


class TestTradeAmountRanking(unittest.TestCase):
    """거래대금순위 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_trade_amount_ranking_success(self):
        """거래대금순위 조회 성공"""
        expected_result = {
            "rt_cd": "0",
            "output2": [{"symb": "TSLA", "name": "TESLA INC", "tamt": "1500000000"}],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.trade_amount_ranking("NAS")

        self.assertEqual(result["output2"][0]["symb"], "TSLA")
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76320010")


class TestTradeGrowthRanking(unittest.TestCase):
    """거래증가율순위 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_trade_growth_ranking_success(self):
        """거래증가율순위 조회 성공"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        result = self.api.trade_growth_ranking("HKS", nday="5")

        self.assertIsNotNone(result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["EXCD"], "HKS")
        self.assertEqual(call_args.kwargs["params"]["NDAY"], "5")
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76330000")


class TestTradeTurnoverRanking(unittest.TestCase):
    """거래회전율순위 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_trade_turnover_ranking_success(self):
        """거래회전율순위 조회 성공"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        result = self.api.trade_turnover_ranking("SHS")

        self.assertIsNotNone(result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76340000")


class TestMarketCapRanking(unittest.TestCase):
    """시가총액순위 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_market_cap_ranking_success(self):
        """시가총액순위 조회 성공"""
        expected_result = {
            "rt_cd": "0",
            "output2": [
                {"symb": "AAPL", "name": "APPLE INC", "mcap": "3000000000000"},
                {"symb": "MSFT", "name": "MICROSOFT CORP", "mcap": "2800000000000"},
            ],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.market_cap_ranking("NAS")

        self.assertEqual(result["output2"][0]["symb"], "AAPL")
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76350100")


class TestPriceChangeRanking(unittest.TestCase):
    """상승률/하락률 순위 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_price_change_ranking_gainers(self):
        """상승률 순위 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.price_change_ranking("NAS", gubn="1")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["GUBN"], "1")
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76290000")

    def test_price_change_ranking_losers(self):
        """하락률 순위 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.price_change_ranking("NAS", gubn="2")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["GUBN"], "2")


class TestPriceFluctuationRanking(unittest.TestCase):
    """가격급등락 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_price_fluctuation_surge(self):
        """급등 종목 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.price_fluctuation_ranking("NAS", gubn="0")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["GUBN"], "0")
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76260000")

    def test_price_fluctuation_plunge(self):
        """급락 종목 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.price_fluctuation_ranking("NAS", gubn="1")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["GUBN"], "1")


class TestNewHighLowRanking(unittest.TestCase):
    """신고/신저가 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_new_high_ranking(self):
        """신고가 종목 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.new_high_low_ranking("NAS", gubn="1")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["GUBN"], "1")
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76300000")

    def test_new_low_ranking(self):
        """신저가 종목 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.new_high_low_ranking("NAS", gubn="0")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["GUBN"], "0")


class TestVolumePowerRanking(unittest.TestCase):
    """매수체결강도 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_volume_power_ranking_success(self):
        """매수체결강도 순위 조회"""
        expected_result = {
            "rt_cd": "0",
            "output2": [{"symb": "AAPL", "vpwr": "150.5"}],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.volume_power_ranking("NAS")

        self.assertEqual(result["output2"][0]["vpwr"], "150.5")
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76280000")


class TestVolumeSurgeRanking(unittest.TestCase):
    """거래량급증 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_volume_surge_ranking_1min(self):
        """1분전 대비 거래량급증 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.volume_surge_ranking("NAS", mixn="0")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["MIXN"], "0")
        self.assertEqual(call_args.kwargs["tr_id"], "HHDFS76270000")

    def test_volume_surge_ranking_5min(self):
        """5분전 대비 거래량급증 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.volume_surge_ranking("NAS", mixn="3")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["MIXN"], "3")


class TestExchangeCodeHandling(unittest.TestCase):
    """거래소 코드 처리 테스트"""

    def setUp(self):
        from pykis.overseas.ranking_api import OverseasRankingAPI

        self.mock_client = MagicMock()
        self.api = OverseasRankingAPI(client=self.mock_client)

    def test_uppercase_exchange_code(self):
        """거래소 코드 대문자 변환"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.trade_volume_ranking("nas")  # 소문자

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["EXCD"], "NAS")  # 대문자로 변환

    def test_all_exchange_codes(self):
        """모든 지원 거래소 코드 테스트"""
        exchanges = ["NAS", "NYS", "AMS", "HKS", "SHS", "SZS", "TSE", "HSX", "HNX"]

        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        for excd in exchanges:
            result = self.api.trade_volume_ranking(excd)
            self.assertIsNotNone(result)


class TestFacadeIntegration(unittest.TestCase):
    """Facade 통합 테스트"""

    def test_facade_has_ranking_api(self):
        """Facade에 ranking_api 속성 존재"""
        from pykis.overseas.api_facade import OverseasStockAPI

        mock_client = MagicMock()
        facade = OverseasStockAPI(client=mock_client)
        self.assertTrue(hasattr(facade, "ranking_api"))

    def test_facade_wrapper_methods(self):
        """Facade 래퍼 메서드 존재"""
        from pykis.overseas.api_facade import OverseasStockAPI

        mock_client = MagicMock()
        facade = OverseasStockAPI(client=mock_client)

        # 모든 래퍼 메서드가 존재하는지 확인
        methods = [
            "trade_volume_ranking",
            "trade_amount_ranking",
            "trade_growth_ranking",
            "trade_turnover_ranking",
            "market_cap_ranking",
            "price_change_ranking",
            "price_fluctuation_ranking",
            "new_high_low_ranking",
            "volume_power_ranking",
            "volume_surge_ranking",
        ]
        for method in methods:
            self.assertTrue(hasattr(facade, method), f"Method {method} not found")

    def test_facade_delegates_to_ranking_api(self):
        """Facade가 ranking_api로 위임하는지 확인"""
        from pykis.overseas.api_facade import OverseasStockAPI

        mock_client = MagicMock()
        facade = OverseasStockAPI(client=mock_client)
        facade.ranking_api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        facade.trade_volume_ranking("NAS")

        facade.ranking_api._make_request_dict.assert_called_once()


class TestResponseTypes(unittest.TestCase):
    """응답 타입 테스트"""

    def test_ranking_types_importable(self):
        """Ranking 응답 타입 import 가능"""
        from pykis.responses.overseas import (
            OverseasRankingOutput1,
            OverseasRankingOutput2Item,
            OverseasRankingResponse,
        )

        self.assertIsNotNone(OverseasRankingOutput1)
        self.assertIsNotNone(OverseasRankingOutput2Item)
        self.assertIsNotNone(OverseasRankingResponse)

    def test_ranking_types_in_init(self):
        """Ranking 응답 타입이 __init__에서 export됨"""
        from pykis.responses import (
            OverseasRankingOutput1,
            OverseasRankingOutput2Item,
            OverseasRankingResponse,
        )

        self.assertIsNotNone(OverseasRankingOutput1)
        self.assertIsNotNone(OverseasRankingOutput2Item)
        self.assertIsNotNone(OverseasRankingResponse)


if __name__ == "__main__":
    unittest.main()
