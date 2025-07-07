#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
토큰 읽기/쓰기 기능 테스트 스크립트
"""

import os
import sys
import json
import shutil
from datetime import datetime, timedelta

# pykis 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pykis.core.auth import save_token, read_token, token_tmp

def test_token_functions():
    """토큰 읽기/쓰기 기능을 테스트합니다."""
    print("=== 토큰 기능 테스트 시작 ===")
    
    # 0. 실제 토큰 파일 백업 (실제 토큰을 보호하기 위해)
    backup_path = token_tmp + '.backup'
    if os.path.exists(token_tmp):
        shutil.copy2(token_tmp, backup_path)
        print(f"0. 실제 토큰 파일 백업: {backup_path}")
    
    try:
        # 1. 현재 토큰 파일 경로 확인
        print(f"1. 토큰 파일 경로: {token_tmp}")
        print(f"   파일 존재 여부: {os.path.exists(token_tmp)}")
        
        # 2. 현재 토큰 읽기 테스트
        print("\n2. 현재 토큰 읽기 테스트:")
        current_token = read_token()
        if current_token:
            print(f"   토큰 읽기 성공: 토큰 있음 (실제 내용은 보안상 생략)")
        else:
            print("   토큰이 없거나 만료됨")
        
        # 3. 새로운 토큰 쓰기 테스트 (테스트용 토큰으로)
        print("\n3. 새로운 토큰 쓰기 테스트:")
        test_token = "test_token_12345_for_testing_only"  # [변경] 테스트임을 명확히 표시
        test_expired = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            save_token(test_token, test_expired)
            print(f"   토큰 저장 성공")
            print(f"   저장된 토큰: {test_token}")
            print(f"   만료 시간: {test_expired}")
        except Exception as e:
            print(f"   토큰 저장 실패: {e}")
        
        # 4. 저장된 토큰 다시 읽기 테스트
        print("\n4. 저장된 토큰 다시 읽기 테스트:")
        saved_token = read_token()
        if saved_token:
            print(f"   읽기 성공: 토큰 정보 확인됨")
        else:
            print("   읽기 실패")
        
        # 5. 파일 내용 직접 확인
        print("\n5. 파일 내용 직접 확인:")
        try:
            with open(token_tmp, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
                print(f"   파일 구조 확인: {list(file_content.keys())}")  # [변경] 실제 토큰값 대신 구조만 확인
        except Exception as e:
            print(f"   파일 읽기 오류: {e}")
        
    finally:
        # 6. 실제 토큰 파일 복구 (테스트 후 원본 복구)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, token_tmp)
            os.remove(backup_path)
            print(f"\n6. 실제 토큰 파일 복구 완료")
        else:
            print(f"\n6. 백업 파일이 없어 복구하지 않음")
    
    print("\n=== 토큰 기능 테스트 완료 ===")

if __name__ == "__main__":
    test_token_functions() 