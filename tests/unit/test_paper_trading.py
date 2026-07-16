"""Paper trading (모의투자) support tests.

Regression coverage for GitHub issue #44: pointing `base_url` at the paper host
still sent real-trading TR_IDs, so every call came back with HTTP 500
``모의투자 TR 이 아닙니다``.
"""

import os
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig
from kis_agent.core.constants import (
    MOCK_BASE_URL,
    REAL_BASE_URL,
    paper_from_env,
    resolve_environment,
)
from kis_agent.core.tr_mapping import (
    REAL_TO_PAPER_TR,
    PaperTradingNotSupportedError,
    is_paper_supported,
    resolve_tr_id,
)


@pytest.fixture
def clean_env(monkeypatch):
    """Isolate tests from the developer's own KIS_* environment."""
    for key in ("KIS_PAPER", "KIS_BASE_URL"):
        monkeypatch.delenv(key, raising=False)


class TestResolveTrId:
    """TR_ID 실전 -> 모의 변환."""

    def test_real_trading_passes_through_unchanged(self):
        assert resolve_tr_id("TTTC8434R", is_real=True) == "TTTC8434R"

    def test_real_trading_allows_paper_unsupported_tr(self):
        # 실전에서는 모의 미지원 API도 당연히 호출 가능해야 한다.
        assert resolve_tr_id("OTFM3116R", is_real=True) == "OTFM3116R"

    @pytest.mark.parametrize(
        "real,paper",
        [
            ("TTTC8434R", "VTTC8434R"),  # 주식잔고조회 — 이슈 #44 신고 경로
            ("TTTC0012U", "VTTC0012U"),  # 주식주문(현금) 매수
            ("TTTC0011U", "VTTC0011U"),  # 주식주문(현금) 매도
            ("CTSC9215R", "VTSC9215R"),  # 첫 글자 C -> V
            ("CTFO6118R", "VTFO6118R"),  # 선물옵션 잔고현황
            ("TTTS3012R", "VTTS3012R"),  # 해외주식 잔고
            ("TTTT1002U", "VTTT1002U"),  # 해외주식 미국 매수
        ],
    )
    def test_maps_real_to_paper(self, real, paper):
        assert resolve_tr_id(real, is_real=False) == paper

    def test_us_sell_order_changes_digits_too(self):
        """TTTT1006U -> VTTT1001U: 첫 글자 외에 번호까지 바뀌는 유일한 예외.

        공식 문서 'API 목록' row249 및 '해외주식 주문' 시트 row7/row22 기준.
        단순 'V' + real[1:] 치환 규칙으로는 잡을 수 없다.
        """
        assert resolve_tr_id("TTTT1006U", is_real=False) == "VTTT1001U"
        assert "VTTT1006U" not in REAL_TO_PAPER_TR.values()

    @pytest.mark.parametrize(
        "tr_id", ["FHKST01010100", "FHKST03010100", "HHDFS00000300", "H0STCNT0"]
    )
    def test_quote_tr_ids_are_identical_on_both_environments(self, tr_id):
        assert resolve_tr_id(tr_id, is_real=False) == tr_id

    @pytest.mark.parametrize(
        "real,paper",
        [("H0STCNI0", "H0STCNI9"), ("H0IFCNI0", "H0IFCNI9"), ("H0GSCNI0", "H0GSCNI9")],
    )
    def test_websocket_notice_swaps_last_digit_not_first_letter(self, real, paper):
        assert resolve_tr_id(real, is_real=False) == paper

    def test_already_resolved_paper_tr_passes_through(self):
        assert resolve_tr_id("VTTC8434R", is_real=False) == "VTTC8434R"

    def test_unsupported_tr_raises_on_paper(self):
        with pytest.raises(PaperTradingNotSupportedError) as exc:
            resolve_tr_id("OTFM3116R", is_real=False)
        assert exc.value.tr_id == "OTFM3116R"
        assert "모의투자를 지원하지 않습니다" in str(exc.value)

    @pytest.mark.parametrize(
        "tr_id",
        [
            "OTFM3116R",  # 해외선물옵션 — 전량 모의 미지원
            "TTTS3018R",  # 해외주식 미체결내역 — 공식 문서상 모의 미지원
            "CTRP6548R",  # 투자계좌자산현황조회
            "TTTC8408R",  # 매도가능수량조회
        ],
    )
    def test_documented_unsupported_apis_are_not_mapped(self, tr_id):
        assert not is_paper_supported(tr_id)

    def test_mapping_table_has_no_self_contradiction(self):
        """모의 TR_ID가 다른 실전 TR_ID의 키와 겹치면 이중 변환이 깨진다."""
        overlap = set(REAL_TO_PAPER_TR.values()) & set(REAL_TO_PAPER_TR)
        # 실전=모의인 시세 TR만 양쪽에 나타나야 한다.
        assert all(REAL_TO_PAPER_TR[tr] == tr for tr in overlap)


