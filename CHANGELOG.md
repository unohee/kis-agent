# Changelog

모든 주요 변경사항이 이 파일에 기록됩니다.

## [0.1.9] - 2025-06-29

### 변경됨
- **인증 방식 변경**: `kis_devlp.yaml` 파일을 사용하던 방식에서 `.env` 파일을 사용하는 방식으로 변경되었습니다.
  - `python-dotenv` 라이브러리를 사용하여 `.env` 파일에서 API 키 및 계좌 정보를 로드합니다.
  - 더 이상 `pyyaml` 라이브러리에 의존하지 않습니다.

### 추가됨
- **`.env.example` 파일**: 사용자가 설정을 쉽게 구성할 수 있도록 `.env.example` 파일을 추가했습니다.
- **예외 처리**: `.env` 파일이 없을 경우 `FileNotFoundError`를 발생시켜 사용자에게 명확한 피드백을 제공합니다.

### 제거됨
- **YAML 관련 코드**: `pykis/core/config.py` 및 테스트 코드에서 YAML 관련 로직을 모두 제거했습니다.
- **`load_account_info` 함수**: `pykis/stock/api.py`에서 더 이상 사용되지 않는 `load_account_info` 함수를 제거했습니다.

## [0.1.8] - 2025-06-29

### 제거됨
- `pykis/program/api.py`: 더 이상 사용되지 않는 deprecated 파일 제거.

## [0.1.7] - 2025-06-29

### 수정됨
- **API 메서드 통합 및 리팩토링**
  - 각 API 엔드포인트당 하나의 메서드만 존재하도록 중복 메서드 통합 및 제거.
  - `pykis/stock/program_trade.py`와 같이 deprecated된 모듈 삭제.
  - `pykis/stock/data.py`와 같이 중복된 기능을 가진 모듈 삭제.
- **테스트 코드 수정**
  - 리팩토링으로 인해 실패하던 테스트 코드 수정.
  - 삭제된 모듈을 참조하는 테스트 파일(`tests/unit/test_stock_data.py`, `tests/unit/test_stock_market.py`) 삭제.
- **`API_ENDPOINTS` 정리**
  - `pykis/core/client.py`의 `API_ENDPOINTS`에서 별칭(alias)들을 제거하여 명확성 및 유지보수성 향상.
- **Facade 패턴 강화**
  - `Agent` 클래스가 모든 하위 API 모듈을 올바르게 호출하도록 수정.
  - `pykis/__init__.py`를 정리하여 `Agent`를 통해 모든 기능에 접근하는 Facade 패턴을 명확히 함.

### 개선됨
- **코드 일관성 및 가독성 향상**
  - 중복 코드 제거 및 API ���출 방식 표준화.
- **안정성 향상**
  - 순환 참조 문제 해결 및 테스트 코드 수정으로 라이브러리 안정성 강화.

## [0.1.6] - 2025-06-28

### 수정됨
- **테스트 코드 대규모 리팩토링 및 버그 수정**
  - `tests/test_agent_usage.py`: `get_market_rankings()` -> `get_price_rank()`, `get_stock_info()` -> `get_stock_opinion()`으로 메서드명 변경. DataFrame의 진리값 평가 오류 수정.
  - `tests/integration/test_agent_comprehensive.py`: `validate_api_response` 함수가 `output1`, `output2` 키를 처리하도록 수정하여 분봉/차트 테스트 실패 해결.
  - `tests/unit/test_auth.py`: `read_token` 및 `save_token` 함수에 대한 잘못된 mock 패치 수정.
  - `tests/unit/test_client.py`: `test_make_request_daily_price`의 `tr_id` 수정. `test_refresh_token`에 `requests.post` mock 추가.
  - `tests/unit/test_program_trade.py`: `datetime` import 누락 수정 및 예외 ��리 테스트에 `pytest.raises` 추가.

- **`pykis/core/agent.py` 리팩토링**
  - `StockMarketAPI`를 `Agent` 클래스에 추가하고 `__getattr__`을 통해 메서드를 위임하도록 수정.

