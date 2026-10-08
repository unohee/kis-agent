"""
WSAgent 실시간 데이터 기능 테스트

새로 추가된 실시간 데이터 구독 타입, 편의 메서드, 데이터 파싱 및 저장소 테스트
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kis_agent.websocket import (
    RealtimeDataParser,
    RealtimeDataStore,
    Subscription,
    SubscriptionType,
    WSAgent,
    WSAgentWithStore,
)


class TestSubscriptionType:
    """SubscriptionType enum 테스트"""

    def test_stock_subscription_types(self):
        """국내주식 구독 타입 확인"""
        assert SubscriptionType.STOCK_TRADE.value == "H0STCNT0"
        assert SubscriptionType.STOCK_ASK_BID.value == "H0STASP0"
        assert SubscriptionType.STOCK_EXPECTED.value == "H0UNANC0"
        assert SubscriptionType.STOCK_NOTICE.value == "H0STCNI0"
        assert SubscriptionType.STOCK_NOTICE_AH.value == "H0STCNI9"

    def test_index_subscription_types(self):
        """지수 구독 타입 확인"""
        assert (
            SubscriptionType.INDEX.value == "H0UPCNT0"
        )  # 수정: H0IF1000 → H0UPCNT0 (공식 TR_ID)
        assert SubscriptionType.INDEX_EXPECTED.value == "H0UPANC0"

    def test_program_member_subscription_types(self):
        """프로그램매매/회원사 구독 타입 확인"""
        assert SubscriptionType.PROGRAM_TRADE.value == "H0STPGM0"  # KRX
        assert (
            SubscriptionType.MEMBER_TRADE.value == "H0STMBC0"
        )  # 수정: H0MBCNT0 → H0STMBC0 (공식 TR_ID)

    def test_futures_options_subscription_types(self):
        """지수선물/옵션, 상품선물, 주식선물/옵션 구독 타입 확인"""
        # 지수선물/옵션
        assert SubscriptionType.INDEX_FUTURES_TRADE.value == "H0IFCNT0"
        assert SubscriptionType.INDEX_FUTURES_ASK_BID.value == "H0IFASP0"
        assert (
            SubscriptionType.INDEX_OPTION_TRADE.value == "H0IOCNT0"
        )  # 수정: H0OPCNT0 → H0IOCNT0
        assert (
            SubscriptionType.INDEX_OPTION_ASK_BID.value == "H0IOASP0"
        )  # 수정: H0OPASP0 → H0IOASP0
        # 상품선물
        assert SubscriptionType.COMMODITY_FUTURES_TRADE.value == "H0CFCNT0"
        assert SubscriptionType.COMMODITY_FUTURES_ASK_BID.value == "H0CFASP0"
        # 주식선물/옵션
        assert SubscriptionType.STOCK_FUTURES_TRADE.value == "H0ZFCNT0"
        assert SubscriptionType.STOCK_FUTURES_ASK_BID.value == "H0ZFASP0"
        assert SubscriptionType.STOCK_OPTION_TRADE.value == "H0ZOCNT0"
        assert SubscriptionType.STOCK_OPTION_ASK_BID.value == "H0ZOASP0"

    def test_overseas_subscription_types(self):
        """해외 구독 타입 확인"""
        assert SubscriptionType.OVERSEAS_STOCK.value == "HDFSCNT0"
        assert SubscriptionType.OVERSEAS_FUTURES.value == "HDFFF020"


class TestWSAgentConvenienceMethods:
    """WSAgent 편의 메서드 테스트"""

    def test_subscribe_stock_basic(self):
        """기본 종목 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_stock("005930")

        assert len(sub_ids) == 1
        assert "H0STCNT0_005930" in sub_ids

    def test_subscribe_stock_with_orderbook(self):
        """호가 포함 종목 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_stock("005930", with_orderbook=True)

        assert len(sub_ids) == 2
        assert "H0STCNT0_005930" in sub_ids
        assert "H0STASP0_005930" in sub_ids

    def test_subscribe_stock_with_all_options(self):
        """모든 옵션 포함 종목 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_stock(
            "005930",
            with_orderbook=True,
            with_expected=True,
            with_program=True,
            with_member=True,
        )

        assert len(sub_ids) == 5
        assert "H0STCNT0_005930" in sub_ids
        assert "H0STASP0_005930" in sub_ids
        assert "H0UNANC0_005930" in sub_ids
        assert "H0STPGM0_005930" in sub_ids  # PROGRAM_TRADE (KRX)
        assert "H0STMBC0_005930" in sub_ids  # 수정: H0MBCNT0 → H0STMBC0

    def test_subscribe_stocks(self):
        """여러 종목 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_stocks(["005930", "000660", "035420"])

        assert len(sub_ids) == 3
        assert "H0STCNT0_005930" in sub_ids
        assert "H0STCNT0_000660" in sub_ids
        assert "H0STCNT0_035420" in sub_ids

    def test_subscribe_index_default(self):
        """기본 지수 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_index()

        assert len(sub_ids) == 3
        assert "H0UPCNT0_0001" in sub_ids  # KOSPI  (수정: H0IF1000 → H0UPCNT0)
        assert "H0UPCNT0_1001" in sub_ids  # KOSDAQ
        assert "H0UPCNT0_2001" in sub_ids  # KOSPI200

    def test_subscribe_index_with_expected(self):
        """예상체결 포함 지수 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_index(with_expected=True)

        assert len(sub_ids) == 6
        # 지수 (수정: H0IF1000 → H0UPCNT0)
        assert "H0UPCNT0_0001" in sub_ids
        assert "H0UPCNT0_1001" in sub_ids
        assert "H0UPCNT0_2001" in sub_ids
        # 예상체결
        assert "H0UPANC0_0001" in sub_ids
        assert "H0UPANC0_1001" in sub_ids
        assert "H0UPANC0_2001" in sub_ids

    def test_subscribe_program_trading(self):
        """프로그램매매 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_program_trading(["005930", "000660"])

        assert len(sub_ids) == 2
        assert "H0STPGM0_005930" in sub_ids  # PROGRAM_TRADE (KRX)
        assert "H0STPGM0_000660" in sub_ids  # PROGRAM_TRADE (KRX)

    def test_subscribe_member_trading(self):
        """회원사 매매동향 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_member_trading(["005930", "000660"])

        assert len(sub_ids) == 2
        assert "H0STMBC0_005930" in sub_ids  # 수정: H0MBCNT0 → H0STMBC0
        assert "H0STMBC0_000660" in sub_ids

    def test_subscribe_futures(self):
        """선물 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_futures("101S6000", with_orderbook=True)

        assert len(sub_ids) == 2
        assert "H0IFCNT0_101S6000" in sub_ids  # subscribe_futures → 지수선물 (수정)
        assert "H0IFASP0_101S6000" in sub_ids

    def test_subscribe_options(self):
        """옵션 구독"""
        agent = WSAgent(approval_key="test_key")
        sub_ids = agent.subscribe_options("201S6C300", with_orderbook=True)

        assert len(sub_ids) == 2
        assert (
            "H0IOCNT0_201S6C300" in sub_ids
        )  # subscribe_options → 지수옵션 (수정: H0OPCNT0 → H0IOCNT0)
        assert "H0IOASP0_201S6C300" in sub_ids

    def test_unsubscribe_stock(self):
        """종목 관련 모든 구독 해제"""
        agent = WSAgent(approval_key="test_key")
        agent.subscribe_stock("005930", with_orderbook=True, with_expected=True)

        assert len(agent.subscriptions) == 3

        agent.unsubscribe_stock("005930")

        assert len(agent.subscriptions) == 0

    def test_unsubscribe_all(self):
        """모든 구독 해제"""
        agent = WSAgent(approval_key="test_key")
        agent.subscribe_stock("005930")
        agent.subscribe_stock("000660")
        agent.subscribe_index()

        assert len(agent.subscriptions) == 5

        agent.unsubscribe_all()

        assert len(agent.subscriptions) == 0


