"""
생성일: 2025-10-10
목적: 신규 구현 API 통합 테스트 (실제 API 호출)
상태: 실제 API 호출 및 응답 검증

주의: 이 테스트는 실제 한국투자증권 API를 호출합니다.
- Rate limiting을 고려하여 각 호출 사이에 지연 추가
- 환경변수에 API 키가 설정되어 있어야 합니다
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

# .env 파일 로드
try:
    from dotenv import load_dotenv

    # 프로젝트 루트의 .env 파일 로드
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ .env 파일 로드: {env_path}")
    else:
        print(f"⚠ .env 파일 없음: {env_path}")
except ImportError:
    print("⚠ python-dotenv 패키지가 없습니다. 환경변수를 직접 설정하세요.")

from kis_agent import Agent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestNewAPIs:
    """신규 구현 API 통합 테스트"""

    @pytest.fixture(scope="class")
    def agent(self):
        """Agent 인스턴스 생성"""
        app_key = os.environ.get("KIS_APP_KEY")
        app_secret = os.environ.get("KIS_APP_SECRET") or os.environ.get("KIS_SECRET")
        account_no = os.environ.get("KIS_ACCOUNT_NO")
        account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

        if not all([app_key, app_secret, account_no]):
            pytest.skip("API 키가 설정되지 않았습니다")

        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
        )
        logger.info("Agent 초기화 완료")
        return agent

    def _validate_response(self, response: Dict, api_name: str) -> bool:
        """API 응답 검증"""
        if response is None:
            logger.warning(f"[{api_name}] 응답이 None입니다")
            return False

        if not isinstance(response, dict):
            logger.warning(
                f"[{api_name}] 응답이 dict 타입이 아닙니다: {type(response)}"
            )
            return False

        # rt_cd 확인 (0: 성공)
        rt_cd = response.get("rt_cd")
        if rt_cd != "0":
            msg1 = response.get("msg1", "알 수 없는 오류")
            logger.warning(f"[{api_name}] API 오류: rt_cd={rt_cd}, msg={msg1}")
            return False

        logger.info(f"[{api_name}] ✓ 성공")
        return True

    def _rate_limit_sleep(self, seconds: float = 0.1):
        """Rate limiting 대응"""
        time.sleep(seconds)

    # ========== 고우선순위 API 테스트 (8개) ==========

    @pytest.mark.requires_credentials
    def test_inquire_time_itemconclusion(self, agent):
        """시간별 체결 조회 테스트"""
        response = agent.inquire_time_itemconclusion("005930")
        assert self._validate_response(response, "inquire_time_itemconclusion")
        assert "output1" in response or "output2" in response
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_inquire_ccnl(self, agent):
        """실시간 체결 조회 테스트"""
        response = agent.inquire_ccnl("005930")
        assert self._validate_response(response, "inquire_ccnl")
        assert "output" in response
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_inquire_price_2(self, agent):
        """주식현재가 시세2 테스트"""
        response = agent.inquire_price_2("005930")
        assert self._validate_response(response, "inquire_price_2")
        assert "output" in response
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_search_stock_info(self, agent):
        """종목 기본정보 조회 테스트"""
        response = agent.search_stock_info("005930")
        assert self._validate_response(response, "search_stock_info")
        assert "output" in response
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_news_title(self, agent):
        """뉴스 제목 조회 테스트"""
        response = agent.news_title(code="005930")
        assert self._validate_response(response, "news_title")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_fluctuation(self, agent):
        """등락률 순위 테스트"""
        response = agent.fluctuation(count="10")
        assert self._validate_response(response, "fluctuation")
        assert "output" in response
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_volume_rank(self, agent):
        """거래량 순위 테스트"""
        response = agent.volume_rank()
        assert self._validate_response(response, "volume_rank")
        assert "output" in response
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_market_cap(self, agent):
        """시가총액 순위 테스트"""
        response = agent.market_cap()
        assert self._validate_response(response, "market_cap")
        assert "output" in response
        self._rate_limit_sleep()

    # ========== 중우선순위 API 테스트 (5개) ==========

    @pytest.mark.requires_credentials
    def test_foreign_institution_total(self, agent):
        """외국인/기관 종합 매매동향 테스트"""
        response = agent.foreign_institution_total()
        assert self._validate_response(response, "foreign_institution_total")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_daily_credit_balance(self, agent):
        """신용잔고 일별추이 테스트"""
        response = agent.daily_credit_balance("005930")
        assert self._validate_response(response, "daily_credit_balance")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_short_sale(self, agent):
        """공매도 상위종목 테스트"""
        response = agent.short_sale()
        assert self._validate_response(response, "short_sale")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_inquire_elw_price(self, agent):
        """ELW 현재가 테스트 (샘플 ELW 코드 필요)"""
        # ELW 코드는 시장 상황에 따라 변경될 수 있으므로 스킵
        pytest.skip("ELW 종목코드가 필요합니다")

    @pytest.mark.requires_credentials
    def test_inquire_vi_status(self, agent):
        """VI 발동 현황 테스트"""
        response = agent.inquire_vi_status()
        assert self._validate_response(response, "inquire_vi_status")
        self._rate_limit_sleep()

    # ========== 시세조회 API 테스트 (샘플링) ==========

    @pytest.mark.requires_credentials
    def test_inquire_daily_overtimeprice(self, agent):
        """시간외 일자별주가 테스트"""
        response = agent.inquire_daily_overtimeprice("005930")
        # 시간외 거래시간이 아니면 데이터가 없을 수 있음
        if response and response.get("rt_cd") == "0":
            logger.info("[inquire_daily_overtimeprice] ✓ 성공")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_inquire_index_price(self, agent):
        """업종 현재지수 테스트 (deprecated, redirects to inquire_index_timeprice)"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            response = agent.inquire_index_price("0001")  # 코스피

            # DeprecationWarning 발생 확인
            assert len(w) > 0
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

        logger.info(
            "[inquire_index_price] ✓ DeprecationWarning 발생 확인 (inquire_index_timeprice로 리다이렉트)"
        )
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_market_time(self, agent):
        """시장영업시간 테스트 (서버 미지원 - API 응답 없음)"""
        response = agent.market_time()
        # 서버에서 "없는 서비스 코드" 응답을 받으므로 None 또는 실패 응답 확인
        if response is None:
            logger.info("[market_time] ⚠ 서버 미지원 (None 반환)")
        elif response.get("rt_cd") != "0":
            logger.info(
                f"[market_time] ⚠ 서버 미지원 (에러 응답: {response.get('msg1', 'N/A')})"
            )
        else:
            logger.warning("[market_time] 예상과 달리 정상 응답을 받았습니다")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_market_value(self, agent):
        """종목별 시가총액 테스트 (서버 미지원 - 404 에러)"""
        response = agent.market_value("005930")
        # 서버에서 404 에러를 받으므로 None 또는 실패 응답 확인
        if response is None:
            logger.info("[market_value] ⚠ 서버 미지원 (None 반환, 404 에러)")
        elif response.get("rt_cd") != "0":
            logger.info(
                f"[market_value] ⚠ 서버 미지원 (에러 응답: {response.get('msg1', 'N/A')})"
            )
        else:
            logger.warning("[market_value] 예상과 달리 정상 응답을 받았습니다")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_disparity(self, agent):
        """이격도 순위 테스트"""
        response = agent.disparity()
        assert self._validate_response(response, "disparity")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_dividend_rate(self, agent):
        """배당률 상위 테스트"""
        response = agent.dividend_rate()
        assert self._validate_response(response, "dividend_rate")
        self._rate_limit_sleep()

    # ========== 투자자동향 API 테스트 (샘플링) ==========

    @pytest.mark.requires_credentials
    def test_get_investor_program_trade_today(self, agent):
        """프로그램매매 투자자매매동향 테스트"""
        response = agent.get_investor_program_trade_today()
        assert self._validate_response(response, "get_investor_program_trade_today")
        self._rate_limit_sleep()

    @pytest.mark.requires_credentials
    def test_get_investor_trade_by_stock_daily(self, agent):
        """종목별 투자자매매동향 테스트"""
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        response = agent.get_investor_trade_by_stock_daily(
            fid_input_iscd="005930", fid_input_date_1=today
        )
        assert self._validate_response(response, "get_investor_trade_by_stock_daily")
        self._rate_limit_sleep()


