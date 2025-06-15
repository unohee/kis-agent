import logging
from typing import Dict, List, Optional
from kis.core.client import KISClient

"""
program.py - 프로그램 매매 API 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 프로그램 매매 추이 조회
- 순매수량 확인
- 매매 동향 분석

✅ 의존:
- client.py: API 클라이언트

🔗 연관 모듈:
- agent.py: KIS API 통합 에이전트
- stock.py: 주식 관련 API

💡 사용 예시:
program = ProgramTradeAPI(client)
trend = program.get_program_trade_trend(code="005930")
"""

class ProgramTradeAPI:
    def __init__(self, client: KISClient):
        """프로그램 매매 API 초기화"""
        self.client = client

    def get_program_trade_trend(self, code: str) -> Optional[Dict]:
        """프로그램 매매 추이 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-program-trade",
                tr_id="FHKST03010100",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logging.error(f"프로그램 매매 추이 조회 실패: {e}")
            return None

    def get_net_buy_volume(self, code: str) -> Optional[Dict]:
        """순매수량 확인"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-net-buy-volume",
                tr_id="FHKST03010200",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logging.error(f"순매수량 확인 실패: {e}")
            return None

    def analyze_trade_trend(self, code: str) -> Optional[Dict]:
        """매매 동향 분석"""
        try:
            trend = self.get_program_trade_trend(code)
            net_buy = self.get_net_buy_volume(code)
            if trend and net_buy:
                return {
                    "trend": trend,
                    "net_buy": net_buy,
                    "analysis": "TODO: 매매 동향 분석 로직 구현"
                }
            return None
        except Exception as e:
            logging.error(f"매매 동향 분석 실패: {e}")
            return None

# Expose facade class for flat import
__all__ = ['ProgramTradeAPI'] 
