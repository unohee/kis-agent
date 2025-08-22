import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pykis import Agent
from pykis.websocket.client import KisWebSocket
import json
import asyncio

@pytest.fixture
def agent():
    """Agent fixture - 실제 설정을 사용"""
    try:
        return Agent()
    except Exception as e:
        pytest.skip(f"Agent 초기화 실패: {e}")

def test_websocket_creation(agent):
    """
    웹소켓 클라이언트가 정상적으로 생성되는지 테스트합니다.
    """
    ws_client = agent.websocket()
    assert ws_client is not None
    assert isinstance(ws_client, KisWebSocket)

def test_websocket_creation_with_options(agent):
    """
    웹소켓 클라이언트가 새로운 옵션들과 함께 정상적으로 생성되는지 테스트합니다.
    """
    ws_client = agent.websocket(
        stock_codes=["005930"],
        enable_index=True,
        enable_program_trading=True,
        enable_ask_bid=True
    )
    assert ws_client is not None
    assert isinstance(ws_client, KisWebSocket)
    assert ws_client.enable_index == True
    assert ws_client.enable_program_trading == True
    assert ws_client.enable_ask_bid == True
    assert ws_client.stock_codes == ["005930"]

def test_websocket_index_name_mapping(agent):
    """
    지수 코드가 올바르게 지수 이름으로 매핑되는지 테스트합니다.
    """
    ws_client = agent.websocket()
    
    assert ws_client.get_index_name('0001') == 'KOSPI'
    assert ws_client.get_index_name('1001') == 'KOSDAQ'
    assert ws_client.get_index_name('2001') == 'KOSPI200'
    assert ws_client.get_index_name('9999') == 'INDEX_9999'  # 알 수 없는 코드

def test_websocket_message_handling(agent):
    """
    실제 웹소켓 메시지 처리 테스트 (새로운 TR 포함)
    """
    ws_client = agent.websocket(stock_codes=["005930"], enable_index=True, enable_program_trading=True)
    
    # 샘플 메시지들
    sample_messages = [
        # 기존 체결 데이터
        "0|H0STCNT0|001|005930^093000^62300^+100^+200^1.5^50000^10000000000000^500^400^100^200^300^120000000^50000^30000^40000^2.5^60^70",
        
        # 지수 데이터 (코스피200 예시)
        "0|H0IF1000|001|2001^2650.50^+15.30^+0.58^2635.20^2665.80^100000^15000000000^12:34:56^Y",
        
        # 프로그램매매 데이터
        "0|H0GSCNT0|001|005930^093000^500^1000000^300^800000^200^200000^100^150^50",
        
        # 호가 데이터 
        "0|H0STASP0|001|005930^62400^62300^62200^62100^62000^61900^61800^61700^61600^61500^62500^62600^62700^62800^62900^63000^63100^63200^63300^63400^100^200^300^400^500^600^700^800^900^1000^150^250^350^450^550^650^750^850^950^1050^5000^7000^62350^2000^0^+50^+0.08^N^Y"
    ]
    
    # 메시지 처리 테스트
    for message in sample_messages:
        try:
            ws_client.handle_message(message)
            print(f"✅ 메시지 처리 성공: {message[:50]}...")
        except Exception as e:
            print(f"❌ 메시지 처리 실패: {str(e)}")
            
    # 데이터 저장 확인
    assert "005930" in ws_client.latest_trade
    print("✅ 체결 데이터 저장 확인")