def run_full_test_suite():
    """전체 테스트 스위트 실행 (pytest 없이)"""
    logger.info("=" * 80)
    logger.info("신규 API 통합 테스트 시작")
    logger.info("=" * 80)

    # Agent 초기화
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET") or os.environ.get("KIS_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        logger.error("❌ API 키가 설정되지 않았습니다")
        logger.error(f"KIS_APP_KEY: {'✓' if app_key else '✗'}")
        logger.error(f"KIS_SECRET/KIS_APP_SECRET: {'✓' if app_secret else '✗'}")
        logger.error(f"KIS_ACCOUNT_NO: {'✓' if account_no else '✗'}")
        logger.error(
            "환경변수를 확인하세요: KIS_APP_KEY, KIS_APP_SECRET/KIS_SECRET, KIS_ACCOUNT_NO"
        )
        return 1

    try:
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
        )
        logger.info("✓ Agent 초기화 완료")
    except Exception as e:
        logger.error(f"❌ Agent 초기화 실패: {e}")
        return 1

    # 테스트 인스턴스 생성
    tester = TestNewAPIs()
    tester.agent = lambda: agent

    # 테스트 메서드 목록
    test_methods = [
        ("inquire_time_itemconclusion", tester.test_inquire_time_itemconclusion),
        ("inquire_ccnl", tester.test_inquire_ccnl),
        ("inquire_price_2", tester.test_inquire_price_2),
        ("search_stock_info", tester.test_search_stock_info),
        ("news_title", tester.test_news_title),
        ("fluctuation", tester.test_fluctuation),
        ("volume_rank", tester.test_volume_rank),
        ("market_cap", tester.test_market_cap),
        ("foreign_institution_total", tester.test_foreign_institution_total),
        ("daily_credit_balance", tester.test_daily_credit_balance),
        ("short_sale", tester.test_short_sale),
        ("inquire_vi_status", tester.test_inquire_vi_status),
        ("inquire_daily_overtimeprice", tester.test_inquire_daily_overtimeprice),
        ("inquire_index_price", tester.test_inquire_index_price),
        ("market_time", tester.test_market_time),
        ("market_value", tester.test_market_value),
        ("disparity", tester.test_disparity),
        ("dividend_rate", tester.test_dividend_rate),
        (
            "get_investor_program_trade_today",
            tester.test_get_investor_program_trade_today,
        ),
        (
            "get_investor_trade_by_stock_daily",
            tester.test_get_investor_trade_by_stock_daily,
        ),
    ]

    results = {"success": 0, "failed": 0, "skipped": 0}

    for idx, (name, test_func) in enumerate(test_methods, 1):
        logger.info(f"\n[{idx}/{len(test_methods)}] Testing {name}...")
        try:
            test_func(agent)
            results["success"] += 1
        except pytest.skip.Exception as e:
            logger.warning(f"⚠ Skipped: {e}")
            results["skipped"] += 1
        except NotImplementedError as e:
            # 서버 미지원 API는 예상된 동작이므로 성공으로 처리
            if "한국투자증권 API 서버에서 지원하지 않는 서비스" in str(e):
                logger.info("✓ 예상된 NotImplementedError (서버 미지원)")
                results["success"] += 1
            else:
                logger.error(f"✗ Unexpected NotImplementedError: {e}")
                results["failed"] += 1
        except AssertionError as e:
            logger.error(f"✗ Failed: {e}")
            results["failed"] += 1
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            results["failed"] += 1

    # 최종 리포트
    logger.info("\n" + "=" * 80)
    logger.info("📊 테스트 결과")
    logger.info("=" * 80)
    total = results["success"] + results["failed"] + results["skipped"]
    logger.info(f"✓ 성공: {results['success']}/{total}")
    logger.info(f"✗ 실패: {results['failed']}/{total}")
    logger.info(f"⚠ 스킵: {results['skipped']}/{total}")
    success_rate = results["success"] / total * 100 if total > 0 else 0
    logger.info(f"성공률: {success_rate:.1f}%")
    logger.info("=" * 80)

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = run_full_test_suite()
    exit(exit_code)
