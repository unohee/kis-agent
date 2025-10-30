#!/usr/bin/env python3
"""
examples_llm의 COLUMN_MAPPING 정보를 사용하여
완전한 TypedDict 응답 모델 파일을 생성하는 스크립트
"""

import json
from pathlib import Path
from typing import Dict, List, Set


# pykis 메서드명과 examples_llm API 이름 매핑
PYKIS_TO_EXAMPLES_MAPPING = {
    # Stock Price APIs
    "get_stock_price": "inquire_price",
    "get_daily_price": "inquire_daily_price",
    "get_orderbook": "inquire_asking_price",
    "get_minute_price": "inquire_time_itemchartprice",
    "get_stock_investor": "inquire_investor",

    # Account APIs
    "get_account_balance": "inquire_balance",
    "get_account_balance_rlz_pl": "inquire_balance_rlz_pl",
    "get_daily_ccld": "inquire_daily_ccld",
    "get_period_trade_profit": "inquire_period_trade_profit",
    "get_psbl_order": "inquire_psbl_order",
    "get_psbl_sell": "inquire_psbl_sell",

    # Market Data APIs
    "get_index_price": "inquire_index_price",
    "get_index_daily_price": "inquire_index_daily_price",
    "inquire_ccnl": "inquire_ccnl",
    "inquire_time_itemconclusion": "inquire_time_itemconclusion",
    "search_stock_info": "search_stock_info",

    # Program Trade APIs
    "get_program_trade_by_stock": "program_trade_by_stock",
    "get_program_trade_by_stock_daily": "program_trade_by_stock_daily",
    "get_program_trade_total": "program_trade_total",
    "get_comp_program_trade_daily": "comp_program_trade_daily",
    "get_comp_program_trade_today": "comp_program_trade_today",

    # Investor APIs
    "get_investor_daily_by_market": "inquire_investor_daily_by_market",
    "get_investor_time_by_market": "inquire_investor_time_by_market",

    # Member APIs
    "get_member": "inquire_member",
    "get_member_daily": "inquire_member_daily",

    # Market Status APIs
    "get_market_status": "market_status_krx",
    "get_chk_holiday": "chk_holiday",

    # Credit & Short APIs
    "get_daily_credit_balance": "daily_credit_balance",
    "get_credit_balance": "credit_balance",
    "get_daily_short_sale": "daily_short_sale",

    # 기타 APIs
    "get_elw_price": "inquire_elw_price",
    "get_index_category_price": "inquire_index_category_price",
    "get_overtime_price": "inquire_overtime_price",
    "get_overtime_asking_price": "inquire_overtime_asking_price",
}


def load_mappings(json_file: Path) -> Dict:
    """response_mappings.json 파일 로드"""
    with json_file.open('r', encoding='utf-8') as f:
        return json.load(f)


def find_api_info(mappings_data: Dict, api_name: str) -> List[Dict]:
    """특정 API 이름에 해당하는 모든 정보 찾기 (중복 가능)"""
    results = []
    for api in mappings_data['apis']:
        if api['parent_dir'] == api_name or api['api_name'] == api_name:
            results.append(api)
    return results


def generate_output_class(
    class_name: str,
    column_mapping: Dict[str, str],
    description: str,
    output_number: int = None
) -> str:
    """TypedDict Output 클래스 코드 생성"""

    suffix = f"Output{output_number}" if output_number else "Output"
    full_class_name = f"{class_name}{suffix}"
    desc_suffix = f" (output{output_number})" if output_number else ""

    lines = [
        f"class {full_class_name}(TypedDict, total=False):",
        f'    """{description}{desc_suffix} 필드"""',
        ""
    ]

    # 필드를 알파벳 순서로 정렬하지 않고, 원본 순서 유지
    for field_name, field_desc in column_mapping.items():
        lines.append(f"    {field_name}: str  # {field_desc}")

    return '\n'.join(lines)


def generate_response_class(
    class_name: str,
    description: str,
    has_multiple_outputs: bool = False,
    output_count: int = 1
) -> str:
    """TypedDict Response 클래스 코드 생성"""

    lines = [
        "",
        "",
        f"class {class_name}Response(BaseResponse):",
        f'    """{description} 응답"""',
        ""
    ]

    if has_multiple_outputs:
        for i in range(1, output_count + 1):
            output_type = f"{class_name}Output{i}" if output_count > 1 else f"{class_name}Output"
            lines.append(f"    output{i}: {output_type}")
    else:
        lines.append(f"    output: {class_name}Output")

    return '\n'.join(lines)


