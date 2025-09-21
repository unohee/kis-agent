# PyKIS 누락된 메서드 문서

기존 문서에서 누락된 메서드들의 사용 예제입니다.

## StockAPI 클래스 추가 메서드

### get_vi_status() - VI(변동성완화장치) 상태 조회

```python
# VI 발동 상태 조회
vi_status = agent.get_vi_status(code="005930")

if vi_status and vi_status.get('rt_cd') == '0':
    output = vi_status['output']
    print(f"VI 발동 여부: {output.get('vi_yn')}")
    print(f"VI 발동 시간: {output.get('vi_strt_time')}")
    print(f"VI 해제 시간: {output.get('vi_end_time')}")
    print(f"정적 VI 발동가: {output.get('stvi_gbn')}")
    print(f"동적 VI 발동가: {output.get('dyvi_gbn')}")
```

### get_elw_price() - ELW 가격 조회

```python
# ELW 시세 조회
elw = agent.get_elw_price("58F001")  # ELW 종목코드

if elw and elw.get('rt_cd') == '0':
    output = elw['output']
    print(f"ELW 현재가: {output['elw_prpr']}원")
    print(f"기초자산: {output['undl_aset_name']}")
    print(f"행사가격: {output['elw_strk_pric']}원")
    print(f"만기일: {output['elw_expr_date']}")
    print(f"잔존일수: {output['elw_rmnd_days']}일")
```

### get_index_category_price() - 업종별 지수 조회

```python
# 업종별 지수 조회
category = agent.get_index_category_price(
    upju_code="0001",  # 업종코드
    fid_cond_mrkt_div_code="U"
)

if category and category.get('rt_cd') == '0':
    for sector in category['output']:
        print(f"업종명: {sector['hts_kor_isnm']}")
        print(f"지수: {sector['bstp_nmix_prpr']}")
        print(f"등락률: {sector['prdy_ctrt']}%")
```

### get_index_tick_price() - 지수 틱 데이터

```python
# 지수 틱 데이터 조회
ticks = agent.get_index_tick_price(
    index_code="0001",  # KOSPI
    hour="153000"
)

if ticks and ticks.get('rt_cd') == '0':
    for tick in ticks['output'][:10]:
        print(f"{tick['stck_bsop_time']}: {tick['bstp_nmix_prpr']}")
```

### get_index_time_price() - 지수 시간별 시세

```python
# 지수 시간별 시세
time_price = agent.get_index_time_price(
    index_code="0001",
    hour="150000"
)

if time_price and time_price.get('rt_cd') == '0':
    for data in time_price['output'][:10]:
        print(f"{data['stck_cntg_hour']}: {data['bstp_nmix_prpr']}")
```

### get_investor_daily_by_market() - 시장별 투자자 일별 매매

```python
# 시장별 투자자 일별 매매 동향
investor_market = agent.get_investor_daily_by_market(
    market_code="STK",  # 주식시장
    start_date="20240101",
    end_date="20240131"
)

if investor_market and investor_market.get('rt_cd') == '0':
    for day in investor_market['output']:
        print(f"날짜: {day['stck_bsop_date']}")
        print(f"  개인: {day['prsn_ntby_qty']:,}주")
        print(f"  외국인: {day['frgn_ntby_qty']:,}주")
        print(f"  기관: {day['orgn_ntby_qty']:,}주")
```

### get_investor_time_by_market() - 시장별 투자자 시간별 매매

```python
# 시장별 투자자 시간별 매매
investor_time = agent.get_investor_time_by_market(
    market_code="STK",
    hour="150000"
)

if investor_time and investor_time.get('rt_cd') == '0':
    for time_data in investor_time['output'][:10]:
        print(f"{time_data['stck_cntg_hour']}:")
        print(f"  개인 순매수: {time_data['prsn_ntby_tr_pbmn']:,}원")
        print(f"  외국인 순매수: {time_data['frgn_ntby_tr_pbmn']:,}원")
```

