#!/usr/bin/env python3
"""
examples_llm의 chk_*.py 파일에서 COLUMN_MAPPING을 추출하여
pykis TypedDict 응답 모델을 업데이트하기 위한 매핑 정보를 생성하는 스크립트
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def extract_api_info(file_path: Path) -> Optional[Dict]:
    """
    chk_*.py 파일에서 API 정보를 추출

    Args:
        file_path: chk_*.py 파일 경로

    Returns:
        API 정보 딕셔너리 또는 None
    """
    try:
        content = file_path.read_text(encoding='utf-8')

        # API 이름 추출 (파일명에서)
        api_name = file_path.stem.replace('chk_', '')

        # 주석에서 API 설명 추출 (예: # [국내주식] 기본시세 > 주식현재가 시세[v1_국내주식-008])
        api_desc_match = re.search(r'#\s*\[(.*?)\].*?>\s*(.*?)\[v1_(.*?)\]', content)
        api_category = api_desc_match.group(1) if api_desc_match else None
        api_description = api_desc_match.group(2).strip() if api_desc_match else None
        api_version = api_desc_match.group(3) if api_desc_match else None

        # COLUMN_MAPPING 추출
        column_mapping = {}
        mapping_match = re.search(r'COLUMN_MAPPING\s*=\s*\{([^}]+)\}', content, re.DOTALL)
        if mapping_match:
            mapping_str = mapping_match.group(0)
            try:
                # AST를 사용하여 안전하게 파싱
                tree = ast.parse(mapping_str)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == 'COLUMN_MAPPING':
                                if isinstance(node.value, ast.Dict):
                                    for key, value in zip(node.value.keys, node.value.values):
                                        if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
                                            column_mapping[key.value] = value.value
            except:
                pass

        # 함수 시그니처에서 output1, output2 구분 확인
        has_multiple_outputs = 'result1, result2' in content or 'output1' in content and 'output2' in content

        return {
            'api_name': api_name,
            'file_path': str(file_path),
            'category': api_category,
            'description': api_description,
            'version': api_version,
            'column_mapping': column_mapping,
            'has_multiple_outputs': has_multiple_outputs,
            'parent_dir': file_path.parent.name
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def find_all_chk_files(base_dir: Path) -> List[Path]:
    """examples_llm 디렉토리에서 모든 chk_*.py 파일 찾기"""
    return list(base_dir.glob('**/chk_*.py'))


def group_by_category(api_infos: List[Dict]) -> Dict[str, List[Dict]]:
    """카테고리별로 API 정보 그룹화"""
    grouped = {}
    for info in api_infos:
        parent_dir = info['parent_dir']
        if parent_dir not in grouped:
            grouped[parent_dir] = []
        grouped[parent_dir].append(info)
    return grouped


def generate_typeddict_code(api_info: Dict) -> str:
    """
    COLUMN_MAPPING 정보로부터 TypedDict 클래스 코드 생성

    Args:
        api_info: extract_api_info()로부터 얻은 정보

    Returns:
        TypedDict 클래스 정의 코드
    """
    api_name = api_info['api_name']
    column_mapping = api_info['column_mapping']
    description = api_info.get('description', api_name)

    # 클래스명 생성 (camelCase)
    class_name_parts = [word.capitalize() for word in api_name.split('_')]
    output_class_name = ''.join(class_name_parts) + 'Output'
    response_class_name = ''.join(class_name_parts) + 'Response'

    code_lines = [
        f"# ============================================================",
        f"# {api_name}() - {description}",
        f"# ============================================================",
        "",
        "",
        f"class {output_class_name}(TypedDict, total=False):",
        f'    """{description} output 필드"""',
        ""
    ]

    for field_name, field_desc in column_mapping.items():
        code_lines.append(f"    {field_name}: str  # {field_desc}")

    code_lines.extend([
        "",
        "",
        f"class {response_class_name}(BaseResponse):",
        f'    """{description} 응답"""',
        "",
        f"    output: {output_class_name}",
        "",
        ""
    ])

    return '\n'.join(code_lines)


def main():
    """메인 실행 함수"""
    # examples_llm 디렉토리 경로
    base_dir = Path('open-trading-api/examples_llm')

    if not base_dir.exists():
        print(f"Error: {base_dir} 디렉토리를 찾을 수 없습니다.")
        return

    print(f"Scanning {base_dir} for chk_*.py files...")
    chk_files = find_all_chk_files(base_dir)
    print(f"Found {len(chk_files)} chk_*.py files")

    # 모든 파일에서 정보 추출
    api_infos = []
    for chk_file in chk_files:
        info = extract_api_info(chk_file)
        if info and info['column_mapping']:
            api_infos.append(info)

    print(f"Extracted information from {len(api_infos)} files")

    # 카테고리별로 그룹화
    grouped = group_by_category(api_infos)

    # JSON 파일로 저장
    output_file = Path('response_mappings.json')
    with output_file.open('w', encoding='utf-8') as f:
        json.dump({
            'total_apis': len(api_infos),
            'categories': list(grouped.keys()),
            'apis': api_infos
        }, f, ensure_ascii=False, indent=2)

    print(f"\nSaved mapping data to {output_file}")

    # 카테고리별 통계 출력
    print("\n=== Category Statistics ===")
    for category, apis in sorted(grouped.items()):
        print(f"{category}: {len(apis)} APIs")

    # domestic_stock 카테고리의 TypedDict 샘플 생성
    print("\n=== Generating TypedDict samples for domestic_stock ===")
    domestic_stock_apis = grouped.get('inquire_price', [])
    if domestic_stock_apis:
        sample_api = domestic_stock_apis[0]
        sample_code = generate_typeddict_code(sample_api)
        print("\nSample TypedDict code:")
        print(sample_code)

    # 매핑 파일 생성 (카테고리별)
    for category, apis in grouped.items():
        category_file = Path(f'mappings_{category}.py')
        with category_file.open('w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write(f'Response TypedDict definitions for {category}\n')
            f.write(f'Auto-generated from examples_llm chk_*.py files\n')
            f.write('"""\n\n')
            f.write('from typing import TypedDict, List\n')
            f.write('from pykis.responses.common import BaseResponse\n\n')

            for api_info in apis:
                f.write(generate_typeddict_code(api_info))

        print(f"Generated {category_file}")


if __name__ == '__main__':
    main()
