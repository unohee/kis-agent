#!/usr/bin/env python3
"""
계좌 관련 API 테스트 스크립트
작성일: 2025-01-08
테스트 대상: 새로 추가된 계좌 관련 API 메서드들
"""

import sys
import os
from datetime import datetime, timedelta

# pykis 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent

def test_account_apis():
    """계좌 관련 API 테스트"""
    
    print("=" * 80)
    print("계좌 관련 API 테스트 시작")
    print("=" * 80)
    
    # Agent 초기화
    agent = Agent()
    
    # 테스트용 날짜 설정 (최근 30일)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    # 테스트 종목코드
    test_stock = "005930"  # 삼성전자
    
    print(f"\n테스트 기간: {start_date} ~ {end_date}")
    print(f"테스트 종목: {test_stock}")
    print("-" * 80)
    
    # 1. 일별주문체결 조회
    print("\n1. 일별주문체결 조회 테스트")
    try:
        result = agent.inquire_daily_ccld(start_date, end_date)
        if result is not None:
            print(f"✅ 성공: {len(result)} 건의 주문체결 내역 조회")
            if len(result) > 0:
                print(f"   최근 체결: {result.iloc[0].to_dict()}")
        else:
            print("⚠️ 주문체결 내역 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 2. 기간별 매매손익 조회
    print("\n2. 기간별 매매손익 조회 테스트")
    try:
        result = agent.inquire_period_trade_profit(start_date, end_date)
        if result is not None:
            print(f"✅ 성공: {len(result)} 건의 매매손익 조회")
            if len(result) > 0:
                total_profit = result['sell_pnl_smtl'].astype(float).sum() if 'sell_pnl_smtl' in result.columns else 0
                print(f"   총 실현손익: {total_profit:,.0f}원")
        else:
            print("⚠️ 매매손익 데이터 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 3. 실현손익 잔고 조회
    print("\n3. 실현손익 잔고 조회 테스트")
    try:
        result = agent.inquire_balance_rlz_pl()
        if result is not None:
            print(f"✅ 성공: {len(result)} 종목 보유")
            if len(result) > 0:
                print("   보유종목 실현손익:")
                for idx, row in result.head(3).iterrows():
                    if 'pdno' in row and 'prdt_name' in row:
                        print(f"   - {row.get('prdt_name', 'N/A')}({row.get('pdno', 'N/A')})")
        else:
            print("⚠️ 보유종목 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 4. 매도가능수량 조회
    print(f"\n4. 매도가능수량 조회 테스트 (종목: {test_stock})")
    try:
        result = agent.inquire_psbl_sell(test_stock)
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            print(f"✅ 성공:")
            print(f"   - 매도가능수량: {output.get('ord_psbl_qty', 0)}주")
            print(f"   - 평균단가: {output.get('pchs_avg_pric', 0)}원")
        else:
            print(f"⚠️ 해당 종목 미보유 또는 조회 실패")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 5. 신용매수가능 조회
    print(f"\n5. 신용매수가능 조회 테스트 (종목: {test_stock})")
    try:
        result = agent.inquire_credit_psamount(test_stock)
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            print(f"✅ 성공:")
            print(f"   - 신용매수가능금액: {output.get('crdt_ord_psbl_amt', 0)}원")
            print(f"   - 최대매수가능수량: {output.get('max_buy_qty', 0)}주")
        else:
            print(f"⚠️ 신용거래 미가능 또는 조회 실패")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 6. 통합증거금 현황 조회
    print("\n6. 통합증거금 현황 조회 테스트")
    try:
        result = agent.inquire_intgr_margin()
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            print(f"✅ 성공:")
            print(f"   - 증거금률: {output.get('dpsit_rate', 0)}%")
            print(f"   - 담보비율: {output.get('cltr_rate', 0)}%")
        else:
            print(f"⚠️ 통합증거금 데이터 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 7. 기간별 권리현황 조회
    print("\n7. 기간별 권리현황 조회 테스트")
    try:
        result = agent.inquire_period_rights(start_date, end_date)
        if result is not None:
            print(f"✅ 성공: {len(result)} 건의 권리현황 조회")
        else:
            print("⚠️ 권리현황 데이터 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 8. 정정취소가능 주문 조회
    print("\n8. 정정취소가능 주문 조회 테스트")
    try:
        result = agent.inquire_psbl_rvsecncl()
        if result and result.get('rt_cd') == '0':
            output1 = result.get('output1', [])
            print(f"✅ 성공: {len(output1)} 건의 정정취소 가능 주문")
            if len(output1) > 0:
                print(f"   최근 주문:")
                for order in output1[:3]:
                    print(f"   - {order.get('prdt_name', 'N/A')} {order.get('ord_qty', 0)}주")
        else:
            print("⚠️ 정정취소 가능한 주문 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 9. 예약주문 조회
    print("\n9. 예약주문 조회 테스트")
    try:
        result = agent.order_resv_ccnl()
        if result and result.get('rt_cd') == '0':
            output = result.get('output', [])
            print(f"✅ 성공: {len(output)} 건의 예약주문")
        else:
            print("⚠️ 예약주문 없음")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    print("\n" + "=" * 80)
    print("계좌 관련 API 테스트 완료")
    print("=" * 80)

if __name__ == "__main__":
    # RTX_ENV 가상환경 활성화 확인
    if 'RTX_ENV' not in sys.prefix:
        print("⚠️ 경고: RTX_ENV 가상환경이 활성화되지 않았습니다.")
        print("source ~/RTX_ENV/bin/activate 명령을 실행한 후 다시 시도하세요.")
        sys.exit(1)
    
    test_account_apis()