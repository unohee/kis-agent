"""
Futures Code Generator 테스트

선물옵션 종목코드 자동 생성 기능을 테스트합니다.

Created: 2026-01-20
Purpose: 종목코드 자동 생성 로직 검증

테스트 대상 기능:
- 선물 종목코드 생성 (현재 월물, 차근월물, 특정 월물)
- 옵션 종목코드 생성 (콜/풋, 행사가)
- ATM 옵션 코드 생성
- 종목코드 파싱
"""

import unittest
from datetime import datetime
from unittest.mock import patch

import pytest

from kis_agent.futures.code_generator import (
    FuturesCodeGenerator,
    generate_call_option,
    generate_current_futures,
    generate_next_futures,
    generate_put_option,
)


class TestFuturesCodeGenerator(unittest.TestCase):
    """FuturesCodeGenerator 테스트"""

    def test_series_map(self):
        """시리즈 매핑 확인"""
        series_map = FuturesCodeGenerator.SERIES_MAP
        self.assertEqual(series_map[3], "S")
        self.assertEqual(series_map[6], "M")
        self.assertEqual(series_map[9], "U")
        self.assertEqual(series_map[12], "Z")

    def test_product_codes(self):
        """상품 코드 확인"""
        self.assertEqual(FuturesCodeGenerator.KOSPI200_FUTURES, "101")
        self.assertEqual(FuturesCodeGenerator.KOSPI200_CALL, "201")
        self.assertEqual(FuturesCodeGenerator.KOSPI200_PUT, "301")

    @patch("pykis.futures.code_generator.datetime")
    def test_get_current_series_january(self, mock_datetime):
        """현재 시리즈 반환 - 1월"""
        mock_datetime.now.return_value = datetime(2026, 1, 20)
        series = FuturesCodeGenerator.get_current_series()
        self.assertEqual(series, "S")  # 3월물

    @patch("pykis.futures.code_generator.datetime")
    def test_get_current_series_march(self, mock_datetime):
        """현재 시리즈 반환 - 3월"""
        mock_datetime.now.return_value = datetime(2026, 3, 10)
        series = FuturesCodeGenerator.get_current_series()
        self.assertEqual(series, "S")  # 3월물

    @patch("pykis.futures.code_generator.datetime")
    def test_get_current_series_april(self, mock_datetime):
        """현재 시리즈 반환 - 4월 (다음은 6월물)"""
        mock_datetime.now.return_value = datetime(2026, 4, 1)
        series = FuturesCodeGenerator.get_current_series()
        self.assertEqual(series, "M")  # 6월물

    @patch("pykis.futures.code_generator.datetime")
    def test_get_current_series_december(self, mock_datetime):
        """현재 시리즈 반환 - 12월"""
        mock_datetime.now.return_value = datetime(2026, 12, 15)
        series = FuturesCodeGenerator.get_current_series()
        self.assertEqual(series, "Z")  # 12월물

    @patch("pykis.futures.code_generator.datetime")
    def test_get_current_expiry_month_january(self, mock_datetime):
        """현재 만기월 반환 - 1월"""
        mock_datetime.now.return_value = datetime(2026, 1, 20)
        month = FuturesCodeGenerator.get_current_expiry_month()
        self.assertEqual(month, 3)

    def test_generate_futures_code_march(self):
        """3월물 선물 코드 생성"""
        code = FuturesCodeGenerator.generate_futures_code(expiry_month=3)
        self.assertEqual(code, "101S03")

    def test_generate_futures_code_june(self):
        """6월물 선물 코드 생성"""
        code = FuturesCodeGenerator.generate_futures_code(expiry_month=6)
        self.assertEqual(code, "101M06")

    def test_generate_futures_code_september(self):
        """9월물 선물 코드 생성"""
        code = FuturesCodeGenerator.generate_futures_code(expiry_month=9)
        self.assertEqual(code, "101U09")

    def test_generate_futures_code_december(self):
        """12월물 선물 코드 생성"""
        code = FuturesCodeGenerator.generate_futures_code(expiry_month=12)
        self.assertEqual(code, "101Z12")

    def test_generate_futures_code_with_series(self):
        """시리즈로 선물 코드 생성"""
        code = FuturesCodeGenerator.generate_futures_code(series="S")
        self.assertEqual(code, "101S03")

    def test_generate_futures_code_invalid_month(self):
        """잘못된 만기월"""
        with self.assertRaises(ValueError) as context:
            FuturesCodeGenerator.generate_futures_code(expiry_month=5)
        self.assertIn("잘못된 만기월", str(context.exception))

    def test_generate_futures_code_invalid_series(self):
        """잘못된 시리즈"""
        with self.assertRaises(ValueError) as context:
            FuturesCodeGenerator.generate_futures_code(series="X")
        self.assertIn("잘못된 시리즈 코드", str(context.exception))

    def test_generate_futures_code_both_params(self):
        """series와 expiry_month 동시 사용 불가"""
        with self.assertRaises(ValueError) as context:
            FuturesCodeGenerator.generate_futures_code(series="S", expiry_month=3)
        self.assertIn("동시에 사용할 수 없습니다", str(context.exception))

    def test_generate_option_code_call(self):
        """콜옵션 코드 생성"""
        code = FuturesCodeGenerator.generate_option_code("CALL", 340.0, expiry_month=3)
        self.assertEqual(code, "201SC340")

    def test_generate_option_code_put(self):
        """풋옵션 코드 생성"""
        code = FuturesCodeGenerator.generate_option_code("PUT", 340.0, expiry_month=3)
        self.assertEqual(code, "301SP340")

    def test_generate_option_code_decimal_strike(self):
        """소수점 행사가 (절사)"""
        code = FuturesCodeGenerator.generate_option_code("CALL", 342.5, expiry_month=6)
        self.assertEqual(code, "201MC342")

    def test_generate_option_code_with_series(self):
        """시리즈로 옵션 코드 생성"""
        code = FuturesCodeGenerator.generate_option_code("CALL", 340.0, series="M")
        self.assertEqual(code, "201MC340")

    def test_generate_option_code_invalid_type(self):
        """잘못된 옵션 타입"""
        with self.assertRaises(ValueError) as context:
            FuturesCodeGenerator.generate_option_code("INVALID", 340.0)
        self.assertIn("CALL", str(context.exception))

    def test_generate_atm_option_codes(self):
        """ATM 옵션 코드 생성"""
        result = FuturesCodeGenerator.generate_atm_option_codes(340.25, expiry_month=3)

        self.assertEqual(result["atm_strike"], 340.0)
        self.assertEqual(len(result["call"]), 7)  # range_count=3 → -3~+3 = 7개
        self.assertEqual(len(result["put"]), 7)

        # ATM 확인
        self.assertIn("201SC340", result["call"])
        self.assertIn("301SP340", result["put"])

        # ITM/OTM 확인
        self.assertIn("201SC337", result["call"])  # OTM (현재가 > 행사가)
        self.assertIn("201SC342", result["call"])  # ITM (현재가 < 행사가)

    def test_generate_atm_option_codes_custom_range(self):
        """ATM 옵션 코드 생성 (범위 커스터마이징)"""
        result = FuturesCodeGenerator.generate_atm_option_codes(
            340.25, expiry_month=3, range_count=1
        )

        self.assertEqual(len(result["call"]), 3)  # -1, 0, +1 = 3개
        self.assertEqual(len(result["put"]), 3)

    def test_parse_futures_code(self):
        """선물 종목코드 파싱"""
        result = FuturesCodeGenerator.parse_futures_code("101S03")

        self.assertEqual(result["product"], "KOSPI200 선물")
        self.assertEqual(result["series"], "S")
        self.assertEqual(result["expiry_month"], 3)

    def test_parse_option_code_call(self):
        """콜옵션 종목코드 파싱"""
        result = FuturesCodeGenerator.parse_option_code("201SC340")

        self.assertEqual(result["product"], "KOSPI200 옵션")
        self.assertEqual(result["option_type"], "CALL")
        self.assertEqual(result["series"], "S")
        self.assertEqual(result["strike_price"], 340.0)

    def test_parse_option_code_put(self):
        """풋옵션 종목코드 파싱"""
        result = FuturesCodeGenerator.parse_option_code("301SP342")

        self.assertEqual(result["product"], "KOSPI200 옵션")
        self.assertEqual(result["option_type"], "PUT")
        self.assertEqual(result["series"], "S")
        self.assertEqual(result["strike_price"], 342.0)

    def test_parse_futures_code_invalid(self):
        """잘못된 선물 코드 파싱"""
        with self.assertRaises(ValueError):
            FuturesCodeGenerator.parse_futures_code("101")

    def test_parse_option_code_invalid(self):
        """잘못된 옵션 코드 파싱"""
        with self.assertRaises(ValueError):
            FuturesCodeGenerator.parse_option_code("201SC")


