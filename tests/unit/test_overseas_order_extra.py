"""해외 예약 주문의 오류 전파 회귀 테스트."""

from unittest.mock import MagicMock

import pytest

from kis_agent.overseas.order_api import OverseasOrderAPI


def test_reserve_modify_and_cancel_reraise_request_errors():
    api = OverseasOrderAPI(MagicMock(), {"CANO": "1", "ACNT_PRDT_CD": "01"}, _from_agent=True)
    api._make_request_dict = MagicMock(side_effect=RuntimeError("offline"))
    with pytest.raises(RuntimeError, match="offline"):
        api.modify_reserve_order("1", 1, 1.0)
    with pytest.raises(RuntimeError, match="offline"):
        api.cancel_reserve_order("1")
