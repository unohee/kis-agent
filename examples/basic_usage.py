#!/usr/bin/env python3
"""
PyKIS 기본 사용 예제

한국투자증권 API를 사용하여 주식 시세를 조회하는 기본 예제입니다.
API 키는 반드시 매개변수로 직접 전달해야 합니다.
"""

import os
import sys
from typing import Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


def create_agent_from_env():
    """API 키를 환경변수에서 로드하여 Agent 생성"""
    print("=" * 60)
    print("API 키 로드 및 Agent 생성")
    print("=" * 60)
    
    # 실제 사용 시에는 환경변수나 별도 설정 파일에서 로드하세요
    # 절대 코드에 직접 하드코딩하지 마세요!
    app_key = os.environ.get('KIS_APP_KEY')
    app_secret = os.environ.get('KIS_APP_SECRET')
    account_no = os.environ.get('KIS_ACCOUNT_NO')
    account_code = os.environ.get('KIS_ACCOUNT_CODE', '01')
    
    if not all([app_key, app_secret, account_no]):
        print("환경변수를 설정해주세요:")
        print("  export KIS_APP_KEY='your_app_key'")
        print("  export KIS_APP_SECRET='your_app_secret'")
        print("  export KIS_ACCOUNT_NO='your_account_no'")
        print("  export KIS_ACCOUNT_CODE='01'  # 선택사항, 기본값 01")
        return None
    
    try:
        # Agent 생성 (실전투자)
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
            # base_url은 기본값이 실전투자 URL
        )
        print("✅ Agent 생성 성공 (실전투자)")
        
        # 모의투자 Agent 생성 예시
        # agent_mock = Agent(
        #     app_key=app_key,
        #     app_secret=app_secret,
        #     account_no=account_no,
        #     account_code=account_code,
        #     base_url="https://openapivts.koreainvestment.com:29443"
        # )
        
        return agent
        
    except ValueError as e:
        print(f"❌ 필수 매개변수 오류: {e}")
        return None
    except RuntimeError as e:
        print(f"❌ 토큰 발급 실패: {e}")
        return None


def demonstrate_basic_features(agent: Agent):
    """기본 기능 시연"""
    if not agent:
        return
    
    print("\n" + "=" * 60)
    print("기본 기능 시연")
    print("=" * 60)
    
    # 1. 계좌 잔고 조회
    print("\n1. 계좌 잔고 조회")
    try:
        balance = agent.get_account_balance()
        if balance and balance.get('rt_cd') == '0':
            print("✅ 계좌 잔고 조회 성공")
            
            # 보유 종목 출력
            holdings = balance.get('output1', [])
            if holdings:
                print(f"   보유 종목 수: {len(holdings)}개")
                for stock in holdings[:3]:  # 상위 3개만 표시
                    print(f"   - {stock.get('prdt_name', 'N/A')}: {stock.get('hldg_qty', 0)}주")
            
            # 계좌 요약 정보
            summary = balance.get('output2', [{}])[0]
            if summary:
                total_asset = summary.get('tot_evlu_amt', 0)
                print(f"   총 평가금액: {int(total_asset):,}원")
        else:
            print("❌ 계좌 잔고 조회 실패")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    # 2. 주식 현재가 조회
    print("\n2. 주식 현재가 조회 (삼성전자)")
    try:
        price_info = agent.get_stock_price("005930")
        if price_info and price_info.get('rt_cd') == '0':
            output = price_info.get('output', {})
            current_price = output.get('stck_prpr', 'N/A')
            change_rate = output.get('prdy_ctrt', 'N/A')
            print(f"✅ 현재가: {current_price}원")
            print(f"   등락률: {change_rate}%")
        else:
            print("❌ 주식 현재가 조회 실패")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    # 3. 일별 시세 조회
    print("\n3. 일별 시세 조회 (카카오)")
    try:
        daily_price = agent.get_daily_price("035720", period="D")
        if daily_price and daily_price.get('rt_cd') == '0':
            output = daily_price.get('output2', [])
            if output:
                recent = output[0]  # 가장 최근 거래일
                print(f"✅ 날짜: {recent.get('stck_bsop_date', 'N/A')}")
                print(f"   종가: {recent.get('stck_clpr', 'N/A')}원")
                print(f"   거래량: {int(recent.get('acml_vol', 0)):,}주")
        else:
            print("❌ 일별 시세 조회 실패")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    # 4. Rate Limiter 상태 확인
    print("\n4. Rate Limiter 상태")
    try:
        status = agent.get_rate_limiter_status()
        if status:
            print(f"✅ Rate Limiter 활성화")
            print(f"   현재 요청률: {status.get('requests_per_second', 0)}/초")
            print(f"   총 요청 수: {status.get('total_requests', 0)}")
        else:
            print("ℹ️ Rate Limiter 비활성화 상태")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    print("\n" + "🚀 PyKIS 기본 사용 예제" + "\n")
    
    # Agent 생성
    agent = create_agent_from_env()
    
    # 기본 기능 시연
    if agent:
        demonstrate_basic_features(agent)
    else:
        print("\n⚠️ Agent 생성에 실패했습니다. API 키를 확인해주세요.")
    
    print("\n" + "=" * 60)
    print("예제 종료")
    print("=" * 60)


if __name__ == "__main__":
    main()