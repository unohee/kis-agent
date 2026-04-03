"""CLI order 서브커맨드 유닛 테스트.

주문 파서, 확인 프롬프트, 주문 실행 Mock 검증.
"""

import json
from unittest.mock import Mock, patch

import pytest

from kis_agent.cli.field_map import PENDING_ORDER, remap
from kis_agent.cli.main import (
    _DOMESTIC_ORDER_TYPES,
    _OVERSEAS_EXCG_MAP,
    _OVERSEAS_ORDER_TYPES,
    build_parser,
)


# ============================================================
# 주문 타입 매핑
# ============================================================


class TestOrderTypeMappings:
    """주문 타입 코드 매핑 테스트."""

    def test_domestic_limit(self):
        assert _DOMESTIC_ORDER_TYPES["limit"] == "00"

    def test_domestic_market(self):
        assert _DOMESTIC_ORDER_TYPES["market"] == "01"

    def test_domestic_best(self):
        assert _DOMESTIC_ORDER_TYPES["best"] == "03"

    def test_domestic_ioc(self):
        assert _DOMESTIC_ORDER_TYPES["ioc"] == "11"

    def test_domestic_fok(self):
        assert _DOMESTIC_ORDER_TYPES["fok"] == "12"

    def test_overseas_limit(self):
        assert _OVERSEAS_ORDER_TYPES["limit"] == "00"

    def test_overseas_moo(self):
        assert _OVERSEAS_ORDER_TYPES["moo"] == "31"

    def test_overseas_loc(self):
        assert _OVERSEAS_ORDER_TYPES["loc"] == "34"

    def test_excg_map_alias(self):
        assert _OVERSEAS_EXCG_MAP["NAS"] == "NASD"
        assert _OVERSEAS_EXCG_MAP["NYS"] == "NYSE"
        assert _OVERSEAS_EXCG_MAP["HKS"] == "SEHK"

    def test_excg_map_direct(self):
        assert _OVERSEAS_EXCG_MAP["NASD"] == "NASD"
        assert _OVERSEAS_EXCG_MAP["NYSE"] == "NYSE"


# ============================================================
# 파서
# ============================================================


class TestOrderParser:
    """order 서브커맨드 파서 테스트."""

    def setup_method(self):
        self.parser = build_parser()

    def test_buy_basic(self):
        args = self.parser.parse_args(["order", "buy", "005930", "--qty", "10", "--price", "70000"])
        assert args.command == "order"
        assert args.action == "buy"
        assert args.code == "005930"
        assert args.qty == 10
        assert args.price == 70000.0
        assert args.type == "limit"
        assert args.yes is False

    def test_sell_market(self):
        args = self.parser.parse_args(["order", "sell", "005930", "--qty", "5", "--type", "market"])
        assert args.action == "sell"
        assert args.type == "market"
        assert args.price == 0

    def test_buy_overseas(self):
        args = self.parser.parse_args(["order", "buy", "AAPL", "--qty", "5", "--price", "230", "--overseas", "NAS"])
        assert args.overseas == "NAS"
        assert args.code == "AAPL"

    def test_cancel(self):
        args = self.parser.parse_args(["order", "cancel", "0014898200"])
        assert args.action == "cancel"
        assert args.order_no == "0014898200"

    def test_cancel_overseas(self):
        args = self.parser.parse_args(["order", "cancel", "0014898200", "--overseas", "NAS", "--code", "AAPL"])
        assert args.overseas == "NAS"
        assert args.code == "AAPL"

    def test_modify(self):
        args = self.parser.parse_args(["order", "modify", "0014898200", "--price", "72000", "--qty", "5"])
        assert args.action == "modify"
        assert args.price == 72000.0
        assert args.qty == 5

    def test_list(self):
        args = self.parser.parse_args(["order", "list"])
        assert args.action == "list"

    def test_list_overseas(self):
        args = self.parser.parse_args(["order", "list", "--overseas", "NAS"])
        assert args.overseas == "NAS"

    def test_yes_flag(self):
        args = self.parser.parse_args(["order", "buy", "005930", "--qty", "10", "--price", "70000", "--yes"])
        assert args.yes is True

    def test_exchange_option(self):
        args = self.parser.parse_args(["order", "buy", "005930", "--qty", "10", "--price", "70000", "--exchange", "NXT"])
        assert args.exchange == "NXT"

    def test_all_order_types(self):
        for t in ["limit", "market", "best", "ioc", "fok", "pre", "after"]:
            args = self.parser.parse_args(["order", "buy", "005930", "--qty", "1", "--type", t])
            assert args.type == t


# ============================================================
# 필드 매핑
# ============================================================


class TestPendingOrderFieldMap:
    """미체결 주문 필드 매핑 테스트."""

    def test_pending_order_remap(self):
        raw = {
            "ord_dt": "20260325",
            "ord_tmd": "143025",
            "odno": "0014898200",
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "sll_buy_dvsn_cd_name": "매수",
            "ord_dvsn_name": "지정가",
            "ord_qty": "10",
            "ord_unpr": "70000",
            "tot_ccld_qty": "0",
            "rmn_qty": "10",
        }
        mapped = remap(raw, PENDING_ORDER)
        assert mapped["orderNo"] == "0014898200"
        assert mapped["code"] == "005930"
        assert mapped["name"] == "삼성전자"
        assert mapped["side"] == "매수"
        assert mapped["remainQty"] == "10"


