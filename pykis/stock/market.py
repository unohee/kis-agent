"""
한국투자증권 API의 시장 정보 조회 기능을 제공하는 모듈입니다.

이 모듈은 한국투자증권 OpenAPI를 통해 다음 기능을 제공합니다:
- 주식 시세 조회
- 투자자별 매매 동향 조회
- 호가 정보 조회
- 시장 지수 조회
- 거래량 순위 조회
- 휴장일 조회
- 재무제표 조회
- 투자의견 조회
- 외국인/기관 매매 동향 조회
- 해외주식 정보 조회
- 채권 정보 조회

의존성:
- kis.core.client.KISClient: API 통신을 담당하는 클라이언트

연관 모듈:
- kis.account: 계좌 정보 관리
- kis.program: 프로그램 매매
- kis.strategy: 전략 실행 및 모니터링

사용 예시:
    >>> client = KISClient()
    >>> market = StockAPI(client)
    >>> price = market.get_stock_price("005930")
"""

import logging
from typing import Dict, List, Optional, Any
from ..core.client import KISClient, API_ENDPOINTS
import pandas as pd

logger = logging.getLogger(__name__)

class StockAPI:
    """
    주식 시장 정보 조회 API 기능을 제공하는 클래스입니다.

    이 클래스는 주식 시세, 투자자 동향, 호가 정보 등의 시장 정보를 조회하는 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신을 담당하는 클라이언트
        account_info (Dict[str, str]): 계좌 정보

    Example:
        >>> client = KISClient()
        >>> market = StockAPI(client)
        >>> price = market.get_stock_price("005930")
    """

    def __init__(self, client: KISClient, account_info: Optional[Dict[str, str]] = None):
        """
        StockAPI를 초기화합니다.

        Args:
            client (KISClient): API 통신을 담당하는 클라이언트
            account_info (Dict[str, str], optional): 계좌 정보

        Example:
            >>> client = KISClient()
            >>> api = StockAPI(client)
        """
        self.client = client
        self.account_info = account_info or {}

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """
        주식 현재가를 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 현재가 정보

        Example:
            >>> price = market.get_stock_price("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['STOCK_PRICE'],
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_daily_price(self, code: str, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """
        주식 일별 시세를 조회합니다.
        Args:
            code (str): 종목 코드
            start_date (str, optional): 조회 시작일(YYYYMMDD). 기본값: 최근 30일 전
            end_date (str, optional): 조회 종료일(YYYYMMDD). 기본값: 오늘
        Returns:
            Optional[Dict]: 일별 시세 정보
        """
        from datetime import datetime, timedelta
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        return self.client.make_request(
            endpoint=API_ENDPOINTS['STOCK_DAILY'],
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date
            }
        )

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """
        주식 호가 정보를 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 호가 정보

        Example:
            >>> orderbook = market.get_orderbook("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['ORDERBOOK'],
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_stock_member(self, code: str) -> Optional[Dict]:
        """
        주식 회원사 정보를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 회원사 정보

        Example:
            >>> member = market.get_stock_member("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_MEMBER'],
                tr_id="FHKST01010300",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 회원사 정보 조회 실패: {e}")
        return None
    
    def get_stock_investor(self, code: str) -> Optional[Dict]:
        """
        투자자별 매매 동향을 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 투자자별 매매 동향 정보

        Example:
            >>> investor = market.get_stock_investor("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['STOCK_INVESTOR'],
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_holiday_info(self) -> Optional[Dict]:
        """
        국내 휴장일 정보를 조회합니다.

        Returns:
            Optional[Dict]: 국내 휴장일 정보

        Example:
            >>> holiday = market.get_holiday_info()
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['HOLIDAY_INFO'],
                tr_id="CTCA0903R",
                params={}
            )
        except Exception as e:
            logger.error(f"국내 휴장일 정보 조회 실패: {e}")
            return None

    def get_stock_basic(self, code: str) -> Optional[Dict]:
        """
        주식 기본 정보를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 기본 정보

        Example:
            >>> basic = market.get_stock_basic("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_BASIC'],
                tr_id="CTPF1604R",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 기본 정보 조회 실패: {e}")
            return None

    def get_stock_income(self, code: str) -> Optional[Dict]:
        """
        주식 손익계산서를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 손익계산서 정보

        Example:
            >>> income = market.get_stock_income("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_INCOME'],
                tr_id="FHKST66430200",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 손익계산서 조회 실패: {e}")
            return None

    def get_stock_financial(self, code: str) -> Optional[Dict]:
        """
        주식 재무비율을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 재무비율 정보

        Example:
            >>> financial = market.get_stock_financial("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_FINANCIAL'],
                tr_id="FHKST66430300",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 재무비율 조회 실패: {e}")
            return None

    def get_stock_stability(self, code: str) -> Optional[Dict]:
        """
        주식 안정성비율을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 안정성비율 정보

        Example:
            >>> stability = market.get_stock_stability("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_STABILITY'],
                tr_id="FHKST66430600",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 안정성비율 조회 실패: {e}")
            return None

    def get_stock_growth(self, code: str) -> Optional[Dict]:
        """
        주식 성장성비율을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 성장성비율 정보

        Example:
            >>> growth = market.get_stock_growth("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_GROWTH'],
                tr_id="FHKST66430800",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 성장성비율 조회 실패: {e}")
            return None

    def get_stock_estimate(self, code: str) -> Optional[Dict]:
        """
        주식 종목추정실적을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 종목추정실적 정보

        Example:
            >>> estimate = market.get_stock_estimate("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_ESTIMATE'],
                tr_id="HHKST668300C0",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 종목추정실적 조회 실패: {e}")
            return None

    def get_stock_broker_opinion(self, code: str) -> Optional[Dict]:
        """
        주식 증권사별 투자의견을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 증권사별 투자의견 정보

        Example:
            >>> broker_opinion = market.get_stock_broker_opinion("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_BROKER_OPINION'],
                tr_id="FHKST663400C0",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 증권사별 투자의견 조회 실패: {e}")
            return None

    def get_stock_opinion(self, code: str) -> Optional[Dict]:
        """
        주식 종목투자의견을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 주식 종목투자의견 정보

        Example:
            >>> opinion = market.get_stock_opinion("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['STOCK_OPINION'],
                tr_id="FHKST663300C0",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"주식 종목투자의견 조회 실패: {e}")
            return None

    def get_domestic_investor(self, code: str) -> Optional[Dict]:
        """
        국내기관/외국인 매매종목 가집계를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 국내기관/외국인 매매종목 가집계 정보

        Example:
            >>> domestic = market.get_domestic_investor("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['DOMESTIC_INVESTOR'],
                tr_id="FHPTJ04400000",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"국내기관/외국인 매매종목 가집계 조회 실패: {e}")
            return None

    def get_foreign_investor(self, code: str) -> Optional[Dict]:
        """
        종목별 외인기관 추정가집계를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 종목별 외인기관 추정가집계 정보

        Example:
            >>> foreign = market.get_foreign_investor("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['FOREIGN_INVESTOR'],
                tr_id="HHPTJ04160200",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"종목별 외인기관 추정가집계 조회 실패: {e}")
            return None

    def get_foreign_trade(self, code: str) -> Optional[Dict]:
        """
        외국계 매매종목 가집계를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 외국계 매매종목 가집계 정보

        Example:
            >>> foreign_trade = market.get_foreign_trade("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['FOREIGN_TRADE'],
                tr_id="FHKST644100C0",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"외국계 매매종목 가집계 조회 실패: {e}")
            return None

    def get_foreign_net_buy(self, code: str) -> Optional[Dict]:
        """
        종목별 외국계 순매수추이를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 종목별 외국계 순매수추이 정보

        Example:
            >>> net_buy = market.get_foreign_net_buy("005930")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['FOREIGN_NET_BUY'],
                tr_id="FHKST644400C0",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"종목별 외국계 순매수추이 조회 실패: {e}")
            return None

    def get_market_money(self) -> Optional[Dict]:
        """
        국내 증시자금 종합을 조회합니다.

        Returns:
            Optional[Dict]: 국내 증시자금 종합 정보

        Example:
            >>> money = market.get_market_money()
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['MARKET_MONEY'],
                tr_id="FHKST649100C0",
                params={}
            )
        except Exception as e:
            logger.error(f"국내 증시자금 종합 조회 실패: {e}")
            return None

    def get_volume_rank(self) -> Optional[Dict]:
        """
        거래량 순위를 조회합니다. (Postman 콜렉션 기준)
        """
        # Postman 콜렉션 기준으로 엔드포인트/파라미터/트랜잭션ID 일치
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/volume-rank",  # Postman 기준
            tr_id="FHPST01710000",  # Postman 기준
            params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0002",  # Postman 예시값
                "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
                "FID_TRGT_EXLS_CLS_CODE": "000000",
                "FID_INPUT_PRICE_1": "0",
                "FID_INPUT_PRICE_2": "0",
                "FID_VOL_CNT": "0",
                "FID_INPUT_DATE_1": "0"
            }
        )

    def get_price_rank(self) -> Optional[Dict]:
        """
        등락률 순위를 조회합니다. (Postman 콜렉션 기준)
        """
        # Postman 콜렉션 기준으로 엔드포인트/파라미터 일치 (트랜잭션ID는 공식문서 참고 필요)
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/ranking/fluctuation",  # Postman 기준
            tr_id="FHPST01700000",  # 실제 트랜잭션ID는 공식문서 참고 필요
            params={
            "fid_cond_mrkt_div_code": "J",
                "fid_cond_scr_div_code": "20170",
                "fid_input_iscd": "0000",
                "fid_rank_sort_cls_code": "0",
                "fid_input_cnt_1": "0",
                "fid_prc_cls_code": "0",
                "fid_input_price_1": "",
                "fid_input_price_2": "",
                "fid_vol_cnt": "",
                "fid_trgt_cls_code": "0",
                "fid_trgt_exls_cls_code": "0",
                "fid_div_cls_code": "0",
                "fid_rsfl_rate1": "",
                "fid_rsfl_rate2": ""
            }
        )

    def get_profit_rank(self) -> Optional[Dict]:
        """
        수익자산지표 순위를 조회합니다.

        Returns:
            Optional[Dict]: 수익자산지표 순위 정보

        Example:
            >>> profit = market.get_profit_rank()
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['PROFIT_RANK'],
                tr_id="FHPST01730000",
                params={}
            )
        except Exception as e:
            logger.error(f"수익자산지표 순위 조회 실패: {e}")
            return None

    def get_overseas_price(self, code: str) -> Optional[Dict]:
        """
        해외주식 기간별시세를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 해외주식 기간별시세 정보

        Example:
            >>> overseas = market.get_overseas_price("AAPL")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['OVERSEAS_PRICE'],
                tr_id="HHDFS76240000",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"해외주식 기간별시세 조회 실패: {e}")
            return None

    def get_overseas_price_detail(self, code: str) -> Optional[Dict]:
        """
        해외주식 종목/지수/환율기간별시세를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 해외주식 종목/지수/환율기간별시세 정보

        Example:
            >>> detail = market.get_overseas_price_detail("AAPL")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['OVERSEAS_PRICE_DETAIL'],
                tr_id="FHKST03030100",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"해외주식 종목/지수/환율기간별시세 조회 실패: {e}")
            return None

    def get_overseas_news(self) -> Optional[Dict]:
        """
        해외뉴스종합을 조회합니다.

        Returns:
            Optional[Dict]: 해외뉴스종합 정보

        Example:
            >>> news = market.get_overseas_news()
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['OVERSEAS_NEWS'],
                tr_id="HHPSTH60100C1",
                params={}
            )
        except Exception as e:
            logger.error(f"해외뉴스종합 조회 실패: {e}")
            return None

    def get_overseas_right(self, code: str) -> Optional[Dict]:
        """
        해외주식 권리종합을 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 해외주식 권리종합 정보

        Example:
            >>> right = market.get_overseas_right("AAPL")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['OVERSEAS_RIGHT'],
                tr_id="HHDFS78330900",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"해외주식 권리종합 조회 실패: {e}")
            return None

    def get_bond_price(self, code: str) -> Optional[Dict]:
        """
        장내채권 기간별시세를 조회합니다.

        Args:
            code (str): 종목코드

        Returns:
            Optional[Dict]: 장내채권 기간별시세 정보

        Example:
            >>> bond = market.get_bond_price("KR1035000C97")
        """
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['BOND_PRICE'],
                tr_id="FHKBJ773701C0",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
            )
        except Exception as e:
            logger.error(f"장내채권 기간별시세 조회 실패: {e}")
            return None
    
    def get_stock_price_detail(self, code: str) -> Optional[Dict]:
        """
        종목 상세 정보를 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 종목 상세 정보

        Example:
            >>> detail = market.get_stock_price_detail("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['STOCK_PRICE_2'],
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_time_conclusion(self, code: str, hour: str = "115959") -> Optional[Dict]:
        """
        시간별 체결 정보를 조회합니다.

        Args:
            code (str): 종목 코드
            hour (str): 시간 (기본값: "115959")

        Returns:
            Optional[Dict]: 시간별 체결 정보

        Example:
            >>> conclusion = market.get_time_conclusion("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['TIME_CONCLUSION'],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour
            }
        )

    def get_overtime_conclusion(self, code: str) -> Optional[Dict]:
        """
        시간외 체결 정보를 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 시간외 체결 정보

        Example:
            >>> conclusion = market.get_overtime_conclusion("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['OVERTIME_CONCLUSION'],
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_daily_chart(self, code: str, start_date: str, end_date: str) -> Optional[Dict]:
        """
        일별 차트 정보를 조회합니다.

        Args:
            code (str): 종목 코드
            start_date (str): 시작일자 (YYYYMMDD)
            end_date (str): 종료일자 (YYYYMMDD)

        Returns:
            Optional[Dict]: 일별 차트 정보

        Example:
            >>> chart = market.get_daily_chart("005930", "20220101", "20220809")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['DAILY_CHART'],
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "1"
            }
        )

    def get_index_chart(self, code: str = "001") -> Optional[Dict]:
        """
        지수 차트 정보를 조회합니다.

        Args:
            code (str): 지수 코드 (기본값: "001" - KOSPI)

        Returns:
            Optional[Dict]: 지수 차트 정보

        Example:
            >>> chart = market.get_index_chart("2001")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['INDEX_CHART'],
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": code,
                "FID_PW_DATA_INCU_YN": "Y"
            }
        )

    # 기존 거래량 파워 메서드는 실제로는 체결강도 랭킹 API가 아님을 확인하여 주석 처리합니다.
    # def get_volume_power(self, code: str) -> Dict:
    #     """
    #     거래량 파워 정보를 조회합니다. (실제 미지원)
    #     """
    #     # 실제로는 체결강도 랭킹 API가 필요함
    #     pass  # 미구현

    def get_volume_power_ranking(self,
                                 fid_cond_mrkt_div_code: str = "J",
                                 fid_cond_scr_div_code: str = "20168",
                                 fid_input_iscd: str = "0000",
                                 fid_div_cls_code: str = "0",
                                 fid_input_price_1: str = "",
                                 fid_input_price_2: str = "",
                                 fid_vol_cnt: str = "0",
                                 fid_trgt_exls_cls_code: str = "0",
                                 fid_trgt_cls_code: str = "0") -> dict:
        """
        체결강도(체결강도 랭킹) 조회 API
        Postman 명세 기준으로 파라미터와 헤더를 맞춰 요청합니다.
        
        Args:
            fid_cond_mrkt_div_code (str): 시장구분코드 (기본값: J)
            fid_cond_scr_div_code (str): 스크리닝구분코드 (기본값: 20168)
            fid_input_iscd (str): 종목코드 (기본값: 0000)
            fid_div_cls_code (str): 구분코드 (기본값: 0)
            fid_input_price_1 (str): 입력가격1 (기본값: 공란)
            fid_input_price_2 (str): 입력가격2 (기본값: 공란)
            fid_vol_cnt (str): 거래량수량 (기본값: 0)
            fid_trgt_exls_cls_code (str): 제외대상구분코드 (기본값: 0)
            fid_trgt_cls_code (str): 대상구분코드 (기본값: 0)
        Returns:
            dict: 체결강도 랭킹 결과
        """
        # 변경 사유: 기존 거래량 파워 API는 실제로는 체결강도 랭킹 API임을 Postman 명세로 확인함
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/ranking/volume-power",
            tr_id="FHPST01680000",
            params={
                "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
                "fid_cond_scr_div_code": fid_cond_scr_div_code,
                "fid_input_iscd": fid_input_iscd,
                "fid_div_cls_code": fid_div_cls_code,
                "fid_input_price_1": fid_input_price_1,
                "fid_input_price_2": fid_input_price_2,
                "fid_vol_cnt": fid_vol_cnt,
                "fid_trgt_exls_cls_code": fid_trgt_exls_cls_code,
                "fid_trgt_cls_code": fid_trgt_cls_code
            },
            headers={
                "content-type": "application/json"
            }
        )

    def get_market_fluctuation(self) -> Optional[Dict]:
        """
        시장 변동성 정보를 조회합니다.

        Returns:
            Optional[Dict]: 시장 변동성 정보

        Example:
            >>> fluctuation = market.get_market_fluctuation()
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['MARKET_FLUCTUATION'],
            tr_id="FHKST01010600",
            params={
            "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "0000"
            }
        )

    def get_market_rankings(self) -> Optional[Dict]:
        """
        시장 순위 정보를 조회합니다.

        Returns:
            Optional[Dict]: 시장 순위 정보

        Example:
            >>> rankings = market.get_market_rankings()
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['MARKET_RANKINGS'],
            tr_id="FHKST01010700"
        )

    def get_member_transaction(self, code: str, mem_code: str) -> Optional[pd.DataFrame]:
        """
        회원사 거래 정보를 조회합니다.

        Args:
            code (str): 종목 코드
            mem_code (str): 회원사 코드

        Returns:
            Optional[pd.DataFrame]: 회원사 거래 정보 DataFrame

        Example:
            >>> transaction = market.get_member_transaction("005930", "99999")
        """
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        try:
            response = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-member-daily",
                tr_id="FHPST04540000",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code,
                    "FID_INPUT_ISCD_2": mem_code,
                    "FID_INPUT_DATE_1": start_date,
                    "FID_INPUT_DATE_2": today,
                    "FID_SCTN_CLS_CODE": ""
                }
            )
            
            if not response or response.get('rt_cd') != '0':
                logging.error(f"회원사 매매 데이터 조회 실패: {response}")
                return None
                
            output = response.get('output', [])
            if not output:
                logging.warning(f"회원사 매매 데이터가 없습니다: {code}")
                return None
                
            # DataFrame 변환
            df = pd.DataFrame(output)
            
            # 컬럼명 한글로 변경
            column_mapping = {
                'stck_bsop_date': '거래일자',
                'mbrn_nm': '회원사명',
                'shnu_qty': '매수수량',
                'seln_qty': '매도수량',
                'ntby_qty': '순매수수량',
                'shnu_amt': '매수금액',
                'seln_amt': '매도금액',
                'ntby_amt': '순매수금액'
            }
            df = df.rename(columns=column_mapping)
            
            # 숫자형 컬럼 변환
            numeric_columns = ['매수수량', '매도수량', '순매수수량', '매수금액', '매도금액', '순매수금액']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logging.error(f"회원사 매매 데이터 처리 중 오류 발생: {e}")
            return None

    def get_expected_closing_price(self, code: str, scr_div_code: str = "11173", blng_cls_code: str = "0", rank_sort_cls_code: str = "0") -> Optional[Dict]:
        """
        예상 종가 정보를 조회합니다.

        Args:
            code (str): 종목 코드
            scr_div_code (str): 화면 구분 코드 (기본값: "11173")
            blng_cls_code (str): 소속 구분 코드 (기본값: "0")
            rank_sort_cls_code (str): 순위 정렬 구분 코드 (기본값: "0")

        Returns:
            Optional[Dict]: 예상 종가 정보

        Example:
            >>> price = market.get_expected_closing_price("0001")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['EXPECTED_CLOSING_PRICE'],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": scr_div_code,
                "FID_INPUT_ISCD": code,
                "FID_BLNG_CLS_CODE": blng_cls_code,
                "FID_RANK_SORT_CLS_CODE": rank_sort_cls_code
            }
        )

    def fetch_minute_data(self, code: str) -> Optional[Dict]:
        """
        분봉 시세를 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 분봉 시세 정보

        Example:
            >>> minute_data = market.fetch_minute_data("005930")
        """
        return self.client.make_request(
            endpoint=API_ENDPOINTS['STOCK_MINUTE'],
            tr_id="FHKST03010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": "0900",
                "FID_PW_DATA_INCU_YN": "N"
            }
        )

    def get_program_trade_hourly_trend(self, code: str) -> Optional[Dict]:
        """
        시간별 프로그램 매매 추이를 조회합니다.

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 시간별 프로그램 매매 추이 정보

        Example:
            >>> trend = market.get_program_trade_hourly_trend("005930")
        """
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock",
            tr_id="FHPPG04650101",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_pgm_trade(self, code: str, ref_date: Optional[str] = None) -> Optional[Dict]:
        """
        프로그램 매매 정보를 조회합니다.

        Args:
            code (str): 종목 코드
            ref_date (Optional[str]): 기준일자 (YYYYMMDD)

        Returns:
            Optional[Dict]: 프로그램 매매 정보

        Example:
            >>> pgm_trade = market.get_pgm_trade("005930")
        """
        if ref_date is None:
            from datetime import datetime
            ref_date = datetime.now().strftime("%Y%m%d")

        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock",
            tr_id="FHPPG04650100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": ref_date
            }
        )

        if not response or 'output' not in response:
            return None

        return response

    def is_holiday(self, date: str) -> bool:
        """
        휴장일 여부를 확인합니다.

        Args:
            date (str): 확인할 날짜 (YYYYMMDD)

        Returns:
            bool: 휴장일 여부

        Example:
            >>> is_holiday = market.is_holiday("20240615")
        """
        try:
            holiday_info = self.get_holiday_info()
            if not holiday_info or 'output' not in holiday_info:
                return False
            return date in holiday_info['output']
        except Exception as e:
            logging.error(f"휴장일 확인 중 오류 발생: {e}")
            return False

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
        test_and_log("get_orderbook", lambda: stock.get_orderbook(test_code))
        test_and_log("get_stock_member", lambda: stock.get_stock_member(test_code))
        test_and_log("get_stock_investor", lambda: stock.get_stock_investor(test_code))
        test_and_log("get_holiday_info", lambda: stock.get_holiday_info())
        test_and_log("get_stock_basic", lambda: stock.get_stock_basic(test_code))
        test_and_log("get_stock_income", lambda: stock.get_stock_income(test_code))
        test_and_log("get_stock_financial", lambda: stock.get_stock_financial(test_code))
        test_and_log("get_stock_stability", lambda: stock.get_stock_stability(test_code))
        test_and_log("get_stock_growth", lambda: stock.get_stock_growth(test_code))
        test_and_log("get_stock_estimate", lambda: stock.get_stock_estimate(test_code))
        test_and_log("get_stock_broker_opinion", lambda: stock.get_stock_broker_opinion(test_code))
        test_and_log("get_stock_opinion", lambda: stock.get_stock_opinion(test_code))
        test_and_log("get_domestic_investor", lambda: stock.get_domestic_investor(test_code))
        test_and_log("get_foreign_investor", lambda: stock.get_foreign_investor(test_code))
        test_and_log("get_foreign_trade", lambda: stock.get_foreign_trade(test_code))
        test_and_log("get_foreign_net_buy", lambda: stock.get_foreign_net_buy(test_code))
        test_and_log("get_market_money", lambda: stock.get_market_money())
        test_and_log("get_volume_rank", lambda: stock.get_volume_rank())
        test_and_log("get_price_rank", lambda: stock.get_price_rank())
        test_and_log("get_profit_rank", lambda: stock.get_profit_rank())
        test_and_log("get_overseas_price", lambda: stock.get_overseas_price(test_code))
        test_and_log("get_overseas_price_detail", lambda: stock.get_overseas_price_detail(test_code))
        test_and_log("get_overseas_news", lambda: stock.get_overseas_news())
        test_and_log("get_overseas_right", lambda: stock.get_overseas_right(test_code))
        test_and_log("get_bond_price", lambda: stock.get_bond_price(test_code))
        test_and_log("get_stock_price_detail", lambda: stock.get_stock_price_detail(test_code))
        test_and_log("get_time_conclusion", lambda: stock.get_time_conclusion(test_code))
        test_and_log("get_overtime_conclusion", lambda: stock.get_overtime_conclusion(test_code))
        test_and_log("get_daily_chart", lambda: stock.get_daily_chart(test_code, "20220101", "20220809"))
        test_and_log("get_index_chart", lambda: stock.get_index_chart(test_code))
        test_and_log("get_volume_power_ranking", lambda: stock.get_volume_power_ranking())
        test_and_log("get_market_fluctuation", lambda: stock.get_market_fluctuation())
        test_and_log("get_market_rankings", lambda: stock.get_market_rankings())
        test_and_log("get_member_transaction", lambda: stock.get_member_transaction(test_code, "99999"))
        test_and_log("get_expected_closing_price", lambda: stock.get_expected_closing_price(test_code))
        test_and_log("fetch_minute_data", lambda: stock.fetch_minute_data(test_code))
        test_and_log("get_program_trade_hourly_trend", lambda: stock.get_program_trade_hourly_trend(test_code))
        test_and_log("get_pgm_trade", lambda: stock.get_pgm_trade(test_code))
        test_and_log("is_holiday", lambda: stock.is_holiday("20240615"))
        print("\n📊 테스트 요약")
        for name, success, error in results:
            flag = "✅" if success else "❌"
            msg = f" ({error})" if error else ""
            print(f"- {name.ljust(35, '.')} {flag}{msg}")
    except Exception as e:
        logging.exception("Test failed")

# 기존 호환성을 위해 별칭 제공
MarketAPI = StockAPI
StockMarketAPI = StockAPI
