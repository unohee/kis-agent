# Rate Limiter 설정 가이드

## 📊 기본 설정 (v1.7.x 기준)

kis-agent의 Rate Limiter는 KIS 공식 한도(20 RPS / 1000 RPM) 대비 충분한 안전
마진을 두고, 동시 호출 시에도 sliding window 위반이 발생하지 않도록 설계되어
있습니다.

### 기본값
```python
# kis_agent/core/rate_limiter.py의 DEFAULT_* 상수
{
    'requests_per_second': 15,   # 공식 한도 20의 75% (5회 여유)
    'requests_per_minute': 800,  # 공식 한도 1000의 80% (200회 여유)
    'min_interval_ms': 70,       # 15 RPS의 이론적 67ms + 3ms jitter
    'burst_size': 3,             # priority>=1 시 effective RPS = 18
    'enable_adaptive': True      # 적응형 백오프 활성화
}
```

### 안전 보장

- **공식 한도 자동 클램프**: `RateLimiter(requests_per_second=25)`처럼 공식 한도를
  초과하는 값을 주면 자동으로 20으로 clamp됩니다 (RPM도 동일).
- **동시 호출 안전**: 다수의 스레드가 동시에 acquire()를 호출해도 sliding window
  내 요청 수가 한도를 넘지 않습니다 (1ms safety padding + slot reservation).
- **Lock-free sleep**: `acquire()`의 `time.sleep()`이 lock 바깥에서 실행되어 한
  스레드의 대기가 다른 스레드를 블록하지 않습니다.
- **전역 싱글턴**: 모든 KISClient/Agent가 동일한 RateLimiter 인스턴스를 공유합니다.

## 🎯 사용 시나리오별 권장 설정

### 1. 안정성 최우선 (Production)
```python
agent = Agent(
    app_key="YOUR_KEY",
    app_secret="YOUR_SECRET",
    account_no="YOUR_ACCOUNT",
    account_code="01",
    rate_limiter_config={
        'requests_per_second': 15,
        'requests_per_minute': 800,
        'min_interval_ms': 60,
        'burst_size': 5
    }
)
```

### 2. 균형 설정 (기본값 사용)
```python
agent = Agent(
    app_key="YOUR_KEY",
    app_secret="YOUR_SECRET",
    account_no="YOUR_ACCOUNT",
    account_code="01"
    # rate_limiter_config 생략 시 기본값 사용
)
```

### 3. 성능 최적화 (개발/테스트)
```python
agent = Agent(
    app_key="YOUR_KEY",
    app_secret="YOUR_SECRET",
    account_no="YOUR_ACCOUNT",
    account_code="01",
    rate_limiter_config={
        'requests_per_second': 20,  # API 최대치
        'requests_per_minute': 1000, # API 최대치
        'min_interval_ms': 40,       # 약간 더 짧은 간격
        'burst_size': 15
    }
)
```

### 4. 실시간 데이터 처리
```python
# 호가, 체결 등 실시간 데이터는 캐시가 안되므로 보수적 설정
agent = Agent(
    app_key="YOUR_KEY",
    app_secret="YOUR_SECRET",
    account_no="YOUR_ACCOUNT",
    account_code="01",
    rate_limiter_config={
        'requests_per_second': 10,
        'requests_per_minute': 500,
        'min_interval_ms': 100,
        'burst_size': 3
    }
)
```

## ⚙️ 고급 설정

### 적응형 백오프 메커니즘
Rate Limiter는 에러 발생 시 자동으로 속도를 조절합니다:

```python
# 에러 발생 시 자동 백오프
- 1번째 에러: 대기시간 1.5배
- 2번째 에러: 대기시간 2.0배
- 3번째 에러: 대기시간 3.0배
- 최대 백오프: 5.0배

# 성공 시 점진적 복구
- 연속 성공 시 백오프 10%씩 감소
- 최소값 1.0배로 복귀
```

### Rate Limiter 비활성화
테스트 목적으로 Rate Limiter를 비활성화할 수 있습니다:

```python
agent = Agent(
    app_key="YOUR_KEY",
    app_secret="YOUR_SECRET",
    account_no="YOUR_ACCOUNT",
    account_code="01",
    enable_rate_limiter=False  # ⚠️ 주의: API 제한 초과 가능
)
```

## 📈 성능 모니터링

### Rate Limiter 상태 확인
```python
# 현재 상태 조회
if hasattr(agent, 'client') and hasattr(agent.client, 'rate_limiter'):
    stats = agent.client.rate_limiter.get_current_rate()
    print(f"현재 초당 요청: {stats['requests_per_second']}")
    print(f"현재 분당 요청: {stats['requests_per_minute']}")
    print(f"스로틀 횟수: {stats['throttled_count']}")
    print(f"평균 대기시간: {stats['avg_wait_time']:.3f}초")
    print(f"백오프 배수: {stats['backoff_multiplier']}x")
```

### 런타임 설정 변경
```python
# 런타임에 제한값 변경
agent.client.rate_limiter.set_limits(
    requests_per_second=12,
    requests_per_minute=600,
    min_interval_ms=80
)
```

## 🚨 주의사항

1. **캐시와 함께 사용**: Rate Limiter는 캐시와 함께 사용할 때 가장 효과적입니다
2. **멀티스레드**: 스레드별로 독립적인 Agent 인스턴스 사용 권장
3. **에러 처리**: Rate Limit 에러 시 자동 재시도하지만, 연속 실패 시 대기 필요
4. **모니터링**: Production에서는 Rate Limiter 통계를 주기적으로 모니터링

## 📊 테스트 결과 요약

2025년 9월 21일 실측 결과:
- **API 스펙**: 20 RPS / 1000 RPM
- **안정적 한계**: 15-18 RPS / 800-900 RPM
- **캐시 효과**: API 호출 80-95% 감소
- **권장 설정**: 15 RPS / 800 RPM (Production)

자세한 내용은 [RATE_LIMIT_ANALYSIS.md](../RATE_LIMIT_ANALYSIS.md) 참조