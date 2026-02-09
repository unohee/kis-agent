"""
선물옵션 종목코드 자동 생성 유틸리티

한국투자증권 선물옵션 종목코드 형식:
- KOSPI200 선물: 101S12 (101=상품, S=시리즈, 12=만기월)
- KOSPI200 콜옵션: 201SC340 (201=상품, S=시리즈, C=콜, 340=행사가)
- KOSPI200 풋옵션: 301SP340 (301=상품, S=시리즈, P=풋, 340=행사가)

Created: 2026-01-20
Purpose: 선물옵션 종목코드 자동 생성 및 편의 기능
"""

from datetime import datetime
from typing import Literal, Optional


class FuturesCodeGenerator:
    """선물옵션 종목코드 자동 생성기"""

    # 상품 코드
    KOSPI200_FUTURES = "101"  # KOSPI200 선물
    KOSPI200_CALL = "201"  # KOSPI200 콜옵션
    KOSPI200_PUT = "301"  # KOSPI200 풋옵션

    # 시리즈 (계절별 만기)
    SERIES_MAP = {
        3: "S",  # 3월물 (Spring)
        6: "M",  # 6월물 (Summer)
        9: "U",  # 9월물 (Fall)
        12: "Z",  # 12월물 (Winter)
    }

    @staticmethod
    def get_current_series() -> str:
        """
        현재 날짜 기준 가장 가까운 선물 시리즈 코드 반환

        Returns:
            str: 시리즈 코드 (S, M, U, Z)

        Example:
            >>> FuturesCodeGenerator.get_current_series()
            'S'  # 2026년 1월 → 3월물
        """
        now = datetime.now()
        current_month = now.month

        # 현재 월 기준 다음 만기월 찾기
        for expiry_month in sorted(FuturesCodeGenerator.SERIES_MAP.keys()):
            if current_month <= expiry_month:
                return FuturesCodeGenerator.SERIES_MAP[expiry_month]

        # 12월 이후면 다음해 3월물
        return FuturesCodeGenerator.SERIES_MAP[3]

    @staticmethod
    def get_current_expiry_month() -> int:
        """
        현재 날짜 기준 가장 가까운 만기월 반환

        Returns:
            int: 만기월 (3, 6, 9, 12)

        Example:
            >>> FuturesCodeGenerator.get_current_expiry_month()
            3  # 2026년 1월 → 3월
        """
        now = datetime.now()
        current_month = now.month

        for expiry_month in sorted(FuturesCodeGenerator.SERIES_MAP.keys()):
            if current_month <= expiry_month:
                return expiry_month

        return 3  # 다음해 3월

    @staticmethod
    def generate_futures_code(
        product: Literal["KOSPI200"] = "KOSPI200",
        expiry_month: Optional[int] = None,
        series: Optional[str] = None,
    ) -> str:
        """
        선물 종목코드 생성

        Args:
            product: 상품 종류 (현재 KOSPI200만 지원)
            expiry_month: 만기월 (3, 6, 9, 12) - 없으면 가장 가까운 월물
            series: 시리즈 코드 (S, M, U, Z) - expiry_month와 함께 사용 불가

        Returns:
            str: 선물 종목코드 (예: "101S12")

        Example:
            >>> # 현재 월물 (자동 선택)
            >>> FuturesCodeGenerator.generate_futures_code()
            '101S03'
            >>>
            >>> # 특정 만기월 지정
            >>> FuturesCodeGenerator.generate_futures_code(expiry_month=6)
            '101M06'
            >>>
            >>> # 시리즈로 직접 지정
            >>> FuturesCodeGenerator.generate_futures_code(series="Z")
            '101Z12'
        """
        if product != "KOSPI200":
            raise ValueError("현재 KOSPI200 상품만 지원합니다")

        product_code = FuturesCodeGenerator.KOSPI200_FUTURES

        if series and expiry_month:
            raise ValueError("series와 expiry_month는 동시에 사용할 수 없습니다")

        if series:
            # 시리즈에서 만기월 역산
            series = series.upper()
            expiry_month = next(
                (m for m, s in FuturesCodeGenerator.SERIES_MAP.items() if s == series),
                None,
            )
            if not expiry_month:
                raise ValueError(f"잘못된 시리즈 코드: {series} (S, M, U, Z만 가능)")
        elif expiry_month:
            # 만기월에서 시리즈 조회
            if expiry_month not in FuturesCodeGenerator.SERIES_MAP:
                raise ValueError(f"잘못된 만기월: {expiry_month} (3, 6, 9, 12만 가능)")
            series = FuturesCodeGenerator.SERIES_MAP[expiry_month]
        else:
            # 자동 선택 (가장 가까운 월물)
            series = FuturesCodeGenerator.get_current_series()
            expiry_month = FuturesCodeGenerator.get_current_expiry_month()

        # 종목코드 생성: 상품코드(3) + 시리즈(1) + 만기월(2)
        return f"{product_code}{series}{expiry_month:02d}"

    @staticmethod
    def generate_option_code(
        option_type: Literal["CALL", "PUT"],
        strike_price: float,
        product: Literal["KOSPI200"] = "KOSPI200",
        expiry_month: Optional[int] = None,
        series: Optional[str] = None,
    ) -> str:
        """
        옵션 종목코드 생성

        Args:
            option_type: 옵션 타입 ("CALL" 또는 "PUT")
            strike_price: 행사가 (예: 340.0, 342.5)
            product: 상품 종류 (현재 KOSPI200만 지원)
            expiry_month: 만기월 (3, 6, 9, 12) - 없으면 가장 가까운 월물
            series: 시리즈 코드 (S, M, U, Z)

        Returns:
            str: 옵션 종목코드 (예: "201SC340")

        Example:
            >>> # 현재 월물 콜옵션 340.0
            >>> FuturesCodeGenerator.generate_option_code("CALL", 340.0)
            '201SC340'
            >>>
            >>> # 6월물 풋옵션 342.5
            >>> FuturesCodeGenerator.generate_option_code("PUT", 342.5, expiry_month=6)
            '301MP342'
            >>>
            >>> # 소수점 행사가 (2.5 단위)
            >>> FuturesCodeGenerator.generate_option_code("CALL", 337.5)
            '201SC337'  # 소수점 절사
        """
        if product != "KOSPI200":
            raise ValueError("현재 KOSPI200 상품만 지원합니다")

        option_type = option_type.upper()
        if option_type not in ("CALL", "PUT"):
            raise ValueError("option_type은 'CALL' 또는 'PUT'이어야 합니다")

        # 상품 코드
        product_code = (
            FuturesCodeGenerator.KOSPI200_CALL
            if option_type == "CALL"
            else FuturesCodeGenerator.KOSPI200_PUT
        )

        # 시리즈 결정
        if series and expiry_month:
            raise ValueError("series와 expiry_month는 동시에 사용할 수 없습니다")

        if series:
            series = series.upper()
            if series not in FuturesCodeGenerator.SERIES_MAP.values():
                raise ValueError(f"잘못된 시리즈 코드: {series} (S, M, U, Z만 가능)")
        elif expiry_month:
            if expiry_month not in FuturesCodeGenerator.SERIES_MAP:
                raise ValueError(f"잘못된 만기월: {expiry_month} (3, 6, 9, 12만 가능)")
            series = FuturesCodeGenerator.SERIES_MAP[expiry_month]
        else:
            series = FuturesCodeGenerator.get_current_series()

        # 옵션 타입 코드
        option_code = "C" if option_type == "CALL" else "P"

        # 행사가 (소수점 절사)
        strike = int(strike_price)

        # 종목코드 생성: 상품코드(3) + 시리즈(1) + 옵션타입(1) + 행사가(3)
        return f"{product_code}{series}{option_code}{strike:03d}"

    @staticmethod
    def generate_atm_option_codes(
        current_price: float,
        product: Literal["KOSPI200"] = "KOSPI200",
        expiry_month: Optional[int] = None,
        range_count: int = 3,
    ) -> dict:
        """
        ATM(At-The-Money) 기준 옵션 종목코드 생성

        Args:
            current_price: 현재 기초자산 가격 (예: 340.25)
            product: 상품 종류
            expiry_month: 만기월
            range_count: ATM 기준 위아래 몇 개 행사가 생성 (기본 3개)

        Returns:
            dict: {"call": [...], "put": [...], "atm_strike": float}

        Example:
            >>> # KOSPI200 현재가 340.25 기준
            >>> codes = FuturesCodeGenerator.generate_atm_option_codes(340.25)
            >>> codes
            {
                "atm_strike": 340.0,
                "call": ["201SC337", "201SC340", "201SC342"],
                "put": ["301SP337", "301SP340", "301SP342"]
            }
        """
        # ATM 행사가 (2.5 단위로 반올림)
        atm_strike = round(current_price / 2.5) * 2.5

        # 행사가 리스트 생성 (2.5 단위)
        strikes = [atm_strike + (i * 2.5) for i in range(-range_count, range_count + 1)]

        call_codes = [
            FuturesCodeGenerator.generate_option_code(
                "CALL", strike, product, expiry_month
            )
            for strike in strikes
        ]

        put_codes = [
            FuturesCodeGenerator.generate_option_code(
                "PUT", strike, product, expiry_month
            )
            for strike in strikes
        ]

        return {"atm_strike": atm_strike, "call": call_codes, "put": put_codes}

    @staticmethod
    def parse_futures_code(code: str) -> dict:
        """
        선물 종목코드 파싱

        Args:
            code: 선물 종목코드 (예: "101S12")

        Returns:
            dict: 파싱 결과
                - product: 상품명
                - series: 시리즈 코드
                - expiry_month: 만기월

        Example:
            >>> FuturesCodeGenerator.parse_futures_code("101S12")
            {'product': 'KOSPI200 선물', 'series': 'S', 'expiry_month': 12}
        """
        if len(code) < 6:
            raise ValueError(f"잘못된 종목코드 형식: {code}")

        product_code = code[:3]
        series = code[3]
        expiry_month = int(code[4:6])

        product_names = {
            "101": "KOSPI200 선물",
            "201": "KOSPI200 콜옵션",
            "301": "KOSPI200 풋옵션",
        }

        return {
            "product": product_names.get(product_code, "알 수 없음"),
            "series": series,
            "expiry_month": expiry_month,
        }

    @staticmethod
    def parse_option_code(code: str) -> dict:
        """
        옵션 종목코드 파싱

        Args:
            code: 옵션 종목코드 (예: "201SC340")

        Returns:
            dict: 파싱 결과
                - product: 상품명
                - option_type: 옵션 타입 (CALL/PUT)
                - series: 시리즈 코드
                - strike_price: 행사가

        Example:
            >>> FuturesCodeGenerator.parse_option_code("201SC340")
            {
                'product': 'KOSPI200 옵션',
                'option_type': 'CALL',
                'series': 'S',
                'strike_price': 340.0
            }
        """
        if len(code) < 8:
            raise ValueError(f"잘못된 옵션 종목코드 형식: {code}")

        series = code[3]
        option_code = code[4]
        strike = float(code[5:8])

        option_type = "CALL" if option_code == "C" else "PUT"

        return {
            "product": "KOSPI200 옵션",
            "option_type": option_type,
            "series": series,
            "strike_price": strike,
        }


