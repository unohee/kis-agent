# PyKIS 완전한 API 예제 가이드

모든 메서드에 대한 상세한 사용 예제를 포함한 완전한 레퍼런스 문서입니다.

## 목차
1. [초기화 및 설정](#초기화-및-설정)
2. [시세 조회 API](#시세-조회-api)
3. [거래원 및 투자자 정보](#거래원-및-투자자-정보)
4. [프로그램 매매](#프로그램-매매)
5. [계좌 관련 API](#계좌-관련-api)
6. [주문 관련 API](#주문-관련-api)
7. [조건검색 및 시장 정보](#조건검색-및-시장-정보)
8. [분봉 데이터 및 기술적 분석](#분봉-데이터-및-기술적-분석)
9. [유틸리티 메서드](#유틸리티-메서드)
10. [Rate Limiter 관리](#rate-limiter-관리)
11. [WebSocket 실시간](#websocket-실시간)

---

## 초기화 및 설정

### Agent 초기화

```python
from pykis import Agent
import os
from datetime import datetime

# 방법 1: 환경 변수 파일 사용
agent = Agent(env_path=".env")

# 방법 2: 직접 인증 정보 전달
agent = Agent(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="12345678",
    account_code="01",
    base_url="https://openapi.koreainvestment.com:9443"  # 실전
)

# 방법 3: Rate Limiter 설정과 함께 초기화
agent = Agent(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="12345678",
    account_code="01",
    enable_rate_limiter=True,
    rate_limiter_config={
        'requests_per_second': 20,
        'requests_per_minute': 1000,
        'min_interval_ms': 10,
        'burst_size': 15,
        'enable_adaptive': True
    }
)

print("Agent 초기화 완료!")
```

---

## 시세 조회 API

### get_stock_price() - 현재가 조회

```python
# 기본 사용법
result = agent.get_stock_price("005930")  # 삼성전자

if result and result.get('rt_cd') == '0':
    output = result['output']
    print(f"종목코드: {output['stck_shrn_iscd']}")
    print(f"현재가: {int(output['stck_prpr']):,}원")
    print(f"전일대비: {int(output['prdy_vrss']):,}원 ({output['prdy_ctrt']}%)")
    print(f"거래량: {int(output['acml_vol']):,}주")
    print(f"시가: {int(output['stck_oprc']):,}원")
    print(f"고가: {int(output['stck_hgpr']):,}원")
    print(f"저가: {int(output['stck_lwpr']):,}원")

# 여러 종목 순차 조회
stocks = ["005930", "000660", "035720"]  # 삼성전자, SK하이닉스, 카카오
for code in stocks:
    result = agent.get_stock_price(code)
    if result and result.get('rt_cd') == '0':
        print(f"{code}: {result['output']['stck_prpr']}원")
```

### get_daily_price() - 일별 시세 조회

```python
# 일봉 데이터 조회
daily = agent.get_daily_price("005930", period="D", org_adj_prc="1")

if daily and daily.get('rt_cd') == '0':
    print("최근 10일 종가:")
    for day in daily['output'][:10]:
        date = day['stck_bsop_date']
        close = int(day['stck_clpr'])
        volume = int(day['acml_vol'])
        print(f"{date}: {close:,}원 (거래량: {volume:,})")

# 주봉 데이터 조회
weekly = agent.get_daily_price("005930", period="W")
if weekly:
    print("\n최근 5주 데이터:")
    for week in weekly['output'][:5]:
        print(f"주간 종가: {week['stck_clpr']}원")

# 월봉 데이터 조회
monthly = agent.get_daily_price("005930", period="M")
if monthly:
    print("\n최근 3개월 데이터:")
    for month in monthly['output'][:3]:
        print(f"월간 종가: {month['stck_clpr']}원")
```

### get_minute_price() - 당일 분봉 조회

```python
# 당일 분봉 조회 (최근 30분)
minutes = agent.get_minute_price("005930", hour="150000")

if minutes and minutes.get('rt_cd') == '0':
    print("최근 30분 분봉 데이터:")
    for i, minute in enumerate(minutes['output'][:30]):
        time = minute['stck_cntg_hour']
        price = int(minute['stck_prpr'])
        vol = int(minute['cntg_vol'])
        print(f"{time}: {price:,}원 (거래량: {vol:,})")

        # 5분 간격으로만 출력
        if (i + 1) % 5 == 0:
            print("---")

# 특정 시간대 분봉 조회
morning_minutes = agent.get_minute_price("005930", hour="100000")
if morning_minutes:
    print("\n오전 10시 이전 분봉:")
    for minute in morning_minutes['output'][:10]:
        print(f"{minute['stck_cntg_hour']}: {minute['stck_prpr']}원")
```

### get_daily_minute_price() - 과거 일자 분봉 조회

```python
# 특정 날짜 분봉 조회
past_date = "20240101"
past_minutes = agent.get_daily_minute_price("005930", past_date, "153000")

if past_minutes and past_minutes.get('rt_cd') == '0':
    print(f"{past_date} 분봉 데이터:")

    # 시가/종가 확인
    if past_minutes['output']:
        first = past_minutes['output'][-1]  # 첫 분봉
        last = past_minutes['output'][0]    # 마지막 분봉

        print(f"시가: {first['stck_prpr']}원 ({first['stck_cntg_hour']})")
        print(f"종가: {last['stck_prpr']}원 ({last['stck_cntg_hour']})")

    # 거래량 상위 시간대 찾기
    high_volume = sorted(
        past_minutes['output'][:60],
        key=lambda x: int(x['cntg_vol']),
        reverse=True
    )[:5]

    print("\n거래량 상위 5개 시간대:")
    for minute in high_volume:
        print(f"{minute['stck_cntg_hour']}: {int(minute['cntg_vol']):,}주")
```

### get_daily_credit_balance() - 신용잔고 조회

```python
# 신용잔고 일별 추이
date = "20240508"
credit = agent.get_daily_credit_balance("005930", date)

if credit and credit.get('rt_cd') == '0':
    for day in credit['output']:
        print(f"날짜: {day['stck_bsop_date']}")
        print(f"  융자잔고: {int(day['loan_bal']):,}주")
        print(f"  융자금액: {int(day['loan_amt']):,}원")
        print(f"  대주잔고: {int(day['stln_bal']):,}주")
        print(f"  대주금액: {int(day['stln_amt']):,}원")
        print("---")
```

### get_orderbook_raw() - 호가 정보 조회

```python
# 호가 정보 조회
orderbook = agent.get_orderbook_raw("005930")

if orderbook and orderbook.get('rt_cd') == '0':
    output = orderbook['output']

    print("=== 매도 호가 ===")
    for i in range(10, 0, -1):
        price = int(output[f'askp{i}'])
        volume = int(output[f'askp_rsqn{i}'])
        if price > 0:
            print(f"매도 {i:2d}호가: {price:,}원 ({volume:,}주)")

    print("\n=== 매수 호가 ===")
    for i in range(1, 11):
        price = int(output[f'bidp{i}'])
        volume = int(output[f'bidp_rsqn{i}'])
        if price > 0:
            print(f"매수 {i:2d}호가: {price:,}원 ({volume:,}주)")

    # 호가 스프레드 계산
    spread = int(output['askp1']) - int(output['bidp1'])
    print(f"\n호가 스프레드: {spread:,}원")

    # 호가 잔량 비율
    total_ask = sum(int(output[f'askp_rsqn{i}']) for i in range(1, 11))
    total_bid = sum(int(output[f'bidp_rsqn{i}']) for i in range(1, 11))
    ratio = (total_bid / total_ask * 100) if total_ask > 0 else 0
    print(f"매수/매도 잔량 비율: {ratio:.1f}%")
```

### get_index_daily_price() - 지수 일별 시세

```python
# KOSPI 지수 조회
kospi = agent.get_index_daily_price("0001", "D")

if kospi and kospi.get('rt_cd') == '0':
    print("KOSPI 최근 5일:")
    for day in kospi['output'][:5]:
        date = day['stck_bsop_date']
        close = float(day['bstp_nmix_prpr'])
        change = float(day['bstp_nmix_prdy_vrss'])
        rate = float(day['prdy_ctrt'])
        print(f"{date}: {close:.2f} ({change:+.2f}, {rate:+.2f}%)")

# KOSDAQ 지수 조회
kosdaq = agent.get_index_daily_price("1001", "D")
if kosdaq:
    print("\nKOSDAQ 최근 5일:")
    for day in kosdaq['output'][:5]:
        print(f"{day['stck_bsop_date']}: {day['bstp_nmix_prpr']}")
```

---

## 거래원 및 투자자 정보

### get_member() - 거래원별 매매 현황

```python
# 거래원 정보 조회
members = agent.get_member("005930")

if members and members.get('rt_cd') == '0':
    print("=== 매도 상위 거래원 ===")
    for i, member in enumerate(members['output'][:5], 1):
        if member['seln_mbcr_no'] != "00000":
            print(f"{i}. {member['seln_mbcr_name']}")
            print(f"   매도량: {int(member['total_seln_qty']):,}주")
            print(f"   매도금액: {int(member['seln_mbcr_rlim_val']):,}원")

    print("\n=== 매수 상위 거래원 ===")
    for i, member in enumerate(members['output'][:5], 1):
        if member['shnu_mbcr_no'] != "00000":
            print(f"{i}. {member['shnu_mbcr_name']}")
            print(f"   매수량: {int(member['total_shnu_qty']):,}주")
            print(f"   매수금액: {int(member['shnu_mbcr_rlim_val']):,}원")
```

### get_foreign_broker_net_buy() - 외국계 순매수

```python
# 외국계 증권사 순매수 현황
foreign = agent.get_foreign_broker_net_buy("005930")

if foreign:
    print(f"외국계 전체 순매수: {foreign['net_buy_volume']:,}주")
    print(f"외국계 순매수 금액: {foreign['net_buy_amount']:,}원")

    # 특정 외국계 증권사 지정
    specific_brokers = ["모간스탠리", "골드만삭스", "UBS"]
    foreign_specific = agent.get_foreign_broker_net_buy(
        "005930",
        foreign_brokers=specific_brokers
    )

    if foreign_specific:
        print(f"\n특정 외국계 순매수: {foreign_specific['net_buy_volume']:,}주")

# 날짜별 외국계 순매수
date = "20240101"
foreign_date = agent.get_foreign_broker_net_buy("005930", date=date)
if foreign_date:
    print(f"\n{date} 외국계 순매수: {foreign_date['net_buy_volume']:,}주")
```

### get_stock_investor() - 투자자별 매매 동향

```python
# 투자자별 매매 동향
investors = agent.get_stock_investor("005930")

if investors and investors.get('rt_cd') == '0':
    output = investors['output']

    # 투자자별 순매수
    foreign_net = int(output['frgn_ntby_qty'])  # 외국인
    inst_net = int(output['orgn_ntby_qty'])     # 기관
    retail_net = int(output['prsn_ntby_qty'])   # 개인

    print("=== 투자자별 순매수 ===")
    print(f"외국인: {foreign_net:,}주")
    print(f"기관: {inst_net:,}주")
    print(f"개인: {retail_net:,}주")

    # 투자자별 거래 비중
    total_vol = int(output['acml_vol'])
    if total_vol > 0:
        foreign_ratio = int(output['frgn_ntby_tr_pbmn']) / total_vol * 100
        inst_ratio = int(output['orgn_ntby_tr_pbmn']) / total_vol * 100

        print("\n=== 거래 비중 ===")
        print(f"외국인: {foreign_ratio:.1f}%")
        print(f"기관: {inst_ratio:.1f}%")
```

### get_member_transaction() - 회원사 거래 정보

```python
# 전체 회원사 거래 정보
member_trans = agent.get_member_transaction("005930")

if member_trans and member_trans.get('rt_cd') == '0':
    for member in member_trans['output'][:10]:
        print(f"{member['mbcr_name']}: 순매수 {member['net_qty']}주")

# 특정 회원사 거래 정보
member_trans = agent.get_member_transaction("005930", mem_code="00230")  # 미래에셋
if member_trans:
    output = member_trans['output']
    print(f"미래에셋 순매수: {output['net_qty']}주")
```

### get_stock_member() - 종목별 회원사 정보

```python
# 종목별 회원사 매매 정보
stock_member = agent.get_stock_member("005930")

if stock_member and stock_member.get('rt_cd') == '0':
    print("=== 회원사별 매매 현황 ===")
    for member in stock_member['output'][:5]:
        print(f"회원사: {member['mbcr_name']}")
        print(f"  매수: {member['shnu_vol']}주")
        print(f"  매도: {member['seln_vol']}주")
        print(f"  순매수: {member['net_vol']}주")
        print("---")
```

---

## 프로그램 매매

### get_program_trade_by_stock() - 종목별 프로그램매매

```python
# 종목별 프로그램매매 추이
program = agent.get_program_trade_by_stock("005930")

if program and program.get('rt_cd') == '0':
    output = program['output']

    # 프로그램 매매 현황
    prog_buy = int(output['program_buy_vol'])
    prog_sell = int(output['program_sell_vol'])
    prog_net = prog_buy - prog_sell

    print("=== 프로그램매매 현황 ===")
    print(f"프로그램 매수: {prog_buy:,}주")
    print(f"프로그램 매도: {prog_sell:,}주")
    print(f"프로그램 순매수: {prog_net:,}주")

    # 차익거래 현황
    arb_buy = int(output['arbitrage_buy_vol'])
    arb_sell = int(output['arbitrage_sell_vol'])

    print("\n=== 차익거래 현황 ===")
    print(f"차익 매수: {arb_buy:,}주")
    print(f"차익 매도: {arb_sell:,}주")
```

### get_program_trade_hourly_trend() - 시간대별 프로그램매매

```python
# 시간대별 프로그램매매 추이
hourly = agent.get_program_trade_hourly_trend("005930")

if hourly and hourly.get('rt_cd') == '0':
    print("=== 시간대별 프로그램 순매수 ===")

    for hour_data in hourly['output'][:10]:  # 최근 10개 시간대
        time = hour_data['time']
        net_buy = int(hour_data['net_buy'])
        cum_net = int(hour_data['cumulative_net'])

        print(f"{time}: {net_buy:,}주 (누적: {cum_net:,}주)")

    # 프로그램 매수 집중 시간대 찾기
    max_buy = max(hourly['output'], key=lambda x: int(x['net_buy']))
    print(f"\n최대 순매수 시간: {max_buy['time']} ({int(max_buy['net_buy']):,}주)")
```

### get_program_trade_daily_summary() - 일별 프로그램매매 집계

```python
# 특정일 프로그램매매 집계
date = "20240107"
daily_program = agent.get_program_trade_daily_summary("005930", date)

if daily_program and daily_program.get('rt_cd') == '0':
    output = daily_program['output']

    print(f"=== {date} 프로그램매매 집계 ===")
    print(f"전체 매수: {output['total_buy']:,}주")
    print(f"전체 매도: {output['total_sell']:,}주")
    print(f"순매수: {output['net_buy']:,}주")
    print(f"차익거래 비중: {output['arbitrage_ratio']:.1f}%")
```

### get_program_trade_period_detail() - 기간별 프로그램매매

```python
# 기간별 프로그램매매 상세
start_date = "20240101"
end_date = "20240107"
period_program = agent.get_program_trade_period_detail(start_date, end_date)

if period_program and period_program.get('rt_cd') == '0':
    print(f"=== {start_date} ~ {end_date} 프로그램매매 ===")

    for day in period_program['output']:
        date = day['trade_date']
        net = int(day['net_buy_amount'])
        print(f"{date}: {net:,}원")

    # 기간 합계
    total_buy = sum(int(d['buy_amount']) for d in period_program['output'])
    total_sell = sum(int(d['sell_amount']) for d in period_program['output'])

    print(f"\n기간 총 매수: {total_buy:,}원")
    print(f"기간 총 매도: {total_sell:,}원")
```

### get_program_trade_market_daily() - 시장 전체 프로그램매매

```python
# 시장 전체 프로그램매매 현황
market_program = agent.get_program_trade_market_daily("20240101", "20240107")

if market_program and market_program.get('rt_cd') == '0':
    print("=== 시장 전체 프로그램매매 ===")

    for day in market_program['output']:
        date = day['trade_date']
        kospi_net = int(day['kospi_net'])
        kosdaq_net = int(day['kosdaq_net'])

        print(f"{date}:")
        print(f"  KOSPI: {kospi_net:,}백만원")
        print(f"  KOSDAQ: {kosdaq_net:,}백만원")
```

---

## 계좌 관련 API

### get_account_balance() - 계좌 잔고 조회

```python
# 계좌 잔고 조회
balance = agent.get_account_balance()

if balance and balance.get('rt_cd') == '0':
    # 개별 종목 정보
    print("=== 보유 종목 ===")
    for stock in balance['output']:
        if int(stock['hldg_qty']) > 0:
            code = stock['pdno']
            name = stock['prdt_name']
            qty = int(stock['hldg_qty'])
            avg_price = float(stock['pchs_avg_pric'])
            cur_price = int(stock['prpr'])
            profit = int(stock['evlu_pfls_amt'])
            rate = float(stock['evlu_pfls_rt'])

            print(f"\n{name} ({code})")
            print(f"  보유수량: {qty:,}주")
            print(f"  평균단가: {avg_price:,.0f}원")
            print(f"  현재가: {cur_price:,}원")
            print(f"  평가손익: {profit:,}원 ({rate:+.2f}%)")

    # 계좌 요약 정보
    if balance.get('output2'):
        summary = balance['output2'][0]
        total_asset = int(summary['tot_evlu_amt'])
        total_buy = int(summary['pchs_amt_smtl'])
        total_eval = int(summary['evlu_amt_smtl'])
        total_profit = int(summary['evlu_pfls_smtl'])

        print("\n=== 계좌 요약 ===")
        print(f"총 평가금액: {total_asset:,}원")
        print(f"총 매입금액: {total_buy:,}원")
        print(f"총 평가금액: {total_eval:,}원")
        print(f"총 평가손익: {total_profit:,}원")
```

### get_possible_order_amount() - 주문 가능 금액 조회

```python
# 매수 가능 조회
possible = agent.get_possible_order_amount("005930", "70000", "01")

if possible and possible.get('rt_cd') == '0':
    output = possible['output']

    cash = int(output['ord_psbl_cash'])
    qty = int(output['ord_psbl_qty'])
    max_qty = int(output['max_buy_qty'])

    print(f"주문 가능 현금: {cash:,}원")
    print(f"주문 가능 수량: {qty:,}주")
    print(f"최대 매수 수량: {max_qty:,}주")

    # 금액별 매수 가능 수량 계산
    prices = [65000, 70000, 75000]
    for price in prices:
        result = agent.get_possible_order_amount("005930", str(price))
        if result:
            qty = int(result['output']['max_buy_qty'])
            print(f"{price:,}원일 때: {qty:,}주 매수 가능")
```

### inquire_balance_rlz_pl() - 평가손익 조회 (DataFrame)

```python
# 실현손익 포함 잔고 조회
df = agent.inquire_balance_rlz_pl()

if df is not None and not df.empty:
    # 수익률 상위 종목
    print("=== 수익률 TOP 5 ===")
    top_gainers = df.nlargest(5, '수익률')
    for _, row in top_gainers.iterrows():
        print(f"{row['종목명']}: {row['수익률']:.2f}%")

    # 손실 종목
    print("\n=== 손실 종목 ===")
    losers = df[df['수익률'] < 0]
    for _, row in losers.iterrows():
        print(f"{row['종목명']}: {row['평가손익']:,}원 ({row['수익률']:.2f}%)")

    # 포트폴리오 요약
    total_profit = df['평가손익'].sum()
    total_value = df['평가금액'].sum()
    avg_rate = df['수익률'].mean()

    print(f"\n=== 포트폴리오 요약 ===")
    print(f"총 평가손익: {total_profit:,.0f}원")
    print(f"총 평가금액: {total_value:,.0f}원")
    print(f"평균 수익률: {avg_rate:.2f}%")
```

### inquire_daily_ccld() - 일별 주문체결 조회

```python
# 최근 30일 주문체결 내역
from datetime import datetime, timedelta

end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

df = agent.inquire_daily_ccld(start_date, end_date)

if df is not None and not df.empty:
    print("=== 최근 주문체결 내역 ===")
    for _, row in df.head(10).iterrows():
        print(f"{row['주문일자']} {row['종목명']}")
        print(f"  {row['매매구분']}: {row['체결수량']}주 @ {row['체결단가']:,}원")
        print(f"  주문번호: {row['주문번호']}")

    # 종목별 거래 집계
    trade_summary = df.groupby('종목명').agg({
        '체결수량': 'sum',
        '체결금액': 'sum'
    })
    print("\n=== 종목별 거래 요약 ===")
    print(trade_summary)
```

### inquire_period_trade_profit() - 기간별 매매손익

```python
# 기간별 매매손익 조회
start_date = "20240101"
end_date = "20240131"

df = agent.inquire_period_trade_profit(start_date, end_date)

if df is not None and not df.empty:
    print(f"=== {start_date} ~ {end_date} 매매손익 ===")

    # 종목별 실현손익
    for _, row in df.iterrows():
        print(f"{row['종목명']} ({row['종목코드']})")
        print(f"  매도금액: {row['매도금액']:,}원")
        print(f"  매수금액: {row['매수금액']:,}원")
        print(f"  실현손익: {row['실현손익']:,}원")
        print(f"  수익률: {row['수익률']:.2f}%")
        print("---")

    # 전체 손익 집계
    total_profit = df['실현손익'].sum()
    total_sell = df['매도금액'].sum()
    total_buy = df['매수금액'].sum()

    print(f"\n=== 기간 총 손익 ===")
    print(f"총 매도금액: {total_sell:,.0f}원")
    print(f"총 매수금액: {total_buy:,.0f}원")
    print(f"총 실현손익: {total_profit:,.0f}원")
```

### inquire_psbl_sell() - 매도가능수량 조회

```python
# 매도 가능 수량 조회
sellable = agent.inquire_psbl_sell("005930")

if sellable and sellable.get('rt_cd') == '0':
    output = sellable['output']

    total_qty = int(output['hldg_qty'])
    sellable_qty = int(output['ord_psbl_qty'])
    locked_qty = total_qty - sellable_qty

    print(f"총 보유수량: {total_qty:,}주")
    print(f"매도 가능수량: {sellable_qty:,}주")
    print(f"매도 불가수량: {locked_qty:,}주")

    # 예상 매도 금액
    if sellable_qty > 0:
        current_price = int(output['prpr'])
        expected_amount = sellable_qty * current_price
        print(f"현재가 기준 예상 매도금액: {expected_amount:,}원")
```

---

## 주문 관련 API

### order_cash() - 현금 주문

```python
# 지정가 매수
buy_result = agent.order_cash(
    pdno="005930",
    qty=10,
    price=70000,
    buy_sell="BUY",
    order_type="00"  # 지정가
)

if buy_result and buy_result.get('rt_cd') == '0':
    order_no = buy_result['output']['ODNO']
    print(f"매수 주문 성공! 주문번호: {order_no}")

    # 주문 정보 확인
    order_time = buy_result['output']['ORD_TMD']
    print(f"주문시간: {order_time}")

# 시장가 매도
sell_result = agent.order_cash(
    pdno="005930",
    qty=5,
    price=0,  # 시장가는 0
    buy_sell="SELL",
    order_type="01"  # 시장가
)

if sell_result and sell_result.get('rt_cd') == '0':
    print(f"매도 주문 성공! 주문번호: {sell_result['output']['ODNO']}")

# IOC 주문 (즉시 체결 또는 취소)
ioc_result = agent.order_cash(
    pdno="005930",
    qty=10,
    price=70000,
    buy_sell="BUY",
    order_type="11"  # IOC 지정가
)
```

### order_stock_cash() - 통합 현금 주문

```python
# 다양한 주문 유형 예시

# 1. 최유리지정가 매수 (빠른 체결)
result = agent.order_stock_cash(
    ord_dv="buy",
    pdno="005930",
    ord_dvsn="03",  # 최유리지정가
    ord_qty="10",
    ord_unpr="0"  # 최유리는 0
)

# 2. 장전 시간외 주문
result = agent.order_stock_cash(
    ord_dv="buy",
    pdno="005930",
    ord_dvsn="05",  # 장전시간외
    ord_qty="10",
    ord_unpr="70000"
)

# 3. FOK 주문 (전량 체결 또는 취소)
result = agent.order_stock_cash(
    ord_dv="buy",
    pdno="005930",
    ord_dvsn="12",  # FOK 지정가
    ord_qty="100",
    ord_unpr="70000"
)

# 4. 조건부지정가
result = agent.order_stock_cash(
    ord_dv="buy",
    pdno="005930",
    ord_dvsn="02",  # 조건부지정가
    ord_qty="10",
    ord_unpr="70000",
    cndt_pric="69500"  # 조건가격
)
```

### order_cash_sor() - SOR 최유리지정가 주문

```python
# SOR 최유리지정가 매수
sor_buy = agent.order_cash_sor(
    pdno="005930",
    qty=10,
    buy_sell="BUY",
    order_type="03"  # 최유리지정가
)

if sor_buy and sor_buy.get('rt_cd') == '0':
    print(f"SOR 매수 주문 성공!")
    print(f"체결 거래소: {sor_buy['output'].get('EXCH_DVSN_CD')}")

# SOR 시장가 매도
sor_sell = agent.order_cash_sor(
    pdno="005930",
    qty=5,
    buy_sell="SELL",
    order_type="01"  # 시장가
)
```

### order_rvsecncl() - 주문 정정/취소

```python
# 주문 후 정정/취소
order = agent.order_stock_cash("buy", "005930", "00", "10", "70000")

if order and order.get('rt_cd') == '0':
    order_no = order['output']['ODNO']

    # 주문 정정 (가격 변경)
    modify_result = agent.order_rvsecncl(
        org_order_no=order_no,
        qty=10,  # 원래 수량
        price=69000,  # 새로운 가격
        order_type="00",
        cncl_type="01"  # 정정
    )

    if modify_result and modify_result.get('rt_cd') == '0':
        print("주문 정정 성공!")

    # 주문 취소
    cancel_result = agent.order_rvsecncl(
        org_order_no=order_no,
        qty=10,
        price=69000,
        order_type="00",
        cncl_type="02"  # 취소
    )

    if cancel_result and cancel_result.get('rt_cd') == '0':
        print("주문 취소 성공!")
```

### order_credit_buy() / order_credit_sell() - 신용 매매

```python
# 신용 매수
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")
credit_buy = agent.order_credit_buy(
    pdno="005930",
    qty=10,
    price=70000,
    order_type="00",  # 지정가
    credit_type="21"  # 자기융자신규
)

if credit_buy and credit_buy.get('rt_cd') == '0':
    print(f"신용 매수 성공! 주문번호: {credit_buy['output']['ODNO']}")
    print(f"대출일자: {today}")

# 신용 매도 (상환)
credit_sell = agent.order_credit_sell(
    pdno="005930",
    qty=10,
    price=75000,
    order_type="00",
    credit_type="11"  # 융자상환매도
)

if credit_sell and credit_sell.get('rt_cd') == '0':
    print("신용 매도(상환) 성공!")
```

### order_stock_credit() - 통합 신용 주문

```python
# 신용 주문 다양한 예시
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")

# 1. 자기융자신규 매수
result = agent.order_stock_credit(
    ord_dv="buy",
    pdno="005930",
    crdt_type="21",  # 자기융자신규
    ord_dvsn="00",   # 지정가
    ord_qty="10",
    ord_unpr="70000",
    loan_dt=today
)

# 2. 유통융자신규 매수
result = agent.order_stock_credit(
    ord_dv="buy",
    pdno="005930",
    crdt_type="23",  # 유통융자신규
    ord_dvsn="03",   # 최유리지정가
    ord_qty="5",
    ord_unpr="0",
    loan_dt=today
)

# 3. 융자상환매도
result = agent.order_stock_credit(
    ord_dv="sell",
    pdno="005930",
    crdt_type="25",  # 자기융자상환
    ord_dvsn="01",   # 시장가
    ord_qty="10",
    ord_unpr="0",
    loan_dt="20240101"  # 원래 대출일자
)
```

### inquire_psbl_rvsecncl() - 정정취소 가능 주문 조회

```python
# 정정/취소 가능한 주문 조회
cancelable = agent.inquire_psbl_rvsecncl()

if cancelable and cancelable.get('rt_cd') == '0':
    print("=== 정정/취소 가능 주문 ===")

    for order in cancelable['output']:
        order_no = order['odno']
        stock_name = order['prdt_name']
        qty = int(order['ord_qty'])
        price = int(order['ord_unpr'])
        status = order['ord_gno_brno']

        print(f"\n주문번호: {order_no}")
        print(f"종목: {stock_name}")
        print(f"수량: {qty:,}주 @ {price:,}원")
        print(f"상태: {status}")

        # 자동 취소 예시
        if price > 70000:  # 특정 조건
            cancel = agent.order_rvsecncl(
                org_order_no=order_no,
                qty=qty,
                price=price,
                order_type="00",
                cncl_type="02"
            )
            if cancel:
                print(f"  → 자동 취소 완료")
```

---

## 조건검색 및 시장 정보

### get_condition_stocks() - 조건검색 종목

```python
# 조건검색 종목 조회
conditions = agent.get_condition_stocks(
    user_id="unohee",
    seq=0,
    tr_cont="N"
)

if conditions:
    print("=== 조건검색 종목 ===")
    for i, stock in enumerate(conditions[:20], 1):
        code = stock['code']
        name = stock['name']
        price = stock.get('price', 0)
        rate = stock.get('rate', 0)
        volume = stock.get('volume', 0)

        print(f"{i:2d}. {name} ({code})")
        print(f"    가격: {price:,}원 ({rate:+.2f}%)")
        print(f"    거래량: {volume:,}주")

        # 추가 정보 조회
        if rate > 10:  # 급등주
            detail = agent.get_stock_price(code)
            if detail:
                print(f"    상세: 고가 {detail['output']['stck_hgpr']}원")
```

### get_top_gainers() - 상승률 상위 종목

```python
# 상승률 상위 종목
gainers = agent.get_top_gainers()

if gainers:
    print("=== 상승률 TOP 10 ===")
    for i, stock in enumerate(gainers[:10], 1):
        name = stock['hts_kor_isnm']
        code = stock['stck_shrn_iscd']
        price = int(stock['stck_prpr'])
        rate = float(stock['prdy_ctrt'])
        volume = int(stock['acml_vol'])

        print(f"{i:2d}. {name} ({code})")
        print(f"    {price:,}원 ({rate:+.2f}%)")
        print(f"    거래량: {volume:,}주")

        # 거래대금 계산
        amount = price * volume
        if amount > 100_000_000_000:  # 1000억 이상
            print(f"    거래대금: {amount/100_000_000:.0f}억원 ★")
```

### get_volume_power() - 체결강도 순위

```python
# 체결강도 상위 종목
volume_stocks = agent.get_volume_power(volume=1000000)  # 100만주 이상

if volume_stocks and volume_stocks.get('rt_cd') == '0':
    print("=== 체결강도 상위 종목 ===")

    for i, stock in enumerate(volume_stocks['output'][:10], 1):
        name = stock['hts_kor_isnm']
        code = stock['stck_shrn_iscd']
        volume = int(stock['acml_vol'])
        power = float(stock.get('vol_power', 0))
        rate = float(stock['prdy_ctrt'])

        print(f"{i:2d}. {name} ({code})")
        print(f"    거래량: {volume:,}주")
        print(f"    체결강도: {power:.1f}")
        print(f"    등락률: {rate:+.2f}%")

        # 매수/매도 신호 판단
        if power > 200 and rate > 0:
            print(f"    → 강한 매수세 ★")
        elif power < 50 and rate < 0:
            print(f"    → 강한 매도세 ☆")
```

### get_holiday_info() - 휴장일 정보

```python
# 휴장일 정보 조회
holidays = agent.get_holiday_info()

if holidays and holidays.get('rt_cd') == '0':
    print("=== 휴장일 정보 ===")

    for day in holidays['output']:
        date = day['bass_dt']
        day_name = day['wday_dvsn_nm']
        holiday_name = day.get('opnd_yn_nm', '')

        print(f"{date}: {day_name} - {holiday_name}")

    # 다음 휴장일 찾기
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")

    next_holiday = None
    for day in holidays['output']:
        if day['bass_dt'] > today and day['opnd_yn'] == 'N':
            next_holiday = day
            break

    if next_holiday:
        print(f"\n다음 휴장일: {next_holiday['bass_dt']} ({next_holiday['wday_dvsn_nm']})")
```

### is_holiday() - 특정일 휴장 여부

```python
# 특정일 휴장 여부 확인
from datetime import datetime, timedelta

# 오늘부터 7일간 개장일 확인
for i in range(7):
    check_date = (datetime.now() + timedelta(days=i))
    date_str = check_date.strftime("%Y%m%d")

    is_holiday = agent.is_holiday(date_str)

    if is_holiday is not None:
        status = "휴장" if is_holiday else "개장"
        weekday = check_date.strftime("%A")
        print(f"{date_str} ({weekday}): {status}")
```

---

## 분봉 데이터 및 기술적 분석

### fetch_minute_data() - 분봉 데이터 수집

```python
import pandas as pd

# 당일 분봉 데이터 수집
df = agent.fetch_minute_data("005930")

if not df.empty:
    print(f"수집된 분봉 데이터: {len(df)}개")
    print(f"시간 범위: {df['stck_cntg_hour'].min()} ~ {df['stck_cntg_hour'].max()}")

    # 거래량 상위 시간대
    df['cntg_vol'] = pd.to_numeric(df['cntg_vol'])
    top_volume = df.nlargest(5, 'cntg_vol')

    print("\n=== 거래량 상위 5개 시간대 ===")
    for _, row in top_volume.iterrows():
        print(f"{row['stck_cntg_hour']}: {row['cntg_vol']:,}주")

    # 가격 변동폭 분석
    df['stck_prpr'] = pd.to_numeric(df['stck_prpr'])
    price_range = df['stck_prpr'].max() - df['stck_prpr'].min()
    volatility = (price_range / df['stck_prpr'].mean()) * 100

    print(f"\n일중 변동폭: {price_range:,.0f}원 ({volatility:.2f}%)")

# 특정 날짜 분봉 데이터
df_past = agent.fetch_minute_data("005930", "20240101")

if not df_past.empty:
    # VWAP 계산
    df_past['typical_price'] = (
        pd.to_numeric(df_past['stck_hgpr']) +
        pd.to_numeric(df_past['stck_lwpr']) +
        pd.to_numeric(df_past['stck_prpr'])
    ) / 3
    df_past['cntg_vol'] = pd.to_numeric(df_past['cntg_vol'])

    vwap = (df_past['typical_price'] * df_past['cntg_vol']).sum() / df_past['cntg_vol'].sum()
    print(f"\nVWAP: {vwap:,.0f}원")
```

### calculate_support_resistance() - 지지/저항선 계산

```python
# 매물대 분석
analysis = agent.calculate_support_resistance(
    code="005930",
    date=None,  # 최근 데이터
    price_bins=50
)

if analysis:
    print(f"=== {analysis['code']} 매물대 분석 ===")
    print(f"분석일: {analysis['analysis_date']}")
    print(f"현재가: {analysis['current_price']:,.0f}원")
    print(f"VWAP: {analysis['vwap']:,.0f}원")

    # 피봇 포인트
    pivot = analysis['pivot_points']
    print(f"\n=== 피봇 포인트 ===")
    print(f"피봇: {pivot['pivot']:,.0f}원")
    print(f"저항선: R1={pivot['resistance']['r1']:,.0f}, "
          f"R2={pivot['resistance']['r2']:,.0f}, "
          f"R3={pivot['resistance']['r3']:,.0f}")
    print(f"지지선: S1={pivot['support']['s1']:,.0f}, "
          f"S2={pivot['support']['s2']:,.0f}, "
          f"S3={pivot['support']['s3']:,.0f}")

    # 주요 지지/저항선
    print(f"\n=== 주요 지지선 (강도순) ===")
    for level in analysis['support_levels'][:3]:
        price = level['price']
        strength = level['strength']
        print(f"  {price:,.0f}원 (강도: {strength:.1f})")

    print(f"\n=== 주요 저항선 (강도순) ===")
    for level in analysis['resistance_levels'][:3]:
        price = level['price']
        strength = level['strength']
        print(f"  {price:,.0f}원 (강도: {strength:.1f})")

    # 매매 신호 판단
    current = analysis['current_price']
    vwap = analysis['vwap']

    if current < vwap and analysis['support_levels']:
        nearest_support = analysis['support_levels'][0]['price']
        if current <= nearest_support * 1.01:
            print(f"\n★ 매수 신호: 지지선 {nearest_support:,.0f}원 근처")

    if current > vwap and analysis['resistance_levels']:
        nearest_resistance = analysis['resistance_levels'][0]['price']
        if current >= nearest_resistance * 0.99:
            print(f"\n☆ 매도 신호: 저항선 {nearest_resistance:,.0f}원 근처")
```

### init_minute_db() / migrate_minute_csv_to_db() - DB 관리

```python
# SQLite DB 초기화
if agent.init_minute_db("db/stonks_candles.db"):
    print("분봉 데이터베이스 초기화 완료")

# CSV 데이터를 DB로 마이그레이션
stocks = ["005930", "000660", "035720"]
for code in stocks:
    if agent.migrate_minute_csv_to_db(code):
        print(f"{code} CSV → DB 마이그레이션 완료")

# DB에서 데이터 조회 예시
import sqlite3
import pandas as pd

conn = sqlite3.connect("db/stonks_candles.db")
query = """
    SELECT * FROM minute_data
    WHERE code = '005930'
    AND date = '20240101'
    ORDER BY stck_cntg_hour DESC
    LIMIT 10
"""
df = pd.read_sql_query(query, conn)
conn.close()

print(f"DB에서 조회한 데이터: {len(df)}건")
```

---

## 유틸리티 메서드

### get_all_methods() - 사용 가능한 메서드 조회

```python
# 전체 메서드 조회
all_methods = agent.get_all_methods()

print("=== 사용 가능한 메서드 ===")
for category, info in all_methods.items():
    if category != "_summary":
        print(f"\n{info['title']}: {info['count']}개")
        for method in info['methods'][:3]:  # 각 카테고리별 3개씩
            print(f"  - {method}")

# 상세 정보 포함
detailed = agent.get_all_methods(show_details=True)

for category, info in detailed.items():
    if category == "stock":  # 주식 카테고리만
        print(f"\n{info['title']}:")
        for method in info['methods'][:5]:
            print(f"\n  {method['name']}")
            print(f"    설명: {method['description']}")
            print(f"    예시: agent.{method['example']}")

# 특정 카테고리만 조회
account_methods = agent.get_all_methods(category="account")
print(f"\n계좌 관련 메서드: {account_methods['account']['count']}개")
```

### search_methods() - 메서드 검색

```python
# 키워드로 메서드 검색
results = agent.search_methods("order")

print("=== 'order' 관련 메서드 ===")
for method in results:
    print(f"\n{method['name']}")
    print(f"  카테고리: {method['category']}")
    print(f"  설명: {method['description']}")
    print(f"  예시: agent.{method['example']}")

# 다양한 검색 예시
search_keywords = ["price", "balance", "program", "minute"]

for keyword in search_keywords:
    results = agent.search_methods(keyword)
    print(f"\n'{keyword}' 검색 결과: {len(results)}개 메서드")
    for method in results[:3]:
        print(f"  - {method['name']}: {method['description']}")
```

### show_method_usage() - 메서드 사용법 표시

```python
# 특정 메서드 사용법 확인
methods_to_check = [
    "get_stock_price",
    "order_stock_cash",
    "get_account_balance",
    "calculate_support_resistance"
]

for method_name in methods_to_check:
    print(f"\n{'='*60}")
    agent.show_method_usage(method_name)
    print(f"{'='*60}")

# 메서드가 없는 경우
agent.show_method_usage("non_existent_method")
# 출력: 'non_existent_method' 메서드를 찾을 수 없습니다.
```

### classify_broker() - 거래원 분류

```python
# 거래원 성격 분류
brokers = [
    "모간스탠리",
    "키움증권",
    "CS증권",
    "NH투자",
    "골드만삭스",
    "미래에셋",
    "알 수 없는 증권"
]

for broker in brokers:
    classification = Agent.classify_broker(broker)
    print(f"{broker}: {classification}")

# 거래원 정보와 함께 사용
members = agent.get_member("005930")
if members:
    for member in members['output'][:5]:
        name = member['seln_mbcr_name']
        classification = Agent.classify_broker(name)
        print(f"{name} ({classification})")
```

---

## Rate Limiter 관리

### get_rate_limiter_status() - Rate Limiter 상태 조회

```python
# Rate Limiter 상태 확인
status = agent.get_rate_limiter_status()

if status:
    print("=== Rate Limiter 상태 ===")
    print(f"현재 초당 요청: {status.get('requests_per_second', 0)}")
    print(f"현재 분당 요청: {status.get('requests_per_minute', 0)}")
    print(f"초당 제한: {status.get('limit_per_second', 20)}")
    print(f"분당 제한: {status.get('limit_per_minute', 1000)}")
    print(f"백오프 배수: {status.get('backoff_multiplier', 1.0)}")
    print(f"총 요청 수: {status.get('total_requests', 0)}")
    print(f"제한 도달 횟수: {status.get('throttled_count', 0)}")
    print(f"평균 대기 시간: {status.get('avg_wait_time', 0):.3f}초")
else:
    print("Rate Limiter가 비활성화되어 있습니다")
```

### set_rate_limits() - Rate Limit 설정 변경

```python
# 보수적인 설정으로 변경
agent.set_rate_limits(
    requests_per_second=10,
    requests_per_minute=500,
    min_interval_ms=100
)
print("Rate limits 업데이트 완료")

# 특정 항목만 변경
agent.set_rate_limits(requests_per_second=15)  # 초당 제한만 변경
agent.set_rate_limits(min_interval_ms=50)  # 최소 간격만 변경

# 공격적인 설정 (주의!)
agent.set_rate_limits(
    requests_per_second=30,
    requests_per_minute=1500,
    min_interval_ms=10
)
```

### reset_rate_limiter() - Rate Limiter 초기화

```python
# Rate Limiter 초기화
print("초기화 전 상태:")
status = agent.get_rate_limiter_status()
if status:
    print(f"  총 요청: {status['total_requests']}")
    print(f"  제한 도달: {status['throttled_count']}")

agent.reset_rate_limiter()
print("\nRate Limiter 초기화 완료")

print("초기화 후 상태:")
status = agent.get_rate_limiter_status()
if status:
    print(f"  총 요청: {status['total_requests']}")
    print(f"  제한 도달: {status['throttled_count']}")
```

### enable_adaptive_rate_limiting() - 적응형 속도 조절

```python
# 적응형 속도 조절 활성화
agent.enable_adaptive_rate_limiting(True)
print("적응형 속도 조절 활성화")

# 대량 요청 테스트
import time

start_time = time.time()
for i in range(50):
    result = agent.get_stock_price("005930")
    if i % 10 == 9:
        status = agent.get_rate_limiter_status()
        if status:
            print(f"요청 {i+1}: 백오프 배수 = {status['backoff_multiplier']:.2f}")

elapsed = time.time() - start_time
print(f"\n50개 요청 완료: {elapsed:.2f}초")

# 적응형 속도 조절 비활성화
agent.enable_adaptive_rate_limiting(False)
print("적응형 속도 조절 비활성화")
```

---

## WebSocket 실시간

### websocket() - 실시간 데이터 수신

```python
# 기본 WebSocket 설정
ws = agent.websocket(
    stock_codes=["005930", "000660", "035720"],
    purchase_prices={
        "005930": (70000, 100),  # (매수가, 수량)
        "000660": (150000, 50),
        "035720": (50000, 20)
    },
    enable_index=True,
    enable_program_trading=True,
    enable_ask_bid=False
)

# 콜백 함수 정의
def on_price_update(data):
    """가격 업데이트 콜백"""
    code = data.get('stock_code')
    price = data.get('current_price')
    change = data.get('price_change')
    rate = data.get('change_rate')
    volume = data.get('volume')

    print(f"[{code}] {price:,}원 ({change:+,}원, {rate:+.2f}%)")
    print(f"  거래량: {volume:,}주")

    # 매수가 대비 수익률 계산
    if code in ws.purchase_prices:
        buy_price, qty = ws.purchase_prices[code]
        profit = (price - buy_price) * qty
        profit_rate = (price / buy_price - 1) * 100
        print(f"  수익: {profit:+,}원 ({profit_rate:+.2f}%)")

def on_index_update(data):
    """지수 업데이트 콜백"""
    index_name = data.get('index_name')
    value = data.get('index_value')
    change = data.get('index_change')

    print(f"[지수] {index_name}: {value:.2f} ({change:+.2f})")

def on_program_update(data):
    """프로그램매매 업데이트 콜백"""
    code = data.get('stock_code')
    buy_vol = data.get('program_buy')
    sell_vol = data.get('program_sell')
    net = buy_vol - sell_vol

    print(f"[프로그램] {code}: 순매수 {net:+,}주")

def on_orderbook_update(data):
    """호가 업데이트 콜백"""
    code = data.get('stock_code')
    ask1 = data.get('ask_price_1')
    bid1 = data.get('bid_price_1')
    spread = ask1 - bid1

    print(f"[호가] {code}: 매도1호가 {ask1:,}, 매수1호가 {bid1:,} (스프레드: {spread})")

# 콜백 함수 연결
ws.on_price_update = on_price_update
ws.on_index_update = on_index_update
ws.on_program_update = on_program_update
ws.on_orderbook_update = on_orderbook_update

# WebSocket 실행
try:
    print("실시간 데이터 수신 시작... (Ctrl+C로 종료)")
    ws.run()
except KeyboardInterrupt:
    print("\n실시간 데이터 수신 종료")
    ws.close()
```

### WebSocket 고급 활용

```python
import threading
import queue
import time
from datetime import datetime

class RealTimeTrader:
    """실시간 자동매매 시스템"""

    def __init__(self, agent):
        self.agent = agent
        self.ws = None
        self.trade_queue = queue.Queue()
        self.positions = {}
        self.running = True

    def start(self, stock_codes):
        """실시간 감시 시작"""
        # WebSocket 설정
        self.ws = self.agent.websocket(
            stock_codes=stock_codes,
            enable_index=True,
            enable_program_trading=True
        )

        # 콜백 설정
        self.ws.on_price_update = self.on_price_update

        # 거래 스레드 시작
        trade_thread = threading.Thread(target=self.process_trades)
        trade_thread.start()

        # WebSocket 실행
        try:
            self.ws.run()
        except KeyboardInterrupt:
            self.stop()

    def on_price_update(self, data):
        """가격 업데이트 처리"""
        code = data.get('stock_code')
        price = data.get('current_price')
        volume = data.get('volume')

        # 매매 신호 체크
        signal = self.check_signal(code, price, volume)

        if signal:
            self.trade_queue.put((code, price, signal))

    def check_signal(self, code, price, volume):
        """매매 신호 생성"""
        # 예시: 거래량 급증 시 매수
        if volume > 5000000:  # 500만주 이상
            return 'BUY'

        # 예시: 수익률 3% 달성 시 매도
        if code in self.positions:
            buy_price = self.positions[code]['price']
            profit_rate = (price / buy_price - 1) * 100
            if profit_rate >= 3.0:
                return 'SELL'

        return None

    def process_trades(self):
        """거래 처리 스레드"""
        while self.running:
            try:
                code, price, signal = self.trade_queue.get(timeout=1)

                if signal == 'BUY' and code not in self.positions:
                    # 매수 실행
                    result = self.agent.order_stock_cash(
                        ord_dv="buy",
                        pdno=code,
                        ord_dvsn="03",  # 최유리지정가
                        ord_qty="10",
                        ord_unpr="0"
                    )

                    if result and result.get('rt_cd') == '0':
                        self.positions[code] = {
                            'price': price,
                            'qty': 10,
                            'time': datetime.now()
                        }
                        print(f"[매수] {code} 10주 @ {price:,}원")

                elif signal == 'SELL' and code in self.positions:
                    # 매도 실행
                    result = self.agent.order_stock_cash(
                        ord_dv="sell",
                        pdno=code,
                        ord_dvsn="01",  # 시장가
                        ord_qty=str(self.positions[code]['qty']),
                        ord_unpr="0"
                    )

                    if result and result.get('rt_cd') == '0':
                        buy_price = self.positions[code]['price']
                        profit = (price - buy_price) * self.positions[code]['qty']
                        print(f"[매도] {code} {self.positions[code]['qty']}주 @ {price:,}원")
                        print(f"  수익: {profit:+,}원")
                        del self.positions[code]

            except queue.Empty:
                continue
            except Exception as e:
                print(f"거래 처리 오류: {e}")

    def stop(self):
        """시스템 종료"""
        self.running = False
        if self.ws:
            self.ws.close()
        print("실시간 자동매매 시스템 종료")

# 실시간 자동매매 실행
trader = RealTimeTrader(agent)
trader.start(["005930", "000660", "035720"])
```

---

## 완전한 예제: 종합 투자 시스템

```python
class InvestmentSystem:
    """종합 투자 관리 시스템"""

    def __init__(self, agent):
        self.agent = agent

    def daily_analysis(self):
        """일일 종합 분석"""
        print("="*60)
        print("일일 투자 분석 리포트")
        print("="*60)

        # 1. 계좌 현황
        self.analyze_account()

        # 2. 보유 종목 분석
        self.analyze_holdings()

        # 3. 시장 동향
        self.analyze_market()

        # 4. 추천 종목
        self.find_opportunities()

        # 5. 리스크 관리
        self.risk_management()

    def analyze_account(self):
        """계좌 분석"""
        balance = self.agent.get_account_balance()

        if balance and balance.get('rt_cd') == '0':
            summary = balance.get('output2', [{}])[0]

            total_asset = int(summary.get('tot_evlu_amt', 0))
            total_profit = int(summary.get('evlu_pfls_smtl', 0))
            profit_rate = float(summary.get('evlu_pfls_rt', 0))

            print("\n[계좌 현황]")
            print(f"총 자산: {total_asset:,}원")
            print(f"총 손익: {total_profit:,}원 ({profit_rate:+.2f}%)")

    def analyze_holdings(self):
        """보유 종목 분석"""
        df = self.agent.inquire_balance_rlz_pl()

        if df is not None and not df.empty:
            print("\n[보유 종목 분석]")

            # 수익률 TOP3
            top3 = df.nlargest(3, '수익률')
            print("\n수익률 상위:")
            for _, row in top3.iterrows():
                print(f"  {row['종목명']}: {row['수익률']:.2f}%")

            # 손실 종목
            losers = df[df['수익률'] < 0]
            if not losers.empty:
                print("\n주의 필요:")
                for _, row in losers.iterrows():
                    print(f"  {row['종목명']}: {row['수익률']:.2f}%")

    def analyze_market(self):
        """시장 동향 분석"""
        print("\n[시장 동향]")

        # KOSPI 지수
        kospi = self.agent.get_index_daily_price("0001", "D")
        if kospi and kospi.get('rt_cd') == '0':
            latest = kospi['output'][0]
            print(f"KOSPI: {float(latest['bstp_nmix_prpr']):.2f} "
                  f"({float(latest['prdy_ctrt']):+.2f}%)")

        # 상승률 상위
        gainers = self.agent.get_top_gainers()
        if gainers:
            print("\n급등주 TOP3:")
            for stock in gainers[:3]:
                print(f"  {stock['hts_kor_isnm']}: {float(stock['prdy_ctrt']):+.2f}%")

    def find_opportunities(self):
        """투자 기회 탐색"""
        print("\n[투자 기회]")

        # 조건검색 종목
        conditions = self.agent.get_condition_stocks()

        if conditions:
            recommendations = []

            for stock in conditions[:10]:
                code = stock['code']

                # 추가 분석
                investor = self.agent.get_stock_investor(code)
                if investor and investor.get('rt_cd') == '0':
                    foreign_net = int(investor['output']['frgn_ntby_qty'])

                    if foreign_net > 100000:  # 외국인 10만주 이상 순매수
                        recommendations.append({
                            'code': code,
                            'name': stock['name'],
                            'rate': stock.get('rate', 0),
                            'foreign_net': foreign_net
                        })

            # 추천 종목 출력
            for rec in recommendations[:3]:
                print(f"\n추천: {rec['name']} ({rec['code']})")
                print(f"  상승률: {rec['rate']:+.2f}%")
                print(f"  외국인: {rec['foreign_net']:,}주 순매수")

    def risk_management(self):
        """리스크 관리"""
        print("\n[리스크 관리]")

        df = self.agent.inquire_balance_rlz_pl()

        if df is not None and not df.empty:
            # 손절 대상
            stop_loss = df[df['수익률'] < -5.0]
            if not stop_loss.empty:
                print("\n손절 검토 필요:")
                for _, row in stop_loss.iterrows():
                    print(f"  {row['종목명']}: {row['수익률']:.2f}% ⚠️")

            # 비중 과다
            df['비중'] = df['평가금액'] / df['평가금액'].sum() * 100
            overweight = df[df['비중'] > 30]
            if not overweight.empty:
                print("\n비중 조절 필요:")
                for _, row in overweight.iterrows():
                    print(f"  {row['종목명']}: {row['비중']:.1f}% ⚠️")

            print("\n권장사항:")
            print("• 단일 종목 비중은 30% 이하로 유지")
            print("• -5% 손실 종목은 손절 검토")
            print("• +10% 수익 종목은 일부 익절 검토")

# 종합 분석 실행
system = InvestmentSystem(agent)
system.daily_analysis()
```

---

## 마무리

이 문서는 PyKIS의 모든 메서드에 대한 완전한 사용 예제를 포함하고 있습니다. 각 예제는 실제로 사용 가능한 코드이며, 오류 처리와 결과 확인을 포함하고 있습니다.

### 주요 팁

1. **API 호출 제한**: 초당 20회, 분당 1000회 제한을 준수하세요.
2. **토큰 관리**: Agent가 자동으로 토큰을 갱신하지만, 24시간마다 재발급됩니다.
3. **데이터 타입**: API 응답의 숫자 필드는 문자열로 반환되므로 int() 또는 float() 변환이 필요합니다.
4. **에러 처리**: 항상 rt_cd == '0'을 확인하여 성공 여부를 판단하세요.
5. **실전/모의 구분**: 실제 거래 전 모의투자 환경에서 충분히 테스트하세요.

### 추가 리소스

- [한국투자증권 OpenAPI 문서](https://apiportal.koreainvestment.com)
- [PyKIS GitHub](https://github.com/your-repo/pykis)
- 문의: support@example.com

*Version: PyKIS v0.1.22*
*Last Updated: 2025-01-17*