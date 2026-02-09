"""
stock/interest.py 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상 함수: get_interest_group_list, get_interest_stock_list
"""

import unittest
from unittest.mock import MagicMock, patch

from pykis.stock.interest import InterestStockAPI


class TestInterestStockAPI(unittest.TestCase):
    """InterestStockAPI 클래스 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.mock_client = MagicMock()
        self.api = InterestStockAPI(
            self.mock_client, account_info=None, enable_cache=False
        )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)

    def test_init_with_from_agent(self):
        """Agent를 통한 초기화 테스트"""
        api = InterestStockAPI(
            self.mock_client, account_info=None, enable_cache=False, _from_agent=True
        )
        self.assertEqual(api.client, self.mock_client)

    # get_interest_group_list 테스트
    def test_get_interest_group_list_success(self):
        """관심종목 그룹 목록 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "00000000",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {"inter_grp_code": "001", "inter_grp_name": "관심그룹1"},
                {"inter_grp_code": "002", "inter_grp_name": "관심그룹2"},
            ],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_group_list("unohee")

        # Then
        self.assertEqual(result, mock_response)
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["tr_id"], "HHKCM113004C7")
        self.assertEqual(call_args[1]["params"]["USER_ID"], "unohee")

    def test_get_interest_group_list_with_params(self):
        """관심종목 그룹 목록 조회 - 파라미터 테스트"""
        # Given
        mock_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_group_list(
            user_id="testuser", type_code="2", fid_etc_cls_code="01"
        )

        # Then
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["params"]["USER_ID"], "testuser")
        self.assertEqual(call_args[1]["params"]["TYPE"], "2")
        self.assertEqual(call_args[1]["params"]["FID_ETC_CLS_CODE"], "01")

    def test_get_interest_group_list_failure(self):
        """관심종목 그룹 목록 조회 실패 테스트"""
        # Given
        mock_response = {
            "rt_cd": "1",
            "msg1": "조회 실패",
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_group_list("unohee")

        # Then
        self.assertIsNone(result)

    def test_get_interest_group_list_none_response(self):
        """관심종목 그룹 목록 조회 - None 응답"""
        # Given
        self.mock_client.make_request.return_value = None

        # When
        result = self.api.get_interest_group_list("unohee")

        # Then
        self.assertIsNone(result)

    # get_interest_stock_list 테스트
    def test_get_interest_stock_list_success(self):
        """관심종목 그룹별 종목 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "00000000",
            "msg1": "정상처리 되었습니다.",
            "output1": {"inter_grp_code": "001", "inter_grp_name": "관심그룹1"},
            "output2": [
                {"jong_code": "005930", "hts_kor_isnm": "삼성전자"},
                {"jong_code": "000660", "hts_kor_isnm": "SK하이닉스"},
            ],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_stock_list("unohee", "001")

        # Then
        self.assertEqual(result, mock_response)
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["tr_id"], "HHKCM113004C6")
        self.assertEqual(call_args[1]["params"]["USER_ID"], "unohee")
        self.assertEqual(call_args[1]["params"]["INTER_GRP_CODE"], "001")

    def test_get_interest_stock_list_with_all_params(self):
        """관심종목 그룹별 종목 조회 - 전체 파라미터"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": {},
            "output2": [],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_stock_list(
            user_id="testuser",
            inter_grp_code="002",
            type_code="2",
            data_rank="1",
            inter_grp_name="테스트그룹",
            hts_kor_isnm="삼성",
            cntg_cls_code="1",
            fid_etc_cls_code="5",
        )

        # Then
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["USER_ID"], "testuser")
        self.assertEqual(params["INTER_GRP_CODE"], "002")
        self.assertEqual(params["TYPE"], "2")
        self.assertEqual(params["DATA_RANK"], "1")
        self.assertEqual(params["INTER_GRP_NAME"], "테스트그룹")
        self.assertEqual(params["HTS_KOR_ISNM"], "삼성")
        self.assertEqual(params["CNTG_CLS_CODE"], "1")
        self.assertEqual(params["FID_ETC_CLS_CODE"], "5")

    def test_get_interest_stock_list_failure(self):
        """관심종목 그룹별 종목 조회 실패 테스트"""
        # Given
        mock_response = {
            "rt_cd": "1",
            "msg1": "조회 실패",
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_stock_list("unohee", "001")

        # Then
        self.assertIsNone(result)

    def test_get_interest_stock_list_none_response(self):
        """관심종목 그룹별 종목 조회 - None 응답"""
        # Given
        self.mock_client.make_request.return_value = None

        # When
        result = self.api.get_interest_stock_list("unohee", "001")

        # Then
        self.assertIsNone(result)

    def test_get_interest_stock_list_empty_output2(self):
        """관심종목 그룹별 종목 조회 - 빈 종목 리스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {"inter_grp_code": "001"},
            "output2": [],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_interest_stock_list("unohee", "001")

        # Then
        self.assertIsNotNone(result)
        self.assertEqual(len(result.get("output2", [])), 0)


if __name__ == "__main__":
    unittest.main()
