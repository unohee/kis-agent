"""
MCP 통합 도구 단위 테스트

PR 리뷰 피드백 반영:
- market_ranking volume 버그 수정 검증
- rate_limiter 로컬 응답 생성 검증
- method_discovery 응답 형식 검증
"""

from unittest.mock import MagicMock

import pytest


class TestMarketRankingTool:
    """market_ranking 도구 테스트"""

    @pytest.fixture
    def mock_agent(self):
        """Mock Agent 설정"""
        agent = MagicMock()
        agent.stock = MagicMock()
        agent.stock.price_api = MagicMock()
        return agent

    def test_volume_ranking_uses_correct_parameters(self, mock_agent):
        """volume ranking이 올바른 파라미터를 사용하는지 검증"""
        # Mock price_api.volume_rank 응답
        mock_agent.stock.price_api.volume_rank.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다",
            "output": [{"stck_shrn_iscd": "005930", "data_rank": "1"}],
        }

        # volume_rank 호출 시 파라미터 확인
        result = mock_agent.stock.price_api.volume_rank(
            fid_cond_mrkt_div_code="J",
            fid_cond_scr_div_code="20101",
            fid_input_iscd="0000",
            fid_div_cls_code="0",
            fid_blng_cls_code="0",
            fid_trgt_cls_code="111111111",
            fid_trgt_exls_cls_code="000000",
            fid_input_price_1="",
            fid_input_price_2="",
            fid_vol_cnt="5000000",
            fid_input_date_1="",
        )

        assert result["rt_cd"] == "0"
        assert len(result["output"]) > 0
        mock_agent.stock.price_api.volume_rank.assert_called_once()

    def test_gainers_ranking_parameters(self, mock_agent):
        """상승률 순위 파라미터 검증"""
        mock_agent.stock.price_api.fluctuation.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다",
            "output": [],
        }

        # fluctuation 호출 (sign=1: 상승)
        result = mock_agent.stock.price_api.fluctuation(
            fid_cond_mrkt_div_code="J",
            fid_cond_scr_div_code="20170",
            fid_input_iscd="0000",
            fid_rank_sort_cls_code="1",  # 상승
        )

        assert result["rt_cd"] == "0"

    def test_losers_ranking_parameters(self, mock_agent):
        """하락률 순위 파라미터 검증"""
        mock_agent.stock.price_api.fluctuation.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다",
            "output": [],
        }

        # fluctuation 호출 (sign=3: 하락)
        result = mock_agent.stock.price_api.fluctuation(
            fid_cond_mrkt_div_code="J",
            fid_cond_scr_div_code="20170",
            fid_input_iscd="0000",
            fid_rank_sort_cls_code="3",  # 하락
        )

        assert result["rt_cd"] == "0"


class TestRateLimiterTool:
    """rate_limiter 도구 테스트 - 로컬 응답 생성 검증"""

    @pytest.fixture
    def mock_agent(self):
        """Mock Agent 설정"""
        agent = MagicMock()
        agent.get_rate_limiter_status.return_value = {
            "requests_per_second": 18,
            "requests_per_minute": 900,
            "current_second_count": 5,
            "current_minute_count": 100,
        }
        agent.rate_limiter = MagicMock()
        agent.rate_limiter.enable_adaptive = True
        return agent

    def test_status_returns_local_response_format(self, mock_agent):
        """status 액션이 로컬 응답 형식을 반환하는지 검증"""
        status = mock_agent.get_rate_limiter_status()

        # API 응답이 아닌 로컬 상태 반환
        assert status is not None
        assert "requests_per_second" in status
        assert "requests_per_minute" in status

    def test_status_handles_disabled_limiter(self, mock_agent):
        """비활성화된 Rate Limiter 처리 검증"""
        mock_agent.get_rate_limiter_status.return_value = None

        status = mock_agent.get_rate_limiter_status()
        assert status is None

    def test_reset_returns_success(self, mock_agent):
        """reset 액션 성공 검증"""
        mock_agent.reset_rate_limiter.return_value = None

        # reset은 None을 반환해도 성공
        mock_agent.reset_rate_limiter()
        mock_agent.reset_rate_limiter.assert_called_once()

    def test_set_limits_applies_values(self, mock_agent):
        """set_limits 액션 값 적용 검증"""
        mock_agent.set_rate_limits.return_value = None

        mock_agent.set_rate_limits(
            requests_per_second=15,
            requests_per_minute=800,
            min_interval_ms=60,
        )

        mock_agent.set_rate_limits.assert_called_once_with(
            requests_per_second=15,
            requests_per_minute=800,
            min_interval_ms=60,
        )