### 개선됨
- **테스트 커버리지 및 안정성 향상**
  - 다수의 테스트 실패를 수정하여 테스트 스위트의 안정성 확보.
  - mock을 사용하여 단위 테스트와 외부 API 호출을 분리.

## [0.1.5] - 2025-06-26

### 수정됨
- **datetime import 충돌 해결**
  - `pykis/core/agent.py`: `import datetime`와 `from datetime import timedelta` 중복 import 문제 해결
  - `pykis/stock/api.py`: `import datetime`를 `from datetime import datetime`로 변경, `datetime.datetime.now()` → `datetime.now()` 수정
  - `pykis/stock/data.py`: 누락된 datetime import문 추가
  - 모든 파일에서 명시적인 import 방식(`from datetime import datetime, timedelta`) 사용으로 통일

- **분봉 API 매개변수 수정 및 재귀적 분봉 수집 기능 복구**
  - 주식당일분봉조회 API의 올바른 매개변수 적용: `FID_ETC_CLS_CODE=""` 추가, `FID_COND_SCR_DIV_CODE` 제거
  - `get_minute_price` 메서드의 API_ENDPOINTS 키를 `MINUTE_CHART` → `MINUTE_PRICE`로 수정
  - `fetch_minute_data` 메서드 데이터 처리 로직 수정: `output` → `output2` 필드 사용
  - 시간 형식을 "0900" → "090000" (HHMMSS)로 수정
  - API 응답 성공 여부 확인 로직 추가 (`rt_cd == '0'`)
  - 재귀적 분봉 수집 기능 완전 복구: 8개 시간대별로 240건 분봉 데이터 수집 성공

- 조건검색 API 통일 및 개선
  - 모든 조건검색 호출이 `condition.py`의 정확한 방식(`tr_id="HHKST03900400"`) 사용하도록 통일
  - `pykis/stock/api.py`의 `get_condition_stocks` 메서드를 올바른 `tr_id`로 수정
  - `pykis/core/agent.py`의 `get_condition_stocks_dict` 함수에서 직접 `ConditionAPI` 사용
  - `examples/list_interest_groups.py`에서 Agent 통합 방식으로 변경
  - 모든 호출 지점에서 `user_id="unohee"` 매개변수 통일 사용
  - `rt_cd='1'` ("조회가 계속 됩니다") 응답을 정상 처리하도록 개선

- 휴장일 관련 기능 추가 및 개선
  - `StockAPI` 클래스에 `get_holiday_info()` 및 `is_holiday()` 메서드 추가
  - Agent 클래스에 휴장일 기능 통합: 직접 API 접근(`get_holiday_info`) + 편의 메서드(`is_holiday`)
  - 복잡한 캐싱 로직 제거하고 API 직접 호출 방식으로 간소화
  - 기준일 계산 로직 개선: 입력 날짜가 포함된 월의 첫 번째 날 사용
  - 최대 재시도 10회 및 상세 디버그 로깅 추가

### 개선됨
- **분봉 데이터 수집 기능 완전 복구**
  - `fetch_minute_data` 메서드가 8개 시간대(09:00~15:30)에서 재귀적으로 분봉 데이터 수집
  - SQLite DB 캐싱 기능 포함으로 효율적인 데이터 관리
  - 총 240건의 분봉 데이터 수집 성공 확인
  - 컬럼: `stck_bsop_date`, `stck_cntg_hour`, `stck_prpr`, `stck_oprc`, `stck_hgpr`, `stck_lwpr`, `cntg_vol`, `acml_tr_pbmn`, `code`, `date`

- Facade 패턴 일관성 강화
  - 조건검색만 `ConditionAPI`를 직접 사용하던 불일치 해결
  - Agent 클래스의 `get_condition_stocks` 메서드에 매개변수(`user_id`, `seq`, `tr_cont`) 추가
  - 모든 기능을 Agent를 통해 접근하도록 통일하면서 내부적으로는 적절한 API 클래스 사용
  - 사용자는 Agent만 사용하고 내부 구현은 캡슐화

