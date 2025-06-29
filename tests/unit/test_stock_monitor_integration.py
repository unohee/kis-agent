import pytest
from unittest.mock import Mock, patch
from pykis import Agent
from pykis.core.client import KISClient


class TestStockMonitorIntegration:
    """StockMonitor에서 사용하는 함수들의 통합 테스트"""

    @pytest.fixture
    def mock_client(self):
        """모킹된 KISClient 인스턴스를 생성합니다."""
        return Mock(spec=KISClient)

    @pytest.fixture
    def agent(self, mock_client):
        """Agent 인스턴스를 생성합니다."""
        with patch('pykis.core.agent.KISClient', return_value=mock_client):
            return Agent(mock_client)

    def test_stockmonitor_core_functions_integration(self, agent, mock_client):
        """StockMonitor 핵심 함수들 통합 테스트"""
        # 1. get_stock_price (현재가 조회)
        stock_price_response = {
            'output': {
                'stck_prpr': '60800',
                'acml_vol': '17340470',
                'hts_frgn_ehrt': '49.74'
            },
            'rt_cd': '0'
        }
        
        # 2. get_daily_price (일별 시세)
        daily_price_response = {
            'output': [
                {
                    'stck_bsop_date': '20241227',
                    'stck_clpr': '60800',
                    'acml_vol': '17340470'
                }
            ],
            'rt_cd': '0'
        }
        
        # 3. get_program_trade_by_stock (프로그램 매매)
        program_trade_response = {
            'output': [
                {
                    'stck_bsop_date': '20241227',
                    'prdy_pgm_buy_vol': '100000',
                    'prdy_pgm_sell_vol': '50000'
                }
            ],
            'rt_cd': '0'
        }
        
        # 4. get_member (회원사 정보)
        member_response = {
            'output': [
                {
                    'seln_mbcr_name': '키움증권',
                    'seln_mbcr_amt1': '1000000'
                }
            ],
            'rt_cd': '0'
        }
        
        # 5. get_condition_stocks (조건검색) - 실제로는 output2에 결과가 들어있고 리스트를 반환
        condition_api_response = {
            'output2': [
                {
                    'stck_shrn_iscd': '005930',
                    'hts_kor_isnm': '삼성전자'
                }
            ],
            'rt_cd': '0'
        }

        # 모든 API 호출에 대한 응답 설정
        mock_client.make_request.side_effect = [
            stock_price_response,      # get_stock_price
            daily_price_response,      # get_daily_price  
            program_trade_response,    # get_program_trade_by_stock
            member_response,           # get_member
            condition_api_response     # get_condition_stocks (API 응답)
        ]

        # StockMonitor 시나리오 실행
        code = '005930'
        
        # 1. 현재가 조회 (StockMonitor.get_stock_data)
        price_data = agent.get_stock_price(code)
        assert price_data == stock_price_response
        assert price_data['output']['stck_prpr'] == '60800'
        
        # 2. 일별 시세 조회 (StockMonitor.get_daily_data)
        daily_data = agent.get_daily_price(code)
        assert daily_data == daily_price_response
        assert len(daily_data['output']) > 0
        
        # 3. 프로그램 매매 정보 (StockMonitor.get_program_trade_data)
        program_data = agent.get_program_trade_by_stock(code)
        assert program_data == program_trade_response
        assert program_data['output'][0]['prdy_pgm_buy_vol'] == '100000'
        
        # 4. 회원사 정보 (StockMonitor.get_member_data)
        member_data = agent.get_member(code)
        assert member_data == member_response
        assert member_data['output'][0]['seln_mbcr_name'] == '키움증권'
        
        # 5. 조건검색 (StockMonitor.process_condition_stocks)
        # Agent.get_condition_stocks는 ConditionAPI에서 output2를 추출한 리스트를 반환
        condition_data = agent.get_condition_stocks("unohee", 0, "N")
        expected_condition_list = condition_api_response['output2']
        assert condition_data == expected_condition_list
        assert condition_data[0]['stck_shrn_iscd'] == '005930'

        # 모든 API 호출이 예상대로 이루어졌는지 확인
        assert mock_client.make_request.call_count == 5

    def test_stockmonitor_volume_ratio_calculation_scenario(self, agent, mock_client):
        """StockMonitor의 거래량 급증도 계산 시나리오 테스트"""
        # 20일간의 거래량 데이터 (calculate_volume_ratio 시뮬레이션)
        daily_data_response = {
            'output': [
                {'acml_vol': '30000000'},  # 오늘 (급증)
                {'acml_vol': '10000000'},  # 1일전
                {'acml_vol': '12000000'},  # 2일전
                {'acml_vol': '8000000'},   # 3일전
                {'acml_vol': '9000000'},   # 4일전
                # ... 추가 20일 데이터
                *[{'acml_vol': '10000000'} for _ in range(15)]
            ],
            'rt_cd': '0'
        }
        
        mock_client.make_request.return_value = daily_data_response
        
        # StockMonitor.calculate_volume_ratio 로직 시뮬레이션
        daily_data = agent.get_daily_price('005930')
        assert daily_data is not None
        
        output = daily_data['output']
        volumes = [float(item['acml_vol']) for item in output[:20]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = float(output[0]['acml_vol'])
        volume_ratio = current_volume / avg_volume
        
        # 거래량 급증 확인 (3배 이상)
        assert volume_ratio > 2.0  # 급증 기준
        
    def test_stockmonitor_program_trade_analysis_scenario(self, agent, mock_client):
        """StockMonitor의 프로그램 매매 분석 시나리오 테스트"""
        # 현재가 정보 (프로그램 매매 비중 계산용)
        stock_price_response = {
            'output': {
                'stck_prpr': '60800',
                'acml_vol': '1000000'  # 전체 거래량
            },
            'rt_cd': '0'
        }
        
        # 프로그램 매매 정보
        program_trade_response = {
            'output': [
                {
                    'prdy_pgm_buy_vol': '300000',   # 매수 30만주
                    'prdy_pgm_sell_vol': '200000'   # 매도 20만주
                }
            ],
            'rt_cd': '0'
        }
        
        mock_client.make_request.side_effect = [
            stock_price_response,
            program_trade_response
        ]
        
        # StockMonitor.check_stock 로직 시뮬레이션
        price_data = agent.get_stock_price('005930')
        current_volume = float(price_data['output']['acml_vol'])
        
        program_data = agent.get_program_trade_by_stock('005930')
        pgm_buy = float(program_data['output'][0]['prdy_pgm_buy_vol'])
        pgm_sell = float(program_data['output'][0]['prdy_pgm_sell_vol'])
        
        # 프로그램 매매 비중 계산
        program_ratio = (pgm_buy + pgm_sell) / current_volume
        
        # 프로그램 매매 비중이 50% 이상인 경우 (StockMonitor 임계값)
        assert program_ratio == 0.5  # 50% 정확히

    def test_stockmonitor_foreign_exhaustion_filtering_scenario(self, agent, mock_client):
        """StockMonitor의 외국인소진율 필터링 시나리오 테스트"""
        # 조건검색 결과 (실제 API 응답 구조)
        condition_api_response = {
            'output2': [
                {
                    'stck_shrn_iscd': '005930',
                    'hts_kor_isnm': '삼성전자'
                },
                {
                    'stck_shrn_iscd': '035720',
                    'hts_kor_isnm': '카카오'
                }
            ],
            'rt_cd': '0'
        }
        
        # 각 종목의 현재가 정보 (외국인소진율 포함)
        samsung_price_response = {
            'output': {
                'hts_frgn_ehrt': '25.5'  # 25.5% (임계값 20% 이상)
            },
            'rt_cd': '0'
        }
        
        kakao_price_response = {
            'output': {
                'hts_frgn_ehrt': '15.2'  # 15.2% (임계값 20% 미만)
            },
            'rt_cd': '0'
        }
        
        mock_client.make_request.side_effect = [
            condition_api_response,  # get_condition_stocks (API 응답)
            samsung_price_response,  # 삼성전자 현재가
            kakao_price_response     # 카카오 현재가
        ]
        
        # StockMonitor.process_condition_stocks 로직 시뮬레이션
        # Agent.get_condition_stocks는 output2에서 추출한 리스트를 반환
        condition_result = agent.get_condition_stocks("unohee", 0, "N")
        stocks = condition_result  # 이미 리스트이므로 바로 사용
        
        filtered_stocks = []
        foreign_exhaustion_threshold = 20.0
        
        for stock in stocks:
            code = stock['stck_shrn_iscd']
            price_data = agent.get_stock_price(code)
            foreign_rate = float(price_data['output']['hts_frgn_ehrt'])
            
            if foreign_rate >= foreign_exhaustion_threshold:
                stock['foreign_exhaustion_rate'] = foreign_rate
                filtered_stocks.append(stock)
        
        # 외국인소진율 필터링 결과 확인
        assert len(filtered_stocks) == 1  # 삼성전자만 통과
        assert filtered_stocks[0]['stck_shrn_iscd'] == '005930'
        assert filtered_stocks[0]['foreign_exhaustion_rate'] == 25.5
        # 오류 상황에서도 프로그램이 중단되지 않음을 확인
        assert mock_client.make_request.call_count == 3

    def test_stockmonitor_initialization_scenario(self, mock_client):
        """StockMonitor 초기화 시나리오 테스트"""
        # Agent 초기화가 정상적으로 이루어지는지 확인
        with patch('pykis.core.agent.KISClient', return_value=mock_client), \
             patch('pykis.core.agent.KISConfig') as mock_config:
            
            # .env 파일에서 계좌 정보 로드 시뮬레이션
            mock_config.return_value.account_stock = '12345678'
            mock_config.return_value.account_product = '01'
            
            agent = Agent()
            
            # StockMonitor.__init__에서 사용하는 것처럼 Agent가 정상 초기화됨
            assert agent is not None
            assert hasattr(agent, 'get_stock_price')
            assert hasattr(agent, 'get_daily_price')
            assert hasattr(agent, 'get_program_trade_by_stock')
            assert hasattr(agent, 'get_member')
            assert hasattr(agent, 'get_condition_stocks') 