"""종목 마스터 다운로드·캐시·검색의 네트워크 없는 회귀 테스트."""

import io
import zipfile
from datetime import datetime

from kis_agent.utils import stock_master


def _master_line(code, name):
    return code.encode("euc-kr").ljust(9, b" ") + b" " * 12 + name.encode("euc-kr").ljust(40, b" ") + b"\n"


class _Response:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


def test_download_master_handles_zip_plain_and_invalid_records(monkeypatch):
    raw = _master_line("A005930", "삼성전자") + b"short\n" + _master_line("", "잘못된코드")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("kospi.mst", raw)
    monkeypatch.setattr(stock_master.urllib.request, "urlopen", lambda *args, **kwargs: _Response(buffer.getvalue()))
    assert stock_master._download_master("kospi") == [{"code": "005930", "name": "삼성전자", "market": "코스피"}]
    monkeypatch.setattr(stock_master.urllib.request, "urlopen", lambda *args, **kwargs: _Response(raw))
    assert stock_master._download_master("kosdaq")[0]["market"] == "코스닥"


def test_cache_load_refresh_fallback_search_and_resolve(tmp_path, monkeypatch):
    monkeypatch.setattr(stock_master, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(stock_master, "_stock_cache", [])
    monkeypatch.setattr(stock_master, "_cache_date", None)
    assert stock_master._load_cache() == []
    assert not stock_master._is_cache_fresh()
    stocks = [
        {"code": "005930", "name": "삼성전자", "market": "코스피"},
        {"code": "005935", "name": "삼성전자우", "market": "코스피"},
        {"code": "000660", "name": "SK하이닉스", "market": "코스피"},
    ]
    stock_master._save_cache(stocks)
    assert stock_master._load_cache() == stocks
    assert stock_master._is_cache_fresh()
    assert stock_master.load_stocks() == stocks
    assert stock_master.load_stocks() == stocks  # 메모리 캐시
    assert stock_master.search("005930") == [stocks[0]]
    assert stock_master.search("삼성") == stocks[:2]
    assert stock_master.search("닉", limit=1) == [stocks[2]]
    assert stock_master.resolve_code("005930") == "005930"
    assert stock_master.resolve_code("삼성전자우") == "005935"
    assert stock_master.resolve_code("없는종목") is None

    monkeypatch.setattr(stock_master, "_stock_cache", [])
    monkeypatch.setattr(stock_master, "_is_cache_fresh", lambda: False)
    monkeypatch.setattr(stock_master, "_download_master", lambda exchange: stocks[:1] if exchange == "kospi" else stocks[1:])
    assert stock_master.load_stocks(force_refresh=True) == stocks
    monkeypatch.setattr(stock_master, "_stock_cache", [])
    monkeypatch.setattr(stock_master, "_download_master", lambda exchange: (_ for _ in ()).throw(RuntimeError("offline")))
    assert stock_master.load_stocks(force_refresh=True) == stocks
    monkeypatch.setattr(stock_master, "_load_cache", lambda: [])
    assert stock_master.load_stocks(force_refresh=True) == []
    monkeypatch.setattr(stock_master, "load_stocks", lambda: [])
    assert stock_master.search("삼성") == []
