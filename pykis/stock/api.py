"""
agent_stock.py - 종목 단위 시세 조회 및 주문 전용 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음 기능을 제공합니다:
- 종목 현재가 조회
- 일별 시세 및 분봉 데이터 조회
- 호가 및 잔량 정보 조회
- 현금 주문 가능 여부 확인
- 지정가/시장가 주문 실행
- 시간외 단일가 정보 조회

✅ 의존:
- kis_core.KISClient: API 호출 실행기

🔗 연관 모듈:
- program_trade_api.py: 프로그램 매매 정보 필터링
- account_api.py: 잔고 및 주문 가능 금액 확인
- (전략 관련 모듈은 deprecated되어 제거됨)

💡 사용 예시:
client = KISClient()
account = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
stock = StockAPI(client, account)
price = stock.get_stock_price("005930")
"""

from typing import Optional, Dict, Any, List
# [변경 이유] pandas 로딩 시간 단축을 위해 필요한 메서드에서만 지역 import 사용
# import pandas as pd  # 지역 import로 변경
import logging
import pandas as pd
from ..core.client import KISClient, API_ENDPOINTS
from ..core.base_api import BaseAPI
from datetime import datetime, timedelta

def get_kospi200_futures_code(today: Optional[datetime] = None) -> str:
    """
    현재 날짜 기준으로 거래되고 있는 가장 활발한 KOSPI200 선물 종목코드를 반환합니다.
    
    KOSPI200 선물은 3, 6, 9, 12월 만기로 거래되며, 만기일은 매월 두 번째 주 목요일입니다.
    현재 날짜를 기준으로 가장 가까운 활성 선물 코드를 자동으로 계산합니다.
    
    Args:
        today (Optional[datetime]): 기준 날짜. None이면 현재 날짜 사용
        
    Returns:
        str: KOSPI200 선물 종목코드 (6자리, 예: "101W09")
        
    Example:
        >>> from pykis.stock.api import get_kospi200_futures_code
        >>> from datetime import datetime
        >>> 
        >>> # 현재 활성 선물 코드
        >>> current_code = get_kospi200_futures_code()
        >>> print(current_code)  # "101W09" (2025년 9월물)
        >>> 
        >>> # 특정 날짜 기준
        >>> specific_date = datetime(2025, 10, 1)
        >>> future_code = get_kospi200_futures_code(specific_date)
        >>> print(future_code)  # "101W12" (2025년 12월물)
        
    Note:
        - 종목코드 패턴: 101W + MM (MM: 03, 06, 09, 12)
        - 만기일: 매월 두 번째 주 목요일 (15:30 마감)
        - 만기일 지나면 자동으로 다음 만기월로 전환
        - 12월물 만기 후에는 다음해 3월물로 전환
    """
    if today is None:
        today = datetime.now()
    
    def get_second_thursday(year: int, month: int) -> datetime:
        """
        특정 년월의 두 번째 주 목요일 날짜를 반환
        
        Args:
            year (int): 연도
            month (int): 월 (1-12)
            
        Returns:
            datetime: 해당 월의 두 번째 주 목요일
        """
        # 해당 월의 첫 번째 날
        first_day = datetime(year, month, 1)
        # 첫 번째 목요일까지의 일수 (0=월요일, 3=목요일)
        days_until_first_thursday = (3 - first_day.weekday()) % 7
        # 첫 번째 목요일
        first_thursday = first_day + timedelta(days=days_until_first_thursday)
        # 두 번째 주 목요일 (7일 후)
        second_thursday = first_thursday + timedelta(days=7)
        return second_thursday
    
    expiry_months = [3, 6, 9, 12]
    current_year = today.year
    current_month = today.month
    
    # 현재 월이 만기월인지 확인
    if current_month in expiry_months:
        # 현재 월의 만기일 계산
        expiry_date = get_second_thursday(current_year, current_month)
        
        # 현재 날짜가 만기일을 지났는지 확인
        if today.date() > expiry_date.date():
            # 만기일을 지났으면 다음 만기월 찾기
            for i, month in enumerate(expiry_months):
                if month > current_month:
                    expiry = month
                    break
            else:
                # 현재 월이 12월인 경우 다음 해 3월물
                expiry = 3
        else:
            # 만기일이 지나지 않았으면 현재 월
            expiry = current_month
    else:
        # 현재 월이 만기월이 아닌 경우, 다음 만기월 찾기
        for month in expiry_months:
            if month > current_month:
                expiry = month
                break
        else:
            # 현재 월이 12월 이후인 경우 다음 해 3월물
            expiry = 3
    
    # 101W + MM 형태로 종목코드 생성 (MM은 2자리)
    return f"101W{expiry:02d}"

