#!/usr/bin/env python3
"""
국내업종 시간별지수 (틱) 조회 예제

이 예제는 Pykis를 사용하여 국내업종 시간별지수(틱) 데이터를 조회하는 방법을 보여줍니다.
API: /uapi/domestic-stock/v1/quotations/inquire-index-tickprice
TR: FHPUP02110100

생성일: 2025-10-20

Note: 이 예제는 레거시 StockAPI를 사용합니다. 새 코드에서는 Agent 사용을 권장합니다.
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis.core.client import KISClient
from pykis.stock import LegacyStockAPI as StockAPI


def main():
    """국내업종 시간별지수(틱) 조회 예제"""

    # KISClient 초기화
    client = KISClient()

    # StockAPI 초기화 (계좌 정보는 선택사항)
    stock_api = StockAPI(client, {})

    print("국내업종 시간별지수(틱) 조회")
    print("=" * 60)

    # 1. KOSPI (거래소) 시간별지수 조회
    print("\n1. KOSPI (거래소) 시간별지수 조회")
    result = stock_api.inquire_index_tickprice(
        index_code="0001", market="U"  # 0001: 거래소  # U: 업종
    )

    if result and result.get("rt_cd") == "0":
        output = result.get("output2", result.get("output", []))
        if isinstance(output, list) and output:
            print(f"조회된 틱 데이터 수: {len(output)}건")
            print("\n최근 5개 틱 데이터:")
            for i, data in enumerate(output[:5]):
                print(
                    f"  {i+1}. 시간: {data.get('stck_cntg_hour', 'N/A')}, "
                    f"지수: {data.get('bstp_nmix_prpr', 'N/A')}, "
                    f"거래량: {data.get('cntg_vol', 'N/A')}"
                )
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 2. KOSDAQ 시간별지수 조회
    print("\n2. KOSDAQ 시간별지수 조회")
    result = stock_api.inquire_index_tickprice(
        index_code="1001", market="U"  # 1001: 코스닥
    )

    if result and result.get("rt_cd") == "0":
        output = result.get("output2", result.get("output", []))
        if isinstance(output, list) and output:
            print(f"조회된 틱 데이터 수: {len(output)}건")
            print("\n최근 5개 틱 데이터:")
            for i, data in enumerate(output[:5]):
                print(
                    f"  {i+1}. 시간: {data.get('stck_cntg_hour', 'N/A')}, "
                    f"지수: {data.get('bstp_nmix_prpr', 'N/A')}, "
                    f"거래량: {data.get('cntg_vol', 'N/A')}"
                )
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 3. KOSPI 200 시간별지수 조회
    print("\n3. KOSPI 200 시간별지수 조회")
    result = stock_api.inquire_index_tickprice(
        index_code="2001", market="U"  # 2001: 코스피200
    )

    if result and result.get("rt_cd") == "0":
        output = result.get("output2", result.get("output", []))
        if isinstance(output, list) and output:
            print(f"조회된 틱 데이터 수: {len(output)}건")
            print("\n최근 5개 틱 데이터:")
            for i, data in enumerate(output[:5]):
                print(
                    f"  {i+1}. 시간: {data.get('stck_cntg_hour', 'N/A')}, "
                    f"지수: {data.get('bstp_nmix_prpr', 'N/A')}, "
                    f"거래량: {data.get('cntg_vol', 'N/A')}"
                )
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 4. KSQ150 시간별지수 조회
    print("\n4. KSQ150 시간별지수 조회")
    result = stock_api.inquire_index_tickprice(
        index_code="3003", market="U"  # 3003: KSQ150
    )

    if result and result.get("rt_cd") == "0":
        output = result.get("output2", result.get("output", []))
        if isinstance(output, list) and output:
            print(f"조회된 틱 데이터 수: {len(output)}건")
            print("\n최근 5개 틱 데이터:")
            for i, data in enumerate(output[:5]):
                print(
                    f"  {i+1}. 시간: {data.get('stck_cntg_hour', 'N/A')}, "
                    f"지수: {data.get('bstp_nmix_prpr', 'N/A')}, "
                    f"거래량: {data.get('cntg_vol', 'N/A')}"
                )
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 5. 지수코드 정보
    print("\n5. 사용 가능한 지수코드")
    index_codes = {
        "0001": "거래소 (KOSPI)",
        "1001": "코스닥 (KOSDAQ)",
        "2001": "코스피200 (KOSPI200)",
        "3003": "KSQ150",
    }

    print("지수코드 목록:")
    for code, name in index_codes.items():
        print(f"  {code}: {name}")

    # 6. 주요 데이터 필드 설명
    print("\n6. 주요 응답 데이터 필드")
    print("  - stck_cntg_hour: 체결 시간 (HHMMSS)")
    print("  - bstp_nmix_prpr: 업종지수 현재가")
    print("  - bstp_nmix_prdy_vrss: 전일대비")
    print("  - bstp_nmix_prdy_ctrt: 전일대비율")
    print("  - cntg_vol: 체결량")
    print("  - acml_vol: 누적 거래량")
    print("  - acml_tr_pbmn: 누적 거래대금")

    print("\n7. 시간별지수 활용 예시")
    print("  - 실시간 지수 흐름 모니터링")
    print("  - 시간대별 변동성 분석")
    print("  - 거래량 패턴 분석")
    print("  - 알고리즘 트레이딩 지표")


if __name__ == "__main__":
    main()
