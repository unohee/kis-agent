"""Regenerate kis_agent/websocket/ws_fields.py from the official realtime columns.

Run from the repo root with the workbook and the open-trading-api clone present:
    python scripts/spec_conformance/gen_ws_fields.py
"""
# Created: 2026-10-08
# Purpose: generate kis_agent/websocket/ws_fields.py from the official realtime columns
# Dependencies: scripts/spec_conformance, workbook, open-trading-api clone
# Test Status: used once per spec refresh
import fnmatch
import json
import os
import sys
import textwrap
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from spec_conformance import official
wbp = official.find_workbook(".")
m = official.merge_ws_columns(official.load_workbook_ws(wbp), official.load_ws_samples("open-trading-api"),
                              official.workbook_date(wbp), official.sample_commit_dates("open-trading-api"))
globs = [e["glob"] for e in json.load(open("scripts/spec_conformance/allowlist.json"))["ws_trs"]]
trs = sorted(t for t in m if not any(fnmatch.fnmatch(t, g) for g in globs))
out = ['''"""Official realtime (WebSocket) column layouts, keyed by TR_ID.

Generated from the KIS OpenAPI workbook (2025-12-12) and the open-trading-api
samples by ``scripts/spec_conformance`` rules: the workbook wins, except where a
sample committed after the workbook only appends columns (e.g. market_cls_code).
Futures/options feeds are not listed (out of scope).

Each value is the space-separated, lower-cased column list in frame order.
Verify with ``python scripts/spec_conformance/check.py``.
"""

from typing import Dict, Tuple

_LAYOUTS: Dict[str, str] = {''']
for t in trs:
    cols = " ".join(m[t]["columns"])
    src = m[t]["file"]
    lines = textwrap.wrap(cols, 74, break_long_words=False, break_on_hyphens=False)
    out.append(f"    # {src}")
    out.append(f'    "{t}": (')
    for i, ln in enumerate(lines):
        sep = " " if i < len(lines) - 1 else ""
        out.append(f'        "{ln}{sep}"')
    out.append("    ),")
out.append("}")
out.append('''

FIELDS: Dict[str, Tuple[str, ...]] = {
    tr_id: tuple(layout.split()) for tr_id, layout in _LAYOUTS.items()
}


def fields_for(tr_id: str) -> Tuple[str, ...]:
    """Column names for ``tr_id`` (empty tuple when the layout is unknown)."""
    return FIELDS.get(tr_id, ())
''')
open("kis_agent/websocket/ws_fields.py", "w", encoding="utf-8").write("\n".join(out))
print(len(trs), trs)