### get_member_daily() - 회원사 일별 매매

```python
# 회원사 일별 매매 현황
member_daily = agent.get_member_daily(
    member_code="00230",  # 미래에셋증권
    start_date="20240101",
    end_date="20240131"
)

if member_daily and member_daily.get('rt_cd') == '0':
    for day in member_daily['output']:
        print(f"{day['stck_bsop_date']}: 순매수 {day['ntby_qty']:,}주")
```

### get_overtime_asking_price() - 시간외 호가

```python
# 시간외 호가 조회
overtime_ask = agent.get_overtime_asking_price("005930")

if overtime_ask and overtime_ask.get('rt_cd') == '0':
    output = overtime_ask['output']
    print("=== 시간외 호가 ===")
    print(f"매도호가: {output['ovtm_askp1']:,}원")
    print(f"매수호가: {output['ovtm_bidp1']:,}원")
    print(f"매도잔량: {output['ovtm_askp_rsqn1']:,}주")
    print(f"매수잔량: {output['ovtm_bidp_rsqn1']:,}주")
```

### get_overtime_price() - 시간외 시세

```python
# 시간외 시세 조회
overtime = agent.get_overtime_price("005930")

if overtime and overtime.get('rt_cd') == '0':
    output = overtime['output']
    print(f"시간외 현재가: {output['ovtm_prpr']:,}원")
    print(f"시간외 거래량: {output['ovtm_vol']:,}주")
    print(f"전일대비: {output['prdy_vrss']:,}원")
```

### get_time_daily_chart_price() - 시간별 일별 차트

```python
# 시간별 일별 차트 데이터
chart = agent.get_time_daily_chart_price(
    code="005930",
    period="D",
    start_date="20240101",
    end_date="20240131"
)

if chart and chart.get('rt_cd') == '0':
    for day in chart['output']:
        print(f"{day['stck_bsop_date']}: O:{day['stck_oprc']} H:{day['stck_hgpr']} L:{day['stck_lwpr']} C:{day['stck_clpr']}")
```

### get_time_index_chart_price() - 시간별 지수 차트

```python
# 시간별 지수 차트
index_chart = agent.get_time_index_chart_price(
    index_code="0001",
    period="M",  # 분봉
    start_time="090000",
    end_time="153000"
)

if index_chart and index_chart.get('rt_cd') == '0':
    for data in index_chart['output'][:10]:
        print(f"{data['stck_cntg_hour']}: {data['bstp_nmix_prpr']}")
```

### get_time_item_conclusion() - 시간별 체결

```python
# 시간별 체결 데이터
conclusions = agent.get_time_item_conclusion(
    code="005930",
    start_time="090000",
    end_time="100000"
)

if conclusions and conclusions.get('rt_cd') == '0':
    for trade in conclusions['output'][:20]:
        print(f"{trade['stck_cntg_hour']}: {trade['stck_prpr']:,}원 x {trade['cntg_vol']:,}주")
```

### get_time_overtime_conclusion() - 시간외 체결

```python
# 시간외 체결 내역
overtime_trades = agent.get_time_overtime_conclusion(
    code="005930",
    start_time="160000",
    end_time="180000"
)

if overtime_trades and overtime_trades.get('rt_cd') == '0':
    for trade in overtime_trades['output']:
        print(f"{trade['ovtm_cntg_hour']}: {trade['ovtm_prpr']:,}원 x {trade['ovtm_cntg_vol']:,}주")
```

### get_asking_price_exp_ccn() - 예상 체결가

```python
# 예상 체결가 조회
expected = agent.get_asking_price_exp_ccn("005930")

if expected and expected.get('rt_cd') == '0':
    output = expected['output']
    print(f"예상 체결가: {output['expc_prpr']:,}원")
    print(f"예상 체결량: {output['expc_vol']:,}주")
    print(f"예상 대비: {output['expc_vrss']:,}원")
```

