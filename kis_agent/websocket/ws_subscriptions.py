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

from typing import Callable, List, Optional

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
        handler: Optional[Callable] = None,
        **metadata,
    ) -> str:
        """
        NXT 시장 장운영정보 구독 (편의 메서드)

        장운영정보는 장 시작/마감, 동시호가 등 시장 상태 변화를 알려줍니다.

        Args:
            handler: 데이터 수신 핸들러
            **metadata: 추가 메타데이터

        Returns:
            str: 구독 ID

        Example:
            >>> agent.subscribe_market_operation_nxt()
            'H0NXMKO0_NXT'
        """
        return self.subscribe(
            SubscriptionType.MARKET_OPERATION_NXT, "NXT", handler, **metadata
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

    def subscribe_overseas_stock(
        self,
        code: str,
        handler: Optional[Callable] = None,
        with_orderbook: bool = False,
        **metadata,
    ) -> List[str]:
        """
        해외주식 실시간 구독 (편의 메서드)

        Args:
            code: 종목코드 (예: "AAPL", "MSFT")
            handler: 데이터 수신 핸들러
            with_orderbook: 실시간 호가도 함께 구독 (미국 1호가 무료)
            **metadata: 추가 메타데이터

        Returns:
            List[str]: 생성된 구독 ID 리스트

        Example:
            >>> agent.subscribe_overseas_stock("AAPL", with_orderbook=True)
            ['HDFSCNT0_AAPL', 'HDFSASP0_AAPL']
        """
        sub_ids = [
            self.subscribe(SubscriptionType.OVERSEAS_STOCK, code, handler, **metadata)
        ]
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.OVERSEAS_STOCK_ASK_BID, code, handler, **metadata
                )
            )
        return sub_ids

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
