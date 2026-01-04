"""
Stock API Facade - 주식 관련 API 통합 인터페이스

Facade Pattern을 적용하여 복잡한 하위 시스템을 단순화
- StockPriceAPI: 시세 정보
- StockMarketAPI: 시장 정보
- StockInvestorAPI: 투자자 정보
- 기존 StockAPI와 동일한 인터페이스 유지 (하위 호환성)
"""

from typing import Any, Dict, List, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .investor_api import StockInvestorAPI
from .market_api import StockMarketAPI
from .price_api import StockPriceAPI


class StockAPI(BaseAPI):
    """
    주식 관련 API 통합 Facade 클래스

    하위 시스템들을 통합하여 기존 인터페이스와 호환성을 유지하면서
    내부적으로는 책임 분산된 구조를 제공합니다.

    Attributes:
        price_api (StockPriceAPI): 시세 조회 전담 API
        market_api (StockMarketAPI): 시장 정보 전담 API
        investor_api (StockInvestorAPI): 투자자 정보 전담 API
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """
        StockAPI Facade 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict, optional): 계좌 정보
            enable_cache (bool): 캐시 사용 여부 (기본: True)
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부 (내부 사용)
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

        # 하위 시스템 초기화 - Agent를 통해 생성된 경우 하위 API도 _from_agent=True로 초기화
        self.price_api = StockPriceAPI(client, account_info, _from_agent=_from_agent)
        self.market_api = StockMarketAPI(client, account_info, _from_agent=_from_agent)
        self.investor_api = StockInvestorAPI(
            client, account_info, _from_agent=_from_agent
        )

    # ===== 시세 관련 메서드 (StockPriceAPI 위임) =====

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        return self.price_api.get_stock_price(code)

    def inquire_daily_price(
        self, code: str, period: str = "D", org_adj_prc: str = "1"
    ) -> Optional[Dict]:
        """주식현재가 일자별 조회 (최근 30건)"""
        return self.price_api.inquire_daily_price(code, period, org_adj_prc)

    def inquire_daily_itemchartprice(
        self,
        code: str,
        start_date: str = "",
        end_date: str = "",
        period: str = "D",
        org_adj_prc: str = "1",
    ) -> Optional[Dict]:
        """국내주식 기간별 시세 조회 (날짜 범위 지정)"""
        return self.price_api.inquire_daily_itemchartprice(
            code, start_date, end_date, period, org_adj_prc
        )

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """주식 호가 정보 조회"""
        return self.price_api.get_orderbook(code)

    def get_orderbook_raw(self, code: str) -> Optional[Dict]:
        """호가 정보 원시 데이터 조회"""
        return self.price_api.get_orderbook_raw(code)

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """분봉 시세 조회"""
        return self.price_api.get_minute_price(code, hour)

    def get_daily_minute_price(
        self, code: str, date: str, hour: str = "153000"
    ) -> Optional[Dict]:
        """특정일 분봉 시세 조회"""
        return self.price_api.get_daily_minute_price(code, date, hour)

    def inquire_price(self, code: str, market: str = "J") -> Optional[Dict]:
        """주식현재가 시세 조회 (추가 정보 포함)

        [변경 이유] price_api에 구현된 시세 관련 메서드를 Facade에서 일관되게 노출하여
        Agent 파사드를 통해 접근 시 AttributeError가 발생하지 않도록 위임합니다.
        """
        return self.price_api.inquire_price(code, market)

    def inquire_price_2(self, code: str, market: str = "J") -> Optional[Dict]:
        """주식현재가 시세2 조회 (추가 정보 포함)"""
        return self.price_api.inquire_price_2(code, market)

    def inquire_ccnl(self, code: str, market: str = "J") -> Optional[Dict]:
        """주식현재가 체결 조회 (최근 30건)"""
        return self.price_api.inquire_ccnl(code, market)

    def inquire_time_itemconclusion(
        self, code: str, hour: str = "153000", market: str = "J"
    ) -> Optional[Dict]:
        """주식현재가 당일시간대별체결 조회"""
        return self.price_api.inquire_time_itemconclusion(code, hour, market)

    # ===== 시장 정보 관련 메서드 (StockMarketAPI 위임) =====

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """시장 변동성 정보 조회"""
        return self.market_api.get_market_fluctuation()

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 기준 종목 순위 조회"""
        return self.market_api.get_market_rankings(volume)

    def get_volume_power(self, volume: int = 0) -> Optional[Dict]:
        """체결강도 순위 조회"""
        return self.market_api.get_volume_power(volume)

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """종목 기본 정보 조회"""
        return self.market_api.get_stock_info(ticker)

    # ===== 투자자 정보 관련 메서드 (StockInvestorAPI 위임) =====

    def get_stock_investor(
        self, ticker: str = "", retries: int = 10, force_refresh: bool = False
    ) -> Optional[Dict]:
        """투자자별 매매동향 조회 (원시 dict 반환)

        Note:
            - [변경 이유] StockInvestorAPI.get_stock_investor가 dict를 반환하므로 Facade도 일관성을 위해 dict로 타입을 맞춤
        """
        return self.investor_api.get_stock_investor(ticker, retries, force_refresh)

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """거래원별 매매 정보 조회"""
        return self.investor_api.get_stock_member(ticker, retries)

    def get_member_transaction(
        self, code: str, mem_code: str
    ) -> Optional[Dict[str, Any]]:
        """특정 거래원의 매매 내역 조회"""
        return self.investor_api.get_member_transaction(code, mem_code)

    def get_frgnmem_pchs_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """외국인 매수 추이 조회"""
        return self.investor_api.get_frgnmem_pchs_trend(code)

    def get_foreign_broker_net_buy(
        self,
        code: str,
        foreign_brokers: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> Optional[tuple]:
        """외국계 증권사 순매수 집계"""
        return self.investor_api.get_foreign_broker_net_buy(code, foreign_brokers, date)

    def get_frgnmem_trade_estimate(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_cond_scr_div_code: str = "16441",
        fid_input_iscd: str = "0000",
        fid_rank_sort_cls_code: str = "0",
        fid_rank_sort_cls_code_2: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """외국계 매매종목 가집계 조회"""
        return self.investor_api.get_frgnmem_trade_estimate(
            fid_cond_mrkt_div_code,
            fid_cond_scr_div_code,
            fid_input_iscd,
            fid_rank_sort_cls_code,
            fid_rank_sort_cls_code_2,
        )

    def get_frgnmem_trade_trend(
        self,
        fid_cond_scr_div_code: str = "20432",
        fid_cond_mrkt_div_code: str = "J",
        fid_input_iscd: str = "",
        fid_input_iscd_2: str = "99999",
        fid_mrkt_cls_code: str = "A",
        fid_vol_cnt: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """회원사 실시간 매매동향(틱) 조회"""
        return self.investor_api.get_frgnmem_trade_trend(
            fid_cond_scr_div_code,
            fid_cond_mrkt_div_code,
            fid_input_iscd,
            fid_input_iscd_2,
            fid_mrkt_cls_code,
            fid_vol_cnt,
        )

    def get_investor_program_trade_today(
        self, mrkt_div_cls_code: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """프로그램매매 투자자매매동향(당일) 조회"""
        return self.investor_api.get_investor_program_trade_today(mrkt_div_cls_code)

    def get_investor_trade_by_stock_daily(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_input_iscd: str = "",
        fid_input_date_1: str = "",
        fid_org_adj_prc: str = "",
        fid_etc_cls_code: str = "",
    ) -> Optional[Dict[str, Any]]:
        """종목별 투자자매매동향(일별) 조회"""
        return self.investor_api.get_investor_trade_by_stock_daily(
            fid_cond_mrkt_div_code,
            fid_input_iscd,
            fid_input_date_1,
            fid_org_adj_prc,
            fid_etc_cls_code,
        )

    def get_investor_trend_estimate(
        self, mksc_shrn_iscd: str
    ) -> Optional[Dict[str, Any]]:
        """종목별 외국인/기관 추정가집계 조회"""
        return self.investor_api.get_investor_trend_estimate(mksc_shrn_iscd)

    def get_index_minute_data(
        self,
        fid_input_iscd: str = "0001",
        fid_input_hour_1: str = "120",
        fid_cond_mrkt_div_code: str = "U",
        fid_pw_data_incu_yn: str = "Y",
        fid_etc_cls_code: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        업종 분봉 조회

        Args:
            fid_input_iscd (str): 종목코드 (0001: 종합, 1001: 코스닥종합)
            fid_input_hour_1 (str): 입력 시간(초) - 조회 시간 범위
            fid_cond_mrkt_div_code (str): 시장 분류 코드 (U: 업종)
            fid_pw_data_incu_yn (str): 과거 데이터 포함 여부 (Y/N)
            fid_etc_cls_code (str): 기타 구분 코드

        Returns:
            Dict containing:
                - output1: 업종 현재가 정보
                - output2: 분봉 데이터 리스트
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
            "FID_INPUT_ISCD": fid_input_iscd,
            "FID_INPUT_HOUR_1": fid_input_hour_1,
            "FID_PW_DATA_INCU_YN": fid_pw_data_incu_yn,
            "FID_ETC_CLS_CODE": fid_etc_cls_code,
        }
        result: Optional[Dict[str, Any]] = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-indexchartprice",
            tr_id="FHKUP03500200",
            params=params,
            method="GET",
        )
        if result:
            if "rt_cd" not in result:
                result["rt_cd"] = ""
            if "msg1" not in result:
                result["msg1"] = ""
        return result

    def get_index_timeprice(
        self,
        fid_input_iscd: str = "1029",
        fid_input_hour_1: str = "600",
        fid_cond_mrkt_div_code: str = "U",
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 시간별 지수 조회 (기본값: KOSPI200)

        Args:
            fid_input_iscd (str): 종목코드 (기본값 "1029": KOSPI200, "1001": KOSPI, "2001": KOSDAQ)
            fid_input_hour_1 (str): 입력 시간(초) - 조회 시간 범위 (기본값 "600": 10분봉)
            fid_cond_mrkt_div_code (str): 시장 분류 코드 (기본값 "U": 업종)

        Returns:
            Dict containing:
                - output1: 업종 현재가 정보
                - output2: 시간별 지수 데이터 리스트
        """
        return self.price_api.get_index_timeprice(
            fid_input_iscd,
            fid_input_hour_1,
            fid_cond_mrkt_div_code,
        )

    def get_time_index_chart_price(
        self,
        index_code: str = "0001",
        period_div: str = "4",
    ) -> Optional[Dict[str, Any]]:
        """
        업종 지수 차트 조회 (일봉/분봉)

        장외 시간에도 과거 데이터 조회 가능 (fid_pw_data_incu_yn=Y 내장)

        Args:
            index_code (str): 업종코드 (예: "0001"=KOSPI종합, "0013"=전기전자, "1001"=KOSDAQ)
            period_div (str): 기간구분
                - "1": 1분봉
                - "2": 3분봉
                - "3": 5분봉
                - "4": 10분봉 (일봉 데이터 30일 반환)
                - "5": 15분봉
                - "6": 30분봉
                - "7": 60분봉

        Returns:
            Dict containing:
                - output1: 업종 현재가 정보
                - output2: 일별/분별 지수 데이터 리스트
                    - stck_bsop_date: 날짜 (YYYYMMDD)
                    - bstp_nmix_prpr: 종가
                    - bstp_nmix_oprc: 시가
                    - bstp_nmix_hgpr: 고가
                    - bstp_nmix_lwpr: 저가
                    - acml_vol: 거래량

        Example:
            >>> stock_api.get_time_index_chart_price("0001", "4")  # KOSPI 일봉 30일
            >>> stock_api.get_time_index_chart_price("0013", "4")  # 전기전자 일봉 30일
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-indexchartprice",
            tr_id="FHKUP03500100",
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": index_code,
                "fid_input_date_1": "",
                "fid_input_date_2": "",
                "fid_period_div_code": period_div,
                "fid_pw_data_incu_yn": "Y",  # 과거 데이터 포함 (장외 시간에도 조회 가능)
            },
        )

    def get_future_option_price(
        self, market_div_code: str = "F", input_iscd: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        선물옵션 시세 조회

        [변경 이유] StockPriceAPI에 구현된 선물옵션 시세 조회 메서드를 Facade에서 일관되게 노출하여
        Agent 파사드를 통해 접근 시 명시적으로 사용 가능하도록 합니다.

        Args:
            market_div_code (str): 시장분류코드 ("F": 지수선물, "O": 지수옵션, "JF": 주식선물, "JO": 주식옵션)
            input_iscd (Optional[str]): 선물옵션종목코드 (None이면 자동으로 KOSPI200 선물코드 사용)

        Returns:
            Optional[Dict[str, Any]]: 선물옵션 시세 데이터
        """
        return self.price_api.get_future_option_price(market_div_code, input_iscd)

    # ===== 추가 Price API 메서드 위임 =====

    def inquire_index_price(self, index_code: str, market: str = "U") -> Optional[Dict]:
        """
        국내업종 현재지수 조회

        DEPRECATION WARNING:
            이 메서드는 deprecated되었습니다. inquire_index_timeprice() 사용을 권장합니다.

        TODO: v2.0에서 제거 예정
        """
        return self.price_api.inquire_index_price(index_code, market)

    def inquire_index_tickprice(
        self, index_code: str, market: str = "U"
    ) -> Optional[Dict]:
        """국내업종 시간별지수(틱) 조회"""
        return self.price_api.inquire_index_tickprice(index_code, market)

    def inquire_index_timeprice(
        self, index_code: str, market: str = "U", time_div: str = "0"
    ) -> Optional[Dict]:
        """국내업종 지수 분/일봉 시세 조회"""
        return self.price_api.inquire_index_timeprice(index_code, market, time_div)

    def inquire_index_category_price(
        self,
        index_code: str,
        screen_code: str = "20214",
        market_cls: str = "K",
        belong_cls: str = "0",
        market: str = "U",
    ) -> Optional[Dict]:
        """업종별 전체시세 조회"""
        return self.price_api.inquire_index_category_price(
            index_code, screen_code, market_cls, belong_cls, market
        )

    def inquire_daily_overtimeprice(
        self, code: str, market: str = "J"
    ) -> Optional[Dict]:
        """국내주식 당일 시간외 체결 조회"""
        return self.price_api.inquire_daily_overtimeprice(code, market)

    def inquire_elw_price(self, code: str, market: str = "W") -> Optional[Dict]:
        """ELW 현재가 시세 조회"""
        return self.price_api.inquire_elw_price(code, market)

    def inquire_overtime_asking_price(
        self, code: str, market: str = "J"
    ) -> Optional[Dict]:
        """국내주식 시간외호가 조회"""
        return self.price_api.inquire_overtime_asking_price(code, market)

    def inquire_overtime_price(self, code: str, market: str = "J") -> Optional[Dict]:
        """국내주식 시간외현재가 조회"""
        return self.price_api.inquire_overtime_price(code, market)

    def inquire_vi_status(
        self,
        div_cls: str = "0",
        screen_code: str = "20139",
        market: str = "0",
        stock_code: str = "",
        sort_cls: str = "0",
        date: str = "",
        target_cls: str = "0",
        exclude_cls: str = "0",
    ) -> Optional[Dict]:
        """변동성완화장치(VI) 현황 조회"""
        return self.price_api.inquire_vi_status(
            div_cls,
            screen_code,
            market,
            stock_code,
            sort_cls,
            date,
            target_cls,
            exclude_cls,
        )

    def get_intraday_price(self, code: str, date: str = "") -> Optional[Dict]:
        """주식 당일 분봉 데이터 조회

        Args:
            code: 종목코드 6자리
            date: 조회 날짜 (YYYYMMDD 형식, 기본값: 오늘)
        """
        from datetime import datetime

        if not date:
            date = datetime.now().strftime("%Y%m%d")
        return self.price_api.get_intraday_price(code, date)

    def get_stock_ccnl(self, code: str, retries: int = 10) -> Optional[Dict]:
        """주식현재가 체결 조회

        Args:
            code: 종목코드 6자리
            retries: 재시도 횟수 (미사용, 호환성 유지용)
        """
        return self.price_api.get_stock_ccnl(code, retries)

    def daily_credit_balance(
        self, code: str, market: str = "J", screen_code: str = "20476", date: str = ""
    ) -> Optional[Dict]:
        """일자별 신용잔고 조회"""
        return self.price_api.daily_credit_balance(code, market, screen_code, date)

    def disparity(
        self,
        market: str = "J",
        screen_code: str = "20178",
        div_cls: str = "0",
        sort_code: str = "0",
        hour_cls: str = "5",
        stock_code: str = "0000",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_from: str = "",
        volume: str = "",
        price_to: str = "",
    ) -> Optional[Dict]:
        """국내주식 이격도 순위 조회"""
        return self.price_api.disparity(
            market,
            screen_code,
            div_cls,
            sort_code,
            hour_cls,
            stock_code,
            target_cls,
            exclude_cls,
            price_from,
            volume,
            price_to,
        )

    def dividend_rate(
        self,
        cts_area: str = "",
        gb1: str = "0",
        upjong: str = "",
        gb2: str = "0",
        gb3: str = "0",
        f_dt: str = "",
        t_dt: str = "",
        gb4: str = "0",
    ) -> Optional[Dict]:
        """배당률 순위 조회"""
        return self.price_api.dividend_rate(
            cts_area, gb1, upjong, gb2, gb3, f_dt, t_dt, gb4
        )

    def fluctuation(
        self,
        market: str = "J",
        screen_code: str = "20171",
        stock_code: str = "",
        sort_code: str = "0",
        count: str = "0",
        price_cls: str = "",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
        target_cls: str = "0",
        exclude_cls: str = "0",
        div_cls: str = "0",
        rate_from: str = "",
        rate_to: str = "",
    ) -> Optional[Dict]:
        """국내주식 등락률 순위 조회"""
        return self.price_api.fluctuation(
            market,
            screen_code,
            stock_code,
            sort_code,
            count,
            price_cls,
            price_from,
            price_to,
            volume,
            target_cls,
            exclude_cls,
            div_cls,
            rate_from,
            rate_to,
        )

    def foreign_institution_total(
        self,
        market: str = "J",
        screen_code: str = "20449",
        stock_code: str = "0000",
        div_cls: str = "0",
        sort_cls: str = "0",
        etc_cls: str = "0",
    ) -> Optional[Dict]:
        """외국인/기관 종합 동향 조회"""
        return self.price_api.foreign_institution_total(
            market, screen_code, stock_code, div_cls, sort_cls, etc_cls
        )

    def intstock_multprice(self, codes: str, market: str = "J") -> Optional[Dict]:
        """복수종목 현재가 조회"""
        return self.price_api.intstock_multprice(codes, market)

    def market_cap(
        self,
        market: str = "J",
        screen_code: str = "20174",
        stock_code: str = "",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
    ) -> Optional[Dict]:
        """시가총액 순위 조회"""
        return self.price_api.market_cap(
            market,
            screen_code,
            stock_code,
            div_cls,
            target_cls,
            exclude_cls,
            price_from,
            price_to,
            volume,
        )

    def market_time(self) -> Optional[Dict]:
        """국내 증시 거래시간 조회"""
        return self.price_api.market_time()

    def market_value(self, code: str, market: str = "J") -> Optional[Dict]:
        """종목별 시가총액 조회"""
        return self.price_api.market_value(code, market)

    def news_title(
        self,
        code: str,
        news_provider: str = "",
        market_cls: str = "0",
        title_content: str = "",
        date: str = "",
        hour: str = "",
        sort_code: str = "0",
        serial_no: str = "",
    ) -> Optional[Dict]:
        """종목 뉴스 제목 조회"""
        return self.price_api.news_title(
            code,
            news_provider,
            market_cls,
            title_content,
            date,
            hour,
            sort_code,
            serial_no,
        )

    def profit_asset_index(self, index_code: str, market: str = "U") -> Optional[Dict]:
        """업종 수익/자산 지수 조회"""
        return self.price_api.profit_asset_index(index_code, market)

    def search_stock_info(self, code: str, product_type: str = "300") -> Optional[Dict]:
        """종목 기본정보 조회"""
        return self.price_api.search_stock_info(code, product_type)

    def short_sale(
        self,
        market: str = "J",
        screen_code: str = "20482",
        stock_code: str = "0000",
        period: str = "0",
        count: str = "30",
        exclude_cls: str = "0",
        target_cls: str = "0",
        volume: str = "",
        price_from: str = "",
        price_to: str = "",
    ) -> Optional[Dict]:
        """공매도 상위종목 조회"""
        return self.price_api.short_sale(
            market,
            screen_code,
            stock_code,
            period,
            count,
            exclude_cls,
            target_cls,
            volume,
            price_from,
            price_to,
        )

    def volume_rank(
        self,
        market: str = "J",
        screen_code: str = "20170",
        stock_code: str = "",
        div_cls: str = "0",
        sort_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
        date: str = "",
    ) -> Optional[Dict]:
        """거래량 순위 조회"""
        return self.price_api.volume_rank(
            market,
            screen_code,
            stock_code,
            div_cls,
            sort_cls,
            target_cls,
            exclude_cls,
            price_from,
            price_to,
            volume,
            date,
        )

    # ===== Market API 메서드 위임 =====

    def get_holiday_info(self, date: Optional[str] = None) -> Optional[Dict]:
        """휴장일 정보 조회

        Args:
            date: 조회 날짜 (YYYYMMDD 형식, None이면 당월)
        """
        return self.market_api.get_holiday_info(date)

    def is_holiday(self, date: str) -> Optional[bool]:
        """특정일 휴장일 여부 확인"""
        return self.market_api.is_holiday(date)

    def get_pbar_tratio(self, code: str, retries: int = 10) -> Optional[Dict]:
        """매물대/거래비중 조회

        Args:
            code: 종목코드 6자리
            retries: 재시도 횟수 (미사용, 호환성 유지)
        """
        return self.market_api.get_pbar_tratio(code, retries)

    def get_fluctuation_rank(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_cond_scr_div_code: str = "20171",
        fid_input_iscd: str = "0000",
        fid_rank_sort_cls_code: str = "0",
        fid_input_cnt_1: str = "0",
    ) -> Optional[Dict]:
        """등락률 순위 조회"""
        return self.market_api.get_fluctuation_rank(
            fid_cond_mrkt_div_code,
            fid_cond_scr_div_code,
            fid_input_iscd,
            fid_rank_sort_cls_code,
            fid_input_cnt_1,
        )

    def get_volume_power_rank(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_cond_scr_div_code: str = "20172",
        fid_input_iscd: str = "0000",
        fid_rank_sort_cls_code: str = "0",
    ) -> Optional[Dict]:
        """체결강도 순위 조회"""
        return self.market_api.get_volume_power_rank(
            fid_cond_mrkt_div_code,
            fid_cond_scr_div_code,
            fid_input_iscd,
            fid_rank_sort_cls_code,
        )

    def get_volume_rank(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_cond_scr_div_code: str = "20170",
        fid_input_iscd: str = "0000",
        fid_div_cls_code: str = "0",
    ) -> Optional[Dict]:
        """거래량 순위 조회"""
        return self.market_api.get_volume_rank(
            fid_cond_mrkt_div_code,
            fid_cond_scr_div_code,
            fid_input_iscd,
            fid_div_cls_code,
        )

    def __getattr__(self, name: str) -> Any:
        """하위 모듈로 동적 위임

        [변경 이유] price_api/market_api/investor_api에 존재하는 메서드가 Facade에 누락될 경우
        Agent에서 Facade를 통해 호출 시 AttributeError가 발생한다. 이를 방지하기 위해
        존재하는 하위 API로 자동 위임한다.
        """
        for api in (self.price_api, self.market_api, self.investor_api):
            if hasattr(api, name):
                return getattr(api, name)
        raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")


# 하위 호환성을 위한 별칭
StockAPIFacade = StockAPI