class TestRealtimeDataParser:
    """RealtimeDataParser 테스트"""

    def test_parse_stock_trade(self):
        """종목 체결 데이터 파싱"""
        # 샘플 체결 데이터 (일부 필드만)
        values = [
            "005930",  # mksc_shrn_iscd
            "093000",  # stck_cntg_hour
            "70000",  # stck_prpr
            "2",  # prdy_vrss_sign
            "500",  # prdy_vrss
            "0.72",  # prdy_ctrt
        ]

        result = RealtimeDataParser.parse_stock_trade(values)

        assert result["mksc_shrn_iscd"] == "005930"
        assert result["stck_cntg_hour"] == "093000"
        assert result["stck_prpr"] == 70000
        assert result["prdy_vrss_sign"] == 2  # 숫자로 변환됨
        assert result["prdy_vrss"] == 500
        assert result["prdy_ctrt"] == 0.72

    @staticmethod
    def _frame(tr_id, **values):
        """Build a value list in the official column order of ``tr_id``."""
        from kis_agent.websocket.ws_fields import FIELDS

        return [str(values.get(name, "")) for name in FIELDS[tr_id]]

    def test_parse_index(self):
        """국내지수 실시간체결 (H0UPCNT0): 첫 컬럼은 업종코드"""
        values = self._frame(
            "H0UPCNT0",
            bstp_cls_code="0001",
            bsop_hour="093000",
            prpr_nmix="2650.50",
            prdy_vrss_sign="2",
            bstp_nmix_prdy_vrss="15.30",
            prdy_ctrt="0.58",
        )
        result = RealtimeDataParser.parse_index(values)

        assert result["bstp_cls_code"] == "0001"
        assert result["bsop_hour"] == "093000"
        assert result["prpr_nmix"] == 2650.50
        assert result["bstp_nmix_prdy_vrss"] == 15.30
        assert result["prdy_vrss_sign"] == 2
        assert result["prdy_ctrt"] == 0.58
        assert len(result) == 30

    def test_parse_program_trade(self):
        """프로그램매매 (H0STPGM0)"""
        values = self._frame(
            "H0STPGM0",
            mksc_shrn_iscd="005930",
            stck_cntg_hour="093000",
            seln_cnqn="10000",
            shnu_cnqn="15000",
            ntby_cnqn="5000",
        )
        result = RealtimeDataParser.parse_program_trade(values)

        assert result["mksc_shrn_iscd"] == "005930"
        assert result["stck_cntg_hour"] == "093000"
        assert result["seln_cnqn"] == 10000
        assert result["shnu_cnqn"] == 15000
        assert result["ntby_cnqn"] == 5000

    def test_parse_member_trade(self):
        """회원사 (H0STMBC0): 78 컬럼, 매도 회원사명부터 시작"""
        values = self._frame(
            "H0STMBC0",
            mksc_shrn_iscd="005930",
            seln2_mbcr_name1="모건스탠리",
            glob_ntby_qty="5000",
        )
        result = RealtimeDataParser.parse_member_trade(values)

        assert len(values) == 78
        assert result["mksc_shrn_iscd"] == "005930"
        assert result["seln2_mbcr_name1"] == "모건스탠리"
        assert result["glob_ntby_qty"] == 5000

    def test_parse_stock_expected(self):
        """예상체결 (H0UNANC0, 통합)"""
        values = self._frame(
            "H0UNANC0",
            mksc_shrn_iscd="005930",
            stck_cntg_hour="085959",
            stck_prpr="70500",
            prdy_vrss="500",
        )
        result = RealtimeDataParser.parse_stock_expected(values)

        assert result["mksc_shrn_iscd"] == "005930"
        assert result["stck_cntg_hour"] == "085959"
        assert result["stck_prpr"] == 70500
        assert result["prdy_vrss"] == 500

    def test_parse_index_expected(self):
        """지수 예상체결 (H0UPANC0)"""
        values = self._frame(
            "H0UPANC0",
            bstp_cls_code="0001",
            bsop_hour="085900",
            prpr_nmix="2645.50",
            bstp_nmix_prdy_vrss="15.50",
        )
        result = RealtimeDataParser.parse_index_expected(values)

        assert result["bstp_cls_code"] == "0001"
        assert result["bsop_hour"] == "085900"
        assert result["prpr_nmix"] == 2645.50
        assert result["bstp_nmix_prdy_vrss"] == 15.50

    def test_parse_unknown_type(self):
        """레이아웃이 없는 타입은 field_N 키로 반환 (해외선물은 범위 밖)"""
        values = ["value1", "value2", "value3"]

        result = RealtimeDataParser.parse(SubscriptionType.OVERSEAS_FUTURES, values)

        assert result["field_0"] == "value1"
        assert result["field_1"] == "value2"
        assert result["field_2"] == "value3"

    def test_parse_overseas_trade_starts_with_rsym(self):
        """해외주식 체결 (HDFSCNT0): 첫 컬럼은 실시간종목코드 RSYM (공식 문서)"""
        values = self._frame("HDFSCNT0", rsym="DNASAAPL", symb="AAPL", last="190.25")
        result = RealtimeDataParser.parse(SubscriptionType.OVERSEAS_STOCK, values)

        assert result["rsym"] == "DNASAAPL"
        assert result["symb"] == "AAPL"
        assert result["last"] == 190.25


