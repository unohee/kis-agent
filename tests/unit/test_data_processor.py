"""DataProcessor의 메시지 파싱과 지표 계산 회귀 테스트."""

import json

import pytest
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from kis_agent.websocket.data_processor import DataProcessor


def _binary_message(header, body):
    header_bytes = json.dumps(header).encode()
    return len(header_bytes).to_bytes(2, "big") + header_bytes + body


def test_process_message_json_pingpong_key_and_invalid_type():
    processor = DataProcessor()

    pingpong = processor.process_message('{"header": {"tr_id": "PINGPONG"}}')
    assert pingpong["type"] == "PINGPONG"

    processor.process_message(
        json.dumps({"header": {"tr_id": "H0STCNT0", "tr_key": "MTIzNDU2Nzg5MDEyMzQ1Ng==", "tr_iv": "MTIzNDU2Nzg5MDEyMzQ1Ng=="}})
    )
    assert processor.aes_keys["H0STCNT0"] == (b"1234567890123456", b"1234567890123456")

    with pytest.raises(ValueError, match="지원하지 않는"):
        processor.process_message(1)
    with pytest.raises(json.JSONDecodeError):
        processor.process_message("not-json")


def test_process_binary_plain_and_encrypted_messages():
    processor = DataProcessor()
    plain = processor.process_message(
        _binary_message({"tr_id": "plain"}, b'{"output": {"value": 1}}')
    )
    assert plain["tr_id"] == "plain"
    assert plain["body"]["output"]["value"] == 1

    key = iv = b"1234567890123456"
    processor.aes_keys["secret"] = (key, iv)
    encrypted = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(b'{"ok": true}', AES.block_size))
    decoded = processor.process_message(
        _binary_message({"tr_id": "secret", "encrypt": "Y"}, encrypted)
    )
    assert decoded["body"] == {"ok": True}

    with pytest.raises(ValueError, match="AES 키"):
        processor._decrypt_aes(b"bad", b"", iv)


def test_trade_orderbook_index_and_indicators():
    processor = DataProcessor()
    assert processor.parse_trade_data({"tr_id": "other"}) is None
    assert processor.parse_trade_data({"tr_id": "H0STCNT0", "body": {}}) is None

    output = {
        "stck_shrn_iscd": "005930", "stck_bsop_date": "Samsung", "stck_prpr": "100",
        "prdy_vrss": "2", "prdy_ctrt": "2.0", "acml_vol": "10", "stck_cntg_hour": "090000",
    }
    trade = processor.parse_trade_data({"tr_id": "H0STCNT0", "body": {"output": output}})
    assert trade["price"] == 100
    processor.trade_history["005930"] = [{"price": 1}] * 1000
    processor.parse_trade_data({"tr_id": "H0STCNT0", "body": {"output": output}})
    assert len(processor.trade_history["005930"]) == 1000
    processor.trade_history["005930"] = [{"price": value} for value in range(1, 26)]
    indicators = processor.calculate_indicators("005930")
    assert indicators["rsi"] == 100 and indicators["macd"] is None
    processor.trade_history["005930"] = [{"price": value} for value in range(1, 27)]
    assert processor.calculate_indicators("005930")["macd"] is not None
    assert processor.calculate_indicators("missing") == {}
    assert processor._calculate_rsi([1]) is None
    assert processor._calculate_rsi([3, 2] * 8) < 100

    assert processor.parse_orderbook_data({"tr_id": "other"}) is None
    assert processor.parse_orderbook_data({"tr_id": "H0STASP0", "body": {}}) is None
    orderbook = processor.parse_orderbook_data({
        "tr_id": "H0STASP0", "body": {"output": {"stck_shrn_iscd": "005930", "askp1": "101", "askp_rsqn1": "2", "bidp1": "99"}}
    })
    assert orderbook["ask_prices"] == [101] and orderbook["bid_volumes"] == [0]
    assert processor.parse_index_data({"tr_id": "other"}) is None
    assert processor.parse_index_data({"tr_id": "H0IF1000", "body": {}}) is None
    index = processor.parse_index_data({
        "tr_id": "H0IF1000", "body": {"output": {"bstp_nmix_prpr": "2500", "bstp_nmix_prdy_vrss": "10", "prdy_vrss_sign": "0.4"}}
    })
    assert index["value"] == 2500.0
