"""
stock/market.py 모듈의 단위 테스트

이 파일은 stock/market.py의 18% 커버리지를 높이기 위해 생성되었습니다.
StockAPI 클래스의 시장 정보 관련 메서드들을 테스트합니다.

커버리지 목표: 18% → 70%+
"""

import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from pykis.core.client import KISClient
from pykis.stock.market import StockAPI


class TestStockMarket(unittest.TestCase):
    """StockAPI 시장 정보 클래스의 포괄적인 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.client = KISClient()
        cls.account_info = {
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01"
        }
        cls.api = StockAPI(cls.client, cls.account_info)
        cls.api_no_account = StockAPI(cls.client)  # 계좌 정보 없는 인스턴스
        cls.test_code = "005930"
        
    def test_init_with_account(self):
        """계좌 정보가 있는 초기화 테스트"""
        api = StockAPI(self.client, self.account_info)
        self.assertEqual(api.account_info, self.account_info)
        self.assertEqual(api.client, self.client)
        
    def test_init_without_account(self):
        """계좌 정보가 없는 초기화 테스트"""
        api = StockAPI(self.client)
        self.assertEqual(api.account_info, {})
        self.assertEqual(api.client, self.client)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_price_success(self, mock_request):
        """주식 현재가 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"stck_prpr": "60000", "prdy_vrss": "1000"}
        }
        
        result = self.api.get_stock_price(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        mock_request.assert_called_once()

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_daily_price_with_dates(self, mock_request):
        """일별 시세 조회 날짜 지정 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"stck_bsop_date": "20241201", "stck_clpr": "60000"}]
        }
        
        result = self.api.get_daily_price(self.test_code, "20241201", "20241210")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_daily_price_default_dates(self, mock_request):
        """일별 시세 조회 기본 날짜 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"stck_bsop_date": "20241201"}]
        }
        
        result = self.api.get_daily_price(self.test_code)
        
        self.assertIsNotNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_orderbook_success(self, mock_request):
        """호가 정보 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"askp1": "60500", "bidp1": "60000", "askp_rsqn1": "100"}
        }
        
        result = self.api.get_orderbook(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_member_success(self, mock_request):
        """주식 회원사 정보 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"seln_mbcr_name1": "삼성증권", "shnu_mbcr_name1": "미래에셋"}
        }
        
        result = self.api.get_stock_member(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_member_exception(self, mock_request):
        """주식 회원사 정보 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_stock_member(self.test_code)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_investor_success(self, mock_request):
        """투자자별 매매 동향 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"prsn_ntby_qty": "1000", "frgn_ntby_qty": "2000"}
        }
        
        result = self.api.get_stock_investor(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_holiday_info_success(self, mock_request):
        """휴장일 정보 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"bass_dt": "20241225", "wday_dvsn_cd": "7"}]
        }
        
        result = self.api.get_holiday_info()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_holiday_info_exception(self, mock_request):
        """휴장일 정보 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_holiday_info()
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_basic_success(self, mock_request):
        """주식 기본 정보 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"hts_kor_isnm": "삼성전자", "std_pdno": self.test_code}
        }
        
        result = self.api.get_stock_basic(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_basic_exception(self, mock_request):
        """주식 기본 정보 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_stock_basic(self.test_code)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_income_success(self, mock_request):
        """손익계산서 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"sale_account": "1000000", "bsop_prfi": "200000"}
        }
        
        result = self.api.get_stock_income(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_income_exception(self, mock_request):
        """손익계산서 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_stock_income(self.test_code)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_financial_success(self, mock_request):
        """재무비율 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"per": "15.5", "pbr": "1.2", "roe": "8.5"}
        }
        
        result = self.api.get_stock_financial(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_financial_exception(self, mock_request):
        """재무비율 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_stock_financial(self.test_code)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_volume_rank_success(self, mock_request):
        """거래량 순위 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"hts_kor_isnm": "삼성전자", "acml_vol": "1000000"}]
        }
        
        result = self.api.get_volume_rank()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_price_rank_success(self, mock_request):
        """등락률 순위 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"hts_kor_isnm": "삼성전자", "prdy_ctrt": "5.25"}]
        }
        
        result = self.api.get_price_rank()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_volume_power_ranking_success(self, mock_request):
        """체결강도 순위 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"hts_kor_isnm": "삼성전자", "vol_tnrt": "150.5"}]
        }
        
        result = self.api.get_volume_power_ranking()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_expected_closing_price_success(self, mock_request):
        """예상 체결가 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"hts_kor_isnm": "삼성전자", "antc_cnpr": "60500"}]
        }
        
        result = self.api.get_expected_closing_price(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_fetch_minute_data_success(self, mock_request):
        """분봉 데이터 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output1": [{"stck_cntg_hour": "153000", "stck_prpr": "60000"}]
        }
        
        result = self.api.fetch_minute_data(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_program_trade_hourly_trend_success(self, mock_request):
        """프로그램매매 시간대별 추이 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"cntg_time": "153000", "seln_cqty": "1000"}]
        }
        
        result = self.api.get_program_trade_hourly_trend(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_pgm_trade_success(self, mock_request):
        """프로그램매매 정보 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"stck_bsop_date": "20241201", "whol_smtn_ntby_qty": "1000"}]
        }
        
        result = self.api.get_pgm_trade(self.test_code)
        
        self.assertIsNotNone(result)

    def test_is_holiday_true(self):
        """휴장일 확인 True 테스트"""
        # Mock data for holidays - is_holiday 메서드는 date in holiday_info['output']로 체크함
        with patch.object(self.api, 'get_holiday_info') as mock_holiday:
            mock_holiday.return_value = {
                "rt_cd": "0",
                "output": ["20241225", "20241226"]  # 실제 메서드 로직에 맞게 수정
            }
            
            result = self.api.is_holiday("20241225")
            
            self.assertTrue(result)

    def test_is_holiday_false(self):
        """휴장일 확인 False 테스트"""
        # Mock data for holidays - is_holiday 메서드는 date in holiday_info['output']로 체크함
        with patch.object(self.api, 'get_holiday_info') as mock_holiday:
            mock_holiday.return_value = {
                "rt_cd": "0",
                "output": ["20241225", "20241226"]  # 실제 메서드 로직에 맞게 수정
            }
            
            result = self.api.is_holiday("20241201")
            
            self.assertFalse(result)

    def test_is_holiday_api_failure(self):
        """휴장일 확인 API 실패 테스트"""
        with patch.object(self.api, 'get_holiday_info') as mock_holiday:
            mock_holiday.return_value = None
            
            result = self.api.is_holiday("20241201")
            
            self.assertFalse(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_member_transaction_success(self, mock_request):
        """회원사 거래 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"time": "153000", "seln_cqty": "100"}]
        }
        
        result = self.api.get_member_transaction(self.test_code, "001")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_member_transaction_failure(self, mock_request):
        """회원사 거래 조회 실패 테스트"""
        mock_request.return_value = {"rt_cd": "1"}
        
        result = self.api.get_member_transaction(self.test_code, "001")
        
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main() 