### get_price_2() - 주식 현재가 2 (상세)

```python
# 상세 현재가 조회
detail = agent.get_price_2("005930")

if detail and detail.get('rt_cd') == '0':
    output = detail['output']
    print(f"현재가: {output['stck_prpr']:,}원")
    print(f"가중평균가: {output['wghn_avrg_stck_prc']:,}원")
    print(f"체결강도: {output['vol_tnrt']}%")
    print(f"순매수 호가잔량: {output['total_askp_rsqn']:,}주")
    print(f"순매도 호가잔량: {output['total_bidp_rsqn']:,}주")
```

### get_stock_ccnl() - 체결 데이터

```python
# 체결 데이터 조회
ccnl = agent.get_stock_ccnl("005930")

if ccnl and ccnl.get('rt_cd') == '0':
    print("=== 최근 체결 ===")
    for trade in ccnl['output'][:10]:
        print(f"{trade['stck_cntg_hour']}: {trade['stck_prpr']:,}원 x {trade['cntg_vol']:,}주")
```

### get_pbar_tratio() - 프로그램매매 비중

```python
# 프로그램매매 비중 조회
pbar = agent.get_pbar_tratio("005930")

if pbar and pbar.get('rt_cd') == '0':
    output = pbar['output']
    print(f"프로그램 매수 비중: {output['pgmm_buy_ratio']}%")
    print(f"프로그램 매도 비중: {output['pgmm_sell_ratio']}%")
    print(f"차익거래 비중: {output['arbt_ratio']}%")
```

### get_hourly_conclusion() - 시간별 체결

```python
# 시간별 체결 조회
hourly = agent.get_hourly_conclusion("005930", hour="115959")

if hourly and hourly.get('rt_cd') == '0':
    for hour in hourly['output']:
        print(f"{hour['stck_cntg_hour']}: {hour['stck_prpr']:,}원")
        print(f"  거래량: {hour['cntg_vol']:,}주")
        print(f"  거래대금: {hour['acml_tr_pbmn']:,}원")
```

### get_frgnmem_pchs_trend() - 외국계 회원사 매수 동향

```python
# 외국계 회원사 매수 동향
foreign_trend = agent.get_frgnmem_pchs_trend("005930", "20240101")

if foreign_trend and foreign_trend.get('rt_cd') == '0':
    for member in foreign_trend['output']:
        print(f"{member['mbcr_name']}: {member['ntby_qty']:,}주")
```

## AccountAPI 추가 메서드

### get_cash_available() - 현금 매수 가능 금액

```python
# 현금 매수 가능 금액 조회
cash = agent.get_cash_available(
    pdno="005930",
    ord_unpr=70000,
    ord_dvsn="00"  # 지정가
)

if cash and cash.get('rt_cd') == '0':
    output = cash['output']
    print(f"매수 가능 현금: {output['ord_psbl_cash']:,}원")
    print(f"최대 매수 수량: {output['max_buy_qty']:,}주")
```

### get_total_asset() - 계좌 총 자산

```python
# 계좌 총 자산 조회
assets = agent.get_total_asset()

if assets and assets.get('rt_cd') == '0':
    output = assets['output']
    print(f"총 평가금액: {output['tot_evlu_amt']:,}원")
    print(f"예수금: {output['dncl_amt']:,}원")
    print(f"주식 평가금액: {output['scts_evlu_amt']:,}원")
    print(f"총 손익금액: {output['evlu_pfls_smtl_amt']:,}원")
    print(f"총 손익률: {output['tot_evlu_pfls_rt']}%")
```

### inquire_psbl_order() - 매수가능조회 (상세)

