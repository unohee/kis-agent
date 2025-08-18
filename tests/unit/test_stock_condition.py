"""
stock/condition.py 모듈의 단위 테스트

이 파일은 stock/condition.py의 29% 커버리지를 높이기 위해 생성되었습니다.
ConditionAPI 클래스의 조건검색 관련 메서드들을 테스트합니다.

커버리지 목표: 29% → 85%+
"""

import unittest
from unittest.mock import patch, MagicMock
from pykis.core.client import KISClient
from pykis.stock.condition import ConditionAPI, get_condition_stocks_dict


class TestConditionAPI(unittest.TestCase):
    """ConditionAPI 클래스의 포괄적인 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.client = KISClient()
        cls.api = ConditionAPI(cls.client)
        cls.test_user_id = "test_user"
        cls.test_condition_id = "TEST001"
        
    def test_init(self):
        """ConditionAPI 초기화 테스트"""
        api = ConditionAPI(self.client)
        self.assertEqual(api.client, self.client)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_success_rt_cd_0(self, mock_request):
        """조건검색 결과 조회 성공 테스트 (rt_cd='0')"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output2": [
                {"code": "005930", "name": "삼성전자"},
                {"code": "000660", "name": "SK하이닉스"}
            ]
        }
        
        result = self.api.get_condition_stocks(self.test_user_id, seq=0, tr_cont='N')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["code"], "005930")
        self.assertEqual(result[0]["name"], "삼성전자")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_success_rt_cd_1(self, mock_request):
        """조건검색 결과 조회 성공 테스트 (rt_cd='1' - 연속조회)"""
        mock_request.return_value = {
            "rt_cd": "1",
            "output2": [
                {"code": "005930", "name": "삼성전자"}
            ]
        }
        
        result = self.api.get_condition_stocks(self.test_user_id, seq=1, tr_cont='Y')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["code"], "005930")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_no_response(self, mock_request):
        """조건검색 응답 없음 테스트"""
        mock_request.return_value = None
        
        result = self.api.get_condition_stocks(self.test_user_id)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_empty_output(self, mock_request):
        """조건검색 결과 빈 응답 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output2": []
        }
        
        result = self.api.get_condition_stocks(self.test_user_id)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_no_output2(self, mock_request):
        """조건검색 결과 output2 없음 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output1": "some data"
        }
        
        result = self.api.get_condition_stocks(self.test_user_id)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_rt_cd_1_empty_output(self, mock_request):
        """조건검색 결과 rt_cd='1' 빈 응답 테스트"""
        mock_request.return_value = {
            "rt_cd": "1",
            "output2": []
        }
        
        result = self.api.get_condition_stocks(self.test_user_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_error_rt_cd(self, mock_request):
        """조건검색 오류 응답 테스트"""
        mock_request.return_value = {
            "rt_cd": "99",
            "msg1": "오류 메시지"
        }
        
        result = self.api.get_condition_stocks(self.test_user_id)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_stocks_exception(self, mock_request):
        """조건검색 예외 발생 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_condition_stocks(self.test_user_id)
        
        self.assertIsNone(result)

    def test_get_condition_stocks_default_params(self):
        """조건검색 기본 파라미터 테스트"""
        with patch.object(self.api.client, 'make_request') as mock_request:
            mock_request.return_value = {
                "rt_cd": "0",
                "output2": [{"code": "005930", "name": "삼성전자"}]
            }
            
            result = self.api.get_condition_stocks()
            
            # 기본값 확인
            args, kwargs = mock_request.call_args
            self.assertIn("params", kwargs)
            params = kwargs["params"]
            self.assertEqual(params["user_id"], "unohee")
            self.assertEqual(params["seq"], 0)
            self.assertEqual(params["tr_cont"], "N")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_list_success(self, mock_request):
        """조건검색 목록 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"condition_id": "001", "condition_name": "조건1"},
                {"condition_id": "002", "condition_name": "조건2"}
            ]
        }
        
        result = self.api.get_condition_list()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_list_exception(self, mock_request):
        """조건검색 목록 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_condition_list()
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_result_success(self, mock_request):
        """조건검색 결과 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930", "name": "삼성전자"}]
        }
        
        result = self.api.get_condition_result(self.test_condition_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_condition_result_exception(self, mock_request):
        """조건검색 결과 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_condition_result(self.test_condition_id)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_save_condition_success(self, mock_request):
        """조건검색 저장 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"condition_id": "NEW001"}
        }
        
        condition_data = {"filter": "price > 1000"}
        result = self.api.save_condition("새조건", condition_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_save_condition_exception(self, mock_request):
        """조건검색 저장 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        condition_data = {"filter": "price > 1000"}
        result = self.api.save_condition("새조건", condition_data)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_delete_condition_success(self, mock_request):
        """조건검색 삭제 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"result": "success"}
        }
        
        result = self.api.delete_condition(self.test_condition_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_delete_condition_exception(self, mock_request):
        """조건검색 삭제 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.delete_condition(self.test_condition_id)
        
        self.assertIsNone(result)


class TestConditionHelperFunctions(unittest.TestCase):
    """조건검색 헬퍼 함수들의 테스트"""
    
    def setUp(self):
        """각 테스트마다 실행되는 설정"""
        self.mock_agent = MagicMock()

    def test_get_condition_stocks_dict_success(self):
        """조건검색 딕셔너리 변환 성공 테스트"""
        # Mock agent의 get_condition_stocks 메서드
        self.mock_agent.get_condition_stocks.return_value = [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"}
        ]
        
        result = get_condition_stocks_dict(self.mock_agent)
        
        self.assertIsInstance(result, dict)
        self.assertIn("기본조건검색식", result)
        self.assertEqual(len(result["기본조건검색식"]), 2)
        
        # 첫 번째 종목 확인
        first_stock = result["기본조건검색식"][0]
        self.assertEqual(first_stock["code"], "005930")
        self.assertEqual(first_stock["name"], "삼성전자")
        self.assertEqual(first_stock["종목코드"], "005930")
        self.assertEqual(first_stock["종목명"], "삼성전자")

    def test_get_condition_stocks_dict_no_stocks(self):
        """조건검색 딕셔너리 변환 결과 없음 테스트"""
        self.mock_agent.get_condition_stocks.return_value = None
        
        result = get_condition_stocks_dict(self.mock_agent)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_get_condition_stocks_dict_empty_stocks(self):
        """조건검색 딕셔너리 변환 빈 목록 테스트"""
        self.mock_agent.get_condition_stocks.return_value = []
        
        result = get_condition_stocks_dict(self.mock_agent)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_get_condition_stocks_dict_incomplete_data(self):
        """조건검색 딕셔너리 변환 불완전한 데이터 테스트"""
        # 코드나 이름이 없는 데이터
        self.mock_agent.get_condition_stocks.return_value = [
            {"code": "005930", "name": "삼성전자"},
            {"code": "", "name": "빈코드"},  # 코드가 빈 문자열
            {"code": "000660"},  # 이름이 없음
            {"name": "이름만"},  # 코드가 없음
            {"code": "051910", "name": "LG화학"}  # 정상 데이터
        ]
        
        result = get_condition_stocks_dict(self.mock_agent)
        
        self.assertIsInstance(result, dict)
        self.assertIn("기본조건검색식", result)
        # 완전한 데이터만 포함되어야 함 (2개)
        self.assertEqual(len(result["기본조건검색식"]), 2)
        
        codes = [stock["code"] for stock in result["기본조건검색식"]]
        self.assertIn("005930", codes)
        self.assertIn("051910", codes)

    def test_get_condition_stocks_dict_exception(self):
        """조건검색 딕셔너리 변환 예외 테스트"""
        self.mock_agent.get_condition_stocks.side_effect = Exception("API 오류")
        
        result = get_condition_stocks_dict(self.mock_agent)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main() 