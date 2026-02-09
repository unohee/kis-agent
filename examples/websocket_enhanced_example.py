#!/usr/bin/env python3
"""
향상된 웹소켓 기능 예제

새로 추가된 기능들:
- 실시간 지수 구독 (코스피, 코스닥, 코스피200)
- 실시간 프로그램매매 구독
- 실시간 호가 구독 (선택적)
"""

import asyncio
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


async def enhanced_websocket_example():
    """
    향상된 웹소켓 기능을 시연하는 예제입니다.
    """
    try:
        # Agent 생성
        agent = Agent()

        print(" 향상된 웹소켓 기능 예제 시작")
        print("=" * 60)

        # 새로운 기능들을 활성화한 웹소켓 클라이언트 생성
        ws_client = agent.websocket(
            stock_codes=["005930", "000660"],  # 삼성전자, SK하이닉스
            enable_index=True,  #  지수 실시간 구독 활성화
            enable_program_trading=True,  #  프로그램매매 실시간 구독 활성화
            enable_ask_bid=False,  #  호가 구독은 비활성화 (너무 많은 데이터)
        )

        print(" 웹소켓 클라이언트 생성 완료")
        print(f"    지수 구독: {'활성화' if ws_client.enable_index else '비활성화'}")
        print(
            f"    프로그램매매: {'활성화' if ws_client.enable_program_trading else '비활성화'}"
        )
        print(f"    호가 구독: {'활성화' if ws_client.enable_ask_bid else '비활성화'}")
        print()

        print("🔑 웹소켓 승인키 발급 중...")
        approval_key = ws_client.get_approval()
        print(f" 승인키 발급 성공: {approval_key[:20]}...")
        print()

        print(" 웹소켓 연결 및 실시간 데이터 수신 시작...")
        print("   (10초간 실시간 데이터를 수신합니다)")
        print("=" * 60)

        # 웹소켓 연결 및 데이터 수신 (10초간)
        import websockets

        async with websockets.connect(
            ws_client.url, ping_interval=30, ping_timeout=30
        ) as websocket:
            ws_client.ws = websocket

            # 지수 구독 요청
            if ws_client.enable_index:
                index_codes = ["0001", "1001", "2001"]  # KOSPI, KOSDAQ, KOSPI200
                for index_code in index_codes:
                    index_name = ws_client.get_index_name(index_code)
                    senddata_index = {
                        "header": {
                            "approval_key": approval_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8",
                        },
                        "body": {"input": {"tr_id": "H0IF1000", "tr_key": index_code}},
                    }
                    await websocket.send(json.dumps(senddata_index))
                    print(f" {index_name} 지수 구독 요청 완료")

            # 종목별 구독 요청
            for stock_code in ws_client.stock_codes:
                # 체결정보 구독
                senddata_trade = {
                    "header": {
                        "approval_key": approval_key,
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8",
                    },
                    "body": {"input": {"tr_id": "H0STCNT0", "tr_key": stock_code}},
                }
                await websocket.send(json.dumps(senddata_trade))
                print(f" {stock_code} 체결정보 구독 요청 완료")

                # 프로그램매매 구독
                if ws_client.enable_program_trading:
                    senddata_program = {
                        "header": {
                            "approval_key": approval_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8",
                        },
                        "body": {"input": {"tr_id": "H0GSCNT0", "tr_key": stock_code}},
                    }
                    await websocket.send(json.dumps(senddata_program))
                    print(f" {stock_code} 프로그램매매 구독 요청 완료")

                await asyncio.sleep(0.1)

            print("\n 실시간 데이터 수신 중...")
            print("-" * 60)

            # 10초간 데이터 수신
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            index_count = 0
            trade_count = 0
            program_count = 0

            while (asyncio.get_event_loop().time() - start_time) < 10:
                try:
                    data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    message_count += 1

                    if "PINGPONG" not in data and "SUBSCRIBE SUCCESS" not in data:
                        if data.startswith("0|H0IF1000"):
                            index_count += 1
                            print(f" 지수 데이터: {data[:80]}...")
                        elif data.startswith("0|H0STCNT0"):
                            trade_count += 1
                            print(f" 체결 데이터: {data[:80]}...")
                        elif data.startswith("0|H0GSCNT0"):
                            program_count += 1
                            print(f" 프로그램매매: {data[:80]}...")

                        # 메시지 처리
                        ws_client.handle_message(data)

                        # 5개 의미있는 메시지 받으면 충분
                        if (index_count + trade_count + program_count) >= 5:
                            break

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f" 데이터 수신 중 오류: {e}")
                    break

            print("-" * 60)
            print(" 실시간 데이터 수신 완료!")
            print(f"    총 메시지: {message_count}개")
            print(f"    지수 데이터: {index_count}개")
            print(f"    체결 데이터: {trade_count}개")
            print(f"    프로그램매매: {program_count}개")

            # 저장된 데이터 확인
            print("\n 저장된 데이터 현황:")
            print(f"    지수 데이터: {len(ws_client.latest_index)}개 지수")
            for index_name in ws_client.latest_index:
                print(f"      - {index_name}")

            print(f"    체결 데이터: {len(ws_client.latest_trade)}개 종목")
            for stock_code in ws_client.latest_trade:
                if ws_client.latest_trade[stock_code]:
                    print(f"      - {stock_code}: 최신 체결 데이터 저장됨")

            print(f"    프로그램매매: {len(ws_client.latest_program_trading)}개 종목")
            for stock_code in ws_client.latest_program_trading:
                print(f"      - {stock_code}: 프로그램매매 데이터 저장됨")

    except Exception as e:
        print(f" 오류 발생: {e}")
        import traceback

        traceback.print_exc()


def main():
    """메인 함수"""
    print(" pykis 향상된 웹소켓 기능 예제")
    print("새로 추가된 기능들을 시연합니다:")
    print("- 실시간 지수 구독 (코스피, 코스닥, 코스피200)")
    print("- 실시간 프로그램매매 구독")
    print("- 향상된 데이터 처리 및 저장")
    print()

    # 비동기 함수 실행
    asyncio.run(enhanced_websocket_example())

    print("\n 예제 실행 완료!")
    print("더 많은 예제는 examples/ 디렉토리를 확인하세요.")


if __name__ == "__main__":
    import json  # JSON 처리를 위해 필요

    main()
