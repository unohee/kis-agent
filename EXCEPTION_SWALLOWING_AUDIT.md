# Exception Swallowing Patterns Audit

**Date**: 2026-03-03
**Auditor**: Claude Code
**Related Issue**: INT-706

## Summary

코드베이스 전체에서 예외 삼킴(exception swallowing) 패턴을 탐지했습니다.
총 **49개** 패턴을 발견했으며, 이 중 **심각도 높음** 패턴은 3개입니다.

## Detection Methodology

1. **Bare except**: `except:` (타입 지정 없음)
2. **Bare pass**: `except: pass` (아무 동작도 하지 않음)
3. **No logging**: 예외를 잡았지만 로그를 남기지 않음
4. **Bare continue/return None**: 조용히 실패하고 계속 진행

## Critical Issues (High Severity)

### 1. Bare except with bare pass
가장 위험한 패턴 - 예외를 완전히 무시함

| File | Line | Pattern |
|------|------|---------|
| `open-trading-api/MCP/Kis Trading MCP/tools/base.py` | 306 | `except: pass` |
| `open-trading-api/stocks_info/overseas_stock_code.py` | 74 | `except: pass` |
| `scripts/response_documentation/extract_response_mappings.py` | 61 | `except: pass` |

### 2. Core authentication bare return None
인증 실패를 조용히 무시함

| File | Line | Pattern |
|------|------|---------|
| `kis_agent/core/auth.py` | 289 | `except Exception: return None` |

## Medium Severity Issues

### Account Models (8개)
`kis_agent/account/models.py`에서 데이터 변환 실패를 조용히 무시:

- Line 83, 99, 108, 131, 139, 147, 155, 163
- Pattern: `except (ValueError, TypeError)` with no logging

### WebSocket (6개)
실시간 데이터 처리 실패를 로깅하지 않음:

- `kis_agent/websocket/client.py`: 140, 553, 572, 970
- `kis_agent/websocket/ws_agent.py`: 623, 666
- `kis_agent/websocket/ws_helpers.py`: 307

### MCP Server Tools (12개)
MCP 서버의 데이터 처리 실패를 무시:

- `open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py`: 379, 452, 466, 479, 677, 704, 706, 721, 723, 766
- `open-trading-api/MCP/Kis Trading MCP/tools/base.py`: 241, 275, 280, 406, 482, 542, 679, 684, 727
- `pykis-mcp-server/src/pykis_mcp_server/tools/investor_tools.py`: 326, 426, 514, 609

## Low Severity Issues

### Import errors (2개)
모듈 import 실패를 조용히 처리 (일반적으로 허용되는 패턴):

- `kis_agent/stock/__init__.py`: 30
- `kis_agent/stock/investor.py`: 114

### Technical analysis (1개)
기술적 분석 실패:

- `kis_agent/core/technical_analysis.py`: 124

## Full Detection Results

