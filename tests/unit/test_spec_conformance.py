"""Tests for the official-spec conformance checker (scripts/spec_conformance).

Fixture-driven unit tests run everywhere. The live comparison against the KIS
workbook and the open-trading-api clone runs only when both are present
locally (neither is tracked in git), like tests/unit/test_paper_trading.py.
"""

import json
import os
import sys
import textwrap

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from spec_conformance import check, official, ours  # noqa: E402

ENDPOINTS = {"PRICE": "/uapi/x/v1/quotations/price"}


def _api(url, real=(), paper=(), methods=("GET",), required=(), optional=()):
    api = official.SpecApi(url=url)
    api.names = ["name"]
    api.menus = {"menu"}
    api.mode = {"REST"}
    api.real_trs = set(real)
    api.paper_trs = set(paper)
    api.methods = set(methods)
    api.required = set(required)
    api.optional = set(optional)
    return api


def _sites(src):
    return ours.extract_call_sites(textwrap.dedent(src), "kis_agent/x.py", ENDPOINTS)


# ---------------------------------------------------------------------------
# official.py
# ---------------------------------------------------------------------------


class TestTrTokens:
    def test_whole_token_match_keeps_leading_letters(self):
        assert official.tr_tokens("HHPSTH60100C1") == ["HHPSTH60100C1"]

    def test_multiple_tokens_and_labels(self):
        assert official.tr_tokens("(매도) TTTC0011U (매수) TTTC0012U") == [
            "TTTC0011U",
            "TTTC0012U",
        ]

    def test_non_tr_text(self):
        assert official.tr_tokens("모의투자 미지원") == []
        assert official.tr_tokens(None) == []
        assert official.tr_tokens("KRX") == []


class TestParseApiSheet:
    def test_request_fields_and_url(self):
        rows = [
            ("URL 명", "/uapi/a"),
            ("구분", "Element", "한글명", "Type", "Required"),
            (
                "Request Header",
                "tr_id",
                "",
                "string",
                "Y",
                "13",
                "[실전투자]\nTTTT1004U : 미국\nTTTS1003U : 홍콩\n(구)TTTT1003U → (신)TTTT1004U\n"
                "[모의투자]\nVTTT1004U : 미국",
            ),
            ("Request Body", "CANO", "", "string", "Y"),
            (None, "EXCG_ID_DVSN_CD", "", "string", "N"),
            ("Response Body", "rt_cd", "", "string", "Y"),
        ]
        out = official.parse_api_sheet(rows)
        assert out == {
            "url": "/uapi/a",
            "required": {"CANO"},
            "optional": {"EXCG_ID_DVSN_CD"},
            "tr_real": {"TTTT1004U", "TTTS1003U"},
            "tr_paper": {"VTTT1004U"},
            "tr_old": {"TTTT1003U"},
        }

    def test_merge_intersects_required(self):
        api = official.SpecApi(url="/u")
        official._merge_fields(api, {"A", "B"}, {"C"})
        official._merge_fields(api, {"A"}, {"D"})
        assert api.required == {"A"}
        assert api.optional == {"B", "C", "D"}
        assert api.all_fields == {"A", "B", "C", "D"}


SAMPLE = '''
API_URL = "/uapi/overseas-stock/v1/trading/order"

def order(env_dv, ord_dv, ovrs_excg_cd, pdno):
    """Docstring mentions TTTX9999U which must be ignored."""
    if ord_dv == "buy":
        if ovrs_excg_cd in ("NASD", "NYSE"):
            tr_id = "TTTT1002U"
        elif ovrs_excg_cd == "SEHK":
            tr_id = "TTTS1002U"
    if env_dv == "demo":
        tr_id = "V" + tr_id[1:]
    params = {"OVRS_EXCG_CD": ovrs_excg_cd, "PDNO": pdno}
    params["ORD_SVR_DVSN_CD"] = "0"
    res = ka._url_fetch(API_URL, tr_id, "", params, postFlag=True)
'''


