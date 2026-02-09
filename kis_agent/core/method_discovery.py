"""
메서드 탐색 모듈

Agent에서 사용 가능한 메서드를 카테고리별로 정리하고
검색 기능을 제공합니다.

Created: 2026-01-03
Purpose: agent.py에서 추출한 메서드 탐색 로직
"""

from __future__ import annotations

from typing import Any


class MethodDiscoveryMixin:
    """
    메서드 탐색 기능을 제공하는 Mixin 클래스.

    Agent 클래스에서 상속받아 사용합니다.
    - 사용 가능한 메서드 카테고리별 조회
    - 키워드 기반 메서드 검색
    - 메서드 사용법 안내
    """

    def get_all_methods(
        self, show_details: bool = False, category: str = None
    ) -> dict[str, Any]:
        """
        Agent에서 사용 가능한 모든 메서드를 카테고리별로 정리하여 반환합니다.

        Args:
            show_details (bool): 각 메서드의 상세 설명 포함 여부 (기본값: False)
            category (str): 특정 카테고리만 보기 (기본값: None - 전체)
                가능한 값: 'stock', 'account', 'program', 'market', 'utility',
                'websocket'

        Returns:
            dict: 메서드 정보가 담긴 딕셔너리

        Example:
            >>> agent = Agent()
            >>> methods = agent.get_all_methods()
            >>> print(f"총 {len(sum(methods.values(), []))}개 메서드 사용 가능")
            >>>
            >>> # 주식 관련 메서드만 보기
            >>> stock_methods = agent.get_all_methods(category='stock')
            >>>
            >>> # 상세 설명 포함
            >>> detailed = agent.get_all_methods(show_details=True)
        """

        # 메서드 카테고리별 분류
        methods_info = {
            "stock": {
                "title": " 주식 시세 관련",
                "methods": [
                    ("get_stock_price", "현재가 조회", 'get_stock_price("005930")'),
                    (
                        "get_daily_price",
                        "일별/주별/월별 시세 조회",
                        'get_daily_price("005930", period="D")',
                    ),
                    (
                        "get_minute_price",
                        "분봉 시세 조회",
                        'get_minute_price("005930", hour="153000")',
                    ),
                    (
                        "get_daily_minute_price",
                        "일별분봉시세조회",
                        'get_daily_minute_price("005930", "20250715", "153000")',
                    ),
                    ("get_orderbook", "호가 정보 조회", 'get_orderbook("005930")'),
                    (
                        "get_stock_investor",
                        "투자자별 매매 동향",
                        'get_stock_investor("005930")',
                    ),
                    ("get_stock_info", "종목 기본 정보", 'get_stock_info("005930")'),
                    (
                        "get_stock_financial",
                        "종목 재무 정보",
                        'get_stock_financial("005930")',
                    ),
                    ("get_stock_basic", "종목 기초 정보", 'get_stock_basic("005930")'),
                    (
                        "get_foreign_broker_net_buy",
                        "외국계 브로커 순매수",
                        'get_foreign_broker_net_buy("005930")',
                    ),
                    ("get_member", "거래원 정보 조회", 'get_member("005930")'),
                    (
                        "get_member_transaction",
                        "회원사 매매 정보",
                        'get_member_transaction("005930")',
                    ),
                ],
            },
            "market": {
                "title": " 시장 정보 관련",
                "methods": [
                    ("get_volume_power", "체결강도 순위", "get_volume_power(0)"),
                    ("get_top_gainers", "상위 상승주", "get_top_gainers()"),
                    (
                        "get_market_fluctuation",
                        "시장 등락 현황",
                        "get_market_fluctuation()",
                    ),
                    (
                        "get_market_rankings",
                        "시장 순위 정보",
                        "get_market_rankings(volume=5000000)",
                    ),
                    ("get_kospi200_index", "KOSPI200 지수", "get_kospi200_index()"),
                    ("get_futures_price", "선물 시세", 'get_futures_price("101S12")'),
                    (
                        "get_future_option_price",
                        "선물옵션 시세",
                        "get_future_option_price()",
                    ),
                    (
                        "get_daily_index_chart_price",
                        "지수 차트",
                        'get_daily_index_chart_price("0001", "D")',
                    ),
                ],
            },
            "account": {
                "title": " 계좌 관련",
                "methods": [
                    ("get_account_balance", "계좌 잔고 조회", "get_account_balance()"),
                    (
                        "get_cash_available",
                        "매수 가능 금액",
                        'get_cash_available("005930")',
                    ),
                    ("get_total_asset", "계좌 총 자산", "get_total_asset()"),
                    (
                        "get_possible_order_amount",
                        "주문 가능 금액",
                        'get_possible_order_amount("005930", "60000")',
                    ),
                    (
                        "get_account_order_quantity",
                        "계좌별 주문 수량",
                        'get_account_order_quantity("005930")',
                    ),
                ],
            },
            "program": {
                "title": "프로그램 매매 관련",
                "methods": [
                    (
                        "get_program_trade_by_stock",
                        "종목별 프로그램매매 추이",
                        'get_program_trade_by_stock("005930")',
                    ),
                    (
                        "get_program_trade_hourly_trend",
                        "시간별 프로그램매매 추이",
                        'get_program_trade_hourly_trend("005930")',
                    ),
                    (
                        "get_program_trade_daily_summary",
                        "일별 프로그램매매 집계",
                        'get_program_trade_daily_summary("005930", "20250107")',
                    ),
                    (
                        "get_program_trade_period_detail",
                        "기간별 프로그램매매 상세",
                        'get_program_trade_period_detail("20250101", "20250107")',
                    ),
                    (
                        "get_program_trade_market_daily",
                        "시장 전체 프로그램매매",
                        'get_program_trade_market_daily("20250101", "20250107")',
                    ),
                ],
            },
            "utility": {
                "title": " 유틸리티",
                "methods": [
                    ("get_holiday_info", "휴장일 정보", "get_holiday_info()"),
                    ("is_holiday", "휴장일 여부 확인", 'is_holiday("20250107")'),
                    (
                        "fetch_minute_data",
                        "분봉 데이터 수집",
                        'fetch_minute_data("005930", "20250107")',
                    ),
                    (
                        "calculate_support_resistance",
                        "매물대 분석",
                        'calculate_support_resistance("005930")',
                    ),
                    ("get_condition_stocks", "조건검색 종목", "get_condition_stocks()"),
                    (
                        "init_minute_db",
                        "SQLite DB 초기화",
                        'init_minute_db("my_data.db")',
                    ),
                    (
                        "migrate_minute_csv_to_db",
                        "CSV→DB 마이그레이션",
                        'migrate_minute_csv_to_db("005930")',
                    ),
                    (
                        "classify_broker",
                        "거래원 성격 분류",
                        'classify_broker("모간스탠리")',
                    ),
                ],
            },
            "websocket": {
                "title": " 실시간 웹소켓",
                "methods": [
                    (
                        "websocket",
                        "실시간 웹소켓 클라이언트",
                        'websocket(["005930"], enable_index=True)',
                    ),
                ],
            },
        }

        # 특정 카테고리만 요청된 경우
        if category:
            if category not in methods_info:
                available_categories = list(methods_info.keys())
                return {
                    "error": f"유효하지 않은 카테고리: {category}",
                    "available_categories": available_categories,
                }
            methods_info = {category: methods_info[category]}

        # 결과 정리
        result = {}
        total_methods = 0

        for cat_key, cat_info in methods_info.items():
            if show_details:
                # 상세 정보 포함
                result[cat_key] = {
                    "title": cat_info["title"],
                    "count": len(cat_info["methods"]),
                    "methods": [
                        {
                            "name": method[0],
                            "description": method[1],
                            "example": method[2],
                        }
                        for method in cat_info["methods"]
                    ],
                }
            else:
                # 간단한 정보만
                result[cat_key] = {
                    "title": cat_info["title"],
                    "count": len(cat_info["methods"]),
                    "methods": [method[0] for method in cat_info["methods"]],
                }

            total_methods += len(cat_info["methods"])

        # 요약 정보 추가
        result["_summary"] = {
            "total_methods": total_methods,
            "total_categories": len(result) - 1,  # _summary 제외
            "usage_tip": (
                'agent.get_all_methods(show_details=True, category="stock") '
                "형태로 상세 정보를 확인할 수 있습니다."
            ),
        }

        return result

    def search_methods(self, keyword: str) -> list[dict[str, Any]]:
        """
        키워드로 메서드를 검색합니다.

        Args:
            keyword (str): 검색할 키워드 (메서드명이나 설명에서 검색)

        Returns:
            list: 매칭되는 메서드 정보 리스트

        Example:
            >>> agent = Agent()
            >>> # "price"라는 키워드로 검색
            >>> results = agent.search_methods("price")
            >>> for method in results:
            ...     print(f"{method['name']}: {method['description']}")
        """
        all_methods = self.get_all_methods(show_details=True)
        results = []
        keyword_lower = keyword.lower()

        for category_key, category_info in all_methods.items():
            if category_key == "_summary":
                continue

            for method in category_info["methods"]:
                # 메서드명이나 설명에서 키워드 검색
                if (
                    keyword_lower in method["name"].lower()
                    or keyword_lower in method["description"].lower()
                ):
                    results.append(
                        {
                            "name": method["name"],
                            "description": method["description"],
                            "example": method["example"],
                            "category": category_info["title"],
                        }
                    )

        return results

    def show_method_usage(self, method_name: str) -> None:
        """
        특정 메서드의 사용법을 출력합니다.

        Args:
            method_name (str): 확인할 메서드명

        Example:
            >>> agent = Agent()
            >>> agent.show_method_usage("get_stock_price")
        """
        all_methods = self.get_all_methods(show_details=True)

        for category_key, category_info in all_methods.items():
            if category_key == "_summary":
                continue

            for method in category_info["methods"]:
                if method["name"] == method_name:
                    print(f" 메서드: {method['name']}")
                    print(f" 설명: {method['description']}")
                    print(f" 카테고리: {category_info['title']}")
                    print(f" 사용 예시: agent.{method['example']}")

                    # 실제 메서드가 있는지 확인하고 docstring 출력
                    if hasattr(self, method_name):
                        actual_method = getattr(self, method_name)
                        if hasattr(actual_method, "__doc__") and actual_method.__doc__:
                            print(" 상세 문서:")
                            print(f"    {actual_method.__doc__.strip()}")
                    return

        print(f" '{method_name}' 메서드를 찾을 수 없습니다.")
        print(" 사용 가능한 메서드 확인: agent.get_all_methods()")

    @staticmethod
    def classify_broker(name: str) -> str:
        """간단한 거래원 성격 분류기: 외국계 / 리테일 / 기관"""
        # Guard clause: if name is not a string, return "N/A"
        if not isinstance(name, str):
            return "N/A"
        foreign_brokers = [
            "모간",
            "CS",
            "맥쿼리",
            "골드만",
            "바클레이",
            "노무라",
            "UBS",
            "BOA",
            "BNP",
        ]
        retail_brokers = ["키움", "NH투자", "미래에셋", "삼성증권", "신한증권"]
        name_upper = name.upper()

        if any(fb.upper() in name_upper for fb in foreign_brokers):
            return "외국계"
        elif any(rb.upper() in name_upper for rb in retail_brokers):
            return "리테일/국내기관"
        else:
            return "기타"