- 테스트 노트북 개선
  - `examples/pykis.ipynb`에 모듈 완전 재로드 기능 추가
  - 휴장일 기능 테스트를 직접 API 호출 방식으로 대체 (모듈 캐시 문제 회피)
  - 조건검색 테스트에서 올바른 매개변수 사용 확인
  - 거래원 분류 테스트 정상 작동 확인
  - 아키텍처 통일 개선사항을 요약에 명시적으로 표시

### 추가됨
- 휴장일 API 엔드포인트 지원
  - `/uapi/domestic-stock/v1/quotations/chk-holiday` 엔드포인트 구현
  - `tr_id="CTCA0903R"`을 사용한 휴장일 정보 조회
  - 날짜별 개장여부(`opnd_yn`) 확인 기능
  - 에러 처리 및 재시도 로직 포함

## [0.1.4] - 2024-06-22

### 수정됨
- 체결강도 관련 API 통합 및 정리
  - `get_volume_power` 메서드 중복 제거 및 통합
  - 올바른 API 엔드포인트 및 TR 코드 적용 (`/uapi/domestic-stock/v1/ranking/volume-power`, `FHPST01680000`)
  - 용어 통일: "거래량 파워" → "체결강도"로 변경
  - 거래량 급증도 관련 기능 제거 (존재하지 않는 API)

- 프로그램 매매 API 개선
  - 종목별 프로그램 매매와 시장 전체 프로그램 매매 API 분리
  - `get_program_trade_daily_summary`: 종목별 기능 유지
  - `get_program_trade_market_daily`: 새로운 시장 전체 API 추가
  - 올바른 엔드포인트 적용

- 등락률 순위 API 수정
  - `get_market_fluctuation` 메서드를 올바른 국내주식 등락률 순위 API로 수정
  - 엔드포인트: `/uapi/domestic-stock/v1/ranking/fluctuation`, TR: `FHPST01700000`

- 계좌 API 정리
  - 주문가능금액조회 엔드포인트 수정
  - `client.py`에 `INQUIRE_PSBL_ORDER` 상수 추가
  - 존재하지 않는 `get_total_evaluation` 메서드 제거

### 개선됨
- 분석 로직 독립화
  - `get_pgm_trade` 메서드를 `examples/program_trade_analysis.py`로 분리
  - `ProgramTradeAnalyzer` 클래스로 분석 기능 캡슐화
  - API와 분석 로직의 명확한 분리

- 조건검색 관련 버그 수정
  - `logger` 미정의 오류 수정: `logger` → `logging`으로 변경
  - 무한 재귀 호출 문제 해결: `get_condition_stocks_dict`에서 직접 API 호출하도록 수정

- Strategy 모듈 완전 제거
  - deprecated된 strategy 관련 import 및 메서드 모두 제거
  - `pykis/core/agent.py`에서 strategy 관련 코드 정리
  - `tests/integration/test_strategy.py` 파일 삭제

### 추가됨
- 종합 테스트 노트북 확장
  - 50개 이상의 메서드에 대한 포괄적인 테스트 추가
  - 계좌, 주식, 시장, 프로그램 매매, 조건검색 등 모든 영역 커버
  - 에러 처리 및 경계 조건 테스트 포함
  - 성능 및 캐싱 테스트 추가

### 제거됨
- 중복된 `get_volume_power` 메서드들 제거
- 존재하지 않는 거래량 급증도 API 관련 코드 제거
- Strategy 모듈 및 관련 의존성 완전 제거
- 미사용 및 잘못된 API 메서드들 정리

## [0.1.3] - 2024-06-19

### 변경됨
- ProgramTradeAPI 클래스 중복 제거 및 통합
  - `pykis/program/api.py`, `pykis/program/trade.py`, `pykis/stock/program_trade.py`의 중복 클래스 통합
  - 모든 import를 `pykis.program.trade`로 통일
  - deprecated 파일들에 안내 메시지 추가

### 개선됨
- 메서드명 개선
  - `get_program_trade_summary` → `get_program_trade_by_stock`으로 변경
  - 메서드명이 실제 기능과 일치하도록 수정
- `get_program_trade_by_stock`이 실제 API를 직접 호출하도록 수정
  - 종목별프로그램매매추이(체결) API 직접 호출
  - 날짜 파라미터 지원 추가

