"""
Stock Price API - 주식 시세 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 StockAPI에서 시세 관련 기능만 분리
- 현재가 조회
- 일별/분봉 시세
- 호가 정보

지수/선물 관련 API는 StockIndexAPI(index_api.py)에서 상속
"""

from typing import Any, Dict, Optional

from ..core.client import API_ENDPOINTS
from .index_api import StockIndexAPI


class StockPriceAPI(StockIndexAPI):
    """주식 시세 조회 전용 API 클래스 (StockIndexAPI 상속으로 지수/선물 API 포함)"""

    def get_stock_price(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        주식 현재가 조회

        Args:
            code: 종목코드 (6자리, 예: '005930')
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)

        Returns:
            StockPriceResponse (82개 필드): stck_prpr(현재가), prdy_vrss(전일대비),
            per, pbr, acml_vol(거래량) 등. 상세: StockPriceOutput TypedDict 참조

        Example:
            >>> price = agent.stock.get_stock_price("005930")
            >>> print(price['output']['stck_prpr'])  # 현재가
            >>> price_nxt = agent.stock.get_stock_price("005930", market="NX")  # NXT
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def inquire_daily_price(
        self,
        code: str,
        period: str = "D",
        org_adj_prc: str = "1",
        market: str = "J",
    ) -> Optional[Dict]:
        """
        주식현재가 일자별 조회 (최근 30건)

        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월)
            org_adj_prc: 수정주가구분 (0: 수정주가 미반영, 1: 수정주가 반영)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)

        Returns:
            DailyPriceResponse: output[] 리스트 (최대 30개) - 일자별 OHLCV

        Example:
            >>> daily = agent.stock.inquire_daily_price("005930", period="D")
            >>> daily_nxt = agent.stock.inquire_daily_price("005930", market="NX")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_PRICE"],
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
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
        market: str = "J",
    ) -> Optional[Dict]:
        """
        기간별 시세 조회

        Args:
            code: 종목코드 (6자리)
            start_date: 시작일자 (YYYYMMDD)
            end_date: 종료일자 (YYYYMMDD)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 미반영, 1: 반영)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)

        Returns:
            output1[]=OHLCV 리스트(최대100건)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_ITEMCHARTPRICE"],
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": org_adj_prc,
            },
        )

    def get_orderbook(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        주식 호가 정보 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)

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
            >>> orderbook_nxt = agent.stock.get_orderbook("005930", market="NX")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_orderbook_raw(self, code: str, market: str = "J") -> Optional[Dict]:
        """
        호가 정보 원시 데이터 조회 (rt_cd 메타데이터 포함)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """[DEPRECATED] 당일 분봉은 get_intraday_price(code), 특정일은 get_daily_minute_price(code, date) 사용"""
        import warnings

        warnings.warn(
            "get_minute_price()는 deprecated 되었습니다. "
            "당일 분봉은 get_intraday_price(code), "
            "특정일 분봉은 get_daily_minute_price(code, date)를 사용하세요.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_intraday_price(code)

    def _fetch_minute_price_page(
        self, code: str, date: str, hour: str = "153000", market: str = "J"
    ) -> Optional[Dict]:
        """[Private] 분봉 단일 페이지 조회 (최대 120건). 외부에서는 get_daily_minute_price() 사용."""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_DAILYCHARTPRICE"],
            tr_id="FHKST03010230",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": "Y",
                "FID_INPUT_DATE_1": date,
                "FID_FAKE_TICK_INCU_YN": "",
            },
        )

    def get_daily_minute_price(
        self, code: str, date: str, market: str = "J"
    ) -> Optional[Dict]:
        """
        특정일 전체 분봉시세조회

        Args:
            code: 종목코드 (6자리)
            date: 조회일자 (YYYYMMDD)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)

        Returns:
            output2에 ~390건 분봉 (내부 4회 API 호출, 중복제거)
        """
        import logging

        # 4번 호출할 시간 기준점 (HHMMSS)
        time_points = ["090000", "110000", "130000", "153000"]

        all_minute_data = []
        output1_data = None

        for hour in time_points:
            try:
                result = self._fetch_minute_price_page(code, date, hour, market)

                if result and result.get("rt_cd") == "0":
                    if output1_data is None:
                        output1_data = result.get("output1", {})

                    minute_data = result.get("output2", [])
                    if minute_data:
                        all_minute_data.extend(minute_data)

            except Exception as e:
                logging.warning(f"분봉 조회 중 오류 ({date} {hour}): {e}")
                continue

        # 시간 역순 정렬 (최신이 앞)
        all_minute_data.sort(
            key=lambda x: x.get("stck_cntg_hour", "000000"), reverse=True
        )

        # 중복 제거
        seen_hours = set()
        unique_data = []
        for item in all_minute_data:
            hour_key = item.get("stck_cntg_hour", "")
            if hour_key not in seen_hours:
                seen_hours.add(hour_key)
                unique_data.append(item)

        return {
            "output1": output1_data or {},
            "output2": unique_data,
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": f"분봉 데이터 수집 완료 ({date}, 총 {len(unique_data)}건)",
        }

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

    # NOTE: inquire_index_* 메서드들은 StockIndexAPI(index_api.py)로 이동됨

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

    def market_time(self, market: str = "J") -> Optional[Dict]:
        """
        국내주식 시장영업시간 조회

        Args:
            market: 시장구분 (J: KRX, NX: NXT 대체거래소)

        Returns:
            시장영업시간 데이터 (개장시간, 폐장시간, 휴장일 등)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["MARKET_TIME"],
            tr_id="FHKST01550000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
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

    def get_intraday_price(self, code: str) -> Optional[Dict]:
        """당일 전체 분봉시세조회. get_daily_minute_price(code, today) wrapper."""
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        return self.get_daily_minute_price(code, today)

    # NOTE: get_index_*, get_future_* 메서드들은 StockIndexAPI(index_api.py)로 이동됨

    def get_stock_financial(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        종목 재무비율 조회 (분기별 재무지표 30개 항목)

        주식의 분기별 재무비율 정보를 조회합니다. 최근 30개 분기 데이터를 반환합니다.

        Args:
            code: 종목코드 6자리 (예: "005930")
            market: 시장구분 (J: KRX, NX: NXT 대체거래소)

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
            >>> financial_nxt = agent.stock.get_stock_financial("005930", market="NX")

        Note:
            - 분기별 데이터를 배열로 반환 (최신 순)
            - 정기 공시 기반 데이터 (분기 결산 발표 후 업데이트)
            - output[0]이 가장 최근 분기 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FINANCIAL_RATIO"],
            tr_id="FHKST66430300",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
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

    def get_stock_member(
        self, ticker: str, retries: int = 10, market: str = "J"
    ) -> Optional[Dict]:
        """
        주식 회원사(증권사) 정보 조회

        특정 종목의 회원사별 매매 동향을 조회합니다.

        Args:
            ticker: 종목코드 6자리 (예: "005930")
            retries: 재시도 횟수 (기본값: 10)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소)

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
            >>> member_nxt = agent.stock.get_stock_member("005930", market="NX")

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
                    params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": ticker},
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
                    logging.error(
                        f"주식 회원사 조회 응답 없음 (시도 {attempt+1}/{retries})"
                    )
                    if attempt < retries - 1:
                        continue
                    else:
                        return None

            except Exception as e:
                logging.error(
                    f"주식 회원사 조회 예외 발생 (시도 {attempt+1}/{retries}): {e}"
                )
                if attempt < retries - 1:
                    continue
                else:
                    return None

        return None

    def get_member(
        self, ticker: str, retries: int = 10, market: str = "J"
    ) -> Optional[Dict]:
        """
        주식 회원사 정보 조회 (get_stock_member 별칭)

        get_stock_member와 동일한 기능을 제공합니다.
        하위 호환성을 위해 유지됩니다.

        Args:
            ticker: 종목코드 6자리 (예: "005930")
            retries: 재시도 횟수 (기본값: 10)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소)

        Returns:
            Optional[Dict]: 회원사 정보 데이터

        See Also:
            get_stock_member: 동일 기능의 메인 메서드
        """
        return self.get_stock_member(ticker, retries, market)

    def get_daily_price_all(
        self,
        code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        org_adj_prc: str = "1",
    ) -> Optional[Dict[str, Any]]:
        """
        기간별 시세 전체 조회 (100건 제한 우회, 페이지네이션 자동 처리)

        한국투자증권 API의 100건 제한을 우회하여 지정한 전체 기간의 일봉 데이터를 조회합니다.
        내부적으로 날짜 범위를 자동 분할하여 여러 번 호출하고 결과를 병합합니다.

        Args:
            code: 종목코드 (6자리, 예: "005930")
            start_date: 조회 시작일 (YYYYMMDD 형식, 예: "20200102")
            end_date: 조회 종료일 (YYYYMMDD 형식, 예: "20201230")
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미반영, 1: 수정주가 반영)

        Returns:
            Optional[Dict[str, Any]]: 전체 시세 데이터
                - output1: 요약 정보 (첫 번째 조회의 output1)
                - output2: 일봉 데이터 리스트 (모든 조회 결과 병합, 시간 역순)
                - rt_cd: 응답 코드
                - msg1: 응답 메시지
                - _pagination_info: 페이지네이션 정보 (디버깅용)
                    - total_calls: 총 API 호출 횟수
                    - total_records: 총 레코드 수
                    - date_range: 실제 조회된 날짜 범위

        Example:
            >>> # 2020년 전체 삼성전자 일봉 데이터 조회
            >>> result = agent.get_daily_price_all(
            ...     code="005930",
            ...     start_date="20200102",
            ...     end_date="20201230"
            ... )
            >>> print(f"총 {len(result['output2'])}건 조회됨")
            >>> print(f"API 호출 횟수: {result['_pagination_info']['total_calls']}")

        Note:
            - 기본 API는 최대 100건까지만 반환
            - 이 메서드는 자동으로 날짜 범위를 분할하여 전체 데이터 수집
            - 대량 데이터 조회 시 Rate Limit 고려 필요 (18 RPS / 900 RPM)
            - 마지막 데이터의 날짜를 기준으로 자동 분할
        """
        import logging
        from datetime import datetime, timedelta

        all_data = []
        output1 = None
        current_end_date = end_date
        call_count = 0
        max_calls = 50  # 안전 장치: 최대 50회 호출 (약 5000일 = 13.7년)

        logger = logging.getLogger(__name__)
        logger.info(
            f"일봉 전체 조회 시작: {code}, {start_date} ~ {end_date}, period={period}"
        )

        while call_count < max_calls:
            call_count += 1

            # API 호출
            result = self.inquire_daily_itemchartprice(
                code=code,
                start_date=start_date,
                end_date=current_end_date,
                period=period,
                org_adj_prc=org_adj_prc,
            )

            if not result or result.get("rt_cd") != "0":
                logger.warning(
                    f"일봉 조회 실패 (호출 {call_count}): {result.get('msg1') if result else 'No response'}"
                )
                break

            # 첫 번째 조회에서 output1 저장
            if output1 is None:
                output1 = result.get("output1", {})

            # output2 데이터 수집
            output2 = result.get("output2", [])
            if not output2:
                logger.info(f"더 이상 데이터 없음 (호출 {call_count})")
                break

            # 데이터 추가 (중복 제거는 나중에 처리)
            all_data.extend(output2)
            logger.info(
                f"호출 {call_count}: {len(output2)}건 수집 (누적: {len(all_data)}건)"
            )

            # 100건 미만이면 마지막 페이지
            if len(output2) < 100:
                logger.info(f"마지막 페이지 도달 (호출 {call_count})")
                break

            # 마지막 데이터의 날짜 확인
            last_date_str = output2[-1].get("stck_bsop_date", "")
            if not last_date_str:
                logger.warning("마지막 데이터에 날짜 정보 없음. 중단.")
                break

            # 마지막 날짜의 하루 전으로 설정 (중복 방지)
            try:
                last_date = datetime.strptime(last_date_str, "%Y%m%d")
                next_end_date = (last_date - timedelta(days=1)).strftime("%Y%m%d")

                # start_date보다 이전이면 중단
                if next_end_date < start_date:
                    logger.info(
                        f"시작일 이전 도달 ({next_end_date} < {start_date}). 중단."
                    )
                    break

                current_end_date = next_end_date
                logger.debug(f"다음 조회 종료일: {current_end_date}")

            except ValueError as e:
                logger.error(f"날짜 파싱 오류: {last_date_str} - {e}")
                break

        # 데이터 정렬 및 중복 제거
        if all_data:
            # 날짜 기준 역순 정렬 (최신이 앞)
            all_data.sort(key=lambda x: x.get("stck_bsop_date", ""), reverse=True)

            # 중복 제거 (날짜 기준)
            seen_dates = set()
            unique_data = []
            for item in all_data:
                date = item.get("stck_bsop_date", "")
                if date and date not in seen_dates:
                    seen_dates.add(date)
                    unique_data.append(item)

            all_data = unique_data
            logger.info(f"중복 제거 완료: {len(all_data)}건 (호출: {call_count}회)")

        # 결과 반환
        return {
            "output1": output1 or {},
            "output2": all_data,
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": f"정상처리 (페이지네이션: {call_count}회 호출, {len(all_data)}건 수집)",
            "_pagination_info": {
                "total_calls": call_count,
                "total_records": len(all_data),
                "date_range": {
                    "requested_start": start_date,
                    "requested_end": end_date,
                    "actual_start": (
                        all_data[-1].get("stck_bsop_date", "") if all_data else ""
                    ),
                    "actual_end": (
                        all_data[0].get("stck_bsop_date", "") if all_data else ""
                    ),
                },
            },
        }
