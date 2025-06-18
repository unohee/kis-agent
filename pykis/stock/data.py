import logging
from typing import Dict, List, Optional, Any
from ..core.client import KISClient, API_ENDPOINTS
import pandas as pd
from datetime import datetime, timedelta

"""
stock.py - 주식 관련 API 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 주식 시세 조회
- 주문 실행
- 주문 취소
- 주문 내역 조회

✅ 의존:
- client.py: API 클라이언트

🔗 연관 모듈:
- agent.py: KIS API 통합 에이전트

💡 사용 예시:
stock = StockAPI(client)
price = stock.get_stock_price(code="005930")
"""

class StockData:
    def __init__(self, client: KISClient):
        self.client = client

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """주식 시세 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
                tr_id="FHKST01010100",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logging.error(f"주식 시세 조회 실패: {e}")
            return None

    def get_daily_price(self, code: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": 'J',
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date
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
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": time,
                "FID_PW_DATA_INCU_YN": "N"
            }
        )

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[pd.DataFrame]:
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker
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

    def get_stock_investor(self, ticker: str = '', retries: int = 10) -> Optional[pd.DataFrame]:
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
        }
        return self._make_request_dataframe(
            endpoint=API_ENDPOINTS['STOCK_INVESTOR'],
            tr_id="FHKST01010900",
            params=params,
            retries=retries
        )

    def get_stock_investor_detail(self, ticker: str = '', retries: int = 10, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
        }
        df = self._make_request_dataframe(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR_DETAIL'],
            tr_id="FHKST01010900",
            params=params,
            retries=retries
        )
        if df is not None and not df.empty:
            try:
                if 'prsn_ntby_qty' in df.columns and 'prsn_ntby_tr_pbmn' in df.columns:
                    try:
                        indiv_qty_str = df['prsn_ntby_qty'].iloc[0]
                        indiv_pbmn_str = df['prsn_ntby_tr_pbmn'].iloc[0]
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
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )
        if response and response.get('rt_cd') == '0':
            return pd.DataFrame(response.get('output', []))
        return None

    def get_overtime(self, code: str) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-price",
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_volume_power(self, volume: int) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-volume-power",
            tr_id="FHKST01010800",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_VOLUME": str(volume)
            }
        )

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-market-fluctuation",
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J"
            }
        )

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-market-rankings",
            tr_id="FHKST01010700",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_VOLUME": str(volume)
            }
        )

    def get_stock_info(self, ticker: str) -> Optional[pd.DataFrame]:
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker
            }
        )
        if response and response.get('rt_cd') == '0':
            return pd.DataFrame([response.get('output', {})])
        return None

    def get_member_transaction(self, code: str, mem_code: str) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-member-transaction",
            tr_id="FHKST01011000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_MEM_CODE": mem_code
            }
        )

    def get_foreign_broker_net_buy(self, code: str, foreign_brokers=None, date: str = None) -> Optional[tuple]:
        if foreign_brokers is None:
            foreign_brokers = ["미래에셋증권", "한국투자증권", "NH투자증권", "KB증권", "신한투자증권"]
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y%m%d")

        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-member-transaction",
            tr_id="FHKST01011000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": date
            }
        )

        if not response or 'output' not in response:
            return None

        total_buy = 0
        total_sell = 0
        for broker in foreign_brokers:
            for item in response['output']:
                if item.get('mem_name') == broker:
                    total_buy += int(item.get('shnu_qty', 0))
                    total_sell += int(item.get('seln_qty', 0))

        return total_buy, total_sell

    def get_pbar_tratio(self, code: str, retries: int = 10) -> Optional[dict]:
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            },
            retries=retries
        )
        if response and response.get('rt_cd') == '0':
            output = response.get('output', {})
            return {
                'pbar_tratio': output.get('pbar_tratio', '0'),
                'prdy_tratio': output.get('prdy_tratio', '0')
            }
        return None

class StockAPI:
    def __init__(self, client: KISClient, account_info: Dict[str, str] = None):
        """주식 API 초기화"""
        self.client = client
        self.account = account_info  # 계좌 정보 저장

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """주식 시세 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
                tr_id="FHKST01010100",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logging.error(f"주식 시세 조회 실패: {e}")
            return None

    def execute_order(self, code: str, quantity: int, price: int, order_type: str = "00") -> Optional[Dict]:
        """주문 실행"""
        try:
            if not self.account:
                raise ValueError("계좌 정보가 없습니다. account_info를 전달해주세요.")
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                tr_id="TTTC0802U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(quantity),
                    "ORD_UNPR": str(price),
                    "CTAC_TLNO": "",
                    "ORD_SVR_DVSN_CD": "0",
                    "ORD_DVSN_CD": "00"
                }
            )
        except Exception as e:
            logging.error(f"주문 실행 실패: {e}")
            return None

    def cancel_order(self, order_id: str) -> Optional[Dict]:
        """주문 취소"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-cancel",
                tr_id="TTTC0803U",
                params={"KRX_FWDG_ORD_ORGNO": order_id}
            )
        except Exception as e:
            logging.error(f"주문 취소 실패: {e}")
            return None

    def get_order_history(self) -> Optional[List[Dict]]:
        """주문 내역 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                tr_id="TTTC8001R",
                params={"INQR_STRT_DT": "", "INQR_END_DT": ""}
            )
        except Exception as e:
            logging.error(f"주문 내역 조회 실패: {e}")
            return None

    def get_daily_price(self, code: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": 'J',
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date
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
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": time,
                "FID_PW_DATA_INCU_YN": "N"
            }
        )

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[pd.DataFrame]:
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker
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

    def get_stock_investor(self, ticker: str = '', retries: int = 10) -> Optional[pd.DataFrame]:
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
        }
        return self._make_request_dataframe(
            endpoint=API_ENDPOINTS['STOCK_INVESTOR'],
            tr_id="FHKST01010900",
            params=params,
            retries=retries
        )

    def get_stock_investor_detail(self, ticker: str = '', retries: int = 10, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
        }
        df = self._make_request_dataframe(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR_DETAIL'],
            tr_id="FHKST01010900",
            params=params,
            retries=retries
        )
        if df is not None and not df.empty:
            try:
                if 'prsn_ntby_qty' in df.columns and 'prsn_ntby_tr_pbmn' in df.columns:
                    try:
                        indiv_qty_str = df['prsn_ntby_qty'].iloc[0]
                        indiv_pbmn_str = df['prsn_ntby_tr_pbmn'].iloc[0]
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
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )
        if response and response.get('rt_cd') == '0':
            return pd.DataFrame(response.get('output', []))
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
                "ORD_DVSN": order_type
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
                "ORD_UNPR": price,
                "CTAC_TLNO": "",
                "ORD_SVR_DVSN_CD": "0",
                "ORD_DVSN_CD": "00"
            }
        )

    def get_overtime(self, code: str) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-price",
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_volume_power(self, volume: int) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-volume-power",
            tr_id="FHKST01010800",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_VOLUME": str(volume)
            }
        )

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-market-fluctuation",
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J"
            }
        )

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-market-rankings",
            tr_id="FHKST01010700",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_VOLUME": str(volume)
            }
        )

    def get_stock_info(self, ticker: str) -> Optional[pd.DataFrame]:
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker
            }
        )
        if response and response.get('rt_cd') == '0':
            return pd.DataFrame([response.get('output', {})])
        return None

    def get_member_transaction(self, code: str, mem_code: str) -> Optional[Dict[str, Any]]:
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-member-transaction",
            tr_id="FHKST01011000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_MEM_CODE": mem_code
            }
        )

    def get_foreign_broker_net_buy(self, code: str, foreign_brokers=None, date: str = None) -> Optional[tuple]:
        if foreign_brokers is None:
            foreign_brokers = ["미래에셋증권", "한국투자증권", "NH투자증권", "KB증권", "신한투자증권"]
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y%m%d")

        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-member-transaction",
            tr_id="FHKST01011000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": date
            }
        )

        if not response or 'output' not in response:
            return None

        total_buy = 0
        total_sell = 0
        for broker in foreign_brokers:
            for item in response['output']:
                if item.get('mem_name') == broker:
                    total_buy += int(item.get('shnu_qty', 0))
                    total_sell += int(item.get('seln_qty', 0))

        return total_buy, total_sell

    def get_pbar_tratio(self, code: str, retries: int = 10) -> Optional[dict]:
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            },
            retries=retries
        )
        if response and response.get('rt_cd') == '0':
            output = response.get('output', {})
            return {
                'pbar_tratio': output.get('pbar_tratio', '0'),
                'prdy_tratio': output.get('prdy_tratio', '0')
            }
        return None

# Expose facade class for flat import
__all__ = ['StockAPI'] 