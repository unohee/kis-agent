# 예제 모음

`examples/` 디렉토리에 32개의 실전 예제가 포함되어 있습니다.

## 기본 사용법

| 파일 | 설명 |
|:---|:---|
| `basic_usage.py` | 기본 사용법 (시세 조회, 잔고, 주문) |
| `async_auth_example.py` | 비동기 인증 예제 |
| `run.py` | 통합 실행 스크립트 |
| `pykis.ipynb` | Jupyter 노트북 |

## 시세/차트

| 파일 | 설명 |
|:---|:---|
| `daily_price_pagination_example.py` | 일봉 데이터 페이지네이션 (100건 우회) |
| `minute_candle_crawler.py` | 분봉 데이터 수집기 |
| `index_tickprice_example.py` | 지수 틱 시세 |
| `daily_index_chart_price_example.py` | 지수 일봉 차트 |

## 선물/옵션

| 파일 | 설명 |
|:---|:---|
| `future_option_price_example.py` | 선물옵션 가격 조회 |
| `future_orderbook_example.py` | 선물옵션 호가 조회 |
| `futures_code_generator_example.py` | 선물 종목코드 자동 생성 |
| `calculate_basis.py` | 베이시스 계산 |
| `test_kospi200_basis.py` | KOSPI200 베이시스 테스트 |

## 해외주식

| 파일 | 설명 |
|:---|:---|
| `overseas_stock_example.py` | 해외주식 시세/주문 |

## WebSocket 실시간

| 파일 | 설명 |
|:---|:---|
| `websocket_enhanced_example.py` | 향상된 WebSocket |
| `websocket_multi_subscribe.py` | 다중 구독 |
| `refactored_websocket_example.py` | 리팩토링 WebSocket |

## 분석/모니터링

| 파일 | 설명 |
|:---|:---|
| `program_trade_analysis.py` | 프로그램 매매 분석 |
| `portfolio_realtime_monitor.py` | 포트폴리오 실시간 모니터 |
| `StockMonitor.py` | 주식 모니터 |
| `pbar_tratio_demo.py` | 매물대/거래비중 데모 |
| `test_pbar_tratio.py` | 매물대/거래비중 테스트 |
| `test_pbar_tratio_with_chart.py` | 차트 포함 매물대 |

## 계좌/거래

| 파일 | 설명 |
|:---|:---|
| `export_trading_history.py` | 거래내역 Excel 내보내기 |
| `list_interest_groups.py` | 관심종목 그룹 목록 |
| `test_interest_stocks.py` | 관심종목 테스트 |

## 성능 테스트

| 파일 | 설명 |
|:---|:---|
| `test_rate_limiter_live.py` | Rate Limiter 실시간 테스트 |
| `test_portfolio_monitor.py` | 포트폴리오 모니터 테스트 |
