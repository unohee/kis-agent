"""
KRX 야간선물/옵션 웹소켓 실시간 데이터 테스트

SubscriptionType enum, 필드 파싱, 데이터 저장소 테스트
"""

import pytest

from kis_agent.websocket import (
    RealtimeDataParser,
    RealtimeDataStore,
    SubscriptionType,
    WSAgent,
)


class TestNightSubscriptionType:
    """야간선물/옵션 SubscriptionType enum 테스트"""

    def test_night_futures_trade(self):
        assert SubscriptionType.NIGHT_FUTURES_TRADE.value == "H0MFCNT0"

    def test_night_futures_ask_bid(self):
        assert SubscriptionType.NIGHT_FUTURES_ASK_BID.value == "H0MFASP0"

    def test_night_option_trade(self):
        assert SubscriptionType.NIGHT_OPTION_TRADE.value == "H0EUCNT0"

    def test_night_option_ask_bid(self):
        assert SubscriptionType.NIGHT_OPTION_ASK_BID.value == "H0EUASP0"


class TestNightFuturesTradeParser:
    """야간선물 체결 파서 테스트 [실시간-064]"""

    def _make_values(self):
        """48개 필드 샘플 데이터"""
        return [
            "101V06",       # futs_shrn_iscd
            "190215",       # bsop_hour
            "1.50",         # futs_prdy_vrss
            "2",            # prdy_vrss_sign
            "0.41",         # futs_prdy_ctrt
            "367.35",       # futs_prpr
            "366.00",       # futs_oprc
            "368.00",       # futs_hgpr
            "365.50",       # futs_lwpr
            "3",            # last_cnqn
            "12345",        # acml_vol
            "4530000000",   # acml_tr_pbmn
            "367.50",       # hts_thpr
            "0.15",         # mrkt_basis
            "0.04",         # dprt
            "367.00",       # nmsc_fctn_stpl_prc
            "368.00",       # fmsc_fctn_stpl_prc
            "1.00",         # spead_prc
            "50000",        # hts_otst_stpl_qty
            "100",          # otst_stpl_qty_icdc
            "180000",       # oprc_hour
            "2",            # oprc_vrss_prpr_sign
            "1.35",         # oprc_vrss_nmix_prpr
            "183000",       # hgpr_hour
            "2",            # hgpr_vrss_prpr_sign
            "0.65",         # hgpr_vrss_nmix_prpr
            "181500",       # lwpr_hour
            "5",            # lwpr_vrss_prpr_sign
            "1.85",         # lwpr_vrss_nmix_prpr
            "52.30",        # shnu_rate
            "105.20",       # cttr
            "0.02",         # esdg
            "50",           # otst_stpl_rgbf_qty_icdc
            "0.10",         # thpr_basis
            "367.40",       # futs_askp1
            "367.30",       # futs_bidp1
            "24",           # askp_rsqn1
            "21",           # bidp_rsqn1
            "5000",         # seln_cntg_csnu
            "5100",         # shnu_cntg_csnu
            "100",          # ntby_cntg_csnu
            "6000",         # seln_cntg_smtn
            "6100",         # shnu_cntg_smtn
            "120",          # total_askp_rsqn
            "115",          # total_bidp_rsqn
            "85.30",        # prdy_vol_vrss_acml_vol_rate
            "380.00",       # dynm_mxpr
            "355.00",       # dynm_llam
            "N",            # dynm_prc_limt_yn
        ]

    def test_parse_night_futures_trade(self):
        values = self._make_values()
        result = RealtimeDataParser.parse_night_futures_trade(values)

        assert result["futs_shrn_iscd"] == "101V06"
        assert result["futs_prpr"] == 367.35
        assert result["acml_vol"] == 12345
        assert result["futs_askp1"] == 367.40
        assert result["futs_bidp1"] == 367.30
        assert result["dynm_prc_limt_yn"] == "N"

    def test_parse_via_generic(self):
        values = self._make_values()
        result = RealtimeDataParser.parse(
            SubscriptionType.NIGHT_FUTURES_TRADE, values
        )
        assert result["futs_prpr"] == 367.35

    def test_field_count(self):
        assert len(RealtimeDataParser.NIGHT_FUTURES_TRADE_FIELDS) == 49


