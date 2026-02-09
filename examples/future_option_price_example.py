#!/usr/bin/env python3
"""
선물옵션 시세 조회 예제

이 예제는 Pykis를 사용하여 선물옵션 시세를 조회하는 방법을 보여줍니다.

Note: 이 예제는 레거시 StockAPI를 사용합니다. 새 코드에서는 Agent 사용을 권장합니다.
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kis_agent.core.client import KISClient
from kis_agent.stock import LegacyStockAPI as StockAPI


def main():
    """선물옵션 시세 조회 예제"""

    # KISClient 초기화
    client = KISClient()

    # StockAPI 초기화 (계좌 정보는 선택사항)
    stock_api = StockAPI(client, {})

    print("선물옵션 시세 조회")
    print("=" * 50)

    # 1. 지수선물 시세 조회 (기본값)
    print("\n1. 지수선물 시세 조회 (기본값: 101S09)")
    result = stock_api.get_future_option_price()

    if result and result.get("rt_cd") == "0":
        # output3에 KOSPI200 지수선물 정보가 들어있음
        output = (
            result.get("output3") or result.get("output2") or result.get("output", {})
        )
        if output:
            print(f"종목명: {output.get('hts_kor_isnm', 'N/A')}")
            print(f"현재가: {output.get('bstp_nmix_prpr', 'N/A')}")
            print(f"전일대비: {output.get('bstp_nmix_prdy_vrss', 'N/A')}")
            print(f"등락률: {output.get('bstp_nmix_prdy_ctrt', 'N/A')}%")
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 2. 다른 지수선물 종목 조회 (현재 거래되는 종목)
    print("\n2. 다른 지수선물 종목 조회 (101S12)")
    result = stock_api.get_future_option_price(
        market_div_code="F", input_iscd="101S12"  # 지수선물  # 2024년 12월 만기 선물
    )

    if result and result.get("rt_cd") == "0":
        # output3에 KOSPI200 지수선물 정보가 들어있음
        output = (
            result.get("output3") or result.get("output2") or result.get("output", {})
        )
        if output:
            print(f"종목명: {output.get('hts_kor_isnm', 'N/A')}")
            print(f"현재가: {output.get('bstp_nmix_prpr', 'N/A')}")
            print(f"전일대비: {output.get('bstp_nmix_prdy_vrss', 'N/A')}")
            print(f"등락률: {output.get('bstp_nmix_prdy_ctrt', 'N/A')}%")
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 3. 지수옵션 시세 조회 (현재 거래되는 종목)
    print("\n3. 지수옵션 시세 조회 (201S12370)")
    result = stock_api.get_future_option_price(
        market_div_code="O",  # 지수옵션
        input_iscd="201S12370",  # 2024년 12월 만기 콜옵션
    )

    if result and result.get("rt_cd") == "0":
        # output3에 KOSPI200 지수선물 정보가 들어있음
        output = (
            result.get("output3") or result.get("output2") or result.get("output", {})
        )
        if output:
            print(f"종목명: {output.get('hts_kor_isnm', 'N/A')}")
            print(f"현재가: {output.get('bstp_nmix_prpr', 'N/A')}")
            print(f"전일대비: {output.get('bstp_nmix_prdy_vrss', 'N/A')}")
            print(f"등락률: {output.get('bstp_nmix_prdy_ctrt', 'N/A')}%")
        else:
            print("데이터가 없습니다.")
    else:
        print(
            f"조회 실패: {result.get('msg1', '알 수 없는 오류') if result else '응답 없음'}"
        )

    # 4. 시장분류코드 정보
    print("\n4. 시장분류코드 정보")
    market_codes = {
        "F": "지수선물",
        "O": "지수옵션",
        "JF": "주식선물",
        "JO": "주식옵션",
    }

    print("사용 가능한 시장분류코드:")
    for code, name in market_codes.items():
        print(f"  {code}: {name}")

    print("\n5. 종목코드 형식 안내")
    print("선물 종목코드: 6자리 (예: 101S03, 101S06, 101S09)")
    print("옵션 종목코드: 9자리 (예: 201S03370, 201S03380)")

    print("\n6. KOSPI 200 현물지수와 선물 베이시스 계산 예시")
    print("--------------------------------------------------")

    from kis_agent.stock import get_kospi200_futures_code

    # 현재 날짜 기준으로 가장 가까운 선물코드 생성 (두 번째 주 목요일 만기 규칙 적용)
    current_futures_code = get_kospi200_futures_code()
    print(f"현재 날짜 기준 가장 가까운 선물코드: {current_futures_code}")

    # 실제 거래되고 있는 종목코드로 테스트 (2025년 9월물)
    actual_futures_code = "101W09"
    print(f"실제 거래되는 종목코드: {actual_futures_code}")

    # 선물옵션 시세 조회 (output1에 선물 상세 정보, output3에 KOSPI200 지수 정보가 포함됨)
    futures_info = stock_api.get_future_option_price(input_iscd=actual_futures_code)
    print(f"선물 시세 API 응답: {futures_info}")

    # 베이시스 정보 추출 (output1 우선, 없으면 직접 계산)
    basis_value = None
    kospi200_value = None
    futures_value = None
    direct_basis = None  # 직접 계산한 베이시스

    if futures_info and "output1" in futures_info and futures_info["output1"]:
        # output1에 선물 상세 정보가 있음
        futures_data = futures_info["output1"]
        futures_value = float(futures_data.get("futs_prpr", 0))
        basis_value = futures_data.get("mrkt_basis") or futures_data.get("basis")
        if basis_value:
            basis_value = float(basis_value)
        print(f"선물 현재가 (output1에서): {futures_value}")
        print(f"API 제공 베이시스: {basis_value}")

    if futures_info and "output3" in futures_info:
        # output3에 KOSPI200 지수 정보가 있음
        kospi200_data = futures_info["output3"]
        kospi200_value = float(kospi200_data.get("bstp_nmix_prpr", 0))
        print(f"KOSPI 200 현물지수 (output3에서): {kospi200_value}")

    # output1(선물 현재가)와 output3(KOSPI200 현물지수)로 직접 계산한 베이시스도 함께 출력
    # 변경 이유: 실제 API 제공값과 직접 계산값 비교를 위해
    if futures_value is not None and kospi200_value is not None:
        direct_basis = futures_value - kospi200_value
        print(f"직접 계산한 베이시스(선물-현물): {direct_basis:.2f}")

    # 베이시스 계산 및 출력
    if basis_value is not None:
        print(f"KOSPI 200 현물지수: {kospi200_value}")
        print(f"지수선물({actual_futures_code}) 현재가: {futures_value}")
        print(f"베이시스(API 제공): {basis_value}")
        if direct_basis is not None:
            print(f"베이시스(직접 계산): {direct_basis:.2f}")
    elif kospi200_value is not None and futures_value is not None:
        # API에서 베이시스를 제공하지 않으면 직접 계산
        print(f"KOSPI 200 현물지수: {kospi200_value}")
        print(f"지수선물({actual_futures_code}) 현재가: {futures_value}")
        print(f"베이시스(직접 계산): {direct_basis:.2f}")
    else:
        print("KOSPI 200 또는 선물 시세 조회 실패")
        if kospi200_value is None:
            print("KOSPI 200 현물지수 조회 실패")
        if futures_value is None:
            print("선물 시세 조회 실패")

    # 베이시스란? 선물가격 - 현물가격 (양수: 콘탱고, 음수: 백워데이션)
    # 이 예제는 실제 투자에 참고용으로만 사용하세요.
    # 변경 이유: output3에서 직접 측정한 베이시스도 함께 확인 가능하도록 개선


if __name__ == "__main__":
    main()
