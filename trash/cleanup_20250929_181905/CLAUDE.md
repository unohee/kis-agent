# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyKIS is a Python wrapper for the Korea Investment & Securities (한국투자증권) OpenAPI. It provides a comprehensive interface for Korean stock market trading, real-time data streaming, and portfolio management.

**Key Features:**
- Unified Agent interface for all KIS API functionality
- Advanced rate limiting with adaptive backoff mechanisms
- Real-time WebSocket data streaming
- Comprehensive caching system with TTL management
- Multi-format trading report generation (Excel exports)
- Support for KOSPI, KOSDAQ, and NXT markets

## Core Architecture

### Agent-Centric Design
The main entry point is the `Agent` class (`pykis/core/agent.py`) which orchestrates all functionality:

```python
from pykis import Agent

agent = Agent(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="YOUR_ACCOUNT_NO",
    account_code="01"  # 계좌상품코드
)
```

### Module Structure
- **`pykis/core/`**: Core infrastructure (auth, client, rate limiting, caching)
- **`pykis/account/`**: Account balance and transaction APIs
- **`pykis/stock/`**: Market data, pricing, and trading APIs
- **`pykis/websocket/`**: Real-time data streaming infrastructure
- **`pykis/program/`**: Program trading and institutional flow data
- **`pykis/utils/`**: Utilities including Excel report generation

### Key Components

**Rate Limiter (`pykis/core/rate_limiter.py`)**:
- Default limits: 18 RPS / 900 RPM (conservative vs API spec of 20/1000)
- Adaptive backoff on errors with priority-based throttling
- Tracks performance metrics and provides runtime adjustment

**Client Architecture (`pykis/core/client.py`)**:
- Centralized HTTP client with automatic authentication
- Built-in caching layer with configurable TTL
- Comprehensive API endpoint mapping for all KIS services

**WebSocket System (`pykis/websocket/`)**:
- Factory pattern for different subscription types
- Event-driven message handling with async/await support
- Multi-stock real-time monitoring with automatic reconnection

## Environment Setup

**Virtual Environment**:
```bash
source ~/RTX_ENV/bin/activate  # Required for all Python operations
```

**API Configuration**:
Set environment variables (no .env file support):
```bash
export KIS_APP_KEY="YOUR_APP_KEY"
export KIS_APP_SECRET="YOUR_APP_SECRET"
export KIS_ACCOUNT_NO="YOUR_ACCOUNT_NO"
export KIS_ACCOUNT_CODE="01"
```

**Installation**:
```bash
pip install -e ".[dev]"  # Development dependencies
pip install -e ".[websocket]"  # WebSocket support
pip install -e ".[all]"  # All optional dependencies
```

## Development Commands

**Testing**:
```bash
# Full test suite
pytest tests/ -v --cov=pykis

# Specific test categories
pytest tests/test_cache_integration.py tests/test_cache_realworld.py tests/test_cache_ttl.py tests/test_exception_handling.py -v

# Single test file
pytest tests/test_market_data.py -v

# With coverage report
pytest tests/ -v --cov=pykis --cov-report=xml --cov-report=term-missing
```

**Code Quality**:
```bash
# Format code
black pykis/ tests/ --diff
isort pykis/ tests/ --diff

# Lint
flake8 pykis/ tests/

# Type checking
mypy pykis/ --ignore-missing-imports
```

**Build**:
```bash
python -m build  # Creates wheel and source distribution
```

## API Rate Limiting

The KIS API has strict rate limits that have been empirically tested:
- **Official spec**: 20 RPS / 1000 RPM
- **Stable limits**: 15-18 RPS / 800-900 RPM
- **Cache hit rate**: 80-95% (significantly reduces API calls)

Rate limiter configuration can be customized:
```python
agent = Agent(
    ...,
    rate_limiter_config={
        'requests_per_second': 15,  # Conservative for production
        'requests_per_minute': 800,
        'min_interval_ms': 60,
        'burst_size': 5
    }
)
```

## Testing Strategy

**Test Structure**:
- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests requiring API connectivity
- `tests/utils/`: Utility function tests
- `examples/`: Functional examples that serve as integration tests

**Key Test Files**:
- `test_exception_handling.py`: Exception handling and error recovery
- `test_cache_*.py`: Caching system validation
- `test_market_data.py`: Market data API validation
- `utils/test_trading_report.py`: Excel export functionality

**Running Tests with API**:
Most tests can run without API keys, but integration tests require:
```bash
export APP_KEY="test_key"  # Note: different variable names for tests
export APP_SECRET="test_secret"
export ACC_NO="test_account"
```

## WebSocket Usage

Real-time data streaming example:
```python
# Multi-stock monitoring
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],  # Samsung, Naver
    enable_index=True,                 # Market indices
    enable_program_trading=True,       # Program trading data
    enable_ask_bid=True               # Order book data
)

import asyncio
asyncio.run(ws_client.start())
```

## Common Patterns

**Market Data Retrieval**:
```python
# Current price (cached)
price = agent.get_stock_price("005930")

# Historical minute data (4-day chunks, SQLite cached)
minute_data = agent.fetch_minute_data("005930", "20250715")

# Order book
orderbook = agent.get_orderbook("005930")
```

**Trading Operations**:
```python
# Cash order
result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")

# Credit order
result = agent.order_stock_credit("buy", "009470", "21", "00", "1", "12000", loan_dt="20250921")
```

**Report Generation**:
```python
from pykis.utils.trading_report import generate_trading_report

report_path = generate_trading_report(
    agent.client,
    {'CANO': 'account_no', 'ACNT_PRDT_CD': '01'},
    '20250101', '20250131',
    output_path='trading_history.xlsx'
)
```

## CI/CD Pipeline

GitHub Actions workflows:
- **`ci.yml`**: Basic testing across Python 3.8, 3.11, 3.12
- **`ci-cd.yml`**: Full pipeline with security scanning, coverage, and build

**Development workflow**:
1. Create feature branch
2. Run tests locally: `pytest tests/ -v`
3. Check code quality: `black --check` + `isort --check` + `flake8`
4. Push and create PR
5. CI automatically runs tests and quality checks

## Important Notes

**Rate Limiting**: Always use the built-in rate limiter. The KIS API will block requests if limits are exceeded.

**Caching**: Heavy use of intelligent caching reduces API calls by 80-95%. Cache keys are based on request parameters and have appropriate TTLs.

**Error Handling**: All API calls use the `@exception_handler` decorator for consistent error handling and automatic retries.

**Environment Variables**: The project intentionally does not support .env files. Use environment variables or pass credentials directly to Agent.

**Market Coverage**: Supports KOSPI, KOSDAQ, and NXT markets with unified API interfaces.

**WebSocket Reliability**: WebSocket connections include automatic reconnection, heartbeat monitoring, and graceful error recovery.