class TestRealtimeDataStore:
    """RealtimeDataStore 테스트"""

    def test_update_and_get(self):
        """데이터 업데이트 및 조회"""
        store = RealtimeDataStore()

        store.update(
            SubscriptionType.STOCK_TRADE,
            "005930",
            {"stck_prpr": 70000, "acml_vol": 1000000},
        )

        result = store.get("005930", SubscriptionType.STOCK_TRADE)

        assert result is not None
        assert result["stck_prpr"] == 70000
        assert result["acml_vol"] == 1000000
        assert "_updated_at" in result

    def test_get_convenience_methods(self):
        """편의 조회 메서드"""
        store = RealtimeDataStore()

        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70000})
        store.update(SubscriptionType.STOCK_ASK_BID, "005930", {"askp1": 70100})
        store.update(SubscriptionType.STOCK_EXPECTED, "005930", {"antc_cnpr": 70050})
        store.update(SubscriptionType.INDEX, "0001", {"bstp_nmix_prpr": 2650.50})
        store.update(SubscriptionType.PROGRAM_TRADE, "005930", {"ntby_cntg_qty": 5000})
        store.update(SubscriptionType.MEMBER_TRADE, "005930", {"frgn_ntby_qty": 3000})

        assert store.get_trade("005930")["stck_prpr"] == 70000
        assert store.get_orderbook("005930")["askp1"] == 70100
        assert store.get_expected("005930")["antc_cnpr"] == 70050
        assert store.get_index("0001")["bstp_nmix_prpr"] == 2650.50
        assert store.get_program_trade("005930")["ntby_cntg_qty"] == 5000
        assert store.get_member_trade("005930")["frgn_ntby_qty"] == 3000

    def test_get_all_types_for_code(self):
        """특정 종목의 모든 타입 조회"""
        store = RealtimeDataStore()

        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70000})
        store.update(SubscriptionType.STOCK_ASK_BID, "005930", {"askp1": 70100})

        result = store.get("005930")

        assert SubscriptionType.STOCK_TRADE in result
        assert SubscriptionType.STOCK_ASK_BID in result

    def test_get_nonexistent(self):
        """존재하지 않는 데이터 조회"""
        store = RealtimeDataStore()

        assert store.get("005930") is None
        assert store.get_trade("005930") is None

    def test_history(self):
        """히스토리 저장 및 조회"""
        store = RealtimeDataStore(max_history=5)

        # 히스토리 활성화하여 업데이트
        for i in range(7):
            store.update(
                SubscriptionType.STOCK_TRADE,
                "005930",
                {"stck_prpr": 70000 + i * 100},
                keep_history=True,
            )

        # 최대 5개까지만 저장
        history = store.get_history("005930", SubscriptionType.STOCK_TRADE)
        assert len(history) == 5

        # 최신순 정렬
        assert history[0]["stck_prpr"] == 70600
        assert history[-1]["stck_prpr"] == 70200

    def test_history_with_limit(self):
        """히스토리 제한 조회"""
        store = RealtimeDataStore(max_history=10)

        for i in range(5):
            store.update(
                SubscriptionType.STOCK_TRADE,
                "005930",
                {"stck_prpr": 70000 + i * 100},
                keep_history=True,
            )

        history = store.get_history("005930", SubscriptionType.STOCK_TRADE, limit=3)
        assert len(history) == 3

    def test_get_all_codes(self):
        """추적 중인 모든 종목코드 조회"""
        store = RealtimeDataStore()

        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70000})
        store.update(SubscriptionType.STOCK_TRADE, "000660", {"stck_prpr": 150000})
        store.update(SubscriptionType.INDEX, "0001", {"bstp_nmix_prpr": 2650.50})

        codes = store.get_all_codes()

        assert "005930" in codes
        assert "000660" in codes
        assert "0001" in codes

    def test_stats(self):
        """저장소 통계"""
        store = RealtimeDataStore()

        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70000})
        store.update(SubscriptionType.STOCK_TRADE, "000660", {"stck_prpr": 150000})
        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70100})

        stats = store.get_stats()

        assert stats["total_updates"] == 3
        assert stats["codes_tracked"] == 2
        assert stats["last_update_time"] is not None

    def test_clear_specific_code(self):
        """특정 종목 데이터 삭제"""
        store = RealtimeDataStore()

        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70000})
        store.update(SubscriptionType.STOCK_TRADE, "000660", {"stck_prpr": 150000})

        store.clear("005930")

        assert store.get("005930") is None
        assert store.get("000660") is not None

    def test_clear_all(self):
        """모든 데이터 삭제"""
        store = RealtimeDataStore()

        store.update(SubscriptionType.STOCK_TRADE, "005930", {"stck_prpr": 70000})
        store.update(SubscriptionType.STOCK_TRADE, "000660", {"stck_prpr": 150000})

        store.clear()

        assert store.get("005930") is None
        assert store.get("000660") is None
        assert len(store.get_all_codes()) == 0


