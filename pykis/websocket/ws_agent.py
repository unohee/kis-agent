import asyncio
import contextlib
import json
import logging
from base64 import b64decode
from dataclasses import dataclass, field
from datetime import datetime
from datetime import time as dt_time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import pytz
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from websockets.exceptions import ConnectionClosed

from .ws_helpers import RealtimeDataParser, RealtimeDataStore, WSAgentWithStore

logger = logging.getLogger(__name__)

# 장 마감 시간 (KST)
MARKET_CLOSE_TIME = dt_time(15, 30)


def _is_after_market_close() -> bool:
    """장 마감 후인지 확인 (KRX: 15:30 이후, NXT: 20:00 이후)

    NXT 세션 (16:00-20:00)은 마감으로 처리하지 않음
    """
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    # 주말 체크 (5=토요일, 6=일요일)
    if now.weekday() >= 5:
        return True

    current_time = now.time()
    # NXT 세션 체크 (16:00-20:00)
    nxt_start = dt_time(16, 0)
    nxt_end = dt_time(20, 0)
    if nxt_start <= current_time <= nxt_end:
        return False  # NXT 세션 중이므로 마감 아님

    # 15:30 이후 체크 (NXT 세션 제외)
    return current_time > MARKET_CLOSE_TIME


class SubscriptionType(Enum):
    """실시간 구독 타입: KRX(STOCK_*), NXT(*_NXT), 지수(INDEX*), 선물옵션, 해외"""

    # 국내주식 실시간 (KRX)
    STOCK_TRADE = "H0STCNT0"  # 국내주식 실시간 체결가 (KRX)
    STOCK_ASK_BID = "H0STASP0"  # 국내주식 실시간 호가 (KRX)
    STOCK_EXPECTED = "H0UNANC0"  # 국내주식 실시간 예상체결 (통합)
    STOCK_NOTICE = "H0STCNI0"  # 국내주식 체결통보
    STOCK_NOTICE_AH = "H0STCNI9"  # 국내주식 시간외 체결통보

    # 국내주식 실시간 (NXT)
    STOCK_TRADE_NXT = "H0NXCNT0"  # 국내주식 실시간 체결가 (NXT)
    STOCK_ASK_BID_NXT = "H0NXASP0"  # 국내주식 실시간 호가 (NXT)
    STOCK_EXPECTED_NXT = "H0NXANC0"  # 국내주식 실시간 예상체결 (NXT)
    PROGRAM_TRADE_NXT = "H0NXPGM0"  # 국내주식 실시간 프로그램매매 (NXT)
    MARKET_OPERATION_NXT = "H0NXMKO0"  # 국내주식 장운영정보 (NXT)
    MEMBER_TRADE_NXT = "H0NXMBC0"  # 국내주식 실시간 회원사 (NXT)

    # 지수 실시간
    INDEX = "H0IF1000"  # 지수 실시간
    INDEX_EXPECTED = "H0UPANC0"  # 지수 실시간 예상체결

    # 프로그램매매/회원사 (KRX)
    PROGRAM_TRADE = "H0STPGM0"  # 프로그램매매 실시간 (KRX)
    MEMBER_TRADE = "H0MBCNT0"  # 회원사별 실시간 매매동향

    # 선물/옵션
    FUTURES_TRADE = "H0CFCNT0"  # 선물 체결
    FUTURES_ASK_BID = "H0CFASP0"  # 선물 호가
    OPTION_TRADE = "H0OPCNT0"  # 옵션 체결
    OPTION_ASK_BID = "H0OPASP0"  # 옵션 호가

    # 해외
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
    """다중 구독 웹소켓 에이전트. 종목/지수/선물 동시 구독, 자동 재연결, AES256 처리."""

    def __init__(
        self,
        approval_key: str,
        url: str = "ws://ops.koreainvestment.com:21000",
        ping_interval: int = 30,
        ping_timeout: int = 30,
        auto_reconnect: bool = True,
        client: Optional[Any] = None,  # KISClient 인스턴스 (토큰 재발급용)
    ):
        """
        WSAgent 초기화

        Args:
            approval_key (str): 웹소켓 승인키 (KISClient.get_ws_approval_key()로 취득)
            url (str): 웹소켓 서버 URL. 기본값은 실전투자 서버
            ping_interval (int): ping 전송 간격 (초)
            ping_timeout (int): ping 응답 대기 시간 (초)
            auto_reconnect (bool): 연결 실패 시 자동 재연결 여부
            client (Optional[Any]): KISClient 인스턴스. 제공 시 토큰 재발급 시 approval_key도 갱신

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
            client: KISClient 인스턴스 (토큰 재발급용)
        """
        self.approval_key = approval_key
        self.url = url
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.auto_reconnect = auto_reconnect
        self.client = client  # KISClient 인스턴스 저장 (토큰 재발급용)

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

        # 구독 응답 대기 관리
        self._pending_subscriptions: Dict[str, asyncio.Event] = {}
        self._subscription_results: Dict[str, bool] = {}  # True=성공, False=실패
        self._subscription_errors: Dict[str, str] = {}  # 실패 시 에러 메시지

        # 통계
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "errors": 0,
            "reconnects": 0,
            "last_message_time": None,
        }

    def update_approval_key(self, new_approval_key: str) -> None:
        """
        approval_key 갱신 (토큰 재발급 시 사용)

        Args:
            new_approval_key: 새로운 승인키
        """
        if not new_approval_key:
            logger.warning("빈 approval_key로 갱신 시도 무시")
            return

        old_key = self.approval_key[:10] if self.approval_key else "None"
        self.approval_key = new_approval_key
        new_key = new_approval_key[:10]
        logger.info(f"approval_key 갱신 완료: {old_key}... → {new_key}...")

        # 연결 중인 경우 재연결 필요 (새 approval_key로 재연결)
        if self.connected:
            logger.warning("연결 중 approval_key 갱신됨. 재연결이 필요할 수 있습니다.")

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

        # 연결되어 있으면 비동기 태스크 생성 (결과 추적)
        if self.connected and self.ws and not self.ws.closed:
            task = asyncio.create_task(self._send_subscription(subscription))
            # 태스크 완료 시 실패 로깅을 위한 콜백 추가
            task.add_done_callback(lambda t: self._on_subscription_task_done(t, sub_id))

        return sub_id

    def _on_subscription_task_done(self, task: asyncio.Task, sub_id: str):
        """구독 태스크 완료 콜백"""
        try:
            result = task.result()
            if not result:
                logger.warning(f"백그라운드 구독 실패: {sub_id}")
        except Exception as e:
            logger.error(f"구독 태스크 예외: {sub_id} - {e}")

    async def subscribe_async(
        self,
        sub_type: SubscriptionType,
        key: str,
        handler: Optional[Callable] = None,
        **metadata,
    ) -> Tuple[str, bool]:
        """
        비동기 구독 추가 (연결 상태에서 사용 권장)

        Args:
            sub_type: 구독 타입
            key: 종목코드/지수코드 등
            handler: 개별 핸들러 (옵션)
            **metadata: 추가 메타데이터

        Returns:
            tuple[str, bool]: (구독 ID, 성공 여부)
        """
        sub_id = f"{sub_type.value}_{key}"

        if sub_id in self.subscriptions:
            logger.warning(f"이미 구독 중: {sub_id}")
            return sub_id, True

        subscription = Subscription(
            sub_type=sub_type, key=key, handler=handler, metadata=metadata
        )

        self.subscriptions[sub_id] = subscription

        # 연결되어 있으면 구독 요청 및 응답 대기
        if self.connected and self.ws and not self.ws.closed:
            success = await self._send_subscription(subscription)
            if not success:
                # 구독 실패 시 등록 제거
                del self.subscriptions[sub_id]
            return sub_id, success

        return sub_id, False

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

        # 구독 해제 메시지 전송 (연결 상태 상세 검증)
        if self.connected and self.ws and not self.ws.closed:
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

    async def _send_subscription(
        self,
        subscription: Subscription,
        max_retries: int = 3,
        timeout: float = 60.0,  # 타임아웃을 60초로 설정
    ) -> bool:
        """
        구독 요청 전송 및 응답 대기

        Args:
            subscription: 구독 정보
            max_retries: 최대 재시도 횟수
            timeout: 응답 대기 타임아웃 (초)

        Returns:
            bool: 구독 성공 여부
        """
        sub_id = f"{subscription.sub_type.value}_{subscription.key}"

        for attempt in range(max_retries):
            try:
                # 연결 상태 상세 검증
                if not self.ws or self.ws.closed:
                    logger.error(f"구독 요청 실패 - 웹소켓 연결 없음: {sub_id}")
                    return False

                # 응답 대기용 Event 설정
                self._pending_subscriptions[sub_id] = asyncio.Event()
                self._subscription_results[sub_id] = False
                self._subscription_errors[sub_id] = ""

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
                logger.info(
                    f"구독 요청 전송: {sub_id} (시도 {attempt + 1}/{max_retries})"
                )

                # 응답 대기
                try:
                    await asyncio.wait_for(
                        self._pending_subscriptions[sub_id].wait(),
                        timeout=timeout,
                    )

                    # 응답 결과 확인
                    if self._subscription_results.get(sub_id, False):
                        self.active_subscriptions.add(sub_id)
                        logger.info(f"구독 성공 확인: {sub_id}")
                        return True
                    else:
                        error_msg = self._subscription_errors.get(
                            sub_id, "알 수 없는 오류"
                        )
                        logger.warning(f"구독 실패 응답: {sub_id} - {error_msg}")

                except asyncio.TimeoutError:
                    logger.warning(
                        f"구독 응답 타임아웃: {sub_id} (시도 {attempt + 1}/{max_retries})"
                    )

            except ConnectionClosed as e:
                logger.error(f"구독 중 연결 종료: {sub_id} - {e}")
                return False

            except Exception as e:
                logger.error(f"구독 요청 오류: {sub_id} - {e}")

            finally:
                # 정리
                self._pending_subscriptions.pop(sub_id, None)

            # 재시도 전 대기 (지수 백오프)
            if attempt < max_retries - 1:
                wait_time = 0.5 * (2**attempt)
                logger.info(f"재시도 대기: {wait_time}초")
                await asyncio.sleep(wait_time)

        logger.error(f"구독 최종 실패: {sub_id} ({max_retries}회 시도)")
        self.stats["errors"] += 1
        return False

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

    async def _subscribe_all(self) -> dict:
        """
        모든 구독 요청 전송 (순차 처리 + 딜레이로 안정성 개선)

        KIS 서버에서 빠른 구독 요청을 처리하지 못하는 문제를 해결하기 위해
        순차 처리와 딜레이를 적용합니다.

        Returns:
            dict: 구독 결과 {"success": [...], "failed": [...]}
        """
        results = {"success": [], "failed": []}
        total = len(self.subscriptions)

        logger.info(f"구독 시작: 총 {total}개 종목 (순차 처리)")

        # 순차 처리로 구독 요청 (연결 안정성 향상)
        for idx, subscription in enumerate(self.subscriptions.values()):
            sub_id = f"{subscription.sub_type.value}_{subscription.key}"

            # 연결 상태 확인
            if not self.ws or self.ws.closed:
                logger.error(
                    f"구독 중단 - 연결 끊김 (성공: {len(results['success'])}, 남은: {total - idx})"
                )
                # 남은 구독들을 실패로 처리
                remaining_subs = list(self.subscriptions.values())[idx:]
                for remaining in remaining_subs:
                    remaining_id = f"{remaining.sub_type.value}_{remaining.key}"
                    results["failed"].append(remaining_id)
                break

            try:
                success = await self._send_subscription(subscription)
                if success:
                    results["success"].append(sub_id)
                else:
                    results["failed"].append(sub_id)

                # 진행 상황 로깅 (10개마다)
                if (idx + 1) % 10 == 0:
                    logger.info(
                        f"구독 진행: {idx + 1}/{total} (성공: {len(results['success'])})"
                    )

                # 구독 사이 딜레이 (0.1초) - 서버 부하 방지
                if idx < total - 1:
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"구독 요청 중 예외 발생: {sub_id} - {e}")
                results["failed"].append(sub_id)

        # 결과 로깅
        if results["failed"]:
            logger.warning(f"일부 구독 실패: {len(results['failed'])}개")
        logger.info(
            f"구독 완료: 성공 {len(results['success'])}개, 실패 {len(results['failed'])}개"
        )

        return results

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

    def _handle_subscription_response(self, json_data: dict) -> bool:
        """
        구독 응답 메시지 처리

        Args:
            json_data: 파싱된 JSON 데이터

        Returns:
            bool: 구독 응답 메시지인 경우 True (추가 처리 불필요)
        """
        header = json_data.get("header", {})
        body = json_data.get("body", {})

        tr_id = header.get("tr_id", "")
        tr_key = header.get("tr_key", "")
        msg1 = body.get("msg1", "")
        rt_cd = body.get("rt_cd", "")

        # 구독 응답 메시지 확인
        if not msg1:
            return False

        sub_id = f"{tr_id}_{tr_key}" if tr_key else tr_id

        # 대기 중인 구독이 있는지 확인
        pending_event = self._pending_subscriptions.get(sub_id)
        if not pending_event:
            # tr_key 없이 tr_id만으로도 확인
            for key in list(self._pending_subscriptions.keys()):
                if key.startswith(f"{tr_id}_"):
                    sub_id = key
                    pending_event = self._pending_subscriptions.get(sub_id)
                    break

        if pending_event:
            # 구독 성공
            if "SUBSCRIBE SUCCESS" in msg1.upper() or rt_cd == "0":
                self._subscription_results[sub_id] = True
                logger.info(f"구독 응답 수신 (성공): {sub_id} - {msg1}")
            else:
                # 구독 실패
                self._subscription_results[sub_id] = False
                self._subscription_errors[sub_id] = msg1
                logger.warning(f"구독 응답 수신 (실패): {sub_id} - {msg1}")

            pending_event.set()
            return True

        # 일반 구독 성공/실패 로그 (대기 중이 아닌 경우)
        if "SUBSCRIBE SUCCESS" in msg1.upper():
            logger.info(f"구독 성공: {tr_id} ({tr_key})")
            return True
        elif "UNSUBSCRIBE" in msg1.upper():
            logger.info(f"구독 해제: {tr_id} ({tr_key})")
            return True

        return False

    async def _handle_message(self, data: str):
        """메시지 처리"""
        try:
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = datetime.now()

            # PINGPONG 메시지는 무시
            if "PINGPONG" in data:
                return

            # JSON 메시지인 경우 구독 응답 먼저 확인
            if data.startswith("{"):
                try:
                    json_data = json.loads(data)
                    if self._handle_subscription_response(json_data):
                        return  # 구독 응답 메시지는 여기서 처리 완료
                except json.JSONDecodeError:
                    pass

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

    async def _receive_loop(self, websocket):
        """
        메시지 수신 루프 (별도 Task로 실행)

        구독 응답을 처리하기 위해 connect() 초기에 백그라운드 Task로 시작됩니다.
        이렇게 하면 구독 요청을 보내고 응답을 기다리는 동안에도
        메시지 수신이 계속 되어 교착 상태를 방지합니다.

        다량 구독 중에도 ping/pong 응답을 받을 수 있도록
        타임아웃을 더 유연하게 처리합니다.

        Args:
            websocket: 웹소켓 연결 객체
        """
        ping_retry_count = 0
        max_ping_retries = 5  # ping/pong 최대 재시도 횟수 증가 (3→5)
        # 다량 구독 중에도 ping 응답을 받을 수 있도록 타임아웃 증가
        # ping_interval * 3으로 설정하여 구독 처리 중에도 ping 응답 대기 시간 확보
        recv_timeout = max(90, self.ping_interval * 3)  # recv 타임아웃 증가 (60→90초)
        last_ping_time = None
        ping_check_interval = 20  # 20초마다 ping 체크

        while self.connected:
            try:
                # recv 타임아웃을 더 짧게 설정하여 ping 체크 주기적으로 수행
                data = await asyncio.wait_for(
                    websocket.recv(), timeout=min(recv_timeout, ping_check_interval)
                )
                await self._handle_message(data)
                ping_retry_count = 0  # 메시지 수신 성공 시 재시도 카운트 리셋
                last_ping_time = None  # 메시지 수신 시 ping 체크 시간 리셋

            except asyncio.TimeoutError:
                # ping/pong으로 연결 확인 (설정된 타임아웃 사용)
                now = datetime.now()
                # 마지막 ping 체크로부터 일정 시간 경과했거나 첫 ping인 경우에만 ping 전송
                if (
                    last_ping_time is None
                    or (now - last_ping_time).total_seconds() >= ping_check_interval
                ):
                    try:
                        pong_waiter = await websocket.ping()
                        await asyncio.wait_for(pong_waiter, timeout=self.ping_timeout)
                        ping_retry_count = 0  # ping 성공 시 리셋
                        last_ping_time = now
                        logger.debug("ping/pong 성공, 연결 유지")
                    except asyncio.TimeoutError:
                        ping_retry_count += 1
                        last_ping_time = now
                        if ping_retry_count >= max_ping_retries:
                            logger.error(
                                f"ping/pong 타임아웃 {max_ping_retries}회 연속 실패, 재연결 필요"
                            )
                            break
                        logger.warning(
                            f"ping/pong 타임아웃 ({ping_retry_count}/{max_ping_retries}), 재시도..."
                        )
                        await asyncio.sleep(1)  # 재시도 전 짧은 대기
                    except Exception as e:
                        ping_retry_count += 1
                        last_ping_time = now
                        if ping_retry_count >= max_ping_retries:
                            logger.error(
                                f"ping/pong 실패 {max_ping_retries}회 연속: {e}"
                            )
                            break
                        logger.warning(
                            f"ping/pong 오류 ({ping_retry_count}/{max_ping_retries}): {e}"
                        )
                        await asyncio.sleep(1)
                else:
                    # ping 체크 간격이 지나지 않았으면 메시지 수신 재시도
                    continue

            except ConnectionClosed:
                logger.warning("웹소켓 연결 종료 (수신 루프)")
                break
            except asyncio.CancelledError:
                logger.debug("수신 루프 취소됨")
                break
            except Exception as e:
                logger.error(f"수신 루프 오류: {e}")
                break

    async def connect(self):
        """
        웹소켓 서버에 연결하고 메시지 수신 루프를 시작합니다.

        이 메서드는 비동기 루프를 실행하며, auto_reconnect가 True인 경우
        연결이 끊어질 때마다 자동으로 재연결을 시도합니다.

        연결되면 기존에 등록된 모든 구독에 대해 자동으로 구독 요청을 전송합니다.
        메시지 수신 루프는 별도 Task로 시작되어 구독 응답을 처리합니다.

        장 마감 후(15:30 이후 또는 주말)에는 연결을 시도하지 않습니다.

        Raises:
            Exception: 연결 실패 또는 메시지 처리 오류
        """
        # 장 마감 후 연결 시도 차단 (EOD 모드)
        if _is_after_market_close():
            logger.info("📴 장 마감 시간 - WebSocket 연결 시도 차단 (EOD 모드)")
            self.auto_reconnect = False
            return

        while self.auto_reconnect:
            receive_task = None
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

                    # 메시지 수신 Task 먼저 시작 (백그라운드)
                    # 이렇게 해야 구독 응답을 받을 수 있음
                    receive_task = asyncio.create_task(self._receive_loop(websocket))

                    # 수신 루프가 시작될 때까지 잠시 대기
                    await asyncio.sleep(0.1)

                    # 모든 구독 요청 전송 (수신 루프와 병렬로 실행)
                    await self._subscribe_all()

                    # 수신 루프 완료 대기 (연결이 끊어질 때까지)
                    await receive_task

            except Exception as e:
                logger.error(f"웹소켓 오류: {e}")

                # 토큰 재발급이 필요한 경우 (401, 403 등 인증 오류)
                if "401" in str(e) or "403" in str(e) or "인증" in str(e):
                    logger.warning("인증 오류 감지. approval_key 갱신 시도...")
                    if self.client:
                        try:
                            new_approval_key = self.client.get_ws_approval_key(
                                force_refresh=True
                            )
                            if new_approval_key:
                                self.update_approval_key(new_approval_key)
                                logger.info("approval_key 갱신 완료. 재연결 시도...")
                        except Exception as refresh_error:
                            logger.error(f"approval_key 갱신 실패: {refresh_error}")

            finally:
                self.connected = False
                self.ws = None
                self.active_subscriptions.clear()
                # 수신 Task 정리
                if receive_task and not receive_task.done():
                    receive_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await receive_task

            if self.auto_reconnect:
                # 장 마감 후(15:30 이후) 재연결 중단 (EOD 모드)
                if _is_after_market_close():
                    logger.info("📴 장 마감 시간 - WebSocket 재연결 중단 (EOD 모드)")
                    self.auto_reconnect = False
                    break

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
        return list(self.active_subscriptions)

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
            self.subscribe(SubscriptionType.FUTURES_TRADE, code, handler, **metadata)
        )
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.FUTURES_ASK_BID, code, handler, **metadata
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
        옵션 실시간 구독 (편의 메서드)

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
            self.subscribe(SubscriptionType.OPTION_TRADE, code, handler, **metadata)
        )
        if with_orderbook:
            sub_ids.append(
                self.subscribe(
                    SubscriptionType.OPTION_ASK_BID, code, handler, **metadata
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


# ============================================================================
# 헬퍼 클래스: ws_helpers.py에서 re-export (하위 호환성)
# ============================================================================

__all__ = [
    "WSAgent",
    "SubscriptionType",
    "Subscription",
    "RealtimeDataParser",
    "RealtimeDataStore",
    "WSAgentWithStore",
]
