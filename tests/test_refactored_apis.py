"""
리팩터링된 API 단위 테스트

데코레이터 기반 API의 단위 테스트 스위트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import warnings
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# 테스트 대상 모듈
from pykis.stock.api_enhanced import StockAPIEnhanced
from pykis.account.api_enhanced import AccountAPIEnhanced
from pykis.core.decorators import api_endpoint, deprecated, with_retry


class TestStockAPIEnhanced:
    """StockAPIEnhanced 단위 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient"""
        client = Mock()
        client.make_request = MagicMock(return_value={
            "rt_cd": "0",
            "msg1": "정상처리",
            "output": {"stck_prpr": "70000", "prdy_ctrt": "-1.5"}
        })
        return client

    @pytest.fixture
    def stock_api(self, mock_client):
        """StockAPIEnhanced 인스턴스"""
        account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        return StockAPIEnhanced(mock_client, account_info)

    def test_get_price_current_success(self, stock_api):
        """현재가 조회 성공 테스트"""
        result = stock_api.get_price_current("005930")
        assert result is not None
        assert "FID_INPUT_ISCD" in result
        assert result["FID_INPUT_ISCD"] == "005930"

    def test_get_price_current_invalid_code(self, stock_api):
        """잘못된 종목코드 예외 테스트"""
        with pytest.raises(ValueError) as exc_info:
            stock_api.get_price_current("INVALID")
        assert "잘못된 종목코드" in str(exc_info.value)

    def test_get_price_daily_validation(self, stock_api):
        """일별 시세 파라미터 검증 테스트"""
        # 정상 호출
        result = stock_api.get_price_daily("005930", "D", "1")
        assert result["fid_period_div_code"] == "D"

        # 잘못된 기간구분
        with pytest.raises(ValueError) as exc_info:
            stock_api.get_price_daily("005930", "X", "1")
        assert "잘못된 기간구분" in str(exc_info.value)

    def test_deprecated_method_warning(self, stock_api):
        """Deprecated 메서드 경고 테스트"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = stock_api.get_stock_price("005930")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_price_current" in str(w[0].message)

    def test_get_market_fluctuation(self, stock_api):
        """시장 등락률 조회 테스트"""
        result = stock_api.get_market_fluctuation(min_volume=1000000)
        assert result["fid_vol_cnt"] == "1000000"
        assert result["fid_cond_scr_div_code"] == "20170"

    def test_get_program_trade_date_default(self, stock_api):
        """프로그램매매 기본 날짜 테스트"""
        with patch('pykis.stock.api_enhanced.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 12, 1)
            mock_datetime.strftime = datetime.strftime

            result = stock_api.get_program_trade_stock("005930")
            assert result["fid_input_date_1"] == "20241201"
            assert result["fid_input_date_2"] == "20241201"

    def test_kospi200_futures_code(self, stock_api):
        """KOSPI200 선물 코드 생성 테스트"""
        # 3월물 테스트
        march_date = datetime(2024, 3, 1)
        code = stock_api.get_kospi200_futures_code(march_date)
        assert code == "101W03"

        # 12월 이후 -> 다음해 3월물
        december_date = datetime(2024, 12, 20)
        code = stock_api.get_kospi200_futures_code(december_date)
        assert code == "101W03"


class TestAccountAPIEnhanced:
    """AccountAPIEnhanced 단위 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient"""
        client = Mock()
        client.make_request = MagicMock(return_value={
            "rt_cd": "0",
            "msg1": "정상처리",
            "output1": [],
            "output2": [{"tot_evlu_amt": "10000000", "erng_rt": "5.5"}]
        })
        return client

    @pytest.fixture
    def account_api(self, mock_client):
        """AccountAPIEnhanced 인스턴스"""
        account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        return AccountAPIEnhanced(mock_client, account_info)

    def test_initialization_validation(self, mock_client):
        """초기화 시 계좌정보 검증 테스트"""
        # 계좌정보 없음
        with pytest.raises(ValueError) as exc_info:
            AccountAPIEnhanced(mock_client, None)
        assert "계좌 정보가 필요" in str(exc_info.value)

        # CANO 없음
        with pytest.raises(ValueError) as exc_info:
            AccountAPIEnhanced(mock_client, {"ACNT_PRDT_CD": "01"})
        assert "CANO와 ACNT_PRDT_CD가 필요" in str(exc_info.value)

    def test_get_balance_holdings(self, account_api):
        """잔고 조회 테스트"""
        result = account_api.get_balance_holdings()
        assert result["CANO"] == "12345678"
        assert result["ACNT_PRDT_CD"] == "01"
        assert result["INQR_DVSN"] == "01"

    def test_get_order_capacity_validation(self, account_api):
        """주문 가능 금액 조회 검증 테스트"""
        # 정상 호출
        result = account_api.get_order_capacity("005930")
        assert result["PDNO"] == "005930"

        # 잘못된 종목코드
        with pytest.raises(ValueError) as exc_info:
            account_api.get_order_capacity("12345")  # 5자리
        assert "잘못된 종목코드" in str(exc_info.value)

    def test_get_total_assets(self, account_api):
        """총 자산 정보 계산 테스트"""
        with patch.object(account_api, 'get_balance_holdings') as mock_balance:
            mock_balance.return_value = {
                "rt_cd": "0",
                "output1": [
                    {"pdno": "005930", "prdt_name": "삼성전자", "hldg_qty": "100"}
                ],
                "output2": [{
                    "dnca_tot_amt": "5000000",
                    "evlu_amt_smtl_amt": "7000000",
                    "evlu_pfls_smtl_amt": "500000",
                    "tot_evlu_amt": "12000000",
                    "erng_rt": "4.35"
                }]
            }

            assets = account_api.get_total_assets()
            assert assets["예수금"] == 5000000
            assert assets["주식평가액"] == 7000000
            assert assets["총자산"] == 12000000
            assert assets["수익률"] == 4.35
            assert assets["보유종목수"] == 1

    def test_get_holdings_summary(self, account_api):
        """보유종목 요약 테스트"""
        with patch.object(account_api, 'get_balance_holdings') as mock_balance:
            mock_balance.return_value = {
                "rt_cd": "0",
                "output1": [{
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "100",
                    "pchs_avg_pric": "65000",
                    "prpr": "70000",
                    "evlu_amt": "7000000",
                    "evlu_pfls_amt": "500000",
                    "evlu_pfls_rt": "7.69"
                }]
            }

            summary = account_api.get_holdings_summary()
            assert len(summary) == 1
            assert summary[0]["종목코드"] == "005930"
            assert summary[0]["보유수량"] == 100
            assert summary[0]["수익률"] == 7.69


class TestDecorators:
    """데코레이터 단위 테스트"""

    def test_api_endpoint_decorator(self):
        """@api_endpoint 데코레이터 테스트"""
        mock_self = Mock()
        mock_self._add_default_params = lambda x: x
        mock_self._make_request_dict = MagicMock(return_value={"rt_cd": "0"})

        @api_endpoint('TEST_ENDPOINT', 'TEST_TR_ID')
        def test_method(self, param1):
            return {"param": param1}

        # 메타데이터 확인
        assert test_method._api_endpoint == 'TEST_ENDPOINT'
        assert test_method._tr_id == 'TEST_TR_ID'

    def test_with_retry_decorator(self):
        """@with_retry 데코레이터 테스트"""
        call_count = 0

        @with_retry(max_retries=3, delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "Success"

        result = flaky_function()
        assert result == "Success"
        assert call_count == 3

    def test_deprecated_decorator(self):
        """@deprecated 데코레이터 테스트"""
        @deprecated(alternative="new_function")
        def old_function():
            return "Old result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()

            assert result == "Old result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "new_function" in str(w[0].message)


class TestFailFastPattern:
    """Fail-fast 패턴 테스트"""

    def test_base_api_fail_fast(self):
        """BaseAPI의 fail-fast 예외 처리 테스트"""
        from pykis.core.base_api import BaseAPI

        mock_client = Mock()
        mock_client.make_request = Mock(side_effect=Exception("API Error"))

        api = BaseAPI(mock_client)

        with pytest.raises(Exception) as exc_info:
            api._make_request_dict(
                endpoint="/test",
                tr_id="TEST",
                params={}
            )
        assert "API 요청 실패" in str(exc_info.value)
        assert "API Error" in str(exc_info.value.__cause__)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])