class TestParseSample:
    def test_rest_sample(self):
        s = official.parse_sample_source(
            SAMPLE, "examples_llm/x/order/order.py", "order"
        )
        assert s.url == "/uapi/overseas-stock/v1/trading/order"
        assert s.tr_ids == {"TTTT1002U", "TTTS1002U"}
        assert s.post is True
        assert s.keys == {"OVRS_EXCG_CD", "PDNO", "ORD_SVR_DVSN_CD"}
        # branching on ord_dv/env_dv is not a market selector; ovrs_excg_cd is
        assert s.tr_branch_keys == {"OVRS_EXCG_CD"}

    def test_module_without_api_url(self):
        assert official.parse_sample_source("x = 1\n", "f.py", "f") is None

    def test_ws_sample_columns(self):
        src = 'def f():\n    tr_id = "H0STCNT0"\n    msg = ka.data_fetch(tr_id, "1", {})\n    columns = ["MKSC_SHRN_ISCD", "STCK_PRPR"]\n'
        assert official.parse_ws_sample_source(src) == {
            "H0STCNT0": ["mksc_shrn_iscd", "stck_prpr"]
        }
        assert official.parse_ws_sample_source("x = 1\n") == {}

    def test_loaders_on_fixture_tree(self, tmp_path):
        rest = tmp_path / "examples_llm" / "overseas_stock" / "order"
        rest.mkdir(parents=True)
        (rest / "order.py").write_text(SAMPLE, encoding="utf-8")
        (rest / "chk_order.py").write_text("API_URL = 'x'\n", encoding="utf-8")
        ws = tmp_path / "examples_llm" / "domestic_stock" / "ccnl_krx"
        ws.mkdir(parents=True)
        (ws / "ccnl_krx.py").write_text(
            'def ccnl_krx():\n    tr_id = "H0STCNT0"\n    ka.data_fetch(tr_id, "1", {})\n    columns = ["A"]\n',
            encoding="utf-8",
        )
        samples = official.load_samples(str(tmp_path))
        assert list(samples) == ["/uapi/overseas-stock/v1/trading/order"]
        ws_samples = official.load_ws_samples(str(tmp_path))
        assert ws_samples["H0STCNT0"]["columns"] == ["a"]
        assert official.find_workbook(str(tmp_path)) is None


# ---------------------------------------------------------------------------
# ours.py
# ---------------------------------------------------------------------------


class TestExtractCallSites:
    def test_literals_and_endpoint_table(self):
        (site,) = _sites("""
            class A:
                def price(self, code):
                    return self._make_request_dict(
                        endpoint=API_ENDPOINTS["PRICE"], tr_id="FHKST01010100",
                        params={"FID_INPUT_ISCD": code, "FID_COND_MRKT_DIV_CODE": "J"})
            """)
        assert site.endpoints == {"/uapi/x/v1/quotations/price"}
        assert site.tr_ids == {"FHKST01010100"}
        assert site.methods == {"GET"}
        assert site.keys == {"FID_INPUT_ISCD", "FID_COND_MRKT_DIV_CODE"}
        assert site.keys_resolved
        assert site.key_literal == {
            "FID_INPUT_ISCD": False,
            "FID_COND_MRKT_DIV_CODE": True,
        }

    def test_correlated_flag_splits_url_tr_and_keys(self):
        sites = _sites("""
            class A:
                def bal(self):
                    is_irp = self.account["ACNT_PRDT_CD"] == "29"
                    endpoint = "/a/inquire-balance" if not is_irp else "/a/pension/inquire-balance"
                    tr_id = "TTTC8434R" if not is_irp else "TTTC2208R"
                    params = {"CANO": "1"}
                    if not is_irp:
                        params["AFHR_FLPR_YN"] = "N"
                    else:
                        params["ACCA_DVSN_CD"] = "00"
                    return self._make_request_dict(endpoint=endpoint, tr_id=tr_id, params=params)
            """)
        by_url = {next(iter(s.endpoints)): s for s in sites}
        assert by_url["/a/inquire-balance"].tr_ids == {"TTTC8434R"}
        assert by_url["/a/inquire-balance"].keys == {"CANO", "AFHR_FLPR_YN"}
        assert by_url["/a/pension/inquire-balance"].tr_ids == {"TTTC2208R"}
        assert by_url["/a/pension/inquire-balance"].keys == {"CANO", "ACCA_DVSN_CD"}
        assert all("is_irp=" in s.where for s in sites)

    def test_tr_only_variation_is_merged(self):
        (site,) = _sites("""
            def f(self, old):
                tr = "CTSC9215R" if old else "TTTC0081R"
                return self._make_request_dict(endpoint="/a", tr_id=tr, params={"X": 1})
            """)
        assert site.tr_ids == {"CTSC9215R", "TTTC0081R"}
        assert "[" not in site.where

    def test_account_params_spread_and_dict_lookup(self):
        (site,) = _sites("""
            TABLE = {"NASD": "TTTT1002U", "SEHK": "TTTS1002U"}
            class A:
                def buy(self, excd):
                    account_params = self._get_account_params()
                    params = {**account_params, "OVRS_EXCG_CD": excd}
                    return self._make_request_dict(endpoint="/o", tr_id=TABLE[excd], params=params, method="POST")
            """)
        assert site.tr_ids == {"TTTT1002U", "TTTS1002U"}
        assert site.keys == {"CANO", "ACNT_PRDT_CD", "OVRS_EXCG_CD"}
        assert site.keys_resolved
        assert site.methods == {"POST"}

    def test_helper_call_over_dict_table_yields_all_values(self):
        (site,) = _sites(
            """
            class A:
                _BUY = {"NASD": "TTTT1002U", "SEHK": "TTTS1002U"}
                def buy(self, excd):
                    tr_id = self._pick(self._BUY, excd)
                    return self._make_request_dict(endpoint="/o", tr_id=tr_id, params={"A": 1})
            """
        )
        assert site.tr_ids == {"TTTT1002U", "TTTS1002U"}

    def test_positional_make_request_and_defaults(self):
        (site,) = _sites("""
            def f(self, method="POST"):
                return self.client.make_request("/p", "TTTC0011U", {"A": 1}, method)
            """)
        assert site.endpoints == {"/p"}
        assert site.methods == {"POST"}

    def test_unresolved_and_pass_through(self):
        sites = _sites("""
            def _make_request_dict(self, endpoint, tr_id, params):
                return self.client.make_request(endpoint=endpoint, tr_id=tr_id, params=params)
            def g(self):
                return self._make_request_dict(endpoint=self.url, tr_id=self.tr, params=build())
            """)
        assert len(sites) == 1
        assert not sites[0].resolvable
        assert sites[0].keys_resolved is False

    def test_update_call_and_module_constant(self):
        (site,) = _sites("""
            URL = "/m"
            def f(self):
                params = {"A": 1}
                params.update({"B": 2})
                return self._make_request_dict(endpoint=URL, tr_id="X1234567", params=params)
            """)
        assert site.endpoints == {"/m"}
        assert site.keys == {"A", "B"}


