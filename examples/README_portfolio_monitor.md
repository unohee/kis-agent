#  포트폴리오 실시간 모니터링 시스템

잔고 조회 후 보유 종목들의 실시간 시세, VWAP 이격률, 프로그램 매매를 통합 모니터링하는 시스템입니다.

##  주요 기능

### 1. 💼 자동 포트폴리오 조회
- 계좌 잔고 자동 조회
- 보유 종목 자동 추출 및 등록
- 매입가, 보유 수량 자동 설정

### 2.  실시간 시세 모니터링
- 웹소켓 기반 실시간 체결 데이터 수신
- 현재가, 거래량 실시간 업데이트
- 손익률 실시간 계산

### 3.  VWAP 이격률 계산
- 60분 윈도우 기반 VWAP 계산
- 실시간 VWAP 이격률 표시
- 과거 분봉 데이터를 활용한 초기 VWAP 설정

### 4.  프로그램 매매 모니터링
- 실시간 프로그램 매매 비중 추적
- 매수/매도 비율 표시
- 순매수 비율 계산

### 5.  실시간 대시보드
- 5초마다 화면 자동 갱신
- 종목별 상세 정보 표시
- 포트폴리오 전체 손익 요약

##  사용법

### 기본 실행
```bash
# 가상환경 활성화
source ~/RTX_ENV/bin/activate

# 프로그램 실행
cd examples
python portfolio_realtime_monitor.py
```

### 설정 옵션
```python
# 5분마다 잔고 새로고침
monitor = PortfolioRealtimeMonitor(refresh_balance_interval=300)

# VWAP 윈도우 시간 조정 (분)
monitor.vwap_window_minutes = 120  # 2시간 윈도우

await monitor.run()
```

##  시스템 구조

### 클래스 다이어그램
```
PortfolioRealtimeMonitor
├── StockPosition (데이터클래스)
│   ├── 기본 정보 (코드, 종목명, 수량, 매입가)
│   ├── 실시간 데이터 (현재가, 거래량)
│   ├── VWAP 정보 (VWAP, 이격률)
│   ├── 프로그램매매 (매수/매도 비율)
│   └── 손익 정보 (평가금액, 손익률)
├── Agent (PyKIS)
├── WebSocket 클라이언트
└── 실시간 데이터 처리
```

### 데이터 흐름
```
1. 잔고 조회 → 보유종목 추출
2. 분봉 데이터 조회 → VWAP 초기값 설정
3. 웹소켓 연결 → 실시간 구독 등록
4. 실시간 데이터 수신 → 데이터 처리 및 계산
5. 대시보드 갱신 → 화면 표시
```

##  설정 가능 항목

### 1. 모니터링 간격
```python
refresh_balance_interval = 300  # 잔고 새로고침 간격 (초)
display_interval = 5           # 화면 갱신 간격 (초)
vwap_window_minutes = 60       # VWAP 계산 윈도우 (분)
```

### 2. 웹소켓 옵션
```python
self.ws_client = self.agent.websocket(
    stock_codes=stock_codes,
    enable_index=False,          # 지수 구독 여부
    enable_program_trading=True, # 프로그램매매 구독 여부
    enable_ask_bid=False        # 호가 구독 여부
)
```

### 3. 로깅 설정
```python
logging.basicConfig(
    level=logging.INFO,          # 로그 레벨
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('portfolio_monitor.log')  # 로그 파일
    ]
)
```

##  대시보드 화면

```
================================================================================
💼 포트폴리오 실시간 모니터링 대시보드
 마지막 업데이트: 2024-12-07 15:30:25
================================================================================
종목명         현재가      매입가     손익률     VWAP     이격률   프로그램     거래량
--------------------------------------------------------------------------------
삼성전자       75,000      70,000    +7.14%   74,500   +0.67%    +2.5%     1,234
SK하이닉스    130,000     125,000    +4.00%  128,500   +1.17%    -1.2%       856
POSCO홀딩스   415,000     400,000    +3.75%  412,000   +0.73%    +0.8%       342
--------------------------------------------------------------------------------
 총 투자금액:        15,750,000원
💎 총 평가금액:        16,425,000원
 총 손익금액:          +675,000원 (+4.29%)
================================================================================
```

