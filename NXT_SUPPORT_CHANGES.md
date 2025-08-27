# NXT 지원을 위한 변경사항

## 개요
PyKIS에서 NXT (Next Market) 지원을 위해 `FID_COND_MRKT_DIV_CODE` 값을 "J"에서 "UN"으로 변경했습니다.

## 변경된 파일들

### 1. Core 모듈
- `pykis/core/client.py`: 예제 코드에서 'J' → 'UN' 변경

### 2. Stock 모듈들  
- `pykis/stock/api.py`: 모든 종목 조회 API에서 'J' → 'UN' 변경
- `pykis/stock/investor_api.py`: 투자자별 매매 정보 API 'J' → 'UN' 변경  
- `pykis/stock/price_api.py`: 시세 조회 API 'J' → 'UN' 변경
- `pykis/stock/market_api.py`: 시장 정보 API 'J' → 'UN' 변경
- `pykis/stock/condition.py`: 조건 검색 API 'J' → 'UN' 변경

### 3. Program 모듈
- `pykis/program/trade.py`: 프로그램 매매 정보 API 'J' → 'UN' 변경
  - 주석도 업데이트: "J: 주식" → "UN: 통합장 (KOSPI+KOSDAQ+NXT)"

### 4. 테스트 파일들
- `tests/unit/test_program_trade.py`: 테스트 기댓값 'J' → 'UN' 변경  
- `tests/unit/test_client.py`: 모든 테스트에서 'J' → 'UN' 변경

## 변경 사유

### FID_COND_MRKT_DIV_CODE 값의 의미:
- **'J'**: KOSPI/KOSDAQ만 지원 (기존)
- **'UN'**: 통합장 - KOSPI + KOSDAQ + NXT 지원 (신규)

### NXT 시장이란?
- Next Market: 혁신 기업 대상 신설 시장
- 벤처기업, 스타트업 등이 상장하는 새로운 거래소
- 기존 KOSPI/KOSDAQ과 별도 운영되는 시장

## 테스트 결과

모든 변경사항이 테스트를 통과했습니다:
- `test_program_trade.py`: 10개 테스트 모두 통과 ✅
- 코드 변경으로 인한 기능 오류 없음 확인

## 호환성

이 변경은 **하위 호환성을 유지**합니다:
- 기존 KOSPI/KOSDAQ 종목은 동일하게 작동
- NXT 시장 종목도 추가로 지원
- API 응답 형식 변경 없음

## 영향받는 기능

다음 기능들이 이제 NXT 시장도 지원합니다:
1. 종목 현재가 조회
2. 일별/분봉 시세 조회  
3. 호가 정보 조회
4. 투자자별 매매 동향
5. 거래원 정보
6. 프로그램 매매 정보
7. 조건 검색 결과
8. 시장 순위 정보

## 사용법

변경 후에도 사용법은 동일합니다:

```python
from pykis import PyKIS

# 기존 방식 그대로 사용 가능
client = PyKIS()

# KOSPI, KOSDAQ, NXT 종목 모두 조회 가능
price = client.get_stock_price("005930")  # 삼성전자 (KOSPI)
price = client.get_stock_price("035720")  # 카카오 (KOSDAQ)  
price = client.get_stock_price("NXT종목코드")  # NXT 종목도 지원
```

## 버전 정보
- 브랜치: `feat/nxt-support`
- 변경 파일 수: 9개
- 테스트 파일 수: 2개
- 총 변경된 FID_COND_MRKT_DIV_CODE 항목: 29개