# ============================================================
# cmd_order 핸들러 (Mock 기반)
# ============================================================


class TestCmdOrderList:
    """order list 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_list_domestic(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.account_api.inquire_psbl_rvsecncl.return_value = {
            "output": [
                {
                    "ord_dt": "20260325",
                    "ord_tmd": "100000",
                    "odno": "0001234",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "sll_buy_dvsn_cd_name": "매수",
                    "ord_dvsn_name": "지정가",
                    "ord_qty": "10",
                    "ord_unpr": "70000",
                    "tot_ccld_qty": "0",
                    "rmn_qty": "10",
                },
            ]
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "list", "--pretty"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["orders"]["count"] == 1
        assert result["data"]["orders"]["items"][0]["orderNo"] == "0001234"

    @patch("kis_agent.cli.main._create_agent")
    def test_list_empty(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.account_api.inquire_psbl_rvsecncl.return_value = {"output": []}
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "list"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["orders"]["count"] == 0


class TestCmdOrderBuy:
    """order buy 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_buy_domestic_with_yes(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.stock_api.search_stock_info.return_value = {
            "output": {"prdt_abrv_name": "삼성전자"}
        }
        mock_agent.account_api.order_cash.return_value = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"odno": "0001234", "ord_tmd": "143025"},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "buy", "005930", "--qty", "10", "--price", "70000", "--yes"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["order"]["status"] == "accepted"
        assert result["data"]["order"]["orderNo"] == "0001234"
        assert result["data"]["order"]["side"] == "매수"

        # API 호출 검증
        mock_agent.account_api.order_cash.assert_called_once_with(
            pdno="005930", qty=10, price=70000.0,
            buy_sell="BUY", order_type="00", exchange="KRX",
        )

    @patch("kis_agent.cli.main._create_agent")
    def test_sell_market_with_yes(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.stock_api.search_stock_info.return_value = {
            "output": {"prdt_abrv_name": "삼성전자"}
        }
        mock_agent.account_api.order_cash.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0005678", "ord_tmd": "100000"},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "sell", "005930", "--qty", "5", "--type", "market", "--yes"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["order"]["side"] == "매도"

        # 시장가이므로 price=0
        call_kwargs = mock_agent.account_api.order_cash.call_args
        assert call_kwargs[1]["price"] == 0
        assert call_kwargs[1]["order_type"] == "01"

    @patch("kis_agent.cli.main._create_agent")
    def test_buy_overseas_with_yes(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.overseas_api.buy_order.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0009999", "ord_tmd": "230000"},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args([
            "order", "buy", "AAPL", "--qty", "5", "--price", "230",
            "--overseas", "NAS", "--yes",
        ])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["order"]["status"] == "accepted"
        assert result["data"]["order"]["exchange"] == "NASD"

        mock_agent.overseas_api.buy_order.assert_called_once_with(
            ovrs_excg_cd="NASD", pdno="AAPL", qty=5,
            price=230.0, ord_dvsn="00",
        )

    @patch("kis_agent.cli.main._create_agent")
    def test_overseas_moo_buy_rejected(self, mock_create_agent, capsys):
        """MOO 매수는 불가능."""
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args([
            "order", "buy", "AAPL", "--qty", "5", "--price", "0",
            "--overseas", "NAS", "--type", "moo", "--yes",
        ])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "error" in result
        assert "매도만" in result["error"]


class TestCmdOrderCancel:
    """order cancel 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_cancel_domestic_with_yes(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.account_api.order_rvsecncl.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0007777"},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "cancel", "0014898200", "--yes"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["cancel"]["status"] == "accepted"
        assert result["data"]["cancel"]["origOrderNo"] == "0014898200"


class TestCmdOrderModify:
    """order modify 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_modify_domestic_with_yes(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.account_api.order_rvsecncl.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0008888"},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "modify", "0014898200", "--price", "72000", "--qty", "5", "--yes"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["modify"]["status"] == "accepted"

        mock_agent.account_api.order_rvsecncl.assert_called_once_with(
            org_order_no="0014898200",
            qty=5, price=72000.0,
            order_type="00", cncl_type="정정",
        )


class TestCmdOrderConfirm:
    """확인 프롬프트 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    @patch("builtins.input", return_value="n")
    def test_buy_rejected_without_yes(self, mock_input, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.stock_api.search_stock_info.return_value = {
            "output": {"prdt_abrv_name": "삼성전자"}
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "buy", "005930", "--qty", "10", "--price", "70000"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["cancelled"] is True

        # API 호출이 없어야 함
        mock_agent.account_api.order_cash.assert_not_called()

    @patch("kis_agent.cli.main._create_agent")
    @patch("builtins.input", return_value="y")
    def test_buy_confirmed(self, mock_input, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_order

        mock_agent = Mock()
        mock_agent.stock_api.search_stock_info.return_value = {
            "output": {"prdt_abrv_name": "삼성전자"}
        }
        mock_agent.account_api.order_cash.return_value = {
            "rt_cd": "0",
            "output": {"odno": "0001111", "ord_tmd": "100000"},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["order", "buy", "005930", "--qty", "10", "--price", "70000"])
        cmd_order(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["order"]["status"] == "accepted"
        mock_agent.account_api.order_cash.assert_called_once()
