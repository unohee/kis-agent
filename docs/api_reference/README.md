# API Reference Documentation

PyKIS API 응답 구조 참고 문서

## 📁 파일 목록

### 완전한 응답 모델 (참고용)

- **`stock_complete.py`** (1050줄)
  - Stock API의 모든 TypedDict 응답 모델
  - `open-trading-api/examples_llm/`에서 추출한 완전한 필드 문서
  - 실제 사용: `pykis/responses/stock.py`에 통합됨

- **`account_complete.py`** (388줄)
  - Account API의 모든 TypedDict 응답 모델
  - 계좌 잔고, 주문, 손익 등 완전한 필드 문서
  - 실제 사용: `pykis/responses/account.py`에 통합됨

### 응답 필드 매핑 데이터

- **`response_mappings.json`**
  - 334개 API 엔드포인트의 응답 필드 매핑
  - 각 API별 COLUMN_MAPPING 추출 데이터
  - 총 288개 카테고리 분류

## 🎯 사용 목적

### 1. 개발 참고
새로운 API 메서드 추가 시 해당 API의 완전한 응답 구조 확인

```python
# stock_complete.py에서 확인
class InquirePriceOutput(TypedDict, total=False):
    """주식현재가 시세 - 82개 필드 완전 문서화"""
    stck_prpr: str  # 주식 현재가
    per: str  # PER
    pbr: str  # PBR
    # ... 82개 필드
```

### 2. API 응답 구조 확인
`response_mappings.json`에서 특정 API의 응답 필드 검색

```bash
# jq로 특정 API 검색
jq '.apis[] | select(.api_name == "inquire_price")' response_mappings.json
```

### 3. 문서화 확장
향후 추가 API (선물옵션, 채권 등) 문서화 시 참고

## 📊 통계

```json
{
  "total_apis": 334,
  "categories": 288,
  "documented_fields": "1000+",
  "integrated_fields": 163
}
```

## 🔍 주요 API 응답 구조

### Stock APIs
- `inquire_price` - 주식 현재가 (82 fields)
- `inquire_daily_price` - 일별 시세 (18 fields)
- `inquire_investor` - 투자자 동향 (27 fields)
- `inquire_asking_price` - 호가 정보 (70+ fields)

### Account APIs
- `inquire_balance` - 주식 잔고 (71 fields)
- `inquire_balance_rlz_pl` - 실현 손익 (15 fields)
- `inquire_period_trade_profit` - 기간별 손익 (35 fields)

### Program Trade APIs
- `program_trade_by_stock` - 종목별 프로그램 매매
- `comp_program_trade_daily` - 일별 프로그램 매매 (88 fields)

### Market Data APIs
- `inquire_index_price` - 지수 시세
- `market_cap` - 시가총액
- `volume_rank` - 거래량 순위

## 🛠️ 생성 방법

이 참고 문서들은 다음 스크립트로 자동 생성되었습니다:

```bash
# 1. COLUMN_MAPPING 추출
python3 scripts/response_documentation/extract_response_mappings.py

# 2. TypedDict 모델 생성
python3 scripts/response_documentation/generate_complete_typeddict.py
```

자세한 사용법은 `scripts/response_documentation/README.md` 참조

## 📝 주의사항

- **이 파일들은 참고용**입니다. 실제 코드는 `pykis/responses/`에 있습니다.
- 한국어 필드 설명은 한국투자증권 API 공식 문서와 1:1 매핑됩니다.
- `total=False` 설정으로 모든 필드가 선택적(Optional)입니다.

## 🔗 관련 문서

- 실제 응답 타입: `pykis/responses/stock.py`, `account.py`
- 스크립트 문서: `scripts/response_documentation/README.md`
- 변경 이력: `CHANGELOG.md` v1.3.1
- 프로젝트 문서: `CLAUDE.md`

---

**Last Updated**: 2025-10-30
**PyKIS Version**: 1.3.1
**Total APIs Documented**: 334/334