class TestConvenienceFunctions(unittest.TestCase):
    """편의 함수 테스트"""

    @patch("pykis.futures.code_generator.FuturesCodeGenerator.generate_futures_code")
    def test_generate_current_futures(self, mock_generate):
        """현재 월물 생성 (편의 함수)"""
        mock_generate.return_value = "101S03"
        result = generate_current_futures()

        self.assertEqual(result, "101S03")
        mock_generate.assert_called_once()

    @patch("pykis.futures.code_generator.FuturesCodeGenerator.get_current_expiry_month")
    @patch("pykis.futures.code_generator.FuturesCodeGenerator.generate_futures_code")
    def test_generate_next_futures(self, mock_generate, mock_get_month):
        """차근월물 생성 (편의 함수)"""
        mock_get_month.return_value = 3  # 현재 3월물
        mock_generate.return_value = "101M06"

        result = generate_next_futures()

        self.assertEqual(result, "101M06")
        mock_generate.assert_called_once_with(expiry_month=6)

    @patch("pykis.futures.code_generator.FuturesCodeGenerator.generate_option_code")
    def test_generate_call_option(self, mock_generate):
        """콜옵션 생성 (편의 함수)"""
        mock_generate.return_value = "201SC340"
        result = generate_call_option(340.0)

        self.assertEqual(result, "201SC340")
        mock_generate.assert_called_once_with("CALL", 340.0, expiry_month=None)

    @patch("pykis.futures.code_generator.FuturesCodeGenerator.generate_option_code")
    def test_generate_put_option(self, mock_generate):
        """풋옵션 생성 (편의 함수)"""
        mock_generate.return_value = "301SP340"
        result = generate_put_option(340.0)

        self.assertEqual(result, "301SP340")
        mock_generate.assert_called_once_with("PUT", 340.0, expiry_month=None)


@pytest.mark.parametrize(
    "expiry_month,expected_series",
    [
        (3, "S"),
        (6, "M"),
        (9, "U"),
        (12, "Z"),
    ],
)
def test_futures_code_generation_parametrized(expiry_month, expected_series):
    """파라미터화된 선물 코드 생성 테스트"""
    code = FuturesCodeGenerator.generate_futures_code(expiry_month=expiry_month)
    expected = f"101{expected_series}{expiry_month:02d}"
    assert code == expected


@pytest.mark.parametrize(
    "option_type,strike,expected_prefix",
    [
        ("CALL", 340.0, "201SC"),
        ("PUT", 340.0, "301SP"),
        ("CALL", 342.5, "201SC"),
        ("PUT", 345.0, "301SP"),
    ],
)
def test_option_code_generation_parametrized(option_type, strike, expected_prefix):
    """파라미터화된 옵션 코드 생성 테스트"""
    code = FuturesCodeGenerator.generate_option_code(
        option_type, strike, expiry_month=3
    )
    assert code.startswith(expected_prefix)
    assert len(code) == 8


if __name__ == "__main__":
    unittest.main()
