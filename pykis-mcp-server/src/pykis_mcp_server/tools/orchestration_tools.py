"""Tool orchestration and planning for meta-queries"""
from typing import Any, Dict, List
from ..server import server


# Tool Registry - 도구 간 관계 정의
TOOL_REGISTRY = {
    # === 시장 스캔 도구 ===
    "get_top_gainers": {
        "category": "market_scan",
        "description": "상승률 상위 종목 조회",
        "outputs": ["stock_codes", "stock_names", "change_rates"],
        "inputs": [],
        "use_case": "어떤 종목이 오늘 많이 올랐는지"
    },
    "get_volume_rank": {
        "category": "market_scan",
        "description": "거래량 상위 종목 조회",
        "outputs": ["stock_codes", "stock_names", "volumes"],
        "inputs": [],
        "use_case": "거래량이 많은 종목이 뭔지"
    },
    "get_market_fluctuation": {
        "category": "market_scan",
        "description": "시장 등락 현황",
        "outputs": ["advancing_count", "declining_count", "market_status"],
        "inputs": [],
        "use_case": "오늘 시장 상황이 어떤지"
    },

    # === 개별 종목 분석 ===
    "get_stock_price": {
        "category": "stock_analysis",
        "description": "종목 현재가 조회",
        "outputs": ["price", "change_rate", "volume"],
        "inputs": ["stock_code"],
        "use_case": "특정 종목의 현재가"
    },
    "get_stock_investor": {
        "category": "investor_flow",
        "description": "종목별 투자자 매매동향",
        "outputs": ["foreign_net", "institution_net", "individual_net"],
        "inputs": ["stock_code"],
        "use_case": "특정 종목의 투자자별 매매현황"
    },
    "get_stock_member": {
        "category": "broker_analysis",
        "description": "종목별 증권사 매매동향",
        "outputs": ["broker_trades", "broker_names", "net_buy_amounts"],
        "inputs": ["stock_code"],
        "use_case": "특정 종목을 어떤 증권사가 매매했는지"
    },
    "get_member_transaction": {
        "category": "broker_analysis",
        "description": "증권사별 기간 거래 내역",
        "outputs": ["broker_period_trades"],
        "inputs": ["stock_code", "start_date", "end_date"],
        "use_case": "특정 기간 동안 증권사별 거래"
    },

    # === 투자자 흐름 분석 ===
    "get_investor_trade_by_stock_daily": {
        "category": "investor_flow",
        "description": "종목별 투자자 일별 매매동향",
        "outputs": ["daily_foreign_net", "daily_institution_net"],
        "inputs": ["stock_code", "start_date", "end_date"],
        "use_case": "특정 기간 외국인/기관 매매"
    },
    "get_frgnmem_pchs_trend": {
        "category": "investor_flow",
        "description": "외국인 매수 추세",
        "outputs": ["foreign_buy_trend"],
        "inputs": ["stock_code"],
        "use_case": "외국인이 매수하고 있는지"
    },

    # === 프로그램 매매 ===
    "get_program_trade_by_stock": {
        "category": "program_trading",
        "description": "종목별 프로그램 매매",
        "outputs": ["program_buy", "program_sell", "program_net"],
        "inputs": ["stock_code"],
        "use_case": "프로그램 매매 현황"
    },

    # === 가격 데이터 ===
    "inquire_daily_price": {
        "category": "price_data",
        "description": "일봉 데이터",
        "outputs": ["daily_prices", "daily_volumes"],
        "inputs": ["stock_code"],
        "use_case": "일별 가격 데이터"
    },
    "get_minute_price": {
        "category": "price_data",
        "description": "분봉 데이터",
        "outputs": ["minute_prices", "minute_volumes"],
        "inputs": ["stock_code"],
        "use_case": "분별 가격 데이터"
    },

    # === 복합 분석 도구 ===
    "analyze_broker_accumulation": {
        "category": "composite_analysis",
        "description": "증권사 매집 분석",
        "outputs": ["accumulated_stocks", "net_buy_amounts"],
        "inputs": ["broker_name", "days"],
        "use_case": "특정 증권사가 많이 매집한 종목"
    },
    "analyze_foreign_institutional_flow": {
        "category": "composite_analysis",
        "description": "외국인/기관 동시 순매수 분석",
        "outputs": ["consensus_stocks"],
        "inputs": ["days"],
        "use_case": "외국인과 기관이 동시에 사는 종목"
    },
    "detect_volume_spike": {
        "category": "composite_analysis",
        "description": "거래량 급등 탐지",
        "outputs": ["volume_spike_stocks"],
        "inputs": ["threshold"],
        "use_case": "거래량이 갑자기 늘어난 종목"
    },
    "find_price_momentum": {
        "category": "composite_analysis",
        "description": "가격 모멘텀 탐색",
        "outputs": ["momentum_stocks"],
        "inputs": ["period", "min_change"],
        "use_case": "지속적으로 상승하는 종목"
    },
    "analyze_market_breadth": {
        "category": "composite_analysis",
        "description": "시장 폭 분석",
        "outputs": ["market_sentiment", "advance_ratio"],
        "inputs": [],
        "use_case": "시장 전체 건강도"
    },
}

