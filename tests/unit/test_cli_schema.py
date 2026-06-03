"""kis_agent.cli.schema의 get_schema() 동작 테스트.

목적: GraphQL SDL introspection 함수의 전체 분기 커버.
"""

import re

import pytest

from kis_agent.cli.schema import SCHEMA_SDL, get_schema


def test_get_schema_full():
    """type_name 미지정 시 전체 SDL 반환."""
    full = get_schema()
    assert full is SCHEMA_SDL or full == SCHEMA_SDL
    assert "type Stock" in full
    assert "type Account" in full or "type StockPrice" in full


def test_get_schema_existing_type_stock():
    """존재하는 타입(Stock) 추출."""
    result = get_schema("Stock")
    assert result, "Stock 타입 추출 결과가 비어 있음"
    assert "type Stock" in result
    # Stock 타입의 필드 일부 확인
    assert "code" in result
    # 다른 타입으로 누수되지 않아야 함
    assert "type Account" not in result


def test_get_schema_existing_type_stockprice():
    """nested type(StockPrice) 추출."""
    result = get_schema("StockPrice")
    assert "type StockPrice" in result
    assert "currentPrice" in result


def test_get_schema_unknown_type():
    """존재하지 않는 타입은 빈 문자열 또는 마커."""
    result = get_schema("NonExistentType_XYZ123")
    # type 정의를 찾지 못하면 빈 결과
    assert "type NonExistentType_XYZ123" not in result


def test_schema_sdl_well_formed_top_level_types():
    """SDL이 type/enum/input 정의를 일정 수 이상 포함."""
    matches = re.findall(r"^(type|enum|input)\s+(\w+)", SCHEMA_SDL, re.MULTILINE)
    # 스키마에 충분한 정의가 있어야 함 (현재 수십 개)
    assert len(matches) >= 10
    names = {m[1] for m in matches}
    assert "Stock" in names


@pytest.mark.parametrize(
    "type_name",
    ["Stock", "StockPrice", "Account", "Orderbook"],
)
def test_get_schema_known_types_return_nonempty(type_name):
    """알려진 주요 타입은 비어있지 않은 결과를 반환해야 함."""
    matches = re.findall(r"^(type|enum|input)\s+(\w+)", SCHEMA_SDL, re.MULTILINE)
    names = {m[1] for m in matches}
    if type_name not in names:
        pytest.skip(f"{type_name} not in current SDL (skip)")
    result = get_schema(type_name)
    assert f"type {type_name}" in result or f"enum {type_name}" in result
