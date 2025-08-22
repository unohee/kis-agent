#!/usr/bin/env python3
"""
BS 패턴 테스트용 샘플 코드
PyKIS 특화 BS 탐지기 검증용
"""

# BS 패턴 1: API 키 하드코딩
API_KEY = "PSK1234567890ABCDEF1234567890"
app_secret = "SECRET123456789ABCDEF"

# BS 패턴 2: 계좌 정보 노출  
CANO = "12345678"
account_number = "99999999"

# BS 패턴 3: 가짜 성공 메시지
def buy_stock():
    print("✅ 주문이 성공적으로 완료되었습니다!")
    return True  # 성공

def process_order():
    print("🚀 모든 기능이 완벽하게 구현되었습니다!")
    return {"status": "success"}

# BS 패턴 4: Mock 데이터
mock_response = {"price": 50000, "volume": 1000}
dummy_data = [{"code": "005930", "name": "삼성전자"}]
test_data = {"api_response": "fake_data"}

# BS 패턴 5: 위험한 주문
def dangerous_order():
    quantity = 99999  # 위험한 대량 주문
    price = 10000000  # 비현실적 고가
    order_type = "market"  # 테스트용 시장가
    
# BS 패턴 6: eval 사용
def unsafe_code():
    user_input = "print('hello')"
    eval(user_input)  # 위험

# BS 패턴 7: 빈 예외 처리
def bad_exception_handling():
    try:
        result = risky_operation()
    except:
        pass  # 예외 무시
    
    try:
        another_operation()
    except Exception:
        pass

# BS 패턴 8: async without await
async def useless_async():
    result = calculate_something()
    return result

# BS 패턴 9: requests in async
import requests
async def bad_async_request():
    response = requests.get("https://api.example.com")  # 동기 호출
    return response.json()

# TODO: 이 코드는 운영용이므로 완성 필요
def unfinished_function():
    # TODO: 실제 로직 구현
    pass