"""CLI futures --night 옵션 유닛 테스트.

야간선물 시세, 잔고, 체결내역 조회 검증.
"""

import json
from unittest.mock import Mock, patch

import pytest

from kis_agent.cli.main import build_parser


class TestFuturesNightParser:
    """futures --night 파서 테스트."""

    def setup_method(self):
        self.parser = build_parser()

    def test_night_price(self):
        args = self.parser.parse_args(["futures", "101W06", "--night"])
        assert args.night is True
        assert args.code == "101W06"
        assert args.balance is False
        assert args.ccnl is False

    def test_night_balance(self):
        args = self.parser.parse_args(["futures", "101W06", "--night", "--balance"])
        assert args.night is True
        assert args.balance is True

    def test_night_ccnl(self):
        args = self.parser.parse_args(["futures", "101W06", "--night", "--ccnl"])
        assert args.night is True
        assert args.ccnl is True

    def test_night_pretty(self):
        args = self.parser.parse_args(["futures", "101W06", "--night", "--pretty"])
        assert args.pretty is True

    def test_regular_futures_unaffected(self):
        args = self.parser.parse_args(["futures", "101S06"])
        assert args.night is False
        assert args.balance is False
        assert args.ccnl is False


class TestCmdFuturesNightPrice:
    """야간선물 시세 조회 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_night_price_success(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.get_price.return_value = {
            "rt_cd": "0",
            "output": {
                "fuop_prpr": "345.50",
                "prdy_vrss": "2.30",
                "prdy_vrss_sign": "2",
                "prdy_ctrt": "0.67",
                "fuop_oprc": "343.20",
                "fuop_hgpr": "346.00",
                "fuop_lwpr": "342.80",
                "acml_vol": "15234",
                "hts_kor_isnm": "코스피200 야간선물 2606",
            },
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101W06", "--night", "--pretty"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "nightFutures" in result["data"]
        nf = result["data"]["nightFutures"]
        assert nf["code"] == "101W06"
        assert nf["name"] == "코스피200 야간선물 2606"
        assert nf["price"]["currentPrice"] == "345.50"
        assert nf["price"]["change"] == "2.30"

    @patch("kis_agent.cli.main._create_agent")
    def test_night_price_empty(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.get_price.return_value = {
            "rt_cd": "0",
            "output": {},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101W06", "--night"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["nightFutures"]["code"] == "101W06"

    @patch("kis_agent.cli.main._create_agent")
    def test_night_price_error(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.get_price.return_value = {
            "rt_cd": "1",
            "msg1": "종목코드 오류",
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "INVALID", "--night"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "error" in result["data"]["nightFutures"]


class TestCmdFuturesNightBalance:
    """야간선물 잔고 조회 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_night_balance(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.inquire_ngt_balance.return_value = {
            "output": [
                {
                    "fuop_item_code": "101W06",
                    "hts_kor_isnm": "코스피200 야간선물",
                    "ccld_qty": "2",
                    "pchs_avg_pric": "343.20",
                },
            ]
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101W06", "--night", "--balance", "--pretty"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result["data"]["nightFutures"]["balance"]) == 1

    @patch("kis_agent.cli.main._create_agent")
    def test_night_balance_empty(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.inquire_ngt_balance.return_value = None
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101W06", "--night", "--balance"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["nightFutures"]["balance"] == []


class TestCmdFuturesNightCcnl:
    """야간선물 체결내역 조회 테스트."""

    @patch("kis_agent.cli.main._create_agent")
    def test_night_ccnl(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.inquire_ngt_ccnl.return_value = {
            "output": [
                {
                    "ord_dt": "20260325",
                    "ord_tmd": "183012",
                    "fuop_item_code": "101W06",
                    "ccld_qty": "1",
                    "ccld_unpr": "344.50",
                },
            ]
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101W06", "--night", "--ccnl"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result["data"]["nightFutures"]["executions"]) == 1

    @patch("kis_agent.cli.main._create_agent")
    def test_night_ccnl_empty(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.inquire_ngt_ccnl.return_value = {"output": []}
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101W06", "--night", "--ccnl"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["nightFutures"]["executions"] == []


class TestRegularFuturesUnaffected:
    """기존 선물 동작 영향 없음 확인."""

    @patch("kis_agent.cli.main._create_agent")
    def test_regular_futures_still_works(self, mock_create_agent, capsys):
        from kis_agent.cli.main import cmd_futures

        mock_agent = Mock()
        mock_agent.futures_api.get_price.return_value = {
            "rt_cd": "0",
            "output": {
                "fuop_prpr": "345.50",
                "hts_kor_isnm": "코스피200선물 2606",
            },
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["futures", "101S06"])
        cmd_futures(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        # 일반 선물은 "futures" 키 사용 (nightFutures가 아님)
        assert "futures" in result["data"]
        assert "nightFutures" not in result["data"]
