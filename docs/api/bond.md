# 장내채권 API

`agent.bond` 네임스페이스로 장내채권 시세 조회와 주문·계좌 조회를 합니다. 내부적으로 `BondAPI` Facade가
`BondPriceAPI`(시세)와 `BondOrderAPI`(주문·계좌)에 위임합니다.

!!! warning "실전투자 전용"
    장내채권 API는 모의투자를 지원하지 않습니다. 모의투자 환경에서는 HTTP 요청 전에
    `PaperTradingNotSupportedError`가 발생합니다. 채권 종목코드는 12자리 표준코드(예: `KR6095572D81`)입니다.

## 시세 (`domestic-bond/v1/quotations/*`)

| 메서드 | 설명 |
|:---|:---|
| `agent.bond.get_bond_asking_price(code)` | 장내채권현재가(호가) [국내주식-132] |
| `agent.bond.get_bond_avg_unit()` | 장내채권 평균단가조회 [국내주식-158] |
| `agent.bond.get_bond_ccnl(code)` | 장내채권현재가(체결) [국내주식-201] |
| `agent.bond.get_bond_daily_chart(code)` | 장내채권 기간별시세(일) [국내주식-159] |
| `agent.bond.get_bond_daily_price(code)` | 장내채권현재가(일별) [국내주식-202] |
| `agent.bond.get_bond_info(code)` | 장내채권 기본조회 [국내주식-129] |
| `agent.bond.get_bond_issue_info(code)` | 장내채권 발행정보 [국내주식-156] |
| `agent.bond.get_bond_price(code)` | 장내채권현재가(시세) [국내주식-200] |

## 주문·계좌 (`domestic-bond/v1/trading/*`)

| 메서드 | 설명 |
|:---|:---|
| `agent.bond.buy_bond(code, quantity, price)` | 장내채권 매수주문 [국내주식-124] |
| `agent.bond.get_bond_balance()` | 장내채권 잔고조회 [국내주식-198] |
| `agent.bond.get_bond_daily_ccld()` | 장내채권 주문체결내역 [국내주식-127] |
| `agent.bond.get_bond_psbl_order(code, price)` | 장내채권 매수가능조회 [국내주식-199] |
| `agent.bond.get_bond_psbl_rvsecncl()` | 채권정정취소가능주문조회 [국내주식-126] |
| `agent.bond.modify_cancel_bond_order(action, code, orgn_odno)` | 장내채권 정정취소주문 [국내주식-125] |
| `agent.bond.sell_bond(code, quantity, price)` | 장내채권 매도주문 [국내주식-123] |

## 주문

주문 3종(`buy_bond`, `sell_bond`, `modify_cancel_bond_order`)은 POST로 한 번만 보내고 재시도하지 않습니다.
종목코드·수량·단가·Y/N 인자를 전송 전에 검증하며, 잘못되면 요청 없이 `ValueError`를 냅니다.

```python
# 매수 (주문단가는 채권 단가)
agent.bond.buy_bond("KR6095572D81", quantity=10, price=10460)

# 매도 — ord_dvsn: "01" 종목별, "02" 일자별(buy_date 필요), "03" 체결가별(buy_date·buy_seq 필요)
agent.bond.sell_bond("KR6095572D81", quantity=1, price=10000)

# 정정 / 잔량 전부 취소
agent.bond.modify_cancel_bond_order("modify", "KR6095572D81", "0000015402", quantity=2, price=10460)
agent.bond.modify_cancel_bond_order("cancel", "KR6095572D81", "0000015402", all_remaining=True)
```

!!! note "실거래 전 확인할 점"
    - 체결가별 매도(`ord_dvsn="03"`)의 매수일자·순번 요구는 공식 문서가 "잔고조회 참조"라고만 적어 둔 부분을
      보수적으로 해석한 것입니다. 값은 `get_bond_balance()` 결과에서 가져오세요.
    - 취소 주문의 단가 필드는 공식 문서에 규정이 없어 `"0"`을 보냅니다.

## 실시간

```python
ws.subscribe_bond("KR103502GA34", with_orderbook=True)   # H0BJCNT0 + H0BJASP0
ws.subscribe_bond_index("KR103502GA34")                  # H0BICNT0
```
