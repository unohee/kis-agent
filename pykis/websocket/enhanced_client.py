import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import os
import json
import pandas as pd

from .ws_agent import WSAgent, SubscriptionType
from ..core.client import KISClient
from ..core.base_exception_handler import BaseExceptionHandler, exception_handler
from ..stock.api import StockAPI
from ..account.api import AccountAPI

logger = logging.getLogger(__name__)


class EnhancedWebSocketClient(BaseExceptionHandler):
    """
    WSAgent를 활용한 향상된 웹소켓 클라이언트

    이 클래스는 WSAgent를 기반으로 고수준 웹소켓 인터페이스를 제공합니다.
    비즈니스 로직에 집중할 수 있도록 복잡한 웹소켓 관리를 추상화합니다.

    주요 기능:
    - 다중 종목/지수/선물 동시 구독
    - 모듈화된 콜백 핸들러 시스템
    - 실시간 시장 데이터 자동 관리
    - 종목 동적 추가/제거 지원
    - 자동 데이터 로깅 및 보관

    Example:
        >>> client = EnhancedWebSocketClient(
        ...     client=kis_client,
        ...     account_info=account_info,
        ...     stock_codes=["005930", "000660"],
        ...     enable_index=True
        ... )
        >>> client.register_callback('on_trade', my_handler)
        >>> await client.start()
    """

    def __init__(
        self,
        client: KISClient,
        account_info: dict,
        stock_codes: List[str] = None,
        enable_index: bool = True,
        enable_program_trading: bool = False,
        enable_ask_bid: bool = False,
        enable_futures: bool = False,
        enable_options: bool = False,
    ):
        """
        EnhancedWebSocketClient 초기화

        Args:
            client (KISClient): KIS API 클라이언트 인스턴스
            account_info (dict): 계좌 정보 {'CANO': '...', 'ACNT_PRDT_CD': '...'}
            stock_codes (List[str], optional): 초기 구독할 종목코드 리스트
            enable_index (bool): 지수 데이터 구독 여부
            enable_program_trading (bool): 프로그램매매 데이터 구독 여부
            enable_ask_bid (bool): 호가 데이터 구독 여부
            enable_futures (bool): 선물 데이터 구독 여부
            enable_options (bool): 옵션 데이터 구독 여부
        """
        """
        Args:
            client: KIS API 클라이언트
            account_info: 계좌 정보
            stock_codes: 구독할 종목코드 리스트
            enable_index: 지수 구독 여부
            enable_program_trading: 프로그램매매 구독 여부
            enable_ask_bid: 호가 구독 여부
            enable_futures: 선물 구독 여부
            enable_options: 옵션 구독 여부
        """
        # BaseExceptionHandler 초기화
        super().__init__("EnhancedWebSocketClient")

        self.client = client
        self.account_info = account_info
        self.stock_api = StockAPI(client=client, account_info=account_info)
        self.account_api = AccountAPI(client=client, account_info=account_info)

        # 구독 설정
        self.stock_codes = stock_codes or []
        self.enable_index = enable_index
        self.enable_program_trading = enable_program_trading
        self.enable_ask_bid = enable_ask_bid
        self.enable_futures = enable_futures
        self.enable_options = enable_options

        # WSAgent 초기화
        approval_key = client.get_ws_approval_key()
        self.ws_agent = WSAgent(approval_key=approval_key)

        # 실시간 데이터 저장소
        self.market_data = {
            "stocks": {},  # 종목별 현재가
            "ask_bid": {},  # 종목별 호가
            "index": {},  # 지수
            "program": {},  # 프로그램매매
            "futures": {},  # 선물
            "options": {},  # 옵션
        }

        # 종목 정보
        self.stock_info = {}  # 종목코드: 종목명

        # 콜백 핸들러
        self.callbacks: Dict[str, List[Callable]] = {
            "on_trade": [],
            "on_ask_bid": [],
            "on_index": [],
            "on_program": [],
            "on_futures": [],
            "on_options": [],
        }

        # 로그 설정
        self.setup_logging()

    def setup_logging(self):
        """로그 디렉토리 설정"""
        self.log_dir = "logs/websocket"
        os.makedirs(self.log_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        self.data_log_file = os.path.join(self.log_dir, f"market_data_{date_str}.jsonl")

    def register_callback(self, event_type: str, callback: Callable):
        """
        이벤트 콜백을 등록합니다.

        Args:
            event_type (str): 이벤트 타입. 다음 중 하나:
                - 'on_trade': 주식 체결 데이터 수신 시
                - 'on_ask_bid': 호가 데이터 수신 시
                - 'on_index': 지수 데이터 수신 시
                - 'on_program': 프로그램매매 데이터 수신 시
            callback (Callable): 콜백 함수. 데이터 딕셔너리를 인자로 받습니다.

        Example:
            >>> def on_trade(data):
            ...     print(f"체결: {data['name']} {data['price']}원")
            >>> client.register_callback('on_trade', on_trade)
        """
        """
        콜백 등록
        
        Args:
            event_type: 이벤트 타입 (on_trade, on_ask_bid, on_index 등)
            callback: 콜백 함수
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    async def _init_subscriptions(self):
        """구독 초기화"""

        # 종목 정보 조회
        await self._fetch_stock_info()

        # 주식 체결 구독
        for code in self.stock_codes:
            self.ws_agent.subscribe(
                SubscriptionType.STOCK_TRADE, code, handler=self._handle_stock_trade
            )

            # 호가 구독
            if self.enable_ask_bid:
                self.ws_agent.subscribe(
                    SubscriptionType.STOCK_ASK_BID,
                    code,
                    handler=self._handle_stock_ask_bid,
                )

            # 프로그램매매 구독
            if self.enable_program_trading:
                self.ws_agent.subscribe(
                    SubscriptionType.PROGRAM_TRADE,
                    code,
                    handler=self._handle_program_trade,
                )

        # 지수 구독
        if self.enable_index:
            index_codes = ["0001", "1001", "2001"]  # KOSPI, KOSDAQ, KOSPI200
            for code in index_codes:
                self.ws_agent.subscribe(
                    SubscriptionType.INDEX, code, handler=self._handle_index
                )

    async def _fetch_stock_info(self):
        """종목 정보 조회"""
        for code in self.stock_codes:
            try:
                info = self.stock_api.get_stock_info(code)
                if isinstance(info, pd.DataFrame) and not info.empty:
                    self.stock_info[code] = info.iloc[0].get("prdt_name", code)
                else:
                    self.stock_info[code] = code
            except Exception as e:
                logger.error(f"종목 정보 조회 실패 {code}: {e}")
                self.stock_info[code] = code

    def _handle_stock_trade(self, data: Any, metadata: Dict):
        """주식 체결 데이터 처리"""
        try:
            if isinstance(data, list) and len(data) >= 19:
                code = data[0]
                trade_data = {
                    "code": code,
                    "name": self.stock_info.get(code, code),
                    "time": data[1],
                    "price": float(data[2]),
                    "change": float(data[4]),
                    "change_rate": float(data[5]),
                    "volume": int(data[12]) if len(data) > 12 else 0,
                    "amount": float(data[14]) if len(data) > 14 else 0,
                    "strength": float(data[18]) if len(data) > 18 else 0,
                    "timestamp": datetime.now(),
                }

                # 데이터 저장
                self.market_data["stocks"][code] = trade_data

                # 로그 기록
                self._log_data("trade", trade_data)

                # 콜백 실행
                for callback in self.callbacks["on_trade"]:
                    callback(trade_data)

        except Exception as e:
            logger.error(f"체결 데이터 처리 오류: {e}")

    def _handle_stock_ask_bid(self, data: Any, metadata: Dict):
        """호가 데이터 처리"""
        try:
            if isinstance(data, list) and len(data) >= 43:
                code = data[0]
                ask_bid_data = {
                    "code": code,
                    "name": self.stock_info.get(code, code),
                    "time": datetime.now(),
                    "sell_prices": [float(data[i]) for i in range(3, 13)],
                    "buy_prices": [float(data[i]) for i in range(13, 23)],
                    "sell_qty": [int(data[i]) for i in range(23, 33)],
                    "buy_qty": [int(data[i]) for i in range(33, 43)],
                }

                # 데이터 저장
                self.market_data["ask_bid"][code] = ask_bid_data

                # 콜백 실행
                for callback in self.callbacks["on_ask_bid"]:
                    callback(ask_bid_data)

        except Exception as e:
            logger.error(f"호가 데이터 처리 오류: {e}")

    def _handle_index(self, data: Any, metadata: Dict):
        """지수 데이터 처리"""
        try:
            if isinstance(data, list) and len(data) >= 10:
                code = data[0]
                index_map = {"0001": "KOSPI", "1001": "KOSDAQ", "2001": "KOSPI200"}

                index_data = {
                    "code": code,
                    "name": index_map.get(code, f"INDEX_{code}"),
                    "value": float(data[1]),
                    "change": float(data[2]),
                    "change_rate": float(data[3]),
                    "timestamp": datetime.now(),
                }

                # 데이터 저장
                self.market_data["index"][code] = index_data

                # 로그 기록
                self._log_data("index", index_data)

                # 콜백 실행
                for callback in self.callbacks["on_index"]:
                    callback(index_data)

        except Exception as e:
            logger.error(f"지수 데이터 처리 오류: {e}")

    def _handle_program_trade(self, data: Any, metadata: Dict):
        """프로그램매매 데이터 처리"""
        try:
            if isinstance(data, list) and len(data) >= 11:
                code = data[0]
                program_data = {
                    "code": code,
                    "name": self.stock_info.get(code, code),
                    "time": data[1],
                    "sell_volume": int(data[2]),
                    "sell_amount": float(data[3]),
                    "buy_volume": int(data[4]),
                    "buy_amount": float(data[5]),
                    "net_volume": int(data[6]),
                    "net_amount": float(data[7]),
                    "timestamp": datetime.now(),
                }

                # 데이터 저장
                self.market_data["program"][code] = program_data

                # 콜백 실행
                for callback in self.callbacks["on_program"]:
                    callback(program_data)

        except Exception as e:
            logger.error(f"프로그램매매 데이터 처리 오류: {e}")

    def _log_data(self, data_type: str, data: Dict):
        """데이터 로그 기록"""
        try:
            log_entry = {
                "type": data_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }

            with open(self.data_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")

        except Exception as e:
            logger.error(f"로그 기록 실패: {e}")

    def add_stock(self, code: str):
        """
        실시간으로 새로운 종목을 추가합니다.

        Args:
            code (str): 추가할 종목코드 (6자리 숫자)

        Example:
            >>> client.add_stock("000660")  # SK하이닉스 추가
        """
        """종목 추가"""
        if code not in self.stock_codes:
            self.stock_codes.append(code)

            # 종목 정보 조회
            try:
                info = self.stock_api.get_stock_info(code)
                if isinstance(info, pd.DataFrame) and not info.empty:
                    self.stock_info[code] = info.iloc[0].get("prdt_name", code)
            except Exception as e:
                logger.warning(f"종목 정보 조회 실패 {code}: {e}")
                self.stock_info[code] = code

            # 구독 추가
            self.ws_agent.subscribe(
                SubscriptionType.STOCK_TRADE, code, handler=self._handle_stock_trade
            )

            if self.enable_ask_bid:
                self.ws_agent.subscribe(
                    SubscriptionType.STOCK_ASK_BID,
                    code,
                    handler=self._handle_stock_ask_bid,
                )

            logger.info(f"종목 추가: {code} ({self.stock_info[code]})")

    def remove_stock(self, code: str):
        """
        종목을 제거하고 관련 구독을 해제합니다.

        Args:
            code (str): 제거할 종목코드
        """
        """종목 제거"""
        if code in self.stock_codes:
            self.stock_codes.remove(code)

            # 구독 해제
            self.ws_agent.unsubscribe(f"{SubscriptionType.STOCK_TRADE.value}_{code}")

            if self.enable_ask_bid:
                self.ws_agent.unsubscribe(
                    f"{SubscriptionType.STOCK_ASK_BID.value}_{code}"
                )

            # 데이터 삭제
            self.market_data["stocks"].pop(code, None)
            self.market_data["ask_bid"].pop(code, None)
            self.market_data["program"].pop(code, None)

            logger.info(f"종목 제거: {code}")

    def get_current_price(self, code: str) -> Optional[float]:
        """
        종목의 현재가를 조회합니다.

        Args:
            code (str): 조회할 종목코드

        Returns:
            Optional[float]: 현재가. 데이터가 없으면 None
        """
        """현재가 조회"""
        if code in self.market_data["stocks"]:
            return self.market_data["stocks"][code]["price"]
        return None

    def get_market_summary(self) -> Dict[str, Any]:
        """
        시장 요약 정보를 반환합니다.

        Returns:
            Dict[str, Any]: 다음 구조의 딕셔너리:
                {
                    'stocks': {
                        '종목코드': {
                            'name': '종목명',
                            'price': 현재가,
                            'change_rate': 등락률,
                            'volume': 거래량,
                            'strength': 체결강도
                        }
                    },
                    'indices': {
                        '지수명': {
                            'value': 지수값,
                            'change_rate': 변동률
                        }
                    },
                    'timestamp': 데이터 생성 시간
                }
        """
        """시장 요약 정보"""
        summary = {"stocks": {}, "indices": {}, "timestamp": datetime.now()}

        # 종목 정보
        for code, data in self.market_data["stocks"].items():
            summary["stocks"][code] = {
                "name": data["name"],
                "price": data["price"],
                "change_rate": data["change_rate"],
                "volume": data["volume"],
                "strength": data.get("strength", 0),
            }

        # 지수 정보
        for code, data in self.market_data["index"].items():
            summary["indices"][data["name"]] = {
                "value": data["value"],
                "change_rate": data["change_rate"],
            }

        return summary

    async def start(self):
        """
        웹소켓 클라이언트를 시작합니다.

        이 메서드는 비동기 루프로 실행되며, 웹소켓 연결을 설정하고
        모든 필요한 구독을 초기화한 후 데이터 수신을 시작합니다.
        """
        """웹소켓 시작"""
        logger.info("Enhanced WebSocket Client 시작")

        # 구독 초기화
        await self._init_subscriptions()

        # WSAgent 연결 시작
        await self.ws_agent.connect()

    async def stop(self):
        """
        웹소켓 클라이언트를 종료합니다.
        """
        """웹소켓 종료"""
        logger.info("Enhanced WebSocket Client 종료")
        await self.ws_agent.disconnect()

    def get_stats(self) -> Dict[str, Any]:
        """
        통계 정보를 반환합니다.

        WSAgent의 통계 정보에 추가 정보를 포함합니다.

        Returns:
            Dict[str, Any]: 통계 정보 딕셔너리
        """
        """통계 정보"""
        stats = self.ws_agent.get_stats()
        stats["active_stocks"] = len(self.stock_codes)
        stats["total_subscriptions"] = len(self.ws_agent.subscriptions)
        return stats
