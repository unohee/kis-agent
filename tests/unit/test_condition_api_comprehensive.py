"""
stock/condition.py 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상 함수: get_condition_stocks, get_condition_list, get_condition_result, save_condition, delete_condition
"""

import logging
import unittest
from unittest.mock import MagicMock, Mock, patch

from pykis.stock.condition import ConditionAPI, get_condition_stocks_dict


class TestConditionAPI(unittest.TestCase):
    """ConditionAPI 클래스 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.mock_client = MagicMock()
        self.api = ConditionAPI(self.mock_client, account_info=None, enable_cache=False)

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)

    # get_condition_stocks 테스트
    def test_get_condition_stocks_success(self):
        """조건검색 결과 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output2": [
                {"code": "005930", "name": "삼성전자"},
                {"code": "000660", "name": "SK하이닉스"},
            ],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee", seq=0)

        # Then
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["code"], "005930")

    def test_get_condition_stocks_continue(self):
        """조건검색 결과 조회 - 연속조회 필요 (rt_cd=1)"""
        # Given
        mock_response = {
            "rt_cd": "1",
            "msg1": "조회가 계속 됩니다.",
            "output2": [{"code": "005930", "name": "삼성전자"}],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee", seq=0)

        # Then
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    def test_get_condition_stocks_continue_empty(self):
        """조건검색 결과 조회 - 연속조회 필요하지만 결과 없음"""
        # Given
        mock_response = {
            "rt_cd": "1",
            "msg1": "조회가 계속 됩니다.",
            "output2": [],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee", seq=0)

        # Then
        self.assertEqual(result, [])

    def test_get_condition_stocks_empty_output(self):
        """조건검색 결과 조회 - 결과 없음"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output2": [],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee")

        # Then
        self.assertIsNone(result)

    def test_get_condition_stocks_no_output2(self):
        """조건검색 결과 조회 - output2 키 없음"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee")

        # Then
        self.assertIsNone(result)

    def test_get_condition_stocks_failure(self):
        """조건검색 결과 조회 - 실패"""
        # Given
        mock_response = {
            "rt_cd": "2",
            "msg1": "에러 발생",
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee")

        # Then
        self.assertIsNone(result)

    def test_get_condition_stocks_none_response(self):
        """조건검색 결과 조회 - None 응답"""
        # Given
        self.mock_client.make_request.return_value = None

        # When
        result = self.api.get_condition_stocks("unohee")

        # Then
        self.assertIsNone(result)

    def test_get_condition_stocks_exception(self):
        """조건검색 결과 조회 - 예외 발생"""
        # Given
        self.mock_client.make_request.side_effect = Exception("Connection error")

        # When
        result = self.api.get_condition_stocks("unohee")

        # Then
        self.assertIsNone(result)

    def test_get_condition_stocks_with_tr_cont(self):
        """조건검색 결과 조회 - 연속조회 파라미터"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output2": [{"code": "005930", "name": "삼성전자"}],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_condition_stocks("unohee", seq=1, tr_cont="Y")

        # Then
        self.assertIsNotNone(result)
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["params"]["seq"], 1)
        self.assertEqual(call_args[1]["params"]["tr_cont"], "Y")

    # get_condition_list 테스트
    def test_get_condition_list_success(self):
        """조건검색 목록 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [{"cond_id": "001", "cond_name": "테스트조건"}],
        }
        with patch.object(self.api, "_make_request_dict", return_value=mock_response):
            # When
            result = self.api.get_condition_list()

            # Then
            self.assertEqual(result, mock_response)

    def test_get_condition_list_exception(self):
        """조건검색 목록 조회 - 예외 발생"""
        # Given
        with patch.object(
            self.api, "_make_request_dict", side_effect=Exception("API Error")
        ):
            # When
            result = self.api.get_condition_list()

            # Then
            self.assertIsNone(result)

    # get_condition_result 테스트
    def test_get_condition_result_success(self):
        """조건검색 결과 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [{"code": "005930"}],
        }
        with patch.object(self.api, "_make_request_dict", return_value=mock_response):
            # When
            result = self.api.get_condition_result("001")

            # Then
            self.assertEqual(result, mock_response)

    def test_get_condition_result_exception(self):
        """조건검색 결과 조회 - 예외 발생"""
        # Given
        with patch.object(
            self.api, "_make_request_dict", side_effect=Exception("API Error")
        ):
            # When
            result = self.api.get_condition_result("001")

            # Then
            self.assertIsNone(result)

    # save_condition 테스트
    def test_save_condition_success(self):
        """조건검색 저장 성공 테스트"""
        # Given
        mock_response = {"rt_cd": "0", "msg1": "저장 완료"}
        with patch.object(self.api, "_make_request_dict", return_value=mock_response):
            # When
            result = self.api.save_condition("테스트조건", {"field": "value"})

            # Then
            self.assertEqual(result, mock_response)

    def test_save_condition_exception(self):
        """조건검색 저장 - 예외 발생"""
        # Given
        with patch.object(
            self.api, "_make_request_dict", side_effect=Exception("API Error")
        ):
            # When
            result = self.api.save_condition("테스트조건", {"field": "value"})

            # Then
            self.assertIsNone(result)

    # delete_condition 테스트
    def test_delete_condition_success(self):
        """조건검색 삭제 성공 테스트"""
        # Given
        mock_response = {"rt_cd": "0", "msg1": "삭제 완료"}
        with patch.object(self.api, "_make_request_dict", return_value=mock_response):
            # When
            result = self.api.delete_condition("001")

            # Then
            self.assertEqual(result, mock_response)

    def test_delete_condition_exception(self):
        """조건검색 삭제 - 예외 발생"""
        # Given
        with patch.object(
            self.api, "_make_request_dict", side_effect=Exception("API Error")
        ):
            # When
            result = self.api.delete_condition("001")

            # Then
            self.assertIsNone(result)


class TestGetConditionStocksDict(unittest.TestCase):
    """get_condition_stocks_dict 함수 테스트"""

    def test_get_condition_stocks_dict_success(self):
        """조건검색식 종목 딕셔너리 조회 성공"""
        # Given
        mock_agent = MagicMock()
        mock_agent.get_condition_stocks.return_value = [
            {"code": "005930", "name": "삼성전자"},
            {"code": "000660", "name": "SK하이닉스"},
        ]

        # When
        result = get_condition_stocks_dict(mock_agent)

        # Then
        self.assertIn("기본조건검색식", result)
        self.assertEqual(len(result["기본조건검색식"]), 2)
        self.assertEqual(result["기본조건검색식"][0]["code"], "005930")

    def test_get_condition_stocks_dict_no_result(self):
        """조건검색식 종목 딕셔너리 조회 - 결과 없음"""
        # Given
        mock_agent = MagicMock()
        mock_agent.get_condition_stocks.return_value = None

        # When
        result = get_condition_stocks_dict(mock_agent)

        # Then
        self.assertEqual(result, {})

    def test_get_condition_stocks_dict_empty_list(self):
        """조건검색식 종목 딕셔너리 조회 - 빈 리스트"""
        # Given
        mock_agent = MagicMock()
        mock_agent.get_condition_stocks.return_value = []

        # When
        result = get_condition_stocks_dict(mock_agent)

        # Then
        self.assertEqual(result, {})

    def test_get_condition_stocks_dict_exception(self):
        """조건검색식 종목 딕셔너리 조회 - 예외 발생"""
        # Given
        mock_agent = MagicMock()
        mock_agent.get_condition_stocks.side_effect = Exception("Error")

        # When
        result = get_condition_stocks_dict(mock_agent)

        # Then
        self.assertEqual(result, {})

    def test_get_condition_stocks_dict_missing_fields(self):
        """조건검색식 종목 딕셔너리 조회 - 필수 필드 누락"""
        # Given
        mock_agent = MagicMock()
        mock_agent.get_condition_stocks.return_value = [
            {"code": "005930", "name": "삼성전자"},  # 정상
            {"code": "", "name": "빈코드"},  # 코드 없음
            {"code": "000660", "name": ""},  # 이름 없음
            {},  # 둘 다 없음
        ]

        # When
        result = get_condition_stocks_dict(mock_agent)

        # Then
        self.assertIn("기본조건검색식", result)
        self.assertEqual(len(result["기본조건검색식"]), 1)  # 정상 항목만


if __name__ == "__main__":
    unittest.main()
