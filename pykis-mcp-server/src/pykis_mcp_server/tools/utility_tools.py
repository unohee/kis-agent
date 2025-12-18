"""Utility and helper MCP tools"""

import inspect
from typing import Any, Dict

from ..errors import InvalidParameterError, validate_api_response
from ..server import get_agent, server


@server.tool()
async def get_holiday_info(date: str = "") -> Dict[str, Any]:
    """휴장일 정보 조회

    Args:
        date: 기준 날짜 (YYYYMMDD, 선택)

    Returns:
        Dict: 휴장일 정보
    """
    agent = get_agent()
    result = agent.get_holiday_info(date if date else None)
    return validate_api_response(result, "휴장일 정보 조회")


@server.tool()
async def is_holiday(date: str) -> Dict[str, Any]:
    """특정일 휴장일 여부 확인

    Args:
        date: 확인할 날짜 (YYYYMMDD)

    Returns:
        Dict: 휴장일 여부 (is_holiday: True/False)
    """
    if not date or len(date) != 8:
        raise InvalidParameterError("date", "날짜는 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.is_holiday(date)

    if result is None:
        return {"success": False, "message": "휴장일 확인 실패"}

    return {"success": True, "is_holiday": result, "date": date}


@server.tool()
async def get_daily_credit_balance(code: str, date: str) -> Dict[str, Any]:
    """신용잔고 일별추이 조회

    Args:
        code: 종목코드 6자리
        date: 결제일자 (YYYYMMDD)

    Returns:
        Dict: 신용잔고 일별추이 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    if not date or len(date) != 8:
        raise InvalidParameterError("date", "날짜는 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.get_daily_credit_balance(code, date)
    return validate_api_response(result, "신용잔고 일별추이 조회")


@server.tool()
async def get_stock_info(stock_code: str) -> Dict[str, Any]:
    """종목 기본정보 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 종목 기본 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_stock_info(stock_code)
    return validate_api_response(result, "종목 기본정보 조회")


@server.tool()
async def get_stock_basic(stock_code: str) -> Dict[str, Any]:
    """종목 기본 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 종목 기본 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_stock_basic(stock_code)
    return validate_api_response(result, "종목 기본 조회")


@server.tool()
async def get_stock_financial(stock_code: str) -> Dict[str, Any]:
    """종목 재무정보 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 종목 재무 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_stock_financial(stock_code)
    return validate_api_response(result, "종목 재무정보 조회")


@server.tool()
async def get_pbar_tratio(stock_code: str) -> Dict[str, Any]:
    """매수매도비율 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 매수/매도 비율 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_pbar_tratio(stock_code)
    return validate_api_response(result, "매수매도비율 조회")


@server.tool()
async def get_asking_price_exp_ccn(stock_code: str) -> Dict[str, Any]:
    """호가예상체결 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 호가 예상 체결 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_asking_price_exp_ccn(stock_code)
    return validate_api_response(result, "호가예상체결 조회")


@server.tool()
async def inquire_vi_status(stock_code: str = "") -> Dict[str, Any]:
    """VI 발동 상태 조회

    Args:
        stock_code: 종목코드 6자리 (선택, 공백시 전체)

    Returns:
        Dict: VI 발동 상태 정보
    """
    agent = get_agent()
    result = agent.inquire_vi_status(stock_code)
    return validate_api_response(result, "VI 발동 상태 조회")


@server.tool()
async def get_condition_stocks(
    user_id: str, seq: int, div_code: str = "N"
) -> Dict[str, Any]:
    """조건검색식 종목 조회

    Args:
        user_id: 사용자 ID
        seq: 조건식 순번
        div_code: 구분 코드 (N/Y)

    Returns:
        Dict: 조건검색식 종목 리스트

    Note:
        이 기능은 PyKIS에서 아직 구현되지 않았을 수 있습니다.
    """
    agent = get_agent()

    # Check if method exists
    if not hasattr(agent, "get_condition_stocks"):
        return {
            "success": False,
            "message": "조건검색식 기능은 아직 구현되지 않았습니다",
            "error_code": "NOT_IMPLEMENTED",
        }

    result = agent.get_condition_stocks(user_id, seq, div_code)
    return validate_api_response(result, "조건검색식 종목 조회")


@server.tool()
async def get_interest_group_list(
    user_id: str, type_code: str = "1", fid_etc_cls_code: str = "00"
) -> Dict[str, Any]:
    """관심종목 그룹 목록 조회

    Args:
        user_id: 사용자 ID
        type_code: 타입 코드 (기본값: "1")
        fid_etc_cls_code: 기타 구분 코드 (기본값: "00")

    Returns:
        Dict: 관심종목 그룹 목록
            - output: 그룹 정보 리스트
    """
    agent = get_agent()
    result = agent.get_interest_group_list(user_id, type_code, fid_etc_cls_code)
    return validate_api_response(result, "관심종목 그룹 목록 조회")


@server.tool()
async def get_interest_stock_list(
    user_id: str,
    inter_grp_code: str,
    type_code: str = "1",
    data_rank: str = "",
    inter_grp_name: str = "",
    hts_kor_isnm: str = "",
    cntg_cls_code: str = "",
    fid_etc_cls_code: str = "4",
) -> Dict[str, Any]:
    """관심종목 그룹별 종목 조회

    Args:
        user_id: 사용자 ID
        inter_grp_code: 관심종목 그룹 코드 (예: "001")
        type_code: 타입 코드 (기본값: "1")
        data_rank: 데이터 순위 (기본값: "")
        inter_grp_name: 관심종목 그룹명 (기본값: "")
        hts_kor_isnm: HTS 한글 종목명 (기본값: "")
        cntg_cls_code: 체결 구분 코드 (기본값: "")
        fid_etc_cls_code: 기타 구분 코드 (기본값: "4")

    Returns:
        Dict: 관심종목 그룹별 종목 목록
            - output1: 그룹 정보
            - output2: 종목 목록 리스트
                - fid_mrkt_cls_code: 시장 구분 코드
                - jong_code: 종목 코드
                - hts_kor_isnm: 종목명
                - exch_code: 거래소 코드
                등
    """
    agent = get_agent()
    result = agent.get_interest_stock_list(
        user_id=user_id,
        inter_grp_code=inter_grp_code,
        type_code=type_code,
        data_rank=data_rank,
        inter_grp_name=inter_grp_name,
        hts_kor_isnm=hts_kor_isnm,
        cntg_cls_code=cntg_cls_code,
        fid_etc_cls_code=fid_etc_cls_code,
    )
    return validate_api_response(result, "관심종목 그룹별 종목 조회")


@server.tool()
async def search_methods(query: str) -> Dict[str, Any]:
    """Agent 메서드 검색

    Args:
        query: 검색할 키워드 (메서드 이름 또는 설명)

    Returns:
        Dict: 검색된 메서드 리스트
    """
    agent = get_agent()
    methods = []

    # Get all public methods
    for name in dir(agent):
        if name.startswith("_"):
            continue

        attr = getattr(agent, name)
        if not callable(attr):
            continue

        # Check if method name or docstring contains query
        if query.lower() in name.lower():
            doc = inspect.getdoc(attr) or "설명 없음"
            sig = str(inspect.signature(attr))

            methods.append(
                {
                    "name": name,
                    "signature": f"{name}{sig}",
                    "description": doc.split("\n")[0],  # First line only
                }
            )

    return {"success": True, "query": query, "count": len(methods), "methods": methods}


@server.tool()
async def get_all_methods() -> Dict[str, Any]:
    """Agent의 모든 공개 메서드 조회

    Returns:
        Dict: 전체 메서드 리스트와 카테고리별 분류
    """
    agent = get_agent()
    methods = []
    categories = {
        "stock": [],
        "order": [],
        "account": [],
        "investor": [],
        "utility": [],
        "other": [],
    }

    # Get all public methods
    for name in dir(agent):
        if name.startswith("_"):
            continue

        attr = getattr(agent, name)
        if not callable(attr):
            continue

        doc = inspect.getdoc(attr) or "설명 없음"
        sig = str(inspect.signature(attr))

        method_info = {
            "name": name,
            "signature": f"{name}{sig}",
            "description": doc.split("\n")[0],
        }

        methods.append(method_info)

        # Categorize
        if any(
            k in name.lower()
            for k in ["stock", "price", "orderbook", "daily", "minute"]
        ):
            categories["stock"].append(name)
        elif any(k in name.lower() for k in ["order", "buy", "sell"]):
            categories["order"].append(name)
        elif any(k in name.lower() for k in ["balance", "account", "psbl"]):
            categories["account"].append(name)
        elif any(k in name.lower() for k in ["investor", "member", "program"]):
            categories["investor"].append(name)
        elif any(k in name.lower() for k in ["holiday", "credit", "condition"]):
            categories["utility"].append(name)
        else:
            categories["other"].append(name)

    return {
        "success": True,
        "total_count": len(methods),
        "methods": methods,
        "categories": categories,
    }


@server.tool()
async def show_method_usage(method_name: str) -> Dict[str, Any]:
    """특정 메서드의 상세 사용법 조회

    Args:
        method_name: 조회할 메서드 이름

    Returns:
        Dict: 메서드 시그니처, 파라미터, 독스트링 등 상세 정보
    """
    agent = get_agent()

    if not hasattr(agent, method_name):
        return {
            "success": False,
            "message": f"메서드 '{method_name}'을 찾을 수 없습니다",
            "error_code": "METHOD_NOT_FOUND",
        }

    method = getattr(agent, method_name)

    if not callable(method):
        return {
            "success": False,
            "message": f"'{method_name}'은 메서드가 아닙니다",
            "error_code": "NOT_CALLABLE",
        }

    # Get method details
    sig = inspect.signature(method)
    doc = inspect.getdoc(method) or "설명 없음"

    # Parse parameters
    params = []
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        param_info = {
            "name": param_name,
            "type": str(param.annotation)
            if param.annotation != inspect.Parameter.empty
            else "Any",
            "default": str(param.default)
            if param.default != inspect.Parameter.empty
            else None,
            "required": param.default == inspect.Parameter.empty,
        }
        params.append(param_info)

    return {
        "success": True,
        "method": method_name,
        "signature": f"{method_name}{sig}",
        "parameters": params,
        "documentation": doc,
        "return_type": str(sig.return_annotation)
        if sig.return_annotation != inspect.Signature.empty
        else "Any",
    }
