"""
한국투자증권 API의 관심종목 기능을 제공하는 모듈입니다.

이 모듈은 한국투자증권 OpenAPI를 통해 다음 기능을 제공합니다:
- 관심종목 그룹 목록 조회
- 관심종목 그룹별 종목 조회

의존성:
- kis.core.client.KISClient: API 통신을 담당하는 클라이언트

연관 모듈:
- kis.stock: 주식 시세 및 주문 처리
- kis.stock.condition: 조건검색 기능

사용 예시:
    >>> client = KISClient()
    >>> interest = InterestStockAPI(client)
    >>> groups = interest.get_interest_group_list("unohee")
    >>> stocks = interest.get_interest_stock_list("unohee", "001")
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS, KISClient
from ..core.exceptions import api_method


class InterestStockAPI(BaseAPI):
    """
    관심종목 API 기능을 제공하는 클래스입니다.

    이 클래스는 관심종목 그룹 및 종목을 조회하는 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신을 담당하는 클라이언트

    Example:
        >>> client = KISClient()
        >>> interest = InterestStockAPI(client)
        >>> groups = interest.get_interest_group_list("unohee")
    """

    def __init__(
        self,
        client: KISClient,
        account_info=None,
        enable_cache=True,
        cache_config=None,
        _from_agent: bool = False,
    ):
        """
        InterestStockAPI를 초기화합니다.

        Args:
            client (KISClient): API 통신을 담당하는 클라이언트
            account_info (dict, optional): 계좌 정보
            enable_cache (bool, optional): 캐시 사용 여부. 기본값은 True.
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부 (내부 사용)

        Example:
            >>> client = KISClient()
            >>> api = InterestStockAPI(client)
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    @api_method("관심종목 그룹 목록 조회")
    def get_interest_group_list(
        self,
        user_id: str,
        type_code: str = "1",
        fid_etc_cls_code: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """
        관심종목 그룹 목록을 조회합니다.

        Args:
            user_id (str): 사용자 ID
            type_code (str, optional): 타입 코드. 기본값은 "1".
            fid_etc_cls_code (str, optional): 기타 구분 코드. 기본값은 "00".

        Returns:
            Optional[Dict[str, Any]]: 관심종목 그룹 목록
                - 성공 시: 관심종목 그룹 정보를 포함한 딕셔너리
                - 실패 시: None

        Note:
            - API 응답은 rt_cd, msg_cd, msg1을 포함합니다.
            - 그룹 목록은 'output' 키에 포함됩니다.

        Example:
            >>> api.get_interest_group_list("unohee")
        """
        # API 요청 파라미터
        params = {
            "TYPE": type_code,
            "FID_ETC_CLS_CODE": fid_etc_cls_code,
            "USER_ID": user_id,
        }

        # API 호출
        response = self.client.make_request(
            endpoint=API_ENDPOINTS["INTEREST_GROUP_LIST"],
            tr_id="HHKCM113004C7",
            params=params,
        )

        if not response:
            self._log_warning("관심종목 그룹 목록 조회 응답이 없습니다.")
            return None

        rt_cd = response.get("rt_cd")
        if rt_cd == "0":
            self._log_info("관심종목 그룹 목록 조회 성공")
            return response
        else:
            self._log_warning(
                f"관심종목 그룹 목록 조회 실패: rt_cd={rt_cd}, msg={response.get('msg1', '')}"
            )
            return None

    @api_method("관심종목 그룹별 종목 조회")
    def get_interest_stock_list(
        self,
        user_id: str,
        inter_grp_code: str,
        type_code: str = "1",
        data_rank: str = "",
        inter_grp_name: str = "",
        hts_kor_isnm: str = "",
        cntg_cls_code: str = "",
        fid_etc_cls_code: str = "4",
    ) -> Optional[Dict[str, Any]]:
        """
        관심종목 그룹별 종목 목록을 조회합니다.

        Args:
            user_id (str): 사용자 ID
            inter_grp_code (str): 관심종목 그룹 코드 (예: "001")
            type_code (str, optional): 타입 코드. 기본값은 "1".
            data_rank (str, optional): 데이터 순위. 기본값은 "".
            inter_grp_name (str, optional): 관심종목 그룹명. 기본값은 "".
            hts_kor_isnm (str, optional): HTS 한글 종목명. 기본값은 "".
            cntg_cls_code (str, optional): 체결 구분 코드. 기본값은 "".
            fid_etc_cls_code (str, optional): 기타 구분 코드. 기본값은 "4".

        Returns:
            Optional[Dict[str, Any]]: 관심종목 그룹별 종목 목록
                - 성공 시: 종목 정보를 포함한 딕셔너리
                    - output1: 그룹 정보
                    - output2: 종목 목록 (리스트)
                - 실패 시: None

        Note:
            - API 응답 output2는 다음 필드를 포함합니다:
                - fid_mrkt_cls_code: 시장 구분 코드
                - data_rank: 데이터 순위
                - exch_code: 거래소 코드
                - jong_code: 종목 코드
                - color_code: 색상 코드
                - memo: 메모
                - hts_kor_isnm: 종목명
                - fxdt_ntby_qty: 고정일 순매수량
                - cntg_unpr: 체결 단가
                - cntg_cls_code: 체결 구분 코드

        Example:
            >>> api.get_interest_stock_list("unohee", "001")
        """
        # API 요청 파라미터
        params = {
            "TYPE": type_code,
            "USER_ID": user_id,
            "DATA_RANK": data_rank,
            "INTER_GRP_CODE": inter_grp_code,
            "INTER_GRP_NAME": inter_grp_name,
            "HTS_KOR_ISNM": hts_kor_isnm,
            "CNTG_CLS_CODE": cntg_cls_code,
            "FID_ETC_CLS_CODE": fid_etc_cls_code,
        }

        # API 호출
        response = self.client.make_request(
            endpoint=API_ENDPOINTS["INTEREST_STOCK_LIST"],
            tr_id="HHKCM113004C6",
            params=params,
        )

        if not response:
            self._log_warning("관심종목 그룹별 종목 조회 응답이 없습니다.")
            return None

        rt_cd = response.get("rt_cd")
        if rt_cd == "0":
            stocks = response.get("output2", [])
            self._log_info(f"관심종목 그룹별 종목 조회 성공: {len(stocks)}개 종목")
            return response
        else:
            self._log_warning(
                f"관심종목 그룹별 종목 조회 실패: rt_cd={rt_cd}, msg={response.get('msg1', '')}"
            )
            return None
