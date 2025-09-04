#!/usr/bin/env python3
"""
PyKIS 프로젝트 메서드 반환 타입 분석 도구
Dict 반환 패턴과 타입 힌팅 일관성을 체계적으로 분석합니다.

생성일: 2025-08-27
목적: 메서드 반환 타입의 일관성 검증 및 리팩토링 가이드 제공
"""

import ast
import os
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MethodReturnTypeAnalyzer:
    """메서드 반환 타입 분석기"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.analysis_results = {
            'dict_typed': [],           # Dict/dict로 명시된 메서드들
            'dict_no_hint': [],         # Dict를 반환하지만 타입 힌트가 없는 메서드들
            'non_dict_typed': [],       # Dict가 아닌 다른 타입을 반환하는 메서드들
            'no_type_hints': [],        # 타입 힌트가 전혀 없는 메서드들
            'optional_dict': [],        # Optional[Dict] 형태
            'union_types': [],          # Union 타입들
            'complex_types': [],        # 복잡한 타입 힌트들
        }
        
    def analyze_project(self) -> Dict[str, Any]:
        """프로젝트 전체 분석"""
        logger.info(f"PyKIS 프로젝트 분석 시작: {self.root_path}")
        
        # pykis 패키지 내 모든 Python 파일 찾기
        python_files = list((self.root_path / 'pykis').rglob('*.py'))
        
        logger.info(f"분석 대상 파일 수: {len(python_files)}")
        
        for py_file in python_files:
            if py_file.name == '__init__.py' and py_file.stat().st_size < 100:
                continue  # 작은 __init__.py 파일들은 스킵
                
            try:
                self._analyze_file(py_file)
            except Exception as e:
                logger.error(f"파일 분석 실패 {py_file}: {e}")
                
        return self._generate_report()
    
    def _analyze_file(self, file_path: Path):
        """단일 파일 분석"""
        logger.debug(f"파일 분석: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._analyze_method(node, file_path, source_code)
                    
        except SyntaxError as e:
            logger.error(f"구문 오류 {file_path}: {e}")
        except Exception as e:
            logger.error(f"파일 처리 오류 {file_path}: {e}")
    
    def _analyze_method(self, node: ast.FunctionDef, file_path: Path, source_code: str):
        """개별 메서드 분석"""
        method_name = node.name
        
        # 프라이빗 메서드나 특수 메서드는 제외
        if method_name.startswith('__') and method_name.endswith('__'):
            return
            
        # 반환 타입 힌트 분석
        return_annotation = self._get_return_annotation(node)
        
        # 실제 반환 패턴 분석
        actual_returns = self._analyze_return_statements(node)
        
        # 메서드 정보 구성
        method_info = {
            'file': str(file_path.relative_to(self.root_path)),
            'method': method_name,
            'line': node.lineno,
            'return_annotation': return_annotation,
            'actual_returns': actual_returns,
            'is_dict_method': self._is_dict_returning_method(actual_returns),
        }
        
        # 카테고리별 분류
        self._categorize_method(method_info)
    
    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """반환 타입 어노테이션 추출"""
        if node.returns is None:
            return None
            
        return ast.unparse(node.returns)
    
    def _analyze_return_statements(self, node: ast.FunctionDef) -> List[str]:
        """반환문들 분석"""
        returns = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                try:
                    return_expr = ast.unparse(child.value)
                    returns.append(return_expr)
                except:
                    returns.append("복잡한_반환문")
                    
        return returns
    
    def _is_dict_returning_method(self, returns: List[str]) -> bool:
        """Dict를 반환하는 메서드인지 판단"""
        dict_patterns = [
            r'\{.*\}',              # 딕셔너리 리터럴
            r'dict\(',              # dict() 호출
            r'\.to_dict\(',         # .to_dict() 호출
            r'response',            # response 변수 (보통 dict)
            r'result',              # result 변수 (보통 dict)
        ]
        
        for return_stmt in returns:
            for pattern in dict_patterns:
                if re.search(pattern, return_stmt, re.IGNORECASE):
                    return True
                    
        return False
    
    def _categorize_method(self, method_info: Dict[str, Any]):
        """메서드를 적절한 카테고리에 분류"""
        annotation = method_info['return_annotation']
        is_dict_method = method_info['is_dict_method']
        
        if annotation is None:
            if is_dict_method:
                self.analysis_results['dict_no_hint'].append(method_info)
            else:
                self.analysis_results['no_type_hints'].append(method_info)
        else:
            # 타입 힌트가 있는 경우
            annotation_lower = annotation.lower()
            
            if 'optional[dict' in annotation_lower or 'dict[' in annotation_lower or annotation_lower == 'dict':
                self.analysis_results['dict_typed'].append(method_info)
            elif 'optional[' in annotation_lower:
                self.analysis_results['optional_dict'].append(method_info)
            elif 'union[' in annotation_lower:
                self.analysis_results['union_types'].append(method_info)
            elif any(t in annotation_lower for t in ['str', 'int', 'bool', 'list', 'tuple', 'float']):
                self.analysis_results['non_dict_typed'].append(method_info)
            else:
                self.analysis_results['complex_types'].append(method_info)
    
    def _generate_report(self) -> Dict[str, Any]:
        """분석 결과 리포트 생성"""
        report = {
            'summary': {
                'total_methods': sum(len(methods) for methods in self.analysis_results.values()),
                'dict_typed_count': len(self.analysis_results['dict_typed']),
                'dict_no_hint_count': len(self.analysis_results['dict_no_hint']),
                'non_dict_typed_count': len(self.analysis_results['non_dict_typed']),
                'no_type_hints_count': len(self.analysis_results['no_type_hints']),
            },
            'categories': self.analysis_results,
            'consistency_score': self._calculate_consistency_score(),
            'recommendations': self._generate_recommendations(),
        }
        
        return report
    
    def _calculate_consistency_score(self) -> float:
        """타입 힌팅 일관성 점수 계산 (0-100)"""
        total = sum(len(methods) for methods in self.analysis_results.values())
        if total == 0:
            return 0.0
            
        typed_methods = (
            len(self.analysis_results['dict_typed']) +
            len(self.analysis_results['non_dict_typed']) +
            len(self.analysis_results['optional_dict']) +
            len(self.analysis_results['union_types']) +
            len(self.analysis_results['complex_types'])
        )
        
        return (typed_methods / total) * 100
    
    def _generate_recommendations(self) -> List[str]:
        """개선 권고사항 생성"""
        recommendations = []
        
        dict_no_hint_count = len(self.analysis_results['dict_no_hint'])
        if dict_no_hint_count > 0:
            recommendations.append(
                f"Dict를 반환하지만 타입 힌트가 없는 메서드 {dict_no_hint_count}개에 "
                "Optional[Dict[str, Any]] 타입 힌트 추가 권장"
            )
        
        no_hints_count = len(self.analysis_results['no_type_hints'])
        if no_hints_count > 0:
            recommendations.append(
                f"타입 힌트가 없는 메서드 {no_hints_count}개에 적절한 반환 타입 힌트 추가 권장"
            )
        
        consistency_score = self._calculate_consistency_score()
        if consistency_score < 80:
            recommendations.append(
                f"타입 힌팅 일관성이 {consistency_score:.1f}%로 낮습니다. "
                "프로젝트 전반적인 타입 힌팅 표준화 권장"
            )
            
        return recommendations

def main():
    """메인 실행 함수"""
    analyzer = MethodReturnTypeAnalyzer('/home/unohee/tools/pykis')
    report = analyzer.analyze_project()
    
    print("=" * 80)
    print("PyKIS 프로젝트 메서드 반환 타입 분석 리포트")
    print("=" * 80)
    
    # 요약 정보
    summary = report['summary']
    print(f"\n📊 전체 요약:")
    print(f"  • 전체 메서드 수: {summary['total_methods']}개")
    print(f"  • Dict 타입 명시: {summary['dict_typed_count']}개")
    print(f"  • Dict 반환, 타입 힌트 없음: {summary['dict_no_hint_count']}개")
    print(f"  • Dict 외 타입 명시: {summary['non_dict_typed_count']}개")
    print(f"  • 타입 힌트 없음: {summary['no_type_hints_count']}개")
    print(f"  • 타입 힌팅 일관성: {report['consistency_score']:.1f}%")
    
    # 카테고리별 상세 정보
    categories = report['categories']
    
    print(f"\n🎯 1. Dict/dict 반환 타입 명시된 메서드들 ({len(categories['dict_typed'])}개):")
    for method in categories['dict_typed'][:5]:  # 상위 5개만 표시
        print(f"  • {method['file']}:{method['line']} - {method['method']}() -> {method['return_annotation']}")
    if len(categories['dict_typed']) > 5:
        print(f"    ... 외 {len(categories['dict_typed']) - 5}개 더")
    
    print(f"\n❓ 2. Dict 반환하지만 타입 힌트 없는 메서드들 ({len(categories['dict_no_hint'])}개):")
    for method in categories['dict_no_hint'][:5]:
        print(f"  • {method['file']}:{method['line']} - {method['method']}()")
        if method['actual_returns']:
            print(f"    반환값: {', '.join(method['actual_returns'][:2])}")
    if len(categories['dict_no_hint']) > 5:
        print(f"    ... 외 {len(categories['dict_no_hint']) - 5}개 더")
    
    print(f"\n🔢 3. Dict가 아닌 다른 타입 반환 메서드들 ({len(categories['non_dict_typed'])}개):")
    for method in categories['non_dict_typed'][:5]:
        print(f"  • {method['file']}:{method['line']} - {method['method']}() -> {method['return_annotation']}")
    if len(categories['non_dict_typed']) > 5:
        print(f"    ... 외 {len(categories['non_dict_typed']) - 5}개 더")
    
    print(f"\n⚪ 4. 타입 힌트가 전혀 없는 메서드들 ({len(categories['no_type_hints'])}개):")
    for method in categories['no_type_hints'][:5]:
        print(f"  • {method['file']}:{method['line']} - {method['method']}()")
    if len(categories['no_type_hints']) > 5:
        print(f"    ... 외 {len(categories['no_type_hints']) - 5}개 더")
    
    # Optional, Union, 복잡한 타입들
    other_categories = ['optional_dict', 'union_types', 'complex_types']
    for cat in other_categories:
        if categories[cat]:
            print(f"\n🔀 {cat.replace('_', ' ').title()} ({len(categories[cat])}개):")
            for method in categories[cat][:3]:
                print(f"  • {method['file']}:{method['line']} - {method['method']}() -> {method['return_annotation']}")
    
    # 권고사항
    print(f"\n💡 개선 권고사항:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n🔍 패턴 분석:")
    
    # 파일별 집계
    file_stats = {}
    for category, methods in categories.items():
        for method in methods:
            file_key = method['file']
            if file_key not in file_stats:
                file_stats[file_key] = {'total': 0, 'typed': 0, 'dict_methods': 0}
            file_stats[file_key]['total'] += 1
            if method['return_annotation']:
                file_stats[file_key]['typed'] += 1
            if method['is_dict_method']:
                file_stats[file_key]['dict_methods'] += 1
    
    # 가장 많은 메서드를 가진 파일들
    top_files = sorted(file_stats.items(), key=lambda x: x[1]['total'], reverse=True)[:5]
    
    print(f"\n📁 메서드 수가 많은 파일들:")
    for file_path, stats in top_files:
        typing_ratio = (stats['typed'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"  • {file_path}: {stats['total']}개 메서드 (타입 힌팅: {typing_ratio:.1f}%, Dict 메서드: {stats['dict_methods']}개)")
    
    print(f"\n" + "=" * 80)
    print("분석 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()