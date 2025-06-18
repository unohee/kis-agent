import logging
from typing import Dict, List, Optional
from ..core.client import KISClient, API_ENDPOINTS

"""
program.py - 프로그램 매매 API 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 종목별 프로그램매매추이(일별) 조회 (Postman 검증됨)
- 프로그램 매매 요약 조회
- 순매수량 확인

✅ 의존:
- client.py: API 클라이언트 및 엔드포인트 정의

🔗 연관 모듈:
- agent.py: KIS API 통합 에이전트
- stock.py: 주식 관련 API

💡 사용 예시:
program = ProgramTradeAPI(client)
daily_trend = program.get_program_trade_by_stock_daily(code="005930", date="20240624")
"""

class ProgramTradeAPI:
    def __init__(self, client, account_info=None):
        """프로그램 매매 API 초기화"""
        self.client = client
        self.account_info = account_info or {}

    def get_program_trade_by_stock_daily(self, code: str, date: str = None) -> Optional[Dict]:
        """
        종목별 프로그램매매추이(일별) 조회 (Postman 검증된 방식)
        
        Args:
            code: 종목코드 (6자리)
            date: 기준일 (YYYYMMDD 형식, 기본값: 오늘)
        """
        from datetime import datetime
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
            
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['PROGRAM_TRADE_BY_STOCK_DAILY'],
                tr_id="FHPPG04650200",  # Postman에서 확인된 TR_ID
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분코드(J: 주식)
                    "FID_INPUT_ISCD": code,         # 종목코드
                    "FID_INPUT_DATE_1": date        # 기준일
                }
            )
        except Exception as e:
            logging.error(f"종목별 프로그램매매추이 조회 실패: {e}")
            return None

    def get_program_trade_summary(self, code: str) -> Optional[Dict]:
        """
        프로그램 매매 요약 조회
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['PROGRAM_TRADE_SUMMARY'],
                tr_id="FHKST03010100",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code
                }
            )
        except Exception as e:
            logging.error(f"프로그램 매매 요약 조회 실패: {e}")
            return None

    def get_net_buy_volume(self, code: str) -> Optional[Dict]:
        """
        순매수량 확인
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['NET_BUY_VOLUME'],
                tr_id="FHKST03010200",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code
                }
            )
        except Exception as e:
            logging.error(f"순매수량 확인 실패: {e}")
            return None

    def analyze_trade_trend(self, code: str, date: str = None) -> Optional[Dict]:
        """
        매매 동향 종합 분석 (Postman 검증된 방식 사용)
        """
        try:
            daily_trend = self.get_program_trade_by_stock_daily(code, date)
            summary = self.get_program_trade_summary(code)
            net_buy = self.get_net_buy_volume(code)
            
            return {
                "daily_trend": daily_trend,
                "summary": summary,
                "net_buy": net_buy,
                "analysis": {
                    "has_daily_data": daily_trend is not None and daily_trend.get('rt_cd') == '0',
                    "has_summary_data": summary is not None and summary.get('rt_cd') == '0',
                    "has_net_buy_data": net_buy is not None and net_buy.get('rt_cd') == '0'
                }
            }
        except Exception as e:
            logging.error(f"매매 동향 분석 실패: {e}")
            return None

# Expose facade class for flat import
__all__ = ['ProgramTradeAPI'] 