### 문서화
- README.md 업데이트
  - 프로그램 매매 관련 메서드 목록 업데이트
  - 사용 예시에 프로그램 매매 관련 예시 추가

## [0.1.2] - 2024-06-16

### 변경됨
- 프로젝트명을 `kis-agent`에서 `pykis`로 변경
- 패키지 구조 개선
  - `src` 디렉토리 제거
  - 메인 모듈을 `pykis`로 변경
- 클래스명 변경
  - `KIS_Agent` → `Agent`
  - `KISClient` → `Client`

## [0.1.1] - 2024-06-15

### 추가됨
- Postman 컬렉션의 모든 엔드포인트 구현
  - 국내주식: 휴장일, 기본정보, 재무제표, 투자의견 등
  - 국내주식: 체결강도 랭킹(거래량 파워) API 구현 및 정상 동작 확인
  - 해외주식: 시세, 뉴스, 권리정보 등
  - 채권: 시세 조회
  - 시장 분석: 거래량/등락률/수익률 순위 등

### 개선됨
- 로깅 시스템 개선
  - 각 API 호출에 대한 상세한 로깅 추가
  - 에러 메시지 한글화
  - 로그 포맷 통일화
- 국내주식 엔드포인트 실제 테스트 결과, 대부분 정상 동작함을 확인 (일부 미지원/폐지 API 및 파라미터 오류 등은 실제 서비스 상태에 따라 다를 수 있음)

### 변경됨
- `market.py` 구조 개선
  - 메서드명 표준화
  - 파라미터 타입 ���트 추가
  - 반환값 타입 명시

### 문서화
- 모든 API 메서드에 상세한 docstring 추가
  - 목적, 파라미터, 반환값 설명
  - 사용 예시 포함
  - 예외 처리 정보 추가

## [0.1.0] - 2025-06-11

### 추가됨
- 한국투자증권 OpenAPI 연동을 위한 기본 모듈 구조 구현
  - `core`: API 클라이언트, 인증, 설정 관리
  - `account`: 계좌 잔고 및 주문 관리
  - `stock`: 주식 시세 및 주문 처리
  - `program`: 프로그램 매매 정보 조회
  - `strategy`: 전략 실행 및 모니터링

### 개선됨
- 모든 모듈 및 클래스에 상세한 docstring 추가
  - 모듈 레벨: 목적, 기능, 의존성, 연관 모듈, 사용 예시
  - 클래스 레벨: 목적, 속성, 사용 예시
  - 메서드 레벨: 목적, 매개변수, 반환값, 주의사항, 사용 예시

### 변경됨
- `program_trade.py`의 메서드명 변경
  - `get_program_trade_detail` → `get_program_trade_period_detail`
  - `get_program_trade_ratio` → `get_pgm_trade`

### 제거됨
- `scripts/convert_yaml_to_env.py`: 사용하지 않는 스크립트 제거

### 보안
- API 키 및 인증 정보를 환경 변수로 관리하도록 변경
- 민감한 정보가 포함된 파일들을 .gitignore에 추가

### 문서화
- 각 모듈의 README.md 파일 추가
- API 사용 ��시 및 설명 추가
- 코드 주석 개선 및 한글화

### 기술적 부채
- `program_trade.py`의 주석 처리된 `get_program_trade_summary` 메서드 재구현 필요
- 일부 API 응답 처리 로직 개선 필요
- 에러 처리 및 재시도 로직 보완 필요

## [0.1.6] - 2025-06-28

### 수정됨
- **테스트 코드 대규모 리팩토링 및 버그 수정**
  - `tests/test_agent_usage.py`: `get_market_rankings()` -> `get_price_rank()`, `get_stock_info()` -> `get_stock_opinion()`으로 메서드명 변경. DataFrame의 진리값 평가 오류 수정.
  - `tests/integration/test_agent_comprehensive.py`: `validate_api_response` 함수가 `output1`, `output2` 키를 처리하도록 수정하여 분봉/차트 테스트 실패 해결.
  - `tests/unit/test_auth.py`: `read_token` 및 `save_token` 함수에 대한 잘못된 mock 패치 수정.
  - `tests/unit/test_client.py`: `test_make_request_daily_price`의 `tr_id` 수정. `test_refresh_token`에 `requests.post` mock 추가.
  - `tests/unit/test_program_trade.py`: `datetime` import 누락 수정 및 예외 ��리 테스트에 `pytest.raises` 추가.

