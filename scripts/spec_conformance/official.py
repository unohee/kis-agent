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
            real_part, _, paper_part = str(r[6]).partition("[모의투자]")
            tr_real.update(t for t in tr_tokens(real_part) if t.isupper())
            tr_paper.update(tr_tokens(paper_part))
        if not section or not section.startswith("Request") or "Header" in section:
            continue
        element, required = r[1], r[4]
        if element and required in ("Y", "N") and r[0] != "구분":
            (req if required == "Y" else opt).add(str(element).strip())
    return {"url": url, "required": req, "optional": opt, "tr_real": tr_real, "tr_paper": tr_paper}


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


def load_samples(clone: str) -> Dict[str, List[SampleApi]]:
    """Load every examples_llm REST sample, keyed by URL."""
    out: Dict[str, List[SampleApi]] = {}
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
