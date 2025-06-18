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

    def test_refresh_token(self):
        """
        refresh_token 메서드를 실제 API 호출로 테스트합니다.
        """
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
        print(f"주식 현재가 API 호출 성공: {response}")

    def test_make_request_daily_price(self):
        """
        make_request 메서드를 실제 일별 시세 API 호출로 테스트합니다.
        """
        # 삼성전자 일별 시세 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "20240601",
                "FID_INPUT_DATE_2": "20240618"
            }
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response['rt_cd'], '0')
        print(f"일별 시세 API 호출 성공: {response}")

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
        print(f"호가 API 호출 성공: {response}")

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
        print(f"투자자별 매매 동향 API 호출 성공: {response}")

    def test_enforce_rate_limit(self):
        """
        _enforce_rate_limit 메서드를 테스트합니다.
        """
        # 요청 제한 테스트
        self.client._enforce_rate_limit()
        self.assertGreater(self.client.last_request_time, 0)
        print(f"요청 제한 테스트 성공: {self.client.last_request_time}")

if __name__ == '__main__':
    unittest.main() 