class TestMappingProvenance:
    """매핑이 공식 문서와 일치하는지 (자기참조 검증 방지).

    워크북은 용량 때문에 git에 추적하지 않으므로, 있으면 검사하고 없으면 skip.
    로컬/릴리즈 전에는 저장소 루트에 워크북을 두고 돌릴 것.
    """

    def test_mapping_matches_official_workbook(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
        try:
            from extract_paper_tr_mapping import extract, find_workbook
        finally:
            sys.path.pop(0)

        pytest.importorskip("openpyxl", reason="openpyxl 없이는 워크북을 읽을 수 없다")
        workbook = find_workbook(str(Path(__file__).resolve().parents[2]))
        if not workbook:
            pytest.skip("KIS 공식 API 워크북이 저장소에 없음 (git 미추적)")

        documented = extract(workbook)
        assert documented, "워크북에서 매핑을 하나도 추출하지 못했다"

        wrong = {
            real: (paper, REAL_TO_PAPER_TR[real])
            for real, paper in documented.items()
            if real in REAL_TO_PAPER_TR and REAL_TO_PAPER_TR[real] != paper
        }
        missing = {r: p for r, p in documented.items() if r not in REAL_TO_PAPER_TR}
        assert not wrong, f"공식 문서와 불일치: {wrong}"
        assert not missing, f"공식 문서에 있으나 매핑 누락: {missing}"

    def test_no_paper_supported_api_is_wrongly_rejected(self):
        """코드베이스가 쓰는 TR 중, 모의 지원인데 우리가 거절하는 것이 없어야 한다.

        make_request가 미매핑 TR을 예외로 막으므로, 매핑 누락은 곧 "KIS는
        제공하는데 우리 라이브러리가 막는" 기능 손실이 된다.
        """
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
        try:
            from extract_paper_tr_mapping import extract, find_workbook
        finally:
            sys.path.pop(0)

        pytest.importorskip("openpyxl")
        root = Path(__file__).resolve().parents[2]
        workbook = find_workbook(str(root))
        if not workbook:
            pytest.skip("KIS 공식 API 워크북이 저장소에 없음 (git 미추적)")

        # 코드베이스가 실제로 전송하는 TR_ID 수집
        pattern = re.compile(r'tr_id\s*=\s*"([A-Z0-9]{6,13})"')
        used = set()
        for path in (root / "kis_agent").rglob("*.py"):
            used |= set(pattern.findall(path.read_text(errors="ignore")))
        assert used, "TR_ID를 하나도 수집하지 못했다 (수집 로직 확인 필요)"

        documented = extract(workbook)
        gap = {
            tr: documented[tr]
            for tr in used
            if tr in documented and tr not in REAL_TO_PAPER_TR
        }
        assert not gap, f"모의 지원인데 매핑 누락으로 거절될 TR: {gap}"


class TestResolveEnvironment:
    """paper / KIS_PAPER / base_url 로부터 환경 결정."""

    def test_defaults_to_real_trading(self, clean_env):
        assert resolve_environment() == (REAL_BASE_URL, True)

    def test_paper_true_selects_mock_url(self, clean_env):
        assert resolve_environment(paper=True) == (MOCK_BASE_URL, False)

    def test_paper_false_selects_real_url(self, clean_env):
        assert resolve_environment(paper=False) == (REAL_BASE_URL, True)

    def test_infers_paper_from_mock_base_url(self, clean_env):
        """이슈 #44 시나리오: base_url만 모의로 준 경우."""
        assert resolve_environment(base_url=MOCK_BASE_URL) == (MOCK_BASE_URL, False)

    def test_kis_base_url_env_is_honored(self, clean_env, monkeypatch):
        monkeypatch.setenv("KIS_BASE_URL", MOCK_BASE_URL)
        assert resolve_environment() == (MOCK_BASE_URL, False)

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
    def test_kis_paper_truthy_values(self, clean_env, monkeypatch, value):
        monkeypatch.setenv("KIS_PAPER", value)
        assert resolve_environment() == (MOCK_BASE_URL, False)

    @pytest.mark.parametrize("value", ["0", "false", "no", "off"])
    def test_kis_paper_falsy_values(self, clean_env, monkeypatch, value):
        monkeypatch.setenv("KIS_PAPER", value)
        assert resolve_environment() == (REAL_BASE_URL, True)

    def test_explicit_paper_overrides_env(self, clean_env, monkeypatch):
        monkeypatch.setenv("KIS_PAPER", "0")
        assert resolve_environment(paper=True) == (MOCK_BASE_URL, False)

    def test_unset_kis_paper_returns_none(self, clean_env):
        assert paper_from_env() is None

    def test_invalid_kis_paper_raises(self, clean_env, monkeypatch):
        # 오타를 실전으로 조용히 해석하면 실제 주문이 나갈 수 있다.
        monkeypatch.setenv("KIS_PAPER", "maybe")
        with pytest.raises(ValueError, match="KIS_PAPER"):
            resolve_environment()

    def test_contradicting_paper_and_base_url_raises(self, clean_env):
        with pytest.raises(ValueError, match="모순"):
            resolve_environment(base_url=REAL_BASE_URL, paper=True)
        with pytest.raises(ValueError, match="모순"):
            resolve_environment(base_url=MOCK_BASE_URL, paper=False)


class TestKisPaperHonoredEverywhere:
    """KIS_PAPER=1 만 설정한 경우 모든 진입점이 모의투자를 선택해야 한다.

    KIS_BASE_URL만 읽던 경로가 KIS_PAPER를 조용히 무시하면, README가 약속한
    동작이 그 경로에서 거짓이 된다.
    """

    def test_config_from_env_honors_kis_paper(self, clean_env, monkeypatch):
        monkeypatch.setenv("KIS_PAPER", "1")
        monkeypatch.setenv("KIS_APP_KEY", "k")
        monkeypatch.setenv("KIS_APP_SECRET", "s")
        monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")

        config = KISConfig.from_env()
        assert config.BASE_URL == MOCK_BASE_URL
        assert config.is_real is False

    def test_client_from_env_honors_kis_paper(self, clean_env, monkeypatch):
        monkeypatch.setenv("KIS_PAPER", "1")
        monkeypatch.setenv("KIS_APP_KEY", "k")
        monkeypatch.setenv("KIS_APP_SECRET", "s")
        monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")

        with patch.object(KISClient, "_initialize_token", lambda self: None):
            client = KISClient(enable_rate_limiter=False)
        assert client.base_url == MOCK_BASE_URL
        assert client.is_real is False

    def test_agent_honors_kis_paper(self, clean_env, monkeypatch):
        from kis_agent.core.agent import Agent

        monkeypatch.setenv("KIS_PAPER", "1")
        with patch.object(KISClient, "_initialize_token", lambda self: None), patch.object(
            Agent, "_preload_masters", lambda self: None
        ):
            agent = Agent(
                app_key="k",
                app_secret="s",
                account_no="12345678",
                account_code="01",
                enable_rate_limiter=False,
            )
        assert agent.is_real is False
        assert agent.client.base_url == MOCK_BASE_URL


class TestClientSendsPaperTrId:
    """client.make_request가 실제로 모의 TR_ID를 전송하는지 (이슈 #44 회귀)."""

    @pytest.fixture
    def sent(self):
        return {}

    @pytest.fixture
    def client(self, sent):
        def fake_request(method, url, **kwargs):
            sent["url"] = url
            sent["tr_id"] = kwargs["headers"]["tr_id"]
            response = MagicMock(status_code=200)
            response.json.return_value = {"rt_cd": "0", "output": {}}
            return response

        config = KISConfig(
            app_key="k",
            app_secret="s",
            base_url=MOCK_BASE_URL,
            account_no="12345678",
            account_code="01",
        )
        env = MagicMock(my_token="t", my_app="k", my_sec="s")
        with patch.object(KISClient, "_initialize_token", lambda self: None), patch(
            "kis_agent.core.client.getTREnv", return_value=env
        ), patch("kis_agent.core.client.httpx.request", side_effect=fake_request):
            client = KISClient(config=config, enable_rate_limiter=False)
            client.base_url = MOCK_BASE_URL
            client.is_real = False
            yield client

    def test_balance_query_sends_paper_tr_to_paper_host(self, client, sent):
        client.make_request(
            "/uapi/domestic-stock/v1/trading/inquire-balance", "TTTC8434R", {}
        )
        assert sent["tr_id"] == "VTTC8434R"
        assert sent["url"].startswith(MOCK_BASE_URL)

    def test_order_sends_paper_tr(self, client, sent):
        client.make_request(
            "/uapi/domestic-stock/v1/trading/order-cash", "TTTC0012U", {}, method="POST"
        )
        assert sent["tr_id"] == "VTTC0012U"

    def test_unsupported_api_fails_without_network_round_trip(self, client, sent):
        with pytest.raises(PaperTradingNotSupportedError):
            client.make_request("/uapi/overseas-futureoption/v1/x", "OTFM3116R", {})
        assert not sent, "요청이 전송되면 안 된다 (재시도 소진 후 500을 받게 됨)"

    def test_real_client_keeps_real_tr(self, client, sent):
        client.is_real = True
        client.make_request(
            "/uapi/domestic-stock/v1/trading/inquire-balance", "TTTC8434R", {}
        )
        assert sent["tr_id"] == "TTTC8434R"

    def test_exception_type_survives_the_api_layer(self, client):
        """API 계층의 예외 핸들러가 APIException으로 감싸면 안 된다.

        감싸버리면 호출부가 "모의 미지원"과 실제 API 오류를 구분할 수 없고,
        README가 약속한 타입도 거짓이 된다.
        """
        import warnings

        from kis_agent.overseas.account_api import OverseasAccountAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            api = OverseasAccountAPI(client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"})

        with pytest.raises(PaperTradingNotSupportedError) as exc:
            api.get_unfilled_orders()  # TTTS3018R — 모의 미지원
        assert exc.value.tr_id == "TTTS3018R"

    def test_holiday_check_degrades_quietly_on_paper(self, client):
        """휴장일 조회는 모의 미지원 — CLI 기동을 깨지 말고 None으로 폴백해야 한다."""
        import warnings

        from kis_agent.stock.market_api import StockMarketAPI

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            api = StockMarketAPI(client)

        assert api.get_holiday_info("20260716") is None


class TestWebSocketPaperTrId:
    """WSAgent 구독 시 체결통보 TR_ID 변환."""

    def _agent(self, url):
        from kis_agent.core.constants import WS_MOCK_URL, WS_REAL_URL
        from kis_agent.websocket import WSAgent

        return WSAgent(approval_key="key", url=url)

    def test_paper_ws_url_marks_agent_as_paper(self):
        from kis_agent.core.constants import WS_MOCK_URL, WS_REAL_URL

        assert self._agent(WS_REAL_URL).is_real is True
        assert self._agent(WS_MOCK_URL).is_real is False

    def test_notice_subscription_uses_paper_tr_on_paper_ws(self):
        from kis_agent.core.constants import WS_MOCK_URL
        from kis_agent.websocket import SubscriptionType

        agent = self._agent(WS_MOCK_URL)
        sub_id = agent.subscribe(SubscriptionType.STOCK_NOTICE, "12345678")
        assert sub_id == "H0STCNI9_12345678"
        assert agent.subscriptions[sub_id].sub_type.value == "H0STCNI9"

    def test_notice_subscription_keeps_real_tr_on_real_ws(self):
        from kis_agent.core.constants import WS_REAL_URL
        from kis_agent.websocket import SubscriptionType

        agent = self._agent(WS_REAL_URL)
        assert agent.subscribe(SubscriptionType.STOCK_NOTICE, "12345678").startswith(
            "H0STCNI0"
        )

    def test_quote_subscription_unchanged_on_paper_ws(self):
        from kis_agent.core.constants import WS_MOCK_URL
        from kis_agent.websocket import SubscriptionType

        agent = self._agent(WS_MOCK_URL)
        assert agent.subscribe(SubscriptionType.STOCK_TRADE, "005930") == (
            "H0STCNT0_005930"
        )

    def test_paper_notice_alias_is_backward_compatible(self):
        """STOCK_NOTICE_AH는 오라벨이었지만 기존 코드가 깨지면 안 된다."""
        from kis_agent.websocket import SubscriptionType

        assert SubscriptionType.STOCK_NOTICE_AH.value == "H0STCNI9"
        assert SubscriptionType.STOCK_NOTICE_PAPER is SubscriptionType.STOCK_NOTICE_AH
