# Created: 2026-10-08
# Purpose: Statically extract kis_agent's REST call sites and WebSocket field
#          definitions so they can be compared with the official contract.
# Dependencies: stdlib only
# Test Status: Covered by tests/unit/test_spec_conformance.py (fixtures).

"""Static extraction of what kis_agent actually sends.

REST: every call to ``_make_request_dict`` / ``make_request`` / ``_paginate``
(or any call carrying a ``tr_id=`` keyword) is resolved to endpoint path,
TR_ID set, HTTP method and request keys. Values are resolved through string
literals, ``API_ENDPOINTS[...]``, ``IfExp``/``BoolOp``, local assignments,
dict-literal lookups (``TABLE[x]``) and literal argument defaults. Anything
that cannot be resolved is reported as ``UNRESOLVED`` so coverage of the check
itself stays visible.

WebSocket: ``SubscriptionType`` members, ``RealtimeDataParser`` field lists and
the ``parse()`` field map.
"""

import ast
import glob
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

UNRESOLVED = "<?>"
CALL_NAMES = {"_make_request_dict", "make_request", "_make_request", "_paginate"}
_POSITIONAL = {
    "make_request": ["endpoint", "tr_id", "params", "method"],
    "_make_request_dict": ["endpoint", "tr_id", "params"],
    "_make_request": ["endpoint", "tr_id", "params"],
    "_paginate": ["endpoint", "tr_id", "params"],
}
# Internal pass-through wrappers: they forward their own arguments.
_PASS_THROUGH = {
    "_make_request_dict",
    "_make_request_dataframe",
    "make_request_with_processing",
    "_paginate",
    "make_request",
}


@dataclass
class CallSite:
    where: str
    func: Optional[str]
    endpoints: Set[str]
    tr_ids: Set[str]
    methods: Set[str]
    keys: Set[str]
    keys_resolved: bool
    # request key -> True when the value sent is a literal constant
    key_literal: Dict[str, bool] = field(default_factory=dict)

    @property
    def resolvable(self) -> bool:
        return UNRESOLVED not in self.endpoints


