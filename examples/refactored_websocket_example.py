#!/usr/bin/env python3
"""
리팩토링된 WebSocket 클라이언트 사용 예제

책임이 분리되고 디자인 패턴이 적용된 새로운 WebSocket 클라이언트를 사용하는 예제입니다.
"""
import asyncio
import logging
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent
from pykis.websocket import (
    ClientType,
    EventType,
    WebSocketClientBuilder,
    WebSocketClientFactory,
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def on_trade_update(event):
    """체결 데이터 콜백"""
    data = event.data
    print(f" 체결: {data.get('code')} - {data.get('price'):,}원")


async def on_index_update(event):
    """지수 데이터 콜백"""
    data = event.data
    print(
        f" {data.get('name')}: {data.get('value'):.2f} ({data.get('change_rate'):+.2f}%)"
    )


async def on_error(event):
    """에러 콜백"""
    logger.error(f" 에러 발생: {event.data}")


async def example_with_factory():
    """
    Factory 패턴을 사용한 WebSocket 클라이언트 예제
    """
    print("=" * 60)
    print(" Factory 패턴 사용 예제")
    print("=" * 60)

    # Agent 생성
    agent = Agent()

    # WebSocket 승인키 발급
    approval_key = agent.client.get_ws_approval_key()
    print(f" 승인키 발급: {approval_key[:20]}...")

    # Factory로 실시간 트레이딩 클라이언트 생성
    client = WebSocketClientFactory.create_client(
        ClientType.REALTIME,
        approval_key,
        stock_codes=["005930", "000660"],  # 삼성전자, SK하이닉스
        enable_orderbook=True,
        enable_program_trading=True,
    )

    # 이벤트 핸들러 등록
    client.register_callback(EventType.TRADE_UPDATE, on_trade_update)
    client.register_callback(EventType.INDEX_UPDATE, on_index_update)
    client.register_callback(EventType.ERROR, on_error)

    try:
        # 연결
        await client.connect()
        print(" WebSocket 연결 성공")

        # 종목 구독
        for code in client.stock_subscriptions:
            await client.subscribe_stock(code, with_orderbook=True)

        # 지수 구독
        await client.subscribe_index()

        # 10초간 실행
        await asyncio.wait_for(client.run(), timeout=10)

    except asyncio.TimeoutError:
        print("\n 10초 실행 완료")
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        raise
    finally:
        # 연결 종료
        await client.disconnect()
        print(" WebSocket 연결 종료")

        # 메트릭 출력
        metrics = client.get_metrics()
        print("\n 메트릭:")
        print(f"  - 수신 메시지: {metrics.get('messages_received', 0)}")
        print(f"  - 처리 메시지: {metrics.get('messages_processed', 0)}")
        print(f"  - 오류 수: {metrics.get('errors', 0)}")


async def example_with_builder():
    """
    Builder 패턴을 사용한 WebSocket 클라이언트 예제
    """
    print("\n" + "=" * 60)
    print(" Builder 패턴 사용 예제")
    print("=" * 60)

    # Agent 생성
    agent = Agent()

    # WebSocket 승인키 발급
    approval_key = agent.client.get_ws_approval_key()
    print(f" 승인키 발급: {approval_key[:20]}...")

    # Builder로 클라이언트 구성
    client = (
        WebSocketClientBuilder(approval_key)
        .add_stocks(["005930", "035420"])  # 삼성전자, NAVER
        .with_index_subscription()
        .with_program_trading_subscription()
        .with_auto_reconnect(True)
        .with_ping_settings(interval=20, timeout=10)
        .with_logging(True)
        .with_metrics(True)
        .build()
    )

    # 이벤트 핸들러 등록
    client.register_callback(EventType.TRADE_UPDATE, on_trade_update)
    client.register_callback(EventType.INDEX_UPDATE, on_index_update)

    try:
        # 연결
        await client.connect()
        print(" WebSocket 연결 성공")

        # 종목 구독
        for code in client.stock_subscriptions:
            await client.subscribe_stock(code)

        # 지수 구독
        await client.subscribe_index()

        # 10초간 실행
        await asyncio.wait_for(client.run(), timeout=10)

    except asyncio.TimeoutError:
        print("\n 10초 실행 완료")
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        raise
    finally:
        # 연결 종료
        await client.disconnect()
        print(" WebSocket 연결 종료")

        # 메트릭 출력
        metrics = client.get_metrics()
        print("\n 메트릭:")
        print(f"  - 실행 시간: {metrics.get('uptime_seconds', 0):.1f}초")
        print(f"  - 수신 메시지: {metrics.get('messages_received', 0)}")
        print(f"  - 처리 메시지: {metrics.get('messages_processed', 0)}")


async def example_monitoring_client():
    """
    모니터링 클라이언트 예제
    """
    print("\n" + "=" * 60)
    print(" 모니터링 클라이언트 예제")
    print("=" * 60)

    # Agent 생성
    agent = Agent()

    # WebSocket 승인키 발급
    approval_key = agent.client.get_ws_approval_key()
    print(f" 승인키 발급: {approval_key[:20]}...")

    # 모니터링 클라이언트 생성
    client = WebSocketClientFactory.create_client(
        ClientType.MONITORING,
        approval_key,
        major_stocks=["005930", "000660", "035420", "005380", "051910"],
    )

    # 이벤트 핸들러 등록
    async def on_monitoring_update(event):
        data = event.data
        if data.get("type") == "index":
            print(f"[지수] {data.get('name')}: {data.get('value'):.2f}")
        elif data.get("type") == "trade":
            print(f"[체결] {data.get('code')}: {data.get('price'):,}원")
        elif data.get("type") == "program_trading":
            print(f"[프로그램] {data.get('code')}: 순매수 {data.get('net_amount'):,}원")

    client.register_callback(EventType.TRADE_UPDATE, on_monitoring_update)
    client.register_callback(EventType.INDEX_UPDATE, on_monitoring_update)
    client.register_callback(EventType.PROGRAM_TRADING_UPDATE, on_monitoring_update)

    try:
        # 연결
        await client.connect()
        print(" 모니터링 시작")

        # 종목 및 지수 구독
        for code in client.stock_subscriptions:
            await client.subscribe_stock(code)
        await client.subscribe_index()

        # 10초간 모니터링
        await asyncio.wait_for(client.run(), timeout=10)

    except asyncio.TimeoutError:
        print("\n 모니터링 종료")
    except Exception as e:
        logger.error(f"모니터링 중 오류: {e}")
        raise
    finally:
        await client.disconnect()
        print(" 모니터링 클라이언트 종료")


async def main():
    """메인 함수"""
    print(" 리팩토링된 WebSocket 클라이언트 예제")
    print("=" * 60)

    try:
        # Factory 패턴 예제
        await example_with_factory()

        # Builder 패턴 예제
        await example_with_builder()

        # 모니터링 클라이언트 예제
        await example_monitoring_client()

    except Exception as e:
        logger.error(f"예제 실행 중 오류: {e}")
        raise

    print("\n 모든 예제 실행 완료")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n 프로그램을 종료합니다")
    except Exception as e:
        logger.error(f"프로그램 실행 실패: {e}")
        sys.exit(1)
