"""
utils/sector_code.py 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상 함수: download_sector_code_mst, parse_sector_code_mst, get_sector_codes, get_sector_code_by_market
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd

from kis_agent.utils.sector_code import (
    SECTOR_CODE_URL,
    SECTOR_CODES,
    download_sector_code_mst,
    get_sector_code_by_market,
    get_sector_codes,
    parse_sector_code_mst,
)


class TestSectorCodeConstants(unittest.TestCase):
    """상수값 테스트"""

    def test_sector_code_url(self):
        """URL 상수 테스트"""
        self.assertIn("idxcode.mst.zip", SECTOR_CODE_URL)

    def test_sector_codes_dict(self):
        """SECTOR_CODES 딕셔너리 테스트"""
        self.assertIn("KOSPI", SECTOR_CODES)
        self.assertIn("KOSDAQ", SECTOR_CODES)
        self.assertIn("KOSPI200", SECTOR_CODES)
        self.assertEqual(SECTOR_CODES["KOSPI"], "0001")
        self.assertEqual(SECTOR_CODES["KOSDAQ"], "1001")


class TestParseSectorCodeMst(unittest.TestCase):
    """parse_sector_code_mst 함수 테스트"""

    def test_parse_sector_code_mst_success(self):
        """MST 파일 파싱 성공 테스트"""
        # Given - 테스트용 MST 데이터 생성
        test_data = "00001코스피\n00002대형주\n10001KOSDAQ\n20001KOSPI200\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mst", delete=False, encoding="cp949"
        ) as f:
            f.write(test_data)
            temp_path = f.name

        try:
            # When
            result = parse_sector_code_mst(temp_path)

            # Then
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 4)
            self.assertIn("market_div", result.columns)
            self.assertIn("sector_code", result.columns)
            self.assertIn("full_code", result.columns)
            self.assertIn("sector_name", result.columns)

            # 첫 번째 레코드 검증
            self.assertEqual(result.iloc[0]["market_div"], "0")
            self.assertEqual(result.iloc[0]["sector_code"], "0001")
            self.assertEqual(result.iloc[0]["full_code"], "00001")
            self.assertEqual(result.iloc[0]["sector_name"], "코스피")
        finally:
            os.unlink(temp_path)

    def test_parse_sector_code_mst_short_lines(self):
        """짧은 라인 무시 테스트"""
        # Given - 짧은 라인이 포함된 데이터
        test_data = "00001코스피\n123\n\n00002대형주\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mst", delete=False, encoding="cp949"
        ) as f:
            f.write(test_data)
            temp_path = f.name

        try:
            # When
            result = parse_sector_code_mst(temp_path)

            # Then
            self.assertEqual(len(result), 2)  # 짧은 라인 제외
        finally:
            os.unlink(temp_path)


class TestDownloadSectorCodeMst(unittest.TestCase):
    """download_sector_code_mst 함수 테스트"""

    @patch("pykis.utils.sector_code.urllib.request.urlretrieve")
    @patch("pykis.utils.sector_code.zipfile.ZipFile")
    @patch("pykis.utils.sector_code.os.remove")
    def test_download_sector_code_mst_success(
        self, mock_remove, mock_zipfile, mock_urlretrieve
    ):
        """MST 파일 다운로드 성공 테스트"""
        # Given
        download_dir = tempfile.gettempdir()
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # When
        result = download_sector_code_mst(download_dir)

        # Then
        self.assertIn("idxcode.mst", result)
        mock_urlretrieve.assert_called_once()
        mock_zip_instance.extractall.assert_called_once_with(download_dir)

    @patch("pykis.utils.sector_code.urllib.request.urlretrieve")
    @patch("pykis.utils.sector_code.zipfile.ZipFile")
    @patch("pykis.utils.sector_code.os.remove")
    def test_download_sector_code_mst_default_dir(
        self, mock_remove, mock_zipfile, mock_urlretrieve
    ):
        """기본 다운로드 디렉토리 테스트"""
        # Given
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        # When
        result = download_sector_code_mst(None)

        # Then
        self.assertIn("idxcode.mst", result)
        self.assertIn(tempfile.gettempdir(), result)


class TestGetSectorCodes(unittest.TestCase):
    """get_sector_codes 함수 테스트"""

    @patch("pykis.utils.sector_code.download_sector_code_mst")
    @patch("pykis.utils.sector_code.parse_sector_code_mst")
    @patch("pykis.utils.sector_code.os.remove")
    def test_get_sector_codes_as_dataframe(
        self, mock_remove, mock_parse, mock_download
    ):
        """DataFrame 형태로 반환 테스트"""
        # Given
        mock_download.return_value = "/tmp/idxcode.mst"
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1"],
                "sector_code": ["0001", "1001"],
                "full_code": ["00001", "11001"],
                "sector_name": ["코스피", "KOSDAQ"],
            }
        )
        mock_parse.return_value = mock_df

        # When
        result = get_sector_codes()

        # Then
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

    @patch("pykis.utils.sector_code.download_sector_code_mst")
    @patch("pykis.utils.sector_code.parse_sector_code_mst")
    @patch("pykis.utils.sector_code.os.remove")
    def test_get_sector_codes_as_dict(self, mock_remove, mock_parse, mock_download):
        """Dict 형태로 반환 테스트"""
        # Given
        mock_download.return_value = "/tmp/idxcode.mst"
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1"],
                "sector_code": ["0001", "1001"],
                "full_code": ["00001", "11001"],
                "sector_name": ["코스피", "KOSDAQ"],
            }
        )
        mock_parse.return_value = mock_df

        # When
        result = get_sector_codes(as_dict=True)

        # Then
        self.assertIsInstance(result, dict)
        self.assertEqual(result["0001"], "코스피")
        self.assertEqual(result["1001"], "KOSDAQ")


class TestGetSectorCodeByMarket(unittest.TestCase):
    """get_sector_code_by_market 함수 테스트"""

    @patch("pykis.utils.sector_code.get_sector_codes")
    def test_get_sector_code_by_market_kospi(self, mock_get_codes):
        """코스피 시장 필터링 테스트"""
        # Given
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "0", "1", "2"],
                "sector_code": ["0001", "0002", "1001", "2001"],
                "sector_name": ["코스피", "대형주", "KOSDAQ", "KOSPI200"],
            }
        )
        mock_get_codes.return_value = mock_df

        # When
        result = get_sector_code_by_market("kospi")

        # Then
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["market_div"] == "0"))

    @patch("pykis.utils.sector_code.get_sector_codes")
    def test_get_sector_code_by_market_kosdaq(self, mock_get_codes):
        """코스닥 시장 필터링 테스트"""
        # Given
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1", "1", "2"],
                "sector_code": ["0001", "1001", "1002", "2001"],
                "sector_name": ["코스피", "KOSDAQ", "대형주", "KOSPI200"],
            }
        )
        mock_get_codes.return_value = mock_df

        # When
        result = get_sector_code_by_market("kosdaq")

        # Then
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["market_div"] == "1"))

    @patch("pykis.utils.sector_code.get_sector_codes")
    def test_get_sector_code_by_market_other(self, mock_get_codes):
        """기타 지수 필터링 테스트"""
        # Given
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1", "2", "2"],
                "sector_code": ["0001", "1001", "2001", "2007"],
                "sector_name": ["코스피", "KOSDAQ", "KOSPI200", "KOSPI100"],
            }
        )
        mock_get_codes.return_value = mock_df

        # When
        result = get_sector_code_by_market("other")

        # Then
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["market_div"] == "2"))

    @patch("pykis.utils.sector_code.get_sector_codes")
    def test_get_sector_code_by_market_all(self, mock_get_codes):
        """전체 시장 조회 테스트"""
        # Given
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1", "2"],
                "sector_code": ["0001", "1001", "2001"],
                "sector_name": ["코스피", "KOSDAQ", "KOSPI200"],
            }
        )
        mock_get_codes.return_value = mock_df

        # When
        result = get_sector_code_by_market("all")

        # Then
        self.assertEqual(len(result), 3)

    @patch("pykis.utils.sector_code.get_sector_codes")
    def test_get_sector_code_by_market_numeric_code(self, mock_get_codes):
        """숫자 코드로 조회 테스트"""
        # Given
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1"],
                "sector_code": ["0001", "1001"],
                "sector_name": ["코스피", "KOSDAQ"],
            }
        )
        mock_get_codes.return_value = mock_df

        # When
        result = get_sector_code_by_market("0")

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["sector_name"], "코스피")

    @patch("pykis.utils.sector_code.get_sector_codes")
    def test_get_sector_code_by_market_unknown(self, mock_get_codes):
        """알 수 없는 시장 코드 테스트 (기본값=코스피)"""
        # Given
        mock_df = pd.DataFrame(
            {
                "market_div": ["0", "1"],
                "sector_code": ["0001", "1001"],
                "sector_name": ["코스피", "KOSDAQ"],
            }
        )
        mock_get_codes.return_value = mock_df

        # When
        result = get_sector_code_by_market("unknown")

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["sector_name"], "코스피")


if __name__ == "__main__":
    unittest.main()
