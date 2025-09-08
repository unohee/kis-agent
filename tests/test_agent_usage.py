"""
KIS_Agent 사용 예시를 보여주는 테스트 스크립트입니다.

이 스크립트는 KIS_Agent의 주요 기능을 테스트하고 사용 방법을 보여줍니다.
"""

import os
import logging
import pytest
from pykis import Agent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_agent_usage():
    """KIS_Agent의 주요 기능을 테스트합니다."""
    try:
        # 환경변수에서 API 키 로드
        app_key = os.environ.get('KIS_APP_KEY')
        app_secret = os.environ.get('KIS_APP_SECRET')
        account_no = os.environ.get('KIS_ACCOUNT_NO')
        account_code = os.environ.get('KIS_ACCOUNT_CODE', '01')
        
        # API 키가 없으면 테스트 건너뛰기
        if not all([app_key, app_secret, account_no]):
            pytest.skip("필수 API 키가 설정되지 않았습니다. 환경변수를 설정하세요: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO")
        
        # KIS_Agent 초기화
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code
        )
        logger.info("KIS_Agent 초기화 완료")

        # 1. 국내주식 시세 조회
        # 삼성전자 현재가 조회
        samsung_price = agent.get_stock_price("005930")
        logger.info(f"삼성전자 현재가: {samsung_price}")
        if samsung_price is not None and hasattr(samsung_price, 'columns') and 'raw_text' in samsung_price.columns:
            logger.info(f"[RAW] 삼성전자 현재가 raw: {samsung_price['raw_text']}")
        elif isinstance(samsung_price, dict) and 'raw_text' in samsung_price:
            logger.info(f"[RAW] 삼성전자 현재가 raw: {samsung_price['raw_text']}")

        # 삼성전자 일별 시세 조회
        samsung_daily = agent.get_daily_price("005930")
        logger.info(f"삼성전자 일별 시세: {samsung_daily}")
        if samsung_daily is not None and hasattr(samsung_daily, 'columns') and 'raw_text' in samsung_daily.columns:
            logger.info(f"[RAW] 삼성전자 일별 시세 raw: {samsung_daily['raw_text']}")
        elif isinstance(samsung_daily, dict) and 'raw_text' in samsung_daily:
            logger.info(f"[RAW] 삼성전자 일별 시세 raw: {samsung_daily['raw_text']}")

        # 삼성전자 호가 정보 조회
        samsung_orderbook = agent.get_orderbook("005930")
        logger.info(f"삼성전자 호가 정보: {samsung_orderbook}")
        if samsung_orderbook is not None and hasattr(samsung_orderbook, 'empty') and not samsung_orderbook.empty:
            if hasattr(samsung_orderbook, 'columns') and 'raw_text' in samsung_orderbook.columns:
                logger.info(f"[RAW] 삼성전자 호가 raw: {samsung_orderbook['raw_text']}")

        # 2. 해외주식 시세 조회
        # 애플 현재가 조회
        # apple_price = agent.get_overseas_price("AAPL")
        # logger.info(f"애플 현재가: {apple_price}")

        # 3. 시장 분석
        # 거래량 순위 조회
        volume_rank = agent.get_volume_power()
        logger.info(f"거래량 순위: {volume_rank}")
        if volume_rank is not None and hasattr(volume_rank, 'columns') and 'raw_text' in volume_rank.columns:
            logger.info(f"[RAW] 거래량 순위 raw: {volume_rank['raw_text']}")
        elif isinstance(volume_rank, dict) and 'raw_text' in volume_rank:
            logger.info(f"[RAW] 거래량 순위 raw: {volume_rank['raw_text']}")

        # 등락률 순위 조회
        price_rank = agent.get_market_rankings()
        logger.info(f"등락률 순위: {price_rank}")
        if price_rank is not None and hasattr(price_rank, 'columns') and 'raw_text' in price_rank.columns:
            logger.info(f"[RAW] 등락률 순위 raw: {price_rank['raw_text']}")
        elif isinstance(price_rank, dict) and 'raw_text' in price_rank:
            logger.info(f"[RAW] 등락률 순위 raw: {price_rank['raw_text']}")

        # 4. 재무정보 조회
        # 삼성전자 재무비율 조회
        samsung_financial = agent.get_stock_info("005930")
        logger.info(f"삼성전자 재무비율: {samsung_financial}")
        if samsung_financial is not None:
            if hasattr(samsung_financial, 'empty') and not samsung_financial.empty:
                logger.info(f"[RAW] 삼성전자 재무비율 raw: {samsung_financial}")
            elif isinstance(samsung_financial, dict):
                logger.info(f"[RAW] 삼성전자 재무비율 raw: {samsung_financial}")

        # 5. 투자자 동향 조회
        # 삼성전자 투자자별 매매 동향
        samsung_investor = agent.get_stock_investor("005930")
        logger.info(f"삼성전자 ��자자 동향: {samsung_investor}")
        if samsung_investor is not None and hasattr(samsung_investor, 'empty') and not samsung_investor.empty and hasattr(samsung_investor, 'columns') and 'raw_text' in samsung_investor.columns:
            logger.info(f"[RAW] 삼성전자 투자자 동향 raw: {samsung_investor['raw_text']}")

        # 6. 증권사 투자의견 조회 (DEPRECATED - 해당 기능은 제거됨)
        # samsung_opinion = agent.get_stock_info("005930")
        # logger.info(f"삼성전자 증권사 투자의견: {samsung_opinion}")
        # if samsung_opinion and 'raw_text' in samsung_opinion:
        #     logger.info(f"[RAW] 삼성전자 증권사 투자의견 raw: {samsung_opinion['raw_text']}")

        logger.info("모든 테스트 완료")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    test_agent_usage() 