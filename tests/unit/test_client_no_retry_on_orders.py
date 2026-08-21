"""상태 변경 요청(POST)이 재전송되지 않는지 고정하는 회귀 테스트 (STO-1729).

타임아웃은 응답에 걸린 것이지 동작에 걸린 것이 아니다. 접수된 주문의 응답만
유실됐는데 같은 본문을 다시 보내면 중복 주문이 된다. KIS 주문 API는 멱등키를
받지 않으므로 거래소가 걸러줄 방법도 없다.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from kis_agent.core.client import KISClient


@pytest.fixture
def client():
    c = KISClient.__new__(KISClient)
    c.base_url = "https://example.test"
    c.is_real = True
    c.verbose = False
    c.token_expired = None  # 토큰 갱신 경로를 타지 않게 한다
    c._enforce_rate_limit = lambda priority=0: None
    return c


@pytest.fixture(autouse=True)
def stub_env():
    env = MagicMock(my_token="Bearer x", my_app="k", my_sec="s")
    with patch("kis_agent.core.client.getTREnv", return_value=env), patch(
        "kis_agent.core.client.resolve_tr_id", side_effect=lambda tr, real: tr
    ), patch("kis_agent.core.client.time.sleep"):
        yield


def _timeout(*args, **kwargs):
    raise httpx.ConnectTimeout("timed out")


class TestOrderPostIsNeverResent:
    def test_post_timeout_sends_exactly_one_request(self, client):
        with patch("kis_agent.core.client.httpx.request", side_effect=_timeout) as req:
            with pytest.raises(httpx.ConnectTimeout):
                client.make_request(
                    endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                    tr_id="TTTC0012U",
                    params={"PDNO": "005930", "ORD_QTY": "10"},
                    method="POST",
                )
        # 재전송이 한 번이라도 일어나면 중복 주문이다.
        assert req.call_count == 1

    def test_explicit_high_retries_cannot_override_the_rule(self, client):
        with patch("kis_agent.core.client.httpx.request", side_effect=_timeout) as req:
            with pytest.raises(httpx.ConnectTimeout):
                client.make_request(
                    endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                    tr_id="TTTC0012U",
                    params={},
                    method="POST",
                    retries=5,
                )
        assert req.call_count == 1

    def test_http_500_on_post_is_not_resent(self, client):
        response = MagicMock(status_code=500, text='{"msg1": "서버 오류"}')
        response.json.return_value = {"msg1": "서버 오류"}
        with patch("kis_agent.core.client.httpx.request", return_value=response) as req:
            result = client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0052U",
                params={},
                method="POST",
            )
        assert req.call_count == 1
        # 재전송 대신 오류를 그대로 올려보내 상위가 실패로 판정하게 한다.
        assert result is not None

    @pytest.mark.parametrize("method", ["POST", "post", "PUT", "DELETE"])
    def test_every_non_get_method_is_covered(self, client, method):
        with patch("kis_agent.core.client.httpx.request", side_effect=_timeout) as req:
            with pytest.raises(httpx.ConnectTimeout):
                client.make_request(
                    endpoint="/uapi/x", tr_id="T", params={}, method=method
                )
        assert req.call_count == 1


class TestGetStillRetries:
    def test_get_timeout_still_retries(self, client):
        with patch("kis_agent.core.client.httpx.request", side_effect=_timeout) as req:
            with pytest.raises(httpx.ConnectTimeout):
                client.make_request(
                    endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
                    tr_id="FHKST01010100",
                    params={"FID_INPUT_ISCD": "005930"},
                    method="GET",
                )
        # 조회는 멱등하므로 재시도가 유효하다 — 기본 2회.
        assert req.call_count == 2


class TestEveryPostEndpointIsAnOrder:
    def test_no_non_order_post_exists_in_the_package(self):
        """이 규칙의 전제: 패키지의 모든 POST가 주문 계열이다.

        조회용 POST가 새로 생기면 재시도가 사라져 성능이 조용히 나빠지므로,
        그때 이 테스트가 먼저 깨져 규칙을 재검토하게 한다.
        """
        import pathlib
        import re

        root = pathlib.Path(__file__).resolve().parents[2] / "kis_agent"
        offenders = []
        for path in root.rglob("*.py"):
            if re.search(r'method\s*=\s*"POST"', path.read_text(encoding="utf-8")):
                if not path.name.startswith("order_api"):
                    offenders.append(str(path.relative_to(root)))
        assert offenders == [], f"주문이 아닌 POST 발견: {offenders}"


class TestRetriesZeroIsNotATrap:
    """`retries=0`이 주문을 조용히 안 보내는 일이 없어야 한다.

    `> 1`만 걸러내면 0이 그대로 통과해 `range(0)` 루프가 돌지 않고, 주문이
    전송되지 않은 채 "Unknown error after retries"로 끝난다. 호출자는 그것을
    전송 실패와 구분할 수 없다.
    """

    def test_zero_retries_still_sends_the_order_once(self, client):
        with patch("kis_agent.core.client.httpx.request", side_effect=_timeout) as req:
            with pytest.raises(httpx.ConnectTimeout):
                client.make_request(
                    endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                    tr_id="TTTC0012U",
                    params={},
                    method="POST",
                    retries=0,
                )
        assert req.call_count == 1

    def test_one_retry_is_left_alone(self, client):
        with patch("kis_agent.core.client.httpx.request", side_effect=_timeout) as req:
            with pytest.raises(httpx.ConnectTimeout):
                client.make_request(
                    endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                    tr_id="TTTC0012U",
                    params={},
                    method="POST",
                    retries=1,
                )
        assert req.call_count == 1