##  커스터마이징

### 1. 새로운 지표 추가
```python
@dataclass
class StockPosition:
    # 기존 필드들...
    rsi: float = 0.0           # RSI 지표 추가
    moving_avg_20: float = 0.0 # 20일 이동평균 추가
    
    def calculate_rsi(self, prices: List[float]) -> float:
        # RSI 계산 로직
        pass
```

### 2. 알림 기능 추가
```python
def check_alert_conditions(self, position: StockPosition) -> None:
    """알림 조건 체크"""
    if abs(position.vwap_deviation) > 5.0:  # VWAP 5% 이상 이격
        self.send_alert(f"{position.name} VWAP 이격률 {position.vwap_deviation:.2f}%")
    
    if abs(position.profit_loss_rate) > 10.0:  # 손익률 10% 이상
        self.send_alert(f"{position.name} 손익률 {position.profit_loss_rate:.2f}%")
```

### 3. 데이터 저장 기능
```python
def save_monitoring_data(self) -> None:
    """모니터링 데이터 저장"""
    timestamp = datetime.now()
    
    for position in self.positions.values():
        data = {
            'timestamp': timestamp,
            'code': position.code,
            'price': position.current_price,
            'vwap': position.vwap,
            'deviation': position.vwap_deviation,
            'volume': position.volume
        }
        # CSV 또는 DB에 저장
        self.save_to_csv(data)
```

##  문제 해결

### 1. 웹소켓 연결 실패
```
 웹소켓 승인키 발급 실패
```
**해결방법**: `.env` 파일의 API 키와 시크릿 확인

### 2. 잔고 조회 실패
```
 잔고 조회 실패
```
**해결방법**: 계좌번호와 상품코드 확인, 정산시간(23:30~01:00) 피하기

### 3. 분봉 데이터 없음
```
 과거 분봉 데이터 로드 실패
```
**해결방법**: 장중 시간에 실행하거나 캐시된 분봉 데이터 확인

### 4. 메모리 사용량 증가
- VWAP 윈도우 시간 줄이기 (`vwap_window_minutes` 감소)
- 오래된 데이터 정리 주기 단축

##  성능 최적화

### 1. 데이터 관리
```python
# 오래된 데이터 정리
cutoff_time = current_time - timedelta(minutes=self.vwap_window_minutes)
self.price_volume_data[code] = [
    (p, v, t) for p, v, t in self.price_volume_data[code]
    if t >= cutoff_time
]
```

### 2. 웹소켓 최적화
```python
# 구독 요청 간격 조정
await asyncio.sleep(0.1)  # 요청 간격

# 타임아웃 설정
data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
```

### 3. 화면 갱신 최적화
```python
# 필요한 경우에만 화면 갱신
if (now - last_display_time).total_seconds() >= display_interval:
    self._display_portfolio_status()
```

##  확장 계획

### 1. 기술적 지표 추가
- RSI, MACD, 볼린저 밴드
- 이동평균선 (5, 20, 60일)
- 거래량 지표 (OBV, Volume Profile)

### 2. 알림 시스템
- 이메일/SMS 알림
- Slack/Discord 웹훅
- 텔레그램 봇 연동

### 3. 백테스팅 기능
- 과거 데이터 기반 성능 분석
- 전략 시뮬레이션
- 리스크 분석

### 4. 웹 인터페이스
- Flask/FastAPI 기반 웹 대시보드
- 실시간 차트 (Chart.js)
- 모바일 반응형 디자인

##  라이센스

이 프로젝트는 PyKIS 라이브러리를 기반으로 하며, 개인 투자 목적으로만 사용하시기 바랍니다.

## 🤝 기여하기

기능 개선이나 버그 리포트는 PyKIS 저장소에 이슈를 등록해주세요.

---

** 주의사항**: 
- 실제 투자에 사용하기 전 충분한 테스트를 진행하세요
- 시장 상황에 따라 데이터 지연이 발생할 수 있습니다
- 프로그램 매매 데이터는 실시간이 아닐 수 있습니다 