def load_endpoint_table(path: str) -> Dict[str, str]:
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    table: Dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "API_ENDPOINTS" for t in n.targets
        ):
            for k, v in zip(n.value.keys, n.value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                    table[k.value] = v.value
    return table


def _cond_key(test: ast.AST) -> Tuple[str, bool]:
    """Normalise an if-test to (key, negated) so `not x` and `x` share a key."""
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        key, neg = _cond_key(test.operand)
        return key, not neg
    return ast.unparse(test), False


def _branch_ok(test: ast.AST, in_body: bool, env: Dict[str, bool]) -> bool:
    key, neg = _cond_key(test)
    if key not in env:
        return True
    value = env[key] != neg
    return value if in_body else not value


class _Resolver:
    def __init__(self, tree: ast.AST, endpoints: Dict[str, str]):
        self.endpoints = endpoints
        self.module_dicts: Dict[str, ast.Dict] = {}
        self.module_strs: Dict[str, str] = {}
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    name = t.id if isinstance(t, ast.Name) else None
                    if name is None:
                        continue
                    if isinstance(n.value, ast.Dict):
                        self.module_dicts[name] = n.value
                    elif isinstance(n.value, ast.Constant) and isinstance(
                        n.value.value, str
                    ):
                        self.module_strs[name] = n.value.value

    env: Dict[str, bool] = {}

    def strings(
        self, expr: Optional[ast.AST], func: Optional[ast.AST], depth: int = 0
    ) -> Set[str]:
        if expr is None or depth > 5:
            return {UNRESOLVED}
        if isinstance(expr, ast.IfExp):
            key, neg = _cond_key(expr.test)
            if key in self.env:
                take_body = self.env[key] != neg
                return self.strings(
                    expr.body if take_body else expr.orelse, func, depth + 1
                )
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return {expr.value}
        if isinstance(expr, ast.IfExp):
            return self.strings(expr.body, func, depth + 1) | self.strings(
                expr.orelse, func, depth + 1
            )
        if isinstance(expr, ast.BoolOp):
            out: Set[str] = set()
            for v in expr.values:
                out |= self.strings(v, func, depth + 1)
            return out
        if isinstance(expr, ast.Subscript):
            base = expr.value
            key = expr.slice
            if isinstance(base, ast.Name) and base.id == "API_ENDPOINTS":
                if isinstance(key, ast.Constant) and key.value in self.endpoints:
                    return {self.endpoints[key.value]}
                return {UNRESOLVED}
            table = self._dict_for(base, func)
            if table is not None:
                if isinstance(key, ast.Constant):
                    for k, v in zip(table.keys, table.values):
                        if isinstance(k, ast.Constant) and k.value == key.value:
                            return self.strings(v, func, depth + 1)
                # unknown key: every value the table can produce
                out = set()
                for v in table.values:
                    out |= self.strings(v, func, depth + 1)
                return out
            return {UNRESOLVED}
        if isinstance(expr, ast.Call):
            f = expr.func
            if isinstance(f, ast.Attribute) and f.attr == "get":
                if isinstance(f.value, ast.Name) and f.value.id == "API_ENDPOINTS":
                    a = expr.args[0] if expr.args else None
                    if isinstance(a, ast.Constant) and a.value in self.endpoints:
                        return {self.endpoints[a.value]}
                table = self._dict_for(f.value, func)
                if table is not None:
                    out = set()
                    for v in table.values:
                        out |= self.strings(v, func, depth + 1)
                    return out
            return {UNRESOLVED}
        if (
            isinstance(expr, ast.Attribute)
            and isinstance(expr.value, ast.Name)
            and expr.value.id == "self"
        ):
            return {UNRESOLVED}
        if isinstance(expr, ast.Name):
            if func is not None:
                found = False
                out = set()
                for n in ast.walk(func):
                    if isinstance(n, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == expr.id for t in n.targets
                    ):
                        found = True
                        out |= self.strings(n.value, func, depth + 1)
                if found:
                    return out
                default = self._arg_default(func, expr.id)
                if default is not None:
                    return self.strings(default, func, depth + 1)
            if expr.id in self.module_strs:
                return {self.module_strs[expr.id]}
            return {UNRESOLVED}
        return {UNRESOLVED}

    def _dict_for(self, node: ast.AST, func: Optional[ast.AST]) -> Optional[ast.Dict]:
        # NAME, self.NAME or cls.NAME bound to a dict literal (module or class level)
        name = None
        if isinstance(node, ast.Name):
            name = node.id
            if func is not None:
                for n in ast.walk(func):
                    if (
                        isinstance(n, ast.Assign)
                        and any(
                            isinstance(t, ast.Name) and t.id == name for t in n.targets
                        )
                        and isinstance(n.value, ast.Dict)
                    ):
                        return n.value
        elif isinstance(node, ast.Attribute):
            name = node.attr
        return self.module_dicts.get(name) if name else None

    parents: Dict[ast.AST, ast.AST] = {}

    def _guards_ok(self, node: ast.AST) -> bool:
        """True when every enclosing `if` branch is consistent with the current env."""
        child = node
        while child in self.parents:
            parent = self.parents[child]
            if isinstance(parent, ast.If):
                in_body = child in parent.body
                if child in parent.body or child in parent.orelse:
                    if not _branch_ok(parent.test, in_body, self.env):
                        return False
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                break
            child = parent
        return True

    @staticmethod
    def _arg_default(func: ast.AST, name: str) -> Optional[ast.AST]:
        args = getattr(func, "args", None)
        if args is None:
            return None
        names = [a.arg for a in args.args]
        defaults = [None] * (len(names) - len(args.defaults)) + list(args.defaults)
        for a, d in zip(names, defaults):
            if a == name:
                return d
        for a, d in zip(args.kwonlyargs, args.kw_defaults):
            if a.arg == name:
                return d
        return None

    def dict_keys(
        self, expr: Optional[ast.AST], func: Optional[ast.AST]
    ) -> Tuple[Set[str], bool, Dict[str, bool]]:
        keys: Set[str] = set()
        literal: Dict[str, bool] = {}
        ok = True
        if isinstance(expr, ast.Dict):
            for k, v in zip(expr.keys, expr.values):
                if k is None:  # **spread
                    sub_keys, sub_ok, sub_lit = self.dict_keys(v, func)
                    if sub_keys:
                        keys |= sub_keys
                        literal.update(sub_lit)
                    else:
                        ok = False
                    ok = ok and sub_ok
                elif isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
                    literal[k.value] = isinstance(v, ast.Constant)
                else:
                    ok = False
            return keys, ok, literal
        if isinstance(expr, ast.Name) and func is not None:
            found = False
            for n in ast.walk(func):
                if isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name) and t.id == expr.id:
                            found = True
                            if isinstance(n.value, (ast.Dict, ast.Call)):
                                k, o, lit = self.dict_keys(n.value, func)
                                keys |= k
                                literal.update(lit)
                                ok = ok and o
                            else:
                                ok = False
                        if (
                            isinstance(t, ast.Subscript)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == expr.id
                            and isinstance(t.slice, ast.Constant)
                            and isinstance(t.slice.value, str)
                            and self._guards_ok(n)
                        ):
                            keys.add(t.slice.value)
                            literal.setdefault(
                                t.slice.value, isinstance(n.value, ast.Constant)
                            )
                if (
                    isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "update"
                    and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == expr.id
                ):
                    for a in n.args:
                        k, o, lit = self.dict_keys(a, func)
                        keys |= k
                        literal.update(lit)
                        ok = ok and o
            return keys, ok and found, literal
        if isinstance(expr, ast.Call):
            # e.g. **self._get_account_params(): account keys are a known shape
            f = expr.func
            if isinstance(f, ast.Attribute) and "account" in f.attr.lower():
                return (
                    {"CANO", "ACNT_PRDT_CD"},
                    True,
                    {"CANO": False, "ACNT_PRDT_CD": False},
                )
        return keys, False, literal