class TestWsDefinitions:
    TYPES = 'class SubscriptionType(Enum):\n    STOCK_TRADE = "H0STCNT0"\n    STOCK_TRADE_NXT = "H0NXCNT0"\n'
    HELPERS = textwrap.dedent("""
        class RealtimeDataParser:
            STOCK_TRADE_FIELDS = ["MKSC_SHRN_ISCD", "stck_prpr"]

            @classmethod
            def parse(cls, sub_type, values):
                ST = SubscriptionType
                field_map = {ST.STOCK_TRADE: cls.STOCK_TRADE_FIELDS, ST.STOCK_TRADE_NXT: cls.STOCK_TRADE_FIELDS}
        """)

    def test_types_and_field_map(self):
        assert ours.load_ws_types(self.TYPES) == {
            "STOCK_TRADE": "H0STCNT0",
            "STOCK_TRADE_NXT": "H0NXCNT0",
        }
        lists, mapping = ours.load_ws_field_lists(self.HELPERS)
        assert lists == {"STOCK_TRADE_FIELDS": ["mksc_shrn_iscd", "stck_prpr"]}
        assert mapping == {
            "STOCK_TRADE": "STOCK_TRADE_FIELDS",
            "STOCK_TRADE_NXT": "STOCK_TRADE_FIELDS",
        }

    def test_load_ws_from_tree(self, tmp_path):
        ws = tmp_path / "kis_agent" / "websocket"
        ws.mkdir(parents=True)
        (ws / "ws_types.py").write_text(self.TYPES, encoding="utf-8")
        (ws / "ws_helpers.py").write_text(self.HELPERS, encoding="utf-8")
        out = ours.load_ws(str(tmp_path))
        assert out["H0STCNT0"]["fields"] == ["mksc_shrn_iscd", "stck_prpr"]


# ---------------------------------------------------------------------------
# check.py rules
# ---------------------------------------------------------------------------


def _site(**kw):
    base = {
        "where": "kis_agent/x.py:1",
        "func": "f",
        "endpoints": {"/u"},
        "tr_ids": {"T0000001R"},
        "methods": {"GET"},
        "keys": {"A"},
        "keys_resolved": True,
        "key_literal": {"A": True},
    }
    base.update(kw)
    return ours.CallSite(**base)


def _rules(findings):
    return sorted(f.rule for f in findings)


