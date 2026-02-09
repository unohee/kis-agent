"""
Unit tests for pagination functionality in PyKIS.

Tests cover:
- inquire_daily_ccld pagination
- Continuation key handling
- Page callback functionality
- Duplicate removal
- Error handling during pagination
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, call, patch

from pykis.account.api import AccountAPI


class TestPagination(unittest.TestCase):
    """Test pagination functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = AccountAPI(self.mock_client, self.account_info)

        # Mock the make_request method to return proper structure
        self.mock_client.make_request = Mock()

    def test_inquire_daily_ccld_single_page(self):
        """Test single page query without pagination"""
        # Mock response
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "정상처리 되었습니다.",
            "output1": [
                {
                    "ord_dt": "20251002",
                    "odno": "0001",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "ord_qty": "10",
                    "tot_ccld_qty": "10",
                }
            ],
            "output2": {
                "tot_ord_qty": "10",
                "tot_ccld_qty": "10",
                "tot_ccld_amt": "700000",
            },
        }

        self.mock_client.make_request.return_value = mock_response

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251002", end_date="20251002", pagination=False
        )

        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output1"]), 1)
        self.mock_client.make_request.assert_called_once()

    def test_inquire_daily_ccld_pagination_multiple_pages(self):
        """Test pagination with multiple pages"""
        # Mock responses for 3 pages
        page1_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",
            "ctx_area_fk100": "FK001",
            "ctx_area_nk100": "NK001",
            "output1": [
                {
                    "ord_dt": "20251001",
                    "odno": f"000{i}",
                    "pdno": "005930",
                    "ord_qty": "10",
                    "tot_ccld_qty": "10",
                    "ord_tmd": "090000",
                }
                for i in range(1, 101)
            ],
            "output2": {"tot_ord_qty": "1000", "tot_ccld_qty": "1000"},
        }

        page2_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",
            "ctx_area_fk100": "FK002",
            "ctx_area_nk100": "NK002",
            "output1": [
                {
                    "ord_dt": "20251001",
                    "odno": f"010{i}",
                    "pdno": "035420",
                    "ord_qty": "5",
                    "tot_ccld_qty": "5",
                    "ord_tmd": "100000",
                }
                for i in range(1, 101)
            ],
            "output2": {"tot_ord_qty": "500", "tot_ccld_qty": "500"},
        }

        page3_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "정상처리 되었습니다.",
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
            "output1": [
                {
                    "ord_dt": "20251001",
                    "odno": f"020{i}",
                    "pdno": "000660",
                    "ord_qty": "20",
                    "tot_ccld_qty": "20",
                    "ord_tmd": "110000",
                }
                for i in range(1, 51)
            ],
            "output2": {"tot_ord_qty": "1000", "tot_ccld_qty": "1000"},
        }

        self.mock_client.make_request.side_effect = [
            page1_response,
            page2_response,
            page3_response,
        ]

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output1"]), 250)  # 100 + 100 + 50
        self.assertEqual(result["output2"]["page_count"], 3)
        self.assertEqual(result["output2"]["total_count"], 250)
        self.assertEqual(self.mock_client.make_request.call_count, 3)

    def test_inquire_daily_ccld_pagination_with_callback(self):
        """Test pagination with page callback"""
        callback_calls = []

        def page_callback(page_num, page_data, ctx_info):
            callback_calls.append(
                {
                    "page": page_num,
                    "count": len(page_data),
                    "fk": ctx_info.get("FK100"),
                    "nk": ctx_info.get("NK100"),
                }
            )

        # Mock two pages
        page1_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",
            "ctx_area_fk100": "FK001",
            "ctx_area_nk100": "NK001",
            "output1": [
                {"ord_dt": "20251001", "odno": f"{i:04d}", "pdno": "005930"}
                for i in range(100)
            ],
            "output2": {},
        }

        page2_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "정상처리 되었습니다.",
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
            "output1": [
                {"ord_dt": "20251001", "odno": f"{i:04d}", "pdno": "005930"}
                for i in range(100, 150)
            ],
            "output2": {},
        }

        self.mock_client.make_request.side_effect = [page1_response, page2_response]

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251001",
            end_date="20251002",
            pagination=True,
            page_callback=page_callback,
        )

        # Verify callback was called
        self.assertEqual(len(callback_calls), 2)
        self.assertEqual(callback_calls[0]["page"], 1)
        self.assertEqual(callback_calls[0]["count"], 100)
        self.assertEqual(callback_calls[1]["page"], 2)
        self.assertEqual(callback_calls[1]["count"], 50)

    def test_inquire_daily_ccld_pagination_duplicate_removal(self):
        """Test duplicate removal in pagination"""
        # Create responses with duplicate entries
        # Page 1 must have 100+ items to trigger continuation, otherwise pagination stops
        page1_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",
            "ctx_area_fk100": "FK001",
            "ctx_area_nk100": "NK001",
            "output1": [
                {
                    "ord_dt": "20251001",
                    "odno": f"{i:04d}",
                    "pdno": "005930",
                    "ord_qty": "10",
                }
                for i in range(1, 101)  # 100 items to trigger continuation
            ]
            + [
                {
                    "ord_dt": "20251001",
                    "odno": "9999",  # This will be duplicated in page 2
                    "pdno": "005930",
                    "ord_qty": "20",
                }
            ],
            "output2": {},
        }

        page2_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "정상처리 되었습니다.",
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
            "output1": [
                {
                    "ord_dt": "20251001",
                    "odno": "9999",  # Duplicate from page 1
                    "pdno": "005930",
                    "ord_qty": "20",
                },
                {
                    "ord_dt": "20251001",
                    "odno": "0500",
                    "pdno": "035420",
                    "ord_qty": "30",
                },
            ],
            "output2": {},
        }

        self.mock_client.make_request.side_effect = [page1_response, page2_response]

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # Verify - should have 102 unique entries (101 from page1 + 1 new from page2)
        # The duplicate "9999" should be removed
        self.assertEqual(len(result["output1"]), 102)
        order_numbers = [item["odno"] for item in result["output1"]]
        # Check that 9999 appears only once
        self.assertEqual(order_numbers.count("9999"), 1)
        # Check that 0500 from page 2 is included
        self.assertIn("0500", order_numbers)

    def test_inquire_daily_ccld_pagination_max_pages(self):
        """Test max_pages limit in pagination"""
        # Create response that would continue
        continuing_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",
            "ctx_area_fk100": "FK001",
            "ctx_area_nk100": "NK001",
            "output1": [
                {"ord_dt": "20251001", "odno": f"{i:04d}", "pdno": "005930"}
                for i in range(100)
            ],
            "output2": {},
        }

        # Mock will return the same continuing response
        self.mock_client.make_request.return_value = continuing_response

        # Execute with max_pages=3
        result = self.api.inquire_daily_ccld(
            start_date="20251001",
            end_date="20251002",
            pagination=True,
            max_pages=3,
        )

        # Verify - should stop at 3 pages
        self.assertEqual(self.mock_client.make_request.call_count, 3)
        self.assertEqual(result["output2"]["page_count"], 3)

    def test_inquire_daily_ccld_pagination_error_handling(self):
        """Test error handling during pagination"""
        # First page succeeds
        page1_response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",
            "ctx_area_fk100": "FK001",
            "ctx_area_nk100": "NK001",
            "output1": [
                {"ord_dt": "20251001", "odno": f"{i:04d}", "pdno": "005930"}
                for i in range(100)
            ],
            "output2": {},
        }

        # Second page fails
        page2_response = None

        self.mock_client.make_request.side_effect = [page1_response, page2_response]

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # Verify - should return data from first page
        self.assertIsNotNone(result)
        self.assertEqual(len(result["output1"]), 100)
        self.assertEqual(result["output2"]["page_count"], 1)

    def test_inquire_daily_ccld_pagination_empty_continuation_keys(self):
        """Test pagination stops when continuation keys are empty"""
        # Response with empty continuation keys
        response = {
            "rt_cd": "0",
            "msg_cd": "SUCCESSFUL",
            "msg1": "조회가 계속됩니다.",  # Message says continue
            "ctx_area_fk100": "",  # But keys are empty
            "ctx_area_nk100": "",
            "output1": [
                {"ord_dt": "20251001", "odno": "0001", "pdno": "005930"},
            ],
            "output2": {},
        }

        self.mock_client.make_request.return_value = response

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # Verify - should stop after first page due to empty keys
        self.assertEqual(self.mock_client.make_request.call_count, 1)
        self.assertEqual(result["output2"]["page_count"], 1)

    def test_inquire_daily_ccld_no_data(self):
        """Test handling of no data response"""
        # Mock empty response
        empty_response = {
            "rt_cd": "0",
            "msg_cd": "NO_DATA",
            "msg1": "조회 결과가 없습니다.",
            "output1": [],
            "output2": {},
        }

        self.mock_client.make_request.return_value = empty_response

        # Execute
        result = self.api.inquire_daily_ccld(
            start_date="20251002", end_date="20251002", pagination=False
        )

        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output1"]), 0)


if __name__ == "__main__":
    unittest.main()
