"""Realtime (WebSocket) receive path and feeds against the official KIS spec.

Frame format (workbook, every realtime sheet):
``encrypted(0|1) | TR_ID | record count | v1^v2^...`` where a count > 1 means the
values of several records are concatenated in order.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from kis_agent.core.constants import WS_MOCK_URL
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError
from kis_agent.websocket.ws_agent import MAX_SUBSCRIPTIONS, WSAgent
from kis_agent.websocket.ws_fields import FIELDS, fields_for
from kis_agent.websocket.ws_helpers import RealtimeDataParser, WSAgentWithStore
from kis_agent.websocket.ws_types import KEYLESS_TR_IDS, SubscriptionType

ST = SubscriptionType
FUTURES_PREFIXES = ("H0IF", "H0IO", "H0CF", "H0ZF", "H0ZO", "H0MF", "H0EU", "HDFF")

NEW_TYPES = {
    "STOCK_EXPECTED_KRX": "H0STANC0",
    "MARKET_OPERATION": "H0STMKO0",
    "STOCK_TRADE_TOTAL": "H0UNCNT0",
    "STOCK_ASK_BID_TOTAL": "H0UNASP0",
    "PROGRAM_TRADE_TOTAL": "H0UNPGM0",
    "MEMBER_TRADE_TOTAL": "H0UNMBC0",
    "MARKET_OPERATION_TOTAL": "H0UNMKO0",
    "INDEX_PROGRAM_TRADE": "H0UPPGM0",
    "ELW_TRADE": "H0EWCNT0",
    "ELW_ASK_BID": "H0EWASP0",
    "ELW_EXPECTED": "H0EWANC0",
    "ETF_NAV": "H0STNAV0",
    "BOND_TRADE": "H0BJCNT0",
    "BOND_ASK_BID": "H0BJASP0",
    "BOND_INDEX": "H0BICNT0",
}


@pytest.fixture
def agent():
    return WSAgent("approval", url="ws://example", auto_reconnect=False)


def _record(tr_id, **values):
    return [str(values.get(name, "")) for name in FIELDS[tr_id]]


def _frame(tr_id, *records, encrypted="0"):
    payload = "^".join(v for record in records for v in record)
    return f"{encrypted}|{tr_id}|{len(records):03d}|{payload}"


# ----- layouts -------------------------------------------------------------


@pytest.mark.parametrize("name,tr_id", sorted(NEW_TYPES.items()))
def test_new_subscription_types(name, tr_id):
    assert SubscriptionType[name].value == tr_id
    assert fields_for(tr_id)


def test_every_non_futures_type_has_an_official_layout():
    missing = [
        member.name
        for member in SubscriptionType
        if not member.value.startswith(FUTURES_PREFIXES) and member.value not in FIELDS
    ]
    assert missing == []
    assert fields_for("UNKNOWN") == ()


@pytest.mark.parametrize(
    "tr_id,first,count",
    [
        ("H0STCNT0", "mksc_shrn_iscd", 47),  # market_cls_code appended (2026 sample)
        ("H0STASP0", "mksc_shrn_iscd", 63),
        ("H0NXASP0", "mksc_shrn_iscd", 65),
        ("H0UNASP0", "mksc_shrn_iscd", 66),
        ("H0UPCNT0", "bstp_cls_code", 30),
        ("H0STMBC0", "mksc_shrn_iscd", 78),
        ("H0UPPGM0", "bstp_cls_code", 88),
        ("H0UNMKO0", "trht_yn", 10),
        ("H0STNAV0", "mksc_shrn_iscd", 8),
        ("HDFSCNT0", "rsym", 26),
        ("HDFSASP1", "rsym", 17),
        ("H0STCNI0", "cust_id", 26),
    ],
)
def test_official_layout_shape(tr_id, first, count):
    assert FIELDS[tr_id][0] == first
    assert len(FIELDS[tr_id]) == count


def test_parser_keeps_time_and_code_fields_as_strings():
    record = _record(
        "H0STOUP0", mksc_shrn_iscd="005930", oprc_hour="090015", stck_prpr="71000"
    )
    parsed = RealtimeDataParser.parse(ST.OVERTIME_TRADE, record)
    assert parsed["oprc_hour"] == "090015"
    assert parsed["stck_prpr"] == 71000
    nav = RealtimeDataParser.parse(
        ST.ETF_NAV, _record("H0STNAV0", mksc_shrn_iscd="069500", nav="37235.46")
    )
    assert nav == {**nav, "mksc_shrn_iscd": "069500", "nav": 37235.46}


# ----- frame parsing -------------------------------------------------------


def test_parse_frame_splits_multi_record_frames(agent):
    a = _record("H0STCNT0", mksc_shrn_iscd="005930", stck_prpr="71000")
    b = _record("H0STCNT0", mksc_shrn_iscd="005930", stck_prpr="71100")
    tr_id, records = agent._parse_frame(_frame("H0STCNT0", a, b))
    assert tr_id == "H0STCNT0"
    assert records == [a, b]


def test_parse_frame_keeps_one_record_when_count_does_not_divide(agent):
    assert agent._parse_frame("0|H0STCNT0|002|a^b^c") == ("H0STCNT0", [["a", "b", "c"]])
    assert agent._parse_frame("0|H0STCNT0|x|a^b") == ("H0STCNT0", [["a", "b"]])
    assert agent._parse_frame("0|H0STCNT0") is None


def test_encryption_flag_is_the_first_field_not_the_count(agent):
    """The count "001" used to be read as the flag, so notices were never decrypted."""
    agent.aes_keys["H0STCNI0"] = ("k", "iv")
    agent._decrypt_aes = MagicMock(return_value="hts^acct")
    assert agent._parse_frame("1|H0STCNI0|001|cipher") == (
        "H0STCNI0",
        [["hts", "acct"]],
    )
    agent._decrypt_aes.assert_called_once_with("k", "iv", "cipher")
    agent._decrypt_aes.reset_mock()
    assert agent._parse_frame("0|H0STCNT0|001|plain^text") == (
        "H0STCNT0",
        [["plain", "text"]],
    )
    agent._decrypt_aes.assert_not_called()


def test_encrypted_frame_without_key_is_dropped(agent):
    assert agent._parse_frame("1|H0GSCNI0|001|cipher") is None
    assert agent._parse_message("1|H0GSCNI0|001|cipher") == (None, None, None)


def test_subscription_response_stores_the_aes_key(agent):
    response = {
        "header": {"tr_id": "H0STCNI0", "tr_key": "hts", "encrypt": "Y"},
        "body": {
            "rt_cd": "0",
            "msg1": "SUBSCRIBE SUCCESS",
            "output": {"key": "k" * 32, "iv": "v" * 16},
        },
    }
    assert agent._handle_subscription_response(response)
    assert agent.aes_keys["H0STCNI0"] == ("k" * 32, "v" * 16)
    agent._remember_aes_key("X", "not-a-dict")
    assert "X" not in agent.aes_keys


def test_parse_message_json_and_first_record(agent):
    raw = json.dumps(
        {
            "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
            "body": {"output": {"key": "k", "iv": "i"}},
        }
    )
    tr_id, tr_key, data = agent._parse_message(raw)
    assert (tr_id, tr_key, agent.aes_keys["H0STCNT0"]) == (
        "H0STCNT0",
        "005930",
        ("k", "i"),
    )
    assert agent._parse_message("0|H0UNMKO0|001|N^^20") == (
        "H0UNMKO0",
        None,
        ["N", "", "20"],
    )


# ----- dispatch ------------------------------------------------------------


@pytest.mark.asyncio
async def test_every_record_of_a_multi_record_frame_is_dispatched(agent):
    seen = []
    agent.subscribe(
        ST.STOCK_TRADE, "005930", handler=lambda data, meta: seen.append(data[2])
    )
    a = _record("H0STCNT0", mksc_shrn_iscd="005930", stck_prpr="71000")
    b = _record("H0STCNT0", mksc_shrn_iscd="005930", stck_prpr="71100")
    await agent._handle_message(_frame("H0STCNT0", a, b))
    await asyncio.sleep(0)
    assert seen == ["71000", "71100"]
    assert agent.stats["messages_processed"] == 2


@pytest.mark.asyncio
async def test_keyless_feed_routes_to_the_only_subscription(agent):
    individual, by_type = [], []
    agent.subscribe(
        ST.MARKET_OPERATION_TOTAL,
        "005930",
        handler=lambda d, m: individual.append(m),
        tag="x",
    )
    agent.register_handler(ST.MARKET_OPERATION_TOTAL, lambda d, m: by_type.append(m))
    await agent._handle_message(_frame("H0UNMKO0", _record("H0UNMKO0", trht_yn="N")))
    assert individual == [{"tr_key": "005930", "tag": "x"}]
    assert by_type == [{"tr_key": "005930", "tag": "x"}]

    agent.subscribe(ST.MARKET_OPERATION_TOTAL, "000660")
    individual.clear(), by_type.clear()
    await agent._handle_message(_frame("H0UNMKO0", _record("H0UNMKO0", trht_yn="N")))
    assert individual == [] and by_type == [{}]


@pytest.mark.asyncio
async def test_unknown_tr_goes_to_default_handler_only(agent):
    seen = []
    agent.set_default_handler(lambda d, m: seen.append(m))
    await agent._handle_message("0|H0ZZZZZ0|001|a^b")
    assert seen == [{"tr_id": "H0ZZZZZ0", "tr_key": "a"}]
    assert agent.stats["messages_processed"] == 0


@pytest.mark.asyncio
async def test_pingpong_is_echoed_with_the_raw_frame(agent):
    raw = json.dumps({"header": {"tr_id": "PINGPONG", "datetime": "20261008093000"}})
    agent.ws = MagicMock(close_code=None)
    agent.ws.pong = AsyncMock()
    await agent._handle_message(raw)
    agent.ws.pong.assert_awaited_once_with(raw)

    agent.ws.pong = AsyncMock(side_effect=RuntimeError("closed"))
    await agent._handle_message(raw)  # failure is logged, not raised
    assert agent.stats["errors"] == 0

    agent.ws = None
    await agent._handle_message(raw)
    await agent._handle_message("PINGPONG")  # non-JSON heartbeat text is ignored


@pytest.mark.asyncio
async def test_invalid_json_is_counted_as_an_error(agent):
    await agent._handle_message("{not json")
    assert agent.stats["errors"] == 1


# ----- subscription limit and paper trading --------------------------------


def test_subscription_limit_is_41(agent):
    for i in range(MAX_SUBSCRIPTIONS):
        agent.subscribe(ST.STOCK_TRADE, f"{i:06d}")
    assert (
        agent.subscribe(ST.STOCK_TRADE, "000000") == "H0STCNT0_000000"
    )  # duplicate is fine
    with pytest.raises(ValueError, match="41"):
        agent.subscribe(ST.STOCK_TRADE, "999999")


@pytest.mark.parametrize("name", sorted(NEW_TYPES))
def test_new_feeds_are_real_only(name):
    paper = WSAgent("approval", url=WS_MOCK_URL, auto_reconnect=False)
    with pytest.raises(PaperTradingNotSupportedError):
        paper.subscribe(SubscriptionType[name], "005930")


# ----- convenience helpers ---------------------------------------------------


def test_convenience_helpers_build_official_keys(agent):
    assert agent.subscribe_stock_total("005930", with_orderbook=True) == [
        "H0UNCNT0_005930",
        "H0UNASP0_005930",
    ]
    assert agent.subscribe_expected(["005930", "000660"], market="krx") == [
        "H0STANC0_005930",
        "H0STANC0_000660",
    ]
    assert agent.subscribe_expected("005930", market="NXT") == ["H0NXANC0_005930"]
    assert agent.subscribe_expected("005930") == ["H0UNANC0_005930"]
    assert agent.subscribe_market_operation("005930") == ["H0STMKO0_005930"]
    assert agent.subscribe_market_operation("005930", market="TOTAL") == [
        "H0UNMKO0_005930"
    ]
    assert agent.subscribe_program_trading_total("005930") == ["H0UNPGM0_005930"]
    assert agent.subscribe_member_trading_total(["005930"]) == ["H0UNMBC0_005930"]
    assert agent.subscribe_index_program_trading() == ["H0UPPGM0_0001"]
    assert agent.subscribe_elw("57LA24", with_orderbook=True, with_expected=True) == [
        "H0EWCNT0_57LA24",
        "H0EWASP0_57LA24",
        "H0EWANC0_57LA24",
    ]
    assert agent.subscribe_elw("57LA25") == ["H0EWCNT0_57LA25"]
    assert agent.subscribe_etf_nav("069500") == ["H0STNAV0_069500"]
    assert agent.subscribe_bond("KR103502GA34", with_orderbook=True) == [
        "H0BJCNT0_KR103502GA34",
        "H0BJASP0_KR103502GA34",
    ]
    assert agent.subscribe_bond("KR103502GA35") == ["H0BJCNT0_KR103502GA35"]
    assert agent.subscribe_bond_index("KR103502GA34") == ["H0BICNT0_KR103502GA34"]
    with pytest.raises(ValueError):
        agent.subscribe_expected("005930", market="ETC")
    with pytest.raises(ValueError):
        agent.subscribe_market_operation("005930", market="NXT")


def test_overseas_helpers_build_rsym_keys(agent):
    assert agent.subscribe_overseas_stock(
        "aapl", exchange="nas", with_orderbook=True
    ) == [
        "HDFSCNT0_DNASAAPL",
        "HDFSASP0_DNASAAPL",
    ]
    assert agent.subscribe_overseas_stock("AAPL", exchange="BAQ", paid=True) == [
        "HDFSCNT0_RBAQAAPL"
    ]
    assert agent.subscribe_overseas_stock("DNYSIBM") == ["HDFSCNT0_DNYSIBM"]
    assert (
        agent.subscribe_overseas_asia_orderbook("00003", exchange="HKS")
        == "HDFSASP1_DHKS00003"
    )


def test_nxt_market_operation_is_keyed_by_stock_code(agent):
    assert agent.subscribe_market_operation_nxt("005930") == "H0NXMKO0_005930"

    def handler(data, meta):
        return None

    with pytest.raises(ValueError, match="종목코드"):
        agent.subscribe_market_operation_nxt(handler)  # old signature: handler only
    assert agent.subscribe_market_operation_nxt("000660", handler) == "H0NXMKO0_000660"
    assert agent.subscriptions["H0NXMKO0_000660"].handler is handler


# ----- store -----------------------------------------------------------------


def test_store_keys_keyless_feeds_by_the_subscription_key():
    agent = WSAgentWithStore("approval", url="ws://example", auto_reconnect=False)
    handler = agent._base_agent.type_handlers[ST.MARKET_OPERATION_TOTAL][0]
    record = _record("H0UNMKO0", trht_yn="N", mkop_cls_code="20")
    handler(record, {"tr_key": "005930"})
    assert agent.store.get("005930", ST.MARKET_OPERATION_TOTAL)["mkop_cls_code"] == "20"
    handler(record, {})  # not attributable: not stored under "N"
    assert agent.store.get("N", ST.MARKET_OPERATION_TOTAL) is None
    assert "H0UNMKO0" in KEYLESS_TR_IDS

    trade = agent._base_agent.type_handlers[ST.STOCK_TRADE][0]
    trade(_record("H0STCNT0", mksc_shrn_iscd="005930", stck_prpr="71000"), {})
    assert agent.store.get_trade("005930")["stck_prpr"] == 71000


@pytest.mark.asyncio
async def test_undecryptable_frame_reaches_no_handler(agent):
    seen = []
    agent.set_default_handler(lambda d, m: seen.append(d))
    await agent._handle_message("1|H0STCNI0|001|cipher")
    assert seen == [] and agent.stats["errors"] == 0