class TestNightFuturesOrderbookParser:
    """야간선물 호가 파서 테스트 [실시간-065]"""

    def _make_values(self):
        """36개 필드 샘플 데이터"""
        return [
            "101V06",   # futs_shrn_iscd
            "190215",   # bsop_hour
            "367.35",   # futs_askp1
            "367.40",   # futs_askp2
            "367.45",   # futs_askp3
            "0.00",     # futs_askp4
            "0.00",     # futs_askp5
            "367.30",   # futs_bidp1
            "367.25",   # futs_bidp2
            "367.20",   # futs_bidp3
            "0.00",     # futs_bidp4
            "0.00",     # futs_bidp5
            "10",       # askp_csnu1
            "8",        # askp_csnu2
            "5",        # askp_csnu3
            "0",        # askp_csnu4
            "0",        # askp_csnu5
            "12",       # bidp_csnu1
            "9",        # bidp_csnu2
            "6",        # bidp_csnu3
            "0",        # bidp_csnu4
            "0",        # bidp_csnu5
            "24",       # askp_rsqn1
            "21",       # askp_rsqn2
            "15",       # askp_rsqn3
            "0",        # askp_rsqn4
            "0",        # askp_rsqn5
            "28",       # bidp_rsqn1
            "20",       # bidp_rsqn2
            "10",       # bidp_rsqn3
            "0",        # bidp_rsqn4
            "0",        # bidp_rsqn5
            "23",       # total_askp_csnu
            "27",       # total_bidp_csnu
            "60",       # total_askp_rsqn
            "58",       # total_bidp_rsqn
            "5",        # total_askp_rsqn_icdc
            "-3",       # total_bidp_rsqn_icdc
        ]

    def test_parse_night_futures_orderbook(self):
        values = self._make_values()
        result = RealtimeDataParser.parse_night_futures_orderbook(values)

        assert result["futs_shrn_iscd"] == "101V06"
        assert result["futs_askp1"] == 367.35
        assert result["futs_bidp1"] == 367.30
        assert result["total_askp_rsqn"] == 60
        assert result["total_bidp_rsqn"] == 58

    def test_field_count(self):
        assert len(RealtimeDataParser.NIGHT_FUTURES_ORDERBOOK_FIELDS) == 38


