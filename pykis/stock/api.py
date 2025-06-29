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
import pandas as pd
import logging
from ..core.client import KISClient, API_ENDPOINTS

class StockAPI:
    def __init__(self, client: KISClient, account_info: Dict[str, str]):
        self.client = client
        self.account = account_info  # { 'CANO': '12345678', 'ACNT_PRDT_CD': '01' }

    def _make_request_dataframe(self, endpoint: str, tr_id: str, params: dict, retries: int = 5) -> Optional[pd.DataFrame]:
        """공통 요청 함수: 응답을 DataFrame으로 변환"""
        response = self.client.make_request(
            endpoint=endpoint,
            tr_id=tr_id,
            params=params,
            retries=retries
        )
        if response and response.get("rt_cd") == "0":
            output = response.get("output", [])
            return pd.DataFrame([output]) if isinstance(output, dict) else pd.DataFrame(output)
        return None

    def get_stock_price(self, code: str) -> Optional[Dict[str, Any]]:
        """주식 현재가 조회"""
        return self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_PRICE'],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        )

    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[Dict]:
        """
        일별 시세 조회 (Postman 검증된 방식)
        
        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미사용, 1: 수정주가 사용)
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_DAILY_ITEMCHARTPRICE'],
            tr_id="FHKST01010400",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_period_div_code": period,
                "fid_org_adj_prc": org_adj_prc
            }
        )

    

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
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
                        "FID_COND_MRKT_DIV_CODE": "J",
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
    
    def get_stock_investor(self, ticker: str = '', retries: int = 10, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """투자자별 매매 동향 조회
        개인 순매수 수량 및 거래대금은 'prsn_ntby_qty', 'prsn_ntby_tr_pbmn' 필드 사용.
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
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
    
    def get_orderbook(self, code: str) -> Optional[pd.DataFrame]:
        """호가 및 예상체결 데이터 조회"""
        response = self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_ASKING_PRICE_EXP_CCN'],
            tr_id="FHKST01010200",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code
            }
        )
        if response and response.get('rt_cd') == '0':
            data = response.get('output1')
            if not data or not isinstance(data, dict):
                logging.error(f"get_orderbook: no output1 found for {code} – {response.get('msg1', '')}")
                return None
            # Sum ask/bid quantities from output1
            try:
                ask_volume = sum(int(data.get(f"askp_rsqn{i}", 0)) for i in range(1, 11))
                bid_volume = sum(int(data.get(f"bidp_rsqn{i}", 0)) for i in range(1, 11))
            except ValueError as e:
                logging.error(f"get_orderbook: volume conversion error for {code}: {e}")
                return None
            # Compute relative strength ratio
            if ask_volume == 0 and bid_volume > 0:
                ratio = float('inf')
            elif ask_volume == 0 and bid_volume == 0:
                ratio = None
            else:
                ratio = (bid_volume / ask_volume) * 100 if ask_volume > 0 else 0
            return pd.DataFrame({
                "매도잔량": [ask_volume],
                "매수잔량": [bid_volume],
                "매수우세": [ratio]
            })
        return None

    def get_volume_power(self, volume: int = 0) -> Optional[Dict[str, Any]]:
        """
        체결강도 순위 조회
        
        Args:
            volume (int): 거래량 기준 (기본값: 0)
            
        Returns:
            Optional[Dict[str, Any]]: 체결강도 순위 정보
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
            
            return self.client.make_request(
                endpoint=API_ENDPOINTS['VOLUME_POWER'],
                tr_id="FHPST01680000",
                params=params
            )
        except Exception as e:
            logging.error(f"체결강도 순위 조회 실패: {e}")
            return None

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """국내주식 등락률 순위 조회"""
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
        response = self.client.make_request(
            endpoint=API_ENDPOINTS['FLUCTUATION'],
            tr_id="FHPST01700000",
            params=params
        )
        return response

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 순위 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
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
        response = self.client.make_request(
            endpoint=API_ENDPOINTS['VOLUME_RANK'],
            tr_id="FHPST01710000",
            params=params
        )
        return response  # Return raw response for debugging

    def get_stock_info(self, ticker: str) -> Optional[pd.DataFrame]:
        """주식 기본 정보 조회"""
        response = self.client.make_request(
            endpoint=API_ENDPOINTS['SEARCH_STOCK_INFO'],
            tr_id="CTPF1002R",
            params={"PRDT_TYPE_CD": "300", "PDNO": ticker}
        )
        if response and response.get('rt_cd') == '0':
            output = response.get('output', {})
            return pd.DataFrame([output]) if output else pd.DataFrame()
        return None

    def get_member_transaction(self, code: str, mem_code: str) -> Optional[Dict[str, Any]]:
        """회원사 일별 매매 종목"""
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
        return self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_MEMBER_DAILY'],
            tr_id="FHPST04540000",
            params=params
        )

    def get_foreign_broker_net_buy(self, code: str, foreign_brokers=None, date: str = None) -> Optional[tuple]:
        """
        투자자별 매매 동향 API를 활용해 외국계 브로커의 순매수(매수-매도) 합계를 집계합니다.
        code: 종목코드
        foreign_brokers: 외국계 브로커명 리스트 (기본값 제공)
        date: 조회일자(YYYYMMDD), None이면 오늘
        반환: (순매수합계, 외국계 DataFrame) 또는 None
        """
        df = self.get_stock_investor(ticker=code)
        
        if df is None or df.empty:
            logging.warning(f"[{code}] 투자자별 매매 동향 데이터가 없습니다.")
            return None
            
        # 외국인 순매수량 추출
        if 'frgn_ntby_qty' not in df.columns:
            logging.error(f"[{code}] 외국인 순매수량 컬럼이 없습니다. 컬럼: {df.columns.tolist()}")
            return None
            
        try:
            # 빈 문자열 처리: 당일 데이터 우선, 빈 값이면 0으로 처리
            foreign_qty_str = df['frgn_ntby_qty'].iloc[0]
            foreign_qty = int(foreign_qty_str) if foreign_qty_str and foreign_qty_str.strip() else 0
            
            if not foreign_qty_str.strip():
                logging.info(f"[{code}] 당일 외국인 순매수량이 빈 값, 0으로 설정 (날짜: {df['stck_bsop_date'].iloc[0]})")
            else:
                logging.info(f"[{code}] 외국인 순매수량: {foreign_qty} (날짜: {df['stck_bsop_date'].iloc[0]})")
            
            return foreign_qty, df
        except (ValueError, IndexError) as e:
            logging.error(f"[{code}] 외국인 순매수량 추출 중 오류 발생: {e}")
            return None

    def get_pbar_tratio(self, code: str, retries: int = 10) -> Optional[dict]:
        """매물대/거래비중 조회"""
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_cond_scr_div_code": "20113",
            "fid_input_hour_1": "",
        }
        return self.client.make_request(
            endpoint=API_ENDPOINTS['PBAR_TRATIO'],
            tr_id="FHPST01130000",
            params=params,
            retries=retries
        )

    def get_hourly_conclusion(self, code: str, hour: str = "115959", retries: int = 10) -> Optional[dict]:
        """시간대별 체결 조회
        
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
        return self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_ITEMCONCLUSION'],
            tr_id="FHPST01060000",
            params=params,
            retries=retries
        )

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """
        분봉 데이터 조회 (주식당일분봉조회)
        
        Args:
            code: 종목코드
            hour: 시간 (HHMMSS 형식, 기본값: 153000)
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['INQUIRE_TIME_ITEMCHARTPRICE'],
            tr_id="FHKST03010200",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": "Y"
            }
        )

    def get_possible_order(self, code: str, price: str, order_type: str = "01") -> Optional[Dict[str, Any]]:
        """매수 가능 주문 조회"""
        if not self.account:
            logging.error("계좌 정보가 없습니다.")
            return None
        
        return self.client.make_request(
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
        """국내 휴장일 정보를 조회합니다.
        
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
            return self.client.make_request(
                endpoint=API_ENDPOINTS['CHK_HOLIDAY'],
                tr_id="CTCA0903R",
                params=params
            )
        except Exception as e:
            logging.error(f"국내 휴장일 정보 조회 실패: {e}")
            return None

    def get_stock_financial(self, code: str) -> Optional[Dict[str, Any]]:
        """재무비율 조회"""
        return self.client.make_request(
            endpoint=API_ENDPOINTS['FINANCIAL_RATIO'],
            tr_id="FHKST66430300",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        )

    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """주식 기본 정보 조회"""
        return self.client.make_request(
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
                        "FID_COND_MRKT_DIV_CODE": "J",
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