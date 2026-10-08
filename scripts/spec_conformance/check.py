# Created: 2026-10-08
# Purpose: Compare kis_agent against the official KIS contract and report every
#          deviation; exit non-zero under --check when a non-allowlisted one exists.
# Dependencies: openpyxl (workbook), stdlib
# Test Status: Covered by tests/unit/test_spec_conformance.py.

"""KIS OpenAPI spec-conformance checker.

Usage (from the repository root, with the 3.12 dev env)::

    python scripts/spec_conformance/check.py                 # markdown report
    python scripts/spec_conformance/check.py --check         # exit 1 on deviations
    python scripts/spec_conformance/check.py --include-coverage --report json

Inputs: the spec workbook (``한국투자증권_오픈API_전체문서_*.xlsx`` in the repo
root, untracked) and the ``open-trading-api`` clone (repo root, untracked).
Intended deviations live in ``allowlist.json`` next to this file, each with a
reason.
"""

import argparse
import fnmatch
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Set

try:  # package import (tests)
    from . import official, ours
except ImportError:  # script execution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import official  # type: ignore[no-redef]
    import ours  # type: ignore[no-redef]

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ALLOWLIST = os.path.join(HERE, "allowlist.json")
BASELINE = os.path.join(HERE, "baseline.json")

# Rules whose findings make --check fail. "info" findings never fail the check.
SEVERITY = {
    "method-mismatch": "error",
    "tr-mismatch": "error",
    "deprecated-tr": "error",
    "tr-selection": "error",
    "url-not-in-spec": "error",
    "missing-required": "error",
    "unknown-key": "error",
    "ws-columns": "error",
    "ws-missing-tail": "error",
    "coverage-rest": "error",
    "coverage-ws": "error",
    "case-only-key": "info",
    "unresolved": "info",
    "spec-inconsistency": "info",
}
HEADERISH_KEYS = {"tr_cont", "tr_id"}


@dataclass
class Finding:
    rule: str
    where: str
    url: str
    detail: str
    order_surface: bool = False

    @property
    def severity(self) -> str:
        return SEVERITY[self.rule]

    @property
    def key(self) -> str:
        """Line-number-free identity used by the baseline ratchet."""
        path = self.where.split(":")[0].split(" ")[0]
        func = re.search(r"func=(\S+)", self.detail)
        return f"{self.rule}|{path}|{func.group(1) if func else ''}|{self.url}"


@dataclass
class Allowlist:
    url_globs: List[str]
    path_globs: List[str]
    ws_tr_globs: List[str]
    coverage_external: Dict[str, str]
    findings: List[Dict[str, str]]

    @classmethod
    def load(cls, path: str) -> "Allowlist":
        if not os.path.exists(path):
            return cls([], [], [], {}, [])
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        return cls(
            url_globs=[e["glob"] for e in raw.get("urls", [])],
            path_globs=[e["glob"] for e in raw.get("paths", [])],
            ws_tr_globs=[e["glob"] for e in raw.get("ws_trs", [])],
            coverage_external={
                e["url"]: e["needle"]
                for e in raw.get("implemented_outside_make_request", [])
            },
            findings=raw.get("findings", []),
        )

    def url_allowed(self, url: str) -> bool:
        return any(fnmatch.fnmatch(url, g) for g in self.url_globs)

    def path_allowed(self, where: str) -> bool:
        return any(fnmatch.fnmatch(where.split(":")[0], g) for g in self.path_globs)

    def ws_allowed(self, tr: str) -> bool:
        return any(fnmatch.fnmatch(tr, g) for g in self.ws_tr_globs)

    def finding_allowed(self, f: Finding) -> bool:
        if self.url_allowed(f.url) or self.path_allowed(f.where):
            return True
        if f.rule.startswith("ws") or f.rule == "coverage-ws":
            if self.ws_allowed(f.url):
                return True
        for e in self.findings:
            if e.get("rule") != f.rule:
                continue
            if "url" in e and e["url"] != f.url:
                continue
            if "where" in e and not f.where.startswith(e["where"]):
                continue
            if "where_contains" in e and e["where_contains"] not in f.where:
                continue
            if "detail_contains" in e and e["detail_contains"] not in f.detail:
                continue
            return True
        return False


def _lower_map(keys: Iterable[str]) -> Dict[str, str]:
    return {k.lower(): k for k in keys}


