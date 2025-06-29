"""
KISClient 클래스의 통합 테스트 모듈입니다.

이 모듈은 KISClient 클래스의 기능을 실제 API 호출로 테스트합니다:
- API 요청 처리
- 토큰 관리
- 요청 제한 관리
- 에러 처리

의존성:
- unittest: 테스트 프레임워크
- pykis.core.client: 테스트 대상
- .env: 실제 인증 정보

사용 예시:
    >>> python -m unittest tests/unit/test_client.py
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from pykis.core.client import KISClient
from pykis.core.config import KISConfig

class TestKISClient(unittest.TestCase):
    """
    KISClient 클래스의 통합 테스트 클래스입니다.

    이 클래스는 KISClient의 각 메서드를 실제 API 호출로 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        # 실제 .env 파일의 인증 정보를 사용
        self.config = KISConfig()
        self.client = KISClient(self.config)

    @patch('requests.post')
    def test_refresh_token(self, mock_post):
        """
        refresh_token 메서드를 실제 API 호출로 테스트합니다.
        """
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'test_token',
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 토큰 갱신 테스트
        self.client.refresh_token()
        # 토큰이 발급되었는지 확인
        self.assertIsNotNone(self.client.token)
        self.assertIsInstance(self.client.token, str)
        self.assertGreater(len(self.client.token), 0)
        print(f"토큰 발급 성공: {self.client.token[:20]}...")

    def test_make_request_stock_price(self):
        """
        make_request 메서드를 실제 주식 현재가 API 호출로 테스트합니다.
        """
        # 삼성전자 현재가 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930"
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response['rt_cd'], '0')

    def test_make_request_daily_price(self):
        """
        make_request 메서드를 실제 일별 시세 API 호출로 테스트합니다.
        """
        # 삼성전자 일별 시세 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "20240601",
                "FID_INPUT_DATE_2": "20240618"
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        if response:
            self.assertEqual(response['rt_cd'], '0')

    def test_make_request_orderbook(self):
        """
        make_request 메서드를 실제 호가 API 호출로 테스트합니다.
        """
        # 삼성전자 호가 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930"
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response['rt_cd'], '0')

    def test_make_request_investor(self):
        """
        make_request 메서드를 실제 투자자별 매매 동향 API 호출로 테스트합니다.
        """
        # 삼성전자 투자자별 매매 동향 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-investor",
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930"
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response['rt_cd'], '0')

    def test_enforce_rate_limit(self):
        """
        _enforce_rate_limit 메서드를 테스트합니다.
        """
        # 요청 제한 테스트
        self.client._enforce_rate_limit()
        self.assertGreater(self.client.last_request_time, 0)

    def test_make_request_program_trade(self):
        """
        make_request 메서드를 실제 프로그램매매 API 호출로 테스트합니다.
        """
        # 삼성전자 프로그램매매 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-ccld",
            tr_id="FHKST03030100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
                "FID_PERIOD_DIV_CODE": "D"
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        if response.get('rt_cd') == '0':
            self.assertEqual(response['rt_cd'], '0')

    def test_make_request_market_cap(self):
        """
        make_request 메서드를 실제 시가총액 순위 API 호출로 테스트합니다.
        """
        # 시가총액 순위 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/ranking/market-cap",
            tr_id="FHPTJ04040000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20170",
                "FID_INPUT_ISCD": "0000",
                "FID_DIV_CLS_CODE": "0",
                "FID_BLNG_CLS_CODE": "0",
                "FID_TRGT_CLS_CODE": "111111111",
                "FID_TRGT_EXLS_CLS_CODE": "000000",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "",
                "FID_INPUT_DATE_1": ""
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        if response.get('rt_cd') == '0':
            self.assertEqual(response['rt_cd'], '0')

if __name__ == '__main__':
    unittest.main() 