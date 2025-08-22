"""
베이스 API 클래스 - 공통 기능 제공

이 모듈은 모든 API 클래스들이 상속받을 베이스 클래스를 제공합니다:
- 공통 데이터 변환 로직
- 숫자형 필드 자동 변환
- DataFrame/Dict 반환 타입 통합
- API 응답 정규화
"""

import pandas as pd
from typing import Optional, Dict, List, Union
from .response_processor import APIRequestManager


class BaseAPI:
    """모든 API 클래스들의 공통 베이스 클래스"""

    def __init__(self, client, account_info=None):
        """
        BaseAPI 초기화

        Args:
            client: KISClient 인스턴스
            account_info: 계좌 정보 (필요한 경우)
        """
        self.client = client
        self.account = account_info

        # 각 API별 숫자형 필드 매핑 테이블
        self.numeric_field_mappings = self._get_numeric_field_mappings()
        
        # API 요청 관리자 초기화 (Factory Pattern)
        self.request_manager = APIRequestManager(
            client=client,
            metadata_adder=self._add_response_metadata,
            field_converter=self._convert_numeric_fields
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

    def _make_request_with_conversion(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict,
        field_type: Optional[str] = None,
        output_key: str = "output",
        return_dataframe: bool = True,
    ) -> Union[Optional[pd.DataFrame], Optional[Dict]]:
        """
        API 요청 후 자동으로 숫자형 변환을 적용하여 DataFrame 반환
        
        복잡도 개선: Factory Pattern으로 응답 처리 로직 위임

        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID
            params: 요청 파라미터
            field_type: 숫자형 필드 매핑에 사용할 타입
            output_key: 응답에서 데이터를 추출할 키 (기본값: 'output')
            return_dataframe: DataFrame 반환 여부 (False면 Dict 반환)

        Returns:
            변환된 DataFrame 또는 Dict
        """
        return self.request_manager.make_request_with_processing(
            endpoint=endpoint,
            tr_id=tr_id,
            params=params,
            field_type=field_type,
            return_dataframe=return_dataframe
        )

    def _make_request_dict(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict,
    ) -> Optional[Dict]:
        """
        API 요청 후 rt_cd 메타데이터를 포함한 Dict 반환

        Args:
            endpoint: API 엔드포인트
            tr_id: 거래 ID
            params: 요청 파라미터

        Returns:
            rt_cd 메타데이터가 포함된 Dict 응답
        """
        try:
            response = self.client.make_request(
                endpoint=endpoint, tr_id=tr_id, params=params
            )

            if not response:
                return None

            # Dict 응답에 rt_cd 메타데이터가 이미 포함되어 있음
            return response
        except Exception as e:
            import logging
            logging.error(f"API 요청 실패 - TR_ID: {tr_id}, Endpoint: {endpoint}, Error: {e}")
            raise Exception(f"API 요청 실패 - TR_ID: {tr_id}, Endpoint: {endpoint}, Error: {e}") from e

    def _make_request_dataframe(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict,
        retries: int = 5,
        field_type: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """기존 메서드와 호환성 유지하면서 숫자형 변환 추가"""
        try:
            return self._make_request_with_conversion(
                endpoint=endpoint,
                tr_id=tr_id,
                params=params,
                field_type=field_type,
                return_dataframe=True,
            )
        except Exception as e:
            import logging
            logging.error(f"DataFrame API 요청 실패 - TR_ID: {tr_id}, Endpoint: {endpoint}, Error: {e}")
            raise Exception(f"DataFrame API 요청 실패 - TR_ID: {tr_id}, Endpoint: {endpoint}, Error: {e}") from e