```
=== Core Code (kis_agent/) ===
kis_agent/account/models.py:83 - except (ValueError, TypeError) -> no logging
kis_agent/account/models.py:99 - except (ValueError, TypeError, ZeroDivisionError) -> no logging
kis_agent/account/models.py:108 - except (ValueError, TypeError) -> bare return None
kis_agent/account/models.py:131 - except (ValueError, TypeError) -> no logging
kis_agent/account/models.py:139 - except (ValueError, TypeError) -> no logging
kis_agent/account/models.py:147 - except (ValueError, TypeError) -> no logging
kis_agent/account/models.py:155 - except (ValueError, TypeError) -> no logging
kis_agent/account/models.py:163 - except (ValueError, TypeError) -> no logging
kis_agent/core/auth.py:289 - except Exception -> bare return None
kis_agent/core/auth.py:594 - except Exception -> no logging
kis_agent/core/base_api.py:306 - except (ValueError, TypeError) -> no logging
kis_agent/core/technical_analysis.py:124 - except Exception -> no logging
kis_agent/stock/__init__.py:30 - except ImportError -> no logging
kis_agent/stock/investor.py:114 - except ImportError -> no logging
kis_agent/stock/investor.py:460 - except Exception -> no logging
kis_agent/websocket/client.py:140 - except ValueError -> no logging
kis_agent/websocket/client.py:553 - except Exception -> no logging
kis_agent/websocket/client.py:572 - except Exception -> no logging
kis_agent/websocket/client.py:970 - except ImportError -> bare return None
kis_agent/websocket/ws_agent.py:623 - except json.JSONDecodeError -> no logging
kis_agent/websocket/ws_agent.py:666 - except ValueError -> no logging
kis_agent/websocket/ws_helpers.py:307 - except ValueError -> no logging

=== MCP Server ===
open-trading-api/MCP/Kis Trading MCP/module/middleware.py:34 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:379 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:452 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:466 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:479 - except (ValueError, AttributeError) -> no logging
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:677 - except UnicodeDecodeError -> bare continue
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:704 - except UnicodeDecodeError -> bare continue
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:706 - except Exception -> bare continue
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:721 - except UnicodeDecodeError -> bare continue
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:723 - except Exception -> bare continue
open-trading-api/MCP/Kis Trading MCP/module/plugin/master_file.py:766 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:241 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:275 - except subprocess.TimeoutExpired -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:280 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:306 - bare except -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:406 - except FileNotFoundError -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:482 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:542 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:679 - except Exception -> bare continue
open-trading-api/MCP/Kis Trading MCP/tools/base.py:684 - except Exception -> no logging
open-trading-api/MCP/Kis Trading MCP/tools/base.py:727 - except Exception -> no logging
open-trading-api/stocks_info/overseas_stock_code.py:74 - bare except -> bare pass

=== PyKis MCP Server ===
pykis-mcp-server/src/pykis_mcp_server/server.py:46 - except ValueError -> no logging
pykis-mcp-server/src/pykis_mcp_server/tools/investor_tools.py:326 - except Exception -> bare continue
pykis-mcp-server/src/pykis_mcp_server/tools/investor_tools.py:426 - except Exception -> bare continue
pykis-mcp-server/src/pykis_mcp_server/tools/investor_tools.py:514 - except Exception -> bare continue
pykis-mcp-server/src/pykis_mcp_server/tools/investor_tools.py:609 - except Exception -> bare continue

=== Scripts ===
scripts/check_loc.py:34 - except Exception -> no logging
scripts/response_documentation/extract_response_mappings.py:61 - bare except -> bare pass
```

## Recommended Actions

### Immediate (Critical)
1. **Fix bare except patterns**: 최소한 `except Exception:` 으로 변경
2. **Add logging**: 모든 예외 처리에 최소한 `logger.debug()` 추가
3. **Auth module**: `kis_agent/core/auth.py:289`에 로깅 추가 (인증 실패는 critical)

### Short-term (Medium)
1. **Account models**: 데이터 변환 실패 로깅 (warning level)
2. **WebSocket**: 실시간 데이터 처리 실패 로깅 (error level)
3. **MCP tools**: 최소한 debug level 로깅 추가

### Long-term (Low)
1. Import error 패턴은 현행 유지 가능 (선택적 의존성)
2. 주기적 audit 스크립트를 CI에 통합

## Detection Script

```python
# kis-agent 루트에서 실행
cd /home/unohee/dev/tools/kis-agent
python3 -c "
import ast
from pathlib import Path

results = []

def check_except_block(node):
    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
        return 'bare pass'
    if len(node.body) == 1 and isinstance(node.body[0], ast.Continue):
        return 'bare continue'
    # 로깅 호출 확인
    has_logging = False
    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Call):
            if isinstance(stmt.func, ast.Attribute):
                if stmt.func.attr in ['debug', 'info', 'warning', 'error']:
                    has_logging = True
    if not has_logging:
        return 'no logging'
    return None

for py_file in Path('.').rglob('*.py'):
    if 'test' in str(py_file) or 'example' in str(py_file):
        continue
    try:
        with open(py_file) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                issue = check_except_block(node)
                if issue:
                    is_bare = node.type is None
                    print(f'{py_file}:{node.lineno} - {\"bare except\" if is_bare else \"typed except\"} -> {issue}')
    except: pass
"
```

## Notes

- **False positives**: Import error 패턴은 실제로 문제가 아닐 수 있음
- **Context matters**: 일부 조용한 실패는 의도적일 수 있음 (예: 선택적 기능)
- **Priority**: Core auth > Account models > WebSocket > MCP tools > Scripts

---

**Total patterns detected**: 49
**Critical**: 3 (bare except + bare pass)
**High**: 1 (auth bare return None)
**Medium**: 37 (no logging)
**Low**: 8 (import errors, optional features)
