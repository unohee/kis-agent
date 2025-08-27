"""
투자자 분석기 테스트
"""

import pandas as pd
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from pykis.stock.investor import (
    InvestorPositionAnalyzer,
    InvestorPositionData,
    PositionAnalysisResult
)
from pykis.core.client import KISClient


class TestInvestorPositionData:
    """InvestorPositionData 데이터클래스 테스트"""
    
    def test_dataclass_creation(self):
        """데이터클래스 기본 생성"""
        data = InvestorPositionData(
            stock_code="005930",
            date="20250127"
        )
        
        assert data.stock_code == "005930"
        assert data.date == "20250127"
        assert data.foreign_buy == 0
        assert data.foreign_net_amount == 0


class TestPositionAnalysisResult:
    """PositionAnalysisResult 데이터클래스 테스트"""
    
    def test_analysis_result_creation(self):
        """분석 결과 데이터클래스 생성"""
        result = PositionAnalysisResult(
            stock_code="005930",
            analysis_date="20250127",
            position_score=75.5,
            summary="긍정적 포지션"
        )
        
        assert result.stock_code == "005930"
        assert result.analysis_date == "20250127"
        assert result.position_score == 75.5
        assert result.summary == "긍정적 포지션"


class TestInvestorPositionAnalyzer:
    """InvestorPositionAnalyzer 메인 클래스 테스트"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock KISClient 픽스처"""
        client = Mock(spec=KISClient)
        client.token = "test_token"
        client.app_key = "test_app_key"
        return client
    
    @pytest.fixture
    def account_info(self):
        """테스트 계좌 정보"""
        return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
    
    @pytest.fixture
    def analyzer(self, mock_client, account_info):
        """InvestorPositionAnalyzer 인스턴스"""
        with patch.object(InvestorPositionAnalyzer, '_import_investor_apis'):
            return InvestorPositionAnalyzer(client=mock_client, account_info=account_info)

    def test_init_basic(self, mock_client, account_info):
        """기본 초기화 테스트"""
        with patch.object(InvestorPositionAnalyzer, '_import_investor_apis') as mock_import:
            analyzer = InvestorPositionAnalyzer(client=mock_client, account_info=account_info)
            
            assert analyzer.client == mock_client
            assert analyzer.account_info == account_info
            mock_import.assert_called_once()
    
    def test_init_without_account(self, mock_client):
        """계좌 정보 없이 초기화"""
        with patch.object(InvestorPositionAnalyzer, '_import_investor_apis'):
            analyzer = InvestorPositionAnalyzer(client=mock_client)
            
            assert analyzer.client == mock_client
            assert analyzer.account_info is None

    @patch('pykis.stock.investor_api.InvestorAPI')
    @patch('pykis.stock.market_api.MarketAPI')
    def test_import_investor_apis(self, mock_market_api, mock_investor_api, mock_client):
        """API 임포트 테스트"""
        analyzer = InvestorPositionAnalyzer(client=mock_client)
        
        mock_investor_api.assert_called_once_with(client=mock_client, account_info=None)
        mock_market_api.assert_called_once_with(client=mock_client)
        assert analyzer.investor_api == mock_investor_api.return_value
        assert analyzer.market_api == mock_market_api.return_value

    def test_get_stock_investor_data_success(self, analyzer):
        """종목 투자자 데이터 조회 성공"""
        # Mock 데이터 설정
        mock_response = pd.DataFrame([{
            'stock_code': '005930',
            'foreign_buy_vol': 1000,
            'institution_net_amt': 500000
        }])
        
        analyzer.investor_api = Mock()
        analyzer.investor_api.get_stock_investor.return_value = mock_response
        
        result = analyzer.get_stock_investor_data("005930")
        
        assert result is not None
        assert len(result) == 1
        analyzer.investor_api.get_stock_investor.assert_called_once_with("005930")
    
    def test_get_stock_investor_data_exception(self, analyzer):
        """종목 투자자 데이터 조회 예외"""
        analyzer.investor_api = Mock()
        analyzer.investor_api.get_stock_investor.side_effect = Exception("API Error")
        
        result = analyzer.get_stock_investor_data("005930")
        
        assert result is None

    def test_get_daily_market_trends_success(self, analyzer):
        """일일 시장 동향 조회 성공"""
        mock_response = pd.DataFrame([{
            'market_type': 'KOSPI',
            'foreign_net_amt': 1000000,
            'date': '20250127'
        }])
        
        analyzer.market_api = Mock()
        analyzer.market_api.get_daily_investor_trend.return_value = mock_response
        
        result = analyzer.get_daily_market_trends("20250127", "KSP")
        
        assert result is not None
        analyzer.market_api.get_daily_investor_trend.assert_called_once_with("20250127", "KSP")

    def test_get_daily_market_trends_default_date(self, analyzer):
        """기본 날짜로 시장 동향 조회"""
        analyzer.market_api = Mock()
        analyzer.market_api.get_daily_investor_trend.return_value = pd.DataFrame()
        
        with patch('pykis.stock.investor.datetime') as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "20250127"
            
            result = analyzer.get_daily_market_trends()
            
            analyzer.market_api.get_daily_investor_trend.assert_called_once_with("20250127", "KSP")

    def test_analyze_daily_position_success(self, analyzer):
        """일일 포지션 분석 성공"""
        mock_data = pd.DataFrame([{
            'stock_code': '005930',
            'foreign_buy_vol': 1000,
            'foreign_sell_vol': 800,
            'foreign_net_vol': 200,
            'institution_net_amt': 500000
        }])
        
        analyzer.get_stock_investor_data = Mock(return_value=mock_data)
        
        result = analyzer.analyze_daily_position("005930")
        
        assert isinstance(result, dict)
        assert 'stock_code' in result
        assert result['stock_code'] == "005930"
        assert 'foreign_net_vol' in result
        assert result['foreign_net_vol'] == 200

    def test_analyze_daily_position_no_data(self, analyzer):
        """일일 포지션 분석 - 데이터 없음"""
        analyzer.get_stock_investor_data = Mock(return_value=None)
        
        result = analyzer.analyze_daily_position("005930")
        
        assert result == {}

    def test_get_30day_cumulative_analysis_success(self, analyzer):
        """30일 누적 분석 성공"""
        # Mock 30일 데이터 생성
        mock_data = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            mock_data.append({
                'date': date,
                'foreign_net_vol': 100 + i,
                'institution_net_amt': 50000 * (i % 5)
            })
        
        mock_df = pd.DataFrame(mock_data)
        
        with patch.object(analyzer, 'get_stock_investor_data', return_value=mock_df):
            result = analyzer.get_30day_cumulative_analysis("005930")
            
            assert isinstance(result, dict)
            assert 'cumulative_foreign_net' in result
            assert 'avg_daily_foreign_net' in result

    def test_interpret_position_context(self, analyzer):
        """포지션 컨텍스트 해석 테스트"""
        daily_data = {
            'foreign_net_vol': 1000,
            'institution_net_amt': 500000,
            'individual_net_vol': -1500
        }
        
        cumulative_data = {
            'cumulative_foreign_net': 15000,
            'avg_daily_foreign_net': 500
        }
        
        result = analyzer.interpret_position_context(daily_data, cumulative_data)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_position_score(self, analyzer):
        """포지션 점수 계산 테스트"""
        daily_data = {
            'foreign_net_vol': 1000,
            'institution_net_amt': 500000,
            'individual_net_vol': -1500
        }
        
        cumulative_data = {
            'cumulative_foreign_net': 15000,
            'trend_strength': 0.7
        }
        
        result = analyzer.calculate_position_score(daily_data, cumulative_data)
        
        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_analyze_comprehensive_position_success(self, analyzer):
        """종합 포지션 분석 성공"""
        # Mock 메소드들 설정
        daily_data = {'foreign_net_vol': 1000, 'institution_net_amt': 500000}
        cumulative_data = {'cumulative_foreign_net': 15000}
        
        analyzer.analyze_daily_position = Mock(return_value=daily_data)
        analyzer.get_30day_cumulative_analysis = Mock(return_value=cumulative_data)
        analyzer.interpret_position_context = Mock(return_value="긍정적 신호")
        analyzer.calculate_position_score = Mock(return_value=75.5)
        
        result = analyzer.analyze_comprehensive_position("005930")
        
        assert isinstance(result, PositionAnalysisResult)
        assert result.stock_code == "005930"
        assert result.position_score == 75.5
        assert result.summary == "긍정적 신호"

    def test_get_market_wide_trends_success(self, analyzer):
        """전체 시장 동향 조회 성공"""
        kospi_data = pd.DataFrame([{'foreign_net_amt': 1000000}])
        kosdaq_data = pd.DataFrame([{'foreign_net_amt': 500000}])
        aggregate_data = pd.DataFrame([{'total_foreign_net': 1500000}])
        
        analyzer.get_daily_market_trends = Mock()
        analyzer.get_daily_market_trends.side_effect = [kospi_data, kosdaq_data]
        analyzer.get_foreign_institution_aggregate = Mock(return_value=aggregate_data)
        
        with patch.object(analyzer, '_generate_market_summary', return_value="시장 요약"):
            result = analyzer.get_market_wide_trends("20250127")
            
            assert isinstance(result, dict)
            assert 'kospi_trends' in result
            assert 'kosdaq_trends' in result
            assert 'summary' in result

    def test_generate_market_summary(self, analyzer):
        """시장 요약 생성 테스트"""
        kospi_data = pd.DataFrame([{'foreign_net_amt': 1000000}])
        kosdaq_data = pd.DataFrame([{'foreign_net_amt': 500000}])
        aggregate_data = pd.DataFrame([{'total_volume': 10000000}])
        
        result = analyzer._generate_market_summary(kospi_data, kosdaq_data, aggregate_data)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_dataframe_handling(self, analyzer):
        """빈 DataFrame 처리 테스트"""
        empty_df = pd.DataFrame()
        
        analyzer.get_stock_investor_data = Mock(return_value=empty_df)
        
        result = analyzer.analyze_daily_position("005930")
        
        assert result == {}