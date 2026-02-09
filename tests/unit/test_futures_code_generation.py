"""
get_kospi200_futures_code() 함수 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-12
목적: pykis/stock/api.py의 커버리지 향상 (38.2% → 70%+)
대상 함수: get_kospi200_futures_code()
"""

from datetime import datetime

import pytest

from pykis.stock.api import get_kospi200_futures_code


class TestGetKospi200FuturesCode:
    """
    KOSPI200 선물 종목코드 생성 함수 테스트

    테스트 시나리오:
    1. 만기월 (3, 6, 9, 12월)에 만기일 전후로 코드 변경 확인
    2. 비만기월 (1, 2, 4, 5, 7, 8, 10, 11월)에 다음 만기월 코드 반환
    3. 12월 만기 후 다음해 3월물로 전환 확인
    4. today=None 시 현재 날짜 기준 동작 확인
    """

    def test_current_date_execution(self):
        """today=None 시 현재 날짜 기준으로 실행"""
        # Act
        code = get_kospi200_futures_code()

        # Assert
        assert code.startswith("101W"), "코드는 101W로 시작해야 함"
        assert len(code) == 6, "코드는 6자리여야 함"
        assert code[4:] in ["03", "06", "09", "12"], "만기월은 03, 06, 09, 12 중 하나"

    def test_march_expiry_before_expiry_date(self):
        """3월 만기일 전 - 3월물 반환"""
        # Arrange: 2025년 3월 1일 (두 번째 목요일 전)
        test_date = datetime(2025, 3, 1)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W03", "3월 만기일 전에는 101W03 반환"

    def test_march_expiry_after_expiry_date(self):
        """3월 만기일 후 - 6월물로 전환"""
        # Arrange: 2025년 3월 20일 (두 번째 목요일 후)
        test_date = datetime(2025, 3, 20)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W06", "3월 만기일 후에는 101W06 반환"

    def test_june_expiry_before_expiry_date(self):
        """6월 만기일 전 - 6월물 반환"""
        # Arrange: 2025년 6월 5일
        test_date = datetime(2025, 6, 5)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W06", "6월 만기일 전에는 101W06 반환"

    def test_june_expiry_after_expiry_date(self):
        """6월 만기일 후 - 9월물로 전환"""
        # Arrange: 2025년 6월 20일
        test_date = datetime(2025, 6, 20)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W09", "6월 만기일 후에는 101W09 반환"

    def test_september_expiry_before_expiry_date(self):
        """9월 만기일 전 - 9월물 반환"""
        # Arrange: 2025년 9월 1일
        test_date = datetime(2025, 9, 1)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W09", "9월 만기일 전에는 101W09 반환"

    def test_september_expiry_after_expiry_date(self):
        """9월 만기일 후 - 12월물로 전환"""
        # Arrange: 2025년 9월 20일
        test_date = datetime(2025, 9, 20)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W12", "9월 만기일 후에는 101W12 반환"

    def test_december_expiry_before_expiry_date(self):
        """12월 만기일 전 - 12월물 반환"""
        # Arrange: 2025년 12월 1일
        test_date = datetime(2025, 12, 1)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W12", "12월 만기일 전에는 101W12 반환"

    def test_december_expiry_after_expiry_date_rollover_to_march(self):
        """12월 만기일 후 - 다음해 3월물로 전환"""
        # Arrange: 2025년 12월 20일 (만기일 후)
        test_date = datetime(2025, 12, 20)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W03", "12월 만기일 후에는 다음해 3월물 101W03 반환"

    def test_non_expiry_month_january(self):
        """비만기월 (1월) - 다음 만기월 3월물 반환"""
        # Arrange: 2025년 1월 15일
        test_date = datetime(2025, 1, 15)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W03", "1월에는 다음 만기월인 101W03 반환"

    def test_non_expiry_month_february(self):
        """비만기월 (2월) - 다음 만기월 3월물 반환"""
        # Arrange: 2025년 2월 10일
        test_date = datetime(2025, 2, 10)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W03", "2월에는 다음 만기월인 101W03 반환"

    def test_non_expiry_month_april(self):
        """비만기월 (4월) - 다음 만기월 6월물 반환"""
        # Arrange: 2025년 4월 10일
        test_date = datetime(2025, 4, 10)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W06", "4월에는 다음 만기월인 101W06 반환"

    def test_non_expiry_month_may(self):
        """비만기월 (5월) - 다음 만기월 6월물 반환"""
        # Arrange: 2025년 5월 15일
        test_date = datetime(2025, 5, 15)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W06", "5월에는 다음 만기월인 101W06 반환"

    def test_non_expiry_month_july(self):
        """비만기월 (7월) - 다음 만기월 9월물 반환"""
        # Arrange: 2025년 7월 20일
        test_date = datetime(2025, 7, 20)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W09", "7월에는 다음 만기월인 101W09 반환"

    def test_non_expiry_month_august(self):
        """비만기월 (8월) - 다음 만기월 9월물 반환"""
        # Arrange: 2025년 8월 5일
        test_date = datetime(2025, 8, 5)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W09", "8월에는 다음 만기월인 101W09 반환"

    def test_non_expiry_month_october(self):
        """비만기월 (10월) - 다음 만기월 12월물 반환"""
        # Arrange: 2025년 10월 10일
        test_date = datetime(2025, 10, 10)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W12", "10월에는 다음 만기월인 101W12 반환"

    def test_non_expiry_month_november(self):
        """비만기월 (11월) - 다음 만기월 12월물 반환"""
        # Arrange: 2025년 11월 25일
        test_date = datetime(2025, 11, 25)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W12", "11월에는 다음 만기월인 101W12 반환"

    def test_edge_case_second_thursday_calculation(self):
        """
        경계 케이스: 두 번째 목요일 계산 검증

        2025년 3월 두 번째 목요일은 3월 13일
        """
        # Arrange: 2025년 3월 13일 (만기일 당일)
        test_date = datetime(2025, 3, 13)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        # 만기일 당일은 "before" 처리 (date() 비교에서 > 사용)
        assert code == "101W03", "만기일 당일은 현재 월 코드 반환"

    def test_edge_case_second_thursday_next_day(self):
        """
        경계 케이스: 두 번째 목요일 다음 날

        2025년 3월 13일이 만기일이면, 3월 14일부터는 6월물
        """
        # Arrange: 2025년 3월 14일 (만기일 다음날)
        test_date = datetime(2025, 3, 14)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W06", "만기일 다음날은 다음 만기월 코드 반환"

    def test_year_rollover_from_december_to_march(self):
        """연말 롤오버: 12월 만기 후 다음해 3월물로 전환"""
        # Arrange: 2025년 12월 31일
        test_date = datetime(2025, 12, 31)

        # Act
        code = get_kospi200_futures_code(test_date)

        # Assert
        assert code == "101W03", "12월 말에는 다음해 3월물 101W03 반환"

    def test_code_format_validation(self):
        """코드 형식 검증: 항상 101W + 2자리 월"""
        # Arrange: 다양한 날짜
        test_dates = [
            datetime(2025, 1, 1),
            datetime(2025, 6, 15),
            datetime(2025, 12, 31),
        ]

        for test_date in test_dates:
            # Act
            code = get_kospi200_futures_code(test_date)

            # Assert
            assert code.startswith("101W"), f"{test_date}: 코드는 101W로 시작"
            assert len(code) == 6, f"{test_date}: 코드는 6자리"
            assert code[4:].isdigit(), f"{test_date}: 마지막 2자리는 숫자"
            month_part = int(code[4:])
            assert month_part in [3, 6, 9, 12], f"{test_date}: 만기월은 3, 6, 9, 12"
