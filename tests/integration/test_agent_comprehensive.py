"""
PyKIS Agent 종합 테스트

이 테스트 파일은 PyKIS Agent의 모든 주요 기능을 검증합니다.
현재 Agent facade 패턴에 맞게 작성되었습니다.

사용 예시:
    >>> pytest tests/integration/test_agent_comprehensive.py -v
"""

import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import pytest

from kis_agent import Agent

pytestmark = pytest.mark.requires_credentials


@pytest.fixture(scope="session")
def agent():
    """Agent 인스턴스를 제공하는 fixture"""
    # 환경변수에서 API 키 가져오기
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        pytest.skip(
            "필수 환경변수가 설정되지 않았습니다: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO"
        )

    return Agent(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        account_code=account_code,
    )


@pytest.fixture(scope="session")
def test_stock():
    """테스트용 종목 코드"""
    return "005930"  # 삼성전자


@pytest.fixture(scope="session")
def test_date():
    """테스트용 날짜"""
    return datetime.now().strftime("%Y%m%d")


def validate_api_response(response, expected_rt_cd="0", require_output=True):
    """API 응답을 검증하는 헬퍼 함수"""
    if response is None:
        return False, "결과 없음"

    # DataFrame은 성공으로 간주
    if isinstance(response, pd.DataFrame):
        return len(response) > 0, f"DataFrame 길이: {len(response)}"

    # 딕셔너리 형태의 응답
    if isinstance(response, dict):
        rt_cd = response.get("rt_cd")
        if rt_cd == expected_rt_cd:
            if require_output:
                return (
                    "output" in response
                    or "output1" in response
                    or "output2" in response
                ), f"rt_cd={rt_cd}"
            return True, f"rt_cd={rt_cd}"
        else:
            return False, f"rt_cd={rt_cd}, msg={response.get('msg1', '')}"

    # tuple, list 등 다른 타입들은 성공으로 간주
    return True, f"타입: {type(response).__name__}"


class TestStockBasicInfo:
    """주식 기본 정보 테스트"""

    def test_get_stock_price(self, agent, test_stock):
        """주식 현재가 조회 테스트"""
        result = agent.get_stock_price(test_stock)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"주식 현재가 조회 실패: {msg}"

        # DataFrame 또는 딕셔너리 형태 모두 허용
        if isinstance(result, pd.DataFrame):
            assert len(result) > 0
        elif isinstance(result, dict) and "output" in result:
            assert "stck_prpr" in result["output"]  # 현재가 필드 확인

    def test_get_daily_price(self, agent, test_stock):
        """일별 시세 조회 테스트"""
        result = agent.get_daily_price(test_stock)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"일별 시세 조회 실패: {msg}"

        # DataFrame 또는 딕셔너리 형태 모두 허용
        if isinstance(result, pd.DataFrame):
            assert len(result) > 0
        elif isinstance(result, dict) and "output" in result:
            assert isinstance(result["output"], list)
            assert len(result["output"]) > 0

            # 첫 번째 항목의 필드 검증
            first_item = result["output"][0]
            required_fields = ["stck_bsop_date", "stck_clpr", "acml_vol"]
            for field in required_fields:
                if field in first_item:  # 필드가 있으면 검증, 없어도 통과
                    assert first_item[field] is not None

    def test_get_minute_price(self, agent, test_stock):
        """분봉 시세 조회 테스트"""
        result = agent.get_minute_price(test_stock, "153000")
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"분봉 시세 조회 실패: {msg}"
        assert "output1" in result or "output2" in result

    def test_get_stock_member(self, agent, test_stock):
        """거래원 정보 조회 테스트"""
        result = agent.get_stock_member(test_stock)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"거래원 정보 조회 실패: {msg}"

        output = result["output"]
        # 매도/매수 거래원 정보 확인
        assert "seln_mbcr_name1" in output  # 매도 1위 거래원명
        assert "shnu_mbcr_name1" in output  # 매수 1위 거래원명


class TestProgramTrade:
    """프로그램 매매 테스트"""

    def test_get_program_trade_by_stock(self, agent, test_stock):
        """종목별 프로그램매매추이 조회 테스트"""
        result = agent.get_program_trade_by_stock(test_stock)
        is_valid, msg = validate_api_response(result, require_output=False)
        assert is_valid, f"프로그램매매추이 조회 실패: {msg}"

        assert isinstance(result["output"], list)
        if len(result["output"]) > 0:
            first_item = result["output"][0]
            assert "whol_smtn_ntby_qty" in first_item  # 순매수량

    def test_get_program_trade_daily_summary(self, agent, test_stock, test_date):
        """일별 프로그램 매매 집계 테스트"""
        result = agent.get_program_trade_daily_summary(test_stock, test_date)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"일별 프로그램 매매 집계 조회 실패: {msg}"

    def test_get_program_trade_market_daily(self, agent):
        """시장 전체 프로그램 매매 현황 테스트"""
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        result = agent.get_program_trade_market_daily(start_date, end_date)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"시장 전체 프로그램 매매 현황 조회 실패: {msg}"


