"""
StockMarketAPI 포괄적 단위 테스트

커버리지 목표: 70% 이상
- get_fluctuation_rank
- get_volume_rank
- get_volume_power_rank
- get_pbar_tratio
- get_holiday_info
- is_holiday

생성일: 2026-01-04
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from kis_agent.stock.market_api import StockMarketAPI


class TestGetFluctuationRank:
    """get_fluctuation_rank 메서드 테스트"""

    def setup_method(self):
        """테스트별 셋업"""
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_fluctuation_rank_success_all_market(self):
        """등락률 순위 - 전체 시장 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {"code": "005930", "name": "삼성전자", "rate": "5.5"},
                {"code": "035420", "name": "NAVER", "rate": "3.2"},
            ],
        }

        result = self.api.get_fluctuation_rank(market="ALL")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_fluctuation_rank_kospi_market(self):
        """등락률 순위 - 코스피 시장"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930", "rate": "2.1"}],
        }

        result = self.api.get_fluctuation_rank(market="KOSPI")

        assert result is not None
        # 호출 파라미터 검증
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "0001"  # 코스피

    def test_fluctuation_rank_kosdaq_market(self):
        """등락률 순위 - 코스닥 시장"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "035720", "rate": "-1.5"}],
        }

        result = self.api.get_fluctuation_rank(market="KOSDAQ")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "1001"  # 코스닥

    def test_fluctuation_rank_konex_market(self):
        """등락률 순위 - 코넥스 시장"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "123456", "rate": "1.0"}],
        }

        result = self.api.get_fluctuation_rank(market="KONEX")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_cond_mrkt_div_code"] == "N"  # 코넥스

    def test_fluctuation_rank_unknown_market(self):
        """등락률 순위 - 알 수 없는 시장 (기본값 적용)"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_fluctuation_rank(market="UNKNOWN")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_cond_mrkt_div_code"] == "J"  # 기본값
        assert params["fid_input_iscd"] == "0000"

    def test_fluctuation_rank_custom_params(self):
        """등락률 순위 - 커스텀 파라미터"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_fluctuation_rank(
            market="KOSPI",
            count="20",
            price_min="5000",
            price_max="100000",
            volume_min="500000",
            target_cls_code="1",
            target_exls_cls_code="1",
            div_cls_code="1",
            rate_min="-10",
            rate_max="10",
        )

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_cnt_1"] == "20"
        assert params["fid_input_price_1"] == "5000"
        assert params["fid_input_price_2"] == "100000"
        assert params["fid_vol_cnt"] == "500000"
        assert params["fid_rsfl_rate1"] == "-10"
        assert params["fid_rsfl_rate2"] == "10"

    def test_fluctuation_rank_api_failure(self):
        """등락률 순위 - API 실패 (rt_cd != 0)"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "1",
            "msg1": "에러 발생",
        }

        result = self.api.get_fluctuation_rank()

        assert result is None

    def test_fluctuation_rank_no_output(self):
        """등락률 순위 - output 없음"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "성공",
        }

        result = self.api.get_fluctuation_rank()

        assert result is None

    def test_fluctuation_rank_none_response(self):
        """등락률 순위 - None 응답"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_fluctuation_rank()

        assert result is None


class TestGetVolumeRank:
    """get_volume_rank 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_volume_rank_success(self):
        """거래량 순위 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"code": "005930", "volume": "10000000"},
                {"code": "035420", "volume": "5000000"},
            ],
        }

        result = self.api.get_volume_rank(market="ALL")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_volume_rank_kospi(self):
        """거래량 순위 - 코스피"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_volume_rank(market="KOSPI")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "0001"

    def test_volume_rank_kosdaq(self):
        """거래량 순위 - 코스닥"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "035720"}],
        }

        result = self.api.get_volume_rank(market="KOSDAQ")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "1001"

    def test_volume_rank_konex(self):
        """거래량 순위 - 코넥스"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "123456"}],
        }

        result = self.api.get_volume_rank(market="KONEX")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_COND_MRKT_DIV_CODE"] == "NX"

    def test_volume_rank_elw(self):
        """거래량 순위 - ELW"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "500001"}],
        }

        result = self.api.get_volume_rank(market="ELW")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_COND_MRKT_DIV_CODE"] == "W"

    def test_volume_rank_custom_params(self):
        """거래량 순위 - 커스텀 파라미터"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_volume_rank(
            market="KOSPI",
            blng_cls_code="3",  # 거래금액순
            price_min="10000",
            price_max="500000",
            volume_min="200000",
            target_cls_code="000000000",
            target_exls_cls_code="1111111111",
            div_cls_code="1",
        )

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_BLNG_CLS_CODE"] == "3"
        assert params["FID_INPUT_PRICE_1"] == "10000"
        assert params["FID_DIV_CLS_CODE"] == "1"

    def test_volume_rank_failure(self):
        """거래량 순위 - 실패"""
        self.mock_client.make_request.return_value = {"rt_cd": "1"}

        result = self.api.get_volume_rank()

        assert result is None

    def test_volume_rank_none_response(self):
        """거래량 순위 - None 응답"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_volume_rank()

        assert result is None


