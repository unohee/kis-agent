import asyncio
import json
import logging
from base64 import b64decode
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

logger = logging.getLogger(__name__)


class SubscriptionType(Enum):
    """구독 타입 정의"""

    STOCK_TRADE = "H0STCNT0"  # 국내주식 체결
    STOCK_ASK_BID = "H0STASP0"  # 국내주식 호가
    STOCK_NOTICE = "H0STCNI0"  # 국내주식 체결통보
    STOCK_NOTICE_AH = "H0STCNI9"  # 국내주식 시간외체결통보
    INDEX = "H0IF1000"  # 지수
    PROGRAM_TRADE = "H0GSCNT0"  # 프로그램매매
    FUTURES_TRADE = "H0CFCNT0"  # 선물 체결
    FUTURES_ASK_BID = "H0CFASP0"  # 선물 호가
    OPTION_TRADE = "H0OPCNT0"  # 옵션 체결
    OPTION_ASK_BID = "H0OPASP0"  # 옵션 호가
    OVERSEAS_STOCK = "HDFSCNT0"  # 해외주식 체결
    OVERSEAS_FUTURES = "HDFFF020"  # 해외선물 체결


@dataclass
class Subscription:
    """구독 정보"""

    sub_type: SubscriptionType
    key: str  # 종목코드 또는 지수코드
    handler: Optional[Callable] = None
    metadata: Dict = field(default_factory=dict)


