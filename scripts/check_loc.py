#!/usr/bin/env python3
"""
LOC (Lines of Code) Gate Check Script

CI/CD 파이프라인에서 파일별 줄 수 제한을 검증하는 스크립트.
max-line-count 임계값을 초과하는 파일이 있으면 실패 코드를 반환.

Usage:
    python scripts/check_loc.py [--threshold 1500] [--path pykis/]
    python scripts/check_loc.py --json  # JSON 형식 출력
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, NamedTuple


class FileStats(NamedTuple):
    """파일 통계 정보"""

    path: str
    lines: int
    exceeds: bool
    excess: int


def count_lines(file_path: Path) -> int:
    """파일의 줄 수를 계산"""
    try:
        with open(file_path, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def scan_directory(
    src_path: Path, threshold: int, extensions: tuple = (".py",)
) -> List[FileStats]:
    """디렉토리 내 모든 파일을 스캔하여 통계 수집"""
    results = []

    for file_path in src_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            lines = count_lines(file_path)
            exceeds = lines > threshold
            excess = lines - threshold if exceeds else 0

            results.append(
                FileStats(
                    path=str(file_path.relative_to(src_path.parent)),
                    lines=lines,
                    exceeds=exceeds,
                    excess=excess,
                )
            )

    return sorted(results, key=lambda x: x.lines, reverse=True)


def print_report(
    results: List[FileStats], threshold: int, json_output: bool = False
) -> int:
    """결과 리포트 출력 및 종료 코드 반환"""
    exceeding_files = [r for r in results if r.exceeds]

    if json_output:
        output = {
            "threshold": threshold,
            "total_files": len(results),
            "exceeding_files": len(exceeding_files),
            "passed": len(exceeding_files) == 0,
            "files": [
                {
                    "path": r.path,
                    "lines": r.lines,
                    "exceeds": r.exceeds,
                    "excess": r.excess,
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 80)
        print(f"LOC Gate Check (Threshold: {threshold} lines)")
        print("=" * 80)
        print()

        # 초과 파일 목록
        if exceeding_files:
            print("EXCEEDING FILES:")
            print("-" * 80)
            for f in exceeding_files:
                status = "FAIL"
                print(f"  [{status}] {f.path}: {f.lines} lines (+{f.excess} over)")
            print()

        # 상위 10개 파일
        print("TOP 10 FILES BY LOC:")
        print("-" * 80)
        for f in results[:10]:
            status = "FAIL" if f.exceeds else "PASS"
            bar_len = min(f.lines // 100, 40)
            bar = "#" * bar_len
            print(f"  [{status}] {f.lines:>5} | {bar:<40} | {f.path}")
        print()

        # 요약
        print("=" * 80)
        print(f"Total Files: {len(results)}")
        print(f"Exceeding Threshold: {len(exceeding_files)}")
        print(f"Status: {'FAILED' if exceeding_files else 'PASSED'}")
        print("=" * 80)

    return 1 if exceeding_files else 0


def main():
    parser = argparse.ArgumentParser(
        description="Check LOC (Lines of Code) for CI gate"
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=1500,
        help="Maximum lines per file (default: 1500)",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default="pykis/",
        help="Path to scan (default: pykis/)",
    )
    parser.add_argument(
        "--json", "-j", action="store_true", help="Output in JSON format"
    )
    parser.add_argument(
        "--extensions",
        "-e",
        type=str,
        default=".py",
        help="Comma-separated file extensions (default: .py)",
    )

    args = parser.parse_args()

    src_path = Path(args.path)
    if not src_path.exists():
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)

    extensions = tuple(ext.strip() for ext in args.extensions.split(","))
    results = scan_directory(src_path, args.threshold, extensions)

    exit_code = print_report(results, args.threshold, args.json)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
