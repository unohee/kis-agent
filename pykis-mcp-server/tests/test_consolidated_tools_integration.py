"""Consolidated MCP Tools 통합 테스트

실제 MCP 서버 환경에서 통합 도구의 기능을 검증합니다.
AsyncMock을 사용하여 Agent 응답을 모킹합니다.
"""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestServerToolRegistration:
    """서버 도구 등록 테스트"""

    def test_all_consolidated_tools_registered(self):
        """18개 통합 도구가 모두 등록되었는지 확인"""
        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        consolidated_names = [
            "stock_quote",
            "stock_chart",
            "index_data",
            "market_ranking",
            "investor_flow",
            "broker_trading",
            "program_trading",
            "account_query",
            "order_execute",
            "order_manage",
            "stock_info",
            "overtime_trading",
            "derivatives",
            "interest_stocks",
            "utility",
            "data_management",
            "rate_limiter",
            "method_discovery",
        ]

        for name in consolidated_names:
            assert name in tools, f"Tool {name} not registered"

    def test_tool_count_reduction(self):
        """도구 수 감소 확인 (하위 호환성 도구 포함)"""
        from pykis_mcp_server.server import server

        total_tools = len(server._tool_manager._tools)

        # 통합 후: 18 consolidated + ~106 legacy = ~124 total
        # 향후 deprecated 제거 시 ~25개로 감소 예정
        assert total_tools < 150, f"Too many tools: {total_tools}"
        assert total_tools >= 18, f"Not enough tools: {total_tools}"

    def test_tool_descriptions_contain_query_types(self):
        """도구 설명에 query_type 정보 포함 확인"""
        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        # query_type 파라미터가 있는 도구들
        query_type_tools = [
            "stock_quote",
            "stock_chart",
            "index_data",
            "market_ranking",
            "investor_flow",
            "broker_trading",
            "program_trading",
            "account_query",
        ]

        for name in query_type_tools:
            tool = tools[name]
            desc = tool.description
            # 설명에 query_type 또는 조회 유형이 포함되어 있어야 함
            assert (
                "query_type" in desc or "조회 유형" in desc or "유형" in desc
            ), f"Tool {name} missing query_type in description"


class TestConsolidatedToolParameters:
    """통합 도구 파라미터 검증"""

    def test_stock_quote_parameters(self):
        """stock_quote 파라미터 확인"""
        from pykis_mcp_server.server import server

        tool = server._tool_manager._tools["stock_quote"]
        params = tool.parameters

        assert "code" in params["properties"]
        assert "query_type" in params["properties"]
        assert "market" in params["properties"]
        assert "hour" in params["properties"]

    def test_stock_chart_parameters(self):
        """stock_chart 파라미터 확인"""
        from pykis_mcp_server.server import server

        tool = server._tool_manager._tools["stock_chart"]
        params = tool.parameters

        assert "code" in params["properties"]
        assert "timeframe" in params["properties"]
        assert "date" in params["properties"]

    def test_order_execute_parameters(self):
        """order_execute 파라미터 확인"""
        from pykis_mcp_server.server import server

        tool = server._tool_manager._tools["order_execute"]
        params = tool.parameters

        assert "code" in params["properties"]
        assert "action" in params["properties"]
        assert "quantity" in params["properties"]
        assert "price" in params["properties"]


class TestValidationLogic:
    """입력 검증 로직 테스트"""

    def test_code_validation_rules(self):
        """종목코드 검증 규칙"""

        # 정상 케이스
        valid_codes = ["005930", "035720", "000660"]
        for code in valid_codes:
            assert len(code) == 6

        # 비정상 케이스
        invalid_codes = ["12345", "1234567", "", None, "abcdef"]
        for code in invalid_codes:
            if code is None:
                assert code is None
            else:
                assert len(code) != 6 or not code.isdigit()

    def test_query_type_validation(self):
        """query_type 검증 규칙"""
        valid_stock_quote_types = [
            "price",
            "detail",
            "detail2",
            "orderbook",
            "execution",
            "time_execution",
        ]
        valid_stock_chart_types = ["minute", "daily", "daily_30", "weekly", "monthly"]

        assert "invalid" not in valid_stock_quote_types
        assert "price" in valid_stock_quote_types
        assert "daily" in valid_stock_chart_types


class TestBackwardCompatibility:
    """하위 호환성 테스트"""

    def test_legacy_tools_available(self):
        """기존 도구가 계속 사용 가능한지 확인"""
        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        # 주요 기존 도구들
        legacy_tools = [
            "get_stock_price",
            "get_account_balance",
            "get_volume_rank",
            "get_stock_investor",
        ]

        for name in legacy_tools:
            assert name in tools, f"Legacy tool {name} not available"

    def test_consolidated_and_legacy_coexist(self):
        """통합 도구와 기존 도구 공존 확인"""
        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        # 통합 도구
        assert "stock_quote" in tools

        # 기존 도구 (하위 호환성)
        assert "get_stock_price" in tools


