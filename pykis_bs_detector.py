#!/usr/bin/env python3
"""
PyKIS 특화 BS Detector v1.0
한국투자증권 API 코드베이스 전용 BS(Bullshit) 패턴 탐지기

기본 BS Detector를 PyKIS 프로젝트 구조에 맞게 커스터마이징:
- 상대 import 경로 화이트리스트
- 금융 API 특화 보안 패턴
- PyKIS 코딩 컨벤션 검증
"""

import ast
import os
import re
import json
import sys
import subprocess
import argparse
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional, Pattern, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# ===================== 심각도 레벨 =====================
class Severity(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

# ===================== 규칙 카테고리 =====================
class RuleCategory(Enum):
    SECURITY = "보안"
    QUALITY = "코드품질"
    PERFORMANCE = "성능"
    RELIABILITY = "신뢰성"
    MAINTAINABILITY = "유지보수성"
    FAKE_PATTERN = "가짜패턴"
    FINANCE_API = "금융API"

# ===================== 이슈 데이터 클래스 =====================
@dataclass
class Issue:
    file: str
    line: Optional[int]
    message: str
    severity: Severity
    rule: str
    category: RuleCategory
    context: Optional[str] = None
    suggestion: Optional[str] = None

# ===================== PyKIS 특화 규칙 정의 =====================
PYKIS_BS_RULES = {
    # ===== 금융 API 특화 보안 =====
    "API_KEY_EXPOSED": {
        "desc": "API 키/시크릿 하드코딩",
        "severity": Severity.CRITICAL,
        "category": RuleCategory.SECURITY,
        "enabled": True,
    },
    "ACCOUNT_INFO_LEAK": {
        "desc": "계좌 정보 노출",
        "severity": Severity.CRITICAL,
        "category": RuleCategory.SECURITY,
        "enabled": True,
    },
    "UNSAFE_ORDER": {
        "desc": "안전하지 않은 주문 로직",
        "severity": Severity.HIGH,
        "category": RuleCategory.FINANCE_API,
        "enabled": True,
    },
    "MISSING_VALIDATION": {
        "desc": "입력 검증 누락",
        "severity": Severity.HIGH,
        "category": RuleCategory.FINANCE_API,
        "enabled": True,
    },
    
    # ===== 가짜 패턴 감지 (PyKIS 특화) =====
    "FAKE_SUCCESS": {
        "desc": "가짜 성공 메시지",
        "severity": Severity.MEDIUM,
        "category": RuleCategory.FAKE_PATTERN,
        "enabled": True,
    },
    "MOCK_DATA": {
        "desc": "운영용 Mock 데이터",
        "severity": Severity.HIGH,
        "category": RuleCategory.FAKE_PATTERN,
        "enabled": True,
    },
    "TODO_PRODUCTION": {
        "desc": "운영 코드의 TODO",
        "severity": Severity.MEDIUM,
        "category": RuleCategory.QUALITY,
        "enabled": True,
    },
    
    # ===== 보안 취약점 =====
    "EVAL_EXEC": {
        "desc": "eval/exec 사용",
        "severity": Severity.CRITICAL,
        "category": RuleCategory.SECURITY,
        "enabled": True,
    },
    "SQL_INJECTION": {
        "desc": "SQL 인젝션 취약점",
        "severity": Severity.CRITICAL,
        "category": RuleCategory.SECURITY,
        "enabled": True,
    },
    "UNSAFE_PICKLE": {
        "desc": "안전하지 않은 pickle 사용",
        "severity": Severity.HIGH,
        "category": RuleCategory.SECURITY,
        "enabled": True,
    },
    
    # ===== 코드 품질 =====
    "EMPTY_EXCEPT": {
        "desc": "빈 except 블록",
        "severity": Severity.HIGH,
        "category": RuleCategory.RELIABILITY,
        "enabled": True,
    },
    "BROAD_EXCEPT": {
        "desc": "너무 광범위한 예외 처리",
        "severity": Severity.MEDIUM,
        "category": RuleCategory.RELIABILITY,
        "enabled": True,
    },
    "COMPLEX_FUNCTION": {
        "desc": "과도하게 복잡한 함수",
        "severity": Severity.MEDIUM,
        "category": RuleCategory.MAINTAINABILITY,
        "enabled": True,
    },
    
    # ===== 성능 문제 =====
    "ASYNC_NO_AWAIT": {
        "desc": "async 함수에 await 없음",
        "severity": Severity.MEDIUM,
        "category": RuleCategory.PERFORMANCE,
        "enabled": True,
    },
    "REQUESTS_IN_ASYNC": {
        "desc": "async 함수 내 requests 동기 호출",
        "severity": Severity.MEDIUM,
        "category": RuleCategory.PERFORMANCE,
        "enabled": True,
    },
}

# ===================== PyKIS 특화 패턴 상수 =====================

# PyKIS 프로젝트 구조 화이트리스트
PYKIS_VALID_MODULES = {
    "pykis", "pykis.core", "pykis.account", "pykis.stock", "pykis.websocket",
    "pykis.program", "pykis.core.client", "pykis.core.auth", "pykis.core.config",
    "pykis.account.api", "pykis.account.balance", "pykis.stock.api", 
    "pykis.stock.condition", "pykis.stock.investor", "pykis.websocket.client",
    "core.client", "core.auth", "core.config", "core.base_api",
    "account.api", "account.balance", "stock.api", "stock.condition", 
    "stock.investor", "websocket.client", "program.trade"
}

# 상대 import 패턴 (정상)
RELATIVE_IMPORT_PATTERNS = [
    r"from\s+\.{1,2}[\w\.]*\s+import",
    r"from\s+\.\s+import",
    r"from\s+\.\.[\w\.]*\s+import"
]

# 금융 API 보안 패턴
FINANCE_SECURITY_PATTERNS = [
    r"(api_key|app_key|app_secret|access_token)\s*=\s*['\"][A-Za-z0-9]{20,}['\"]",
    r"(CANO|ACNT_PRDT_CD)\s*=\s*['\"][0-9]{8,}['\"]",  # 계좌번호 패턴
    r"password\s*=\s*['\"][^'\"]{4,}['\"]",
    r"secret\s*=\s*['\"][A-Za-z0-9]{20,}['\"]"
]

# 가짜 성공 패턴 (PyKIS 특화)
PYKIS_FAKE_PATTERNS = [
    r"print\(['\"].*성공.*완료.*['\"]",
    r"print\(['\"].*정상.*작동.*['\"]",
    r"return\s+True\s*#.*성공",
    r"✅.*완료.*됨",
    r"🚀.*성공.*구현",
    r"return\s+{\s*['\"]status['\"]:\s*['\"]success['\"]"
]

# Mock 데이터 패턴
MOCK_DATA_PATTERNS = [
    r"mock_.*=",
    r"dummy_.*=",
    r"test_data\s*=.*{.*}",
    r"fake_.*=",
    r"sample_.*=.*['\"].*['\"]"
]

# 위험한 주문 패턴
UNSAFE_ORDER_PATTERNS = [
    r"quantity\s*=\s*[0-9]{4,}",  # 너무 큰 수량
    r"price\s*=\s*[0-9]{7,}",     # 너무 큰 가격
    r"order_type\s*=\s*['\"].*['\"].*#.*테스트",
    r"buy\(.*quantity.*9999.*\)",  # 테스트성 대량 주문
]

# ===================== PyKIS 특화 의존성 검사기 =====================
class PyKISDependencyChecker:
    def __init__(self):
        self.installed_packages = self._get_installed_packages()
        self.project_modules = self._get_pykis_modules()
        
    def _get_installed_packages(self) -> Set[str]:
        """설치된 패키지 목록"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg["name"].lower().replace("-", "_") for pkg in packages}
        except:
            pass
        return set()
    
    def _get_pykis_modules(self) -> Set[str]:
        """PyKIS 프로젝트 모듈 목록"""
        modules = set()
        pykis_path = Path("pykis")
        if pykis_path.exists():
            for py_file in pykis_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    rel_path = py_file.relative_to(Path("."))
                    module_path = str(rel_path.with_suffix("")).replace("/", ".")
                    modules.add(module_path)
        return modules.union(PYKIS_VALID_MODULES)
    
    def check_import(self, module_name: str, line_content: str = "") -> Optional[str]:
        """PyKIS 특화 import 검증"""
        # 표준 라이브러리
        if module_name in sys.stdlib_module_names:
            return None
            
        # 상대 import 패턴 체크
        for pattern in RELATIVE_IMPORT_PATTERNS:
            if re.search(pattern, line_content):
                return None  # 상대 import는 정상
        
        # PyKIS 내부 모듈
        base_module = module_name.split('.')[0]
        if any(module_name.startswith(valid) for valid in self.project_modules):
            return None
        
        # 설치된 패키지
        pkg_name = base_module.lower().replace("-", "_")
        if pkg_name in self.installed_packages:
            return None
        
        # 알려진 패키지들 (PyKIS에서 사용)
        known_packages = {
            "pandas", "numpy", "requests", "asyncio", "websocket", "json", 
            "logging", "datetime", "typing", "dataclasses", "enum", "pathlib",
            "dotenv", "crypto", "base64", "collections", "ssl", "time"
        }
        if pkg_name in known_packages:
            return None
        
        return f"알 수 없는 모듈: {module_name}"

# ===================== PyKIS 특화 BS 탐지기 =====================
class PyKISBullshitDetector(ast.NodeVisitor):
    def __init__(self, src: str, filename: str = "<unknown>"):
        self.src = src
        self.filename = filename
        self.lines = src.split('\n')
        self.issues: List[Issue] = []
        self.dependency_checker = PyKISDependencyChecker()
        
        try:
            self.tree = ast.parse(src)
            self._annotate_parents(self.tree)
        except SyntaxError as e:
            self._add_issue(
                None, f"구문 오류: {e}", 
                severity=Severity.CRITICAL, 
                rule="SYNTAX_ERROR",
                category=RuleCategory.RELIABILITY
            )
            self.tree = None
    
    def _annotate_parents(self, tree):
        """AST 노드에 부모 참조 추가"""
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
    
    def run(self, severity_threshold: Severity = Severity.LOW) -> List[Issue]:
        if self.tree is None:
            return self.issues
        
        self.severity_threshold = severity_threshold
        
        # AST 기반 검사
        self.visit(self.tree)
        
        # 텍스트 패턴 검사
        self._check_finance_security_patterns()
        self._check_fake_patterns()
        self._check_mock_patterns()
        self._check_unsafe_order_patterns()
        
        # 의존성 검사
        self._check_dependencies()
        
        # 심각도 필터링
        return [
            issue for issue in self.issues
            if issue.severity.value >= severity_threshold.value
        ]
    
    def _add_issue(self, line: Optional[int], message: str, 
                   severity: Severity = Severity.MEDIUM, 
                   rule: str = "GENERAL",
                   category: RuleCategory = RuleCategory.QUALITY,
                   context: Optional[str] = None,
                   suggestion: Optional[str] = None):
        """이슈 추가"""
        self.issues.append(Issue(
            file=self.filename,
            line=line,
            message=message,
            severity=severity,
            rule=rule,
            category=category,
            context=context,
            suggestion=suggestion
        ))
    
    def _get_context(self, line: int, window: int = 2) -> str:
        """라인 주변 컨텍스트 추출"""
        start = max(0, line - window - 1)
        end = min(len(self.lines), line + window)
        context_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line - 1 else "    "
            context_lines.append(f"{prefix}{i+1:4d}: {self.lines[i]}")
        return "\n".join(context_lines)
    
    def _check_finance_security_patterns(self):
        """금융 API 보안 패턴 검사"""
        for i, line in enumerate(self.lines):
            line_num = i + 1
            
            for pattern in FINANCE_SECURITY_PATTERNS:
                if re.search(pattern, line):
                    self._add_issue(
                        line_num, "금융 API 민감 정보 하드코딩 의심",
                        severity=Severity.CRITICAL,
                        rule="API_KEY_EXPOSED",
                        category=RuleCategory.SECURITY,
                        context=self._get_context(line_num),
                        suggestion="환경 변수나 설정 파일 사용"
                    )
    
    def _check_fake_patterns(self):
        """가짜 패턴 검사"""
        for i, line in enumerate(self.lines):
            line_num = i + 1
            
            for pattern in PYKIS_FAKE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self._add_issue(
                        line_num, "가짜 성공 메시지 의심",
                        severity=Severity.MEDIUM,
                        rule="FAKE_SUCCESS",
                        category=RuleCategory.FAKE_PATTERN,
                        context=self._get_context(line_num),
                        suggestion="실제 검증 로직으로 교체"
                    )
    
    def _check_mock_patterns(self):
        """Mock 데이터 패턴 검사"""
        for i, line in enumerate(self.lines):
            line_num = i + 1
            
            for pattern in MOCK_DATA_PATTERNS:
                if re.search(pattern, line):
                    self._add_issue(
                        line_num, "운영용 Mock 데이터 의심",
                        severity=Severity.HIGH,
                        rule="MOCK_DATA",
                        category=RuleCategory.FAKE_PATTERN,
                        context=self._get_context(line_num),
                        suggestion="실제 데이터 소스로 교체 또는 테스트 환경으로 격리"
                    )
    
    def _check_unsafe_order_patterns(self):
        """위험한 주문 패턴 검사"""
        for i, line in enumerate(self.lines):
            line_num = i + 1
            
            for pattern in UNSAFE_ORDER_PATTERNS:
                if re.search(pattern, line):
                    self._add_issue(
                        line_num, "안전하지 않은 주문 로직",
                        severity=Severity.HIGH,
                        rule="UNSAFE_ORDER",
                        category=RuleCategory.FINANCE_API,
                        context=self._get_context(line_num),
                        suggestion="주문 검증 로직 추가 및 안전장치 구현"
                    )
    
    def _check_dependencies(self):
        """의존성 검사"""
        for i, line in enumerate(self.lines):
            line_num = i + 1
            
            # import 문 찾기
            import_match = re.match(r"^\s*(from\s+[\w\.]+\s+import|import\s+[\w\.]+)", line)
            if import_match:
                # 모듈명 추출
                if line.strip().startswith("from"):
                    match = re.match(r"from\s+([\w\.]+)\s+import", line)
                    if match:
                        module_name = match.group(1)
                else:
                    match = re.match(r"import\s+([\w\.]+)", line)
                    if match:
                        module_name = match.group(1)
                
                if 'module_name' in locals():
                    issue = self.dependency_checker.check_import(module_name, line)
                    if issue:
                        self._add_issue(
                            line_num, issue,
                            severity=Severity.LOW,  # PyKIS에서는 LOW로 조정
                            rule="UNKNOWN_MODULE",
                            category=RuleCategory.MAINTAINABILITY,
                            suggestion="모듈 경로 확인 또는 패키지 설치"
                        )
    
    # ===== AST 방문자 메서드들 =====
    
    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """함수 정의 검사"""
        # 복잡도 계산 (간단 버전)
        complexity = self._calculate_complexity(node)
        if complexity > 15:  # PyKIS용 임계값 조정
            self._add_issue(
                node.lineno, f"함수 '{node.name}'의 복잡도가 너무 높음: {complexity}",
                severity=Severity.MEDIUM,
                rule="COMPLEX_FUNCTION",
                category=RuleCategory.MAINTAINABILITY,
                suggestion="함수를 더 작은 단위로 분할"
            )
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """비동기 함수 검사"""
        # await 없는 async 함수
        has_await = any(isinstance(n, ast.Await) for n in ast.walk(node))
        if not has_await:
            self._add_issue(
                node.lineno, f"async 함수 '{node.name}'에 await가 없음",
                severity=Severity.MEDIUM,
                rule="ASYNC_NO_AWAIT",
                category=RuleCategory.PERFORMANCE,
                suggestion="일반 함수로 변경하거나 await 추가"
            )
        
        self.visit_FunctionDef(node)
    
    def visit_Call(self, node: ast.Call):
        """함수 호출 검사"""
        func_name = self._get_func_name(node)
        
        # eval/exec
        if func_name in {"eval", "exec"}:
            self._add_issue(
                node.lineno, f"위험한 함수 사용: {func_name}",
                severity=Severity.CRITICAL,
                rule="EVAL_EXEC",
                category=RuleCategory.SECURITY,
                suggestion="안전한 대안 사용"
            )
        
        # requests in async
        parent_func = self._find_enclosing_function(node)
        if parent_func and isinstance(parent_func, ast.AsyncFunctionDef):
            if self._is_module_call(node, "requests"):
                self._add_issue(
                    node.lineno, "async 함수에서 requests 동기 호출",
                    severity=Severity.MEDIUM,
                    rule="REQUESTS_IN_ASYNC",
                    category=RuleCategory.PERFORMANCE,
                    suggestion="aiohttp 또는 httpx 사용"
                )
        
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """예외 처리 검사"""
        # 빈 except 블록
        if len(node.body) == 0:
            self._add_issue(
                node.lineno, "빈 except 블록",
                severity=Severity.HIGH,
                rule="EMPTY_EXCEPT",
                category=RuleCategory.RELIABILITY,
                suggestion="적절한 예외 처리 추가"
            )
        elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self._add_issue(
                node.lineno, "예외를 무시하는 except: pass",
                severity=Severity.HIGH,
                rule="EMPTY_EXCEPT",
                category=RuleCategory.RELIABILITY,
                suggestion="로깅 또는 적절한 처리 추가"
            )
        
        # 너무 광범위한 예외
        if node.type and isinstance(node.type, ast.Name):
            if node.type.id in {"Exception", "BaseException"}:
                self._add_issue(
                    node.lineno, f"너무 광범위한 예외 처리: {node.type.id}",
                    severity=Severity.MEDIUM,
                    rule="BROAD_EXCEPT",
                    category=RuleCategory.RELIABILITY,
                    suggestion="구체적인 예외 타입 지정"
                )
        
        self.generic_visit(node)
    
    # ===== 헬퍼 메서드들 =====
    
    def _calculate_complexity(self, node) -> int:
        """간단한 복잡도 계산"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity
    
    def _get_func_name(self, node: ast.Call) -> str:
        """함수 호출 노드에서 함수명 추출"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""
    
    def _is_module_call(self, node: ast.Call, module: str) -> bool:
        """특정 모듈의 호출인지 확인"""
        if hasattr(node.func, 'value'):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == module
        return False
    
    def _find_enclosing_function(self, node):
        """노드를 감싸는 함수 찾기"""
        current = getattr(node, 'parent', None)
        while current:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current
            current = getattr(current, 'parent', None)
        return None

# ===================== 리포트 생성 =====================
def generate_pykis_report(issues: List[Issue], files_scanned: int) -> str:
    """PyKIS 특화 리포트 생성"""
    lines = []
    lines.append("# PyKIS 코드베이스 BS 탐지 보고서\n")
    lines.append(f"**스캔한 파일**: {files_scanned}개")
    lines.append(f"**발견된 이슈**: {len(issues)}개\n")
    
    if not issues:
        lines.append("✅ **BS 패턴이 발견되지 않았습니다.**")
        return "\n".join(lines)
    
    # 심각도별 요약
    lines.append("## 심각도별 요약\n")
    severity_counts = defaultdict(int)
    for issue in issues:
        severity_counts[issue.severity] += 1
    
    for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
        count = severity_counts[severity]
        if count > 0:
            emoji = {
                Severity.CRITICAL: "🔴",
                Severity.HIGH: "🟠", 
                Severity.MEDIUM: "🟡",
                Severity.LOW: "🟢"
            }[severity]
            lines.append(f"- {emoji} **{severity.name}**: {count}개")
    
    # 카테고리별 분석
    lines.append("\n## 카테고리별 분석\n")
    category_counts = defaultdict(int)
    for issue in issues:
        category_counts[issue.category] += 1
    
    for category, count in category_counts.items():
        lines.append(f"- **{category.value}**: {count}개")
    
    # 주요 이슈 상세
    lines.append("\n## 주요 이슈 상세\n")
    critical_high = [i for i in issues if i.severity in [Severity.CRITICAL, Severity.HIGH]]
    
    for issue in critical_high[:10]:  # 상위 10개만
        location = f"{issue.file}:{issue.line}" if issue.line else issue.file
        lines.append(f"### [{issue.severity.name}] {location}")
        lines.append(f"- **문제**: {issue.message}")
        if issue.suggestion:
            lines.append(f"- **해결책**: {issue.suggestion}")
        lines.append("")
    
    return "\n".join(lines)

# ===================== 메인 함수 =====================
def scan_pykis_file(filepath: str, severity_threshold: Severity) -> List[Issue]:
    """PyKIS 파일 스캔"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        detector = PyKISBullshitDetector(source, filepath)
        return detector.run(severity_threshold)
    except Exception as e:
        return [Issue(
            file=filepath,
            line=None,
            message=f"파일 읽기 오류: {e}",
            severity=Severity.HIGH,
            rule="FILE_ERROR",
            category=RuleCategory.RELIABILITY
        )]

def main():
    parser = argparse.ArgumentParser(
        description="PyKIS 특화 BS Detector v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("path", help="스캔할 파일 또는 디렉토리 경로")
    parser.add_argument("--severity", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        default="MEDIUM", help="최소 심각도 레벨")
    parser.add_argument("--json", action="store_true", help="JSON 형식 출력")
    
    args = parser.parse_args()
    
    severity_threshold = Severity[args.severity]
    all_issues = []
    files_scanned = 0
    
    # 파일 스캔
    if os.path.isfile(args.path):
        issues = scan_pykis_file(args.path, severity_threshold)
        all_issues.extend(issues)
        files_scanned = 1
    else:
        # 디렉토리 스캔
        for root, dirs, files in os.walk(args.path):
            # __pycache__ 등 제외
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache'}]
            
            for filename in files:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    issues = scan_pykis_file(filepath, severity_threshold)
                    all_issues.extend(issues)
                    files_scanned += 1
    
    # 결과 출력
    if args.json:
        data = {
            "files_scanned": files_scanned,
            "total_issues": len(all_issues),
            "issues": [
                {
                    "file": issue.file,
                    "line": issue.line,
                    "message": issue.message,
                    "severity": issue.severity.name,
                    "rule": issue.rule,
                    "category": issue.category.value,
                    "suggestion": issue.suggestion
                }
                for issue in all_issues
            ]
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(generate_pykis_report(all_issues, files_scanned))
    
    # 종료 코드
    critical_high = [i for i in all_issues if i.severity in [Severity.CRITICAL, Severity.HIGH]]
    sys.exit(1 if critical_high else 0)

if __name__ == "__main__":
    main()