class StockAPI(BaseAPI):
    def __init__(self, client: KISClient, account_info: Dict[str, str]):
        super().__init__(client, account_info)

    def _make_request_dataframe(self, endpoint: str, tr_id: str, params: dict, retries: int = 5) -> Optional['pd.DataFrame']:
        """공통 요청 함수: 응답을 DataFrame으로 변환"""
        response = self.client.make_request(
            endpoint=endpoint,
            tr_id=tr_id,
            params=params,
            retries=retries
        )
        if response and response.get("rt_cd") == "0":
            import pandas as pd  # 지역 import로 로딩 시간 단축
            output = response.get("output", [])
            return pd.DataFrame([output]) if isinstance(output, dict) else pd.DataFrame(output)
        return None

    def get_stock_price(self, code: str) -> Optional[pd.DataFrame]:
        """주식 현재가 조회 (숫자형 자동 변환)"""
        return self._make_request_with_conversion(
            endpoint=API_ENDPOINTS['INQUIRE_PRICE'],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "UN", "FID_INPUT_ISCD": code},
            field_type='stock_price'
        )

    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[pd.DataFrame]:
        """
        일별 시세 조회 (숫자형 자동 변환)
        
        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미사용, 1: 수정주가 사용)
        """
        return self._make_request_with_conversion(
            endpoint=API_ENDPOINTS['INQUIRE_DAILY_ITEMCHARTPRICE'],
            tr_id="FHKST01010400",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_period_div_code": period,
                "fid_org_adj_prc": org_adj_prc
            },
            field_type='daily_price'
        )

    

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """
        주식 회원사 정보 조회 (Postman 검증된 방식) (rt_cd 메타데이터가 포함된)
        
        Args:
            ticker: 종목코드 (6자리)
            retries: 재시도 횟수
        """
        for attempt in range(retries):
            try:
                response = self._make_request_dict(
                    endpoint=API_ENDPOINTS['INQUIRE_MEMBER'],
                    tr_id="FHKST01010600",
                    params={
                        "FID_COND_MRKT_DIV_CODE": "UN",
                        "FID_INPUT_ISCD": ticker
                    }
                )
                
                if response and response.get('rt_cd') == '0':
                    return response
                elif response and response.get('rt_cd') != '0':
                    logging.warning(f"주식 회원사 조회 실패 (시도 {attempt+1}/{retries}): {response.get('msg1', '알 수 없는 오류')}")
                    if attempt < retries - 1:
                        continue
                    else:
                        return response
                else:
                    logging.error(f"주식 회원사 조회 응답 없음 (시도 {attempt+1}/{retries})")
                    if attempt < retries - 1:
                        continue
                    else:
                        return None
                        
            except Exception as e:
                logging.error(f"주식 회원사 조회 예외 발생 (시도 {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    continue
                else:
                    return None
        
        return None
    
    def get_stock_investor(self, ticker: str = '', retries: int = 10, force_refresh: bool = False) -> Optional['pd.DataFrame']:
        """투자자별 매매 동향 조회
        개인 순매수 수량 및 거래대금은 'prsn_ntby_qty', 'prsn_ntby_tr_pbmn' 필드 사용.
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "UN",
            "FID_INPUT_ISCD": ticker,
        }
        df = self._make_request_dataframe(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR'],
            tr_id="FHKST01010900",
            params=params,
            retries=retries
        )
        # 개인 투자자 정보 집계 예시 (필요시 DataFrame에서 바로 추출)
        if df is not None and not df.empty:
            # 'prsn_ntby_qty', 'prsn_ntby_tr_pbmn' 필드 사용
            try:
                if 'prsn_ntby_qty' in df.columns and 'prsn_ntby_tr_pbmn' in df.columns:
                    try:
                        indiv_qty_str = df['prsn_ntby_qty'].iloc[0]
                        indiv_pbmn_str = df['prsn_ntby_tr_pbmn'].iloc[0]
                        
                        # Convert empty strings to 0
                        indiv_qty = int(indiv_qty_str) if indiv_qty_str.strip() else 0
                        indiv_pbmn = int(indiv_pbmn_str) / 100000000 if indiv_pbmn_str.strip() else 0
                        
                        if not indiv_qty_str.strip() or not indiv_pbmn_str.strip():
                            logging.info("Empty string encountered for individual investor details, set to 0.")

                        df['개인_순매수수량'] = indiv_qty
                        df['개인_순매수거래대금_억'] = indiv_pbmn
                    except Exception as e:
                        logging.error(f"Error extracting individual investor details: {e}", exc_info=True)
            except Exception as e:
                logging.error(f"Error extracting individual investor details: {e}", exc_info=True)
        return df
        
    def estimate_accumulated_volume_by_top_members(self, stock_member_data: Dict[str, Any], force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        거래원 데이터에서 세력의 누적 매집량 추정 (항상 실시간 계산).
        상위 5개 매수/매도 창구의 총 매수/매도 수량을 이용하여
        net_accumulation을 (총매수 - 총매도)로 계산.
        """
        try:
            output = stock_member_data.get("output", {}) if isinstance(stock_member_data, dict) else stock_member_data
            buy_total_keys = [f"total_shnu_qty{i}" for i in range(1, 6)]
            sell_total_keys = [f"total_seln_qty{i}" for i in range(1, 6)]

            buy_total = sum(int(output.get(k, "0")) for k in buy_total_keys)
            sell_total = sum(int(output.get(k, "0")) for k in sell_total_keys)
            net = buy_total - sell_total

            total_buy = int(output.get("glob_total_seln_qty", "0"))
            total_sell = int(output.get("glob_total_shnu_qty", "0"))

            turnover_volume = buy_total + sell_total
            dominance_ratio = net / turnover_volume if turnover_volume > 0 else 0

            result = {
                "accumulated_buy_qty": buy_total,
                "accumulated_sell_qty": sell_total,
                "net_accumulation": net,
                "total_buy_qty": total_buy,
                "total_sell_qty": total_sell,
                "turnover_volume": turnover_volume,
                "dominance_ratio": round(dominance_ratio, 4)
            }
            return result
        except Exception as e:
            logging.error(f"Failed to estimate accumulated volume: {e}", exc_info=True)
            return None
    
    def get_orderbook_raw(self, code: str) -> Optional[Dict]:
        """
        실제 호가 정보 조회 (원본 데이터 반환)
        
        기존 get_orderbook과 달리 실제 호가 10단 정보를 포함한 원본 데이터를 반환합니다.
        
        Args:
            code: 종목코드
            
        Returns:
            Dict: 원본 API 응답 (output1에 호가 정보, output2에 현재가 정보)
                - output1: 호가 정보
                  - bidp1~bidp10: 매수호가 1~10단
                  - askp1~askp10: 매도호가 1~10단  
                  - bidp_rsqn1~bidp_rsqn10: 매수호가 잔량 1~10단
                  - askp_rsqn1~askp_rsqn10: 매도호가 잔량 1~10단
                  - total_bidp_rsqn: 총 매수호가 잔량
                  - total_askp_rsqn: 총 매도호가 잔량
                - output2: 현재가 정보
        """
        response = self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_ASKING_PRICE_EXP_CCN'],
            tr_id="FHKST01010200",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
        )
        
        if response and response.get('rt_cd') == '0':
            output1 = response.get('output1')  # 호가 정보
            output2 = response.get('output2')  # 현재가 정보
            
            if output1 and output2:
                return {
                    'rt_cd': response.get('rt_cd'),
                    'msg_cd': response.get('msg_cd'),
                    'msg1': response.get('msg1'),
                    'output1': output1,
                    'output2': output2
                }
            else:
                logging.warning(f"get_orderbook_raw: output1 또는 output2가 없음 for {code}")
                return None
        else:
            error_msg = response.get('msg1') if response else 'No response'
            rt_cd = response.get('rt_cd') if response else 'None'
            logging.warning(f"get_orderbook_raw: API 호출 실패 for {code} - rt_cd: {rt_cd}, msg: {error_msg}")
            return None
    
    def get_orderbook(self, code: str) -> Optional['pd.DataFrame']:
        """호가 및 예상체결 데이터 조회 (개선된 버전 - 각 호가단별 실제 거래대금 계산)"""
        # [변경 이유] get_orderbook은 deprecated 되었으며, get_orderbook_raw로 대체됩니다.
        logging.warning("get_orderbook is deprecated. Use get_orderbook_raw instead.")
        raw_data = self.get_orderbook_raw(code)
        
        if not raw_data:
            logging.error(f"get_orderbook: get_orderbook_raw 호출 실패 for {code}")
            return None
        
        try:
            output1 = raw_data.get('output1')  # 호가 정보
            output2 = raw_data.get('output2')  # 현재가 정보
            
            # 각 호가단별 실제 거래대금 계산
            total_ask_amount = 0  # 매도호가 총 거래대금
            total_bid_amount = 0  # 매수호가 총 거래대금
            
            # 매도호가 1~10단 계산 (askp1~askp10 × askp_rsqn1~askp_rsqn10)
            for i in range(1, 11):
                ask_price = float(output1.get(f'askp{i}', 0) or 0)
                ask_volume = int(output1.get(f'askp_rsqn{i}', 0) or 0)
                total_ask_amount += ask_price * ask_volume
            
            # 매수호가 1~10단 계산 (bidp1~bidp10 × bidp_rsqn1~bidp_rsqn10)
            for i in range(1, 11):
                bid_price = float(output1.get(f'bidp{i}', 0) or 0)
                bid_volume = int(output1.get(f'bidp_rsqn{i}', 0) or 0)
                total_bid_amount += bid_price * bid_volume
            
            # 기존 호환성을 위한 총 잔량 계산
            total_ask_volume = int(output1.get('total_askp_rsqn', 0) or 0)
            total_bid_volume = int(output1.get('total_bidp_rsqn', 0) or 0)
            
            # 총 거래대금 = 매도호가 거래대금 + 매수호가 거래대금
            total_amount = total_ask_amount + total_bid_amount
            
            # DataFrame 생성 (기존 호환성 유지하면서 새로운 정보 추가)
            df_dict = {
                '매도잔량': [total_ask_volume],
                '매수잔량': [total_bid_volume],
                '총거래대금': [total_amount],  # 🆕 실제 각 호가×잔량의 정확한 합계
                '매도거래대금': [total_ask_amount],  # 🆕 매도호가 거래대금
                '매수거래대금': [total_bid_amount],  # 🆕 매수호가 거래대금
                '현재가': [float(output2.get('stck_prpr', 0) or 0)],
                '시가': [float(output2.get('stck_oprc', 0) or 0)],
                '고가': [float(output2.get('stck_hgpr', 0) or 0)],
                '저가': [float(output2.get('stck_lwpr', 0) or 0)]
            }
            
            import pandas as pd  # 지역 import로 로딩 시간 단축
            return pd.DataFrame(df_dict)
            
        except (ValueError, TypeError, KeyError) as e:
            logging.error(f"get_orderbook: 데이터 파싱 오류 for {code}: {e}")
            return None

    def get_volume_power(self, volume: int = 0) -> Optional[pd.DataFrame]:
        """
        체결강도 순위 조회 (숫자형 자동 변환)
        
        Args:
            volume (int): 거래량 기준 (기본값: 0)
            
        Returns:
            Optional[pd.DataFrame]: 체결강도 순위 정보
        """
        try:
            # [변경 이유] Postman에서 확인된 올바른 체결강도 API 사용
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_cond_scr_div_code": "20168",
                "fid_input_iscd": "0000",
                "fid_div_cls_code": "0",
                "fid_input_price_1": "",
                "fid_input_price_2": "",
                "fid_vol_cnt": str(volume),
                "fid_trgt_exls_cls_code": "0",
                "fid_trgt_cls_code": "0"
            }
            
            return self._make_request_with_conversion(
                endpoint=API_ENDPOINTS['VOLUME_POWER'],
                tr_id="FHPST01680000",
                params=params,
                field_type='volume_power'
            )
        except Exception as e:
            logging.error(f"체결강도 순위 조회 실패: {e}")
            return None

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """국내주식 등락률 순위 조회 (rt_cd 메타데이터가 포함된)"""
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": "0",
            "fid_prc_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "3000000",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": "",
            "fid_rsfl_rate2": ""
        }
        response = self._make_request_dict(
            endpoint=API_ENDPOINTS['FLUCTUATION'],
            tr_id="FHPST01700000",
            params=params
        )
        return response

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 순위 조회 (rt_cd 메타데이터가 포함된)"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "UN",
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "1",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "0000011101",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": str(volume),
            "FID_INPUT_DATE_1": ""
        }
        response = self._make_request_dict(
            endpoint=API_ENDPOINTS['VOLUME_RANK'],
            tr_id="FHPST01710000",
            params=params
        )
        return response  # Return raw response for debugging

    def get_stock_info(self, ticker: str) -> Optional['pd.DataFrame']:
        """주식 기본 정보 조회"""
        response = self.client.make_request(
            endpoint=API_ENDPOINTS['SEARCH_STOCK_INFO'],
            tr_id="CTPF1002R",
            params={"PRDT_TYPE_CD": "300", "PDNO": ticker}
        )
        if response and response.get('rt_cd') == '0':
            output = response.get('output', {})
            import pandas as pd  # 지역 import로 로딩 시간 단축
            return pd.DataFrame([output]) if output else pd.DataFrame()
        return None

    def get_member_transaction(self, code: str, mem_code: str) -> Optional[Dict[str, Any]]:
        """회원사 일별 매매 종목 (rt_cd 메타데이터가 포함된)"""
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_input_iscd_2": mem_code,
            "fid_input_date_1": start_date,
            "fid_input_date_2": today,
            "fid_sctn_cls_code": ""
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_MEMBER_DAILY'],
            tr_id="FHPST04540000",
            params=params
        )

    def get_frgnmem_pchs_trend(self, code: str, date: str) -> Optional[Dict[str, Any]]:
        """
        종목별 외국계 순매수추이 조회 (날짜별 API) (rt_cd 메타데이터가 포함된)
        
        Args:
            code: 종목코드
            date: 조회일자 (YYYYMMDD)
            
        Returns:
            Dict: 외국계 순매수추이 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['FRGNMEM_PCHS_TREND'],
            tr_id="FHKST644400C0",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": date
            }
        )

    def get_foreign_broker_net_buy(self, code: str, foreign_brokers=None, date: str = None) -> Optional[tuple]:
        """
        거래원 정보를 활용해 외국계 증권사의 순매수(매수-매도) 합계를 집계합니다.
        
        Args:
            code: 종목코드
            foreign_brokers: 외국계 브로커명 리스트 (사용되지 않음, 자동 패턴 매칭)
            date: 조회일자(YYYYMMDD), None이면 당일, 특정 날짜면 해당 날짜 데이터 조회
            
        Returns:
            tuple: (순매수량, 상세정보 dict) 또는 None
                - 순매수량: 외국계 증권사 순매수량 (매수-매도)
                - 상세정보: {'brokers': [...], 'buy_total': int, 'sell_total': int}
        """
        from datetime import datetime
        
        # 날짜 파라미터가 있고 당일이 아닌 경우 외국계 순매수추이 API 사용
        if date and date != datetime.now().strftime('%Y%m%d'):
            return self._get_foreign_broker_historical(code, date)
        
        # 당일인 경우 기존 거래원 정보 방식 사용
        return self._get_foreign_broker_current(code, date)
    
    def _get_foreign_broker_historical(self, code: str, date: str) -> Optional[tuple]:
        """과거 날짜의 외국인 순매수 조회 (투자자별 매매 동향 기반)"""
        try:
            # get_stock_investor로 30일간 외국인 매매 데이터 조회
            investor_df = self.get_stock_investor(ticker=code)
            
            if investor_df is None or investor_df.empty:
                logging.warning(f"[{code}] 투자자별 매매 동향 데이터 조회 실패")
                return None
            
            # 해당 날짜 데이터 찾기
            target_data = investor_df[investor_df['stck_bsop_date'] == date]
            
            if target_data.empty:
                logging.warning(f"[{code}] {date} 날짜 데이터 없음 (최근 30일 범위 내에서만 조회 가능)")
                # 사용 가능한 날짜 범위 표시
                available_dates = investor_df['stck_bsop_date'].tolist()
                logging.info(f"[{code}] 사용 가능한 날짜: {available_dates[0]} ~ {available_dates[-1]}")
                return None
            
            # 외국인 매매 데이터 추출
            row = target_data.iloc[0]
            frgn_ntby_qty = int(row.get('frgn_ntby_qty', 0)) if row.get('frgn_ntby_qty') else 0
            frgn_buy_vol = int(row.get('frgn_shnu_vol', 0)) if row.get('frgn_shnu_vol') else 0
            frgn_sell_vol = int(row.get('frgn_seln_vol', 0)) if row.get('frgn_seln_vol') else 0
            
            details = {
                'brokers': [],  # 과거 날짜는 개별 거래원 정보 없음
                'buy_total': frgn_buy_vol,
                'sell_total': frgn_sell_vol,
                'total_brokers_found': 0,
                'query_date': date,
                'note': '투자자별 매매 동향 기반 외국인 전체 순매수 (과거 날짜)',
                'api_method': 'stock_investor',
                'data_range': f"{investor_df['stck_bsop_date'].iloc[0]} ~ {investor_df['stck_bsop_date'].iloc[-1]}"
            }
            
            logging.info(f"[{code}] {date} 외국인 순매수: {frgn_ntby_qty:,}주 (매수: {frgn_buy_vol:,}, 매도: {frgn_sell_vol:,})")
            return frgn_ntby_qty, details
            
        except Exception as e:
            logging.error(f"[{code}] 과거 날짜 외국인 순매수 조회 실패 ({date}): {e}")
            return None
    
    def _get_foreign_broker_current(self, code: str, date: str = None) -> Optional[tuple]:
        """당일 외국계 증권사 순매수 조회 (거래원 정보 기반)"""
        # 외국계 증권사 패턴 (실제 거래원명에서 확인된 것들)
        foreign_patterns = [
            'JP모간', '모간스탠리', '모건스탠리', '모간증권',
            '골드만', '골드만삭스', 
            '메릴린치', '메릴',
            'UBS', 'UBS코리아',
            'CS증권', '크레디트',
            'BNP', 'BNP파리바',
            'HSBC', 'HSBC증권',
            '도이치', '도이치은행',
            '노무라', '노무라증권',
            '다이와', '다이와증권',
            '씨티그룹', '씨티',
            '바클레이', '바클레이즈'
        ]
        
        # 거래원 정보 조회
        member_data = self.get_member(code)
        if not member_data or 'output' not in member_data:
            logging.warning(f"[{code}] 거래원 정보 조회 실패")
            return None
        
        output = member_data['output']
        
        # 외국계 증권사 매수/매도 집계
        foreign_buy_total = 0
        foreign_sell_total = 0
        foreign_brokers_found = []
        
        # 매수 거래원 확인 (상위 5개)
        for i in range(1, 6):
            broker_name = output.get(f'shnu_mbcr_name{i}', '')
            volume = int(output.get(f'total_shnu_qty{i}', 0))
            
            # 외국계 증권사 패턴 매칭
            is_foreign = any(pattern in broker_name for pattern in foreign_patterns)
            if is_foreign and volume > 0:
                foreign_buy_total += volume
                foreign_brokers_found.append({
                    'name': broker_name,
                    'type': 'buy',
                    'volume': volume,
                    'rank': i
                })
        
        # 매도 거래원 확인 (상위 5개)
        for i in range(1, 6):
            broker_name = output.get(f'seln_mbcr_name{i}', '')
            volume = int(output.get(f'total_seln_qty{i}', 0))
            
            # 외국계 증권사 패턴 매칭
            is_foreign = any(pattern in broker_name for pattern in foreign_patterns)
            if is_foreign and volume > 0:
                foreign_sell_total += volume
                foreign_brokers_found.append({
                    'name': broker_name,
                    'type': 'sell',
                    'volume': volume,
                    'rank': i
                })
        
        net_buy = foreign_buy_total - foreign_sell_total
        
        # 상세 정보 구성
        details = {
            'brokers': foreign_brokers_found,
            'buy_total': foreign_buy_total,
            'sell_total': foreign_sell_total,
            'total_brokers_found': len(foreign_brokers_found),
            'query_date': date or 'today',
            'note': '거래원 정보 기반 외국계 증권사 순매수 (상위 5개 매수/매도 거래원 분석)',
            'api_method': 'member'
        }
        
        # 로그 출력
        if foreign_brokers_found:
            logging.info(f"[{code}] 외국계 증권사 {len(foreign_brokers_found)}개 발견, 순매수: {net_buy:,}주 (매수: {foreign_buy_total:,}, 매도: {foreign_sell_total:,})")
        else:
            logging.info(f"[{code}] 상위 5개 거래원에 외국계 증권사 없음")
        
        return net_buy, details

    def get_pbar_tratio(self, code: str, retries: int = 10) -> Optional[dict]:
        """매물대/거래비중 조회 (rt_cd 메타데이터가 포함된)"""
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_cond_scr_div_code": "20113",
            "fid_input_hour_1": "",
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['PBAR_TRATIO'],
            tr_id="FHPST01130000",
            params=params
        )

    def get_hourly_conclusion(self, code: str, hour: str = "115959", retries: int = 10) -> Optional[dict]:
        """시간대별 체결 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code: 종목코드 (6자리)
            hour: 기준시간-이전체결처리 (6자리, HHMMSS 형식, 기본값: 115959)
            retries: 재시도 횟수
            
        Returns:
            Optional[dict]: 시간대별 체결 정보
        """
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_input_hour_1": hour,
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_ITEMCONCLUSION'],
            tr_id="FHPST01060000",
            params=params,
            retries=retries
        )

    def get_stock_ccnl(self, code: str, retries: int = 10) -> Optional[dict]:
        """주식현재가 체결(최근30건) 조회 (rt_cd 메타데이터가 포함된)
        
        최근 30건의 체결 내역과 함께 당일 체결강도(tday_rltv)를 포함한 상세한 체결 정보를 제공합니다.
        
        Args:
            code: 종목코드 (6자리)
            retries: 재시도 횟수
            
        Returns:
            Optional[dict]: 최근 30건 체결 내역
                - output: 체결 내역 리스트 (30건)
                  - stck_cntg_hour: 체결시간
                  - stck_prpr: 체결가격  
                  - prdy_vrss: 전일대비
                  - prdy_ctrt: 등락률
                  - tday_rltv: 당일 체결강도 ★
                  - cntg_vol: 체결량
                  - acml_vol: 누적거래량
                  - askp: 매도호가
                  - bidp: 매수호가
                  - cnqn: 체결건수
        """
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_CCNL'],
            tr_id="FHKST01010300",
            params=params,
            retries=retries
        )

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """
        분봉 데이터 조회 (주식당일분봉조회) (rt_cd 메타데이터가 포함된)
        
        Args:
            code: 종목코드
            hour: 시간 (HHMMSS 형식, 기본값: 153000)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_ITEMCHARTPRICE'],
            tr_id="FHKST03010200",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": "Y"
            }
        )

    def get_daily_minute_price(self, code: str, date: str, hour: str = "153000") -> Optional[Dict]:
        """
        일별분봉시세조회 - 과거일자 분봉 데이터 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            date (str): 조회 날짜 (YYYYMMDD 형식)
            hour (str): 조회 시간 (HHMMSS 형식, 기본값: 153000)
            
        Returns:
            Optional[Dict]: 일별분봉시세 데이터
            
        Note:
            - 실전계좌의 경우 한 번의 호출에 최대 120건까지 조회 가능
            - 과거 최대 1년까지의 분봉 데이터 조회 가능
            - 당사 서버에 보관된 데이터만 조회 가능
        """
        # [변경 이유] 한국투자증권 새로운 일별분봉시세조회 API 추가
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_DAILYCHARTPRICE'],
            tr_id="FHKST03010230",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": "Y",
                "FID_INPUT_DATE_1": date,
                "FID_FAKE_TICK_INCU_YN": ""
            }
        )

    def get_full_day_minute_price(self, code: str, date: str) -> Optional[Dict]:
        """
        하루 전체 분봉시세조회 - 4번 호출로 하루 전체 분봉 데이터 수집
        
        Args:
            code (str): 종목코드 (6자리)
            date (str): 조회 날짜 (YYYYMMDD 형식)
            
        Returns:
            Optional[Dict]: 하루 전체 분봉시세 데이터
            
        Note:
            - 9시부터 15시30분까지 전체 분봉 데이터 수집
            - 4번의 API 호출로 최대 480건 분봉 수집
            - 시간 순서로 정렬되어 반환
        """
        # [변경 이유] 하루 전체 분봉 데이터 수집을 위해 4번 호출하여 합치는 메서드 추가
        import time
        
        # 4번 호출할 시간 기준점 설정 (HHMMSS 형식)
        time_points = ["090000", "110000", "130000", "153000"]
        
        all_minute_data = []
        output1_data = None
        
        for i, hour in enumerate(time_points):
            try:
                # API 호출 간 간격을 두어 서버 부하 방지
                if i > 0:
                    time.sleep(0.1)
                
                result = self.get_daily_minute_price(code, date, hour)
                
                if result and result.get('rt_cd') == '0':
                    # 첫 번째 호출에서 output1 데이터 저장
                    if output1_data is None:
                        output1_data = result.get('output1', {})
                    
                    # output2의 분봉 데이터 수집
                    minute_data = result.get('output2', [])
                    if minute_data:
                        all_minute_data.extend(minute_data)
                        
            except Exception as e:
                logging.warning(f"시간 {hour} 분봉 조회 중 오류 발생: {e}")
                continue
        
        # 시간 순서로 정렬 (최신 시간이 앞에 오도록)
        all_minute_data.sort(key=lambda x: x.get('stck_cntg_hour', '000000'), reverse=True)
        
        # 중복 제거 (같은 시간의 분봉이 있을 경우)
        seen_hours = set()
        unique_minute_data = []
        for data in all_minute_data:
            hour_key = data.get('stck_cntg_hour', '')
            if hour_key not in seen_hours:
                seen_hours.add(hour_key)
                unique_minute_data.append(data)
        
        # 최종 결과 반환
        return {
            'output1': output1_data or {},
            'output2': unique_minute_data,
            'rt_cd': '0',
            'msg_cd': 'MCA00000',
            'msg1': f'하루 전체 분봉 데이터 수집 완료 (총 {len(unique_minute_data)}건)'
        }

    def get_possible_order(self, code: str, price: str, order_type: str = "01") -> Optional[Dict[str, Any]]:
        """매수 가능 주문 조회 (rt_cd 메타데이터가 포함된)"""
        if not self.account:
            logging.error("계좌 정보가 없습니다.")
            return None
        
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_PSBL_ORDER'],
            tr_id="TTTC8908R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "PDNO": code,
                "ORD_UNPR": price,
                "ORD_DVSN": order_type,
                "CMA_EVLU_AMT_ICLD_YN": "Y",
                "OVRS_ICLD_YN": "Y"
            }
        )

    def get_holiday_info(self, date: Optional[str] = None) -> Optional[Dict]:
        """국내 휴장일 정보를 조회합니다. (rt_cd 메타데이터가 포함된)
        
        Args:
            date (str, optional): YYYYMMDD 형식의 기준 날짜. Defaults to None.
        
        Returns:
            Dict: 휴장일 정보, 실패 시 None
        """
        import logging
        params = {'CTX_AREA_NK': '', 'CTX_AREA_FK': ''}
        if date:
            params['BASS_DT'] = date
            
        try:
            return self._make_request_dict(
                endpoint=API_ENDPOINTS['CHK_HOLIDAY'],
                tr_id="CTCA0903R",
                params=params
            )
        except Exception as e:
            logging.error(f"국내 휴장일 정보 조회 실패: {e}")
            return None

    def get_stock_financial(self, code: str) -> Optional[Dict[str, Any]]:
        """재무비율 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['FINANCIAL_RATIO'],
            tr_id="FHKST66430300",
            params={"FID_COND_MRKT_DIV_CODE": "UN", "FID_INPUT_ISCD": code}
        )

    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """주식 기본 정보 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['SEARCH_STOCK_INFO'],
            tr_id="CTPF1002R",
            params={"PRDT_TYPE_CD": "300", "PDNO": code}
        )
        
    def get_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """
        주식 회원사 정보 조회 (Postman 검증된 방식)
        
        Args:
            ticker: 종목코드 (6자리)
            retries: 재시도 횟수
        """
        for attempt in range(retries):
            try:
                response = self.client.make_request(
                    endpoint=API_ENDPOINTS['INQUIRE_MEMBER'],
                    tr_id="FHKST01010600",
                    params={
                        "FID_COND_MRKT_DIV_CODE": "UN",
                        "FID_INPUT_ISCD": ticker
                    }
                )
                
                if response and response.get('rt_cd') == '0':
                    return response
                elif response and response.get('rt_cd') != '0':
                    logging.warning(f"주식 회원사 조회 실패 (시도 {attempt+1}/{retries}): {response.get('msg1', '알 수 없는 오류')}")
                    if attempt < retries - 1:
                        continue
                    else:
                        return response
                else:
                    logging.error(f"주식 회원사 조회 응답 없음 (시도 {attempt+1}/{retries})")
                    if attempt < retries - 1:
                        continue
                    else:
                        return None
                        
            except Exception as e:
                logging.error(f"주식 회원사 조회 예외 발생 (시도 {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    continue
                else:
                    return None
        
        return None

    def is_holiday(self, date: str) -> Optional[bool]:
        """주어진 날짜가 한국 주식 시장 휴장일인지 확인합니다.
        
        Args:
            date: YYYYMMDD 형식의 날짜 문자열
            
        Returns:
            bool: 휴장일이면 True, 거래일이면 False, 확인 불가면 None
        """
        import logging
        from datetime import datetime
        
        try:
            target_date = datetime.strptime(date, '%Y%m%d')
            
            # 1. 주말(토요일, 일요일) 여부 확인
            if target_date.weekday() >= 5:  # 5: 토요일, 6: 일요일
                return True

            # 2. API를 통해 공휴일 정보 확인
            # 기준일 계산: 입력 날짜가 포함된 월의 첫 번째 날
            base_date_str = target_date.replace(day=1).strftime('%Y%m%d')
            
            holiday_info = self.get_holiday_info(base_date_str)
            
            if not holiday_info or holiday_info.get('rt_cd') not in ['0', '1']:
                logging.warning(f"휴장일 정보를 가져올 수 없습니다: {holiday_info.get('msg1') if holiday_info else 'No response'}")
                return None

            output = holiday_info.get('output', [])
            if not output:
                logging.warning("휴장일 데이터가 비어있습니다")
                # API 응답이 비어있으면 주말이 아닌 이상 거래일로 간주
                return False

            for day_info in output:
                if day_info.get('bass_dt') == date:
                    is_open = day_info.get('opnd_yn', 'N') == 'Y'
                    # opnd_yn이 'Y'가 아니면 휴장일
                    return not is_open

            # 해당 날짜 정보가 없으면 거래일로 간주
            return False
            
        except Exception as e:
            logging.error(f"Error checking holiday status for {date}: {e}")
            return None

    def get_kospi200_index(self, futures_month: str = "202409") -> Optional[Dict[str, Any]]:
        """
        KOSPI 200 지수 시세 조회 (기초자산) (rt_cd 메타데이터가 포함된)
        
        Args:
            futures_month (str): 조회할 선물의 만기년월 (YYYYMM 형식).
                                 이 값에 따라 관련된 기초자산(KOSPI 200)의 시세가 조회됩니다.
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INDEX_PRICE'],
            tr_id="FHMIF10100000",
            params={
                "fid_cond_mrkt_cls_code": "K21",
                "fid_input_iscd": futures_month,
            }
        )

    def get_futures_price(self, code: str) -> Optional[Dict[str, Any]]:
        """
        선물 시세 조회 (rt_cd 메타데이터가 포함된)
        
        KOSPI200 선물의 실시간 시세 정보를 조회합니다.
        현재가, 등락률, 거래량 등의 상세 정보를 제공합니다.
        
        Args:
            code (str): 선물 종목코드 (6자리, 예: "101T12")
                       - 형식: YYY[계약타입][만기월]
                       - YYY: 연도의 마지막 3자리
                       - 계약타입: T(선물), S(스프레드)
                       - 만기월: 03, 06, 09, 12 (분기별)
        
        Returns:
            Optional[Dict[str, Any]]: 선물 시세 데이터
                - 성공 시: rt_cd와 함께 시세 정보 딕셔너리
                - 실패 시: None
                
        Example:
            >>> # 가장 활발한 KOSPI200 선물 시세 조회
            >>> futures_code = get_kospi200_futures_code()
            >>> result = stock_api.get_futures_price(futures_code)
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"현재가: {result['output']['stck_prpr']}")
            ...     print(f"등락률: {result['output']['prdy_ctrt']}%")
            
            >>> # 특정 선물 시세 조회 
            >>> result = stock_api.get_futures_price("101T12")
        
        Note:
            - F 시장(지수선물)에서만 조회 가능
            - 실시간 데이터이므로 시장 개장 시간에만 유효한 데이터 제공
            - rt_cd가 '0'이면 성공, 그 외는 오류
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_FUTURES_PRICE'],
            tr_id="FHMIF10000000",
            params={
                "fid_cond_mrkt_div_code": "F",
                "fid_input_iscd": code,
            }
        )

    def get_daily_index_chart_price(self, 
                                   market_div_code: str = "U", 
                                   input_iscd: str = "0007", 
                                   start_date: str = "20210101", 
                                   end_date: str = "20220722", 
                                   period_div_code: str = "D") -> Optional[Dict[str, Any]]:
        """
        국내주식업종기간별시세 조회 (일/주/월/년) (rt_cd 메타데이터가 포함된)
        
        Args:
            market_div_code (str): 시장 분류 코드 (U: 업종)
            input_iscd (str): 업종코드 (0001: 종합, 0002: 대형주, ...)
            start_date (str): 시작일자 (YYYYMMDD 형식)
            end_date (str): 종료일자 (YYYYMMDD 형식)
            period_div_code (str): 기간분류코드 (D: 일봉, W: 주봉, M: 월봉, Y: 년봉)
            
        Returns:
            Dict: 업종기간별시세 데이터, 실패 시 None
            
        Note:
            - 한 번의 호출에 최대 50건의 데이터 수신
            - 다음 데이터를 받아오려면 OUTPUT 값의 가장 과거 일자의 1일 전 날짜를 end_date에 넣어 재호출
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_DAILY_INDEXCHARTPRICE'],
            tr_id="FHKUP03500100",
            params={
                "fid_cond_mrkt_div_code": market_div_code,
                "fid_input_iscd": input_iscd,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date,
                "fid_period_div_code": period_div_code
            }
        )

    def get_index_daily_price(self,
                              index_code: str = "0001",
                              end_date: str = None,
                              period: str = "D") -> Optional[Dict[str, Any]]:
        """
        국내 지수 일자별 시세 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            index_code (str): 지수코드 (0001:KOSPI, 1001:KOSDAQ, 2001:KOSPI200)
            end_date (str): 조회 종료일 (YYYYMMDD), None이면 오늘
            period (str): 기간 구분 (D:일별, W:주별, M:월별)
            
        Returns:
            Dict: 지수 일별 시세 데이터
            
        Example:
            >>> stock_api.get_index_daily_price("0001", "20250818")  # KOSPI
            >>> stock_api.get_index_daily_price("1001", "20250818")  # KOSDAQ
        """
        if end_date is None:
            from datetime import datetime
            end_date = datetime.now().strftime('%Y%m%d')
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS.get('INQUIRE_INDEX_DAILY_PRICE', '/uapi/domestic-stock/v1/quotations/inquire-index-daily-price'),
            tr_id="FHPUP02120000",
            params={
                "FID_PERIOD_DIV_CODE": period,
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": index_code,
                "FID_INPUT_DATE_1": end_date,
            }
        )
    
    def get_orderbook_raw(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 호가 조회 (원시 데이터) (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 호가 원시 데이터
            
        Example:
            >>> stock_api.get_orderbook_raw("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_ASKING_PRICE_EXP_CCN'],
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_INPUT_ISCD": code
            }
        )
    
    def get_stock_member(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 회원사(거래원) 정보 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 회원사 매매 정보
            
        Example:
            >>> stock_api.get_stock_member("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_MEMBER'],
            tr_id="FHKST01010600",
            params={
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_INPUT_ISCD": code
            }
        )
    
    def get_daily_credit_balance(self, 
                                code: str, 
                                date: str) -> Optional[Dict[str, Any]]:
        """
        국내주식 신용잔고 일별추이 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리, 예: "005930")
            date (str): 결제일자 (YYYYMMDD 형식, 예: "20240508")
            
        Returns:
            Optional[Dict[str, Any]]: 신용잔고 일별추이 데이터
                - 성공 시: 신용잔고 일별추이 정보를 포함한 응답 데이터
                - 실패 시: None
                
        Note:
            신용잔고는 신용거래(융자, 대주거래)로 인한 미결제 잔고를 의미합니다.
            일별 추이를 통해 해당 종목의 신용거래 동향을 파악할 수 있습니다.
            
        Example:
            >>> stock_api.get_daily_credit_balance("005930", "20240508")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['DAILY_CREDIT_BALANCE'],
            tr_id="FHPST04760000",  # 국내주식 신용잔고 일별추이 TR ID
            params={
                "fid_cond_mrkt_div_code": "J",  # 시장 분류 코드 (J: 주식)
                "fid_cond_scr_div_code": "20476",  # 화면 분류 코드
                "fid_input_iscd": code,  # 종목코드
                "fid_input_date_1": date  # 결제일자
            }
        )

    def get_future_option_price(self, 
                               market_div_code: str = "F", 
                               input_iscd: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        선물옵션 시세 조회 (rt_cd 메타데이터가 포함된)
        
        KOSPI200 선물/옵션, 주식선물/옵션의 실시간 시세를 조회합니다.
        종목코드를 지정하지 않으면 가장 활발한 KOSPI200 선물 시세를 조회합니다.
        
        Args:
            market_div_code (str, optional): 시장분류코드. Defaults to "F".
                - "F": 지수선물 (KOSPI200 선물)
                - "O": 지수옵션 (KOSPI200 옵션)  
                - "JF": 주식선물 (개별주식 선물)
                - "JO": 주식옵션 (개별주식 옵션)
            input_iscd (Optional[str], optional): 선물옵션종목코드. Defaults to None.
                - None인 경우 가장 활발한 KOSPI200 선물코드 자동 사용
                - 선물: 6자리 (예: "101T12", "101S03")
                - 옵션: 9자리 (예: "201T12370", "201S03370")
                
        Returns:
            Optional[Dict[str, Any]]: 선물옵션 시세 데이터
                - 성공 시: rt_cd와 함께 시세 정보 딕셔너리
                - 실패 시: None
                
        Example:
            >>> # 가장 활발한 KOSPI200 선물 시세 조회 (기본값)
            >>> result = stock_api.get_future_option_price()
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"현재가: {result['output']['stck_prpr']}")
            
            >>> # 특정 KOSPI200 선물 시세 조회
            >>> result = stock_api.get_future_option_price("F", "101T12")
            
            >>> # KOSPI200 옵션 시세 조회  
            >>> result = stock_api.get_future_option_price("O", "201T12370")
            
            >>> # 개별주식 선물 시세 조회
            >>> result = stock_api.get_future_option_price("JF", "005930T12")
        
        Note:
            - 실시간 데이터이므로 시장 개장 시간에만 유효한 데이터 제공
            - 옵션의 경우 행사가가 포함된 9자리 코드 필요
            - rt_cd가 '0'이면 성공, 그 외는 오류
            - 주식선물/옵션은 종목별로 상장 여부 확인 필요
        """
        if input_iscd is None:
            input_iscd = get_kospi200_futures_code()
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['FUTUREOPTION_INQUIRE_PRICE'],
            tr_id="FHMIF10000000",
            params={
                "fid_cond_mrkt_div_code": market_div_code,
                "fid_input_iscd": input_iscd
            }
        )

    def get_vi_status(self, 
                     code: str = "",
                     div_cls_code: str = "0",
                     mrkt_cls_code: str = "0",
                     rank_sort_cls_code: str = "0",
                     input_date: str = "") -> Optional[Dict[str, Any]]:
        """
        변동성완화장치(VI) 현황 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리, 예: "005930"), 전체 조회시 빈 문자열
            div_cls_code (str): 구분코드 (0:전체, 1:상승, 2:하락)
            mrkt_cls_code (str): 시장구분코드 (0:전체, K:거래소, Q:코스닥)
            rank_sort_cls_code (str): 정렬구분코드 (0:전체, 1:정적, 2:동적, 3:정적&동적)
            input_date (str): 영업일 (YYYYMMDD 형식)
            
        Returns:
            Dict: VI 현황 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_vi_status("005930", input_date="20240126")
        """
        from datetime import datetime
        if not input_date:
            input_date = datetime.now().strftime("%Y%m%d")
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_VI_STATUS'],
            tr_id="FHPST01390000",
            params={
                "fid_div_cls_code": div_cls_code,
                "fid_cond_scr_div_code": "20139",
                "fid_mrkt_cls_code": mrkt_cls_code,
                "fid_input_iscd": code,
                "fid_rank_sort_cls_code": rank_sort_cls_code,
                "fid_input_date_1": input_date,
                "fid_trgt_cls_code": "",
                "fid_trgt_exls_cls_code": ""
            }
        )

    def get_elw_price(self, code: str) -> Optional[Dict[str, Any]]:
        """
        ELW(주식워런트증권) 현재가 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): ELW 종목코드
            
        Returns:
            Dict: ELW 시세 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_elw_price("58F282")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_ELW_PRICE'],
            tr_id="FHKEW15010000",
            params={
                "fid_cond_mrkt_div_code": "W",  # W: ELW
                "fid_input_iscd": code
            }
        )

    def get_index_category_price(self, 
                                 upjong_code: str = "0001") -> Optional[Dict[str, Any]]:
        """
        업종별 지수 시세 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            upjong_code (str): 업종코드 (예: "0001")
            
        Returns:
            Dict: 업종별 지수 시세 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_index_category_price("0001")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INDEX_CATEGORY_PRICE'],
            tr_id="FHKUP03500100",
            params={
                "fid_cond_mrkt_div_code": "U",  # U: 업종
                "fid_input_iscd": upjong_code
            }
        )

    def get_index_tick_price(self, 
                            index_code: str = "0001",
                            hour: str = "") -> Optional[Dict[str, Any]]:
        """
        지수 틱(체결) 시세 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            index_code (str): 지수코드 (예: "0001")
            hour (str): 조회 시간 (HH24MISS 형식, 예: "090000")
            
        Returns:
            Dict: 지수 틱 시세 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_index_tick_price("0001", "090000")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INDEX_TICKPRICE'],
            tr_id="FHPUP02110100",
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": index_code,
                "fid_hour_cls_code": "0" if not hour else "1",
                "fid_pw_data_incu_yn": "Y",
                "fid_input_hour_1": hour if hour else ""
            }
        )

    def get_index_time_price(self, 
                            index_code: str = "0001",
                            time_div: str = "0") -> Optional[Dict[str, Any]]:
        """
        지수 분/일봉 시세 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            index_code (str): 지수코드 (예: "0001")
            time_div (str): 시간구분 (0:30초, 1:1분, 2:10분, 3:30분, D:일봉)
            
        Returns:
            Dict: 지수 분/일봉 시세 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_index_time_price("0001", "1")  # 1분봉
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INDEX_TIMEPRICE'],
            tr_id="FHKUP03500200",
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": index_code,
                "fid_input_date_1": "",
                "fid_input_date_2": "",
                "fid_period_div_code": time_div
            }
        )

    def get_investor_daily_by_market(self, 
                                     market_code: str = "STK",
                                     input_date: str = "") -> Optional[Dict[str, Any]]:
        """
        시장별 투자자별 일별 매매동향 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            market_code (str): 시장구분코드 (STK:전체, KSP:코스피, KSQ:코스닥)
            input_date (str): 조회일자 (YYYYMMDD 형식)
            
        Returns:
            Dict: 투자자별 일별 매매동향 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_investor_daily_by_market("STK", "20240126")
        """
        from datetime import datetime
        if not input_date:
            input_date = datetime.now().strftime("%Y%m%d")
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR_DAILY_BY_MARKET'],
            tr_id="FHPTJ04400000",
            params={
                "fid_cond_mrkt_div_code": market_code,
                "fid_input_date_1": input_date
            }
        )

    def get_investor_time_by_market(self, 
                                    market_code: str = "STK",
                                    time_div: str = "0") -> Optional[Dict[str, Any]]:
        """
        시장별 투자자별 당일 시간대별 매매동향 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            market_code (str): 시장구분코드 (STK:전체, KSP:코스피, KSQ:코스닭)
            time_div (str): 시간구분 (0:당일전체, 1:1분, 2:10분, 3:30분)
            
        Returns:
            Dict: 투자자별 시간대별 매매동향 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_investor_time_by_market("STK", "1")  # 1분 단위
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR_TIME_BY_MARKET'],
            tr_id="FHPTJ04410000",
            params={
                "fid_cond_mrkt_div_code": market_code,
                "fid_input_hour_1": "",
                "fid_pw_data_incu_yn": "Y",
                "fid_hour_cls_code": time_div
            }
        )

    def get_member_daily(self, 
                        code: str,
                        start_date: str = "",
                        end_date: str = "") -> Optional[Dict[str, Any]]:
        """
        종목별 회원사 일별 매매동향 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            start_date (str): 시작일자 (YYYYMMDD 형식)
            end_date (str): 종료일자 (YYYYMMDD 형식)
            
        Returns:
            Dict: 회원사 일별 매매동향 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_member_daily("005930", "20240101", "20240131")
        """
        from datetime import datetime
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = end_date
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_MEMBER_DAILY'],
            tr_id="FHKST01010700",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date
            }
        )

    def get_overtime_asking_price(self, code: str) -> Optional[Dict[str, Any]]:
        """
        시간외 호가 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 시간외 호가 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_overtime_asking_price("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_OVERTIME_ASKING_PRICE'],
            tr_id="FHKST01010200",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
        )

    def get_overtime_price(self, code: str) -> Optional[Dict[str, Any]]:
        """
        시간외 시세 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 시간외 시세 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_overtime_price("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_OVERTIME_PRICE'],
            tr_id="FHKST01010300",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
        )

    def get_time_daily_chart_price(self, 
                                   code: str,
                                   period_div: str = "0") -> Optional[Dict[str, Any]]:
        """
        종목 분/일봉 차트 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            period_div (str): 기간구분 (0:30초, 1:1분, 2:3분, 3:5분, 4:10분, 5:15분, 6:30분, 7:60분, D:일)
            
        Returns:
            Dict: 분/일봉 차트 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_time_daily_chart_price("005930", "1")  # 1분봉
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_DAILYCHARTPRICE'],
            tr_id="FHKST03010200",
            params={
                "fid_etc_cls_code": "",
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": "",
                "fid_input_date_2": "",
                "fid_period_div_code": period_div,
                "fid_org_adj_prc": "0"
            }
        )

    def get_time_index_chart_price(self, 
                                   index_code: str = "0001",
                                   period_div: str = "1") -> Optional[Dict[str, Any]]:
        """
        지수 분봉 차트 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            index_code (str): 지수코드 (예: "0001")
            period_div (str): 기간구분 (1:1분, 2:3분, 3:5분, 4:10분, 5:15분, 6:30분, 7:60분)
            
        Returns:
            Dict: 지수 분봉 차트 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_time_index_chart_price("0001", "1")  # 1분봉
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_INDEXCHARTPRICE'],
            tr_id="FHKUP03500100",
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": index_code,
                "fid_input_date_1": "",
                "fid_input_date_2": "",
                "fid_period_div_code": period_div,
                "fid_pw_data_incu_yn": "Y"
            }
        )

    def get_time_item_conclusion(self, 
                                code: str,
                                hour: str = "") -> Optional[Dict[str, Any]]:
        """
        종목별 체결 조회 (틱 데이터) (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            hour (str): 조회시간 (HH24MISS 형식)
            
        Returns:
            Dict: 체결 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_time_item_conclusion("005930", "090000")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_ITEMCONCLUSION'],
            tr_id="FHPST01060000",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_hour_1": hour if hour else "",
                "fid_pw_data_incu_yn": "Y"
            }
        )

    def get_time_overtime_conclusion(self, 
                                    code: str,
                                    hour: str = "") -> Optional[Dict[str, Any]]:
        """
        시간외 체결 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            hour (str): 조회시간 (HH24MISS 형식)
            
        Returns:
            Dict: 시간외 체결 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_time_overtime_conclusion("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_OVERTIMECONCLUSION'],
            tr_id="FHPST02320000",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_hour_1": hour if hour else "",
                "fid_pw_data_incu_yn": "Y"
            }
        )

    def get_asking_price_exp_ccn(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 호가 및 예상체결 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 호가 및 예상체결 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_asking_price_exp_ccn("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_ASKING_PRICE_EXP_CCN'],
            tr_id="FHKST01010200",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
        )

    def get_price_2(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 현재가 시세2 조회 (확장 정보) (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            
        Returns:
            Dict: 주식 시세2 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_price_2("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_PRICE_2'],
            tr_id="FHPST01010000",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
        )

    def get_daily_overtimeprice(self, 
                                code: str,
                                start_date: str = "",
                                end_date: str = "") -> Optional[Dict[str, Any]]:
        """
        시간외 일자별 주가 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            start_date (str): 시작일자 (YYYYMMDD 형식)
            end_date (str): 종료일자 (YYYYMMDD 형식)
            
        Returns:
            Dict: 시간외 일자별 주가 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_daily_overtimeprice("005930", "20240101", "20240131")
        """
        from datetime import datetime
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = end_date
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_DAILY_OVERTIMEPRICE'],
            tr_id="FHPST02320000",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date,
                "fid_period_div_code": "D"
            }
        )

    def get_daily_trade_volume(self, 
                              code: str,
                              start_date: str = "",
                              end_date: str = "") -> Optional[Dict[str, Any]]:
        """
        종목별 일별 매수매도 체결량 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            start_date (str): 시작일자 (YYYYMMDD 형식)
            end_date (str): 종료일자 (YYYYMMDD 형식)
            
        Returns:
            Dict: 일별 매수매도 체결량 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_daily_trade_volume("005930", "20240101", "20240131")
        """
        from datetime import datetime
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=30)).strftime("%Y%m%d")
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_DAILY_TRADE_VOLUME'],
            tr_id="FHKST03010800",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date
            }
        )

    def get_program_trade_by_stock(self, 
                                   code: str,
                                   market_code: str = "J") -> Optional[Dict[str, Any]]:
        """
        종목별 프로그램매매 추이(체결) 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            market_code (str): 시장구분코드 (J:KRX, NX:NXT, UN:통합)
            
        Returns:
            Dict: 프로그램매매 추이 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_program_trade_by_stock("005930")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['PROGRAM_TRADE_BY_STOCK'],
            tr_id="FHPPG04650101",
            params={
                "fid_cond_mrkt_div_code": market_code,
                "fid_input_iscd": code
            }
        )

    def get_program_trade_by_stock_daily(self, 
                                         code: str,
                                         start_date: str = "",
                                         end_date: str = "",
                                         market_code: str = "J") -> Optional[Dict[str, Any]]:
        """
        종목별 프로그램매매 추이(일별) 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            code (str): 종목코드 (6자리)
            start_date (str): 시작일자 (YYYYMMDD 형식)
            end_date (str): 종료일자 (YYYYMMDD 형식)
            market_code (str): 시장구분코드 (J:KRX, NX:NXT, UN:통합)
            
        Returns:
            Dict: 일별 프로그램매매 추이 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_program_trade_by_stock_daily("005930", "20240101", "20240131")
        """
        from datetime import datetime
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=30)).strftime("%Y%m%d")
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['PROGRAM_TRADE_BY_STOCK_DAILY'],
            tr_id="FHPPG04650200",
            params={
                "fid_cond_mrkt_div_code": market_code,
                "fid_input_iscd": code,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date
            }
        )

    def get_comp_program_trade_daily(self, 
                                     market_code: str = "J",
                                     start_date: str = "",
                                     end_date: str = "") -> Optional[Dict[str, Any]]:
        """
        프로그램매매 종합현황(일별) 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            market_code (str): 시장구분코드 (J:거래소, Q:코스닥, JQ:KRX)
            start_date (str): 시작일자 (YYYYMMDD 형식)
            end_date (str): 종료일자 (YYYYMMDD 형식)
            
        Returns:
            Dict: 프로그램매매 종합현황 일별 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_comp_program_trade_daily("J", "20240101", "20240131")
        """
        from datetime import datetime
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=30)).strftime("%Y%m%d")
            
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['COMP_PROGRAM_TRADE_DAILY'],
            tr_id="FHPPG04600000",
            params={
                "fid_input_option": market_code,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date
            }
        )

    def get_comp_program_trade_today(self, 
                                     market_code: str = "J",
                                     time_div: str = "0") -> Optional[Dict[str, Any]]:
        """
        프로그램매매 종합현황(당일/시간별) 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            market_code (str): 시장구분코드 (J:거래소, Q:코스닥, JQ:KRX)
            time_div (str): 시간구분 (0:당일전체, 1:1분, 2:10분, 3:30분)
            
        Returns:
            Dict: 프로그램매매 종합현황 당일 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_comp_program_trade_today("J", "1")  # 거래소 1분 단위
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['COMP_PROGRAM_TRADE_TODAY'],
            tr_id="FHPPG04600100",
            params={
                "fid_input_option": market_code,
                "fid_hour_cls_code": time_div,
                "fid_pw_data_incu_yn": "Y"
            }
        )

    def get_investor_program_trade_today(self, 
                                         market_code: str = "J") -> Optional[Dict[str, Any]]:
        """
        프로그램매매 투자자별 매매동향(당일) 조회 (rt_cd 메타데이터가 포함된)
        
        Args:
            market_code (str): 시장구분코드 (J:거래소, Q:코스닥, JQ:KRX)
            
        Returns:
            Dict: 투자자별 프로그램매매 동향 데이터, 실패 시 None
            
        Example:
            >>> stock_api.get_investor_program_trade_today("J")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INVESTOR_PROGRAM_TRADE_TODAY'],
            tr_id="HHPPG046600C0",
            params={
                "fid_input_option": market_code
            }
        )
