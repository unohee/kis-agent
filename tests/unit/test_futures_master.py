"""
선물옵션 마스터 유틸리티 테스트

다운로드 모킹, 캐싱, 검색, 근월물 조회 테스트
"""

from unittest.mock import MagicMock, patch

import pytest

from kis_agent.utils.futures_master import (
    _IDX_TYPE_MAP,
    _download_index_master,
    _filter_markets,
    get_current_futures,
    get_futures_by_month_type,
    load_futures,
    resolve_futures_code,
    search,
)

# 테스트용 샘플 데이터
SAMPLE_SYMBOLS = [
    {
        "code": "A01606",
        "std_code": "KR4A01660005",
        "name": "F 202606",
        "atm": "",
        "strike": "00000.00",
        "month_type": "1",
        "underlying_code": "2001",
        "underlying_name": "KOSPI200",
        "product_type": "1",
        "product_type_name": "지수선물",
        "market": "index",
    },
    {
        "code": "A01609",
        "std_code": "KR4A01690002",
        "name": "F 202609",
        "atm": "",
        "strike": "00000.00",
        "month_type": "2",
        "underlying_code": "2001",
        "underlying_name": "KOSPI200",
        "product_type": "1",
        "product_type_name": "지수선물",
        "market": "index",
    },
    {
        "code": "A05604",
        "std_code": "KR4A05640003",
        "name": "미니F 202604",
        "atm": "",
        "strike": "00000.00",
        "month_type": "1",
        "underlying_code": "2001",
        "underlying_name": "KOSPI200",
        "product_type": "B",
        "product_type_name": "미니선물",
        "market": "index",
    },
    {
        "code": "201MA350",
        "std_code": "KR4201MA3500",
        "name": "C 202606 350.0",
        "atm": "3",
        "strike": "00350.00",
        "month_type": "1",
        "underlying_code": "2001",
        "underlying_name": "KOSPI200",
        "product_type": "5",
        "product_type_name": "지수콜옵션",
        "market": "index",
    },
    {
        "code": "GC2604",
        "std_code": "KR4GC2604001",
        "name": "금F 202604",
        "atm": "",
        "strike": "",
        "month_type": "1",
        "underlying_code": "GC",
        "underlying_name": "금",
        "product_type": "11",
        "product_type_name": "상품1",
        "market": "commodity",
    },
]


@pytest.fixture(autouse=True)
def clear_cache():
    """각 테스트 전 메모리 캐시 초기화"""
    import kis_agent.utils.futures_master as fm
    fm._futures_cache = []
    fm._cache_date = None
    yield


class TestFilterMarkets:
    def test_no_filter(self):
        result = _filter_markets(SAMPLE_SYMBOLS, None)
        assert len(result) == len(SAMPLE_SYMBOLS)

    def test_index_only(self):
        result = _filter_markets(SAMPLE_SYMBOLS, ["index"])
        assert all(s["market"] == "index" for s in result)
        assert len(result) == 4

    def test_commodity_only(self):
        result = _filter_markets(SAMPLE_SYMBOLS, ["commodity"])
        assert len(result) == 1
        assert result[0]["code"] == "GC2604"


class TestSearch:
    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_exact_code_match(self, mock_load):
        results = search("A01606")
        assert len(results) == 1
        assert results[0]["code"] == "A01606"

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_name_search(self, mock_load):
        results = search("F 2026")
        assert len(results) >= 2
        assert results[0]["code"] == "A01606"

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_partial_name(self, mock_load):
        results = search("미니")
        assert len(results) == 1
        assert results[0]["code"] == "A05604"

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_product_type_filter(self, mock_load):
        results = search("F", product_types=["지수선물"])
        assert all(s["product_type_name"] == "지수선물" for s in results)

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_empty_query(self, mock_load):
        results = search("NONEXISTENT")
        assert len(results) == 0

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_limit(self, mock_load):
        results = search("F", limit=1)
        assert len(results) == 1


class TestGetCurrentFutures:
    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_kospi200_current(self, mock_load):
        result = get_current_futures("kospi200")
        assert result is not None
        assert result["code"] == "A01606"
        assert result["month_type"] == "1"

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_mini_current(self, mock_load):
        result = get_current_futures("mini")
        assert result is not None
        assert result["code"] == "A05604"

    @patch("kis_agent.utils.futures_master.load_futures", return_value=[])
    def test_empty_returns_none(self, mock_load):
        result = get_current_futures("kospi200")
        assert result is None


class TestGetFuturesByMonthType:
    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_nearest_month(self, mock_load):
        results = get_futures_by_month_type("1", "지수선물")
        assert len(results) == 1
        assert results[0]["code"] == "A01606"

    @patch("kis_agent.utils.futures_master.load_futures", return_value=SAMPLE_SYMBOLS)
    def test_next_month(self, mock_load):
        results = get_futures_by_month_type("2", "지수선물")
        assert len(results) == 1
        assert results[0]["code"] == "A01609"


class TestResolveFuturesCode:
    @patch("kis_agent.utils.futures_master.search")
    def test_resolve_by_name(self, mock_search):
        mock_search.return_value = [{"code": "A01606", "name": "F 202606"}]
        assert resolve_futures_code("F 202606") == "A01606"

    @patch("kis_agent.utils.futures_master.search")
    def test_resolve_by_code(self, mock_search):
        mock_search.return_value = [{"code": "A01606", "name": "F 202606"}]
        assert resolve_futures_code("A01606") == "A01606"

    @patch("kis_agent.utils.futures_master.search")
    def test_resolve_not_found(self, mock_search):
        mock_search.return_value = []
        assert resolve_futures_code("INVALID") is None


class TestIdxTypeMap:
    def test_all_types_defined(self):
        expected_types = ["1", "2", "3", "4", "5", "6", "7", "8",
                          "9", "A", "B", "C", "D", "E", "J", "K", "L", "M"]
        for t in expected_types:
            assert t in _IDX_TYPE_MAP


class TestDownloadIntegration:
    """실제 다운로드 통합 테스트 (네트워크 필요)"""

    @pytest.mark.slow
    def test_download_index_master(self):
        symbols = _download_index_master()
        assert len(symbols) > 100
        # KOSPI200 선물이 있어야 함
        kospi_futures = [s for s in symbols if s["product_type"] == "1"]
        assert len(kospi_futures) >= 3

    @pytest.mark.slow
    def test_load_futures_full(self):
        symbols = load_futures(force_refresh=True)
        assert len(symbols) > 100

        # 근월물이 있어야 함
        cur = get_current_futures()
        assert cur is not None
        assert cur["month_type"] == "1"