class TestWSAgentWithStore:
    """WSAgentWithStore 테스트"""

    def test_initialization(self):
        """초기화"""
        agent = WSAgentWithStore(approval_key="test_key")

        assert agent.store is not None
        assert isinstance(agent.store, RealtimeDataStore)

    def test_store_handlers_registered(self):
        """자동 저장 핸들러 등록 확인"""
        agent = WSAgentWithStore(approval_key="test_key")

        # 모든 구독 타입에 대해 핸들러가 등록되어야 함
        for sub_type in SubscriptionType:
            assert sub_type in agent.type_handlers
            assert len(agent.type_handlers[sub_type]) > 0

    def test_inheritance(self):
        """WSAgent 상속 확인"""
        agent = WSAgentWithStore(approval_key="test_key")

        # WSAgent의 모든 편의 메서드 사용 가능
        sub_ids = agent.subscribe_stock("005930", with_orderbook=True)
        assert len(sub_ids) == 2

    def test_keep_history_option(self):
        """히스토리 보관 옵션"""
        agent = WSAgentWithStore(
            approval_key="test_key",
            keep_history=True,
            max_history=50,
        )

        assert agent.keep_history is True
        assert agent.store.max_history == 50


class TestWSAgentReconnectConfig:
    """재연결 설정 테스트"""

    def test_default_max_reconnect_attempts(self):
        """기본 max_reconnect_attempts 값 확인"""
        agent = WSAgent(approval_key="test_key")
        assert agent.max_reconnect_attempts == 10

    def test_custom_max_reconnect_attempts(self):
        """커스텀 max_reconnect_attempts 설정"""
        agent = WSAgent(approval_key="test_key", max_reconnect_attempts=5)
        assert agent.max_reconnect_attempts == 5

    def test_unlimited_reconnect(self):
        """무제한 재연결 (0)"""
        agent = WSAgent(approval_key="test_key", max_reconnect_attempts=0)
        assert agent.max_reconnect_attempts == 0

    def test_fatal_error_patterns_exist(self):
        """복구 불가능한 에러 패턴 존재 확인"""
        # _FATAL_ERROR_PATTERNS는 compiled re.Pattern 목록
        patterns_str = [p.pattern for p in WSAgent._FATAL_ERROR_PATTERNS]
        assert any("401" in p for p in patterns_str)
        assert any("403" in p for p in patterns_str)
        assert any("인증" in p for p in patterns_str)

    @pytest.mark.asyncio
    async def test_connect_blocked_after_market_close(self):
        """장 마감 후 연결 차단 확인"""
        agent = WSAgent(approval_key="test_key")

        with patch(
            "kis_agent.websocket.ws_agent._is_after_market_close", return_value=True
        ):
            await agent.connect()
            assert agent.auto_reconnect is False

    def test_ping_check_interval_matches_ping_interval(self):
        """ping_check_interval이 ping_interval과 동일한지 확인"""
        agent = WSAgent(approval_key="test_key", ping_interval=45)
        assert agent.ping_interval == 45