class TestNightOptionTradeParser:
    """야간옵션 체결 파서 테스트 [실시간-032]"""

    def _make_values(self):
        """53개 필드 샘플 데이터"""
        return [
            "101W9000",     # optn_shrn_iscd
            "190215",       # bsop_hour
            "3.50",         # optn_prpr
            "2",            # prdy_vrss_sign
            "0.20",         # optn_prdy_vrss
            "6.06",         # prdy_ctrt
            "3.40",         # optn_oprc
            "3.65",         # optn_hgpr
            "3.30",         # optn_lwpr
            "5",            # last_cnqn
            "2500",         # acml_vol
            "87500000",     # acml_tr_pbmn
            "3.48",         # hts_thpr
            "8000",         # hts_otst_stpl_qty
            "50",           # otst_stpl_qty_icdc
            "180000",       # oprc_hour
            "2",            # oprc_vrss_prpr_sign
            "0.10",         # oprc_vrss_nmix_prpr
            "183000",       # hgpr_hour
            "2",            # hgpr_vrss_prpr_sign
            "0.15",         # hgpr_vrss_nmix_prpr
            "181500",       # lwpr_hour
            "5",            # lwpr_vrss_prpr_sign
            "0.20",         # lwpr_vrss_nmix_prpr
            "55.00",        # shnu_rate
            "2.80",         # prmm_val
            "0.70",         # invl_val
            "2.10",         # tmvl_val
            "0.45",         # delta
            "0.08",         # gama
            "0.12",         # vega
            "-0.05",        # theta
            "0.01",         # rho
            "18.50",        # hts_ints_vltl
            "0.02",         # esdg
            "30",           # otst_stpl_rgbf_qty_icdc
            "0.02",         # thpr_basis
            "15.20",        # unas_hist_vltl
            "110.50",       # cttr
            "0.57",         # dprt
            "0.05",         # mrkt_basis
            "3.55",         # optn_askp1
            "3.45",         # optn_bidp1
            "15",           # askp_rsqn1
            "18",           # bidp_rsqn1
            "1200",         # seln_cntg_csnu
            "1300",         # shnu_cntg_csnu
            "100",          # ntby_cntg_csnu
            "1500",         # seln_cntg_smtn
            "1600",         # shnu_cntg_smtn
            "80",           # total_askp_rsqn
            "85",           # total_bidp_rsqn
            "75.50",        # prdy_vol_vrss_acml_vol_rate
            "5.00",         # dynm_mxpr
            "N",            # dynm_prc_limt_yn
            "1.50",         # dynm_llam
        ]

    def test_parse_night_option_trade(self):
        values = self._make_values()
        result = RealtimeDataParser.parse_night_option_trade(values)

        assert result["optn_shrn_iscd"] == "101W9000"
        assert result["optn_prpr"] == 3.50
        assert result["delta"] == 0.45
        assert result["theta"] == -0.05
        assert result["hts_ints_vltl"] == 18.50
        assert result["optn_askp1"] == 3.55

    def test_field_count(self):
        assert len(RealtimeDataParser.NIGHT_OPTION_TRADE_FIELDS) == 56


class TestNightOptionOrderbookParser:
    """야간옵션 호가 파서 테스트 [실시간-033]"""

    def _make_values(self):
        """36개 필드 샘플 데이터"""
        return [
            "101W9000",     # optn_shrn_iscd
            "190215",       # bsop_hour
            "3.55",         # optn_askp1
            "3.60",         # optn_askp2
            "3.65",         # optn_askp3
            "3.70",         # optn_askp4
            "3.75",         # optn_askp5
            "3.45",         # optn_bidp1
            "3.40",         # optn_bidp2
            "3.35",         # optn_bidp3
            "3.30",         # optn_bidp4
            "3.25",         # optn_bidp5
            "5",            # askp_csnu1
            "4",            # askp_csnu2
            "3",            # askp_csnu3
            "2",            # askp_csnu4
            "1",            # askp_csnu5
            "6",            # bidp_csnu1
            "5",            # bidp_csnu2
            "4",            # bidp_csnu3
            "3",            # bidp_csnu4
            "2",            # bidp_csnu5
            "15",           # askp_rsqn1
            "12",           # askp_rsqn2
            "10",           # askp_rsqn3
            "8",            # askp_rsqn4
            "5",            # askp_rsqn5
            "18",           # bidp_rsqn1
            "14",           # bidp_rsqn2
            "11",           # bidp_rsqn3
            "9",            # bidp_rsqn4
            "6",            # bidp_rsqn5
            "15",           # total_askp_csnu
            "20",           # total_bidp_csnu
            "50",           # total_askp_rsqn
            "58",           # total_bidp_rsqn
            "3",            # total_askp_rsqn_icdc
            "-2",           # total_bidp_rsqn_icdc
        ]

    def test_parse_night_option_orderbook(self):
        values = self._make_values()
        result = RealtimeDataParser.parse_night_option_orderbook(values)

        assert result["optn_shrn_iscd"] == "101W9000"
        assert result["optn_askp1"] == 3.55
        assert result["optn_bidp1"] == 3.45
        assert result["total_askp_rsqn"] == 50
        assert result["total_bidp_rsqn"] == 58

    def test_field_count(self):
        assert len(RealtimeDataParser.NIGHT_OPTION_ORDERBOOK_FIELDS) == 38


