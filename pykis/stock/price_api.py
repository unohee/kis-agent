"""
Stock Price API - 주식 시세 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 StockAPI에서 시세 관련 기능만 분리
- 현재가 조회
- 일별/분봉 시세
- 호가 정보
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class StockPriceAPI(BaseAPI):
    """주식 시세 조회 전용 API 클래스"""

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """
        주식 현재가 조회

        Args:
            code: 종목코드 (6자리, 예: '005930')

        Returns:
            StockPriceResponse 형식의 Dict (82개 필드):
                - output.stck_prpr: 주식 현재가
                - output.prdy_vrss: 전일 대비
                - output.prdy_vrss_sign: 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
                - output.prdy_ctrt: 전일 대비율 (%)
                - output.acml_vol: 누적 거래량
                - output.acml_tr_pbmn: 누적 거래대금
                - output.stck_oprc: 주식 시가
                - output.stck_hgpr: 주식 최고가
                - output.stck_lwpr: 주식 최저가
                - output.stck_mxpr: 주식 상한가
                - output.stck_llam: 주식 하한가
                - output.per: PER (Price Earning Ratio)
                - output.pbr: PBR (Price Book-value Ratio)
                - output.eps: EPS (Earning Per Share)
                - output.bps: BPS (Book-value Per Share)
                - output.hts_frgn_ehrt: HTS 외국인 소진율
                - output.frgn_ntby_qty: 외국인 순매수 수량
                - output.w52_hgpr: 52주일 최고가
                - output.w52_lwpr: 52주일 최저가
                - 기타 60여개 필드 (상세는 StockPriceOutput TypedDict 참조)

        Example:
            >>> price = agent.stock.get_stock_price("005930")
            >>> print(price['output']['stck_prpr'])  # 현재가
            >>> print(price['output']['per'])        # PER
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    def inquire_daily_price(
        self, code: str, period: str = "D", org_adj_prc: str = "1"
    ) -> Optional[Dict]:
        """
        주식현재가 일자별 조회 (최근 30건)

        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월)
            org_adj_prc: 수정주가구분 (0: 수정주가 미반영, 1: 수정주가 반영)

        Returns:
            DailyPriceResponse 형식의 Dict:
                - output[]: List[DailyPriceItem] (최대 30개)
                    - stck_bsop_date: 주식 영업일자 (YYYYMMDD)
                    - stck_clpr: 주식 종가
                    - stck_oprc: 주식 시가
                    - stck_hgpr: 주식 최고가
                    - stck_lwpr: 주식 최저가
                    - acml_vol: 누적 거래량

        Example:
            >>> daily = agent.stock.inquire_daily_price("005930", period="D")
            >>> for day in daily['output']:
            ...     print(day['stck_bsop_date'], day['stck_clpr'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_PRICE"],
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": org_adj_prc,
            },
        )

    def inquire_daily_itemchartprice(
        self,
        code: str,
        start_date: str = "",
        end_date: str = "",
        period: str = "D",
        org_adj_prc: str = "1",
    ) -> Optional[Dict]:
        """
        국내주식 기간별 시세 조회 (날짜 범위 지정)

        Args:
            code: 종목코드 (6자리)
            start_date: 조회 시작일자 (YYYYMMDD, 공백이면 100건 이전부터)
            end_date: 조회 종료일자 (YYYYMMDD, 공백이면 오늘까지)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가, 1: 원주가)

        Returns:
            DailyItemChartPriceResponse 형식의 Dict:
                - output1[]: List[DailyPriceItem] (최대 100개)
                    - stck_bsop_date: 주식 영업일자 (YYYYMMDD)
                    - stck_clpr: 주식 종가
                    - stck_oprc: 주식 시가
                    - stck_hgpr: 주식 최고가
                    - stck_lwpr: 주식 최저가
                    - acml_vol: 누적 거래량
                - output2: 요약 정보

        Example:
            >>> data = agent.stock.inquire_daily_itemchartprice("005930", "20240101", "20240131")
            >>> for day in data['output1']:
            ...     print(day['stck_bsop_date'], day['stck_clpr'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_ITEMCHARTPRICE"],
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": org_adj_prc,
            },
        )

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """
        주식 호가 정보 조회

        Args:
            code: 종목코드 (6자리)

        Returns:
            OrderbookResponse 형식의 Dict:
                - output.askp1~10: 매도호가 1~10
                - output.bidp1~10: 매수호가 1~10
                - output.askp_rsqn1~10: 매도호가 잔량 1~10
                - output.bidp_rsqn1~10: 매수호가 잔량 1~10
                - output.total_askp_rsqn: 총 매도호가 잔량
                - output.total_bidp_rsqn: 총 매수호가 잔량
                - output.antc_cnpr: 예상 체결가
                - output.antc_cnqn: 예상 체결량
                - output.stck_prpr: 주식 현재가

        Example:
            >>> orderbook = agent.stock.get_orderbook("005930")
            >>> print(orderbook['output']['askp1'])  # 매도1호가
            >>> print(orderbook['output']['bidp1'])  # 매수1호가
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    def get_orderbook_raw(self, code: str) -> Optional[Dict]:
        """호가 정보 원시 데이터 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """분봉 시세 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_ITEMCHARTPRICE"],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
            },
        )

    def get_daily_minute_price(
        self, code: str, date: str, hour: str = "153000"
    ) -> Optional[Dict]:
        """
        일별분봉시세조회 - 과거일자 분봉 데이터 조회 (rt_cd 메타데이터 포함)

        Args:
            code: 종목코드 (6자리)
            date: 조회일자 (YYYYMMDD)
            hour: 조회 시간 (HHMMSS, 기본값: 153000)

        Returns:
            분봉 시세 데이터 (output1: 종목정보, output2: 분봉 리스트)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_DAILYCHARTPRICE"],
            tr_id="FHKST03010230",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": "Y",
                "FID_INPUT_DATE_1": date,
                "FID_FAKE_TICK_INCU_YN": "",
            },
        )

    def inquire_time_itemconclusion(
        self, code: str, hour: str = "153000", market: str = "J"
    ) -> Optional[Dict]:
        """
        주식현재가 당일시간대별체결 조회

        Args:
            code: 종목코드 (6자리)
            hour: 조회 시간 (HHMMSS, 기본값: 153000)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            시간대별 체결 데이터 (output1: 요약, output2: 시간별 체결 리스트)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_ITEMCONCLUSION"],
            tr_id="FHPST01060000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
            },
        )

    def inquire_ccnl(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        주식현재가 체결 조회 (최근 30건)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            최근 체결 데이터 (최대 30건)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_CCNL"],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_price(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        주식현재가 시세 조회 (추가 정보 포함)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            주식현재가 시세2 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_price_2(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        주식현재가 시세2 조회 (추가 정보 포함)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            주식현재가 시세2 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE_2"],
            tr_id="FHPST01010000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def search_stock_info(self, code: str, product_type: str = "300") -> Optional[Dict]:
        """
        주식 기본정보 조회

        Args:
            code: 종목코드 (6자리, ETN의 경우 Q로 시작)
            product_type: 상품유형코드 (300:주식/ETF/ETN/ELW, 301:선물옵션, 302:채권, 306:ELS)

        Returns:
            주식 기본정보 (종목명, 업종, 상장일, 자본금 등)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["SEARCH_STOCK_INFO"],
            tr_id="CTPF1002R",
            params={
                "PRDT_TYPE_CD": product_type,
                "PDNO": code,
            },
        )

    def news_title(
        self,
        code: str = "",
        news_provider: str = "2",
        market_cls: str = "00",
        title_content: str = "",
        date: str = "",
        hour: str = "000000",
        sort_code: str = "01",
        serial_no: str = "1",
    ) -> Optional[Dict]:
        """
        종합 시황/공시 뉴스 제목 조회

        Args:
            code: 종목코드 (공백: 전체)
            news_provider: 뉴스제공업체코드 (2:전체)
            market_cls: 시장구분코드 (00:전체)
            title_content: 제목내용 (검색어)
            date: 조회날짜 (YYYYMMDD, 공백: 당일)
            hour: 조회시간 (HHMMSS)
            sort_code: 정렬코드 (01:시간순)
            serial_no: 일련번호

        Returns:
            뉴스 제목 리스트
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["NEWS_TITLE"],
            tr_id="FHKST01011800",
            params={
                "FID_NEWS_OFER_ENTP_CODE": news_provider,
                "FID_COND_MRKT_CLS_CODE": market_cls,
                "FID_INPUT_ISCD": code,
                "FID_TITL_CNTT": title_content,
                "FID_INPUT_DATE_1": date,
                "FID_INPUT_HOUR_1": hour,
                "FID_RANK_SORT_CLS_CODE": sort_code,
                "FID_INPUT_SRNO": serial_no,
            },
        )

    def fluctuation(
        self,
        market: str = "J",
        screen_code: str = "20170",
        stock_code: str = "0000",
        sort_code: str = "0",
        count: str = "30",
        price_cls: str = "0",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
        target_cls: str = "0",
        exclude_cls: str = "0",
        div_cls: str = "0",
        rate_from: str = "",
        rate_to: str = "",
    ) -> Optional[Dict]:
        """
        등락률 순위 조회

        Args:
            market: 시장구분 (J:주식, W:ELW, Q:ETF)
            screen_code: 화면코드 (20170:등락률)
            stock_code: 종목코드 (0000:전체)
            sort_code: 정렬코드 (0:상승률순)
            count: 조회건수
            price_cls: 가격구분 (0:전체)
            price_from: 가격하한
            price_to: 가격상한
            volume: 거래량하한
            target_cls: 대상구분코드 (0:전체)
            exclude_cls: 제외구분코드 (0:없음)
            div_cls: 분류구분 (0:전체)
            rate_from: 등락률하한
            rate_to: 등락률상한

        Returns:
            등락률 순위 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FLUCTUATION"],
            tr_id="FHPST01700000",
            params={
                "fid_rsfl_rate2": rate_to,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": screen_code,
                "fid_input_iscd": stock_code,
                "fid_rank_sort_cls_code": sort_code,
                "fid_input_cnt_1": count,
                "fid_prc_cls_code": price_cls,
                "fid_input_price_1": price_from,
                "fid_input_price_2": price_to,
                "fid_vol_cnt": volume,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_div_cls_code": div_cls,
                "fid_rsfl_rate1": rate_from,
            },
        )

    def volume_rank(
        self,
        market: str = "J",
        screen_code: str = "20171",
        stock_code: str = "0000",
        div_cls: str = "0",
        sort_cls: str = "0",
        target_cls: str = "111111111",
        exclude_cls: str = "0000000000",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
        date: str = "",
    ) -> Optional[Dict]:
        """
        거래량 순위 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT, UN:통합, W:ELW)
            screen_code: 화면코드 (20171:거래량)
            stock_code: 종목코드 (0000:전체)
            div_cls: 분류구분 (0:전체, 1:보통주, 2:우선주)
            sort_cls: 정렬구분 (0:평균거래량, 1:거래증가율, 2:평균거래회전율, 3:거래금액순, 4:평균거래금액회전율)
            target_cls: 대상구분코드 (9자리, 증거금비율)
            exclude_cls: 제외구분코드 (10자리, 투자위험/관리종목 등)
            price_from: 가격하한
            price_to: 가격상한
            volume: 거래량하한
            date: 조회날짜 (YYYYMMDD, 공백:당일)

        Returns:
            거래량 순위 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["VOLUME_RANK"],
            tr_id="FHPST01710000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_INPUT_ISCD": stock_code,
                "FID_DIV_CLS_CODE": div_cls,
                "FID_BLNG_CLS_CODE": sort_cls,
                "FID_TRGT_CLS_CODE": target_cls,
                "FID_TRGT_EXLS_CLS_CODE": exclude_cls,
                "FID_INPUT_PRICE_1": price_from,
                "FID_INPUT_PRICE_2": price_to,
                "FID_VOL_CNT": volume,
                "FID_INPUT_DATE_1": date,
            },
        )

    def market_cap(
        self,
        market: str = "J",
        screen_code: str = "20174",
        stock_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
    ) -> Optional[Dict]:
        """
        시가총액 순위 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20174:시가총액)
            stock_code: 종목코드 (0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200)
            div_cls: 분류구분 (0:전체, 1:보통주, 2:우선주)
            target_cls: 대상구분 (0:전체)
            exclude_cls: 제외구분 (0:전체)
            price_from: 가격하한
            price_to: 가격상한
            volume: 거래량하한

        Returns:
            시가총액 순위 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["MARKET_CAP"],
            tr_id="FHPST01740000",
            params={
                "fid_input_price_2": price_to,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": screen_code,
                "fid_div_cls_code": div_cls,
                "fid_input_iscd": stock_code,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_input_price_1": price_from,
                "fid_vol_cnt": volume,
            },
        )

    def inquire_daily_overtimeprice(
        self, code: str, market: str = "J"
    ) -> Optional[Dict]:
        """
        주식현재가 시간외 일자별주가 조회 (최근 30건)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            시간외 일자별주가 데이터 (output1: 요약, output2: 일자별 리스트)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_OVERTIMEPRICE"],
            tr_id="FHPST02320000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_elw_price(self, code: str, market: str = "W") -> Optional[Dict]:
        """
        ELW 현재가 조회

        Args:
            code: ELW 종목코드
            market: 시장구분 (W:ELW)

        Returns:
            ELW 현재가 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ELW_PRICE"],
            tr_id="FHKEW15010000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_index_category_price(
        self,
        index_code: str,
        screen_code: str = "20214",
        market_cls: str = "K",
        belong_cls: str = "0",
        market: str = "U",
    ) -> Optional[Dict]:
        """
        국내업종 구분별 전체시세 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            screen_code: 화면코드 (20214:고정값)
            market_cls: 시장구분코드 (K:거래소, Q:코스닥, K2:코스피200)
            belong_cls: 소속구분코드 (0:전업종, 1:기타구분, 2:자본금/벤처구분, 3:상업별/일반구분)
            market: 시장구분 (U:업종)

        Returns:
            업종별 전체시세 데이터 (output1: 요약, output2: 업종별 리스트)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_CATEGORY_PRICE"],
            tr_id="FHPUP02140000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": index_code,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_MRKT_CLS_CODE": market_cls,
                "FID_BLNG_CLS_CODE": belong_cls,
            },
        )

    def inquire_index_price(self, index_code: str, market: str = "U") -> Optional[Dict]:
        """
        국내업종 현재지수 조회

        DEPRECATION WARNING:
            이 메서드는 원본 KIS API 엔드포인트(FHPUP02100000)가 404를 반환하여
            내부적으로 inquire_index_timeprice()를 호출합니다.
            향후 버전에서 제거될 수 있으니 inquire_index_timeprice() 사용을 권장합니다.

        TODO: v2.0에서 제거 예정 - inquire_index_timeprice() 또는 get_index_timeprice() 사용

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            market: 시장구분 (U:업종)

        Returns:
            업종 지수 데이터 (분봉 시세)
        """
        import warnings

        warnings.warn(
            "inquire_index_price()는 deprecated되었습니다. "
            "inquire_index_timeprice() 또는 get_index_timeprice() 사용을 권장합니다. "
            "(원본 API 엔드포인트 404 에러)",
            DeprecationWarning,
            stacklevel=2,
        )
        # 404 에러 발생하는 원본 엔드포인트 대신 정상 작동하는 메서드 사용
        return self.inquire_index_timeprice(index_code, market, time_div="600")

    def inquire_index_tickprice(
        self, index_code: str, market: str = "U"
    ) -> Optional[Dict]:
        """
        국내업종 시간별지수(틱) 조회

        Args:
            index_code: 업종코드 (0001:거래소, 1001:코스닥, 2001:코스피200, 3003:KSQ150)
            market: 시장구분 (U:업종)

        Returns:
            시간별지수 틱 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TICKPRICE"],
            tr_id="FHPUP02110100",
            params={
                "FID_INPUT_ISCD": index_code,
                "FID_COND_MRKT_DIV_CODE": market,
            },
        )

    def inquire_index_timeprice(
        self, index_code: str, market: str = "U", time_div: str = "600"
    ) -> Optional[Dict]:
        """
        국내업종 지수 시간별 시세 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            market: 시장구분 (U:업종)
            time_div: 시간간격(초) - 기본값 600 (10분봉)
                - "60": 1분봉
                - "120": 2분봉
                - "300": 5분봉
                - "600": 10분봉
                - "900": 15분봉
                - "1800": 30분봉
                - "3600": 60분봉

        Returns:
            지수 시간별 시세 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TIMEPRICE"],
            tr_id="FHPUP02110200",
            params={
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": index_code,
                "fid_input_hour_1": time_div,
            },
        )

    def inquire_overtime_asking_price(
        self, code: str, market: str = "J"
    ) -> Optional[Dict]:
        """
        국내주식 시간외호가 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            시간외호가 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_OVERTIME_ASKING_PRICE"],
            tr_id="FHPST02300400",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_overtime_price(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        국내주식 시간외현재가 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            시간외현재가 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_OVERTIME_PRICE"],
            tr_id="FHPST02300000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

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
        """
        국내주식 이격도 순위 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20178:이격도)
            div_cls: 분류구분 (0:전체, 1:관리종목, 2:투자주의 등)
            sort_code: 정렬코드 (0:이격도상위순, 1:이격도하위순)
            hour_cls: 시간구분 (5:이격도5, 10:이격도10, 20:이격도20, 60:이격도60, 120:이격도120)
            stock_code: 종목코드 (0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200)
            target_cls: 대상구분 (0:전체)
            exclude_cls: 제외구분 (0:전체)
            price_from: 가격하한
            volume: 거래량하한
            price_to: 가격상한

        Returns:
            이격도 순위 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["DISPARITY"],
            tr_id="FHPST01780000",
            params={
                "fid_input_price_2": price_to,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": screen_code,
                "fid_div_cls_code": div_cls,
                "fid_rank_sort_cls_code": sort_code,
                "fid_hour_cls_code": hour_cls,
                "fid_input_iscd": stock_code,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_input_price_1": price_from,
                "fid_vol_cnt": volume,
            },
        )

    def dividend_rate(
        self,
        cts_area: str = " ",
        gb1: str = "1",
        upjong: str = "0001",
        gb2: str = "0",
        gb3: str = "1",
        f_dt: str = "",
        t_dt: str = "",
        gb4: str = "0",
    ) -> Optional[Dict]:
        """
        국내주식 배당률 상위 조회

        Args:
            cts_area: 연속영역 (공백)
            gb1: 시장구분 (0:전체, 1:코스피, 2:코스피200, 3:코스닥)
            upjong: 업종구분 (0001:종합, 0002:대형주 등)
            gb2: 종목선택 (0:전체, 6:보통주, 7:우선주)
            gb3: 배당구분 (1:주식배당, 2:현금배당)
            f_dt: 기준일From (YYYYMMDD)
            t_dt: 기준일To (YYYYMMDD)
            gb4: 결산/중간배당 (0:전체, 1:결산배당, 2:중간배당)

        Returns:
            배당률 상위 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["DIVIDEND_RATE"],
            tr_id="HHKDB13470100",
            params={
                "CTS_AREA": cts_area,
                "GB1": gb1,
                "UPJONG": upjong,
                "GB2": gb2,
                "GB3": gb3,
                "F_DT": f_dt,
                "T_DT": t_dt,
                "GB4": gb4,
            },
        )

    def market_time(self) -> Optional[Dict]:
        """
        국내주식 시장영업시간 조회

        Returns:
            시장영업시간 데이터 (개장시간, 폐장시간, 휴장일 등)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["MARKET_TIME"],
            tr_id="FHKST01550000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "0000",
            },
        )

    def market_value(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        국내주식 종목별 시가총액 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            종목별 시가총액 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["MARKET_VALUE"],
            tr_id="FHKST70300200",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def profit_asset_index(
        self, index_code: str = "0001", market: str = "U"
    ) -> Optional[Dict]:
        """
        국내주식 자산/수익지수 조회

        Args:
            index_code: 지수코드 (0001:코스피, 1001:코스닥)
            market: 시장구분 (U:업종)

        Returns:
            자산/수익지수 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["PROFIT_ASSET_INDEX"],
            tr_id="FHKUP03500400",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": index_code,
            },
        )

    def intstock_multprice(self, codes: str, market: str = "J") -> Optional[Dict]:
        """
        국내주식 복수종목 현재가 조회

        Args:
            codes: 종목코드 (복수 종목은 ','로 구분, 최대 50종목)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            복수종목 현재가 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INTSTOCK_MULTPRICE"],
            tr_id="FHKST662300C0",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": codes,
            },
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
        """
        외국인/기관 종합 매매동향 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20449:외국인/기관종합)
            stock_code: 종목코드 (0000:전체)
            div_cls: 분류구분 (0:전체, 1:보통주, 2:우선주)
            sort_cls: 정렬구분 (0:순매수상위, 1:순매도상위)
            etc_cls: 기타구분 (0:전체, 1:외국인, 2:기관계, 3:기타)

        Returns:
            외국인/기관 종합 매매동향 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FOREIGN_INSTITUTION_TOTAL"],
            tr_id="FHPTJ04400000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_INPUT_ISCD": stock_code,
                "FID_DIV_CLS_CODE": div_cls,
                "FID_RANK_SORT_CLS_CODE": sort_cls,
                "FID_ETC_CLS_CODE": etc_cls,
            },
        )

    def daily_credit_balance(
        self, code: str, market: str = "J", screen_code: str = "20476", date: str = ""
    ) -> Optional[Dict]:
        """
        신용잔고 일별추이 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20476:신용잔고)
            date: 조회날짜 (YYYYMMDD, 공백:당일)

        Returns:
            신용잔고 일별추이 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["DAILY_CREDIT_BALANCE"],
            tr_id="FHPST04760000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": date,
            },
        )

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
        """
        공매도 상위종목 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20482:공매도)
            stock_code: 종목코드 (0000:전체)
            period: 조회구분 (0:일, 1:월)
            count: 조회일수/월수
            exclude_cls: 제외구분 (0:없음)
            target_cls: 대상구분 (0:전체)
            volume: 거래량하한
            price_from: 가격하한
            price_to: 가격상한

        Returns:
            공매도 상위종목 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["SHORT_SALE"],
            tr_id="FHPST04820000",
            params={
                "FID_APLY_RANG_VOL": volume,
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_INPUT_ISCD": stock_code,
                "FID_PERIOD_DIV_CODE": period,
                "FID_INPUT_CNT_1": count,
                "FID_TRGT_EXLS_CLS_CODE": exclude_cls,
                "FID_TRGT_CLS_CODE": target_cls,
                "FID_APLY_RANG_PRC_1": price_from,
                "FID_APLY_RANG_PRC_2": price_to,
            },
        )

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
        """
        VI(변동성완화장치) 발동 현황 조회

        Args:
            div_cls: 분류구분 (0:전체, 1:정적, 2:동적)
            screen_code: 화면코드 (20139:VI발동현황)
            market: 시장구분 (0:전체, 1:KOSPI, 2:KOSDAQ)
            stock_code: 종목코드 (공백:전체)
            sort_cls: 정렬구분 (0:VI발동시간순)
            date: 조회날짜 (YYYYMMDD, 공백:당일)
            target_cls: 대상구분 (0:전체)
            exclude_cls: 제외구분 (0:없음)

        Returns:
            VI 발동 현황 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_VI_STATUS"],
            tr_id="FHPST01390000",
            params={
                "FID_DIV_CLS_CODE": div_cls,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_MRKT_CLS_CODE": market,
                "FID_INPUT_ISCD": stock_code,
                "FID_RANK_SORT_CLS_CODE": sort_cls,
                "FID_INPUT_DATE_1": date,
                "FID_TRGT_CLS_CODE": target_cls,
                "FID_TRGT_EXLS_CLS_CODE": exclude_cls,
            },
        )

    def get_stock_ccnl(self, code: str, _retries: int = 10) -> Optional[dict]:
        """주식현재가 체결(최근30건) 조회 - inquire_ccnl 래퍼

        최근 30건의 체결 내역과 함께 당일 체결강도(tday_rltv)를 포함한 상세한 체결 정보를 제공합니다.

        Args:
            code: 종목코드 (6자리)
            _retries: 재시도 횟수 (미사용, 호환성 유지용)

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
        return self.inquire_ccnl(code, market="J")

    def get_intraday_price(self, code: str, date: str) -> Optional[Dict]:
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
        import logging

        # 4번 호출할 시간 기준점 설정 (HHMMSS 형식)
        time_points = ["090000", "110000", "130000", "153000"]

        all_minute_data = []
        output1_data = None

        for hour in time_points:
            try:
                result = self.get_daily_minute_price(code, date, hour)

                if result and result.get("rt_cd") == "0":
                    # 첫 번째 호출에서 output1 데이터 저장
                    if output1_data is None:
                        output1_data = result.get("output1", {})

                    # output2의 분봉 데이터 수집
                    minute_data = result.get("output2", [])
                    if minute_data:
                        all_minute_data.extend(minute_data)

            except Exception as e:
                logging.warning(f"시간 {hour} 분봉 조회 중 오류 발생: {e}")
                continue

        # 시간 순서로 정렬 (최신 시간이 앞에 오도록)
        all_minute_data.sort(
            key=lambda x: x.get("stck_cntg_hour", "000000"), reverse=True
        )

        # 중복 제거 (같은 시간의 분봉이 있을 경우)
        seen_hours = set()
        unique_minute_data = []
        for data in all_minute_data:
            hour_key = data.get("stck_cntg_hour", "")
            if hour_key not in seen_hours:
                seen_hours.add(hour_key)
                unique_minute_data.append(data)

        # 최종 결과 반환
        return {
            "output1": output1_data or {},
            "output2": unique_minute_data,
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": f"하루 전체 분봉 데이터 수집 완료 (총 {len(unique_minute_data)}건)",
        }

    def get_index_timeprice(
        self,
        fid_input_iscd: str = "1029",
        fid_input_hour_1: str = "600",
        fid_cond_mrkt_div_code: str = "U",
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 시간별 지수 조회 (기본값: KOSPI200)

        Args:
            fid_input_iscd (str): 종목코드 (기본값 "1029": KOSPI200)
                - "1001": KOSPI
                - "2001": KOSDAQ
                - "1029": KOSPI200
            fid_input_hour_1 (str): 입력 시간(초) - 조회 시간 범위 (기본값 "600": 10분봉)
                - "60": 1분봉
                - "120": 2분봉
                - "180": 3분봉
                - "300": 5분봉
                - "600": 10분봉
                - "900": 15분봉
                - "1800": 30분봉
                - "3600": 60분봉
            fid_cond_mrkt_div_code (str): 시장 분류 코드 (기본값 "U": 업종)

        Returns:
            Dict containing:
                - output: 시간별 지수 데이터 리스트 (각 시간대별 업종 정보)

        Example:
            >>> agent.get_index_timeprice()  # KOSPI200 10분봉 데이터
            >>> agent.get_index_timeprice("1001", "120")  # KOSPI 2분봉 데이터
            >>> agent.get_index_timeprice("2001", "60")  # KOSDAQ 1분봉 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TIMEPRICE"],
            tr_id="FHPUP02110200",
            params={
                "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
                "fid_input_iscd": fid_input_iscd,
                "fid_input_hour_1": fid_input_hour_1,
            },
        )

    def get_index_daily_price(
        self, index_code: str = "0001", end_date: str = None, period: str = "D"
    ) -> Optional[Dict[str, Any]]:
        """
        국내 지수 일자별 시세 조회 (rt_cd 메타데이터가 포함된)

        KOSPI, KOSDAQ 등 주요 지수의 일별/주별/월별 시세를 조회합니다.
        베타 계산, 시장 상관관계 분석 등에 활용할 수 있습니다.

        Args:
            index_code (str): 지수코드 (기본값: "0001")
                - "0001": KOSPI
                - "1001": KOSDAQ
                - "2001": KOSPI200
            end_date (str): 조회 종료일 (YYYYMMDD), None이면 오늘
            period (str): 기간 구분 (기본값: "D")
                - "D": 일별
                - "W": 주별
                - "M": 월별

        Returns:
            Dict: 지수 일별 시세 데이터
                - output1: 지수 기본 정보 (지수명, 현재가 등)
                - output2: 일자별 시세 리스트 (최대 100건)
                    - stck_bsop_date: 영업일자 (YYYYMMDD)
                    - bstp_nmix_prpr: 업종지수 현재가
                    - bstp_nmix_oprc: 업종지수 시가
                    - bstp_nmix_hgpr: 업종지수 고가
                    - bstp_nmix_lwpr: 업종지수 저가
                    - acml_vol: 누적거래량
                    - acml_tr_pbmn: 누적거래대금
                    - prdy_vrss: 전일대비
                    - prdy_vrss_sign: 전일대비부호

        Example:
            >>> # KOSPI 일별 시세 조회
            >>> result = agent.stock.get_index_daily_price("0001")
            >>> for day in result['output2']:
            ...     print(day['stck_bsop_date'], day['bstp_nmix_prpr'])

            >>> # KOSDAQ 최근 100일 시세
            >>> result = agent.stock.get_index_daily_price("1001", "20251210")

            >>> # KOSPI200 월별 시세
            >>> result = agent.stock.get_index_daily_price("2001", period="M")

        Note:
            - TR ID: FHPUP02120000
            - 최대 100건까지 조회 가능
            - 베타 계산 시: β = Cov(Stock, Market) / Var(Market)
        """
        if end_date is None:
            from datetime import datetime

            end_date = datetime.now().strftime("%Y%m%d")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_DAILY_PRICE"],
            tr_id="FHPUP02120000",
            params={
                "FID_PERIOD_DIV_CODE": period,
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": index_code,
                "FID_INPUT_DATE_1": end_date,
            },
        )

    def get_future_option_price(
        self, market_div_code: str = "F", input_iscd: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
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
            # get_kospi200_futures_code는 pykis.stock.api 모듈에 있으므로 import
            from .api import get_kospi200_futures_code

            input_iscd = get_kospi200_futures_code()
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_PRICE"],
            tr_id="FHMIF10000000",
            params={
                "fid_cond_mrkt_div_code": market_div_code,
                "fid_input_iscd": input_iscd,
            },
        )

    def get_future_orderbook(
        self, code: str, market_div_code: str = "F"
    ) -> Optional[Dict[str, Any]]:
        """
        선물옵션 호가창 조회 (미결제약정 정보 포함)

        KOSPI200 선물/옵션의 매도/매수 호가 10단계와 미결제약정 정보를 조회합니다.
        현물/선물 포지션 분석 시 호가 분포와 미결제약정 변화를 분석할 수 있습니다.

        Args:
            code (str): 선물옵션 종목코드
                - 지수선물: 6자리 (예: "101W09" - KOSPI200 2025년 9월물)
                - 주식선물: 6자리 (예: "005930F09")
                - 옵션: 9자리 (예: "201W09370" - 콜옵션 행사가 370)
            market_div_code (str, optional): 시장 분류 코드. Defaults to "F".
                - "F": 지수선물 (KOSPI200 선물)
                - "JF": 주식선물 (개별종목 선물)
                - "O": 옵션 (KOSPI200 옵션)
                - "JO": 주식옵션

        Returns:
            Optional[Dict[str, Any]]: 선물옵션 호가 데이터
                - rt_cd: 응답 코드 ("0" = 성공)
                - msg1: 응답 메시지
                - output1: 호가 요약 정보 (객체)
                    - 현재가, 거래량 등 요약 정보
                    - 미결제약정 관련 필드 (API 응답 구조에 따라 다름)
                - output2: 호가 상세 정보 (객체)
                    - 매도호가 1~10단계 (askp1~askp10)
                    - 매수호가 1~10단계 (bidp1~bidp10)
                    - 각 호가별 잔량 정보
                    - 총 매도/매수 호가 잔량

        Example:
            >>> # KOSPI200 선물 호가창 조회
            >>> orderbook = agent.stock.get_future_orderbook("101W09", "F")
            >>> if orderbook and orderbook.get('rt_cd') == '0':
            ...     output1 = orderbook['output1']
            ...     output2 = orderbook['output2']
            ...     print(f"매도1호가: {output2.get('askp1')}")
            ...     print(f"매수1호가: {output2.get('bidp1')}")

            >>> # 옵션 호가창 조회
            >>> opt_orderbook = agent.stock.get_future_orderbook("201W09370", "O")

        Note:
            - TR ID: FHMIF10010000
            - 실시간 호가 데이터는 WebSocket `subscribe_futures(with_orderbook=True)` 사용
            - 미결제약정(Open Interest) 데이터는 output1 또는 output2에 포함 가능
            - 호가 조회는 시장 개장 시간에만 유효한 데이터 제공
            - 선물 종목코드는 `get_kospi200_futures_code()`로 자동 생성 가능
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_ASKING_PRICE"],
            tr_id="FHMIF10010000",
            params={
                "FID_COND_MRKT_DIV_CODE": market_div_code,
                "FID_INPUT_ISCD": code,
            },
        )

    def get_stock_financial(self, code: str) -> Optional[Dict[str, Any]]:
        """
        종목 재무비율 조회 (분기별 재무지표 30개 항목)

        주식의 분기별 재무비율 정보를 조회합니다. 최근 30개 분기 데이터를 반환합니다.

        Args:
            code: 종목코드 6자리 (예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 재무비율 데이터
                - rt_cd: 응답 코드 ("0" = 성공)
                - msg1: 응답 메시지
                - output: 분기별 재무비율 리스트 (최근 30개 분기)
                    - stac_yymm: 결산년월 (YYYYMM)
                    - grs: 매출총이익률 (%)
                    - bsop_prfi_inrt: 영업이익률 (%)
                    - ntin_inrt: 순이익률 (%)
                    - roe_val: ROE (자기자본이익률, %)
                    - eps: EPS (주당순이익, 원)
                    - sps: SPS (주당매출액, 원)
                    - bps: BPS (주당순자산, 원)
                    - rsrv_rate: 유보율 (%)
                    - lblt_rate: 부채비율 (%)

        Example:
            >>> financial = agent.stock.get_stock_financial("005930")
            >>> if financial and financial.get('rt_cd') == '0':
            ...     latest = financial['output'][0]  # 최신 분기
            ...     print(f"결산년월: {latest['stac_yymm']}")
            ...     print(f"ROE: {latest['roe_val']}%")
            ...     print(f"EPS: {latest['eps']}원")
            ...     print(f"영업이익률: {latest['bsop_prfi_inrt']}%")

        Note:
            - 분기별 데이터를 배열로 반환 (최신 순)
            - 정기 공시 기반 데이터 (분기 결산 발표 후 업데이트)
            - output[0]이 가장 최근 분기 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FINANCIAL_RATIO"],
            tr_id="FHKST66430300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_DIV_CLS_CODE": "1",  # 1=분기별 재무비율
            },
        )

    def get_stock_basic(self, code: str) -> Optional[Dict[str, Any]]:
        """
        종목 기본 정보 조회

        주식의 기본 정보(상장주식수, 시가총액, 액면가 등)를 조회합니다.

        Args:
            code: 종목코드 6자리 (예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 기본 정보 데이터
                - rt_cd: 응답 코드 ("0" = 성공)
                - msg1: 응답 메시지
                - output: 기본 정보
                    - lstg_stqt: 상장 주식수
                    - stck_prpr: 주식 현재가
                    - hts_avls: 시가총액
                    - per: PER
                    - pbr: PBR
                    - stac_month: 결산월
                    - face_value: 액면가
                    - 기타 기본 정보

        Example:
            >>> basic = agent.stock.get_stock_basic("005930")
            >>> if basic and basic.get('rt_cd') == '0':
            ...     print(f"상장주식수: {basic['output']['lstg_stqt']}")
            ...     print(f"시가총액: {basic['output']['hts_avls']}")

        Note:
            - 종목의 메타데이터 성격의 정보 제공
            - 상장주식수는 정기적으로 업데이트
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["SEARCH_STOCK_INFO"],
            tr_id="CTPF1002R",
            params={"PRDT_TYPE_CD": "300", "PDNO": code},
        )

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """
        주식 회원사(증권사) 정보 조회

        특정 종목의 회원사별 매매 동향을 조회합니다.

        Args:
            ticker: 종목코드 6자리 (예: "005930")
            retries: 재시도 횟수 (기본값: 10)

        Returns:
            Optional[Dict]: 회원사 정보 데이터
                - rt_cd: 응답 코드 ("0" = 성공)
                - msg1: 응답 메시지
                - output: 회원사별 매매 정보 리스트
                    - mbcr_name: 회원사명
                    - askp_rsqn: 매도 잔량
                    - bidp_rsqn: 매수 잔량
                    - ntby_qty: 순매수 수량
                    - 기타 회원사 매매 정보

        Example:
            >>> member = agent.stock.get_stock_member("005930")
            >>> if member and member.get('rt_cd') == '0':
            ...     for m in member['output']:
            ...         print(f"{m['mbcr_name']}: 순매수 {m['ntby_qty']}")

        Note:
            - API 응답이 불안정할 수 있어 재시도 로직 포함
            - 실패 시 최대 retries 횟수만큼 재시도
            - 회원사 데이터는 실시간성 정보
        """
        import logging

        for attempt in range(retries):
            try:
                response = self._make_request_dict(
                    endpoint=API_ENDPOINTS["INQUIRE_MEMBER"],
                    tr_id="FHKST01010600",
                    params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
                )

                if response and response.get("rt_cd") == "0":
                    return response
                elif response and response.get("rt_cd") != "0":
                    logging.warning(
                        f"주식 회원사 조회 실패 (시도 {attempt+1}/{retries}): {response.get('msg1', '알 수 없는 오류')}"
                    )
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

    def get_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """
        주식 회원사 정보 조회 (get_stock_member 별칭)

        get_stock_member와 동일한 기능을 제공합니다.
        하위 호환성을 위해 유지됩니다.

        Args:
            ticker: 종목코드 6자리 (예: "005930")
            retries: 재시도 횟수 (기본값: 10)

        Returns:
            Optional[Dict]: 회원사 정보 데이터

        See Also:
            get_stock_member: 동일 기능의 메인 메서드
        """
        return self.get_stock_member(ticker, retries)