class TestMemberTransaction:
    """회원사 및 거래 정보 테스트"""

    def test_get_member_transaction(self, agent, test_stock):
        """회원사 매매 정보 조회 테스트"""
        result = agent.get_member_transaction(test_stock)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"회원사 매매 정보 조회 실패: {msg}"

    def test_get_volume_power(self, agent):
        """체결강도 순위 조회 테스트"""
        result = agent.get_volume_power(0)
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"체결강도 순위 조회 실패: {msg}"


class TestAccountInfo:
    """계좌 관련 테스트"""

    def test_get_account_balance(self, agent):
        """계좌 잔고 조회 테스트"""
        result = agent.get_account_balance()

        # DataFrame 또는 dict 형태로 반환될 수 있음
        assert result is not None, "계좌 잔고 조회 결과 없음"

        if isinstance(result, pd.DataFrame):
            assert len(result.columns) > 0, "계좌 잔고 DataFrame이 비어있음"
            # 주요 컬럼들이 있는지 확인
            expected_columns = ["pdno", "prdt_name", "hldg_qty"]
            for col in expected_columns:
                if col in result.columns:
                    assert True  # 적어도 하나의 예상 컬럼이 있으면 성공
                    break
            else:
                pytest.fail("예상 컬럼들이 없습니다")


class TestAdditionalStockInfo:
    """추가 주식 정보 테스트"""

    def test_get_orderbook(self, agent, test_stock):
        """호가 정보 조회 테스트"""
        result = agent.get_orderbook(test_stock)
        assert result is not None, "호가 정보 조회 결과 없음"

        if isinstance(result, pd.DataFrame):
            assert len(result) > 0, "호가 정보 DataFrame이 비어있음"

    def test_get_stock_info(self, agent, test_stock):
        """주식 기본 정보 조회 테스트"""
        result = agent.get_stock_info(test_stock)
        assert result is not None, "주식 기본 정보 조회 결과 없음"

        if isinstance(result, pd.DataFrame):
            assert len(result) > 0, "주식 기본 정보 DataFrame이 비어있음"


class TestInvestorInfo:
    """투자자별 매매동향 테스트"""

    def test_get_stock_investor(self, agent, test_stock):
        """투자자별 매매동향 조회 테스트"""
        result = agent.get_stock_investor(test_stock)
        assert result is not None, "투자자별 매매동향 조회 결과 없음"

        if isinstance(result, pd.DataFrame):
            assert len(result) > 0, "투자자별 매매동향 DataFrame이 비어있음"
            # 주요 컬럼 확인
            expected_columns = ["prsn_ntby_qty", "frgn_ntby_qty", "orgn_ntby_qty"]
            for col in expected_columns:
                if col in result.columns:
                    assert True
                    break
            else:
                pytest.fail("예상 컬럼들이 없습니다")

    def test_get_foreign_broker_net_buy(self, agent, test_stock):
        """외국계 브로커 순매수 조회 테스트"""
        result = agent.get_foreign_broker_net_buy(test_stock)
        assert result is not None, "외국계 브로커 순매수 조회 결과 없음"

        # API가 tuple (순매수량, 상세정보) 형태로 반환
        assert isinstance(
            result, tuple
        ), "외국계 브로커 순매수 조회 결과가 tuple이 아님"
        assert len(result) == 2, "tuple 길이가 2가 아님"

        net_buy_amount, detail_info = result
        assert isinstance(net_buy_amount, (int, float)), "순매수량이 숫자가 아님"
        assert isinstance(detail_info, dict), "상세정보가 dict가 아님"

        # 상세정보 키 확인
        required_keys = ["brokers", "buy_total", "sell_total", "total_brokers_found"]
        for key in required_keys:
            assert key in detail_info, f"필수 키 '{key}'가 결과에 없음"

        # 브로커 정보 확인
        assert isinstance(detail_info["brokers"], list), "브로커 정보가 리스트가 아님"
        assert len(detail_info["brokers"]) > 0, "브로커 정보가 비어있음"

    def test_get_possible_order_amount(self, agent, test_stock):
        """매수 가능 주문 조회 테스트"""
        result = agent.get_possible_order_amount(test_stock, "10000")
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"매수 가능 주문 조회 실패: {msg}"


