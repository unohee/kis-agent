"""
베이스 API 클래스 - 공통 기능 제공

이 모듈은 모든 API 클래스들이 상속받을 베이스 클래스를 제공합니다:
- 공통 데이터 변환 로직
- 숫자형 필드 자동 변환
- DataFrame/Dict 반환 타입 통합
- API 응답 정규화
- 통합 예외 처리 (ExceptionHandler 상속)
- Agent를 통한 올바른 사용법 검증
"""

import logging
import traceback
import warnings
from typing import Dict, List, Optional

import pandas as pd

from .cache import APICache
from .exceptions import ExceptionHandler, api_method
from .response_processor import APIRequestManager

# 모듈 레벨 로거
_logger = logging.getLogger(__name__)


class DirectAPIUsageWarning(UserWarning):
    """Agent를 통하지 않고 직접 API를 사용할 때 발생하는 경고"""

    pass


class BaseAPI(ExceptionHandler):
    """모든 API 클래스들의 공통 베이스 클래스"""

    # Agent를 통해 생성되었는지 추적하는 플래그
    _created_via_agent: bool = False

    def __init__(
        self,
        client,
        account_info=None,
        enable_cache=True,
        cache_config=None,
        _from_agent: bool = False,
    ):
        """
        BaseAPI 초기화

        Args:
            client: KISClient 인스턴스
            account_info: 계좌 정보 (필요한 경우)
            enable_cache: 캐시 사용 여부 (기본: True)
            cache_config: 캐시 설정 (default_ttl, max_size)
            _from_agent: Agent를 통해 생성되었는지 여부 (내부 사용)

        Warning:
            이 클래스를 직접 인스턴스화하지 마세요.
            반드시 `pykis.Agent`를 통해 API에 접근해야 합니다.

        Example:
            올바른 사용법:
            >>> from kis_agent import Agent
            >>> agent = Agent(app_key="...", app_secret="...", ...)
            >>> price = agent.get_stock_price("005930")

            잘못된 사용법 (경고 발생):
            >>> from kis_agent.stock.price_api import StockPriceAPI
            >>> api = StockPriceAPI(client)  # DirectAPIUsageWarning 발생
        """
        ExceptionHandler.__init__(self)
        self.client = client
        self.account = account_info
        self._created_via_agent = _from_agent

        # Agent를 통하지 않고 직접 사용하면 경고 발생
        if not _from_agent:
            self._warn_direct_usage()

        # 캐시 초기화
        if enable_cache:
            cache_config = cache_config or {}
            self.cache = APICache(
                default_ttl=cache_config.get("default_ttl", 5),
                max_size=cache_config.get("max_size", 1000),
            )
        else:
            self.cache = None

        # 각 API별 숫자형 필드 매핑 테이블
        self.numeric_field_mappings = self._get_numeric_field_mappings()

        # API 요청 관리자 초기화 (Factory Pattern)
        self.request_manager = APIRequestManager(
            client=client,
            metadata_adder=self._add_response_metadata,
            field_converter=self._convert_numeric_fields,
        )

    def _warn_direct_usage(self) -> None:
        """Agent를 통하지 않고 직접 API를 사용할 때 경고 발생"""
        class_name = self.__class__.__name__

        # 호출 스택 정보 가져오기 (사용자 코드 위치 파악)
        stack_info = "".join(traceback.format_stack()[:-2])

        warning_message = f"""
================================================================================
⚠️  PyKIS 직접 API 사용 경고 (DirectAPIUsageWarning)
================================================================================

'{class_name}'를 직접 인스턴스화했습니다.
이 방식은 권장되지 않으며 인증 문제나 설정 충돌이 발생할 수 있습니다.

📌 올바른 사용법:
    from kis_agent import Agent

    agent = Agent(
        app_key="YOUR_APP_KEY",
        app_secret="YOUR_APP_SECRET",
        account_no="YOUR_ACCOUNT_NO",
        account_code="01"
    )

    # Agent를 통해 API 메서드 호출
    price = agent.get_stock_price("005930")
    balance = agent.get_account_balance()

❌ 잘못된 사용법 (현재):
    from kis_agent.stock.price_api import StockPriceAPI
    api = StockPriceAPI(client)  # 직접 인스턴스화 - 권장하지 않음

📍 호출 위치:
{stack_info}
================================================================================
"""
        # 경고 발생 (stacklevel=4로 실제 호출 위치 표시)
        warnings.warn(warning_message, DirectAPIUsageWarning, stacklevel=4)

        # 로거에도 경고 기록
        _logger.warning(
            f"'{class_name}'가 Agent를 통하지 않고 직접 인스턴스화되었습니다. "
            "pykis.Agent를 사용하세요."
        )

    def _get_numeric_field_mappings(self) -> Dict[str, List[str]]:
        """API별 숫자형 변환이 필요한 필드들을 정의"""
        return {
            # 계좌 관련
            "account_balance": [
                "hldg_qty",
                "ord_psbl_qty",
                "pchs_avg_pric",
                "pchs_amt",
                "prpr",
                "evlu_amt",
                "evlu_pfls_amt",
                "evlu_pfls_rt",
                "evlu_erng_rt",
                "bfdy_buy_qty",
                "bfdy_sll_qty",
                "thdt_buyqty",
                "thdt_sll_qty",
                "loan_amt",
                "loan_dt",
                "expd_dt",
                "fltt_rt",
            ],
            # 주식 시세 관련
            "stock_price": [
                "stck_prpr",
                "prdy_vrss",
                "prdy_vrss_sign",
                "prdy_ctrt",
                "stck_oprc",
                "stck_hgpr",
                "stck_lwpr",
                "acml_vol",
                "acml_tr_pbmn",
                "ssts_yn",
                "stck_fcam",
                "stck_sspr",
                "hts_avls",
            ],
            # 일별 시세
            "daily_price": [
                "stck_bsop_date",
                "stck_oprc",
                "stck_hgpr",
                "stck_lwpr",
                "stck_clpr",
                "acml_vol",
                "prdy_vrss_vol_rate",
                "prdy_vrss",
                "prdy_vrss_sign",
                "prdy_ctrt",
                "hts_frgn_ehrt",
                "frgn_ntby_qty",
            ],
            # 분봉 데이터
            "minute_price": [
                "stck_bsop_date",
                "stck_cntg_hour",
                "stck_prpr",
                "stck_oprc",
                "stck_hgpr",
                "stck_lwpr",
                "cntg_vol",
                "acml_tr_pbmn",
            ],
            # 거래원 데이터
            "member_data": [
                "total_shnu_qty1",
                "total_shnu_qty2",
                "total_shnu_qty3",
                "total_shnu_qty4",
                "total_shnu_qty5",
                "total_seln_qty1",
                "total_seln_qty2",
                "total_seln_qty3",
                "total_seln_qty4",
                "total_seln_qty5",
            ],
            # 투자자별 매매 동향
            "investor_data": [
                "prsn_ntby_qty",
                "prsn_ntby_tr_pbmn",
                "frgn_ntby_qty",
                "frgn_ntby_tr_pbmn",
                "orgn_ntby_qty",
                "orgn_ntby_tr_pbmn",
            ],
            # 호가 데이터
            "orderbook": [
                "askp1",
                "askp2",
                "askp3",
                "askp4",
                "askp5",
                "askp6",
                "askp7",
                "askp8",
                "askp9",
                "askp10",
                "bidp1",
                "bidp2",
                "bidp3",
                "bidp4",
                "bidp5",
                "bidp6",
                "bidp7",
                "bidp8",
                "bidp9",
                "bidp10",
                "askp_rsqn1",
                "askp_rsqn2",
                "askp_rsqn3",
                "askp_rsqn4",
                "askp_rsqn5",
                "bidp_rsqn1",
                "bidp_rsqn2",
                "bidp_rsqn3",
                "bidp_rsqn4",
                "bidp_rsqn5",
                "total_askp_rsqn",
                "total_bidp_rsqn",
            ],
            # 체결강도 및 순위
            "volume_power": [
                "hts_kor_isnm",
                "mksc_shrn_iscd",
                "stck_prpr",
                "prdy_vrss",
                "prdy_vrss_sign",
                "prdy_ctrt",
                "acml_vol",
                "stck_vol_rlrt",
                "vol_tnrt",
            ],
            # 프로그램 매매
            "program_trade": ["stck_bsop_date", "pgtr_ntby_qty", "pgtr_ntby_tr_pbmn"],
        }

    def _safe_numeric_convert(self, value):
        """문자열을 안전하게 숫자로 변환하는 헬퍼 함수"""
        if pd.isna(value) or value == "" or value is None:
            return 0

        try:
            str_value = str(value).strip()
            if str_value == "":
                return 0

            # 소수점이 있는지 확인
            if "." in str_value:
                float_val = float(str_value)
                # 00.0000 형태의 정수는 int로 변환
                if float_val == int(float_val):
                    return int(float_val)
                else:
                    return float_val
            else:
                return int(str_value)

        except (ValueError, TypeError):
            # 변환 실패 시 원래 값 반환
            return value

    def _convert_numeric_fields(
        self, df: pd.DataFrame, field_type: str = None
    ) -> pd.DataFrame:
        """DataFrame의 숫자형 필드들을 자동 변환"""
        if df.empty:
            return df

        # 필드 타입이 지정되지 않은 경우 모든 필드에서 숫자형으로 보이는 것들을 찾음
        if field_type is None:
            numeric_fields = []
            for col in df.columns:
                # 컬럼명에 qty, amt, prc, vol, rate 등이 포함된 경우 숫자형으로 간주
                if any(
                    keyword in col.lower()
                    for keyword in [
                        "qty",
                        "amt",
                        "prc",
                        "vol",
                        "rate",
                        "pbmn",
                        "prpr",
                        "vrss",
                        "ctrt",
                    ]
                ):
                    numeric_fields.append(col)
        else:
            # 지정된 필드 타입의 숫자형 필드들 사용
            numeric_fields = self.numeric_field_mappings.get(field_type, [])

        df_copy = df.copy()

        for field in numeric_fields:
            if field in df_copy.columns:
                df_copy[field] = df_copy[field].apply(self._safe_numeric_convert)

        return df_copy

    def _add_response_metadata(self, df: pd.DataFrame, response: dict) -> pd.DataFrame:
        """DataFrame에 API 응답 메타데이터 추가"""
        df["rt_cd"] = response.get("rt_cd", "")
        df["msg_cd"] = response.get("msg_cd", "")
        df["msg1"] = response.get("msg1", "")
        return df

    @api_method("API 요청 (Dict)", reraise=True)
    def _make_request_dict(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        method: str = "GET",
    ) -> Optional[Dict]:
        """
        API 요청 후 rt_cd 메타데이터를 포함한 Dict 반환

        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID
            params: 요청 파라미터
            use_cache: 캐시 사용 여부 (기본: True)
            cache_ttl: 캐시 TTL (초), None인 경우 엔드포인트별 기본값 사용
            method: HTTP 메서드 (기본: GET, 주문 API는 POST 사용)

        Returns:
            rt_cd 메타데이터가 포함된 Dict 응답
        """
        # 캐시 사용 여부 확인
        if use_cache and self.cache:
            # 캐시 키 생성
            cache_key = self.cache._make_key(
                {"endpoint": endpoint, "tr_id": tr_id, "params": params}
            )

            # 캐시 조회
            cached_value = self.cache.get(cache_key)
            if cached_value is not None:
                # 캐시 히트 시 _cached 플래그 추가
                cached_value["_cached"] = True
                return cached_value

        response = self.client.make_request(
            endpoint=endpoint, tr_id=tr_id, params=params, method=method
        )

        if not response:
            return None

        # 성공 응답을 캐시에 저장
        if use_cache and self.cache and response.get("rt_cd") == "0":
            # TTL 결정 (지정값 또는 엔드포인트별 기본값)
            ttl = (
                cache_ttl
                if cache_ttl is not None
                else self.cache.get_ttl_for_endpoint(endpoint)
            )
            cache_key = self.cache._make_key(
                {"endpoint": endpoint, "tr_id": tr_id, "params": params}
            )
            self.cache.set(cache_key, response, ttl)

        # Dict 응답에 rt_cd 메타데이터가 이미 포함되어 있음
        return response

    @api_method("API 요청 (DataFrame)", reraise=True)
    def _make_request_dataframe(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict,
        retries: int = 5,
        field_type: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """기존 메서드와 호환성 유지하면서 숫자형 변환 추가"""
        # 캐시 사용 여부 확인
        if use_cache and self.cache:
            # 캐시 키 생성
            cache_key = self.cache._make_key(
                {
                    "endpoint": endpoint,
                    "tr_id": tr_id,
                    "params": params,
                    "dataframe": True,
                }
            )

            # 캐시 조회
            cached_value = self.cache.get(cache_key)
            if cached_value is not None:
                # DataFrame으로 복원
                return cached_value

        # request_manager를 사용하여 DataFrame가져오기
        result = self.request_manager.make_request_with_processing(
            endpoint=endpoint,
            tr_id=tr_id,
            params=params,
            field_type=field_type,
            return_dataframe=True,
        )

        # 성공 응답을 캐시에 저장
        if use_cache and self.cache and result is not None and not result.empty:
            # TTL 결정 (지정값 또는 엔드포인트별 기본값)
            ttl = (
                cache_ttl
                if cache_ttl is not None
                else self.cache.get_ttl_for_endpoint(endpoint)
            )
            cache_key = self.cache._make_key(
                {
                    "endpoint": endpoint,
                    "tr_id": tr_id,
                    "params": params,
                    "dataframe": True,
                }
            )
            self.cache.set(cache_key, result, ttl)

        return result
