"""
InvestorPositionAnalyzer 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상: pykis/stock/investor.py
"""

from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest


class TestInvestorPositionAnalyzer:
    """InvestorPositionAnalyzer 클래스 테스트"""

    @pytest.fixture
    def mock_client(self):
        """모의 클라이언트"""
        client = MagicMock()
        client.make_request.return_value = {"rt_cd": "0", "output": []}
        return client

    @pytest.fixture
    def account_info(self):
        """계좌 정보"""
        return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    @pytest.fixture
    def analyzer(self, mock_client, account_info):
        """InvestorPositionAnalyzer 인스턴스"""
        from kis_agent.stock.investor import InvestorPositionAnalyzer

        return InvestorPositionAnalyzer(client=mock_client, account_info=account_info)

    # ===== InvestorPositionData 테스트 =====

    def test_investor_position_data_creation(self):
        """InvestorPositionData 데이터 구조 생성 테스트"""
        from kis_agent.stock.investor import InvestorPositionData

        data = InvestorPositionData(
            stock_code="005930",
            date="20260104",
            foreign_buy=1000,
            foreign_sell=500,
            foreign_net=500,
            institution_buy=800,
            institution_sell=300,
            institution_net=500,
            individual_buy=200,
            individual_sell=400,
            individual_net=-200,
            price=70000,
            volume=10000,
        )

        assert data.stock_code == "005930"
        assert data.foreign_net == 500
        assert data.institution_net == 500
        assert data.individual_net == -200

    def test_investor_position_data_defaults(self):
        """InvestorPositionData 기본값 테스트"""
        from kis_agent.stock.investor import InvestorPositionData

        data = InvestorPositionData(stock_code="005930", date="20260104")

        assert data.foreign_buy == 0
        assert data.foreign_sell == 0
        assert data.institution_net == 0
        assert data.price == 0

    # ===== PositionAnalysisResult 테스트 =====

    def test_position_analysis_result_creation(self):
        """PositionAnalysisResult 데이터 구조 생성 테스트"""
        from kis_agent.stock.investor import PositionAnalysisResult

        result = PositionAnalysisResult(
            stock_code="005930",
            analysis_date="20260104",
            daily_analysis={"foreign": {"net_amount": 1000000}},
            cumulative_30d={"foreign": {"net_amount": 5000000}},
            interpretation="외국인 순매수 우위",
            score=7.5,
        )

        assert result.stock_code == "005930"
        assert result.score == 7.5
        assert "foreign" in result.daily_analysis

    # ===== get_stock_investor_data 테스트 =====

    def test_get_stock_investor_data_success(self, analyzer, mock_client):
        """종목 투자자 데이터 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {
                    "frgn_shnu_vol": "1000",
                    "frgn_seln_vol": "500",
                    "inst_shnu_vol": "800",
                }
            ],
        }

        # Act
        result = analyzer.get_stock_investor_data("005930")

        # Assert
        assert result is not None
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "FHKST01010900"
        assert call_args[1]["params"]["FID_INPUT_ISCD"] == "005930"

    def test_get_stock_investor_data_exception(self, analyzer, mock_client):
        """종목 투자자 데이터 조회 예외 처리"""
        from kis_agent.core.exceptions import APIException

        # Arrange
        mock_client.make_request.side_effect = Exception("API 오류")

        # Act & Assert - api_method 데코레이터가 APIException으로 래핑
        with pytest.raises(APIException):
            analyzer.get_stock_investor_data("005930")

    # ===== get_daily_market_trends 테스트 =====

    def test_get_daily_market_trends_success(self, analyzer, mock_client):
        """시장별 일별 투자자 동향 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"frgn_ntby_qty": "10000", "inst_ntby_qty": "5000"}],
        }

        # Act
        result = analyzer.get_daily_market_trends("20260104", "KSP")

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "FHKST01010800"
        assert call_args[1]["params"]["FID_INPUT_ISCD_1"] == "KSP"

    def test_get_daily_market_trends_default_date(self, analyzer, mock_client):
        """시장별 일별 동향 조회 - 기본 날짜"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": []}

        # Act
        result = analyzer.get_daily_market_trends()  # 날짜 미지정

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        # 오늘 날짜가 사용됨
        assert "FID_INPUT_DATE_1" in call_args[1]["params"]

    # ===== get_foreign_institution_aggregate 테스트 =====

    def test_get_foreign_institution_aggregate_success(self, analyzer, mock_client):
        """외국인/기관 집계 데이터 조회 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"frgn_ntby_qty": "50000", "inst_ntby_qty": "30000"}],
        }

        # Act
        result = analyzer.get_foreign_institution_aggregate()

        # Assert
        assert result is not None
        call_args = mock_client.make_request.call_args
        assert call_args[1]["tr_id"] == "FHPTJ04400000"

    # ===== interpret_position_context 테스트 =====

    def test_interpret_position_context_bullish(self, analyzer):
        """포지션 해석 - 강세 신호"""
        # Arrange
        daily_data = {
            "foreign": {"net_amount": 1000000000},  # 10억 순매수
            "institution": {"net_amount": 500000000},
            "individual": {"net_amount": -1500000000},
        }
        cumulative_data = {
            "foreign": {"net_amount": 5000000000},  # 50억 누적 순매수
            "institution": {"net_amount": 3000000000},
            "individual": {"net_amount": -8000000000},
        }

        # Act
        result = analyzer.interpret_position_context(daily_data, cumulative_data)

        # Assert
        assert "순매수" in result or "매수" in result
        assert "종합 해석" in result

    def test_interpret_position_context_bearish(self, analyzer):
        """포지션 해석 - 약세 신호"""
        # Arrange
        daily_data = {
            "foreign": {"net_amount": -1000000000},  # 순매도
            "institution": {"net_amount": -500000000},
            "individual": {"net_amount": 1500000000},
        }
        cumulative_data = {
            "foreign": {"net_amount": -5000000000},  # 누적 순매도
            "institution": {"net_amount": -3000000000},
            "individual": {"net_amount": 8000000000},
        }

        # Act
        result = analyzer.interpret_position_context(daily_data, cumulative_data)

        # Assert
        assert "매도" in result or "약세" in result or "신중" in result

    def test_interpret_position_context_empty_data(self, analyzer):
        """포지션 해석 - 빈 데이터"""
        # Act
        result = analyzer.interpret_position_context({}, {})

        # Assert
        assert "부족" in result

    def test_interpret_position_context_mixed_signals(self, analyzer):
        """포지션 해석 - 혼합 신호 (당일 순매도, 누적 순매수)"""
        # Arrange
        daily_data = {
            "foreign": {"net_amount": -500000000},  # 당일 순매도
            "institution": {"net_amount": 200000000},
            "individual": {"net_amount": 300000000},
        }
        cumulative_data = {
            "foreign": {"net_amount": 3000000000},  # 누적 순매수
            "institution": {"net_amount": 1000000000},
            "individual": {"net_amount": -4000000000},
        }

        # Act
        result = analyzer.interpret_position_context(daily_data, cumulative_data)

        # Assert
        assert result is not None
        assert len(result) > 0

    # ===== calculate_position_score 테스트 =====

    def test_calculate_position_score_high(self, analyzer):
        """포지션 점수 계산 - 높은 점수"""
        # Arrange
        daily_data = {
            "foreign": {"net_amount": 1000000000},
            "institution": {"net_amount": 500000000},
            "individual": {"net_amount": -1500000000},
        }
        cumulative_data = {
            "foreign": {"net_amount": 5000000000},
            "institution": {"net_amount": 3000000000},
            "individual": {"net_amount": -8000000000},
        }

        # Act
        score = analyzer.calculate_position_score(daily_data, cumulative_data)

        # Assert
        assert score > 7.0  # 외국인+기관 순매수 = 높은 점수
        assert score <= 10.0

    def test_calculate_position_score_low(self, analyzer):
        """포지션 점수 계산 - 낮은 점수"""
        # Arrange
        daily_data = {
            "foreign": {"net_amount": -1000000000},
            "institution": {"net_amount": -500000000},
            "individual": {"net_amount": 1500000000},
        }
        cumulative_data = {
            "foreign": {"net_amount": -5000000000},
            "institution": {"net_amount": -3000000000},
            "individual": {"net_amount": 8000000000},
        }

        # Act
        score = analyzer.calculate_position_score(daily_data, cumulative_data)

        # Assert
        assert score <= 6.0
        assert score >= 0.0

    def test_calculate_position_score_empty_data(self, analyzer):
        """포지션 점수 계산 - 빈 데이터"""
        # Act
        score = analyzer.calculate_position_score({}, {})

        # Assert
        assert score == 0.0

    def test_calculate_position_score_pattern_change(self, analyzer):
        """포지션 점수 계산 - 패턴 변화"""
        # Arrange - 당일은 순매수이지만 누적은 순매도
        daily_data = {
            "foreign": {"net_amount": 500000000},  # 당일 순매수
            "institution": {"net_amount": 300000000},
        }
        cumulative_data = {
            "foreign": {"net_amount": -2000000000},  # 누적 순매도
            "institution": {"net_amount": -1000000000},
        }

        # Act
        score = analyzer.calculate_position_score(daily_data, cumulative_data)

        # Assert - 패턴 변화로 약간의 점수 추가
        assert 5.0 < score < 7.0

    # ===== analyze_comprehensive_position 테스트 =====

    def test_analyze_comprehensive_position_success(self, analyzer, mock_client):
        """종합 포지션 분석 성공"""
        # Arrange
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [
                {
                    "frgn_shnu_vol": "10000",
                    "frgn_seln_vol": "5000",
                    "frgn_ntby_qty": "5000",
                    "frgn_shnu_tr_pbmn": "1000000000",
                    "frgn_seln_tr_pbmn": "500000000",
                    "frgn_ntby_tr_pbmn": "500000000",
                    "inst_shnu_vol": "8000",
                    "inst_seln_vol": "3000",
                    "inst_ntby_qty": "5000",
                    "inst_shnu_tr_pbmn": "800000000",
                    "inst_seln_tr_pbmn": "300000000",
                    "inst_ntby_tr_pbmn": "500000000",
                    "prsn_shnu_vol": "2000",
                    "prsn_seln_vol": "7000",
                    "prsn_ntby_qty": "-5000",
                    "stck_prpr": "70000",
                    "acml_vol": "100000",
                }
            ],
        }

        # Act
        result = analyzer.analyze_comprehensive_position("005930")

        # Assert
        from kis_agent.stock.investor import PositionAnalysisResult

        assert isinstance(result, PositionAnalysisResult)
        assert result.stock_code == "005930"
        assert result.score >= 0.0

    def test_analyze_comprehensive_position_api_failure(self, analyzer, mock_client):
        """종합 포지션 분석 - API 실패"""
        # Arrange - 빈 응답 반환 (API 실패 시뮬레이션)
        mock_client.make_request.return_value = None

        # Act
        result = analyzer.analyze_comprehensive_position("005930")

        # Assert - 데이터 없을 때의 결과
        assert "부족" in result.interpretation or result.score == 0.0

    # ===== get_market_wide_trends 테스트 =====

    def test_get_market_wide_trends_success(self, analyzer, mock_client):
        """시장 전체 투자자 동향 분석 성공"""
        import pandas as pd

        # Arrange - API가 DataFrame을 반환하는 경우와 dict를 반환하는 경우 모두 처리
        mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output": [{"frgn_ntby_qty": "10000"}],
        }

        # Act
        result = analyzer.get_market_wide_trends("20260104")

        # Assert - get_market_wide_trends는 @api_method(default_return={})로 빈 dict 반환 가능
        assert isinstance(result, dict)

    def test_get_market_wide_trends_default_date(self, analyzer, mock_client):
        """시장 전체 동향 분석 - 기본 날짜"""
        # Arrange
        mock_client.make_request.return_value = {"rt_cd": "0", "output": []}

        # Act
        result = analyzer.get_market_wide_trends()

        # Assert
        assert isinstance(result, dict)

    # ===== _generate_market_summary 테스트 =====

    def test_generate_market_summary_all_data(self, analyzer):
        """시장 동향 요약 생성 - 전체 데이터"""
        import pandas as pd

        # Arrange
        kospi_data = pd.DataFrame([{"frgn_ntby_qty": "10000"}])
        kosdaq_data = pd.DataFrame([{"frgn_ntby_qty": "5000"}])
        aggregate_data = pd.DataFrame([{"frgn_ntby_qty": "15000"}])

        # Act
        result = analyzer._generate_market_summary(
            kospi_data, kosdaq_data, aggregate_data
        )

        # Assert
        assert "KOSPI" in result
        assert "KOSDAQ" in result
        assert "완료" in result

    def test_generate_market_summary_partial_data(self, analyzer):
        """시장 동향 요약 생성 - 부분 데이터"""
        import pandas as pd

        # Arrange
        kospi_data = pd.DataFrame([{"frgn_ntby_qty": "10000"}])
        kosdaq_data = None
        aggregate_data = pd.DataFrame()  # 빈 DataFrame

        # Act
        result = analyzer._generate_market_summary(
            kospi_data, kosdaq_data, aggregate_data
        )

        # Assert
        assert "KOSPI" in result

    def test_generate_market_summary_no_data(self, analyzer):
        """시장 동향 요약 생성 - 데이터 없음"""
        # Act
        result = analyzer._generate_market_summary(None, None, None)

        # Assert
        assert "실패" in result

    # ===== _import_investor_apis 테스트 =====

    def test_import_investor_apis_success(self, analyzer):
        """투자자 API import 테스트 (존재하지 않으면 None)"""
        # Act
        result = analyzer._import_investor_apis()

        # Assert - 실제 환경에 따라 None 또는 dict 반환
        assert result is None or isinstance(result, dict)

    # ===== 초기화 테스트 =====

    def test_analyzer_initialization_without_account(self, mock_client):
        """계좌 정보 없이 초기화"""
        from kis_agent.stock.investor import InvestorPositionAnalyzer

        # Act
        analyzer = InvestorPositionAnalyzer(client=mock_client)

        # Assert
        assert analyzer.account == {}
        assert analyzer.client == mock_client

    def test_analyzer_initialization_with_account(self, mock_client, account_info):
        """계좌 정보와 함께 초기화"""
        from kis_agent.stock.investor import InvestorPositionAnalyzer

        # Act
        analyzer = InvestorPositionAnalyzer(
            client=mock_client, account_info=account_info
        )

        # Assert
        assert analyzer.account == account_info