class TestCheckRest:
    def test_clean(self):
        spec = {"/u": _api("/u", real={"T0000001R"}, required={"A"})}
        assert check.check_rest([_site()], spec, {}) == []

    def test_every_rule(self):
        spec = {
            "/u": _api(
                "/u",
                real={"T0000002R"},
                methods={"POST"},
                required={"B"},
                optional={"CC"},
            )
        }
        site = _site(keys={"A", "cc", "tr_cont"})
        rules = _rules(check.check_rest([site], spec, {}))
        assert rules == [
            "case-only-key",
            "method-mismatch",
            "missing-required",
            "tr-mismatch",
            "unknown-key",
        ]

    def test_paper_tr_and_sample_tr_are_accepted(self):
        spec = {
            "/u": _api("/u", real={"T0000001R"}, paper={"V0000001R"}, required={"A"})
        }
        sample = official.SampleApi("f", "/u", {"T0000009R"}, False, set())
        site = _site(tr_ids={"V0000001R", "T0000009R"})
        assert check.check_rest([site], spec, {"/u": [sample]}) == []

    def test_retired_tr_is_its_own_rule(self):
        api = _api("/u", real={"T0000002R"}, required={"A"})
        api.old_trs = {"T0000001R"}
        assert _rules(check.check_rest([_site()], {"/u": api}, {})) == ["deprecated-tr"]

    def test_tr_selection(self):
        spec = {
            "/u": _api(
                "/u", real={"T0000001R"}, required=set(), optional={"OVRS_EXCG_CD"}
            )
        }
        sample = official.SampleApi(
            "f", "/u", {"T0000001R"}, True, {"OVRS_EXCG_CD"}, {"OVRS_EXCG_CD"}
        )
        site = _site(keys={"OVRS_EXCG_CD"}, key_literal={"OVRS_EXCG_CD": False})
        assert _rules(check.check_rest([site], spec, {"/u": [sample]})) == [
            "tr-selection"
        ]
        literal = _site(keys={"OVRS_EXCG_CD"}, key_literal={"OVRS_EXCG_CD": True})
        assert check.check_rest([literal], spec, {"/u": [sample]}) == []

    def test_url_not_in_spec_and_unresolved(self):
        assert _rules(check.check_rest([_site(endpoints={"/nope"})], {}, {})) == [
            "url-not-in-spec"
        ]
        assert _rules(
            check.check_rest([_site(endpoints={ours.UNRESOLVED})], {}, {})
        ) == ["unresolved"]
        spec = {"/u": _api("/u", real={"T0000001R"})}
        assert _rules(check.check_rest([_site(keys_resolved=False)], spec, {})) == [
            "unresolved"
        ]

    def test_spec_without_request_table_skips_key_rules(self):
        api = _api("/u", real={"T0000001R"})
        api.required = None
        assert check.check_rest([_site(keys={"Z"})], {"/u": api}, {}) == []


class TestCheckWsAndCoverage:
    def test_ws_position_and_tail(self):
        ours_ws = {
            "H0A": {"members": ["A"], "fields": ["x", "y"]},
            "H0B": {"members": ["B"], "fields": ["x"]},
            "H0C": {"members": ["C"], "fields": ["x", "y"]},
            "H0D": {"members": ["D"], "fields": None},
        }
        off = {
            "H0A": {"file": "a", "columns": ["x", "z"]},
            "H0B": {"file": "b", "columns": ["x", "y"]},
            "H0C": {"file": "c", "columns": ["x", "y"]},
        }
        assert _rules(check.check_ws(ours_ws, off)) == ["ws-columns", "ws-missing-tail"]

    def test_coverage(self, tmp_path):
        pkg = tmp_path / "kis_agent"
        pkg.mkdir()
        (pkg / "auth.py").write_text('URL = "/oauth2/tokenP"\n', encoding="utf-8")
        spec = {
            "/u": _api("/u"),
            "/missing": _api("/missing", methods={"POST"}),
            "/oauth2/tokenP": _api("/oauth2/tokenP"),
            "/tryitout/H0STCNT0": _api("/tryitout/H0STCNT0", real={"H0STCNT0"}),
        }
        allow = check.Allowlist([], [], [], {"/oauth2/tokenP": "/oauth2/tokenP"}, [])
        findings = check.check_coverage(
            [_site()],
            spec,
            {"H0STCNT0": {}},
            {"H0UNCNT0": {"file": "s", "columns": []}},
            allow,
            str(tmp_path),
        )
        assert [(f.rule, f.url, f.order_surface) for f in findings] == [
            ("coverage-rest", "/missing", True),
            ("coverage-ws", "H0UNCNT0", False),
        ]

    def test_spec_consistency(self):
        spec = {"/u": _api("/u", real={"T0000001R"})}
        samples = {
            "/u": [official.SampleApi("f", "/u", {"T0000002R"}, False, set())],
            "/gone": [official.SampleApi("g", "/gone", set(), False, set())],
        }
        assert _rules(check.check_spec_consistency(spec, samples)) == [
            "spec-inconsistency",
            "spec-inconsistency",
        ]


