"""Shared continuation-query support: response tr_cont, header passthrough, BaseAPI._paginate."""

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import kis_agent.core.client as client_module
from kis_agent.core.base_api import BaseAPI
from kis_agent.core.client import KISClient

FK, NK = "CTX_AREA_FK100", "CTX_AREA_NK100"
CURSOR = [(FK, "ctx_area_fk100"), (NK, "ctx_area_nk100")]


def _request_client():
    client = object.__new__(KISClient)
    client.base_url = "https://example.test"
    client.is_real = True
    client.verbose = False
    client.enable_rate_limiter = False
    client.rate_limiter = None
    client.token_refresh_lock = threading.Lock()
    client._check_and_refresh_token = MagicMock()
    client._enforce_rate_limit = MagicMock()
    return client


def _http_response(payload, headers):
    response = MagicMock(status_code=200, text="ok", headers=headers)
    response.json.return_value = payload
    return response


class TestClientSurfacesTrCont:
    def _send(self, headers):
        env = SimpleNamespace(my_token="token", my_app="app", my_sec="secret")
        with patch.object(client_module, "getTREnv", return_value=env), patch.object(
            client_module.httpx,
            "request",
            return_value=_http_response({"rt_cd": "0"}, headers),
        ) as request:
            result = _request_client().make_request(
                "/test", "TR", {"A": "1"}, headers={"tr_cont": "N"}
            )
        return result, request

    def test_header_value_is_added(self):
        result, request = self._send({"tr_cont": "M"})
        assert result == {"rt_cd": "0", "_tr_cont": "M"}
        assert request.call_args.kwargs["headers"]["tr_cont"] == "N"

    def test_missing_or_non_string_header_is_ignored(self):
        assert self._send({})[0] == {"rt_cd": "0"}
        assert self._send(MagicMock())[0] == {"rt_cd": "0"}


def _api(responses):
    client = MagicMock()
    client.make_request.side_effect = list(responses)
    return BaseAPI(client, enable_cache=True, _from_agent=True), client


def _page(rows, fk="", nk="", tr_cont=None, **extra):
    page = {"rt_cd": "0", "msg1": "ok", "output1": rows, "ctx_area_fk100": fk, "ctx_area_nk100": nk}
    if tr_cont is not None:
        page["_tr_cont"] = tr_cont
    page.update(extra)
    return page


class TestMakeRequestDictHeaders:
    def test_headers_are_forwarded_and_bypass_cache(self):
        api, client = _api([{"rt_cd": "0"}, {"rt_cd": "0"}])
        for _ in range(2):
            api._make_request_dict("/x", "TR", {"A": 1}, headers={"tr_cont": "N"})
        assert client.make_request.call_count == 2
        assert client.make_request.call_args.kwargs["headers"] == {"tr_cont": "N"}

    def test_without_headers_the_call_shape_is_unchanged(self):
        api, client = _api([{"rt_cd": "0"}])
        api._make_request_dict("/x", "TR", {"A": 1})
        client.make_request.assert_called_once_with(
            endpoint="/x", tr_id="TR", params={"A": 1}, method="GET"
        )


class TestPaginate:
    def test_follows_tr_cont_and_merges_lists(self):
        api, client = _api(
            [
                _page([1, 2], "f1", "n1", tr_cont="M", output2={"sum": 1}),
                _page([3], "f2", "n2", tr_cont="D", output2={"sum": 2}),
            ]
        )
        callback = MagicMock()
        out = api._paginate("/x", "TR", {FK: "", NK: "", "Q": "1"}, CURSOR, page_callback=callback)
        assert out["output1"] == [1, 2, 3]
        assert out["output2"] == {"sum": 2}
        assert out["_pagination"] == {"pages": 2, "truncated": False, "error": None}
        assert "_tr_cont" not in out
        first, second = client.make_request.call_args_list
        assert "headers" not in first.kwargs
        assert second.kwargs["headers"] == {"tr_cont": "N"}
        assert second.kwargs["params"] == {FK: "f1", NK: "n1", "Q": "1"}
        assert callback.call_count == 2

    def test_without_header_stops_on_empty_or_repeated_cursor(self):
        api, client = _api([_page([1], "f1", "n1"), _page([2], "f1", "n1")])
        out = api._paginate("/x", "TR", {FK: "", NK: ""}, CURSOR)
        assert out["output1"] == [1, 2]
        assert client.make_request.call_count == 2

        api, client = _api([_page([1])])
        assert api._paginate("/x", "TR", {}, CURSOR)["_pagination"]["pages"] == 1

    def test_first_page_failure_is_returned_as_is(self):
        failure = {"rt_cd": "1", "msg1": "bad"}
        api, _ = _api([failure])
        assert api._paginate("/x", "TR", {}, CURSOR) == failure
        api, _ = _api([None])
        assert api._paginate("/x", "TR", {}, CURSOR) is None

    def test_later_failure_and_page_limit_mark_truncated(self):
        api, _ = _api([_page([1], "f", "n", tr_cont="M"), {"rt_cd": "1", "msg1": "limit"}])
        out = api._paginate("/x", "TR", {}, CURSOR)
        assert out["output1"] == [1]
        assert out["_pagination"] == {"pages": 1, "truncated": True, "error": "limit"}

        api, _ = _api([_page([1], "f", "n", tr_cont="M"), None])
        assert api._paginate("/x", "TR", {}, CURSOR)["_pagination"]["error"] == "no response"

        api, client = _api([_page([1], "f1", "n", tr_cont="F"), _page([2], "f2", "n", tr_cont="M")])
        out = api._paginate("/x", "TR", {}, CURSOR, max_pages=2)
        assert out["_pagination"] == {"pages": 2, "truncated": True, "error": None}

    def test_list_output_first_seen_on_a_later_page(self):
        api, _ = _api([{"rt_cd": "0", "cts": "c1", "_tr_cont": "M"}, {"rt_cd": "0", "output": [9], "cts": ""}])
        out = api._paginate("/x", "TR", {"CTS": ""}, [("CTS", "cts")], output_keys=("output",))
        assert out["output"] == [9]

    def test_rejects_non_positive_page_limit(self):
        api, _ = _api([])
        with pytest.raises(ValueError, match="max_pages"):
            api._paginate("/x", "TR", {}, CURSOR, max_pages=0)
