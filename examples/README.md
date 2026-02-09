# PyKIS 예제 모음

이 폴더에는 PyKIS 라이브러리의 다양한 기능을 시연하는 예제 파일들이 포함되어 있습니다.

##  목차

- [ 종합 테스트](#-종합-테스트)
- [ 웹소켓 실시간 데이터](#-웹소켓-실시간-데이터)
- [ 주식 시세 분석](#-주식-시세-분석)
- [ 프로그램 매매](#-프로그램-매매)
- [ 선물옵션](#-선물옵션)
- [ 특화 기능](#-특화-기능)

---

##  종합 테스트

### `pykis.ipynb`
**핵심 기능 종합 테스트 노트북**
- PyKIS의 모든 주요 기능을 한 번에 테스트
- API 연결, 주식 시세, 계좌 조회, 프로그램 매매 등
- 새로 시작하는 사용자에게 권장하는 첫 번째 예제

```python
# 노트북에서 실행
# 각 셀을 순서대로 실행하여 모든 기능 확인
```

---

##  웹소켓 실시간 데이터

### `websocket_enhanced_example.py` ⭐ **신규 추가**
**향상된 웹소켓 실시간 데이터 수신 예제**
- 실시간 지수 구독 (코스피, 코스닥, 코스피200)
- 실시간 프로그램매매 구독
- 실시간 호가 구독 (선택적)
- 새로운 웹소켓 기능들의 완전한 시연

```bash
python examples/websocket_enhanced_example.py
```

### `StockMonitor_example.py`
**실시간 주식 모니터링 시스템**
- 여러 종목 동시 모니터링
- 실시간 체결 데이터 수신 및 분석
- 기술적 지표 계산 (RSI, MACD)
- 보유 종목 자동 추적

```bash
python examples/StockMonitor_example.py
```

---

##  주식 시세 분석

### `daily_index_chart_price_example.py`
**업종별 시세 데이터 조회 예제**
- 국내주식 업종기간별 시세 조회
- 종합, 대형주, 중형주, 소형주, KOSPI, KOSDAQ 등
- 일봉, 주봉, 월봉, 년봉 데이터 수집

```bash
python examples/daily_index_chart_price_example.py
```

### `list_interest_groups.py`
**관심 종목 그룹 관리 예제**
- 사용자 정의 관심 종목 그룹 조회
- 그룹별 종목 리스트 확인
- 종목 추가/삭제 기능

```bash
python examples/list_interest_groups.py
```

---

##  프로그램 매매

### `program_trade_analysis.py`
**프로그램 매매 분석 예제**
- 종목별 프로그램 매매 추이 분석
- 시간별, 일별 프로그램 매매 데이터
- 기관/외국인 매매 동향 분석
- 매매 강도 및 패턴 분석

```bash
python examples/program_trade_analysis.py
```

---

##  선물옵션

### `future_option_price_example.py`
**선물옵션 시세 조회 예제**
- 지수선물, 지수옵션 시세 조회
- 주식선물, 주식옵션 시세 조회
- 실시간 선물옵션 가격 모니터링

```bash
python examples/future_option_price_example.py
```

### `calculate_basis.py`
**KOSPI200 베이시스 계산 예제**
- KOSPI200 현물과 선물 간 베이시스 계산
- 만기월 자동 계산 기능
- 베이시스 추이 분석

```bash
python examples/calculate_basis.py
```

---

##  특화 기능

### `run.py`
**고급 트레이딩 시스템 예제**
- 복합적인 투자 전략 구현
- 실시간 데이터 기반 자동 매매
- 리스크 관리 및 포지션 관리
- 상세한 로깅 및 성과 분석

```bash
python examples/run.py
```

---

##  시작하기

### 1. 환경 설정
```bash
# 가상환경 활성화
source ~/RTX_ENV/bin/activate

# 필요한 패키지 설치 (이미 설치되어 있다면 생략)
pip install -r requirements.txt
```

### 2. 설정 파일 준비
```bash
# .env 파일 생성 (프로젝트 루트에)
cp .env.example .env
# .env 파일에 실제 API 키와 계좌 정보 입력
```

### 3. 예제 실행
```bash
# 종합 테스트부터 시작 (권장)
jupyter notebook examples/pykis.ipynb

# 또는 개별 예제 실행
python examples/websocket_enhanced_example.py
```

---

##  예제별 난이도

| 예제 | 난이도 | 설명 |
|------|--------|------|
| `pykis.ipynb` | ⭐ 초급 | 기본 기능 전체 학습 |
| `daily_index_chart_price_example.py` | ⭐ 초급 | 단순 시세 조회 |
| `list_interest_groups.py` | ⭐ 초급 | 관심종목 관리 |
| `future_option_price_example.py` | ⭐⭐ 중급 | 선물옵션 이해 필요 |
| `calculate_basis.py` | ⭐⭐ 중급 | 베이시스 개념 이해 |
| `websocket_enhanced_example.py` | ⭐⭐⭐ 고급 | 실시간 데이터 처리 |
| `program_trade_analysis.py` | ⭐⭐⭐ 고급 | 프로그램매매 분석 |
| `StockMonitor_example.py` | ⭐⭐⭐⭐ 전문가 | 실시간 모니터링 |
| `run.py` | ⭐⭐⭐⭐⭐ 마스터 | 고급 트레이딩 시스템 |

---

##  문제 해결

### 일반적인 오류
1. **인증 오류**: `.env` 파일의 API 키와 계좌 정보 확인
2. **네트워크 오류**: 인터넷 연결 및 한국투자증권 API 서버 상태 확인
3. **권한 오류**: API 권한 설정 및 계좌 상태 확인

### 도움이 필요한 경우
- 프로젝트 루트의 `README.md` 참조
- `PYKIS_API_METHODS.md`에서 상세 API 문서 확인
- GitHub Issues에 문제 보고

---

##  추가 자료

- **API 문서**: `../PYKIS_API_METHODS.md`
- **변경사항**: `../CHANGELOG.md`
- **설정 가이드**: `../README.md`
- **Postman 컬렉션**: `../postman_collections/`

---

** 팁**: 새로운 기능을 사용해보려면 `websocket_enhanced_example.py`부터 시작하세요! 