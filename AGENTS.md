# KIS_AGENT 개발 가이드

## 프로젝트 개요
KIS_AGENT는 한국투자증권 API를 Python으로 쉽게 사용할 수 있도록 래핑한 라이브러리입니다. 본 프로젝트는 pip를 통해 설치하여 사용할 수 있는 형태로 개발되고 있습니다.

## 핵심 컴포넌트
- `KIS_Agent`: 메인 래퍼 클래스
- `KISClient`: API 통신을 담당하는 기본 클라이언트
- `StockAPI`: 주식 관련 API 기능
- `ProgramTradeAPI`: 프로그램 매매 관련 API 기능

## 주요 기능
1. 계좌 잔고 조회
2. 주식 시세 조회
3. 프로그램 매매 정보 조회
4. 조건검색식 종목 조회
5. 실시간 시세 조회

## 개발 환경 설정
1. Python 3.8 이상
2. 가상환경 설정 (venv)
3. credit/kis_devlp.yaml 파일에 API 인증 정보 설정

## 테스트
- 통합 테스트: `kis_integration_test.py`
- 조건검색 테스트: `test_condition_stocks.py`
- 프로그램매매 테스트: `test_program_trade.py`

## 주의사항
- API 호출 시 실제 주문이 발생할 수 있으므로 테스트 시 주의
- 인증 정보는 반드시 안전하게 관리
- API 호출 제한에 주의

## 개발 가이드라인
1. 코드 수정 시 기존 변수명/함수명 유지
2. 모든 변경사항에 대한 한국어 주석 필수
3. 최소한의 수정으로 기능 구현
4. 테스트 코드 작성 필수 