"""작은 모듈의 남은 분기 회귀 테스트."""

import pytest

from kis_agent.core.config import KISConfig
from kis_agent.core.constants import WS_REAL_URL, get_ws_url
from kis_agent.core.rate_limiter_mixin import RateLimiterControlMixin
from kis_agent.message_schema import CliMessageValidator
from kis_agent.program.trade import ProgramTradeAPI


def test_config_validation_reports_missing_base_url_on_direct_state():
    config = object.__new__(KISConfig)
    config.APP_KEY = config.APP_SECRET = config.ACCOUNT_NO = config.ACCOUNT_CODE = "set"
    config.BASE_URL = ""
    with pytest.raises(ValueError, match="base_url"):
        config._validate()


def test_real_ws_url_and_invalid_error_response_id():
    assert get_ws_url(True) == WS_REAL_URL
    assert CliMessageValidator.validate_response_error({"id": 1}) == (False, "'id' must be a string or null")


def test_rate_limiter_disabled_warning_and_program_hourly_delegation(caplog):
    mixin = object.__new__(RateLimiterControlMixin)
    mixin.rate_limiter = None
    mixin.enable_adaptive_rate_limiting(False)
    assert "비활성화 상태" in caplog.text

    api = object.__new__(ProgramTradeAPI)
    api.get_program_trade_by_stock = lambda code, ref_date: (code, ref_date)
    assert api.get_program_trade_hourly_trend("005930") == ("005930", None)