- **`pykis/core/agent.py` 리팩토링**
  - `StockMarketAPI`를 `Agent` 클래스에 추가하고 `__getattr__`을 통해 메서드를 위임하도록 수정.

### 개선됨
- **테스트 커버리지 및 안정성 향상**
  - 다수의 테스트 실패를 수정하여 테스트 스위트의 안정성 확보.
  - mock을 사용하여 단위 테스트와 외부 API 호출을 분리.

## [0.1.5] - 2025-06-26

### 수정됨
- **datetime import 충돌 해결**
  - `pykis/core/agent.py`: `import datetime`와 `from datetime import timedelta` 중복 import 문제 해결
  - `pykis/stock/api.py`: `import datetime`를 `from datetime import datetime`로 변경, `datetime.datetime.now()` → `datetime.now()` 수정
  - `pykis/stock/data.py`: 누락된 datetime import문 추가
  - 모든 파일에서 명시적인 import 방식(`from datetime import datetime, timedelta`) 사용으로 통일

- **분봉 API 매개변수 수정 및 재귀적 분봉 수집 기능 복구**
  - 주식당일분봉조회 API의 올바른 매개변수 적용: `FID_ETC_CLS_CODE=""` 추가, `FID_COND_SCR_DIV_CODE` 제거
  - `get_minute_price` 메서드의 API_ENDPOINTS 키를 `MINUTE_CHART` → `MINUTE_PRICE`로 수정
  - `fetch_minute_data` 메서드 데이터 처리 로직 수정: `output` → `output2` 필드 사용
  - 시간 형식을 "0900" → "090000" (HHMMSS)로 수정
  - API 응답 성공 여부 확인 로직 추가 (`rt_cd == '0'`)
  - 재귀적 분봉 수집 기능 완전 복구: 8개 시간대별로 240건 분봉 데이터 수집 성공

- 조건검색 API 통일 및 개선
  - 모든 조건검색 호출이 `condition.py`의 정확한 방식(`tr_id="HHKST03900400"`) 사용하도록 통일
  - `pykis/stock/api.py`의 `get_condition_stocks` 메서드를 올바른 `tr_id`로 수정
  - `pykis/core/agent.py`의 `get_condition_stocks_dict` 함수에서 직접 `ConditionAPI` 사용
  - `examples/list_interest_groups.py`에서 Agent 통합 방식으로 변경
  - 모든 호출 지점에서 `user_id="unohee"` 매개변수 통일 사용
  - `rt_cd='1'` ("조회가 계속 됩니다") 응답을 정상 처리하도록 개선

- 휴장일 관련 기능 추가 및 개선
  - `StockAPI` 클래스에 `get_holiday_info()` 및 `is_holiday()` 메서드 추가
  - Agent 클래스에 휴장일 기능 통합: 직접 API 접근(`get_holiday_info`) + 편의 메서드(`is_holiday`)
  - 복잡한 캐싱 로직 제거하고 API 직접 호출 방식으로 간소화
  - 기준일 계산 로직 개선: 입력 날짜가 포함된 월의 첫 번째 날 사용
  - 최대 재시도 10회 및 상세 디버그 로깅 추가

### 개선됨
- **분봉 데이터 수집 기능 완전 복구**
  - `fetch_minute_data` 메서드가 8개 시간대(09:00~15:30)에서 재귀적으로 분봉 데이터 수집
  - SQLite DB 캐싱 기능 포함으로 효율적인 데이터 관리
  - 총 240건의 분봉 데이터 수집 성공 확인
  - 컬럼: `stck_bsop_date`, `stck_cntg_hour`, `stck_prpr`, `stck_oprc`, `stck_hgpr`, `stck_lwpr`, `cntg_vol`, `acml_tr_pbmn`, `code`, `date`

