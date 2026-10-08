"""WSAgent 구독 편의 메서드 (Convenience Methods).

`ws_agent.py`가 1500줄 LOC 게이트를 넘겨 분리한 믹스인. 순수 이동이며 로직 변경은
없다. 여기 있는 메서드는 전부 `WSAgent.subscribe()` / `unsubscribe()` 위에 얹힌
얇은 래퍼로, 종목코드·시장 구분에 맞는 `SubscriptionType`을 골라주는 역할만 한다.

호스트 클래스(`WSAgent`)가 제공해야 하는 것:
- `subscribe(sub_type, key, handler=None, **metadata) -> str`
- `unsubscribe(sub_id) -> None`
- `subscriptions: Dict[str, Subscription]`

선례: `RateLimiterControlMixin`을 `Agent`에서 분리한 것과 같은 패턴.
"""

from typing import Callable, List, Optional, Union

from .ws_types import SubscriptionType

__all__ = ["WSSubscriptionMixin"]


class WSSubscriptionMixin:
    """구독 편의 메서드 모음. `WSAgent`가 상속한다."""

    # ========================================================================
    # 편의 메서드 (Convenience Methods)
    # ========================================================================

    def subscribe_stock(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        with_program: bool = False,
        with_member: bool = False,
        **metadata,
    ) -> List[str]:
        """
        종목 실시간 구독 (편의 메서드)

        Args:
            code: 종목코드 (6자리)
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            with_expected: 예상체결 데이터도 함께 구독
            with_program: 프로그램매매 데이터도 함께 구독
            with_member: 회원사 매매동향도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_stock("005930", with_orderbook=True)
            ['H0STCNT0_005930', 'H0STASP0_005930']
        """
        sub_ids = []

        # 체결가 구독 (기본)
        sub_ids.append(
            self.subscribe(SubscriptionType.STOCK_TRADE, code, handler, **metadata)
        )

        # 호가 구독
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_ASK_BID, code, handler, **metadata
                )
            )

        # 예상체결 구독
        if with_expected:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_EXPECTED, code, handler, **metadata
                )
            )

        # 프로그램매매 구독
        if with_program:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.PROGRAM_TRADE, code, handler, **metadata
                )
            )

        # 회원사 매매동향 구독
        if with_member:
            sub_ids.append(
                self.subscribe(SubscriptionType.MEMBER_TRADE, code, handler, **metadata)
            )

        return sub_ids

    def subscribe_stocks(
        self,
        codes: List[str],
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        with_program: bool = False,
        with_member: bool = False,
        **metadata,
    ) -> List[str]:
        """
        여러 종목 실시간 구독 (편의 메서드)

        Args:
            codes: 종목코드 리스트
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            with_expected: 예상체결 데이터도 함께 구독
            with_program: 프로그램매매 데이터도 함께 구독
            with_member: 회원사 매매동향도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        for code in codes:
            sub_ids.extend(
                self.subscribe_stock(
                    code,
                    handler,
                    with_orderbook=with_orderbook,
                    with_expected=with_expected,
                    with_program=with_program,
                    with_member=with_member,
                    **metadata,
                )
            )
        return sub_ids

    # ========================================================================
    # NXT 시장 전용 편의 메서드
    # ========================================================================

    def subscribe_stock_nxt(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        with_program: bool = False,
        with_member: bool = False,
        **metadata,
    ) -> List[str]:
        """
        NXT 시장 종목 실시간 구독 (편의 메서드)

        NXT(Next Trading System)는 한국거래소의 대체거래시스템(ATS)으로,
        기존 KRX 시장과 별도의 실시간 데이터 스트림을 제공합니다.

        Args:
            code: 종목코드 (6자리)
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            with_expected: 예상체결 데이터도 함께 구독
            with_program: 프로그램매매 데이터도 함께 구독
            with_member: 회원사 매매동향도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_stock_nxt("005930", with_orderbook=True)
            ['H0NXCNT0_005930', 'H0NXASP0_005930']
        """
        sub_ids = []

        # NXT 체결가 구독 (기본)
        sub_ids.append(
            self.subscribe(SubscriptionType.STOCK_TRADE_NXT, code, handler, **metadata)
        )

        # NXT 호가 구독
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_ASK_BID_NXT, code, handler, **metadata
                )
            )

        # NXT 예상체결 구독
        if with_expected:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_EXPECTED_NXT, code, handler, **metadata
                )
            )

        # NXT 프로그램매매 구독
        if with_program:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.PROGRAM_TRADE_NXT, code, handler, **metadata
                )
            )

        # NXT 회원사 매매동향 구독
        if with_member:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.MEMBER_TRADE_NXT, code, handler, **metadata
                )
            )

        return sub_ids

    def subscribe_stocks_nxt(
        self,
        codes: List[str],
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        with_program: bool = False,
        with_member: bool = False,
        **metadata,
    ) -> List[str]:
        """
        NXT 시장 여러 종목 실시간 구독 (편의 메서드)

        Args:
            codes: 종목코드 리스트
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            with_expected: 예상체결 데이터도 함께 구독
            with_program: 프로그램매매 데이터도 함께 구독
            with_member: 회원사 매매동향도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        for code in codes:
            sub_ids.extend(
                self.subscribe_stock_nxt(
                    code,
                    handler,
                    with_orderbook=with_orderbook,
                    with_expected=with_expected,
                    with_program=with_program,
                    with_member=with_member,
                    **metadata,
                )
            )
        return sub_ids

    def subscribe_market_operation_nxt(
        self,
        code: Union[str, Callable, None] = None,
        handler: Optional[Callable] = None,
        **metadata,
    ) -> str:
        """
        NXT 시장 장운영정보 구독 (편의 메서드)

        장운영정보는 거래정지·VI 발동/해제·장운영 구분 변화를 종목 단위로 알려줍니다.
        공식 문서상 구독 키는 종목코드입니다 (이전 버전은 "NXT"로 구독했다).

        Args:
            code: 종목코드 (예: "005930")
            handler: 데이터 수신 핸들러
            **metadata: 추가 메타데이터

        Returns:
            str: 구독 ID

        Raises:
            ValueError: 종목코드를 주지 않은 경우

        Example:
            >>> agent.subscribe_market_operation_nxt("005930")
            'H0NXMKO0_005930'
        """
        if callable(code) and handler is None:
            # 이전 시그니처 subscribe_market_operation_nxt(handler) 호환
            code, handler = None, code
        if not code:
            raise ValueError("장운영정보 구독에는 종목코드가 필요합니다 (예: '005930')")
        return self.subscribe(
            SubscriptionType.MARKET_OPERATION_NXT, code, handler, **metadata
        )

    def subscribe_program_trading_nxt(
        self,
        codes: List[str],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """
        NXT 시장 프로그램매매 실시간 구독 (편의 메서드)

        Args:
            codes: 종목코드 리스트
            handler: 데이터 수신 핸들러
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        for code in codes:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.PROGRAM_TRADE_NXT, code, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_member_trading_nxt(
        self,
        codes: List[str],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """
        NXT 시장 회원사 실시간 매매동향 구독 (편의 메서드)

        Args:
            codes: 종목코드 리스트
            handler: 데이터 수신 핸들러
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        for code in codes:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.MEMBER_TRADE_NXT, code, handler, **metadata
                )
            )
        return sub_ids

    # ========================================================================
    # 기존 편의 메서드 (KRX 시장)
    # ========================================================================

    def subscribe_index(
        self,
        codes: Optional[List[str]] = None,
        handler: Optional[Callable] = None,
        with_expected: bool = False,
        **metadata,
    ) -> List[str]:
        """
        지수 실시간 구독 (편의 메서드)

        Args:
            codes: 지수코드 리스트. None이면 KOSPI, KOSDAQ, KOSPI200 구독
                - "0001": KOSPI
                - "1001": KOSDAQ
                - "2001": KOSPI200
            handler: 데이터 수신 핸들러
            with_expected: 예상체결 데이터도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_index(with_expected=True)
            ['H0IF1000_0001', 'H0IF1000_1001', 'H0IF1000_2001', ...]
        """
        if codes is None:
            codes = ["0001", "1001", "2001"]  # KOSPI, KOSDAQ, KOSPI200

        sub_ids = []
        for code in codes:
            sub_ids.append(
                self.subscribe(SubscriptionType.INDEX, code, handler, **metadata)
            )
            if with_expected:
                sub_ids.append(
                    self.subscribe(
                        SubscriptionType.INDEX_EXPECTED, code, handler, **metadata
                    )
                )

        return sub_ids

    def subscribe_program_trading(
        self,
        codes: List[str],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """
        프로그램매매 실시간 구독 (편의 메서드)

        Args:
            codes: 종목코드 리스트
            handler: 데이터 수신 핸들러
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        for code in codes:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.PROGRAM_TRADE, code, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_member_trading(
        self,
        codes: List[str],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """
        회원사 실시간 매매동향 구독 (편의 메서드)

        증권사별 매매동향을 실시간으로 수신합니다.

        Args:
            codes: 종목코드 리스트
            handler: 데이터 수신 핸들러
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        for code in codes:
            sub_ids.append(
                self.subscribe(SubscriptionType.MEMBER_TRADE, code, handler, **metadata)
            )
        return sub_ids

    def subscribe_futures(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        **metadata,
    ) -> List[str]:
        """
        선물 실시간 구독 (편의 메서드)

        Args:
            code: 선물 종목코드
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        sub_ids.append(
            self.subscribe(
                SubscriptionType.INDEX_FUTURES_TRADE, code, handler, **metadata
            )
        )
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.INDEX_FUTURES_ASK_BID, code, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_options(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        **metadata,
    ) -> List[str]:
        """
        지수옵션 실시간 구독 (편의 메서드)

        Args:
            code: 옵션 종목코드
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        sub_ids = []
        sub_ids.append(
            self.subscribe(
                SubscriptionType.INDEX_OPTION_TRADE, code, handler, **metadata
            )
        )
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.INDEX_OPTION_ASK_BID, code, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_stock_futures(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        **metadata,
    ) -> List[str]:
        """
        주식선물 실시간 구독 (편의 메서드)

        Args:
            code: 주식선물 종목코드
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            with_expected: 예상체결 데이터도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_stock_futures("111V06", with_orderbook=True)
            ['H0ZFCNT0_111V06', 'H0ZFASP0_111V06']
        """
        sub_ids = []
        sub_ids.append(
            self.subscribe(
                SubscriptionType.STOCK_FUTURES_TRADE, code, handler, **metadata
            )
        )
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_FUTURES_ASK_BID, code, handler, **metadata
                )
            )
        if with_expected:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_FUTURES_EXPECTED, code, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_stock_options(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        **metadata,
    ) -> List[str]:
        """
        주식옵션 실시간 구독 (편의 메서드)

        Args:
            code: 주식옵션 종목코드
            handler: 데이터 수신 핸들러
            with_orderbook: 호가 데이터도 함께 구독
            with_expected: 예상체결 데이터도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_stock_options("211V05059", with_orderbook=True)
            ['H0ZOCNT0_211V05059', 'H0ZOASP0_211V05059']
        """
        sub_ids = []
        sub_ids.append(
            self.subscribe(
                SubscriptionType.STOCK_OPTION_TRADE, code, handler, **metadata
            )
        )
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_OPTION_ASK_BID, code, handler, **metadata
                )
            )
        if with_expected:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_OPTION_EXPECTED, code, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_overtime(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_expected: bool = False,
        **metadata,
    ) -> List[str]:
        """
        시간외 단일가 실시간 구독 (편의 메서드)

        Args:
            code: 종목코드
            handler: 데이터 수신 핸들러
            with_expected: 시간외 예상체결도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트 [호가, 체결, (예상체결)]

        Example:
            >>> agent.subscribe_overtime("005930", with_expected=True)
            ['H0STOAA0_005930', 'H0STOUP0_005930', 'H0STOAC0_005930']
        """
        sub_ids = [
            self.subscribe(
                SubscriptionType.OVERTIME_ASK_BID, code, handler, **metadata
            ),
            self.subscribe(SubscriptionType.OVERTIME_TRADE, code, handler, **metadata),
        ]
        if with_expected:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.OVERTIME_EXPECTED, code, handler, **metadata
                )
            )
        return sub_ids

    @staticmethod
    def _overseas_key(code: str, exchange: Optional[str], paid: bool) -> str:
        """해외 실시간 구독 키: (D 무료 | R 유료·미국주간) + 시장구분 3자리 + 종목코드."""
        if not exchange:
            return code
        return f"{'R' if paid else 'D'}{exchange.upper()}{code.upper()}"

    def subscribe_overseas_stock(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        exchange: Optional[str] = None,
        paid: bool = False,
        **metadata,
    ) -> List[str]:
        """
        해외주식 실시간 구독 (편의 메서드)

        KIS 구독 키는 ``D``(무료) 또는 ``R``(유료/미국 주간거래) + 시장구분 3자리 +
        종목코드입니다 (예: ``DNASAAPL``). 수신 프레임의 첫 컬럼(RSYM)도 같은 값이라
        이 키로 구독해야 개별 핸들러가 호출됩니다. ``exchange``를 주면 키를 만들어
        주고, 생략하면 ``code``를 그대로 키로 씁니다.

        Args:
            code: 종목코드 ("AAPL") 또는 완성된 키 ("DNASAAPL")
            handler: 데이터 수신 핸들러
            with_orderbook: 실시간 호가(HDFSASP0)도 함께 구독
            exchange: 시장구분 3자리 (NAS, NYS, AMS, TSE, HKS, SHS, SZS, HSX, HNX,
                미국 주간: BAQ, BAY, BAA)
            paid: True면 ``R`` 접두어 (유료시세 신청 계정, 미국 주간거래)
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_overseas_stock("AAPL", exchange="NAS", with_orderbook=True)
            ['HDFSCNT0_DNASAAPL', 'HDFSASP0_DNASAAPL']
        """
        key = self._overseas_key(code, exchange, paid)
        sub_ids = [
            self.subscribe(SubscriptionType.OVERSEAS_STOCK, key, handler, **metadata)
        ]
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.OVERSEAS_STOCK_ASK_BID, key, handler, **metadata
                )
            )
        return sub_ids

    def subscribe_overseas_asia_orderbook(
        self,
        code: str,
        exchange: Optional[str] = None,
        handler: Optional[Callable] = None,
        **metadata,
    ) -> str:
        """
        해외주식 지연호가(아시아, HDFSASP1) 구독 — 무료 1호가

        Args:
            code: 종목코드 ("00003") 또는 완성된 키 ("DHKS00003")
            exchange: 시장구분 (TSE, HKS, SHS, SZS, HSX, HNX)
            handler: 데이터 수신 핸들러

        Example:
            >>> agent.subscribe_overseas_asia_orderbook("00003", exchange="HKS")
            'HDFSASP1_DHKS00003'
        """
        key = self._overseas_key(code, exchange, paid=False)
        return self.subscribe(
            SubscriptionType.OVERSEAS_STOCK_ASK_BID_ASIA, key, handler, **metadata
        )

    def subscribe_overseas_futures(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        **metadata,
    ) -> List[str]:
        """
        해외선물옵션 실시간 구독 (편의 메서드)

        Args:
            code: 종목코드
            handler: 데이터 수신 핸들러
            with_orderbook: 실시간 호가도 함께 구독
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_overseas_futures("ESM25", with_orderbook=True)
            ['HDFFF020_ESM25', 'HDFFF010_ESM25']
        """
        sub_ids = [
            self.subscribe(SubscriptionType.OVERSEAS_FUTURES, code, handler, **metadata)
        ]
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.OVERSEAS_FUTURES_ASK_BID, code, handler, **metadata
                )
            )
        return sub_ids

    # ========================================================================
    # 공식 실시간 피드 보강 (통합/KRX 단독, 지수 프로그램매매, ELW, ETF, 채권)
    # ========================================================================

    def _subscribe_each(
        self,
        sub_type: SubscriptionType,
        codes: Union[str, List[str]],
        handler: Optional[Callable],
        metadata: dict,
    ) -> List[str]:
        if isinstance(codes, str):
            codes = [codes]
        return [self.subscribe(sub_type, code, handler, **metadata) for code in codes]

    def subscribe_stock_total(
        self,
        codes: Union[str, List[str]],
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        **metadata,
    ) -> List[str]:
        """국내주식 통합(KRX+NXT) 실시간체결가 H0UNCNT0 (+ 통합호가 H0UNASP0). 실전 전용.

        Example:
            >>> agent.subscribe_stock_total("005930", with_orderbook=True)
            ['H0UNCNT0_005930', 'H0UNASP0_005930']
        """
        if isinstance(codes, str):
            codes = [codes]
        sub_ids: List[str] = []
        for code in codes:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.STOCK_TRADE_TOTAL, code, handler, **metadata
                )
            )
            if with_orderbook:
                sub_ids.append(
                    self.subscribe(
                        SubscriptionType.STOCK_ASK_BID_TOTAL, code, handler, **metadata
                    )
                )
        return sub_ids

    def subscribe_expected(
        self,
        codes: Union[str, List[str]],
        market: str = "TOTAL",
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """국내주식 실시간예상체결. market: "KRX"(H0STANC0) / "NXT"(H0NXANC0) / "TOTAL"(H0UNANC0)."""
        sub_type = {
            "KRX": SubscriptionType.STOCK_EXPECTED_KRX,
            "NXT": SubscriptionType.STOCK_EXPECTED_NXT,
            "TOTAL": SubscriptionType.STOCK_EXPECTED,
        }.get(market.upper())
        if sub_type is None:
            raise ValueError(f"market은 KRX/NXT/TOTAL 중 하나여야 합니다: {market!r}")
        return self._subscribe_each(sub_type, codes, handler, metadata)

    def subscribe_market_operation(
        self,
        codes: Union[str, List[str]],
        market: str = "KRX",
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """국내주식 장운영정보 (VI 발동/해제, 거래정지 등). market: "KRX"(H0STMKO0) / "TOTAL"(H0UNMKO0).

        통합(H0UNMKO0) 프레임에는 종목코드가 없어, 같은 TR 구독이 하나일 때만 개별
        핸들러가 호출된다. 여러 종목은 타입별 핸들러(register_handler)로 받는다.
        """
        sub_type = {
            "KRX": SubscriptionType.MARKET_OPERATION,
            "TOTAL": SubscriptionType.MARKET_OPERATION_TOTAL,
        }.get(market.upper())
        if sub_type is None:
            raise ValueError(f"market은 KRX/TOTAL 중 하나여야 합니다: {market!r}")
        return self._subscribe_each(sub_type, codes, handler, metadata)

    def subscribe_program_trading_total(
        self,
        codes: Union[str, List[str]],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """국내주식 실시간프로그램매매 (통합, H0UNPGM0)."""
        return self._subscribe_each(
            SubscriptionType.PROGRAM_TRADE_TOTAL, codes, handler, metadata
        )

    def subscribe_member_trading_total(
        self,
        codes: Union[str, List[str]],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """국내주식 실시간회원사 (통합, H0UNMBC0)."""
        return self._subscribe_each(
            SubscriptionType.MEMBER_TRADE_TOTAL, codes, handler, metadata
        )

    def subscribe_index_program_trading(
        self,
        codes: Union[str, List[str]] = "0001",
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """국내지수 실시간프로그램매매 (H0UPPGM0). 키는 업종구분코드 (0001 코스피, 1001 코스닥)."""
        return self._subscribe_each(
            SubscriptionType.INDEX_PROGRAM_TRADE, codes, handler, metadata
        )

    def subscribe_elw(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        with_expected: bool = False,
        **metadata,
    ) -> List[str]:
        """ELW 실시간체결가 H0EWCNT0 (+ 호가 H0EWASP0, 예상체결 H0EWANC0). 실전 전용.

        Example:
            >>> agent.subscribe_elw("57LA24", with_orderbook=True)
            ['H0EWCNT0_57LA24', 'H0EWASP0_57LA24']
        """
        sub_ids = [
            self.subscribe(SubscriptionType.ELW_TRADE, code, handler, **metadata)
        ]
        if with_orderbook:
            sub_ids.append(
                self.subscribe(SubscriptionType.ELW_ASK_BID, code, handler, **metadata)
            )
        if with_expected:
            sub_ids.append(
                self.subscribe(SubscriptionType.ELW_EXPECTED, code, handler, **metadata)
            )
        return sub_ids

    def subscribe_etf_nav(
        self,
        codes: Union[str, List[str]],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """국내ETF NAV추이 (H0STNAV0). 실전 전용."""
        return self._subscribe_each(SubscriptionType.ETF_NAV, codes, handler, metadata)

    def subscribe_bond(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        **metadata,
    ) -> List[str]:
        """일반채권 실시간체결가 H0BJCNT0 (+ 호가 H0BJASP0). 키는 채권 표준코드 (예: KR103502GA34)."""
        sub_ids = [
            self.subscribe(SubscriptionType.BOND_TRADE, code, handler, **metadata)
        ]
        if with_orderbook:
            sub_ids.append(
                self.subscribe(SubscriptionType.BOND_ASK_BID, code, handler, **metadata)
            )
        return sub_ids

    def subscribe_bond_index(
        self,
        codes: Union[str, List[str]],
        handler: Optional[Callable] = None,
        **metadata,
    ) -> List[str]:
        """채권지수 실시간체결가 (H0BICNT0)."""
        return self._subscribe_each(
            SubscriptionType.BOND_INDEX, codes, handler, metadata
        )

    def unsubscribe_stock(self, code: str, include_nxt: bool = True) -> None:
        """
        종목 관련 모든 구독 해제 (편의 메서드)

        Args:
            code: 종목코드
            include_nxt: NXT 시장 구독도 함께 해제할지 여부 (기본값: True)
        """
        # KRX 시장 타입
        stock_types = [
            SubscriptionType.STOCK_TRADE,
            SubscriptionType.STOCK_ASK_BID,
            SubscriptionType.STOCK_EXPECTED,
            SubscriptionType.PROGRAM_TRADE,
            SubscriptionType.MEMBER_TRADE,
        ]

        # NXT 시장 타입 추가
        if include_nxt:
            stock_types.extend(
                [
                    SubscriptionType.STOCK_TRADE_NXT,
                    SubscriptionType.STOCK_ASK_BID_NXT,
                    SubscriptionType.STOCK_EXPECTED_NXT,
                    SubscriptionType.PROGRAM_TRADE_NXT,
                    SubscriptionType.MEMBER_TRADE_NXT,
                ]
            )

        for sub_type in stock_types:
            sub_id = f"{sub_type.value}_{code}"
            if sub_id in self.subscriptions:
                self.unsubscribe(sub_id)

    def unsubscribe_stock_nxt(self, code: str) -> None:
        """
        NXT 시장 종목 관련 모든 구독 해제 (편의 메서드)

        Args:
            code: 종목코드
        """
        nxt_types = [
            SubscriptionType.STOCK_TRADE_NXT,
            SubscriptionType.STOCK_ASK_BID_NXT,
            SubscriptionType.STOCK_EXPECTED_NXT,
            SubscriptionType.PROGRAM_TRADE_NXT,
            SubscriptionType.MEMBER_TRADE_NXT,
        ]
        for sub_type in nxt_types:
            sub_id = f"{sub_type.value}_{code}"
            if sub_id in self.subscriptions:
                self.unsubscribe(sub_id)

    def unsubscribe_all(self) -> None:
        """
        모든 구독 해제
        """
        for sub_id in list(self.subscriptions.keys()):
            self.unsubscribe(sub_id)