class TestAllowlistBaselineAndReport:
    def test_allowlist(self, tmp_path):
        path = tmp_path / "allow.json"
        path.write_text(
            json.dumps(
                {
                    "urls": [{"glob": "/uapi/domestic-futureoption/*"}],
                    "paths": [{"glob": "kis_agent/futures/*"}],
                    "ws_trs": [{"glob": "H0IF*"}],
                    "implemented_outside_make_request": [{"url": "/x", "needle": "/x"}],
                    "findings": [
                        {
                            "rule": "unknown-key",
                            "url": "/u",
                            "where": "kis_agent/y.py",
                            "detail_contains": "FOO",
                        },
                        {"rule": "missing-required", "where_contains": "[cancel=True]"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        allow = check.Allowlist.load(str(path))
        F = check.Finding
        assert allow.finding_allowed(
            F("tr-mismatch", "kis_agent/a.py:1", "/uapi/domestic-futureoption/v1/x", "")
        )
        assert allow.finding_allowed(
            F("tr-mismatch", "kis_agent/futures/a.py:1", "/u", "")
        )
        assert allow.finding_allowed(F("coverage-ws", "-", "H0IFCNT0", ""))
        assert allow.finding_allowed(
            F("unknown-key", "kis_agent/y.py:3", "/u", "unknown=['FOO']")
        )
        assert not allow.finding_allowed(
            F("unknown-key", "kis_agent/y.py:3", "/u", "unknown=['BAR']")
        )
        assert not allow.finding_allowed(
            F("unknown-key", "kis_agent/z.py:3", "/u", "FOO")
        )
        assert not allow.finding_allowed(
            F("missing-required", "kis_agent/y.py:3", "/u", "FOO")
        )
        assert allow.finding_allowed(
            F("missing-required", "kis_agent/y.py:3 [cancel=True]", "/u", "")
        )
        assert check.Allowlist.load(str(tmp_path / "absent.json")).findings == []

    def test_finding_key_ignores_line_numbers(self):
        a = check.Finding(
            "tr-mismatch", "kis_agent/a.py:10 [x=True]", "/u", "func=buy ours=[]"
        )
        b = check.Finding("tr-mismatch", "kis_agent/a.py:99", "/u", "func=buy other")
        assert a.key == b.key == "tr-mismatch|kis_agent/a.py|buy|/u"
        assert (
            check.Finding("coverage-rest", "-", "/m", "name").key
            == "coverage-rest|-||/m"
        )

    def test_baseline_roundtrip(self, tmp_path):
        path = str(tmp_path / "b.json")
        findings = [
            check.Finding("tr-mismatch", "kis_agent/a.py:1", "/u", "func=f"),
            check.Finding("unresolved", "x", "/u", ""),
        ]
        assert check.write_baseline(path, findings) == 1
        assert check.load_baseline(path) == {"tr-mismatch|kis_agent/a.py|f|/u"}
        assert check.load_baseline(None) == set()

    def test_render_markdown(self):
        f = check.Finding("tr-mismatch", "kis_agent/a.py:1", "/u", "func=f", True)
        md = check.render_markdown(
            {
                "stats": {"errors": 1},
                "findings": [f],
                "new_errors": [f],
                "workbook": "wb.xlsx",
            }
        )
        assert "## NEW (not in baseline, 1)" in md
        assert "**[order]**" in md


# ---------------------------------------------------------------------------
# Live comparison (local only)
# ---------------------------------------------------------------------------

_WORKBOOK = official.find_workbook(ROOT)
_CLONE = os.path.join(ROOT, official.CLONE_DIRNAME)


@pytest.mark.skipif(
    not (_WORKBOOK and os.path.isdir(os.path.join(_CLONE, "examples_llm"))),
    reason="KIS spec workbook / open-trading-api clone not present (untracked)",
)
def test_no_new_spec_deviations():
    """Fail on any deviation not recorded in scripts/spec_conformance/baseline.json."""
    result = check.run(ROOT, include_coverage=True)
    new = [f"{f.rule} {f.where} {f.url} {f.detail}" for f in result["new_errors"]]
    assert new == [], "\n".join(new)