- Facade 패턴 일관성 강화
  - 조건검색만 `ConditionAPI`를 직접 사용하던 불일치 해결
  - Agent 클래스의 `get_condition_stocks` 메서드에 매개변수(`user_id`, `seq`, `tr_cont`) 추가
  - 모든 기능을 Agent를 통해 접근하도록 통일하면서 내부적으로는 적절한 API 클래스 사용
  - 사용자는 Agent만 사용하고 내부 구현은 캡슐화

- 테스트 노트북 개선
  - `examples/pykis.ipynb`에 모듈 완전 재로드 기능 추가
  - 휴장일 기능 테스트를 직접 API 호출 방식으로 대체 (모듈 캐시 문제 회피)
  - 조건검색 테스트에서 올바른 매개변수 사용 확인
  - 거래원 분류 테스트 정상 작동 확인
  - 아키텍처 통일 개선사항을 요약에 명시적으로 표시

### 추가됨
- 휴장일 API 엔드포인트 지원
  - `/uapi/domestic-stock/v1/quotations/chk-holiday` 엔드포인트 구현
  - `tr_id="CTCA0903R"`을 사용한 휴장일 정보 조회
  - 날짜별 개장여부(`opnd_yn`) 확인 기능
  - 에러 처리 및 재시도 로직 포함

## [0.1.4] - 2024-06-22

### 수정됨
- 체결강도 관련 API 통합 및 정리
  - `get_volume_power` 메서드 중복 제거 및 통합
  - 올바른 API 엔드포인트 및 TR 코드 적용 (`/uapi/domestic-stock/v1/ranking/volume-power`, `FHPST01680000`)
  - 용어 통일: "거래량 파워" → "체결강도"로 변경
  - 거래량 급증도 관련 기능 제거 (존재하지 않는 API)

- 프로그램 매매 API 개선
  - 종목별 프로그램 매매와 시장 전체 프로그램 매매 API 분리
  - `get_program_trade_daily_summary`: 종목별 기능 유지
  - `get_program_trade_market_daily`: 새로운 시장 전체 API 추가
  - 올바른 엔드포인트 적용

- 등락률 순위 API 수정
  - `get_market_fluctuation` 메서드를 올바른 국내주식 등락률 순위 API로 수정
  - 엔드포인트: `/uapi/domestic-stock/v1/ranking/fluctuation`, TR: `FHPST01700000`

- 계좌 API 정리
  - 주문가능금액조회 엔드포인트 수정
  - `client.py`에 `INQUIRE_PSBL_ORDER` 상수 추가
  - 존재하지 않는 `get_total_evaluation` 메서드 제거

### 개선됨
- 분석 로직 독립화
  - `get_pgm_trade` 메서드를 `examples/program_trade_analysis.py`로 분리
  - `ProgramTradeAnalyzer` 클래스로 분석 기능 캡슐화
  - API와 분석 로직의 명확한 분리

- 조건검색 관련 버그 수정
  - `logger` 미정의 오류 수정: `logger` → `logging`으로 변경
  - 무한 재귀 호출 문제 해결: `get_condition_stocks_dict`에서 직접 API 호출하도록 수정

- Strategy 모듈 완전 제거
  - deprecated된 strategy 관련 import 및 메서드 모두 제거
  - `pykis/core/agent.py`에서 strategy 관련 코드 정리
  - `tests/integration/test_strategy.py` 파일 삭제

### 추가됨
- 종합 테스트 노트북 확장
  - 50개 이상의 메서드에 대한 포괄적인 테스트 추가
  - 계좌, 주식, 시장, 프로그램 매매, 조건검색 등 모든 영역 커버
  - 에러 처리 및 경계 조건 테스트 포함
  - 성능 및 캐싱 테스트 추가

### 제거됨
- 중복된 `get_volume_power` 메서드들 제거
- 존재하지 않는 거래량 급증도 API 관련 코드 제거
- Strategy 모듈 및 관련 의존성 완전 제거
- 미사용 및 잘못된 API 메서드들 정리

## [0.1.3] - 2024-06-19

