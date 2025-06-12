# Changelog

모든 주요 변경사항이 이 파일에 기록됩니다.

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