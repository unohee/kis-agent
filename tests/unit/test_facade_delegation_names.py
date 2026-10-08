"""Dynamic delegation must never resolve a name ambiguously.

StockAPI, AccountAPI, ElwAPI, BondAPI and Agent resolve unknown attributes by
walking a chain of sub-APIs; the first one that has the name wins. If two
sub-APIs in the same chain define the same public method, the later one is
silently unreachable. A name may appear in several sub-APIs only when the
facade defines it explicitly (the facade method wins and picks the target).
"""

import collections
import inspect

import pytest

from kis_agent.account.api import AccountAPI
from kis_agent.account.balance_query_api import AccountBalanceQueryAPI
from kis_agent.account.order_api import AccountOrderAPI
from kis_agent.account.pension_api import AccountPensionAPI
from kis_agent.account.profit_api import AccountProfitAPI
from kis_agent.bond import BondAPI, BondOrderAPI, BondPriceAPI
from kis_agent.core.agent import Agent
from kis_agent.core.base_api import BaseAPI
from kis_agent.elw import ElwAPI, ElwPriceAPI, ElwRankingAPI
from kis_agent.program.trade import ProgramTradeAPI
from kis_agent.stock import (
    StockAnalysisAPI,
    StockAPI,
    StockChartAPI,
    StockEtfAPI,
    StockFinanceAPI,
    StockInvestorAPI,
    StockKsdInfoAPI,
    StockMarketAPI,
    StockPriceAPI,
    StockRankingAPI,
)
from kis_agent.stock.interest import InterestStockAPI

_BASE = set(dir(BaseAPI))


def _public(cls):
    return {
        name
        for name, _ in inspect.getmembers(cls, inspect.isfunction)
        if not name.startswith("_") and name not in _BASE
    }


STOCK_CHAIN = [
    StockPriceAPI,
    StockMarketAPI,
    StockInvestorAPI,
    StockRankingAPI,
    StockAnalysisAPI,
    StockFinanceAPI,
    StockKsdInfoAPI,
    StockEtfAPI,
    StockChartAPI,
]
ACCOUNT_CHAIN = [AccountBalanceQueryAPI, AccountOrderAPI, AccountProfitAPI, AccountPensionAPI]


def _collisions(chain, facade):
    owners = collections.defaultdict(list)
    for cls in chain:
        for name in _public(cls):
            owners[name].append(cls.__name__)
    explicit = _public(facade)
    return {n: o for n, o in owners.items() if len(o) > 1 and n not in explicit}


@pytest.mark.parametrize(
    "facade,chain",
    [
        (StockAPI, STOCK_CHAIN),
        (AccountAPI, ACCOUNT_CHAIN),
        (ElwAPI, [ElwPriceAPI, ElwRankingAPI]),
        (BondAPI, [BondPriceAPI, BondOrderAPI]),
    ],
    ids=["stock", "account", "elw", "bond"],
)
def test_no_ambiguous_names_within_a_facade(facade, chain):
    assert _collisions(chain, facade) == {}


def test_no_ambiguous_names_across_the_agent_chain():
    groups = {
        "stock": set().union(_public(StockAPI), *(_public(c) for c in STOCK_CHAIN)),
        "account": set().union(_public(AccountAPI), *(_public(c) for c in ACCOUNT_CHAIN)),
        "program": _public(ProgramTradeAPI),
        "interest": _public(InterestStockAPI),
    }
    owners = collections.defaultdict(list)
    for group, names in groups.items():
        for name in names:
            owners[name].append(group)
    explicit = _public(Agent)
    assert {n: g for n, g in owners.items() if len(g) > 1 and n not in explicit} == {}


def test_new_sub_apis_are_reachable_through_their_facades():
    from unittest.mock import MagicMock

    stock = StockAPI(MagicMock(), _from_agent=True)
    assert [type(a).__name__ for a in stock._delegates()] == [c.__name__ for c in STOCK_CHAIN]
    with pytest.raises(AttributeError):
        _ = stock.not_a_method

    account = AccountAPI(MagicMock(), {"CANO": "1", "ACNT_PRDT_CD": "01"}, _from_agent=True)
    account._pension_api.probe = lambda: "pension"
    assert account.probe() == "pension"

    for facade, subs in ((ElwAPI, ("price_api", "ranking_api")), (BondAPI, ("price_api", "order_api"))):
        api = facade(MagicMock(), _from_agent=True)
        getattr(api, subs[1]).probe = lambda: "second"
        assert api.probe() == "second"
        with pytest.raises(AttributeError):
            _ = api._private
        with pytest.raises(AttributeError):
            _ = api.not_a_method


def test_agent_exposes_elw_and_bond():
    agent = object.__new__(Agent)
    agent.elw_api = "elw"
    agent.bond_api = "bond"
    assert (agent.elw, agent.bond) == ("elw", "bond")
