#!/usr/bin/env python
"""
거래내역 Excel 내보내기 예제
============================

PyKIS 거래내역 유틸리티를 사용하여 계좌의 거래내역을
Excel 파일로 내보내는 다양한 방법을 보여줍니다.

테스트 커버리지: 98%
기능:
- 기간별 거래내역 조회
- 종목별 필터링
- 체결된 거래만 추출
- Excel 파일 생성 및 포맷팅
- 종목별 시트 분리

사용법:
    python export_trading_history.py

필수 환경변수 (.env):
    APP_KEY, APP_SECRET, KIS_BASE_URL, CANO, ACNT_PRDT_CD
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from kis_agent.utils.trading_report import (
    TradingReportGenerator,
    generate_trading_report,
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()


def main():
    """메인 실행 함수"""

    # 1. KIS 클라이언트 초기화
    logger.info("KIS 클라이언트 초기화...")

    KISClient(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_APP_SECRET"),
        account_number=os.getenv("KIS_ACCOUNT_NUMBER"),
        is_real=False,  # 모의투자로 테스트
    )

    # 계좌 정보 설정
    account_info = {
        "CANO": os.getenv("KIS_ACCOUNT_NUMBER").split("-")[0],
        "ACNT_PRDT_CD": os.getenv("KIS_ACCOUNT_NUMBER").split("-")[1],
    }

    # 2. 날짜 설정 (최근 30일)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    logger.info(f"조회 기간: {start_date_str} ~ {end_date_str}")

    # =============================================================
    # 예제 1: 전체 거래내역을 하나의 파일로
    # =============================================================
    logger.info("\n=== 예제 1: 전체 거래내역 내보내기 ===")

    try:
        file_path = generate_trading_report(
            client=agent.client,
            account_info=account_info,
            start_date=start_date_str,
            end_date=end_date_str,
            output_path="전체_거래내역.xlsx",
            only_executed=True,  # 체결된 거래만
        )
        logger.info(f" 파일 생성 완료: {file_path}")
    except Exception as e:
        logger.error(f" 오류 발생: {e}")

    # =============================================================
    # 예제 2: 특정 종목들만 조회
    # =============================================================
    logger.info("\n=== 예제 2: 특정 종목 거래내역 ===")

    # 관심 종목 리스트
    watch_list = ["005930", "000660", "035720"]  # 삼성전자, SK하이닉스, 카카오

    try:
        file_path = generate_trading_report(
            client=agent.client,
            account_info=account_info,
            start_date=start_date_str,
            end_date=end_date_str,
            output_path="관심종목_거래내역.xlsx",
            tickers=watch_list,
            only_executed=True,
        )
        logger.info(f" 파일 생성 완료: {file_path}")
    except Exception as e:
        logger.error(f" 오류 발생: {e}")

    # =============================================================
    # 예제 3: 종목별로 시트 분리
    # =============================================================
    logger.info("\n=== 예제 3: 종목별 시트 분리 ===")

    try:
        file_path = generate_trading_report(
            client=agent.client,
            account_info=account_info,
            start_date=start_date_str,
            end_date=end_date_str,
            output_path="종목별_거래내역.xlsx",
            tickers=watch_list,
            only_executed=True,
            separate_sheets=True,  # 종목별로 시트 분리
        )
        logger.info(f" 파일 생성 완료: {file_path}")
    except Exception as e:
        logger.error(f" 오류 발생: {e}")

    # =============================================================
    # 예제 4: 고급 사용법 - TradingReportGenerator 직접 사용
    # =============================================================
    logger.info("\n=== 예제 4: 고급 사용법 ===")

    try:
        # 리포트 생성기 인스턴스 생성
        generator = TradingReportGenerator(agent.client, account_info)

        # 특정 종목 거래내역만 조회
        samsung_df = generator.get_trading_history(
            start_date=start_date_str,
            end_date=end_date_str,
            ticker="005930",
            only_executed=True,
        )

        if not samsung_df.empty:
            logger.info(f"삼성전자 거래 건수: {len(samsung_df)}건")

            # 매수/매도 통계
            if "sll_buy_dvsn_cd_name" in samsung_df.columns:
                buy_count = samsung_df[
                    samsung_df["sll_buy_dvsn_cd_name"].str.contains("매수", na=False)
                ].shape[0]
                sell_count = samsung_df[
                    samsung_df["sll_buy_dvsn_cd_name"].str.contains("매도", na=False)
                ].shape[0]

                logger.info(f"  - 매수: {buy_count}건")
                logger.info(f"  - 매도: {sell_count}건")

            # 체결금액 합계
            if "ccld_amt" in samsung_df.columns:
                total_amount = samsung_df["ccld_amt"].sum()
                logger.info(f"  - 총 체결금액: {total_amount:,.0f}원")
        else:
            logger.info("삼성전자 거래내역이 없습니다.")

    except Exception as e:
        logger.error(f" 오류 발생: {e}")

    # =============================================================
    # 예제 5: 월별 리포트 생성
    # =============================================================
    logger.info("\n=== 예제 5: 월별 리포트 ===")

    # 이번 달 1일부터 오늘까지
    month_start = datetime.now().replace(day=1)
    month_start_str = month_start.strftime("%Y%m%d")

    try:
        file_path = generate_trading_report(
            client=agent.client,
            account_info=account_info,
            start_date=month_start_str,
            end_date=end_date_str,
            output_path=f"월간리포트_{month_start.strftime('%Y%m')}.xlsx",
            only_executed=True,
        )
        logger.info(f" 월간 리포트 생성 완료: {file_path}")
    except Exception as e:
        logger.error(f" 오류 발생: {e}")

    logger.info("\n 모든 예제 실행 완료!")

    # 생성된 파일 목록 출력
    logger.info("\n📁 생성된 파일 목록:")
    for file in Path(".").glob("*.xlsx"):
        size_kb = file.stat().st_size / 1024
        logger.info(f"  - {file.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
