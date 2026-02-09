# Created: 2025-12-12
# Purpose: NXT WebSocket subscription types unit tests
# Test Status: 신규 작성

"""
NXT(대체거래시스템) WebSocket 구독 타입 단위 테스트

테스트 범위:
1. SubscriptionType enum - NXT 타입 정의 검증
2. WSAgent - NXT 구독/해제 메서드 검증
3. RealtimeDataParser - NXT 데이터 파싱 검증
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kis_agent.websocket.ws_agent import (
    RealtimeDataParser,
    SubscriptionType,
    WSAgent,
)


class TestSubscriptionTypeNXT:
    """SubscriptionType enum NXT 타입 테스트"""

    def test_nxt_subscription_types_exist(self):
        """NXT 구독 타입 6개가 정의되어 있는지 확인"""
        nxt_types = [
            SubscriptionType.STOCK_TRADE_NXT,
            SubscriptionType.STOCK_ASK_BID_NXT,
            SubscriptionType.STOCK_EXPECTED_NXT,
            SubscriptionType.PROGRAM_TRADE_NXT,
            SubscriptionType.MARKET_OPERATION_NXT,
            SubscriptionType.MEMBER_TRADE_NXT,
        ]
        assert len(nxt_types) == 6

    def test_nxt_tr_ids_correct(self):
        """NXT TR_ID 값이 올바른지 확인"""
        expected_tr_ids = {
            SubscriptionType.STOCK_TRADE_NXT: "H0NXCNT0",
            SubscriptionType.STOCK_ASK_BID_NXT: "H0NXASP0",
            SubscriptionType.STOCK_EXPECTED_NXT: "H0NXANC0",
            SubscriptionType.PROGRAM_TRADE_NXT: "H0NXPGM0",
            SubscriptionType.MARKET_OPERATION_NXT: "H0NXMKO0",
            SubscriptionType.MEMBER_TRADE_NXT: "H0NXMBC0",
        }
        for sub_type, expected_tr_id in expected_tr_ids.items():
            assert sub_type.value == expected_tr_id, f"{sub_type.name} TR_ID mismatch"

    def test_nxt_types_have_nxt_prefix_in_tr_id(self):
        """NXT 타입의 TR_ID는 H0NX로 시작해야 함"""
        nxt_types = [st for st in SubscriptionType if "NXT" in st.name]
        for st in nxt_types:
            assert st.value.startswith("H0NX"), f"{st.name} should start with H0NX"

    def test_program_trade_krx_tr_id_fixed(self):
        """PROGRAM_TRADE (KRX) TR_ID가 H0STPGM0으로 수정되었는지 확인"""
        # 이전에 잘못된 값 H0GSCNT0이었음
        assert SubscriptionType.PROGRAM_TRADE.value == "H0STPGM0"


class TestWSAgentNXTSubscription:
    """WSAgent NXT 구독 메서드 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient"""
        client = MagicMock()
        client.app_key = "test_app_key"
        client.app_secret = "test_app_secret"
        client.hts_id = "test_hts_id"
        return client

    @pytest.fixture
    def ws_agent(self, mock_client):
        """WSAgent 인스턴스 생성"""
        return WSAgent(approval_key="test_approval_key", client=mock_client)

    def test_subscribe_stock_nxt_adds_trade_only_by_default(self, ws_agent):
        """subscribe_stock_nxt가 기본적으로 체결가만 구독하는지 확인"""
        ws_agent.subscribe_stock_nxt("005930")

        subscriptions = ws_agent.subscriptions
        # 체결가는 기본 포함
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" in subscriptions
        # 호가는 기본 미포함
        assert f"{SubscriptionType.STOCK_ASK_BID_NXT.value}_005930" not in subscriptions

    def test_subscribe_stock_nxt_with_orderbook(self, ws_agent):
        """subscribe_stock_nxt가 with_orderbook=True로 호가도 구독하는지 확인"""
        ws_agent.subscribe_stock_nxt("005930", with_orderbook=True)

        subscriptions = ws_agent.subscriptions
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" in subscriptions
        assert f"{SubscriptionType.STOCK_ASK_BID_NXT.value}_005930" in subscriptions

    def test_subscribe_stock_nxt_with_expected(self, ws_agent):
        """subscribe_stock_nxt가 예상체결도 포함하는지 확인"""
        ws_agent.subscribe_stock_nxt("005930", with_expected=True)

        subscriptions = ws_agent.subscriptions
        assert f"{SubscriptionType.STOCK_EXPECTED_NXT.value}_005930" in subscriptions

    def test_subscribe_stock_nxt_without_expected(self, ws_agent):
        """subscribe_stock_nxt가 예상체결 제외 가능한지 확인"""
        ws_agent.subscribe_stock_nxt("005930", with_expected=False)

        subscriptions = ws_agent.subscriptions
        assert (
            f"{SubscriptionType.STOCK_EXPECTED_NXT.value}_005930" not in subscriptions
        )

    def test_subscribe_stock_nxt_all_options(self, ws_agent):
        """subscribe_stock_nxt가 모든 옵션을 활성화할 수 있는지 확인"""
        ws_agent.subscribe_stock_nxt(
            "005930",
            with_orderbook=True,
            with_expected=True,
            with_program=True,
            with_member=True,
        )

        subscriptions = ws_agent.subscriptions
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" in subscriptions
        assert f"{SubscriptionType.STOCK_ASK_BID_NXT.value}_005930" in subscriptions
        assert f"{SubscriptionType.STOCK_EXPECTED_NXT.value}_005930" in subscriptions
        assert f"{SubscriptionType.PROGRAM_TRADE_NXT.value}_005930" in subscriptions
        assert f"{SubscriptionType.MEMBER_TRADE_NXT.value}_005930" in subscriptions

    def test_subscribe_stocks_nxt_multiple(self, ws_agent):
        """subscribe_stocks_nxt가 복수 종목을 처리하는지 확인"""
        codes = ["005930", "035420", "000660"]
        ws_agent.subscribe_stocks_nxt(codes)

        subscriptions = ws_agent.subscriptions
        for code in codes:
            # 기본은 체결가만
            assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_{code}" in subscriptions

    def test_subscribe_market_operation_nxt(self, ws_agent):
        """subscribe_market_operation_nxt 메서드 테스트"""
        ws_agent.subscribe_market_operation_nxt()

        subscriptions = ws_agent.subscriptions
        # 장운영정보는 종목코드 "NXT" 사용
        assert f"{SubscriptionType.MARKET_OPERATION_NXT.value}_NXT" in subscriptions

    def test_subscribe_program_trading_nxt(self, ws_agent):
        """subscribe_program_trading_nxt 메서드 테스트"""
        ws_agent.subscribe_stock_nxt("005930", with_program=True)

        subscriptions = ws_agent.subscriptions
        assert f"{SubscriptionType.PROGRAM_TRADE_NXT.value}_005930" in subscriptions

    def test_subscribe_member_trading_nxt(self, ws_agent):
        """subscribe_member_trading_nxt 메서드 테스트"""
        ws_agent.subscribe_stock_nxt("005930", with_member=True)

        subscriptions = ws_agent.subscriptions
        assert f"{SubscriptionType.MEMBER_TRADE_NXT.value}_005930" in subscriptions

    def test_unsubscribe_stock_nxt(self, ws_agent):
        """unsubscribe_stock_nxt가 NXT 타입만 해제하는지 확인"""
        # 먼저 KRX와 NXT 모두 구독
        ws_agent.subscribe_stock("005930")
        ws_agent.subscribe_stock_nxt("005930")

        # NXT만 해제
        ws_agent.unsubscribe_stock_nxt("005930")

        subscriptions = ws_agent.subscriptions
        # KRX 체결가는 남아있어야 함
        assert f"{SubscriptionType.STOCK_TRADE.value}_005930" in subscriptions
        # NXT 체결가는 제거되어야 함
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" not in subscriptions

    def test_unsubscribe_stock_includes_nxt_by_default(self, ws_agent):
        """unsubscribe_stock가 기본적으로 NXT도 포함하는지 확인"""
        ws_agent.subscribe_stock("005930")
        ws_agent.subscribe_stock_nxt("005930")

        # include_nxt=True (기본값)
        ws_agent.unsubscribe_stock("005930", include_nxt=True)

        subscriptions = ws_agent.subscriptions
        # 모두 제거되어야 함
        assert f"{SubscriptionType.STOCK_TRADE.value}_005930" not in subscriptions
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" not in subscriptions

    def test_unsubscribe_stock_exclude_nxt(self, ws_agent):
        """unsubscribe_stock에서 NXT 제외 가능한지 확인"""
        ws_agent.subscribe_stock("005930")
        ws_agent.subscribe_stock_nxt("005930")

        # NXT 제외하고 KRX만 해제
        ws_agent.unsubscribe_stock("005930", include_nxt=False)

        subscriptions = ws_agent.subscriptions
        # KRX는 제거
        assert f"{SubscriptionType.STOCK_TRADE.value}_005930" not in subscriptions
        # NXT는 남아있어야 함
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" in subscriptions


class TestRealtimeDataParserNXT:
    """RealtimeDataParser NXT 데이터 파싱 테스트"""

    def test_nxt_field_definitions_exist(self):
        """NXT 전용 필드 정의가 존재하는지 확인"""
        assert hasattr(RealtimeDataParser, "MARKET_OPERATION_NXT_FIELDS")
        assert hasattr(RealtimeDataParser, "PROGRAM_TRADE_NXT_FIELDS")

    def test_market_operation_nxt_fields_count(self):
        """MARKET_OPERATION_NXT_FIELDS 필드 개수 확인"""
        fields = RealtimeDataParser.MARKET_OPERATION_NXT_FIELDS
        assert len(fields) == 11
        assert "mksc_shrn_iscd" in fields
        assert "mkop_cls_code" in fields

    def test_program_trade_nxt_fields_count(self):
        """PROGRAM_TRADE_NXT_FIELDS 필드 개수 확인"""
        fields = RealtimeDataParser.PROGRAM_TRADE_NXT_FIELDS
        assert len(fields) == 11
        assert "mksc_shrn_iscd" in fields
        assert "ntby_cnqn" in fields

    def test_parse_nxt_stock_trade(self):
        """NXT 체결가 데이터 파싱 테스트"""
        # parse 메서드는 List[str]을 받음
        field_count = len(RealtimeDataParser.STOCK_TRADE_FIELDS)
        mock_values = ["test_value"] * field_count
        mock_values[0] = "005930"  # mksc_shrn_iscd
        mock_values[2] = "70000"  # stck_prpr (현재가)

        result = RealtimeDataParser.parse(
            SubscriptionType.STOCK_TRADE_NXT, mock_values  # 리스트로 전달
        )

        assert result is not None
        assert result["mksc_shrn_iscd"] == "005930"
        assert result["stck_prpr"] == 70000  # 숫자로 변환됨

    def test_parse_nxt_stock_ask_bid(self):
        """NXT 호가 데이터 파싱 테스트"""
        field_count = len(RealtimeDataParser.STOCK_ORDERBOOK_FIELDS)
        mock_values = ["0"] * field_count
        mock_values[0] = "005930"  # mksc_shrn_iscd

        result = RealtimeDataParser.parse(
            SubscriptionType.STOCK_ASK_BID_NXT, mock_values  # 리스트로 전달
        )

        assert result is not None
        assert result["mksc_shrn_iscd"] == "005930"

    def test_parse_nxt_market_operation(self):
        """NXT 장운영정보 데이터 파싱 테스트"""
        field_count = len(RealtimeDataParser.MARKET_OPERATION_NXT_FIELDS)
        mock_values = ["0"] * field_count
        mock_values[0] = "0001"  # mksc_shrn_iscd
        mock_values[3] = "20"  # mkop_cls_code (장중)

        result = RealtimeDataParser.parse(
            SubscriptionType.MARKET_OPERATION_NXT, mock_values  # 리스트로 전달
        )

        assert result is not None
        assert result["mksc_shrn_iscd"] == "0001"
        assert result["mkop_cls_code"] == "20"

    def test_parse_nxt_program_trade(self):
        """NXT 프로그램매매 데이터 파싱 테스트"""
        field_count = len(RealtimeDataParser.PROGRAM_TRADE_NXT_FIELDS)
        mock_values = ["0"] * field_count
        mock_values[0] = "005930"  # mksc_shrn_iscd
        mock_values[6] = "1000"  # ntby_cnqn (순매수수량)

        result = RealtimeDataParser.parse(
            SubscriptionType.PROGRAM_TRADE_NXT, mock_values  # 리스트로 전달
        )

        assert result is not None
        assert result["mksc_shrn_iscd"] == "005930"
        assert result["ntby_cnqn"] == 1000  # 숫자로 변환됨

    def test_parse_empty_data_returns_empty(self):
        """빈 리스트는 빈 dict 반환"""
        result = RealtimeDataParser.parse(
            SubscriptionType.STOCK_TRADE_NXT, []  # 빈 리스트
        )
        # 빈 리스트는 빈 dict 반환
        assert result == {}

    def test_all_nxt_types_in_field_map(self):
        """모든 NXT 타입이 field_map에 매핑되어 있는지 확인"""
        nxt_types = [
            SubscriptionType.STOCK_TRADE_NXT,
            SubscriptionType.STOCK_ASK_BID_NXT,
            SubscriptionType.STOCK_EXPECTED_NXT,
            SubscriptionType.PROGRAM_TRADE_NXT,
            SubscriptionType.MARKET_OPERATION_NXT,
            SubscriptionType.MEMBER_TRADE_NXT,
        ]

        # parse 메서드 내부의 field_map 구조를 테스트
        # 각 타입에 대해 파싱이 실패하지 않는지 확인
        for sub_type in nxt_types:
            # 필드 개수에 맞는 더미 데이터 생성 (리스트로 전달)
            mock_values = ["test"] * 50  # 충분한 필드
            try:
                result = RealtimeDataParser.parse(sub_type, mock_values)
                # None이 아니거나 에러 없이 처리되면 OK
                assert result is not None, f"{sub_type.name} parsing failed"
            except KeyError:
                pytest.fail(f"{sub_type.name} not found in field_map")


class TestNXTIntegration:
    """NXT 기능 통합 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient"""
        client = MagicMock()
        client.app_key = "test_app_key"
        client.app_secret = "test_app_secret"
        client.hts_id = "test_hts_id"
        return client

    def test_krx_and_nxt_coexistence(self, mock_client):
        """KRX와 NXT 구독이 동시에 공존할 수 있는지 확인"""
        ws_agent = WSAgent(approval_key="test_approval_key", client=mock_client)

        # KRX 구독 (체결가만 기본)
        ws_agent.subscribe_stock("005930")
        # NXT 구독 (체결가만 기본)
        ws_agent.subscribe_stock_nxt("005930")

        subscriptions = ws_agent.subscriptions

        # KRX 체결가 타입 확인
        assert f"{SubscriptionType.STOCK_TRADE.value}_005930" in subscriptions

        # NXT 체결가 타입 확인
        assert f"{SubscriptionType.STOCK_TRADE_NXT.value}_005930" in subscriptions

    def test_subscription_count_with_nxt(self, mock_client):
        """NXT 포함 시 구독 개수 확인"""
        ws_agent = WSAgent(approval_key="test_approval_key", client=mock_client)

        # KRX만 (체결가만 기본)
        ws_agent.subscribe_stock("005930")
        krx_only_count = len(ws_agent.subscriptions)
        assert krx_only_count == 1  # 체결가만

        # NXT 추가 (체결가만 기본)
        ws_agent.subscribe_stock_nxt("005930")
        with_nxt_count = len(ws_agent.subscriptions)
        assert with_nxt_count == 2  # KRX 체결가 1 + NXT 체결가 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