def check_rest(
    sites: List["ours.CallSite"],
    spec: Dict[str, "official.SpecApi"],
    samples: Dict[str, List["official.SampleApi"]],
) -> List[Finding]:
    findings: List[Finding] = []
    for s in sites:
        if not s.resolvable or ours.UNRESOLVED in s.tr_ids:
            findings.append(
                Finding(
                    "unresolved",
                    s.where,
                    ",".join(sorted(s.endpoints)),
                    f"func={s.func} tr={sorted(s.tr_ids)}",
                )
            )
            continue
        for url in sorted(s.endpoints):
            api = spec.get(url)
            if api is None:
                findings.append(
                    Finding(
                        "url-not-in-spec",
                        s.where,
                        url,
                        f"func={s.func} tr={sorted(s.tr_ids)}",
                    )
                )
                continue
            order = "POST" in api.methods
            allowed_trs = api.real_trs | api.paper_trs
            for sample in samples.get(url, []):
                allowed_trs |= sample.tr_ids
            retired = sorted(t for t in s.tr_ids if t in api.old_trs)
            if retired:
                findings.append(
                    Finding(
                        "deprecated-tr",
                        s.where,
                        url,
                        f"func={s.func} ours={retired} is marked (구) in the spec; use {sorted(api.real_trs)}",
                        order,
                    )
                )
            allowed_trs -= api.old_trs
            bad = sorted(t for t in s.tr_ids if t not in allowed_trs and t not in api.old_trs)
            if bad:
                findings.append(
                    Finding(
                        "tr-mismatch",
                        s.where,
                        url,
                        f"func={s.func} ours={bad} spec={sorted(api.real_trs)}",
                        order,
                    )
                )
            if s.methods != api.methods:
                findings.append(
                    Finding(
                        "method-mismatch",
                        s.where,
                        url,
                        f"func={s.func} ours={sorted(s.methods)} spec={sorted(api.methods)}",
                        order,
                    )
                )
            branch_keys: Set[str] = set()
            for sample in samples.get(url, []):
                branch_keys |= sample.tr_branch_keys
            for key in sorted(branch_keys):
                sent_variable = key in s.key_literal and not s.key_literal[key]
                if sent_variable and len(s.tr_ids) == 1:
                    findings.append(
                        Finding(
                            "tr-selection",
                            s.where,
                            url,
                            f"func={s.func} sends variable {key} but always uses {sorted(s.tr_ids)}; "
                            f"the official sample selects the TR_ID by {key}",
                            order,
                        )
                    )
            if not s.keys_resolved:
                findings.append(
                    Finding(
                        "unresolved",
                        s.where,
                        url,
                        f"func={s.func} request keys built dynamically",
                    )
                )
                continue
            if api.required is None:
                continue
            sent = {k for k in s.keys if k not in HEADERISH_KEYS}
            sent_lower = {k.lower() for k in sent}
            spec_lower = _lower_map(api.all_fields)
            missing = sorted(k for k in api.required if k.lower() not in sent_lower)
            unknown = sorted(
                k
                for k in sent
                if k not in api.all_fields and k.lower() not in spec_lower
            )
            case_only = sorted(
                k for k in sent if k not in api.all_fields and k.lower() in spec_lower
            )
            if missing:
                findings.append(
                    Finding(
                        "missing-required",
                        s.where,
                        url,
                        f"func={s.func} missing={missing}",
                        order,
                    )
                )
            if unknown:
                findings.append(
                    Finding(
                        "unknown-key",
                        s.where,
                        url,
                        f"func={s.func} unknown={unknown}",
                        order,
                    )
                )
            if case_only:
                findings.append(
                    Finding(
                        "case-only-key",
                        s.where,
                        url,
                        f"func={s.func} keys={case_only}",
                        order,
                    )
                )
    return findings


def check_spec_consistency(
    spec: Dict[str, "official.SpecApi"], samples: Dict[str, List["official.SampleApi"]]
) -> List[Finding]:
    """Report places where the workbook and the current samples disagree."""
    findings = []
    for url, group in sorted(samples.items()):
        api = spec.get(url)
        if api is None:
            findings.append(
                Finding(
                    "spec-inconsistency",
                    group[0].file,
                    url,
                    "sample URL absent from workbook",
                )
            )
            continue
        sample_real = {t for g in group for t in g.tr_ids if not t.startswith("V")}
        extra = sample_real - api.real_trs
        if extra and not any(g.tr_branch_keys for g in group):
            findings.append(
                Finding(
                    "spec-inconsistency",
                    group[0].file,
                    url,
                    f"sample TR {sorted(extra)} not in workbook {sorted(api.real_trs)}",
                )
            )
    return findings