class TestConditionSearch:
    """조건검색 테스트"""

    def test_get_condition_stocks_default(self, agent):
        """조건검색 종목 조회 (기본 파라미터) 테스트"""
        result = agent.get_condition_stocks()
        assert result is not None, "조건검색 결과 없음"

        if isinstance(result, list):
            # 결과가 있든 없든 list 형태로 반환되면 성공
            assert True

    def test_get_condition_stocks_explicit(self, agent):
        """조건검색 종목 조회 (명시적 파라미터) 테스트"""
        result = agent.get_condition_stocks("unohee", 0, "N")
        assert result is not None, "조건검색 결과 없음"

        if isinstance(result, list):
            # 결과가 있든 없든 list 형태로 반환되면 성공
            assert True


class TestChartData:
    """차트 데이터 테스트"""

    def test_get_minute_price(self, agent, test_stock):
        """분봉 차트 조회 테스트"""
        result = agent.get_minute_price(test_stock, "153000")
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"분봉 차트 조회 실패: {msg}"

    def test_fetch_minute_data(self, agent, test_stock, test_date):
        """분봉 데이터 수집 테스트"""
        result = agent.fetch_minute_data(test_stock, test_date)
        assert result is not None, "분봉 데이터 수집 결과 없음"

        if isinstance(result, pd.DataFrame) and not result.empty:
            # DataFrame의 기본 구조 확인
            expected_columns = ["stck_bsop_date", "stck_cntg_hour", "stck_prpr"]
            for col in expected_columns:
                if col in result.columns:
                    assert True
                    break
            else:
                pytest.fail("예상 컬럼들이 없습니다")
        elif isinstance(result, dict):
            assert "output2" in result, "분봉 데이터에 output2가 없습니다"
        elif isinstance(result, pd.DataFrame) and result.empty:
            pass
        else:
            pytest.fail("결과가 DataFrame도 아니고, output2를 포함한 dict도 아닙니다.")

    def test_init_minute_db(self, agent):
        """분봉 DB 초기화 테스트"""
        result = agent.init_minute_db()
        assert isinstance(result, bool), "DB 초기화 결과가 boolean이 아님"

    def test_migrate_minute_csv_to_db(self, agent, test_stock):
        """CSV to DB 마이그레이션 테스트"""
        result = agent.migrate_minute_csv_to_db(test_stock)
        assert isinstance(result, bool), "마이그레이션 결과가 boolean이 아님"


class TestUtilities:
    """기타 유틸리티 테스트"""

    @pytest.mark.parametrize(
        "test_date, expected",
        [
            ("20250705", True),  # Saturday
            ("20250706", True),  # Sunday
            ("20250707", False),  # Monday
        ],
    )
    def test_is_holiday(self, agent, test_date, expected):
        """휴장일 확인 테스트"""
        result = agent.is_holiday(test_date)
        assert result == expected, f"휴장일 확인 결과가 올바르지 않음: {test_date}"

    def test_classify_broker(self):
        """거래원 분류 테스트"""
        test_cases = [
            ("키움증권", "리테일/국내기관"),
            ("골드만삭스", "외국계"),
            ("삼성증권", "리테일/국내기관"),
        ]

        for broker_name, expected_category in test_cases:
            result = Agent.classify_broker(broker_name)
            assert (
                expected_category in result
            ), f"거래원 분류 오류: {broker_name} -> {result}"


class TestMarketInfo:
    """시장 정보 테스트"""

    def test_get_top_gainers(self, agent):
        """상위 상승주 조회 테스트"""
        result = agent.get_top_gainers()
        is_valid, msg = validate_api_response(result)
        assert is_valid, f"상위 상승주 조회 실패: {msg}"


class TestPerformance:
    """성능 테스트"""

    def test_consecutive_api_calls(self, agent, test_stock):
        """연속 API 호출 성능 테스트"""
        call_times = []

        for i in range(3):
            start_time = time.time()
            result = agent.get_stock_price(test_stock)
            elapsed = time.time() - start_time
            call_times.append(elapsed)

            assert result is not None, f"API 호출 {i+1} 실패"

        # 모든 호출이 10초 이내에 완료되어야 함
        for i, elapsed in enumerate(call_times):
            assert elapsed < 10.0, f"API 호출 {i+1}이 너무 오래 걸림: {elapsed:.3f}초"


@pytest.mark.parametrize("stock_code", ["066570", "028260", "051910"])
def test_different_stocks(agent, stock_code):
    """다른 종목들에 대한 테스트"""
    result = agent.get_stock_price(stock_code)
    is_valid, msg = validate_api_response(result)
    assert is_valid, f"종목 {stock_code} 조회 실패: {msg}"


def test_past_date_program_trade(agent, test_stock):
    """과거 날짜 프로그램매매 테스트"""
    past_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    result = agent.get_program_trade_daily_summary(test_stock, past_date)
    is_valid, msg = validate_api_response(result)
    assert is_valid, f"과거 날짜 프로그램매매 조회 실패: {msg}"
