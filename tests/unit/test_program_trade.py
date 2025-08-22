import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pykis.program.trade import ProgramTradeAPI
from pykis.core.client import KISClient


class TestProgramTradeAPI:
    """ProgramTradeAPI 클래스 단위 테스트"""

    @pytest.fixture
    def mock_client(self):
        """모킹된 KISClient 인스턴스를 생성합니다."""
        return Mock(spec=KISClient)

    @pytest.fixture
    def program_api(self, mock_client):
        """ProgramTradeAPI 인스턴스를 생성합니다."""
        return ProgramTradeAPI(mock_client)

    @pytest.fixture
    def program_api_with_account(self, mock_client):
        """계좌 정보가 있는 ProgramTradeAPI 인스턴스를 생성합니다."""
        account_info = {'CANO': '12345678', 'ACNT_PRDT_CD': '01'}
        return ProgramTradeAPI(mock_client, account_info)

    def test_init(self, mock_client):
        """ProgramTradeAPI 초기화 테스트"""
        api = ProgramTradeAPI(mock_client)
        assert api.client == mock_client
        assert api.account is None

    def test_init_with_account(self, mock_client):
        """계좌 정보가 있는 ProgramTradeAPI 초기화 테스트"""
        account_info = {'CANO': '12345678', 'ACNT_PRDT_CD': '01'}
        api = ProgramTradeAPI(mock_client, account_info)
        assert api.client == mock_client
        assert api.account == account_info

    def test_get_program_trade_by_stock_success(self, program_api, mock_client):
        """get_program_trade_by_stock 성공 테스트"""
        # Given
        expected_result = {
            'output': [
                {
                    'stck_bsop_date': '20241227',
                    'prdy_pgm_buy_vol': '100000',
                    'prdy_pgm_sell_vol': '50000'
                }
            ],
            'rt_cd': '0'
        }
        mock_client.make_request.return_value = expected_result

        # When
        result = program_api.get_program_trade_by_stock('005930')

        # Then
        assert result == expected_result
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert 'endpoint' in call_args.kwargs
        assert call_args.kwargs['tr_id'] == 'FHPPG04650101'
        assert call_args.kwargs['params']['FID_INPUT_ISCD'] == '005930'
        assert call_args.kwargs['params']['FID_COND_MRKT_DIV_CODE'] == 'J'

    @patch('pykis.program.trade.datetime')
    def test_get_program_trade_by_stock_with_default_date(self, mock_datetime, program_api, mock_client):
        """get_program_trade_by_stock 기본 날짜 테스트"""
        # Given
        mock_datetime.now.return_value.strftime.return_value = datetime.now().strftime("%Y%m%d")
        expected_result = {'output': [], 'rt_cd': '0'}
        mock_client.make_request.return_value = expected_result
    
        # When
        result = program_api.get_program_trade_by_stock('005930')
    
        # Then
        assert result == expected_result
        call_args = mock_client.make_request.call_args
        assert 'FID_INPUT_DATE_1' not in call_args.kwargs['params']

    def test_get_program_trade_by_stock_with_specific_date(self, program_api, mock_client):
        """get_program_trade_by_stock 특정 날짜 지정 테스트"""
        # Given
        expected_result = {'output': [], 'rt_cd': '0'}
        mock_client.make_request.return_value = expected_result

        # When
        result = program_api.get_program_trade_by_stock('005930', '20241225')

        # Then
        assert result == expected_result
        call_args = mock_client.make_request.call_args
        assert call_args.kwargs['params']['FID_INPUT_DATE_1'] == '20241225'

    

    def test_get_program_trade_daily_summary_success(self, program_api, mock_client):
        """get_program_trade_daily_summary 성공 테스트"""
        # Given
        expected_result = {
            'output': [
                {
                    'stck_bsop_date': '20241227',
                    'prgr_shnu_vol': '150000',
                    'prgr_seln_vol': '100000'
                }
            ],
            'rt_cd': '0'
        }
        mock_client.make_request.return_value = expected_result

        # When
        result = program_api.get_program_trade_daily_summary('005930', '20241227')

        # Then
        assert result == expected_result
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args.kwargs['tr_id'] == 'FHPPG04650200'
        assert call_args.kwargs['params']['FID_INPUT_ISCD'] == '005930'
        assert call_args.kwargs['params']['FID_INPUT_DATE_1'] == '20241227'

    def test_get_program_trade_market_daily_success(self, program_api, mock_client):
        """get_program_trade_market_daily 성공 테스트"""
        # Given
        expected_result = {
            'output': [
                {
                    'stck_bsop_date': '20241227',
                    'tot_pgm_shnu_vol': '1000000'
                }
            ],
            'rt_cd': '0'
        }
        mock_client.make_request.return_value = expected_result

        # When
        result = program_api.get_program_trade_market_daily('20241201', '20241227')

        # Then
        assert result == expected_result
        mock_client.make_request.assert_called_once()
        call_args = mock_client.make_request.call_args
        assert call_args.kwargs['tr_id'] == 'FHPPG04600000'
        assert call_args.kwargs['params']['FID_INPUT_DATE_1'] == '20241201'
        assert call_args.kwargs['params']['FID_INPUT_DATE_2'] == '20241227'

    

    def test_get_program_trade_by_stock_client_exception(self, program_api, mock_client):
        """get_program_trade_by_stock 클라이언트 예외 테스트"""
        # Given
        mock_client.make_request.side_effect = Exception("API 호출 실패")

        # When / Then
        with pytest.raises(Exception, match="API 호출 실패"):
            program_api.get_program_trade_by_stock('005930')
        mock_client.make_request.assert_called_once()

    

    def test_get_program_trade_daily_summary_client_exception(self, program_api, mock_client):
        """get_program_trade_daily_summary 클라이언트 예외 테스트"""
        # Given
        mock_client.make_request.side_effect = Exception("API 호출 실패")

        # When / Then
        with pytest.raises(Exception, match="API 호출 실패"):
            program_api.get_program_trade_daily_summary('005930', '20241227')
        mock_client.make_request.assert_called_once()

    def test_get_program_trade_market_daily_client_exception(self, program_api, mock_client):
        """get_program_trade_market_daily 클라이언트 예외 테스트"""
        # Given
        mock_client.make_request.side_effect = Exception("API 호출 실패")

        # When / Then
        with pytest.raises(Exception, match="API 호출 실패"):
            program_api.get_program_trade_market_daily('20241201', '20241227')
        mock_client.make_request.assert_called_once()

     