# 편의 함수
def generate_current_futures() -> str:
    """현재 월물 선물 종목코드 생성"""
    return FuturesCodeGenerator.generate_futures_code()


def generate_next_futures() -> str:
    """차근월물 선물 종목코드 생성"""
    current_month = FuturesCodeGenerator.get_current_expiry_month()
    next_months = sorted(FuturesCodeGenerator.SERIES_MAP.keys())

    # 다음 만기월 찾기
    for i, month in enumerate(next_months):
        if month == current_month and i < len(next_months) - 1:
            return FuturesCodeGenerator.generate_futures_code(
                expiry_month=next_months[i + 1]
            )

    # 현재가 12월이면 다음해 3월
    return FuturesCodeGenerator.generate_futures_code(expiry_month=3)


def generate_call_option(
    strike_price: float, expiry_month: Optional[int] = None
) -> str:
    """콜옵션 종목코드 생성 (편의 함수)"""
    return FuturesCodeGenerator.generate_option_code(
        "CALL", strike_price, expiry_month=expiry_month
    )


def generate_put_option(strike_price: float, expiry_month: Optional[int] = None) -> str:
    """풋옵션 종목코드 생성 (편의 함수)"""
    return FuturesCodeGenerator.generate_option_code(
        "PUT", strike_price, expiry_month=expiry_month
    )