def check_ws(
    our_ws: Dict[str, Dict[str, object]], official_ws: Dict[str, Dict[str, object]]
) -> List[Finding]:
    findings = []
    for tr, entry in sorted(our_ws.items()):
        fields = entry["fields"]
        off = official_ws.get(tr)
        if not fields or not off:
            continue
        cols = off["columns"]
        common = min(len(fields), len(cols))
        first_diff = next((i for i in range(common) if fields[i] != cols[i]), None)
        where = f"kis_agent/websocket/ws_helpers.py ({'/'.join(entry['members'])})"
        if first_diff is not None:
            findings.append(
                Finding(
                    "ws-columns",
                    where,
                    tr,
                    f"position {first_diff}: ours={fields[first_diff]} official={cols[first_diff]} "
                    f"(ours {len(fields)}, official {len(cols)}, {off['file']})",
                )
            )
        elif len(fields) != len(cols):
            findings.append(
                Finding(
                    "ws-missing-tail" if len(fields) < len(cols) else "ws-columns",
                    where,
                    tr,
                    f"ours {len(fields)} official {len(cols)}; tail={cols[len(fields):] or fields[len(cols):]}",
                )
            )
    return findings


def check_coverage(
    sites: List["ours.CallSite"],
    spec: Dict[str, "official.SpecApi"],
    our_ws: Dict[str, Dict[str, object]],
    official_ws: Dict[str, Dict[str, object]],
    allow: Allowlist,
    repo: str,
) -> List[Finding]:
    called = {u for s in sites for u in s.endpoints}
    source_blob = _package_source(repo)
    findings = []
    for url, api in sorted(spec.items()):
        if url.startswith("/tryitout/") or "WEBSOCKET" in api.mode:
            continue
        if url in called:
            continue
        needle = allow.coverage_external.get(url)
        if needle and needle in source_blob:
            continue
        findings.append(
            Finding(
                "coverage-rest",
                "-",
                url,
                f"{api.names[0]} [{'/'.join(sorted(api.menus))}] tr={sorted(api.real_trs)}",
                "POST" in api.methods,
            )
        )
    ours_trs = set(our_ws)
    official_trs = set(official_ws)
    for api in spec.values():
        if api.url.startswith("/tryitout/") or "WEBSOCKET" in api.mode:
            official_trs |= {
                t for t in api.real_trs | api.paper_trs if t.startswith(("H0", "HDF"))
            }
    for tr in sorted(official_trs - ours_trs):
        src = official_ws.get(tr, {}).get("file", "workbook")
        findings.append(
            Finding(
                "coverage-ws",
                "-",
                tr,
                f"official realtime TR not in SubscriptionType ({src})",
            )
        )
    return findings


def _package_source(repo: str) -> str:
    chunks = []
    for root, _dirs, files in os.walk(os.path.join(repo, "kis_agent")):
        for name in files:
            if name.endswith(".py"):
                with open(os.path.join(root, name), encoding="utf-8") as fh:
                    chunks.append(fh.read())
    return "\n".join(chunks)


def run(
    repo: str = REPO,
    workbook: Optional[str] = None,
    clone: Optional[str] = None,
    include_coverage: bool = False,
    allowlist_path: str = ALLOWLIST,
    baseline_path: Optional[str] = BASELINE,
) -> Dict[str, object]:
    workbook = workbook or official.find_workbook(repo)
    clone = clone or os.path.join(repo, official.CLONE_DIRNAME)
    if not workbook or not os.path.isdir(clone):
        raise FileNotFoundError("spec workbook or open-trading-api clone not found")
    spec = official.load_workbook_apis(workbook)
    samples = official.load_samples(clone)
    official_ws = official.load_ws_samples(clone)
    sites = ours.load_call_sites(repo)
    our_ws = ours.load_ws(repo)
    allow = Allowlist.load(allowlist_path)

    findings = (
        check_rest(sites, spec, samples)
        + check_ws(our_ws, official_ws)
        + check_spec_consistency(spec, samples)
    )
    if include_coverage:
        findings += check_coverage(sites, spec, our_ws, official_ws, allow, repo)
    active = [f for f in findings if not allow.finding_allowed(f)]
    allowlisted = len(findings) - len(active)
    baseline = load_baseline(baseline_path)
    if not include_coverage:
        baseline = {k for k in baseline if not k.startswith("coverage-")}
    new_errors = [f for f in active if f.severity == "error" and f.key not in baseline]
    fixed = sorted(baseline - {f.key for f in active})
    stats = {
        "call_sites": len(sites),
        "call_sites_resolvable": sum(1 for s in sites if s.resolvable),
        "spec_urls": len(spec),
        "sample_urls": len(samples),
        "ws_trs_ours": len(our_ws),
        "ws_trs_official_samples": len(official_ws),
        "findings_total": len(findings),
        "allowlisted": allowlisted,
        "errors": sum(1 for f in active if f.severity == "error"),
        "info": sum(1 for f in active if f.severity == "info"),
        "baseline": len(baseline),
        "new_errors": len(new_errors),
        "baseline_fixed": len(fixed),
    }
    return {
        "stats": stats,
        "findings": active,
        "new_errors": new_errors,
        "baseline_fixed": fixed,
        "workbook": os.path.basename(workbook),
    }


