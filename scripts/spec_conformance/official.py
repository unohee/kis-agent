# Created: 2026-10-08
# Purpose: Load the official KIS OpenAPI contract from the spec workbook and the
#          koreainvestment/open-trading-api sample repository.
# Dependencies: openpyxl (workbook only), stdlib
# Test Status: Covered by tests/unit/test_spec_conformance.py (fixtures) and the
#              live check that runs when the workbook and clone are present.

"""Official contract loaders.

The workbook is the authoritative source for URLs, HTTP methods, TR_IDs and
request-field requirements. The sample repository is used for two things the
workbook does not express well: which request parameter a sample branches on
when it selects a TR_ID (e.g. one TR_ID per overseas exchange), and the
WebSocket column lists.

Lessons baked in from the 2026-10-08 audit:

- Sample docstring ``[필수]`` markers disagree with the workbook ``Required``
  column, so required fields come from the workbook only.
- TR_IDs are taken from cells by whole-token match. A substring regex
  truncated ``HHPSTH60100C1`` to ``HPSTH60100C1``.
- Several sheets can share one URL (per-market variants). Their required
  fields are intersected, everything else becomes optional.
"""

import ast
import glob
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

WORKBOOK_GLOB = "한국투자증권_오픈API_전체문서_*.xlsx"
CLONE_DIRNAME = "open-trading-api"

# A TR_ID is one uppercase alphanumeric token that starts with a letter and
# contains at least one digit, e.g. TTTC0011U, FHKST01010100, HHPSTH60100C1, H0STCNT0.
_TOKEN = re.compile(r"[A-Z0-9]+")
# "(구)TTTC8036R → (신)TTTC0084R": the workbook names retired TR_IDs this way.
_OLD_TR = re.compile(r"\(구\)\s*([A-Z0-9]+)")
# Sample-side TR_ID literals (REST and WebSocket).
TR_ID_RE = re.compile(r"^[A-Z][A-Z0-9]{6,12}$")

# Request parameters that select the environment or the side rather than the
# market. Branching on these is expected to map to separate methods/args.
_NON_MARKET_BRANCH_ARGS = {"env_dv", "ord_dv", "tr_cont"}


def tr_tokens(cell: object) -> List[str]:
    """Return every TR_ID-looking token in a workbook cell, in order."""
    if cell is None:
        return []
    out = []
    for tok in _TOKEN.findall(str(cell)):
        if tok[0].isalpha() and any(c.isdigit() for c in tok) and 7 <= len(tok) <= 13:
            out.append(tok)
    return out


def find_workbook(root: str) -> Optional[str]:
    """Locate the newest KIS spec workbook under ``root``."""
    matches = sorted(glob.glob(os.path.join(root, WORKBOOK_GLOB)), reverse=True)
    return matches[0] if matches else None


@dataclass
class SpecApi:
    """One API as described by the workbook (merged across sheets sharing a URL)."""

    url: str
    names: List[str] = field(default_factory=list)
    menus: Set[str] = field(default_factory=set)
    mode: Set[str] = field(default_factory=set)  # REST / WEBSOCKET
    real_trs: Set[str] = field(default_factory=set)
    paper_trs: Set[str] = field(default_factory=set)
    paper_supported: bool = False
    methods: Set[str] = field(default_factory=set)
    old_trs: Set[str] = field(default_factory=set)  # retired: "(구)XXXX → (신)YYYY"
    required: Optional[Set[str]] = None
    optional: Set[str] = field(default_factory=set)

    @property
    def all_fields(self) -> Set[str]:
        return (self.required or set()) | self.optional


def _merge_fields(api: SpecApi, req: Set[str], opt: Set[str]) -> None:
    if api.required is None:
        api.required = set(req)
        api.optional = set(opt)
        return
    everything = api.required | api.optional | req | opt
    api.required = api.required & req
    api.optional = everything - api.required