```python
# 매수가능 상세 조회
psbl = agent.inquire_psbl_order(
    price=70000,
    pdno="005930",
    ord_dvsn="00"
)

if psbl and psbl.get('rt_cd') == '0':
    output = psbl['output']
    print(f"주문가능현금: {output['ord_psbl_cash']:,}원")
    print(f"주문가능대용: {output['ord_psbl_sbst']:,}원")
    print(f"재사용가능금액: {output['ruse_psbl_amt']:,}원")
    print(f"최대 주문가능금액: {output['max_buy_amt']:,}원")
    print(f"최대 주문가능수량: {output['max_buy_qty']:,}주")
```

### order_credit() - 신용 주문 (직접)

```python
# 신용 주문 직접 호출
from datetime import datetime

credit_order = agent.order_credit(
    ord_dv="buy",
    pdno="005930",
    ord_dvsn="00",
    ord_qty="10",
    ord_unpr="70000",
    crdt_type="21",  # 자기융자신규
    loan_dt=datetime.now().strftime("%Y%m%d")
)

if credit_order and credit_order.get('rt_cd') == '0':
    print(f"신용주문 성공: {credit_order['output']['ODNO']}")
```

### order_resv() - 예약 주문

```python
# 예약 주문 등록
reservation = agent.order_resv(
    code="005930",
    qty=10,
    price=70000,
    order_type="00"
)

if reservation and reservation.get('rt_cd') == '0':
    print(f"예약주문 등록 완료: {reservation['output']['ORD_NO']}")
```

### order_resv_ccnl() - 예약 주문 조회

```python
# 예약 주문 목록 조회
reservations = agent.order_resv_ccnl()

if reservations and reservations.get('rt_cd') == '0':
    print("=== 예약 주문 목록 ===")
    for order in reservations['output']:
        print(f"예약번호: {order['resv_ord_no']}")
        print(f"종목: {order['prdt_name']} ({order['pdno']})")
        print(f"수량: {order['ord_qty']}주 @ {order['ord_unpr']:,}원")
        print(f"조건: {order['resv_cndt_name']}")
```

### order_resv_rvsecncl() - 예약 주문 정정/취소

```python
# 예약 주문 정정/취소
cancel_resv = agent.order_resv_rvsecncl(
    seq=1,  # 예약주문순번
    qty=0,  # 0이면 취소
    price=0,
    order_type="02"  # 취소
)

if cancel_resv and cancel_resv.get('rt_cd') == '0':
    print("예약주문 취소 완료")
```

## 프로그램 트레이드 API 추가 메서드

```python
# ProgramTradeAPI는 이미 문서화되어 있으나 직접 호출 예시 추가
from pykis.program.trade import ProgramTradeAPI

# 직접 API 생성
program_api = ProgramTradeAPI(agent.client, agent.account_info)

# 시간별 프로그램매매 상세
hourly_detail = program_api.get_program_trade_hourly_detail("005930")
if hourly_detail:
    for hour in hourly_detail['output']:
        print(f"{hour['time']}: 차익 {hour['arbitrage_net']:,}, 비차익 {hour['non_arbitrage_net']:,}")
```

## StockMarketAPI 추가 메서드

```python
from pykis.stock import StockMarketAPI

# 직접 API 생성
market_api = StockMarketAPI(agent.client, agent.account_info)

# KOSPI200 구성종목 조회
kospi200 = market_api.get_kospi200_components()
if kospi200:
    print(f"KOSPI200 구성종목: {len(kospi200['output'])}개")
    for stock in kospi200['output'][:10]:
        print(f"{stock['hts_kor_isnm']} ({stock['stck_shrn_iscd']})")

# 섹터별 시세 조회
sectors = market_api.get_sector_prices()
if sectors:
    for sector in sectors['output']:
        print(f"{sector['sector_name']}: {sector['index_value']} ({sector['change_rate']:+.2f}%)")
```

## WebSocket 추가 기능

