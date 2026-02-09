#!/usr/bin/env python3
"""
오프라인 WebSocket 구독 한도(41개) 모킹 테스트

네트워크 접근 없이 `WSAgent`가 41개 구독 요청을 정상 처리하고
`active_subscriptions` 집합에 41개가 등록되는지 확인합니다.

주의: 실제 한국투자증권 서버 연결이 아닌 모킹 환경입니다.
      원격 제약(계정당 한도) 자체를 보증하지는 않으며, 클라이언트 로직을 검증합니다.
"""
import asyncio
import contextlib
import json
import time
from typing import Any, Dict, Optional

# 테스트 대상 모듈
from pykis.websocket import ws_agent as ws_mod
from pykis.websocket.ws_agent import SubscriptionType, WSAgent


class FakeWebSocket:
    """WSAgent와 호환되는 최소한의 가짜 WebSocket 객체"""

    def __init__(self) -> None:
        # 간단한 메시지 큐로 recv를 구현
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self.closed: bool = False

    async def send(self, message: str) -> None:
        # WSAgent가 보내는 구독 요청(JSON)을 받아 즉시 성공 응답 JSON을 큐에 넣는다.
        data = json.loads(message)
        tr_id = data.get("body", {}).get("input", {}).get("tr_id")
        tr_key = data.get("body", {}).get("input", {}).get("tr_key")

        ack: Dict[str, Any] = {
            "header": {"tr_id": tr_id, "tr_key": tr_key},
            "body": {"rt_cd": "0", "msg1": "SUBSCRIBE SUCCESS"},
        }
        await self._queue.put(json.dumps(ack))

    async def recv(self) -> str:
        # 큐에서 메시지를 꺼내 반환. 닫힌 경우 예외 발생시켜 수신 루프 종료 유도
        if self.closed:
            raise Exception("fake websocket closed")
        msg = await self._queue.get()
        return msg

    async def ping(self):
        # websockets.ping() 호환: 즉시 완료되는 awaitable 반환
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        fut.set_result(True)
        return fut

    async def close(self) -> None:
        # 닫힘 표시 후 수신 대기를 깨우기 위해 센티넬 메시지 주입
        self.closed = True
        try:
            await self._queue.put("__CLOSE__")
        except Exception:
            pass


class FakeConnect:
    """`websockets.connect`를 대체할 비동기 컨텍스트 매니저"""

    def __init__(self, *args, **kwargs) -> None:
        self.ws = FakeWebSocket()

    async def __aenter__(self) -> FakeWebSocket:
        return self.ws

    async def __aexit__(self, exc_type, exc, tb) -> Optional[bool]:
        await self.ws.close()
        return None


async def run_mock_test() -> bool:
    # websockets.connect를 가짜로 교체
    original_connect = ws_mod.websockets.connect
    ws_mod.websockets.connect = lambda *a, **k: FakeConnect(*a, **k)  # type: ignore

    try:
        # 임의의 41개 종목 코드 (실제 유효성은 중요치 않음 — 모킹 환경)
        STOCK_CODES = [
            "005930",
            "000660",
            "035420",
            "035720",
            "051910",
            "006400",
            "068270",
            "028260",
            "105560",
            "055550",
            "003670",
            "012330",
            "066570",
            "032830",
            "096770",
            "003550",
            "034730",
            "015760",
            "017670",
            "030200",
            "033780",
            "010130",
            "009150",
            "000270",
            "005380",
            "018260",
            "034020",
            "010950",
            "086790",
            "024110",
            "316140",
            "009540",
            "010140",
            "011200",
            "036570",
            "259960",
            "352820",
            "003490",
            "000720",
            "005490",
            "000100",  # 41번째 코드 (임의)
        ]

        agent = WSAgent(approval_key="dummy-approval-key", auto_reconnect=True)

        # 41개 구독 등록
        for code in STOCK_CODES:
            agent.subscribe(SubscriptionType.STOCK_TRADE, code)

        # connect()를 태스크로 실행
        connect_task = asyncio.create_task(agent.connect())

        # 구독 완료까지 대기 (최대 5초)
        start = time.time()
        target = len(STOCK_CODES)
        success = False

        while time.time() - start < 5.0:
            await asyncio.sleep(0.05)
            if len(agent.active_subscriptions) == target:
                success = True
                break

        # 종료 처리: 태스크 취소 및 상태 정리
        # 우아한 종료: 먼저 disconnect로 수신 루프를 종료시키고 태스크를 기다린다
        try:
            await agent.disconnect()
        finally:
            with contextlib.suppress(asyncio.CancelledError):
                connect_task.cancel()
                await connect_task

        # 검증 결과 반환
        return success

    finally:
        # 패치 원복
        ws_mod.websockets.connect = original_connect  # type: ignore


if __name__ == "__main__":
    import contextlib

    ok = asyncio.run(run_mock_test())
    print("[MOCK] 41개 구독 등록 결과:", "성공" if ok else "실패")
    # 성공일 때 프로세스 0으로 종료
    raise SystemExit(0 if ok else 1)