class WSAgent:
    """
    다중 구독 가능한 웹소켓 에이전트

    이 클래스는 한국투자증권 OpenAPI의 실시간 데이터를 수신하기 위한
    웹소켓 연결을 관리하고, 다양한 타입의 데이터를 동시에 구독할 수 있게 합니다.

    주요 기능:
    - 여러 종목/지수/선물 등을 동시에 구독
    - 구독 타입별 핸들러 등록 및 관리
    - 자동 재연결 및 오류 복구
    - AES256 암호화 메시지 자동 처리
    - 실시간 통계 및 모니터링

    Example:
        >>> agent = WSAgent(approval_key="your_key")
        >>> agent.subscribe(SubscriptionType.STOCK_TRADE, "005930")
        >>> await agent.connect()
    """

    def __init__(
        self,
        approval_key: str,
        url: str = "ws://ops.koreainvestment.com:21000",
        ping_interval: int = 30,
        ping_timeout: int = 30,
        auto_reconnect: bool = True,
    ):
        """
        WSAgent 초기화

        Args:
            approval_key (str): 웹소켓 승인키 (KISClient.get_ws_approval_key()로 취득)
            url (str): 웹소켓 서버 URL. 기본값은 실전투자 서버
            ping_interval (int): ping 전송 간격 (초)
            ping_timeout (int): ping 응답 대기 시간 (초)
            auto_reconnect (bool): 연결 실패 시 자동 재연결 여부

        Raises:
            ValueError: approval_key가 None이거나 빈 문자열인 경우
        """
        if not approval_key:
            raise ValueError("approval_key는 필수입니다")
        """
        Args:
            approval_key: 웹소켓 승인키
            url: 웹소켓 URL
            ping_interval: ping 전송 간격
            ping_timeout: ping 응답 대기 시간
            auto_reconnect: 자동 재연결 여부
        """
        self.approval_key = approval_key
        self.url = url
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.auto_reconnect = auto_reconnect

        # 웹소켓 연결
        self.ws = None
        self.connected = False

        # 구독 관리
        self.subscriptions: Dict[str, Subscription] = (
            {}
        )  # key: f"{sub_type.value}_{key}"
        self.active_subscriptions: Set[str] = set()

        # 핸들러 관리
        self.type_handlers: Dict[SubscriptionType, List[Callable]] = {}
        self.default_handler: Optional[Callable] = None

        # AES 키 관리
        self.aes_keys: Dict[str, tuple] = {}  # tr_id: (key, iv)

        # 통계
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "errors": 0,
            "reconnects": 0,
            "last_message_time": None,
        }

    def subscribe(
        self,
        sub_type: SubscriptionType,
        key: str,
        handler: Optional[Callable] = None,
        **metadata,
    ) -> str:
        """
        새로운 구독을 추가합니다.

        Args:
            sub_type (SubscriptionType): 구독할 데이터 타입
            key (str): 종목코드, 지수코드 또는 기타 식별자
            handler (Optional[Callable]): 이 구독에만 적용될 개별 핸들러
            **metadata: 구독과 함께 저장될 추가 메타데이터

        Returns:
            str: 구독 ID ("{sub_type.value}_{key}" 형식)

        Raises:
            ValueError: sub_type이나 key가 유효하지 않은 경우

        Example:
            >>> agent.subscribe(SubscriptionType.STOCK_TRADE, "005930",
            ...                handler=my_handler, company="삼성전자")
            'H0STCNT0_005930'
        """
        """
        구독 추가

        Args:
            sub_type: 구독 타입
            key: 종목코드/지수코드 등
            handler: 개별 핸들러 (옵션)
            **metadata: 추가 메타데이터

        Returns:
            구독 ID
        """
        sub_id = f"{sub_type.value}_{key}"

        if sub_id in self.subscriptions:
            logger.warning(f"이미 구독 중: {sub_id}")
            return sub_id

        subscription = Subscription(
            sub_type=sub_type, key=key, handler=handler, metadata=metadata
        )

        self.subscriptions[sub_id] = subscription

        # 연결되어 있으면 즉시 구독 요청
        if self.connected and self.ws:
            asyncio.create_task(self._send_subscription(subscription))

        return sub_id

    def unsubscribe(self, sub_id: str):
        """
        기존 구독을 해제합니다.

        Args:
            sub_id (str): subscribe() 메서드에서 반환된 구독 ID

        Example:
            >>> agent.unsubscribe("H0STCNT0_005930")
        """
        """구독 해제"""
        if sub_id not in self.subscriptions:
            logger.warning(f"구독 정보 없음: {sub_id}")
            return

        subscription = self.subscriptions[sub_id]

        # 구독 해제 메시지 전송
        if self.connected and self.ws:
            asyncio.create_task(self._send_unsubscription(subscription))

        # 구독 정보 삭제
        del self.subscriptions[sub_id]
        self.active_subscriptions.discard(sub_id)

    def register_handler(self, sub_type: SubscriptionType, handler: Callable):
        """
        구독 타입별 공통 핸들러를 등록합니다.

        이 핸들러는 해당 타입의 모든 구독에 대해 호출됩니다.
        개별 구독의 핸들러와 다른 타입 핸들러들과 함께 호출됩니다.

        Args:
            sub_type (SubscriptionType): 구독 타입
            handler (Callable): 핸들러 함수. (data, metadata) 두 개 인자를 받아야 합니다.

        Example:
            >>> def handle_all_trades(data, metadata):
            ...     print(f"체결: {data}")
            >>> agent.register_handler(SubscriptionType.STOCK_TRADE, handle_all_trades)
        """
        """
        타입별 핸들러 등록

        Args:
            sub_type: 구독 타입
            handler: 핸들러 함수 (data, metadata를 인자로 받음)
        """
        if sub_type not in self.type_handlers:
            self.type_handlers[sub_type] = []
        self.type_handlers[sub_type].append(handler)

    def set_default_handler(self, handler: Callable):
        """
        기본 핸들러를 설정합니다.

        이 핸들러는 모든 메시지에 대해 호출됩니다.
        개별 구독 핸들러나 타입별 핸들러와 함께 실행됩니다.

        Args:
            handler (Callable): 핸들러 함수. (data, metadata) 두 개 인자를 받아야 합니다.
        """
        """기본 핸들러 설정"""
        self.default_handler = handler

    async def _send_subscription(self, subscription: Subscription):
        """구독 요청 전송"""
        try:
            message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8",
                },
                "body": {
                    "input": {
                        "tr_id": subscription.sub_type.value,
                        "tr_key": subscription.key,
                    }
                },
            }

            await self.ws.send(json.dumps(message))
            sub_id = f"{subscription.sub_type.value}_{subscription.key}"
            self.active_subscriptions.add(sub_id)
            logger.info(f"구독 요청 전송: {sub_id}")

        except Exception as e:
            logger.error(f"구독 요청 실패: {e}")

    async def _send_unsubscription(self, subscription: Subscription):
        """구독 해제 요청 전송"""
        try:
            message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "2",  # 구독 해제
                    "content-type": "utf-8",
                },
                "body": {
                    "input": {
                        "tr_id": subscription.sub_type.value,
                        "tr_key": subscription.key,
                    }
                },
            }

            await self.ws.send(json.dumps(message))
            sub_id = f"{subscription.sub_type.value}_{subscription.key}"
            self.active_subscriptions.discard(sub_id)
            logger.info(f"구독 해제 요청 전송: {sub_id}")

        except Exception as e:
            logger.error(f"구독 해제 요청 실패: {e}")

    async def _subscribe_all(self):
        """모든 구독 요청 전송"""
        for subscription in self.subscriptions.values():
            await self._send_subscription(subscription)
            await asyncio.sleep(0.1)  # 요청 간 딜레이

    def _parse_message(self, data: str) -> tuple:
        """
        메시지 파싱

        Returns:
            (tr_id, tr_key, parsed_data)
        """
        if data.startswith("{"):
            # JSON 메시지
            json_data = json.loads(data)
            header = json_data.get("header", {})
            body = json_data.get("body", {})

            tr_id = header.get("tr_id")
            tr_key = header.get("tr_key")

            # AES 키 저장
            if tr_id in ["H0STCNI0", "H0STCNI9"]:
                output = body.get("output", {})
                if "key" in output and "iv" in output:
                    self.aes_keys[tr_id] = (output["key"], output["iv"])

            return tr_id, tr_key, json_data

        elif data[0] in ("0", "1"):
            # 바이너리 메시지
            parts = data.split("|")
            if len(parts) >= 4:
                tr_id = parts[1]
                encrypted = parts[2]

                # 암호화된 메시지 처리
                if encrypted == "1" and tr_id in self.aes_keys:
                    key, iv = self.aes_keys[tr_id]
                    decrypted = self._decrypt_aes(key, iv, parts[3])
                    values = decrypted.split("^")
                else:
                    values = parts[3].split("^")

                tr_key = values[0] if values else None
                return tr_id, tr_key, values

        return None, None, None

    def _decrypt_aes(self, key: str, iv: str, cipher_text: str) -> str:
        """AES256 복호화"""
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        return bytes.decode(
            unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size)
        )

    async def _handle_message(self, data: str):
        """메시지 처리"""
        try:
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = datetime.now()

            # PINGPONG 메시지는 무시
            if "PINGPONG" in data:
                return

            tr_id, tr_key, parsed_data = self._parse_message(data)

            if not tr_id:
                return

            # 구독 ID 생성
            sub_id = f"{tr_id}_{tr_key}" if tr_key else tr_id

            # 해당 구독 찾기
            subscription = self.subscriptions.get(sub_id)

            # 타입별 핸들러 실행
            try:
                sub_type = SubscriptionType(tr_id)

                # 개별 핸들러 실행
                if subscription and subscription.handler:
                    await self._call_handler(
                        subscription.handler, parsed_data, subscription.metadata
                    )

                # 타입별 핸들러 실행
                if sub_type in self.type_handlers:
                    for handler in self.type_handlers[sub_type]:
                        await self._call_handler(
                            handler,
                            parsed_data,
                            subscription.metadata if subscription else {},
                        )

                # 기본 핸들러 실행
                if self.default_handler:
                    await self._call_handler(
                        self.default_handler,
                        parsed_data,
                        {"tr_id": tr_id, "tr_key": tr_key},
                    )

                self.stats["messages_processed"] += 1

            except ValueError:
                # 알 수 없는 tr_id
                if self.default_handler:
                    await self._call_handler(
                        self.default_handler,
                        parsed_data,
                        {"tr_id": tr_id, "tr_key": tr_key},
                    )

        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            self.stats["errors"] += 1

    async def _call_handler(self, handler: Callable, data: Any, metadata: Dict):
        """핸들러 호출"""
        if asyncio.iscoroutinefunction(handler):
            await handler(data, metadata)
        else:
            handler(data, metadata)

    async def connect(self):
        """
        웹소켓 서버에 연결하고 메시지 수신 루프를 시작합니다.

        이 메서드는 비동기 루프를 실행하며, auto_reconnect가 True인 경우
        연결이 끊어질 때마다 자동으로 재연결을 시도합니다.

        연결되면 기존에 등록된 모든 구독에 대해 자동으로 구독 요청을 전송합니다.

        Raises:
            Exception: 연결 실패 또는 메시지 처리 오류
        """
        """웹소켓 연결 및 메시지 수신 루프"""
        while self.auto_reconnect:
            try:
                logger.info(f"웹소켓 연결 시도: {self.url}")

                async with websockets.connect(
                    self.url,
                    ping_interval=self.ping_interval,
                    ping_timeout=self.ping_timeout,
                ) as websocket:
                    self.ws = websocket
                    self.connected = True
                    logger.info("웹소켓 연결 성공")

                    # 모든 구독 요청 전송
                    await self._subscribe_all()

                    # 메시지 수신 루프
                    while True:
                        try:
                            data = await asyncio.wait_for(websocket.recv(), timeout=60)
                            await self._handle_message(data)

                        except asyncio.TimeoutError:
                            # ping/pong으로 연결 확인
                            try:
                                pong_waiter = await websocket.ping()
                                await asyncio.wait_for(pong_waiter, timeout=10)
                            except asyncio.TimeoutError:
                                logger.error(
                                    "ping/pong 타임아웃, 재연결 필요", exc_info=True
                                )
                                break
                            except Exception as e:
                                logger.error(f"ping/pong 실패: {e}", exc_info=True)
                                break

                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("웹소켓 연결 종료")
                            break

            except Exception as e:
                logger.error(f"웹소켓 오류: {e}")

            finally:
                self.connected = False
                self.ws = None
                self.active_subscriptions.clear()

            if self.auto_reconnect:
                self.stats["reconnects"] += 1
                logger.info("5초 후 재연결 시도...")
                await asyncio.sleep(5)
            else:
                break

    async def disconnect(self):
        """
        웹소켓 연결을 종료합니다.

        auto_reconnect를 False로 설정하고 현재 연결을 닫습니다.
        """
        """웹소켓 연결 종료"""
        self.auto_reconnect = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.connected = False
        logger.info("웹소켓 연결 종료")

    def get_stats(self) -> Dict[str, Any]:
        """
        웹소켓 통계 정보를 반환합니다.

        Returns:
            Dict[str, Any]: 다음 키들을 포함하는 딕셔너리:
                - messages_received: 수신한 매시지 총 개수
                - messages_processed: 처리한 매시지 총 개수
                - errors: 발생한 에러 개수
                - reconnects: 재연결 횟수
                - last_message_time: 마지막 매시지 수신 시간
        """
        """통계 정보 반환"""
        return self.stats.copy()

    def is_connected(self) -> bool:
        """
        웹소켓 연결 상태를 확인합니다.

        Returns:
            bool: 연결되어 있으면 True, 그렇지 않으면 False
        """
        """연결 상태 확인"""
        return self.connected

    def get_active_subscriptions(self) -> List[str]:
        """
        현재 활성 상태인 구독 목록을 반환합니다.

        Returns:
            List[str]: 활성 구독 ID 리스트
        """
        """활성 구독 목록 반환"""
        return list(self.active_subscriptions)