class TestNightDataStore:
    """야간선물/옵션 데이터 저장소 테스트"""

    def test_night_futures_trade_store(self):
        store = RealtimeDataStore()
        data = {"futs_prpr": 367.35, "acml_vol": 12345}
        store.update(SubscriptionType.NIGHT_FUTURES_TRADE, "101V06", data)

        result = store.get_night_futures_trade("101V06")
        assert result["futs_prpr"] == 367.35

    def test_night_futures_orderbook_store(self):
        store = RealtimeDataStore()
        data = {"futs_askp1": 367.40, "futs_bidp1": 367.30}
        store.update(SubscriptionType.NIGHT_FUTURES_ASK_BID, "101V06", data)

        result = store.get_night_futures_orderbook("101V06")
        assert result["futs_askp1"] == 367.40

    def test_night_option_trade_store(self):
        store = RealtimeDataStore()
        data = {"optn_prpr": 3.50, "delta": 0.45}
        store.update(SubscriptionType.NIGHT_OPTION_TRADE, "101W9000", data)

        result = store.get_night_option_trade("101W9000")
        assert result["optn_prpr"] == 3.50

    def test_night_option_orderbook_store(self):
        store = RealtimeDataStore()
        data = {"optn_askp1": 3.55, "optn_bidp1": 3.45}
        store.update(SubscriptionType.NIGHT_OPTION_ASK_BID, "101W9000", data)

        result = store.get_night_option_orderbook("101W9000")
        assert result["optn_askp1"] == 3.55

    def test_night_store_returns_none_for_missing(self):
        store = RealtimeDataStore()
        assert store.get_night_futures_trade("NONE") is None
        assert store.get_night_futures_orderbook("NONE") is None
        assert store.get_night_option_trade("NONE") is None
        assert store.get_night_option_orderbook("NONE") is None


class TestNightWSAgentSubscription:
    """WSAgent 야간 구독 테스트"""

    def test_subscribe_night_futures(self):
        agent = WSAgent(approval_key="test_key")
        sub_id = agent.subscribe(
            SubscriptionType.NIGHT_FUTURES_TRADE, "101V06"
        )
        assert sub_id == "H0MFCNT0_101V06"
        assert sub_id in agent.subscriptions

    def test_subscribe_night_futures_orderbook(self):
        agent = WSAgent(approval_key="test_key")
        sub_id = agent.subscribe(
            SubscriptionType.NIGHT_FUTURES_ASK_BID, "101V06"
        )
        assert sub_id == "H0MFASP0_101V06"

    def test_subscribe_night_option(self):
        agent = WSAgent(approval_key="test_key")
        sub_id = agent.subscribe(
            SubscriptionType.NIGHT_OPTION_TRADE, "101W9000"
        )
        assert sub_id == "H0EUCNT0_101W9000"

    def test_subscribe_night_option_orderbook(self):
        agent = WSAgent(approval_key="test_key")
        sub_id = agent.subscribe(
            SubscriptionType.NIGHT_OPTION_ASK_BID, "101W9000"
        )
        assert sub_id == "H0EUASP0_101W9000"

    def test_subscribe_multiple_night_types(self):
        """야간선물 체결+호가 동시 구독"""
        agent = WSAgent(approval_key="test_key")
        id1 = agent.subscribe(SubscriptionType.NIGHT_FUTURES_TRADE, "101V06")
        id2 = agent.subscribe(SubscriptionType.NIGHT_FUTURES_ASK_BID, "101V06")
        id3 = agent.subscribe(SubscriptionType.NIGHT_OPTION_TRADE, "101W9000")
        id4 = agent.subscribe(SubscriptionType.NIGHT_OPTION_ASK_BID, "101W9000")

        assert len(agent.subscriptions) == 4
        assert all(
            sid in agent.subscriptions for sid in [id1, id2, id3, id4]
        )