def _parents(tree: ast.AST) -> Dict[ast.AST, ast.AST]:
    out = {}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p):
            out[c] = p
    return out


def _enclosing(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> Optional[ast.AST]:
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    return None


def extract_call_sites(
    source: str, rel: str, endpoints: Dict[str, str]
) -> List[CallSite]:
    tree = ast.parse(source)
    resolver = _Resolver(tree, endpoints)
    parents = _parents(tree)
    resolver.parents = parents
    sites = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        fname = (
            f.attr
            if isinstance(f, ast.Attribute)
            else (f.id if isinstance(f, ast.Name) else None)
        )
        kw = {k.arg: k.value for k in n.keywords if k.arg}
        if fname not in CALL_NAMES and "tr_id" not in kw:
            continue
        for name, value in zip(_POSITIONAL.get(fname, []), n.args):
            kw.setdefault(name, value)
        func = _enclosing(n, parents)
        if func is not None and func.name in _PASS_THROUGH:
            continue
        conds = _branch_conditions(func) if func is not None else []
        envs: List[Dict[str, bool]] = [{}]
        for c in conds[:3]:
            envs = [dict(e, **{c: v}) for e in envs for v in (True, False)]
        variants = []  # (env, endpoints, trs, methods, keys, ok, literal)
        for env in envs:
            resolver.env = env
            endpoints_found = (
                resolver.strings(kw.get("endpoint"), func)
                if "endpoint" in kw
                else {UNRESOLVED}
            )
            trs = (
                resolver.strings(kw.get("tr_id"), func)
                if "tr_id" in kw
                else {UNRESOLVED}
            )
            methods = (
                resolver.strings(kw.get("method"), func) if "method" in kw else {"GET"}
            )
            if "params" in kw:
                keys, ok, literal = resolver.dict_keys(kw.get("params"), func)
            else:
                keys, ok, literal = set(), False, {}
            variants.append((env, endpoints_found, trs, methods, keys, ok, literal))
        # Merge variants that only differ in TR_ID (e.g. a date picks one of two TRs
        # for the same URL and body); keep a split only where URL or keys change.
        merged: Dict[Tuple[frozenset, frozenset], list] = {}
        for env, eps, trs, methods, keys, ok, literal in variants:
            sig = (frozenset(eps), frozenset(keys))
            if sig in merged:
                m = merged[sig]
                m[2] |= trs
                m[3] |= methods
                m[0].append(env)
            else:
                merged[sig] = [[env], eps, set(trs), set(methods), keys, ok, literal]
        groups = list(merged.values())
        varying = set()
        if len(groups) > 1:
            for c in conds[:3]:
                vals = [{e[c] for e in g[0] if c in e} for g in groups]
                if (
                    any(len(v) == 1 for v in vals)
                    and len({frozenset(v) for v in vals}) > 1
                ):
                    varying.add(c)
        for envs_g, eps, trs, methods, keys, ok, literal in groups:
            label = ""
            if varying:
                parts = []
                for c in sorted(varying):
                    vals = {e[c] for e in envs_g if c in e}
                    if len(vals) == 1:
                        parts.append(f"{c}={vals.pop()}")
                label = " [" + ", ".join(parts) + "]" if parts else ""
            sites.append(
                CallSite(
                    where=f"{rel}:{n.lineno}{label}",
                    func=func.name if func is not None else None,
                    endpoints=eps,
                    tr_ids=trs,
                    methods={m.upper() for m in methods},
                    keys=keys,
                    keys_resolved=ok,
                    key_literal=literal,
                )
            )
        resolver.env = {}
    return sites


def _branch_conditions(func: ast.AST) -> List[str]:
    """Boolean conditions that select both an IfExp value and an `if` block in ``func``.

    Only conditions used by an IfExp are enumerated; that is the pattern where one
    flag picks endpoint, TR_ID and request keys together (e.g. IRP accounts).
    """
    ifexp = []
    for n in ast.walk(func):
        if isinstance(n, ast.IfExp):
            key, _ = _cond_key(n.test)
            if key not in ifexp:
                ifexp.append(key)
    return ifexp


def load_call_sites(repo: str) -> List[CallSite]:
    endpoints = load_endpoint_table(
        os.path.join(repo, "kis_agent", "core", "endpoints.py")
    )
    sites: List[CallSite] = []
    for path in sorted(
        glob.glob(os.path.join(repo, "kis_agent", "**", "*.py"), recursive=True)
    ):
        rel = os.path.relpath(path, repo)
        if rel.endswith("tr_mapping.py"):
            continue
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        try:
            sites.extend(extract_call_sites(src, rel, endpoints))
        except SyntaxError:
            continue
    return sites


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


def load_ws_types(source: str) -> Dict[str, str]:
    """SubscriptionType member name -> TR_ID."""
    tree = ast.parse(source)
    out: Dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == "SubscriptionType":
            for stmt in n.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(stmt.value, ast.Constant)
                ):
                    out[stmt.targets[0].id] = stmt.value.value
    return out


