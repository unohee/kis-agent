"""
한국투자증권 API의 조건검색 기능을 제공하는 모듈입니다.

이 모듈은 한국투자증권 OpenAPI를 통해 다음 기능을 제공합니다:
- 조건검색 결과 조회
- 조건검색 시퀀스 관리
- 조건검색 결과 필터링

의존성:
- kis.core.client.KISClient: API 통신을 담당하는 클라이언트

연관 모듈:
- kis.stock: 주식 시세 및 주문 처리
- kis.account: 계좌 정보 관리
- kis.strategy: 전략 실행 및 모니터링

사용 예시:
    >>> client = KISClient()
    >>> condition = ConditionAPI(client)
    >>> stocks = condition.get_condition_stocks("user123")
"""

import logging
from typing import Dict, List, Optional, Any
from core.client import KISClient, API_ENDPOINTS

class ConditionAPI:
    """
    조건검색 API 기능을 제공하는 클래스입니다.

    이 클래스는 조건검색 결과를 조회하고 관리하는 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신을 담당하는 클라이언트

    Example:
        >>> client = KISClient()
        >>> condition = ConditionAPI(client)
        >>> stocks = condition.get_condition_stocks("user123")
    """
    
    def __init__(self, client: KISClient):
        """
        ConditionAPI를 초기화합니다.

        Args:
            client (KISClient): API 통신을 담당하는 클라이언트

        Example:
            >>> client = KISClient()
            >>> api = ConditionAPI(client)
        """
        self.client = client

    def get_condition_stocks(self, user_id: str, seq: int = 0, tr_cont: str = 'N') -> Optional[List[Dict]]:
        """
        조건검색 결과를 조회합니다.
        
        Args:
            user_id (str): 사용자 ID
            seq (int, optional): 조건검색 시퀀스 번호. 기본값은 0.
            tr_cont (str, optional): 연속조회 여부. 기본값은 'N'.
                - 'N': 연속조회 아님
                - 'Y': 연속조회
            
        Returns:
            Optional[List[Dict]]: 조건검색 결과 리스트
                - 성공 시: 조건검색 결과를 포함한 리스트
                - 실패 시: None

        Note:
            - 조건검색 결과가 없는 경우 None을 반환합니다.
            - API 호출 실패 시 로그에 오류가 기록됩니다.

        Example:
            >>> api.get_condition_stocks("user123", seq=1)
        """
        try:
            # API 요청 파라미터
            params = {
                "user_id": user_id,
                "seq": seq,
                "tr_cont": tr_cont
            }
            
            # API 호출
            response = self.client.make_request(
                endpoint=API_ENDPOINTS['CONDITIONED_STOCK'],
                tr_id="CTCA0903R",
                params=params
            )
            
            if not response or response.get('rt_cd') != '0':
                logging.error(f"조건검색 실패: {response}")
                return None
                
            # output2 필드에서 결과 추출
            stocks = response.get('output2', [])
            if not stocks:
                logging.warning("조건검색 결과가 없습니다.")
                return None
                
            logging.info(f"조건검색 결과: {len(stocks)}개 종목")
            return stocks
            
        except Exception as e:
            logging.error(f"조건검색 중 오류 발생: {e}")
            return None

    def get_condition_list(self) -> Optional[Dict[str, Any]]:
        """조건검색 목록 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-condition",
                tr_id="FHKST03010000",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "20171"
                }
            )
        except Exception as e:
            logging.error(f"조건검색 목록 조회 실패: {e}")
            return None

    def get_condition_result(self, condition_id: str) -> Optional[Dict[str, Any]]:
        """조건검색 결과 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-condition-result",
                tr_id="FHKST03010100",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "20171",
                    "FID_COND_ID": condition_id
                }
            )
        except Exception as e:
            logging.error(f"조건검색 결과 조회 실패: {e}")
            return None

    def save_condition(self, condition_name: str, condition_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조건검색 저장"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/save-condition",
                tr_id="FHKST03010200",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "20171",
                    "FID_COND_NAME": condition_name,
                    "FID_COND_DATA": condition_data
                }
            )
        except Exception as e:
            logging.error(f"조건검색 저장 실패: {e}")
            return None

    def delete_condition(self, condition_id: str) -> Optional[Dict[str, Any]]:
        """조건검색 삭제"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/delete-condition",
                tr_id="FHKST03010300",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "20171",
                    "FID_COND_ID": condition_id
                }
            )
        except Exception as e:
            logging.error(f"조건검색 삭제 실패: {e}")
            return None 