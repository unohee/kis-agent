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
- strategy_trigger.py: 실전 조건 기반 매수 트리거 실행

💡 사용 예시:
client = KISClient()
account = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
stock = StockAPI(client, account)
price = stock.get_stock_price("005930")
"""

from typing import Optional, Dict, Any, List
import pandas as pd
import logging
from ..core.client import KISClient
from ..core.client import API_ENDPOINTS

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
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": code}
        )

    def get_daily_price(self, code: str) -> Optional[pd.DataFrame]:
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id="FHKST01010400",
            params={
                "fid_cond_mrkt_div_code": 'J',
                "fid_input_iscd": code,
                "fid_period_div_code": 'D',
                "fid_org_adj_prc": '0'
            }
        )
        if response and response.get('rt_cd') == '0':
            return pd.DataFrame(response.get('output', []))
        return None

    def get_minute_chart(self, code: str, time: str) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            tr_id="FHKST03010200",
            params={
                "fid_etc_cls_code": "",
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_hour_1": time,
                "fid_pw_data_incu_yn": "N"
            }
        )

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[pd.DataFrame]:
        """주식 회원사 정보 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-member",
            tr_id="FHKST01010600",
            params=params,
            retries=retries
        )
        if response and response.get('rt_cd') == '0':
            output = response.get('output', [])
            return pd.DataFrame([output]) if isinstance(output, dict) else pd.DataFrame(output)
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
            endpoint=API_ENDPOINTS['STOCK_INVESTOR'],
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
                            logging.warning("Empty string encountered for individual investor details, set to 0.")

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
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
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

    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """보유 종목, 수량, 평균단가, 평가손익 등"""
        params = {
            "CANO": self.account['CANO'],
            "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id="TTTC8434R",
            params=params,
            retries=5
        )
        if res and res.get('rt_cd') == '0':
            return res
        return None

    def get_account_balance_df(self) -> Optional[pd.DataFrame]:
        """
        잔고 정보를 DataFrame으로 반환 (테스트 목적)
        """
        params = {
            "CANO": self.account['CANO'].zfill(8),  # 8자리로 맞춤
            "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'].zfill(2),  # 2자리로 맞춤
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",  # 빈 문자열
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",  # 빈 문자열
            "CTX_AREA_NK100": ""   # 빈 문자열
        }
        # print("[DEBUG][잔고조회 요청 파라미터]", params)  # 요청 파라미터 출력
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id="TTTC8434R",
            params=params,
            retries=3
        )
        # print("[DEBUG][잔고조회 raw response]", res)
        if res and res.get("rt_cd") == "0":
            return pd.DataFrame(res.get("output1", []))
        return None

    def get_possible_order(self, code: str, price: str, order_type: str = "01") -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
            tr_id="TTTC8908R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "PDNO": code,
                "ORD_UNPR": price,
                "ORD_DVSN": order_type,
                "OVRS_ICLD_YN": "N",
                "CMA_EVLU_AMT_ICLD_YN": "N"
            }
        )

    def order_stock_cash(self, code: str, price: str, quantity: str, order_type: str = "01") -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/order-cash",
            tr_id="TTTC0802U",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "PDNO": code,
                "ORD_DVSN": order_type,
                "ORD_QTY": quantity,
                "ORD_UNPR": price
            },
            method="POST"
        )

    def get_overtime(self, code: str) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-overtimeprice",
            tr_id="FHKST663400C0",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    # Added for StockMonitor
    def inquire_ccnl(self, code: str) -> Optional[Dict[str, Any]]:
        """주식 체결 조회"""
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-ccnl",
            tr_id="FHKST01010300",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
        )

    def get_volume_power(self, volume: int = 0) -> Optional[Dict[str, Any]]:
        """체결강도 순위 조회"""
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20168",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": str(volume),
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0"
        }
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/ranking/volume-power",
            tr_id="FHPST01680000",
            params=params
        )

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """등락률 순위 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20170",
            "FID_INPUT_ISCD": "0000",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_INPUT_CNT_1": "0",
            "FID_PRC_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "3000000",
            "FID_TRGT_CLS_CODE": "0",
            "FID_TRGT_EXLS_CLS_CODE": "0",
            "FID_DIV_CLS_CODE": "0",
            "FID_RSFL_RATE1": "",
            "FID_RSFL_RATE2": ""
        }
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/ranking/fluctuation",
            tr_id="FHPST01700000",
            params=params
        )
        return response  # Return raw response for debugging

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
            endpoint="/uapi/domestic-stock/v1/quotations/volume-rank",
            tr_id="FHPST01710000",
            params=params
        )
        return response  # Return raw response for debugging

    def get_stock_info(self, ticker: str) -> Optional[pd.DataFrame]:
        """주식 기본 정보 조회"""
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/search-stock-info",
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
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-member-daily",
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
        import datetime
        if foreign_brokers is None:
            foreign_brokers = [
                "골드만", "메릴린치", "모건스탠리", "크레디트스위스", "도이치", "JP모간", "UBS", "노무라", "맥쿼리", "HSBC"
            ]
        if date is None:
            date = datetime.datetime.now().strftime("%Y%m%d")
            
        # 투자자별 매매 동향 조회
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
        }
        
        try:
            df = self._make_request_dataframe(
                endpoint=API_ENDPOINTS['STOCK_INVESTOR'],  # INQUIRE_INVESTOR_DETAIL 대신 STOCK_INVESTOR 사용
                tr_id="FHKST01010900",
                params=params
            )
            
            if df is None or df.empty:
                logging.warning(f"[{code}] 투자자별 매매 동향 데이터가 없습니다.")
                return None
                
            # 외국인 순매수량 추출
            if 'frgn_ntby_qty' not in df.columns:
                logging.error(f"[{code}] 외국인 순매수량 컬럼이 없습니다. 컬럼: {df.columns.tolist()}")
                return None
                
            try:
                foreign_qty = int(df['frgn_ntby_qty'].iloc[0])
                return foreign_qty, df
            except (ValueError, IndexError) as e:
                logging.error(f"[{code}] 외국인 순매수량 추출 중 오류 발생: {e}")
                return None
                
        except Exception as e:
            logging.error(f"[{code}] 투자자별 매매 동향 조회 중 오류 발생: {e}", exc_info=True)
            return None

    def get_pbar_tratio(self, code: str, retries: int = 10) -> Optional[dict]:
        """시간대별 체결강도 조회"""
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": code,
            "fid_input_hour_1": "",
            "fid_pw_data_incu_yn": "N"
        }
        return self.client.make_request(
            endpoint=API_ENDPOINTS['PBAR_TRATIO'],
            tr_id="FHPTJ04040000",
            params=params,
            retries=retries
        )

    def get_condition_stocks(self, user_id: str, seq: int = 0, tr_cont: str = 'N') -> Optional[List[Dict]]:
        """조건검색 결과를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            seq: 조건검색 시퀀스 번호 (기본값: 0)
            tr_cont: 연속조회 여부 (기본값: 'N')
            
        Returns:
            List[Dict]: 조건검색 결과 리스트, 실패 시 None
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