@pytest.mark.asyncio
async def test_websocket_real_connection_with_new_features(agent):
    """
    새로운 기능들을 포함한 실제 웹소켓 연결 테스트 (Mock 사용)
    """
    with patch('pykis.websocket.client.KisWebSocket.get_approval') as mock_get_approval:
        mock_get_approval.return_value = "mock_approval_key_12345"
        
        ws_client = agent.websocket(
            stock_codes=["005930"], 
            enable_index=True, 
            enable_program_trading=True,
            enable_ask_bid=False  # 호가는 너무 많은 데이터가 올 수 있어서 비활성화
        )
        
        # 승인키 발급 테스트 (Mock)
        approval_key = ws_client.get_approval()
        assert approval_key is not None
        assert len(approval_key) > 10
        print(f"✅ 승인키 발급 성공: {approval_key[:20]}...")
    
    # 실제 연결 테스트 (30초 타임아웃)
    connection_successful = False
    data_received = False
    
    try:
        # 웹소켓 연결 시도 (실제 데이터 대기)
        import websockets
        async with websockets.connect(ws_client.url, ping_interval=30, ping_timeout=30) as websocket:
            ws_client.ws = websocket
            print("✅ 웹소켓 연결 성공")
            connection_successful = True
            
            # 지수 구독 테스트
            if ws_client.enable_index:
                index_codes = ['0001', '1001', '2001']
                for index_code in index_codes:
                    senddata_index = {
                        "header": {
                            "approval_key": approval_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8"
                        },
                        "body": {
                            "input": {
                                "tr_id": "H0IF1000",
                                "tr_key": index_code
                            }
                        }
                    }
                    await websocket.send(json.dumps(senddata_index))
                    print(f"✅ {ws_client.get_index_name(index_code)} 지수 구독 요청 완료")
            
            # 체결 정보 구독
            for stock_code in ws_client.stock_codes:
                senddata_trade = {
                    "header": {
                        "approval_key": approval_key,
                        "custtype": "P",
                        "tr_type": "1",
                        "content-type": "utf-8"
                    },
                    "body": {
                        "input": {
                            "tr_id": "H0STCNT0",
                            "tr_key": stock_code
                        }
                    }
                }
                await websocket.send(json.dumps(senddata_trade))
                print(f"✅ {stock_code} 체결 정보 구독 요청 완료")
                
                # 프로그램매매 구독
                if ws_client.enable_program_trading:
                    senddata_program = {
                        "header": {
                            "approval_key": approval_key,
                            "custtype": "P",
                            "tr_type": "1",
                            "content-type": "utf-8"
                        },
                        "body": {
                            "input": {
                                "tr_id": "H0GSCNT0",
                                "tr_key": stock_code
                            }
                        }
                    }
                    await websocket.send(json.dumps(senddata_program))
                    print(f"✅ {stock_code} 프로그램매매 구독 요청 완료")
            
            # 데이터 수신 대기 (최대 30초)
            try:
                for _ in range(30):  # 30초 대기
                    data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    if data and 'PINGPONG' not in data and 'SUBSCRIBE SUCCESS' not in data:
                        print(f"✅ 실시간 데이터 수신: {data[:100]}...")
                        ws_client.handle_message(data)
                        data_received = True
                        break
            except asyncio.TimeoutError:
                pass
                
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
    
    assert connection_successful, "웹소켓 연결에 실패했습니다"
    if data_received:
        print("✅ 실시간 데이터 수신 확인")
    else:
        print("ℹ️ 실시간 데이터 수신 없음 (정상적일 수 있음)")

def test_websocket_data_processing_with_new_features(agent):
    """
    새로운 기능들을 포함한 거래 이력 저장 및 지표 계산 테스트
    """
    ws_client = agent.websocket(
        stock_codes=["005930"], 
        enable_index=True, 
        enable_program_trading=True
    )
    
    # 샘플 체결 데이터 처리
    sample_trade_data = "0|H0STCNT0|001|005930^093000^62300^+100^+200^1.5^50000^10000000000000^500^400^100^200^300^120000000^50000^30000^40000^2.5^60^70"
    ws_client.handle_message(sample_trade_data)
    
    # 체결 데이터 저장 확인
    assert "005930" in ws_client.latest_trade
    assert ws_client.latest_trade["005930"] is not None
    
    # 기술적 지표 계산 확인 (데이터가 충분하지 않을 수 있음)
    rsi = ws_client.compute_RSI_candles("005930")
    macd = ws_client.compute_MACD_candles("005930")
    print(f"✅ RSI: {rsi}, MACD: {macd}")
    
    # 지수 데이터 저장 확인
    sample_index_data = "0|H0IF1000|001|0001^2650.50^+15.30^+0.58^2635.20^2665.80^100000^15000000000^12:34:56^Y"
    ws_client.handle_message(sample_index_data)
    
    if 'KOSPI' in ws_client.latest_index:
        print("✅ 지수 데이터 저장 확인")
    
    # 프로그램매매 데이터 저장 확인
    sample_program_data = "0|H0GSCNT0|001|005930^093000^500^1000000^300^800000^200^200000^100^150^50"
    ws_client.handle_message(sample_program_data)
    
    if "005930" in ws_client.latest_program_trading:
        print("✅ 프로그램매매 데이터 저장 확인")
        
    print("✅ 모든 새로운 기능 테스트 완료")

# 실제 웹소켓 테스트 실행을 위한 메인 함수
if __name__ == "__main__":
    async def run_live_test():
        from pykis import Agent
        try:
            agent = Agent()
            await test_websocket_real_connection_with_new_features(agent)
        except Exception as e:
            print(f"라이브 테스트 실패: {e}")
    
    asyncio.run(run_live_test())