def load_ws_field_lists(source: str) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    """Return (field-list name -> fields, SubscriptionType member -> field-list name)."""
    tree = ast.parse(source)
    lists: Dict[str, List[str]] = {}
    mapping: Dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == "RealtimeDataParser":
            for stmt in n.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(stmt.value, ast.List)
                ):
                    lists[stmt.targets[0].id] = [
                        e.value.lower()
                        for e in stmt.value.elts
                        if isinstance(e, ast.Constant)
                    ]
            for f in n.body:
                if isinstance(f, ast.FunctionDef) and f.name == "parse":
                    for d in ast.walk(f):
                        if isinstance(d, ast.Dict):
                            for k, v in zip(d.keys, d.values):
                                if isinstance(k, ast.Attribute) and isinstance(
                                    v, ast.Attribute
                                ):
                                    mapping[k.attr] = v.attr
    return lists, mapping


def load_ws(repo: str) -> Dict[str, Dict[str, object]]:
    """TR_ID -> {"member": name, "fields": list|None} for the supported WSAgent path."""
    base = os.path.join(repo, "kis_agent", "websocket")
    with open(os.path.join(base, "ws_types.py"), encoding="utf-8") as fh:
        types = load_ws_types(fh.read())
    with open(os.path.join(base, "ws_helpers.py"), encoding="utf-8") as fh:
        lists, mapping = load_ws_field_lists(fh.read())
    out: Dict[str, Dict[str, object]] = {}
    for member, tr in types.items():
        list_name = mapping.get(member)
        entry = out.setdefault(tr, {"members": [], "fields": None})
        entry["members"].append(member)
        if list_name and entry["fields"] is None:
            entry["fields"] = lists.get(list_name)
    return out