def load_baseline(path: Optional[str]) -> Set[str]:
    if not path or not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return set(json.load(fh)["known"])


def write_baseline(path: str, findings: List[Finding]) -> int:
    keys = sorted({f.key for f in findings if f.severity == "error"})
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "_comment": "Known deviations still to be fixed. --check fails only on findings not listed here. "
                "Shrink this file as fixes land; never add to it to silence a new finding.",
                "known": keys,
            },
            fh,
            ensure_ascii=False,
            indent=1,
        )
        fh.write("\n")
    return len(keys)


def render_markdown(result: Dict[str, object]) -> str:
    stats = result["stats"]
    lines = [f"# KIS spec conformance ({result['workbook']})", ""]
    lines.append("| metric | value |")
    lines.append("|---|---|")
    for k, v in stats.items():
        lines.append(f"| {k} | {v} |")
    if result.get("new_errors"):
        lines += ["", f"## NEW (not in baseline, {len(result['new_errors'])})", ""]
        lines += [
            f"- `{f.where}` `{f.url}` {f.rule} — {f.detail}"
            for f in result["new_errors"]
        ]
    by_rule: Dict[str, List[Finding]] = {}
    for f in result["findings"]:
        by_rule.setdefault(f.rule, []).append(f)
    order = sorted(by_rule, key=lambda r: (SEVERITY[r] != "error", r))
    for rule in order:
        group = sorted(
            by_rule[rule], key=lambda f: (not f.order_surface, f.where, f.url)
        )
        lines += ["", f"## {rule} ({SEVERITY[rule]}, {len(group)})", ""]
        for f in group:
            flag = " **[order]**" if f.order_surface else ""
            lines.append(f"- `{f.where}` `{f.url}`{flag} — {f.detail}")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--check",
        action="store_true",
        help="exit 1 on an error-severity finding that is not in the baseline",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="with --check: ignore the baseline, require zero errors",
    )
    p.add_argument(
        "--write-baseline",
        action="store_true",
        help="record the current errors as the baseline",
    )
    p.add_argument(
        "--include-coverage",
        action="store_true",
        help="also report unwrapped official APIs and realtime TRs",
    )
    p.add_argument("--report", choices=["md", "json"], default="md")
    p.add_argument("--workbook")
    p.add_argument("--clone")
    p.add_argument("--repo", default=REPO)
    p.add_argument("--describe", metavar="URL", help="print the workbook field table for one URL and exit")
    p.add_argument("--with-response", action="store_true", help="with --describe: include response fields")
    args = p.parse_args(argv)
    if args.describe:
        workbook = args.workbook or official.find_workbook(args.repo)
        print("\n".join(official.describe_api(workbook, args.describe, args.with_response)))
        return 0
    result = run(
        args.repo,
        args.workbook,
        args.clone,
        args.include_coverage,
        baseline_path=None if args.strict else BASELINE,
    )
    if args.write_baseline:
        n = write_baseline(BASELINE, result["findings"])
        print(f"baseline written: {n} known errors -> {BASELINE}", file=sys.stderr)
        return 0
    if args.report == "json":
        payload = dict(result)
        payload["findings"] = [
            dict(asdict(f), severity=f.severity, key=f.key) for f in result["findings"]
        ]
        payload["new_errors"] = [f.key for f in result["new_errors"]]
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(result))
    if result["baseline_fixed"]:
        print(
            f"{len(result['baseline_fixed'])} baseline entries are fixed; run --write-baseline to ratchet.",
            file=sys.stderr,
        )
    if args.check and result["new_errors"]:
        for f in result["new_errors"]:
            print(f"NEW: {f.rule} {f.where} {f.url} {f.detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
