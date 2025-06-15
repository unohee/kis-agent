"""
국내주식 API 테스트 스크립트

이 스크립트는 국내주식 관련 API들이 정상적으로 작동하는지 테스트합니다.
"""

import os
import logging
import pytest
from pykis import Agent
from pykis.stock import market

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_market_api():
    """
    국내주식 API 테스트를 실행합니다.
    """
    try:
        # KIS_Agent 초기화
        agent = Agent()
        logger.info("KIS_Agent 초기화 완료")

        # 테스트할 종목 코드 (삼성전자)
        test_code = "005930"

        # 1. 종목정보 관련 API 테스트
        logger.info("\n=== 종목정보 관련 API 테스트 ===")
        
        # 현재가 조회
        price = agent.get_stock_price(test_code)
        logger.info(f"현재가 조회 결과: {price}")
        
        # 종목 상세 정보 조회
        detail = agent.get_stock_price_detail(test_code)
        logger.info(f"종목 상세 정보 조회 결과: {detail}")
        
        # 시간별 체결 정보 조회
        time_conclusion = agent.get_time_conclusion(test_code)
        logger.info(f"시간별 체결 정보 조회 결과: {time_conclusion}")
        
        # 시간외 체결 정보 조회
        overtime_conclusion = agent.get_overtime_conclusion(test_code)
        logger.info(f"시간외 체결 정보 조회 결과: {overtime_conclusion}")
        
        # 일별 차트 정보 조회
        daily_chart = agent.get_daily_chart(test_code, "20240101", "20240615")
        logger.info(f"일별 차트 정보 조회 결과: {daily_chart}")
        
        # 지수 차트 정보 조회 (KOSPI)
        index_chart = agent.get_index_chart("2001")
        logger.info(f"지수 차트 정보 조회 결과: {index_chart}")

        # 2. 시세분석 관련 API 테스트
        logger.info("\n=== 시세분석 관련 API 테스트 ===")
        
        # 거래량 파워 정보 조회
        # volume_power = agent.get_volume_power(test_code)
        # logger.info(f"거래량 파워 정보 조회 결과: {volume_power}")
        
        # 시장 변동성 정보 조회
        market_fluctuation = agent.get_market_fluctuation()
        logger.info(f"시장 변동성 정보 조회 결과: {market_fluctuation}")
        
        # 시장 순위 정보 조회
        market_rankings = agent.get_market_rankings()
        logger.info(f"시장 순위 정보 조회 결과: {market_rankings}")
        
        # 회원사 거래 정보 조회
        member_transaction = agent.get_member_transaction(test_code)
        logger.info(f"회원사 거래 정보 조회 결과: {member_transaction}")

        # 3. 순위분석 관련 API 테스트
        logger.info("\n=== 순위분석 관련 API 테스트 ===")
        
        # 예상 종가 정보 조회
        expected_price = agent.get_expected_closing_price(test_code)
        logger.info(f"예상 종가 정보 조회 결과: {expected_price}")

        # 4. 기본시세 관련 API 테스트
        logger.info("\n=== 기본시세 관련 API 테스트 ===")
        
        # 분봉 시세 정보 조회
        minute_price = agent.get_minute_price(test_code)
        logger.info(f"분봉 시세 정보 조회 결과: {minute_price}")

        # 5. 기타 정보 조회 API 테스트
        logger.info("\n=== 기타 정보 조회 API 테스트 ===")
        
        # 휴장일 정보 조회
        holiday_info = agent.get_holiday_info()
        logger.info(f"휴장일 정보 조회 결과: {holiday_info}")
        
        # 기본 정보 조회
        basic_info = agent.get_stock_basic(test_code)
        logger.info(f"기본 정보 조회 결과: {basic_info}")
        
        # 투자자별 매매 동향 조회
        investor_info = agent.get_stock_investor(test_code)
        logger.info(f"투자자별 매매 동향 조회 결과: {investor_info}")
        
        # 외국인 보유 정보 조회
        foreign_info = agent.get_foreign_investor(test_code)
        logger.info(f"외국인 보유 정보 조회 결과: {foreign_info}")
        
        # 국내기관/외국인 매매종목 가집계 조회
        domestic_investor = agent.get_domestic_investor(test_code)
        logger.info(f"국내기관/외국인 매매종목 가집계 조회 결과: {domestic_investor}")
        
        # 외국계 매매종목 가집계 조회
        foreign_trade = agent.get_foreign_trade(test_code)
        logger.info(f"외국계 매매종목 가집계 조회 결과: {foreign_trade}")
        
        # 종목별 외국계 순매수추이 조회
        foreign_net_buy = agent.get_foreign_net_buy(test_code)
        logger.info(f"종목별 외국계 순매수추이 조회 결과: {foreign_net_buy}")
        
        # 국내 증시자금 종합 조회
        market_money = agent.get_market_money()
        logger.info(f"국내 증시자금 종합 조회 결과: {market_money}")
        
        # 거래량 순위 조회
        volume_rank = agent.get_volume_rank()
        logger.info(f"거래량 순위 조회 결과: {volume_rank}")
        
        # 등락률 순위 조회
        price_rank = agent.get_price_rank()
        logger.info(f"등락률 순위 조회 결과: {price_rank}")
        
        # 수익자산지표 순위 조회
        profit_rank = agent.get_profit_rank()
        logger.info(f"수익자산지표 순위 조회 결과: {profit_rank}")

        logger.info("\n✅ 모든 API 테스트가 성공적으로 완료되었습니다.")

    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    test_market_api() 