def parse_api_sheet(rows: List[tuple]) -> Dict[str, object]:
    """Extract URL and request-field requirements from one per-API sheet."""
    url = None
    section = None
    req: Set[str] = set()
    opt: Set[str] = set()
    tr_real: Set[str] = set()
    tr_paper: Set[str] = set()
    tr_old: Set[str] = set()
    for raw in rows:
        r = list(raw) + [None] * 8
        if r[0] == "URL 명":
            url = str(r[1]).strip()
            continue
        if r[0] and str(r[0]).startswith(("Request", "Response")):
            section = str(r[0])
        if r[1] == "tr_id" and section and "Header" in section and r[6]:
            # Per-market TR_IDs live only in this description, e.g.
            # "[실전투자] TTTT1004U : 미국 ... [모의투자] VTTT1004U : ..."
            text = str(r[6])
            tr_old.update(_OLD_TR.findall(text))
            text = _OLD_TR.sub(" ", text)
            real_part, _, paper_part = text.partition("[모의투자]")
            tr_real.update(t for t in tr_tokens(real_part) if t.isupper())
            tr_paper.update(tr_tokens(paper_part))
        if not section or not section.startswith("Request") or "Header" in section:
            continue
        element, required = r[1], r[4]
        if element and required in ("Y", "N") and r[0] != "구분":
            (req if required == "Y" else opt).add(str(element).strip())
    return {
        "url": url,
        "required": req,
        "optional": opt,
        "tr_real": tr_real,
        "tr_paper": tr_paper,
        "tr_old": tr_old,
    }


def load_workbook_apis(path: str) -> Dict[str, SpecApi]:
    """Load the API list sheet and every per-API sheet, keyed by URL."""
    import warnings

    import openpyxl

    warnings.filterwarnings("ignore", module="openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    apis: Dict[str, SpecApi] = {}
    rows = list(wb["API 목록"].iter_rows(values_only=True))[1:]
    for r in rows:
        if not r or not r[0]:
            continue
        mode, menu, name, real, paper, method, url = (
            r[1],
            r[2],
            r[3],
            r[5],
            r[6],
            r[7],
            r[8],
        )
        if not url:
            continue
        api = apis.setdefault(str(url).strip(), SpecApi(url=str(url).strip()))
        api.names.append(str(name))
        api.menus.add(str(menu))
        api.mode.add(str(mode))
        api.real_trs.update(tr_tokens(real))
        paper_tokens = tr_tokens(paper)
        api.paper_trs.update(paper_tokens)
        api.paper_supported = api.paper_supported or bool(paper_tokens)
        if method:
            api.methods.add(str(method).strip().upper())
    for name in wb.sheetnames[1:]:
        parsed = parse_api_sheet(list(wb[name].iter_rows(values_only=True)))
        url = parsed["url"]
        if url in apis:
            _merge_fields(apis[url], parsed["required"], parsed["optional"])
            apis[url].real_trs.update(parsed["tr_real"])
            apis[url].paper_trs.update(parsed["tr_paper"])
            apis[url].old_trs.update(parsed["tr_old"])
            apis[url].real_trs -= apis[url].old_trs
            apis[url].paper_trs -= apis[url].old_trs
    return apis


# ---------------------------------------------------------------------------
# Sample repository
# ---------------------------------------------------------------------------


@dataclass
class SampleApi:
    """One examples_llm REST sample."""

    file: str
    url: str
    tr_ids: Set[str]
    post: bool
    keys: Set[str]
    # request key -> set of argument values the sample branches on to pick a TR_ID
    tr_branch_keys: Set[str] = field(default_factory=set)
    # YYYYMMDD of the sample file's last commit ("" when unknown)
    updated: str = ""


def _docstring_ids(func: ast.AST) -> Set[int]:
    return {
        id(n.value)
        for n in ast.walk(func)
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
    }


def _branch_args_for_tr(func: ast.FunctionDef) -> Set[str]:
    """Argument names whose comparison guards an assignment to ``tr_id``."""
    args: Set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, ast.If):
            continue
        assigns_tr = any(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "tr_id" for t in n.targets)
            for stmt in node.body
            for n in ast.walk(stmt)
        )
        if not assigns_tr:
            continue
        for n in ast.walk(node.test):
            if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name):
                if n.left.id not in _NON_MARKET_BRANCH_ARGS:
                    args.add(n.left.id)
    return args


