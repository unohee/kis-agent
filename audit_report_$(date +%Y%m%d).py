#!/usr/bin/env python3
"""
PyKIS 코드베이스 감사 보고서 생성기
BS Detector 결과를 종합하여 BS 지수 계산 및 위험 요소 분석
"""

import subprocess
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def run_bs_detector():
    """BS Detector 실행하여 JSON 결과 반환"""
    try:
        result = subprocess.run([
            sys.executable, str(Path.home() / ".claude/tools/bs_detector.py"),
            "pykis/", "--severity", "LOW", "--json"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"BS Detector 실행 실패: {result.stderr}")
            return None
    except Exception as e:
        print(f"BS Detector 실행 중 오류: {e}")
        return None

def calculate_bs_index(data):
    """BS 지수 계산"""
    if not data:
        return 0.0
    
    # 가중치 정의
    severity_weights = {
        "CRITICAL": 10,
        "HIGH": 5, 
        "MEDIUM": 3,
        "LOW": 1
    }
    
    total_weighted_score = 0
    total_issues = data.get("total_issues", 0)
    files_scanned = data.get("files_scanned", 1)
    
    # 심각도별 가중 점수 계산
    for severity, count in data.get("by_severity", {}).items():
        weight = severity_weights.get(severity, 1)
        total_weighted_score += count * weight
    
    # BS 지수 = 총 가중점수 / 파일수
    bs_index = total_weighted_score / files_scanned if files_scanned > 0 else 0
    
    return bs_index

def analyze_critical_patterns(data):
    """CRITICAL 패턴 심층 분석"""
    critical_issues = []
    high_issues = []
    
    for issue in data.get("issues", []):
        if issue["severity"] == "CRITICAL":
            critical_issues.append(issue)
        elif issue["severity"] == "HIGH":
            high_issues.append(issue)
    
    return critical_issues, high_issues

def categorize_issues(data):
    """이슈 카테고리별 분석"""
    category_analysis = defaultdict(list)
    rule_frequency = Counter()
    
    for issue in data.get("issues", []):
        category = issue["category"]
        rule = issue["rule"]
        
        category_analysis[category].append(issue)
        rule_frequency[rule] += 1
    
    return dict(category_analysis), rule_frequency

def generate_recommendations(data):
    """개선 권고사항 생성"""
    recommendations = []
    
    critical_issues, high_issues = analyze_critical_patterns(data)
    
    # CRITICAL 이슈 기반 권고
    if critical_issues:
        recommendations.append({
            "priority": "URGENT",
            "title": "즉시 수정 필요한 보안/신뢰성 이슈",
            "count": len(critical_issues),
            "action": "CRITICAL 등급 이슈를 즉시 수정하여 보안 위험 제거"
        })
    
    # HIGH 이슈 기반 권고
    if high_issues:
        recommendations.append({
            "priority": "HIGH", 
            "title": "환각 패턴 및 의존성 문제",
            "count": len(high_issues),
            "action": "존재하지 않는 패키지 import 및 의존성 문제 해결"
        })
    
    # 코드 품질 개선
    quality_issues = [i for i in data.get("issues", []) if i["category"] == "코드품질"]
    if quality_issues:
        recommendations.append({
            "priority": "MEDIUM",
            "title": "코드 품질 개선",
            "count": len(quality_issues),
            "action": "코딩 표준 준수 및 유지보수성 향상"
        })
    
    return recommendations

def generate_report():
    """최종 감사 보고서 생성"""
    print("=" * 60)
    print("🔍 PyKIS 코드베이스 품질 감사 보고서")
    print("=" * 60)
    print(f"📅 감사 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # BS Detector 실행
    print("📊 BS Detector 실행 중...")
    data = run_bs_detector()
    
    if not data:
        print("❌ BS Detector 실행 실패")
        return
    
    # 기본 통계
    files_scanned = data.get("files_scanned", 0)
    total_issues = data.get("total_issues", 0)
    
    print(f"📁 스캔된 파일: {files_scanned}개")
    print(f"🚨 발견된 이슈: {total_issues}개")
    print()
    
    # BS 지수 계산
    bs_index = calculate_bs_index(data)
    print(f"🎯 BS 지수: {bs_index:.2f}")
    
    # BS 지수 등급 판정
    if bs_index < 5.0:
        grade = "🟢 양호"
    elif bs_index < 10.0:
        grade = "🟡 주의"
    elif bs_index < 20.0:
        grade = "🟠 경고"
    else:
        grade = "🔴 위험"
    
    print(f"📈 품질 등급: {grade}")
    print()
    
    # 심각도별 분석
    print("📋 심각도별 이슈 분포:")
    for severity, count in data.get("by_severity", {}).items():
        print(f"  {severity}: {count}개")
    print()
    
    # CRITICAL 패턴 분석
    critical_issues, high_issues = analyze_critical_patterns(data)
    
    if critical_issues:
        print("🚨 CRITICAL 이슈 (즉시 수정 필요):")
        for issue in critical_issues[:5]:  # 상위 5개만 표시
            location = f"{issue['file']}:{issue['line']}" if issue['line'] else issue['file']
            print(f"  - {location}: {issue['message']}")
        if len(critical_issues) > 5:
            print(f"  ... 외 {len(critical_issues) - 5}개")
        print()
    
    # 카테고리별 분석
    category_analysis, rule_frequency = categorize_issues(data)
    
    print("📊 카테고리별 이슈:")
    for category, issues in category_analysis.items():
        print(f"  {category}: {len(issues)}개")
    print()
    
    # 자주 발생하는 규칙
    print("🔄 자주 발생하는 패턴 (상위 5개):")
    for rule, count in rule_frequency.most_common(5):
        print(f"  {rule}: {count}회")
    print()
    
    # 개선 권고사항
    recommendations = generate_recommendations(data)
    
    print("💡 개선 권고사항:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. [{rec['priority']}] {rec['title']}")
        print(f"     - 이슈 수: {rec['count']}개")
        print(f"     - 조치: {rec['action']}")
        print()
    
    # 최종 결론
    print("🎯 최종 평가:")
    if bs_index < 5.0:
        print("✅ 코드 품질이 양호합니다. 발견된 이슈들을 점진적으로 개선하세요.")
    elif bs_index < 10.0:
        print("⚠️  일부 개선이 필요합니다. HIGH/CRITICAL 이슈를 우선 처리하세요.")
    elif bs_index < 20.0:
        print("🔶 상당한 개선이 필요합니다. 체계적인 리팩토링을 고려하세요.")
    else:
        print("🚨 긴급한 개선이 필요합니다. 보안 및 신뢰성 이슈를 즉시 해결하세요.")
    
    print()
    print("📝 상세 보고서는 BS Detector --markdown 옵션으로 확인 가능합니다.")
    print("=" * 60)

if __name__ == "__main__":
    generate_report()