def generate_complete_stock_responses(mappings_data: Dict) -> str:
    """완전한 stock.py 응답 파일 생성"""

    header = '''"""
Stock Response Types - 주식 관련 응답 타입 정의 (완전판)

주식 시세 조회, 호가, 분봉 등 Stock API 응답 구조
examples_llm의 COLUMN_MAPPING 정보를 기반으로 완전히 문서화됨
"""

from typing import List, TypedDict

from .common import BaseResponse


'''

    sections = []

    # pykis 메서드별로 처리
    for pykis_method, examples_api in sorted(PYKIS_TO_EXAMPLES_MAPPING.items()):
        # Stock 관련 메서드만 처리
        if pykis_method.startswith('get_') and any(x in pykis_method for x in [
            'stock', 'daily', 'minute', 'orderbook', 'investor', 'index', 'elw', 'overtime'
        ]):
            api_infos = find_api_info(mappings_data, examples_api)
            if not api_infos:
                continue

            api_info = api_infos[0]
            column_mapping = api_info.get('column_mapping', {})
            if not column_mapping:
                continue

            # 클래스명 생성 (camelCase)
            class_name_parts = [word.capitalize() for word in pykis_method.replace('get_', '').split('_')]
            class_name = ''.join(class_name_parts)

            description = api_info.get('description', pykis_method)
            has_multiple = api_info.get('has_multiple_outputs', False)

            section_lines = [
                "# " + "=" * 60,
                f"# {pykis_method}() - {description}",
                "# " + "=" * 60,
                "",
                ""
            ]

            # Output 클래스 생성
            output_class_code = generate_output_class(
                class_name,
                column_mapping,
                description
            )
            section_lines.append(output_class_code)

            # Response 클래스 생성
            response_class_code = generate_response_class(
                class_name,
                description,
                has_multiple
            )
            section_lines.append(response_class_code)
            section_lines.append("")
            section_lines.append("")

            sections.append('\n'.join(section_lines))

    return header + '\n\n'.join(sections)


def generate_complete_account_responses(mappings_data: Dict) -> str:
    """완전한 account.py 응답 파일 생성"""

    header = '''"""
Account Response Types - 계좌 관련 응답 타입 정의 (완전판)

계좌 잔고, 주문 가능 수량, 체결 내역 등 Account API 응답 구조
examples_llm의 COLUMN_MAPPING 정보를 기반으로 완전히 문서화됨
"""

from typing import List, TypedDict

from .common import BaseResponse


'''

    sections = []

    # Account 관련 메서드만 처리
    account_methods = {k: v for k, v in PYKIS_TO_EXAMPLES_MAPPING.items()
                       if 'account' in k or 'balance' in k or 'ccld' in k or 'psbl' in k or 'profit' in k}

    for pykis_method, examples_api in sorted(account_methods.items()):
        api_infos = find_api_info(mappings_data, examples_api)
        if not api_infos:
            continue

        api_info = api_infos[0]
        column_mapping = api_info.get('column_mapping', {})
        if not column_mapping:
            continue

        # 클래스명 생성
        class_name_parts = [word.capitalize() for word in pykis_method.replace('get_', '').split('_')]
        class_name = ''.join(class_name_parts)

        description = api_info.get('description', pykis_method)
        has_multiple = api_info.get('has_multiple_outputs', False)

        section_lines = [
            "# " + "=" * 60,
            f"# {pykis_method}() - {description}",
            "# " + "=" * 60,
            "",
            ""
        ]

        output_class_code = generate_output_class(
            class_name,
            column_mapping,
            description
        )
        section_lines.append(output_class_code)

        response_class_code = generate_response_class(
            class_name,
            description,
            has_multiple
        )
        section_lines.append(response_class_code)
        section_lines.append("")
        section_lines.append("")

        sections.append('\n'.join(section_lines))

    return header + '\n\n'.join(sections)


def main():
    """메인 실행 함수"""
    mappings_file = Path('response_mappings.json')

    if not mappings_file.exists():
        print(f"Error: {mappings_file} 파일을 찾을 수 없습니다.")
        print("먼저 extract_response_mappings.py를 실행하세요.")
        return

    print("Loading mappings data...")
    mappings_data = load_mappings(mappings_file)
    print(f"Loaded {mappings_data['total_apis']} APIs from {len(mappings_data['categories'])} categories")

    # Stock 응답 파일 생성
    print("\nGenerating complete stock responses...")
    stock_responses = generate_complete_stock_responses(mappings_data)
    stock_output = Path('pykis/responses/stock_complete.py')
    stock_output.write_text(stock_responses, encoding='utf-8')
    print(f"✓ Generated {stock_output}")

    # Account 응답 파일 생성
    print("\nGenerating complete account responses...")
    account_responses = generate_complete_account_responses(mappings_data)
    account_output = Path('pykis/responses/account_complete.py')
    account_output.write_text(account_responses, encoding='utf-8')
    print(f"✓ Generated {account_output}")

    # 통계 출력
    print("\n=== Generation Summary ===")
    print(f"Stock responses file: {stock_output} ({stock_output.stat().st_size} bytes)")
    print(f"Account responses file: {account_output} ({account_output.stat().st_size} bytes)")

    print("\nNext steps:")
    print("1. Review generated files: stock_complete.py, account_complete.py")
    print("2. Compare with current pykis/responses/stock.py and account.py")
    print("3. Merge the improvements into existing files")
    print("4. Update method docstrings to reference the new TypedDict fields")


if __name__ == '__main__':
    main()
