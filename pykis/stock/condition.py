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
- (전략 관련 모듈은 deprecated되어 제거됨)

사용 예시:
    >>> client = KISClient()
    >>> condition = ConditionAPI(client)
    >>> stocks = condition.get_condition_stocks("user123")
"""

import logging
from typing import Dict, List, Optional, Any
from ..core.client import KISClient, API_ENDPOINTS

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

    def get_condition_stocks(self, user_id: str = "unohee", seq: int = 0, tr_cont: str = 'N') -> Optional[List[Dict]]:
        """
        조건검색 결과를 조회합니다.
        
        Args:
            user_id (str): 사용자 ID (기본값: "unohee")
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
            - rt_cd가 '1'인 경우 "조회가 계속 됩니다"는 정상적인 응답입니다.

        Example:
            >>> api.get_condition_stocks("unohee", seq=0)
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
                tr_id="HHKST03900400",
                params=params
            )
            
            if not response:
                logging.error("조건검색 응답이 없습니다.")
                return None
                
            rt_cd = response.get('rt_cd')
            if rt_cd == '0':
                # 정상 응답
                stocks = response.get('output2', [])
                if not stocks:
                    logging.warning("조건검색 결과가 없습니다.")
                    return None
                    
                logging.info(f"조건검색 결과: {len(stocks)}개 종목")
                return stocks
            elif rt_cd == '1':
                # "조회가 계속 됩니다" - 정상적인 응답이지만 추가 조회 필요
                logging.info("조건검색 조회가 계속됩니다. 다음 seq로 조회하세요.")
                stocks = response.get('output2', [])
                return stocks if stocks else []
            else:
                logging.error(f"조건검색 실패: rt_cd={rt_cd}, msg={response.get('msg1', '')}")
                return None
            
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

def get_condition_stocks_dict(agent) -> Dict[str, List[Dict]]:
    """조건검색식 종목 목록을 딕셔너리로 반환합니다.
    
    Args:
        agent: pykis.Agent 인스턴스
        
    Returns:
        dict: {조건검색식명: [종목정보리스트]} 형태의 딕셔너리
    """
    try:
        # Agent를 통한 조건검색 결과 조회
        stocks = agent.get_condition_stocks("unohee", seq=0, tr_cont="N")
        
        if not stocks:
            logging.warning("조건검색식 종목 조회 실패")
            return {}
            
        # condition API에서 직접 리스트를 반환하므로 바로 사용
        stock_list = stocks
            
        if not stock_list:
            logging.warning("조건검색식 종목이 없습니다.")
            return {}
        
        # StockMonitor.py에서 기대하는 형태로 변환
        # {조건검색식명: [종목정보리스트]} 형태
        condition_stocks = {
            "기본조건검색식": []  # 기본 조건검색식으로 설정
        }
        
        for stock in stock_list:
            code = stock.get('code', '')
            name = stock.get('name', '')
            if code and name:  # 코드와 이름이 모두 있는 경우만 추가
                stock_info = {
                    'code': code,
                    'name': name,
                    '종목코드': code,
                    '종목명': name
                }
                condition_stocks["기본조건검색식"].append(stock_info)
                
        return condition_stocks
        
    except Exception as e:
        logging.error(f"조건검색식 종목 조회 중 오류 발생: {e}")
        return {} 