def load_account_info(yaml_path: str = "credit/kis_devlp.yaml") -> dict:
    import yaml
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    return {
        "CANO": config.get("my_acct_stock", ""),
        "ACNT_PRDT_CD": config.get("my_prod", "01")
    }

if __name__ == "__main__":
    import json
    import logging
    import pandas as pd
    from ..core.client import KISClient

    logging.basicConfig(level=logging.INFO)
    test_code = "005930"  # 삼성전자
    account_info = load_account_info()
    client = KISClient(verbose=True)
    stock = StockAPI(client, account_info)

    def print_df(df, name):
        print(f"\n📊 {name}")
        if isinstance(df, pd.DataFrame):
            print(df.head())
        elif isinstance(df, dict):
            print(json.dumps(df, indent=2, ensure_ascii=False))
        else:
            print("❌ Failed or None")

    results = []

    def test_and_log(name, func):
        try:
            result = func()
            print_df(result, name)
            results.append((name, True, None))
        except Exception as e:
            logging.exception(f"{name} failed")
            results.append((name, False, str(e)))

    try:
        test_and_log("get_stock_price", lambda: stock.get_stock_price(test_code))
        test_and_log("get_daily_price", lambda: stock.get_daily_price(test_code))
        test_and_log("get_minute_chart", lambda: stock.get_minute_chart(test_code, "0900"))
        test_and_log("get_stock_member", lambda: stock.get_stock_member(test_code))
        test_and_log("get_stock_investor", lambda: stock.get_stock_investor(test_code))
        test_and_log("estimate_accumulated_volume_by_top_members", lambda: stock.estimate_accumulated_volume_by_top_members({"output": stock.get_stock_member(test_code).iloc[0].to_dict()}))
        test_and_log("get_orderbook", lambda: stock.get_orderbook(test_code))
        test_and_log("get_account_balance", lambda: stock.get_account_balance())
        test_and_log("get_possible_order", lambda: stock.get_possible_order(test_code, "60000"))
        test_and_log("order_stock_cash", lambda: stock.order_stock_cash(test_code, "60000", "10"))
        test_and_log("get_overtime", lambda: stock.get_overtime(test_code))
        test_and_log("inquire_ccnl", lambda: stock.inquire_ccnl(test_code))
        test_and_log("get_volume_power", lambda: stock.get_volume_power(10))
        test_and_log("get_market_fluctuation", lambda: stock.get_market_fluctuation())
        test_and_log("get_market_rankings", lambda: stock.get_market_rankings())
        test_and_log("get_stock_info", lambda: stock.get_stock_info(test_code))
        test_and_log("get_member_transaction", lambda: stock.get_member_transaction(test_code, "00086"))
        test_and_log("get_foreign_broker_net_buy", lambda: stock.get_foreign_broker_net_buy(test_code))
        test_and_log("get_pbar_tratio", lambda: stock.get_pbar_tratio(test_code))
        # 매물대 비중 API 결과를 표로도 출력 (한국어 주석: 신규 API 시각화)
        try:
            pbar_result = stock.get_pbar_tratio(test_code)
            if pbar_result and pbar_result.get('rt_cd') == '0' and 'output2' in pbar_result:
                df_pbar = pd.DataFrame(pbar_result['output2'])
                print("\n[매물대 비중 표]")
                print(df_pbar.head(10))  # 상위 10개만 출력
            else:
                print("❌ 매물대 비중 API 결과 없음 또는 오류:", pbar_result.get('msg1', pbar_result))
        except Exception as e:
            print(f"[get_pbar_tratio] 예외 발생: {e}")
        print("\n📊 테스트 요약")
        for name, success, error in results:
            flag = "✅" if success else "❌"
            msg = f" ({error})" if error else ""
            print(f"- {name.ljust(35, '.')} {flag}{msg}")
    except Exception as e:
        logging.exception("Test failed")