### 변경됨
- ProgramTradeAPI 클래스 중복 제거 및 통합
  - `pykis/program/api.py`, `pykis/program/trade.py`, `pykis/stock/program_trade.py`의 중복 클래스 통합
  - 모든 import를 `pykis.program.trade`로 통일
  - deprecated 파일들에 안내 메시지 추가

### 개선됨
- 메서드명 개선
  - `get_program_trade_summary` → `get_program_trade_by_stock`으로 변경
  - 메서드명이 실제 기능과 일치하도록 수정
- `get_program_trade_by_stock`이 실제 API를 직접 호출하도록 수정
  - 종목별프로그램매매추이(체결) API 직접 호출
  - 날짜 파라미터 지원 추가

### 문서화
- README.md 업데이트
  - 프로그램 매매 관련 메서드 목록 업데이트
  - 사용 예시에 프로그램 매매 관련 예시 추가

## [0.1.2] - 2024-06-16

### 변경됨
- 프로젝트명을 `kis-agent`에서 `pykis`로 변경
- 패키지 구조 개선
  - `src` 디렉토리 제거
  - 메인 모듈을 `pykis`로 변경
- 클래스명 변경
  - `KIS_Agent` → `Agent`
  - `KISClient` → `Client`

## [0.1.1] - 2024-06-15

### 추가됨
- Postman 컬렉션의 모든 엔드포인트 구현
  - 국내주식: 휴장일, 기본정보, 재무제표, 투자의견 등
  - 국내주식: 체결강도 랭킹(거래량 파워) API 구현 및 정상 동작 확인
  - 해외주식: 시세, 뉴스, 권리정보 등
  - 채권: 시세 조회
  - 시장 분석: 거래량/등락률/수익률 순위 등

### 개선됨
- 로깅 시스템 개선
  - 각 API 호출에 대한 상세한 로깅 추가
  - 에러 메시지 한글화
  - 로그 포맷 통일화
- 국내주식 엔드포인트 실제 테스트 결과, 대부분 정상 동작함을 확인 (일부 미지원/폐지 API 및 파라미터 오류 등은 실제 서비스 상태에 따라 다를 수 있음)

### 변경됨
- `market.py` 구조 개선
  - 메서드명 표준화
  - 파라미터 타입 힌트 추가
  - 반환값 타입 명시

### 문서화
- 모든 API 메서드에 상세한 docstring 추가
  - 목적, 파라미터, 반환값 설명
  - 사용 예시 포함
  - 예외 처리 정보 추가

## [0.1.0] - 2025-06-11

### 추가됨
- 한국투자증권 OpenAPI 연동을 위한 기본 모듈 구조 구현
  - `core`: API 클라이언트, 인증, 설정 관리
  - `account`: 계좌 잔고 및 주문 관리
  - `stock`: 주식 시세 및 주문 처리
  - `program`: 프로그램 매매 정보 조회
  - `strategy`: 전략 실행 및 모니터링

### 개선됨
- 모든 모듈 및 클래스에 상세한 docstring 추가
  - 모듈 레벨: 목적, 기능, 의존성, 연관 모듈, 사용 예시
  - 클래스 레벨: 목적, 속성, 사용 예시
  - 메서드 레벨: 목적, 매개변수, 반환값, 주의사항, 사용 예시

### 변경됨
- `program_trade.py`의 메서드명 변경
  - `get_program_trade_detail` → `get_program_trade_period_detail`
  - `get_program_trade_ratio` → `get_pgm_trade`

### 제거됨
- `scripts/convert_yaml_to_env.py`: 사용하지 않는 스크립트 제거

### 보안
- API 키 및 인증 정보를 환경 변수로 관리하도록 변경
- 민감한 정보가 포함된 파일들을 .gitignore에 추가

### 문서화
- 각 모듈의 README.md 파일 추가
- API 사용 예시 및 설명 추가
- 코드 주석 개선 및 한글화

### 기술적 부채
- `program_trade.py`의 주석 처리된 `get_program_trade_summary` 메서드 재구현 필요
- 일부 API 응답 처리 로직 개선 필요
- 에러 처리 및 재시도 로직 보완 필요  