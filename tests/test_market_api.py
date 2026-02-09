"""
국내주식 API 테스트 스크립트

이 스크립트는 국내주식 관련 API들이 정상적으로 작동하는지 테스트합니다.
"""

import logging
import os

import pytest

from kis_agent import Agent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.mark.requires_credentials
def test_market_api():
    """
    국내주식 API 테스트를 실행합니다.
    """
    try:
        # API 키 체크 및 스킵 처리
        if not (os.getenv("KIS_APP_KEY") and os.getenv("KIS_APP_SECRET")):
            pytest.skip("API 키가 설정되지 않아 테스트를 스킵합니다.")

        # KIS_Agent 초기화
        agent = Agent(
            app_key=os.getenv("KIS_APP_KEY"),
            app_secret=os.getenv("KIS_APP_SECRET"),
            account_no=os.getenv("KIS_ACCOUNT_NO", ""),
            account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
        )
        logger.info("KIS_Agent 초기화 완료")

        # 테스트할 종목 코드 (삼성전자)
        test_code = "005930"

        # 1. 종목정보 관련 API 테스트
        logger.info("\n=== 종목정보 관련 API 테스트 ===")

        # 현재가 조회
        price = agent.get_stock_price(test_code)

        # 일별 차트 정보 조회
        daily_chart = agent.get_daily_price(test_code, "20240101", "20240615")

        # 2. 시세분석 관련 API 테스트
        logger.info("\n=== 시세분석 관련 API 테스트 ===")

        # 시장 변동성 정보 조회
        market_fluctuation = agent.get_market_fluctuation()

        # 시장 순위 정보 조회
        market_rankings = agent.get_market_rankings()

        # 회원사 거래 정보 조회
        member_transaction = agent.get_member_transaction(test_code)

        # 3. 순위분석 관련 API 테스트
        logger.info("\n=== 순위분석 관련 API 테스트 ===")

        # 4. 기본시세 관련 API 테스트
        logger.info("\n=== 기본시세 관련 API 테스트 ===")

        # 분봉 시세 정보 조회
        minute_price = agent.get_minute_price(test_code)

        # 5. 기타 정보 조회 API 테스트
        logger.info("\n=== 기타 정보 조회 API 테스트 ===")

        # 휴��일 정보 조회
        holiday_info = agent.get_holiday_info()

        # 기본 정보 조회
        basic_info = agent.get_stock_info(test_code)

        # 투자자별 매매 동향 조회
        investor_info = agent.get_stock_investor(test_code)

        # 국내 증시자금 종합 조회
        market_money = agent.get_market_rankings()

        # 거래량 순위 조회
        volume_rank = agent.get_volume_power()

        # 등락률 순위 조회
        price_rank = agent.get_market_fluctuation()

        # 수익자산지표 순위 조회
        profit_rank = agent.get_market_rankings()

        logger.info("\n 모든 API 테스트가 성공적으로 완료되었습니다.")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    test_market_api()
