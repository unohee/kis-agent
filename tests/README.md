# PyKIS 테스트 가이드

이 디렉토리는 PyKIS 라이브러리의 모든 테스트를 포함합니다.

## 📁 디렉토리 구조

```
tests/
├── unit/                    # 단위 테스트
│   ├── test_agent.py        # Agent 클래스 테스트 (업데이트됨)
│   ├── test_stock_api.py    # StockAPI 클래스 테스트 (확장됨)
│   ├── test_client.py       # KISClient 클래스 테스트
│   ├── test_auth.py         # 인증 모듈 테스트
│   └── test_config.py       # 설정 모듈 테스트
├── integration/             # 통합 테스트
│   ├── test_agent_comprehensive.py  # Agent 종합 테스트 (신규)
│   ├── test_account.py      # 계좌 API 테스트
│   ├── test_api.py          # API 호출 테스트
│   ├── test_program_trade.py # 프로그램매매 테스트
│   └── test_stock_market.py # 주식시장 테스트
└── conftest.py              # pytest 설정
```

##  테스트 실행 방법

### 전체 테스트 실행
```bash
# pytest 사용 (권장)
pytest tests/ -v

# unittest 사용
python -m unittest discover tests/
```

### 특정 테스트 파일 실행
```bash
# Agent 종합 테스트 (신규)
pytest tests/integration/test_agent_comprehensive.py -v

# Agent 단위 테스트 (업데이트됨)
pytest tests/unit/test_agent.py -v

# StockAPI 단위 테스트 (확장됨)
pytest tests/unit/test_stock_api.py -v
```

### 테스트 카테고리별 실행
```bash
# 단위 테스트만 실행
pytest tests/unit/ -v

# 통합 테스트만 실행
pytest tests/integration/ -v

# 특정 클래스의 테스트만 실행
pytest tests/integration/test_agent_comprehensive.py::TestStockBasicInfo -v

# 특정 테스트 메서드만 실행
pytest tests/unit/test_agent.py::TestAgent::test_get_stock_price -v
```

### 마커를 사용한 테스트 실행
```bash
# 파라미터화된 테스트 실행
pytest tests/integration/test_agent_comprehensive.py -k "parametrize" -v

# 성능 테스트만 실행
pytest tests/integration/test_agent_comprehensive.py::TestPerformance -v
```

##  주요 업데이트 사항

###  업데이트된 파일들

1. **tests/unit/test_agent.py** - Agent facade 패턴에 맞게 수정
   - `get_program_trade_summary` → `get_program_trade_by_stock`
   - `get_orderbook` → `agent.stock_api.get_orderbook`
   - `get_stock_investor` → `agent.stock_api.get_stock_investor`
   - `get_volume_rank` → `get_volume_power`
   - `get_price_rank` → `get_top_gainers`
   - 추가 메서드들: `get_member`, `get_member_transaction`, `fetch_minute_data`, `get_condition_stocks`

2. **tests/unit/test_stock_api.py** - 포괄적으로 확장
   - 기존 2개 메서드에서 10개 메서드로 확장
   - DataFrame 반환 타입 처리 추가
   - 상세한 필드 검증 추가

3. **tests/unit/test_client.py** - 추가 API 테스트
   - 프로그램매매 API 테스트 추가
   - 시가총액 순위 API 테스트 추가

4. **tests/integration/test_agent_comprehensive.py** - 신규 생성
   - Jupyter notebook을 pytest 형식으로 변환
   - 9개 테스트 클래스, 30+ 테스트 메서드
   - 현재 Agent facade 패턴에 완전히 맞춤

##  테스트 환경 설정

### 필수 환경 변수
테스트 실행 전에 다음 환경 변수들이 설정되어 있어야 합니다:

```bash
# .env 파일 또는 시스템 환경 변수
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
KIS_ACCOUNT_NO=your_account_number
KIS_ACCOUNT_CODE=01
```

### 의존성 설치
```bash
pip install pytest pandas
# 또는 requirements.txt가 있다면
pip install -r requirements.txt
```

##  테스트 커버리지

### Agent facade 패턴 검증 완료
-  주식 기본 정보 (현재가, 일봉, 분봉, 거래원)
-  프로그램 매매 (종목별, 시간별, 일별, 시장 전체)
-  회원사 및 거래 정보
-  계좌 관련 (잔고 조회)
-  추가 주식 정보 (호가, 기본정보, 순위)
-  투자자별 매매동향
-  조건검색
-  차트 데이터 (분봉 수집, DB 처리)
-  유틸리티 (휴장일, 거래원 분류)
-  시장 정보
-  성능 테스트

### 테스트 통계
- **단위 테스트**: 25+ 메서드
- **통합 테스트**: 35+ 메서드
- **총 테스트**: 60+ 메서드

##  테스트 실행 예시

```bash
# 빠른 테스트 (기본 기능만)
pytest tests/unit/test_agent.py::TestAgent::test_get_stock_price -v

# 종합 테스트 (모든 기능)
pytest tests/integration/test_agent_comprehensive.py -v

# 성능 테스트
pytest tests/integration/test_agent_comprehensive.py::TestPerformance -v

# 특정 종목으로 테스트
pytest tests/integration/test_agent_comprehensive.py -k "different_stocks" -v
```

##  주의사항

1. **실제 API 호출**: 대부분의 테스트는 실제 한국투자증권 API를 호출합니다
2. **계좌 정보**: 계좌 관련 테스트는 실제 계좌 정보가 필요합니다
3. **API 제한**: 과도한 API 호출을 피하기 위해 rate limiting이 적용됩니다
4. **시장 시간**: 일부 테스트는 시장 운영 시간에 따라 결과가 달라질 수 있습니다

## 🐛 문제 해결

### 자주 발생하는 오류
- **토큰 오류**: 환경 변수 설정 확인
- **API 오류**: 네트워크 연결 및 API 키 유효성 확인
- **계좌 오류**: 계좌 번호 및 계좌 코드 확인
- **DB 오류**: SQLite 파일 권한 확인

### 디버그 모드 실행
```bash
pytest tests/ -v -s --tb=short
``` 