class TestGetVolumePowerRank:
    """get_volume_power_rank 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_volume_power_rank_success(self):
        """체결강도 순위 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"code": "005930", "power": "150.5"},
                {"code": "035420", "power": "120.3"},
            ],
        }

        result = self.api.get_volume_power_rank(market="ALL")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_volume_power_rank_kospi(self):
        """체결강도 순위 - 코스피"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_volume_power_rank(market="KOSPI")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "0001"

    def test_volume_power_rank_kosdaq(self):
        """체결강도 순위 - 코스닥"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "035720"}],
        }

        result = self.api.get_volume_power_rank(market="KOSDAQ")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "1001"

    def test_volume_power_rank_kospi200(self):
        """체결강도 순위 - 코스피200"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_volume_power_rank(market="KOSPI200")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "2001"

    def test_volume_power_rank_custom_params(self):
        """체결강도 순위 - 커스텀 파라미터"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_volume_power_rank(
            market="KOSPI",
            div_cls_code="1",  # 보통주만
            price_min="5000",
            price_max="100000",
            volume_min="100000",
            target_cls_code="1",
            target_exls_cls_code="1",
        )

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_div_cls_code"] == "1"
        assert params["fid_input_price_1"] == "5000"
        assert params["fid_vol_cnt"] == "100000"

    def test_volume_power_rank_failure(self):
        """체결강도 순위 - 실패"""
        self.mock_client.make_request.return_value = {"rt_cd": "1"}

        result = self.api.get_volume_power_rank()

        assert result is None


class TestGetPbarTratio:
    """get_pbar_tratio 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_pbar_tratio_success(self):
        """매물대/거래비중 조회 - 성공"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"pbar_data": "test"},
        }

        result = self.api.get_pbar_tratio("005930")

        assert result is not None
        assert result["rt_cd"] == "0"

    def test_pbar_tratio_params(self):
        """매물대/거래비중 조회 - 파라미터 검증"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        self.api.get_pbar_tratio("035420")

        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "035420"
        assert params["fid_cond_mrkt_div_code"] == "J"
        assert params["fid_cond_scr_div_code"] == "20113"

    def test_pbar_tratio_retries_param_ignored(self):
        """매물대/거래비중 조회 - retries 파라미터 (호환성 유지용)"""
        self.mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}

        # retries 파라미터는 무시됨
        result = self.api.get_pbar_tratio("005930", retries=5)

        assert result is not None


class TestGetHolidayInfo:
    """get_holiday_info 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_holiday_info_success_without_date(self):
        """휴장일 정보 - 날짜 없이 조회"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"bass_dt": "20260101", "opnd_yn": "N"}],
        }

        result = self.api.get_holiday_info()

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert "BASS_DT" not in params

    def test_holiday_info_success_with_date(self):
        """휴장일 정보 - 날짜 지정 조회"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"bass_dt": "20260101", "opnd_yn": "N"}],
        }

        result = self.api.get_holiday_info(date="20260101")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["BASS_DT"] == "20260101"

    def test_holiday_info_exception(self):
        """휴장일 정보 - 예외 발생"""
        self.mock_client.make_request.side_effect = Exception("API 에러")

        result = self.api.get_holiday_info()

        assert result is None


class TestIsHoliday:
    """is_holiday 메서드 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_is_holiday_weekend_saturday(self):
        """휴장일 확인 - 토요일"""
        # 2026-01-03은 토요일
        result = self.api.is_holiday("20260103")

        assert result is True
        # 주말은 API 호출 없음
        self.mock_client.make_request.assert_not_called()

    def test_is_holiday_weekend_sunday(self):
        """휴장일 확인 - 일요일"""
        # 2026-01-04는 일요일
        result = self.api.is_holiday("20260104")

        assert result is True
        self.mock_client.make_request.assert_not_called()

    def test_is_holiday_public_holiday(self):
        """휴장일 확인 - 공휴일"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"bass_dt": "20260101", "opnd_yn": "N"},  # 신정 - 휴장
                {"bass_dt": "20260102", "opnd_yn": "Y"},  # 개장일
            ],
        }

        result = self.api.is_holiday("20260101")

        assert result is True

    def test_is_holiday_trading_day(self):
        """휴장일 확인 - 거래일"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"bass_dt": "20260102", "opnd_yn": "Y"},  # 개장일
            ],
        }

        result = self.api.is_holiday("20260102")

        assert result is False

    def test_is_holiday_date_not_found(self):
        """휴장일 확인 - 날짜 정보 없음"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {"bass_dt": "20260101", "opnd_yn": "N"},
            ],
        }

        # 없는 날짜는 거래일로 간주
        result = self.api.is_holiday("20260115")

        assert result is False

    def test_is_holiday_empty_output(self):
        """휴장일 확인 - 빈 output"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [],
        }

        result = self.api.is_holiday("20260102")

        assert result is False

    def test_is_holiday_api_error(self):
        """휴장일 확인 - API 에러"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "9",  # 실패
            "msg1": "시스템 오류",
        }

        result = self.api.is_holiday("20260102")

        assert result is None

    def test_is_holiday_api_returns_none(self):
        """휴장일 확인 - API None 반환"""
        self.mock_client.make_request.return_value = None

        result = self.api.is_holiday("20260102")

        assert result is None

    def test_is_holiday_invalid_date_format(self):
        """휴장일 확인 - 잘못된 날짜 형식"""
        result = self.api.is_holiday("invalid-date")

        assert result is None

    def test_is_holiday_exception_handling(self):
        """휴장일 확인 - 예외 처리"""
        self.mock_client.make_request.side_effect = Exception("네트워크 오류")

        result = self.api.is_holiday("20260102")

        assert result is None


class TestMarketCodeMapping:
    """시장 코드 매핑 테스트"""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_lowercase_market_code(self):
        """소문자 시장 코드"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "005930"}],
        }

        result = self.api.get_fluctuation_rank(market="kospi")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["fid_input_iscd"] == "0001"

    def test_mixed_case_market_code(self):
        """혼합 대소문자 시장 코드"""
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"code": "035720"}],
        }

        result = self.api.get_volume_rank(market="Kosdaq")

        assert result is not None
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        assert params["FID_INPUT_ISCD"] == "1001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
