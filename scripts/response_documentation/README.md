# Response Documentation Scripts

이 디렉토리는 PyKIS API 응답 구조 문서화를 자동화하는 스크립트들을 포함합니다.

## 📁 파일 구조

### 스크립트

- **`extract_response_mappings.py`** - COLUMN_MAPPING 추출 스크립트
  - `open-trading-api/examples_llm/`의 334개 `chk_*.py` 파일에서 API 응답 필드 매핑 추출
  - 출력: `docs/api_reference/response_mappings.json`

- **`generate_complete_typeddict.py`** - TypedDict 모델 생성 스크립트
  - `response_mappings.json`을 기반으로 완전한 TypedDict 응답 모델 생성
  - 출력: `docs/api_reference/stock_complete.py`, `account_complete.py`

## 🚀 사용법

### 1. COLUMN_MAPPING 추출

```bash
# 프로젝트 루트에서 실행
python3 scripts/response_documentation/extract_response_mappings.py
```

**출력:**
- `docs/api_reference/response_mappings.json` - 334개 API 응답 필드 매핑

### 2. TypedDict 모델 생성

```bash
# 프로젝트 루트에서 실행
python3 scripts/response_documentation/generate_complete_typeddict.py
```

**출력:**
- `docs/api_reference/stock_complete.py` - Stock API 완전한 TypedDict 모델
- `docs/api_reference/account_complete.py` - Account API 완전한 TypedDict 모델

## 📊 처리 통계

- **추출된 API 수**: 334개
- **카테고리 수**: 288개
- **생성된 TypedDict 클래스**: 100+ 클래스
- **문서화된 필드 수**: 1000+ 필드

## 🔧 커스터마이징

### 새로운 API 매핑 추가

`generate_complete_typeddict.py`의 `PYKIS_TO_EXAMPLES_MAPPING` 딕셔너리에 추가:

```python
PYKIS_TO_EXAMPLES_MAPPING = {
    # 기존 매핑...
    "new_api_method": "corresponding_examples_api_name",
}
```

### 응답 클래스 생성 로직 수정

`generate_output_class()` 및 `generate_response_class()` 함수 참조

## 📚 참고 자료

- 생성된 완전 문서: `docs/api_reference/`
- 실제 적용된 파일: `pykis/responses/stock.py`, `pykis/responses/account.py`
- CHANGELOG: `CHANGELOG.md` v1.3.1

## 🎯 다음 단계

향후 추가 API (선물옵션, 채권, ELW 등) 문서화 시:

1. `response_mappings.json`에서 해당 API 찾기
2. `PYKIS_TO_EXAMPLES_MAPPING`에 매핑 추가
3. 스크립트 재실행
4. 생성된 TypedDict를 `pykis/responses/`에 통합

## 📝 작성 정보

- **작성일**: 2025-10-30
- **작성자**: Claude Code (AI Agent)
- **버전**: PyKIS v1.3.1