def parse_sample_source(source: str, rel: str, func_name: str) -> Optional[SampleApi]:
    """Parse one examples_llm REST sample module."""
    tree = ast.parse(source)
    url = None
    for n in tree.body:
        if (
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "API_URL" for t in n.targets)
            and isinstance(n.value, ast.Constant)
        ):
            url = n.value.value
    if not url:
        return None
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    func = next((f for f in funcs if f.name == func_name), funcs[0] if funcs else None)
    if func is None:
        return None
    skip = _docstring_ids(func)
    trs = {
        n.value
        for n in ast.walk(func)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and id(n) not in skip
        and TR_ID_RE.match(n.value)
        and any(c.isdigit() for c in n.value)
    }
    post = any(
        isinstance(n, ast.keyword)
        and n.arg == "postFlag"
        and isinstance(n.value, ast.Constant)
        and n.value.value is True
        for n in ast.walk(func)
    )
    keys: Set[str] = set()
    arg_to_key: Dict[str, str] = {}
    for n in ast.walk(func):
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if (
                isinstance(t, ast.Name)
                and t.id == "params"
                and isinstance(n.value, ast.Dict)
            ):
                for k, v in zip(n.value.keys, n.value.values):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.add(k.value)
                        if isinstance(v, ast.Name):
                            arg_to_key[v.id] = k.value
            if (
                isinstance(t, ast.Subscript)
                and isinstance(t.value, ast.Name)
                and t.value.id == "params"
                and isinstance(t.slice, ast.Constant)
                and isinstance(t.slice.value, str)
            ):
                keys.add(t.slice.value)
                if isinstance(n.value, ast.Name):
                    arg_to_key[n.value.id] = t.slice.value
    branch_keys = {arg_to_key[a] for a in _branch_args_for_tr(func) if a in arg_to_key}
    return SampleApi(rel, url, trs, post, keys, branch_keys)


def workbook_date(path: str) -> str:
    """YYYYMMDD encoded in the workbook file name (한국투자증권_오픈API_전체문서_YYYYMMDD_...)."""
    m = re.search(r"_(\d{8})_", os.path.basename(path))
    return m.group(1) if m else ""


def sample_commit_dates(clone: str) -> Dict[str, str]:
    """Map examples_llm file path (relative to the clone) to its last commit date YYYYMMDD."""
    import subprocess  # nosec B404 - fixed argv, no shell

    try:
        log = subprocess.run(  # nosec B603 B607
            ["git", "-C", clone, "log", "--name-only", "--format=@%cs", "--", "examples_llm"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    dates: Dict[str, str] = {}
    current = ""
    for line in log.splitlines():
        if line.startswith("@"):
            current = line[1:].replace("-", "")
        elif line.strip() and line not in dates:
            dates[line] = current
    return dates


def load_samples(clone: str) -> Dict[str, List[SampleApi]]:
    """Load every examples_llm REST sample, keyed by URL."""
    out: Dict[str, List[SampleApi]] = {}
    dates = sample_commit_dates(clone)
    for path in sorted(
        glob.glob(os.path.join(clone, "examples_llm", "*", "*", "*.py"))
    ):
        base = os.path.basename(path)
        if base.startswith("chk_") or base == "kis_auth.py":
            continue
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        try:
            sample = parse_sample_source(
                src, os.path.relpath(path, clone), os.path.splitext(base)[0]
            )
        except SyntaxError:
            continue
        if sample:
            sample.updated = dates.get(sample.file, "")
            out.setdefault(sample.url, []).append(sample)
    return out


def parse_ws_sample_source(source: str) -> Dict[str, List[str]]:
    """Return {tr_id: lowercase column list} for one WebSocket sample module."""
    tree = ast.parse(source)
    columns: Optional[List[str]] = None
    trs: Set[str] = set()
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "columns" for t in n.targets)
            and isinstance(n.value, ast.List)
        ):
            columns = [
                e.value.lower()
                for e in n.value.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            ]
        if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "tr_id" for t in n.targets
        ):
            for c in ast.walk(n.value):
                if (
                    isinstance(c, ast.Constant)
                    and isinstance(c.value, str)
                    and TR_ID_RE.match(c.value)
                ):
                    trs.add(c.value)
    if not columns:
        return {}
    return dict.fromkeys(trs, columns)


def load_ws_samples(
    clone: str, domains: Optional[List[str]] = None
) -> Dict[str, Dict[str, object]]:
    """Load WebSocket column lists from examples_llm, keyed by TR_ID."""
    out: Dict[str, Dict[str, object]] = {}
    pattern = os.path.join(clone, "examples_llm", "*", "*", "*.py")
    for path in sorted(glob.glob(pattern)):
        base = os.path.basename(path)
        domain = path.split(os.sep)[-3]
        if base.startswith("chk_") or (domains and domain not in domains):
            continue
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        if "API_URL" in src and "ka.data_fetch" not in src:
            continue  # REST sample
        try:
            found = parse_ws_sample_source(src)
        except SyntaxError:
            continue
        for tr, cols in found.items():
            out[tr] = {"file": os.path.relpath(path, clone), "columns": cols}
    return out