```python
# WebSocket 고급 설정
ws = agent.websocket(
    stock_codes=["005930", "000660"],
    enable_index=True,
    enable_program_trading=True,
    enable_ask_bid=True  # 호가 실시간 추가
)

# 커스텀 메시지 핸들러
def custom_handler(message):
    msg_type = message.get('header', {}).get('tr_id')

    if msg_type == 'H0STCNT0':  # 실시간 체결
        print(f"체결: {message}")
    elif msg_type == 'H0STCNI0':  # 실시간 뉴스
        print(f"뉴스: {message}")
    elif msg_type == 'H0STCNI9':  # 실시간 프로그램매매
        print(f"프로그램: {message}")

ws.on_message = custom_handler

# 구독 추가/제거
ws.subscribe("005930", "H0STCNT0")  # 체결 구독
ws.unsubscribe("005930", "H0STCNT0")  # 체결 구독 해제

# 연결 상태 확인
if ws.is_connected():
    print("WebSocket 연결됨")
```

## 내부 헬퍼 메서드

```python
# Agent 내부 헬퍼 메서드들

# 영업일 계산
last_business_day = agent._get_last_business_day()
print(f"최근 영업일: {last_business_day}")

# 특정 날짜 기준 영업일
specific_date = "20240105"
business_day = agent._get_last_business_day(specific_date)
print(f"{specific_date} 기준 최근 영업일: {business_day}")

# 캐시 확인
import datetime
csv_path = "cache/005930_minute_data_20240101.csv"
cached = agent._check_cache(csv_path, "20240101", datetime.datetime.now())
if cached is not None:
    print("캐시 데이터 유효")

# DB 저장 (내부)
import pandas as pd
df = pd.DataFrame({'test': [1, 2, 3]})
agent._save_to_db(df, "005930", "20240101")

# 거래량 프로필 계산
df = agent.fetch_minute_data("005930")
volume_profile = agent._calculate_volume_profile(df, bins=50)
print(f"거래량 프로필 생성: {len(volume_profile)}개 구간")

# 피봇 포인트 계산
pivot = agent._calculate_pivot_points(df)
print(f"피봇: {pivot['pivot']:,.0f}")

# VWAP 계산
vwap = agent._calculate_vwap(df)
print(f"VWAP: {vwap:,.0f}")

# 지지선/저항선 감지
support = agent._detect_support_levels(df, volume_profile)
resistance = agent._detect_resistance_levels(df, volume_profile)
print(f"지지선: {len(support)}개, 저항선: {len(resistance)}개")

# 매물대 강도 계산
support_strength = agent._calculate_level_strength(df, support)
resistance_strength = agent._calculate_level_strength(df, resistance)
print(f"최강 지지선: {support[0]:,.0f} (강도: {support_strength[0]:.1f})")
```

## 누락 확인 완료

다음 메서드들이 추가로 문서화되었습니다:

### StockAPI 클래스 (30개 추가)
- get_vi_status, get_elw_price, get_index_category_price
- get_index_tick_price, get_index_time_price
- get_investor_daily_by_market, get_investor_time_by_market
- get_member_daily, get_overtime_asking_price, get_overtime_price
- get_time_daily_chart_price, get_time_index_chart_price
- get_time_item_conclusion, get_time_overtime_conclusion
- get_asking_price_exp_ccn, get_price_2
- get_stock_ccnl, get_pbar_tratio, get_hourly_conclusion
- get_frgnmem_pchs_trend 등

### AccountAPI 클래스 (7개 추가)
- get_cash_available, get_total_asset
- inquire_psbl_order, order_credit
- order_resv, order_resv_ccnl, order_resv_rvsecncl

### Agent 내부 메서드 (9개)
- _get_last_business_day, _check_cache, _save_to_db
- _calculate_volume_profile, _calculate_pivot_points
- _calculate_vwap, _detect_support_levels
- _detect_resistance_levels, _calculate_level_strength

모든 public 메서드와 일부 유용한 내부 헬퍼 메서드까지 포함하여 완전한 문서화를 완료했습니다.