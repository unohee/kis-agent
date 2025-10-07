#!/usr/bin/env python3
"""
국내주식업종기간별시세 조회 예제

이 예제는 Pykis를 사용하여 국내주식업종기간별시세를 조회하는 방법을 보여줍니다.
"""

import os
import sys
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import KISClient, StockAPI


def main():
    """국내주식업종기간별시세 조회 예제"""

    # KISClient 초기화
    client = KISClient()

    # StockAPI 초기화 (계좌 정보는 선택사항)
    stock_api = StockAPI(client, {})

    # end_date는 항상 오늘 날짜로 설정
    end_date = datetime.now().strftime('%Y%m%d')
    # start_date는 최근 1년 전으로 설정
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

    print(f"업종기간별시세 조회: {start_date} ~ {end_date}")
    print("=" * 50)

    # 1. KOSPI200 업종 일봉 데이터 조회
    print("\n1. KOSPI200 업종 일봉 데이터 조회")
    result = stock_api.get_daily_index_chart_price(
        market_div_code="U",      # 업종
        input_iscd="0007",        # KOSPI200
        start_date=start_date,
        end_date=end_date,
        period_div_code="D"       # 일봉
    )

    if result and result.get('rt_cd') == '0':
        output = result.get('output2', result.get('output', []))
        if isinstance(output, list) and output:
            print(f"조회된 데이터 수: {len(output)}건")
            print("최근 5일 데이터:")
            for i, data in enumerate(output[:5]):
                print(f"  {i+1}. 날짜: {data.get('stck_bsop_date', 'N/A')}, "
                      f"종가: {data.get('bstp_nmix_prpr', 'N/A')}, "
                      f"거래량: {data.get('acml_vol', 'N/A')}")
        else:
            print("데이터가 없습니다.")
    else:
        print(f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}")

    # 2. 대형주 업종 주봉 데이터 조회
    print("\n2. 대형주 업종 주봉 데이터 조회")
    result = stock_api.get_daily_index_chart_price(
        market_div_code="U",      # 업종
        input_iscd="0002",        # 대형주
        start_date=start_date,
        end_date=end_date,
        period_div_code="W"       # 주봉
    )

    if result and result.get('rt_cd') == '0':
        output = result.get('output2', result.get('output', []))
        if isinstance(output, list) and output:
            print(f"조회된 데이터 수: {len(output)}건")
            print("최근 3주 데이터:")
            for i, data in enumerate(output[:3]):
                print(f"  {i+1}. 주차: {data.get('stck_bsop_date', 'N/A')}, "
                      f"종가: {data.get('bstp_nmix_prpr', 'N/A')}, "
                      f"거래량: {data.get('acml_vol', 'N/A')}")
        else:
            print("데이터가 없습니다.")
    else:
        print(f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}")

    # 3. 업종코드별 조회 예시
    print("\n3. 주요 업종코드 정보 (기본: KOSPI200)")
    sector_codes = {
        "0007": "KOSPI200 (기본)",
        "0001": "종합",
        "0002": "대형주",
        "0003": "중형주",
        "0004": "소형주",
        "0005": "KOSPI",
        "0006": "KOSDAQ",
        "0008": "KOSPI100",
        "0009": "KOSPI50",
        "0010": "KOSDAQ150"
    }

    print("사용 가능한 주요 업종코드:")
    for code, name in sector_codes.items():
        print(f"  {code}: {name}")

if __name__ == "__main__":
    main()
