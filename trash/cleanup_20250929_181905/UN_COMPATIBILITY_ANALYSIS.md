# PyKIS FID_COND_MRKT_DIV_CODE "J" 호환성 분석

##  개요
PyKIS v0.1.22에서 FID_COND_MRKT_DIV_CODE를 "J"에서 "J"으로 변경했으나, 일부 API는 UN 코드를 지원하지 않습니다.

##  UN 지원 가능 API (PyKIS에서 UN 사용)

### 기본 시세 API
- `inquire_price` - 주식현재가 시세: `J:KRX, NX:NXT, UN:통합` 명시 지원
- `inquire_daily_price` - 일별 시세
- `inquire_time_itemchartprice` - 분봉 차트
- 기타 대부분의 기본 시세 조회 API

### 투자자 동향 API  
- `inquire_investor_daily_by_market` - 시장별 투자자 일별 동향
- `frgnmem_trade_trend` - 외국인 매매 동향

##  UN 지원 불가 API (J 또는 NX만 지원)

### 매물대/거래량 분석
- `pbar_tratio` - 매물대/거래비중: **J만 지원**
- `tradprt_byamt` - 체결금액별 매매비중: `J:KRX, NX:NXT`만 지원

### 투자자 분석
- `inquire_investor` - 투자자 정보: `J:KRX, NX:NXT`만 지원
- `inquire_member` - 회원사 정보: `J:KRX, NX:NXT`만 지원

### 실시간 API
- 웹소켓 기반 실시간 API들은 별도 파라미터 체계 사용

##  권장 해결 방안

### 1. 동적 코드 선택
```python
def get_market_code(api_name: str, default: str = "J") -> str:
    """API별 최적 시장 코드 반환"""
    unsupported_apis = {
        'pbar_tratio': 'J',
        'tradprt_byamt': 'J',
        'inquire_investor': 'J',
        'inquire_member': 'J'
    }
    return unsupported_apis.get(api_name, default)
```

### 2. API별 예외 처리
특정 API만 기존 "J" 코드로 롤백:
- 매물대/거래비중 관련 API
- 일부 투자자 정보 API

### 3. 단계적 전환
1. **1단계**: 기본 시세 API는 UN 유지
2. **2단계**: 호환성 문제 API는 J/NX 사용
3. **3단계**: 한투 API 업데이트 시 전체 UN 전환

##  현재 PyKIS 상황
- **v0.1.22**: 전체 API에 UN 적용
- **문제**: 매물대, 거래비중 등 일부 API 오류 발생 가능
- **해결 필요**: 호환성 매트릭스 기반 선별적 적용

##  적용 완료 사항 (v0.1.22)

### 변경된 API
- `investor_api.py`: 모든 API가 J 코드 사용
  - `get_stock_investor()`: UN → J
  - `get_stock_member()`: UN → J  
  - `get_member_transaction()`: UN → J

### 유지된 API  
- `api.py`: 매물대(`get_pbar_tratio`)는 원래부터 J 코드 사용
- `price_api.py`: 기본 시세 API들은 UN 코드 유지 (NXT 지원)
- `market_api.py`: 시장 동향 API들은 UN 코드 유지

### 테스트 결과
- 투자자/거래원 API: J 코드 적용 완료 
- 매물대 API: J 코드 사용 (기존 유지)   
- 기본 시세 API: UN 코드 유지 (NXT 호환) 

##  결론
문제가 되는 API들만 선별적으로 J 코드로 롤백하여 호환성 문제 해결