#!/usr/bin/env python3
"""
PyKIS 예외 처리 시스템 마이그레이션 스크립트

이 스크립트는 기존 PyKIS 코드를 새로운 통합 예외 처리 시스템으로 마이그레이션합니다.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ExceptionMigrator:
    """예외 처리 코드 마이그레이션 도구"""

    def __init__(self, project_root: str = "./pykis"):
        self.project_root = Path(project_root)
        self.modified_files = []
        self.issues_found = []

    def find_python_files(self) -> List[Path]:
        """프로젝트 내 모든 Python 파일 찾기"""
        return list(self.project_root.rglob("*.py"))

    def analyze_file(self, filepath: Path) -> List[dict]:
        """파일 분석하여 개선이 필요한 부분 찾기"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 1. except Exception as e 패턴 찾기
            pattern_generic = re.compile(r'^\s*except\s+Exception\s+as\s+\w+:')
            pattern_bare = re.compile(r'^\s*except:')
            pattern_no_raise = re.compile(r'^\s*except.*:\s*\n\s*(logging\.(error|warning)|print)\(.*\)\s*\n\s*(return|pass)', re.MULTILINE)

            for i, line in enumerate(lines, 1):
                # 너무 광범위한 예외 처리
                if pattern_generic.match(line):
                    issues.append({
                        'file': str(filepath),
                        'line': i,
                        'type': 'GENERIC_EXCEPTION',
                        'text': line.strip(),
                        'suggestion': '특정 예외 타입 사용 권장 (APIException, ValidationException 등)'
                    })

                # bare except
                if pattern_bare.match(line):
                    issues.append({
                        'file': str(filepath),
                        'line': i,
                        'type': 'BARE_EXCEPT',
                        'text': line.strip(),
                        'suggestion': '구체적인 예외 타입 지정 필요'
                    })

                # 예외를 먹고 None 반환
                if 'return None' in line and i > 1:
                    prev_lines = lines[max(0, i-5):i]
                    if any('except' in l for l in prev_lines):
                        issues.append({
                            'file': str(filepath),
                            'line': i,
                            'type': 'SWALLOW_EXCEPTION',
                            'text': line.strip(),
                            'suggestion': '예외를 raise하거나 명시적인 기본값 반환'
                        })

                # logging.error만 하고 raise 안함
                if 'logging.error' in line and i < len(lines) - 1:
                    next_lines = lines[i:min(i+3, len(lines))]
                    if not any('raise' in l for l in next_lines):
                        # except 블록 내부인지 확인
                        prev_lines = lines[max(0, i-10):i]
                        if any('except' in l for l in prev_lines):
                            issues.append({
                                'file': str(filepath),
                                'line': i,
                                'type': 'NO_RAISE_AFTER_LOG',
                                'text': line.strip(),
                                'suggestion': 'logging 후 예외를 반드시 raise'
                            })

        except Exception as e:
            logger.error(f"파일 분석 실패 {filepath}: {e}")

        return issues

    def generate_migration_plan(self) -> dict:
        """마이그레이션 계획 생성"""
        all_issues = []
        python_files = self.find_python_files()

        for filepath in python_files:
            # 테스트 파일과 마이그레이션 파일은 제외
            if 'test' in str(filepath) or 'migrate' in str(filepath):
                continue

            issues = self.analyze_file(filepath)
            if issues:
                all_issues.extend(issues)

        # 이슈 통계
        stats = {
            'total_files': len(python_files),
            'files_with_issues': len(set(i['file'] for i in all_issues)),
            'total_issues': len(all_issues),
            'by_type': {}
        }

        for issue in all_issues:
            issue_type = issue['type']
            if issue_type not in stats['by_type']:
                stats['by_type'][issue_type] = 0
            stats['by_type'][issue_type] += 1

        return {
            'stats': stats,
            'issues': all_issues
        }

    def generate_fixed_code(self, filepath: Path) -> str:
        """파일에 대한 수정된 코드 생성 (예시)"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # BaseAPI를 상속받는 클래스인지 확인
        if 'class ' in content and 'BaseAPI' in content:
            # ExceptionHandler import 추가
            import_line = "from ..core.exceptions import ExceptionHandler, APIException, ValidationException, handle_exceptions\n"

            # import 섹션 찾기
            import_end = content.find('\n\nclass')
            if import_end > 0:
                content = content[:import_end] + '\n' + import_line + content[import_end:]

            # 클래스 정의에 ExceptionHandler 추가
            class_pattern = re.compile(r'(class\s+\w+)\((.*BaseAPI.*)\):')
            content = class_pattern.sub(r'\1(\2, ExceptionHandler):', content)

            # __init__ 메서드에 ExceptionHandler 초기화 추가
            init_pattern = re.compile(r'(def __init__\(self.*?\):.*?)(BaseAPI\.__init__\(self.*?\))', re.DOTALL)
            def add_exception_handler(match):
                return match.group(1) + match.group(2) + '\n        ExceptionHandler.__init__(self)'

            content = init_pattern.sub(add_exception_handler, content)

            # except Exception as e를 더 구체적으로 변경
            content = re.sub(
                r'except Exception as (\w+):',
                r'except Exception as \1:  # TODO: 구체적 예외 타입으로 변경 필요',
                content
            )

            # return None을 예외로 변경 (except 블록 내)
            lines = content.split('\n')
            new_lines = []
            in_except = False

            for i, line in enumerate(lines):
                if 'except' in line:
                    in_except = True
                elif in_except and line and not line.startswith(' '):
                    in_except = False

                if in_except and 'return None' in line:
                    new_lines.append(line.replace('return None',
                                                 'raise  # TODO: None 반환 대신 예외 발생'))
                else:
                    new_lines.append(line)

            content = '\n'.join(new_lines)

        return content

    def create_report(self, plan: dict) -> str:
        """마이그레이션 보고서 생성"""
        report = []
        report.append("=" * 80)
        report.append("PyKIS 예외 처리 마이그레이션 분석 보고서")
        report.append("=" * 80)
        report.append("")

        # 통계
        stats = plan['stats']
        report.append("[ 전체 통계 ]")
        report.append(f"- 전체 파일 수: {stats['total_files']}")
        report.append(f"- 이슈가 있는 파일: {stats['files_with_issues']}")
        report.append(f"- 발견된 이슈: {stats['total_issues']}")
        report.append("")

        report.append("[ 이슈 유형별 통계 ]")
        for issue_type, count in stats['by_type'].items():
            report.append(f"- {issue_type}: {count}건")
        report.append("")

        # 파일별 이슈 그룹화
        file_issues = {}
        for issue in plan['issues']:
            filename = issue['file']
            if filename not in file_issues:
                file_issues[filename] = []
            file_issues[filename].append(issue)

        report.append("[ 파일별 상세 이슈 ]")
        report.append("")

        for filename, issues in sorted(file_issues.items())[:10]:  # 처음 10개 파일만
            report.append(f"📁 {filename}")
            for issue in issues[:5]:  # 파일당 처음 5개 이슈만
                report.append(f"  ├─ Line {issue['line']}: {issue['type']}")
                report.append(f"  │  코드: {issue['text']}")
                report.append(f"  │  개선: {issue['suggestion']}")
            report.append("")

        return "\n".join(report)


def main():
    """메인 실행 함수"""
    migrator = ExceptionMigrator()

    logger.info("PyKIS 예외 처리 분석 시작...")
    plan = migrator.generate_migration_plan()

    # 보고서 생성
    report = migrator.create_report(plan)

    # 보고서 파일로 저장
    report_file = "exception_migration_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"분석 완료! 보고서: {report_file}")
    print("\n" + "=" * 50)
    print("요약:")
    print(f"- 이슈가 있는 파일: {plan['stats']['files_with_issues']}개")
    print(f"- 전체 이슈: {plan['stats']['total_issues']}개")
    print("=" * 50)

    # 주요 권장사항
    print("\n[ 마이그레이션 권장사항 ]")
    print("1. 모든 API 클래스에 ExceptionHandler 상속 추가")
    print("2. except Exception을 구체적 예외로 변경")
    print("3. 예외를 먹지 말고 반드시 raise")
    print("4. logging.error 후에는 항상 raise")
    print("5. None 반환 대신 명시적 예외 발생")


if __name__ == "__main__":
    main()