"""CLI trades 서브커맨드 유닛 테스트.

거래내역 조회, 날짜 파싱, 필드 매핑, 포맷팅 검증.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from kis_agent.cli.field_map import (
    DAILY_PROFIT,
    PERIOD_PROFIT,
    TRADE_EXECUTION,
    TRADE_SUMMARY,
    remap,
)
from kis_agent.cli.main import (
    _fmt_date,
    _fmt_number,
    _fmt_time,
    _parse_date,
    build_parser,
)


# ============================================================
# 날짜 파싱
# ============================================================


class TestParseDate:
    """_parse_date 함수 테스트."""

    def test_today(self):
        result = _parse_date("today")
        assert result == datetime.now().strftime("%Y%m%d")

    def test_empty_string(self):
        result = _parse_date("")
        assert result == datetime.now().strftime("%Y%m%d")

    def test_relative_days(self):
        result = _parse_date("7d")
        expected = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        assert result == expected

    def test_relative_days_with_dash(self):
        """이전 -7d 형식도 동일하게 동작."""
        result = _parse_date("-7d")
        expected = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        assert result == expected

    def test_relative_months(self):
        result = _parse_date("3m")
        expected = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        assert result == expected

    def test_relative_years(self):
        result = _parse_date("1y")
        expected = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        assert result == expected

    def test_absolute_date_with_dashes(self):
        assert _parse_date("2026-03-01") == "20260301"

    def test_absolute_date_plain(self):
        assert _parse_date("20260301") == "20260301"

    def test_absolute_date_with_dots(self):
        assert _parse_date("2026.03.01") == "20260301"

    def test_absolute_date_with_slashes(self):
        assert _parse_date("2026/03/01") == "20260301"


# ============================================================
# 포맷터
# ============================================================


class TestFormatters:
    """포맷팅 함수 테스트."""

    def test_fmt_date(self):
        assert _fmt_date("20260325") == "2026-03-25"

    def test_fmt_date_short(self):
        assert _fmt_date("abc") == "abc"

    def test_fmt_time(self):
        assert _fmt_time("143025") == "14:30:25"

    def test_fmt_time_short(self):
        assert _fmt_time("14") == "14"

    def test_fmt_number_int(self):
        assert _fmt_number("1234567") == "1,234,567"

    def test_fmt_number_float(self):
        assert _fmt_number("70123.45") == "70,123.45"

    def test_fmt_number_whole_float(self):
        """소수점 .00은 정수로 표시."""
        assert _fmt_number("50000.00") == "50,000"

    def test_fmt_number_zero(self):
        assert _fmt_number("0") == "0"

    def test_fmt_number_empty(self):
        assert _fmt_number("") == "0"

    def test_fmt_number_invalid(self):
        assert _fmt_number("abc") == "abc"


# ============================================================
# 필드 매핑
# ============================================================


class TestFieldMaps:
    """거래내역 필드 매핑 테스트."""

    def test_trade_execution_remap(self):
        raw = {
            "ord_dt": "20260325",
            "ord_tmd": "143025",
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "sll_buy_dvsn_cd_name": "매수",
            "ord_dvsn_name": "지정가",
            "ord_qty": "10",
            "ord_unpr": "70000",
            "tot_ccld_qty": "10",
            "avg_prvs": "70000",
            "tot_ccld_amt": "700000",
            "rmn_qty": "0",
            "cncl_yn": "N",
            "odno": "0001234",
        }
        mapped = remap(raw, TRADE_EXECUTION)
        assert mapped["date"] == "20260325"
        assert mapped["code"] == "005930"
        assert mapped["name"] == "삼성전자"
        assert mapped["side"] == "매수"
        assert mapped["filledQty"] == "10"
        assert mapped["avgPrice"] == "70000"

    def test_trade_summary_remap(self):
        raw = {
            "tot_ord_qty": "100",
            "tot_ccld_qty": "80",
            "tot_ccld_amt": "5600000",
            "prsm_tlex_smtl": "1500",
        }
        mapped = remap(raw, TRADE_SUMMARY)
        assert mapped["totalOrderQty"] == "100"
        assert mapped["totalFilledQty"] == "80"
        assert mapped["totalFilledAmount"] == "5600000"
        assert mapped["totalFees"] == "1500"

    def test_period_profit_remap(self):
        raw = {
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "sll_buy_dvsn_cd_name": "매도",
            "buy_qty": "10",
            "buy_amt": "700000",
            "sll_qty": "10",
            "sll_amt": "750000",
            "rlzt_pfls": "50000",
            "rlzt_erng_rt": "7.14",
        }
        mapped = remap(raw, PERIOD_PROFIT)
        assert mapped["code"] == "005930"
        assert mapped["realizedPL"] == "50000"
        assert mapped["realizedPLRate"] == "7.14"

    def test_daily_profit_remap(self):
        raw = {
            "bsop_dt": "20260325",
            "rlzt_pfls": "150000",
            "rlzt_erng_rt": "3.5",
            "sll_amt": "5000000",
            "buy_amt": "4850000",
        }
        mapped = remap(raw, DAILY_PROFIT)
        assert mapped["date"] == "20260325"
        assert mapped["realizedPL"] == "150000"


# ============================================================
# CLI 파서
# ============================================================


class TestTradesParser:
    """trades 서브커맨드 파서 테스트."""

    def setup_method(self):
        self.parser = build_parser()

    def test_default_args(self):
        args = self.parser.parse_args(["trades"])
        assert args.command == "trades"
        assert args.start == "today"
        assert args.end == ""
        assert args.buy is False
        assert args.sell is False
        assert args.stock == ""
        assert args.filled is False
        assert args.limit == 0
        assert args.profit is False
        assert args.daily_profit is False
        assert args.pretty is False

    def test_date_range(self):
        args = self.parser.parse_args(["trades", "--from", "30d", "--to", "2026-03-25"])
        assert args.start == "30d"
        assert args.end == "2026-03-25"

    def test_buy_filter(self):
        args = self.parser.parse_args(["trades", "--buy"])
        assert args.buy is True

    def test_sell_filter(self):
        args = self.parser.parse_args(["trades", "--sell"])
        assert args.sell is True

    def test_stock_filter(self):
        args = self.parser.parse_args(["trades", "--stock", "005930"])
        assert args.stock == "005930"

    def test_filled_only(self):
        args = self.parser.parse_args(["trades", "--filled"])
        assert args.filled is True

    def test_limit(self):
        args = self.parser.parse_args(["trades", "--limit", "50"])
        assert args.limit == 50

    def test_profit_mode(self):
        args = self.parser.parse_args(["trades", "--profit"])
        assert args.profit is True

    def test_daily_profit_mode(self):
        args = self.parser.parse_args(["trades", "--profit", "--daily-profit"])
        assert args.profit is True
        assert args.daily_profit is True

    def test_pretty(self):
        args = self.parser.parse_args(["trades", "--pretty"])
        assert args.pretty is True

    def test_combined_flags(self):
        args = self.parser.parse_args([
            "trades", "--from", "7d", "--sell",
            "--stock", "005930", "--filled", "--limit", "10", "--pretty",
        ])
        assert args.start == "7d"
        assert args.sell is True
        assert args.stock == "005930"
        assert args.filled is True
        assert args.limit == 10
        assert args.pretty is True


# ============================================================
# cmd_trades 함수 (Mock 기반)
# ============================================================


class TestCmdTrades:
    """cmd_trades 핸들러 테스트."""

    def _make_ccld_response(self, items=None):
        """체결조회 응답 Mock 생성."""
        if items is None:
            items = [
                {
                    "ord_dt": "20260325",
                    "ord_tmd": "093012",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "sll_buy_dvsn_cd_name": "매수",
                    "ord_dvsn_name": "지정가",
                    "ord_qty": "10",
                    "ord_unpr": "70000",
                    "tot_ccld_qty": "10",
                    "avg_prvs": "70000",
                    "tot_ccld_amt": "700000",
                    "rmn_qty": "0",
                    "cncl_yn": "N",
                    "odno": "0001234",
                    "orgn_odno": "0001234",
                },
            ]
        return {
            "rt_cd": "0",
            "msg1": "정상처리",
            "output1": items,
            "output2": {
                "tot_ord_qty": "10",
                "tot_ccld_qty": "10",
                "tot_ccld_amt": "700000",
                "page_count": 1,
                "total_count": len(items),
            },
        }

    @patch("kis_agent.cli.main._create_agent")
    def test_basic_trades(self, mock_create_agent, capsys):
        """기본 당일 거래내역 조회."""
        from kis_agent.cli.main import cmd_trades

        mock_agent = Mock()
        mock_agent.account_api.inquire_daily_ccld.return_value = self._make_ccld_response()
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades"])
        cmd_trades(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "data" in result
        assert result["data"]["trades"]["count"] == 1
        trade = result["data"]["trades"]["items"][0]
        assert trade["code"] == "005930"
        assert trade["name"] == "삼성전자"
        assert trade["side"] == "매수"
        assert trade["date"] == "2026-03-25"
        assert trade["time"] == "09:30:12"
        assert trade["filledQty"] == "10"
        assert trade["filledAmount"] == "700,000"

    @patch("kis_agent.cli.main._create_agent")
    def test_empty_trades(self, mock_create_agent, capsys):
        """거래내역이 없는 경우."""
        from kis_agent.cli.main import cmd_trades

        mock_agent = Mock()
        mock_agent.account_api.inquire_daily_ccld.return_value = {
            "rt_cd": "0", "output1": [], "output2": {},
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades"])
        cmd_trades(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["trades"]["count"] == 0

    @patch("kis_agent.cli.main._create_agent")
    def test_sell_filter_passed(self, mock_create_agent, capsys):
        """--sell 필터가 API 호출에 전달됨."""
        from kis_agent.cli.main import cmd_trades

        mock_agent = Mock()
        mock_agent.account_api.inquire_daily_ccld.return_value = self._make_ccld_response([])
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades", "--sell"])
        cmd_trades(args)

        call_kwargs = mock_agent.account_api.inquire_daily_ccld.call_args
        assert call_kwargs[1]["ord_dvsn_cd"] == "01"  # 매도

    @patch("kis_agent.cli.main._create_agent")
    def test_buy_filter_passed(self, mock_create_agent, capsys):
        """--buy 필터가 API 호출에 전달됨."""
        from kis_agent.cli.main import cmd_trades

        mock_agent = Mock()
        mock_agent.account_api.inquire_daily_ccld.return_value = self._make_ccld_response([])
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades", "--buy"])
        cmd_trades(args)

        call_kwargs = mock_agent.account_api.inquire_daily_ccld.call_args
        assert call_kwargs[1]["ord_dvsn_cd"] == "02"  # 매수

    @patch("kis_agent.cli.main._create_agent")
    def test_limit(self, mock_create_agent, capsys):
        """--limit으로 출력 건수 제한."""
        from kis_agent.cli.main import cmd_trades

        items = [
            {
                "ord_dt": f"2026032{i}",
                "ord_tmd": "100000",
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "sll_buy_dvsn_cd_name": "매수",
                "ord_dvsn_name": "지정가",
                "ord_qty": "1",
                "ord_unpr": "70000",
                "tot_ccld_qty": "1",
                "avg_prvs": "70000",
                "tot_ccld_amt": "70000",
                "rmn_qty": "0",
                "cncl_yn": "N",
                "odno": f"000{i}",
                "orgn_odno": f"000{i}",
            }
            for i in range(5)
        ]

        mock_agent = Mock()
        mock_agent.account_api.inquire_daily_ccld.return_value = self._make_ccld_response(items)
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades", "--limit", "2"])
        cmd_trades(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result["data"]["trades"]["items"]) == 2

    @patch("kis_agent.cli.main._create_agent")
    def test_profit_mode(self, mock_create_agent, capsys):
        """--profit 모드 테스트."""
        from kis_agent.cli.main import cmd_trades

        mock_agent = Mock()
        mock_agent.account_api.get_period_trade_profit.return_value = {
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "sll_buy_dvsn_cd_name": "매도",
                    "buy_qty": "10",
                    "buy_amt": "700000",
                    "sll_qty": "10",
                    "sll_amt": "750000",
                    "rlzt_pfls": "50000",
                    "rlzt_erng_rt": "7.14",
                    "prsm_tlex_smtl": "1500",
                },
            ],
            "output2": {
                "tot_sll_amt": "750000",
                "tot_buy_amt": "700000",
                "tot_rlzt_pfls": "50000",
                "tot_prsm_tlex_smtl": "1500",
                "tot_rlzt_erng_rt": "7.14",
            },
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades", "--from", "30d", "--profit"])
        cmd_trades(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "profit" in result["data"]
        assert result["data"]["profit"]["count"] == 1
        item = result["data"]["profit"]["items"][0]
        assert item["code"] == "005930"
        assert item["realizedPL"] == "50,000"

    @patch("kis_agent.cli.main._create_agent")
    def test_daily_profit_mode(self, mock_create_agent, capsys):
        """--profit --daily-profit 모드 테스트."""
        from kis_agent.cli.main import cmd_trades

        mock_agent = Mock()
        mock_agent.account_api.get_period_profit.return_value = {
            "rt_cd": "0",
            "output1": [
                {
                    "bsop_dt": "20260325",
                    "rlzt_pfls": "150000",
                    "rlzt_erng_rt": "3.5",
                    "sll_amt": "5000000",
                    "buy_amt": "4850000",
                    "prsm_tlex_smtl": "2000",
                },
            ],
        }
        mock_create_agent.return_value = mock_agent

        args = build_parser().parse_args(["trades", "--from", "30d", "--profit", "--daily-profit"])
        cmd_trades(args)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "dailyProfit" in result["data"]
        assert result["data"]["dailyProfit"]["count"] == 1
        item = result["data"]["dailyProfit"]["items"][0]
        assert item["date"] == "2026-03-25"
        assert item["realizedPL"] == "150,000"