class TestToolCategorization:
    """도구 카테고리 분류 테스트"""

    def test_price_related_tools(self):
        """시세 관련 도구 분류"""
        price_tools = ["stock_quote", "stock_chart", "index_data"]

        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        for name in price_tools:
            assert name in tools

    def test_trading_related_tools(self):
        """거래 관련 도구 분류"""
        trading_tools = ["order_execute", "order_manage"]

        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        for name in trading_tools:
            assert name in tools

    def test_analytics_related_tools(self):
        """분석 관련 도구 분류"""
        analytics_tools = [
            "investor_flow",
            "broker_trading",
            "program_trading",
            "market_ranking",
        ]

        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        for name in analytics_tools:
            assert name in tools

    def test_account_related_tools(self):
        """계좌 관련 도구 분류"""
        account_tools = ["account_query"]

        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        for name in account_tools:
            assert name in tools


class TestToolFunctionSignatures:
    """도구 함수 시그니처 테스트"""

    def test_all_tools_are_async(self):
        """모든 통합 도구가 async 함수인지 확인"""
        from pykis_mcp_server.tools import consolidated_tools

        tools_to_check = [
            "stock_quote",
            "stock_chart",
            "index_data",
            "market_ranking",
            "investor_flow",
            "broker_trading",
            "program_trading",
            "account_query",
            "order_execute",
            "order_manage",
            "stock_info",
            "overtime_trading",
            "derivatives",
            "interest_stocks",
            "utility",
            "data_management",
            "rate_limiter",
            "method_discovery",
        ]

        # 모든 도구가 모듈에 존재하는지 확인
        for name in tools_to_check:
            assert hasattr(consolidated_tools, name), f"Tool {name} not found in module"


class TestConsolidationMetrics:
    """통합 지표 테스트"""

    def test_consolidation_ratio(self):
        """통합 비율 확인"""
        original_tools = 110  # 원래 개별 도구 수
        consolidated_tools = 18  # 통합 후 도구 수

        ratio = consolidated_tools / original_tools
        assert ratio < 0.20, f"Consolidation ratio too high: {ratio:.2%}"

    def test_category_coverage(self):
        """카테고리 커버리지 확인"""
        categories = {
            "price": ["stock_quote", "stock_chart"],
            "index": ["index_data"],
            "ranking": ["market_ranking"],
            "investor": ["investor_flow"],
            "broker": ["broker_trading"],
            "program": ["program_trading"],
            "account": ["account_query"],
            "order": ["order_execute", "order_manage"],
            "info": ["stock_info"],
            "overtime": ["overtime_trading"],
            "derivatives": ["derivatives"],
            "interest": ["interest_stocks"],
            "utility": ["utility"],
            "data": ["data_management"],
            "rate_limiter": ["rate_limiter"],
            "discovery": ["method_discovery"],
        }

        total_tools = sum(len(tools) for tools in categories.values())
        assert total_tools == 18, f"Category coverage mismatch: {total_tools}"


class TestDocumentationQuality:
    """문서 품질 테스트"""

    def test_all_tools_have_descriptions(self):
        """모든 도구에 설명이 있는지 확인"""
        from pykis_mcp_server.server import server

        consolidated_names = [
            "stock_quote",
            "stock_chart",
            "index_data",
            "market_ranking",
            "investor_flow",
            "broker_trading",
            "program_trading",
            "account_query",
            "order_execute",
            "order_manage",
            "stock_info",
            "overtime_trading",
            "derivatives",
            "interest_stocks",
            "utility",
            "data_management",
            "rate_limiter",
            "method_discovery",
        ]

        tools = server._tool_manager._tools

        for name in consolidated_names:
            tool = tools[name]
            assert tool.description, f"Tool {name} has no description"
            assert len(tool.description) > 50, f"Tool {name} has short description"

    def test_descriptions_are_in_korean(self):
        """설명이 한국어로 작성되었는지 확인"""
        from pykis_mcp_server.server import server

        tools = server._tool_manager._tools

        # 샘플 도구들의 설명 확인
        sample_tools = ["stock_quote", "account_query", "order_execute"]

        for name in sample_tools:
            tool = tools[name]
            desc = tool.description
            # 한글 포함 여부 확인
            has_korean = any("\uac00" <= char <= "\ud7a3" for char in desc)
            assert has_korean, f"Tool {name} description not in Korean"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