def parse_ws_sheet(rows: List[tuple]) -> Dict[str, object]:
    """Extract TR_IDs and the ordered Response Body columns from one realtime sheet.

    A sheet is realtime when its URL is ``/tryitout/<TR_ID>``; the URL also names
    the TR. The "API 통신방식" and "실전 TR_ID" cells are not trusted: the
    2025-12-12 workbook labels some realtime sheets REST (H0UNMKO0, H0NXMKO0),
    one REST sheet WEBSOCKET (FHPST04320000), and gives H0BJASP0's sheet the
    TR_ID H0BJCNT0.
    """
    url = ""
    paper: List[str] = []
    columns: List[str] = []
    in_body = False
    for raw in rows:
        r = list(raw) + [None] * 8
        head = str(r[0]).strip() if r[0] is not None else ""
        if head == "URL 명":
            url = str(r[1]).strip()
        elif head == "모의 TR_ID":
            paper = [t for t in tr_tokens(r[1]) if TR_ID_RE.match(t)]
        if head == "Response Body":
            in_body = True
        elif head:
            in_body = False
        if in_body and r[1]:
            columns.append(str(r[1]).strip().lower())
    tr = url[len("/tryitout/") :] if url.startswith("/tryitout/") else ""
    real = [tr] if TR_ID_RE.match(tr) else []
    return {"websocket": bool(real), "real": real, "paper": paper, "columns": columns}


def load_workbook_ws(path: str) -> Dict[str, Dict[str, object]]:
    """Realtime column lists from the workbook's realtime sheets, keyed by TR_ID."""
    import warnings

    import openpyxl

    warnings.filterwarnings("ignore", module="openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out: Dict[str, Dict[str, object]] = {}
    for name in wb.sheetnames[1:]:
        parsed = parse_ws_sheet(list(wb[name].iter_rows(values_only=True)))
        if not parsed["websocket"] or not parsed["columns"]:
            continue
        for tr in list(parsed["real"]) + list(parsed["paper"]):
            out.setdefault(tr, {"file": f"workbook:{name}", "columns": parsed["columns"]})
    return out


def merge_ws_columns(
    workbook: Dict[str, Dict[str, object]],
    samples: Dict[str, Dict[str, object]],
    workbook_day: str,
    sample_dates: Dict[str, str],
) -> Dict[str, Dict[str, object]]:
    """Official realtime columns: workbook first, newer samples only extend the tail.

    KIS appends columns to live feeds (e.g. market_cls_code, 2026) and updates the
    samples first, so a sample committed after the workbook whose columns start
    with the workbook's columns wins. Otherwise the workbook wins: several
    samples omit the leading RSYM column of overseas feeds (pandas read_csv turns
    the extra first value into the index) or list response-header keys as columns.
    """
    out = dict(samples)
    for tr, wb_entry in workbook.items():
        smp = samples.get(tr)
        if smp:
            newer = sample_dates.get(str(smp["file"]), "") > workbook_day > ""
            cols, wcols = list(smp["columns"]), list(wb_entry["columns"])
            if newer and len(cols) > len(wcols) and cols[: len(wcols)] == wcols:
                continue
        out[tr] = wb_entry
    return out


def describe_api(path: str, url: str, include_response: bool = False) -> List[str]:
    """Human-readable field table for one URL, straight from the workbook sheets."""
    import warnings

    import openpyxl

    warnings.filterwarnings("ignore", module="openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out: List[str] = []
    for name in wb.sheetnames[1:]:
        rows = list(wb[name].iter_rows(values_only=True))
        if not any(r and r[0] == "URL 명" and str(r[1]).strip() == url for r in rows):
            continue
        out.append(f"### {name} {url}")
        section = None
        for raw in rows:
            r = list(raw) + [None] * 8
            if r[0] in ("실전 TR_ID", "모의 TR_ID", "HTTP Method"):
                out.append(f"  {r[0]}: {r[1]}")
            if r[0] and str(r[0]).startswith(("Request", "Response")):
                section = str(r[0])
            if not section or (section.startswith("Response") and not include_response):
                continue
            if section.startswith("Request Header") and r[1] != "tr_id":
                continue
            if r[1] and r[4] in ("Y", "N") and r[0] != "구분":
                desc = " | ".join(str(r[6] or "").replace("\r", "").split("\n"))
                out.append(f"  [{section.split()[-1][:4]}] {r[1]} ({r[2]}) {r[4]}: {desc[:300]}")
    return out