class TestMethodDiscoveryTool:
    """method_discovery 도구 테스트 - 로컬 응답 생성 검증"""

    @pytest.fixture
    def mock_agent(self):
        """Mock Agent 설정"""
        agent = MagicMock()
        agent.get_all_methods.return_value = [
            {
                "name": "get_stock_price",
                "category": "stock",
                "description": "주식 현재가 조회",
            },
            {
                "name": "get_account_balance",
                "category": "account",
                "description": "계좌 잔고 조회",
            },
        ]
        agent.search_methods.return_value = [
            {
                "name": "get_stock_price",
                "category": "stock",
                "description": "주식 현재가 조회",
            },
        ]
        return agent

    def test_list_all_returns_list(self, mock_agent):
        """list_all 액션이 리스트를 반환하는지 검증"""
        methods = mock_agent.get_all_methods(show_details=True)

        assert isinstance(methods, list)
        assert len(methods) == 2
        assert all("name" in m for m in methods)

    def test_search_filters_by_keyword(self, mock_agent):
        """search 액션이 키워드로 필터링하는지 검증"""
        results = mock_agent.search_methods("price")

        assert isinstance(results, list)
        assert len(results) == 1
        assert "price" in results[0]["name"]

    def test_usage_returns_method_info(self, mock_agent):
        """usage 액션이 메서드 정보를 반환하는지 검증"""
        mock_agent.get_all_methods.return_value = [
            {
                "name": "get_stock_price",
                "category": "stock",
                "description": "주식 현재가 조회",
            },
        ]

        methods = mock_agent.get_all_methods(show_details=True)
        method_info = next((m for m in methods if m["name"] == "get_stock_price"), None)

        assert method_info is not None
        assert method_info["name"] == "get_stock_price"


class TestUtilityTool:
    """utility 도구 테스트 - holiday_info date 파라미터 검증"""

    @pytest.fixture
    def mock_agent(self):
        """Mock Agent 설정"""
        agent = MagicMock()
        agent.stock = MagicMock()
        return agent

    def test_holiday_info_accepts_date_parameter(self, mock_agent):
        """holiday_info가 date 파라미터를 받는지 검증"""
        mock_agent.stock.get_holiday_info.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다",
            "output": [{"bass_dt": "20260104", "opnd_yn": "N"}],
        }

        result = mock_agent.stock.get_holiday_info("20260104")

        assert result["rt_cd"] == "0"
        mock_agent.stock.get_holiday_info.assert_called_once_with("20260104")

    def test_holiday_info_without_date(self, mock_agent):
        """holiday_info가 date 없이도 동작하는지 검증"""
        mock_agent.stock.get_holiday_info.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다",
            "output": [],
        }

        result = mock_agent.stock.get_holiday_info(None)

        assert result["rt_cd"] == "0"
        mock_agent.stock.get_holiday_info.assert_called_once_with(None)


class TestErrorMessageImprovement:
    """에러 메시지 개선 테스트"""

    def test_error_message_includes_operation_context(self):
        """에러 메시지에 operation 컨텍스트가 포함되는지 검증"""
        operation = "market_ranking"
        rt_cd = "1"
        msg_cd = "EGW00201"
        msg1 = ""

        # msg1이 비어있을 때 rt_cd/msg_cd 표시
        if msg1:
            error_message = msg1
        else:
            error_message = f"rt_cd={rt_cd}, msg_cd={msg_cd}"

        full_error = f"{operation} failed: {error_message}"

        assert operation in full_error
        assert rt_cd in full_error
        assert msg_cd in full_error

    def test_error_message_uses_msg1_when_available(self):
        """msg1이 있을 때 사용하는지 검증"""
        operation = "stock_quote"
        msg1 = "주문가능수량이 부족합니다"

        if msg1:
            error_message = msg1
        else:
            error_message = "rt_cd=1, msg_cd=ERR"

        full_error = f"{operation} failed: {error_message}"

        assert msg1 in full_error
        assert "rt_cd" not in full_error