# 도구 간 연결 관계 정의
TOOL_CHAINS = {
    "broker_accumulation_analysis": {
        "description": "특정 증권사의 매집 종목 분석",
        "steps": [
            {"tool": "get_volume_rank", "purpose": "분석 대상 종목 선정"},
            {"tool": "get_member_transaction", "purpose": "각 종목의 증권사별 거래 조회", "loop": True},
        ],
        "keywords": ["증권사", "매집", "순매수"]
    },
    "foreign_institutional_consensus": {
        "description": "외국인/기관 동시 매수 종목",
        "steps": [
            {"tool": "get_volume_rank", "purpose": "분석 대상 종목 선정"},
            {"tool": "get_investor_trade_by_stock_daily", "purpose": "투자자별 매매 조회", "loop": True},
        ],
        "keywords": ["외국인", "기관", "동시", "순매수"]
    },
    "volume_breakout_detection": {
        "description": "거래량 돌파 종목 탐지",
        "steps": [
            {"tool": "get_volume_rank", "purpose": "거래량 상위 종목 조회"},
            {"tool": "inquire_daily_price", "purpose": "20일 평균 거래량 계산", "loop": True},
        ],
        "keywords": ["거래량", "급등", "돌파", "평균"]
    },
    "momentum_screening": {
        "description": "모멘텀 종목 스크리닝",
        "steps": [
            {"tool": "get_top_gainers", "purpose": "상승 종목 조회"},
            {"tool": "inquire_daily_price", "purpose": "기간 수익률 계산", "loop": True},
        ],
        "keywords": ["모멘텀", "상승", "추세", "수익률"]
    },
    "stock_comprehensive_analysis": {
        "description": "종목 종합 분석",
        "steps": [
            {"tool": "get_stock_price", "purpose": "현재가 조회"},
            {"tool": "get_stock_investor", "purpose": "투자자 동향 확인"},
            {"tool": "get_stock_member", "purpose": "증권사 동향 확인"},
            {"tool": "get_program_trade_by_stock", "purpose": "프로그램 매매 확인"},
        ],
        "keywords": ["종합", "분석", "전체", "상세"]
    },
}


@server.tool()
async def get_tool_registry() -> Dict[str, Any]:
    """사용 가능한 도구 목록과 관계 조회

    LLM이 도구 간 관계를 이해하고 적절한 도구 조합을 선택하도록
    도구 메타데이터를 제공합니다.

    Returns:
        Dict: 도구 레지스트리
            - tools: 개별 도구 정보
            - chains: 미리 정의된 도구 체인
            - categories: 카테고리별 도구 그룹
    """
    # 카테고리별 그룹핑
    categories = {}
    for tool_name, tool_info in TOOL_REGISTRY.items():
        category = tool_info["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(tool_name)

    return {
        "success": True,
        "tools": TOOL_REGISTRY,
        "chains": TOOL_CHAINS,
        "categories": categories,
        "usage_hint": "쿼리에 맞는 도구 체인을 선택하거나 개별 도구를 조합하세요"
    }


@server.tool()
async def plan_query_execution(query: str) -> Dict[str, Any]:
    """사용자 쿼리를 분석하여 실행 계획 생성

    자연어 쿼리를 분석하여 어떤 도구를 어떤 순서로
    호출해야 하는지 계획을 생성합니다.

    Args:
        query: 사용자 질문 (예: "JP모건이 최근 7일간 가장 많이 매집한 종목은?")

    Returns:
        Dict: 실행 계획
            - analysis: 쿼리 분석 결과
            - recommended_chain: 추천 도구 체인
            - execution_plan: 상세 실행 계획
            - direct_tool: 직접 사용 가능한 복합 도구 (있는 경우)
    """
    query_lower = query.lower()

    # 1. 직접 사용 가능한 복합 도구 확인
    direct_tools = []
    for tool_name, tool_info in TOOL_REGISTRY.items():
        if tool_info["category"] == "composite_analysis":
            use_case = tool_info.get("use_case", "").lower()
            if any(keyword in query_lower for keyword in use_case.split()):
                direct_tools.append({
                    "tool": tool_name,
                    "description": tool_info["description"],
                    "inputs": tool_info["inputs"]
                })

    # 2. 키워드 기반 체인 매칭
    matched_chains = []
    for chain_name, chain_info in TOOL_CHAINS.items():
        keywords = chain_info.get("keywords", [])
        match_count = sum(1 for kw in keywords if kw in query_lower)
        if match_count > 0:
            matched_chains.append({
                "chain": chain_name,
                "description": chain_info["description"],
                "match_score": match_count,
                "steps": chain_info["steps"]
            })

    # 매칭 점수로 정렬
    matched_chains.sort(key=lambda x: x["match_score"], reverse=True)

    # 3. 필요한 개별 도구 식별
    required_outputs = []
    if "증권사" in query_lower or "브로커" in query_lower:
        required_outputs.extend(["broker_trades", "broker_names"])
    if "외국인" in query_lower:
        required_outputs.extend(["foreign_net", "foreign_buy_trend"])
    if "기관" in query_lower:
        required_outputs.append("institution_net")
    if "거래량" in query_lower:
        required_outputs.extend(["volumes", "volume_spike_stocks"])
    if "상승" in query_lower or "수익률" in query_lower:
        required_outputs.extend(["change_rates", "momentum_stocks"])

    # 필요한 출력을 제공하는 도구 찾기
    suggested_tools = []
    for tool_name, tool_info in TOOL_REGISTRY.items():
        tool_outputs = tool_info.get("outputs", [])
        if any(output in tool_outputs for output in required_outputs):
            suggested_tools.append({
                "tool": tool_name,
                "category": tool_info["category"],
                "provides": [o for o in tool_outputs if o in required_outputs]
            })

    # 4. 실행 계획 생성
    execution_plan = {
        "query": query,
        "analysis": {
            "detected_entities": {
                "broker": "증권사" in query_lower or any(name in query_lower for name in ["모건", "골드만", "jp", "메릴린치"]),
                "foreign": "외국인" in query_lower,
                "institution": "기관" in query_lower,
                "period": any(term in query_lower for term in ["일", "주", "월", "기간"]),
                "volume": "거래량" in query_lower,
                "price": "가격" in query_lower or "수익률" in query_lower
            }
        },
        "direct_tools": direct_tools[:3] if direct_tools else None,
        "recommended_chain": matched_chains[0] if matched_chains else None,
        "alternative_chains": matched_chains[1:3] if len(matched_chains) > 1 else None,
        "individual_tools": suggested_tools[:5],
        "execution_hint": ""
    }

    # 실행 힌트 생성
    if direct_tools:
        execution_plan["execution_hint"] = f"'{direct_tools[0]['tool']}' 도구를 직접 호출하면 결과를 얻을 수 있습니다."
    elif matched_chains:
        chain = matched_chains[0]
        execution_plan["execution_hint"] = f"'{chain['chain']}' 체인을 따라 {len(chain['steps'])}단계로 실행하세요."
    else:
        execution_plan["execution_hint"] = "개별 도구를 조합하여 실행하세요."

    return {
        "success": True,
        "plan": execution_plan
    }


@server.tool()
async def suggest_tool_combination(
    goal: str,
    available_data: List[str] = None
) -> Dict[str, Any]:
    """목표 달성을 위한 도구 조합 제안

    분석 목표와 현재 가진 데이터를 기반으로
    다음에 사용할 도구를 제안합니다.

    Args:
        goal: 분석 목표 (예: "특정 증권사의 매집 패턴 분석")
        available_data: 이미 가진 데이터 (예: ["stock_codes", "volumes"])

    Returns:
        Dict: 도구 조합 제안
            - next_tools: 다음 실행할 도구
            - remaining_steps: 남은 단계
            - expected_outputs: 예상 결과
    """
    available_data = available_data or []
    available_set = set(available_data)

    # 각 도구의 실행 가능 여부 확인
    executable_tools = []
    pending_tools = []

    for tool_name, tool_info in TOOL_REGISTRY.items():
        required_inputs = set(tool_info.get("inputs", []))

        # 필요한 입력이 모두 있거나 입력이 필요 없는 경우
        if not required_inputs or required_inputs.issubset(available_set):
            tool_outputs = set(tool_info.get("outputs", []))
            new_outputs = tool_outputs - available_set

            if new_outputs:  # 새로운 출력을 제공하는 경우만
                executable_tools.append({
                    "tool": tool_name,
                    "category": tool_info["category"],
                    "description": tool_info["description"],
                    "new_outputs": list(new_outputs),
                    "priority": len(new_outputs)
                })
        else:
            missing_inputs = required_inputs - available_set
            pending_tools.append({
                "tool": tool_name,
                "missing_inputs": list(missing_inputs)
            })

    # 우선순위로 정렬
    executable_tools.sort(key=lambda x: x["priority"], reverse=True)

    return {
        "success": True,
        "goal": goal,
        "current_data": available_data,
        "next_tools": executable_tools[:5],
        "pending_tools": pending_tools[:5],
        "suggestion": executable_tools[0]["tool"] if executable_tools else "더 많은 기본 데이터가 필요합니다"
    }
