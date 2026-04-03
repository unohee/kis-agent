"""kis_agent CLI Bridge 유닛 테스트.

JSON stdin/stdout 기반 subprocess 통신 기능 검증.
"""

import json
from unittest.mock import Mock, MagicMock, patch
import pytest

from kis_agent.cli_bridge import (
    call_method,
    handle_request,
    output_json,
    check_market_status,
    load_env,
    create_agent,
)


class TestCallMethod:
    """call_method 함수 테스트."""

    def test_valid_method_call(self):
        """유효한 메서드 호출 테스트."""
        # Mock agent 생성
        mock_api = Mock()
        mock_api.test_method = Mock(return_value={"result": "success"})

        mock_agent = Mock()
        mock_agent.test_domain = mock_api

        result = call_method(mock_agent, "test_domain.test_method", {})
        assert result == {"result": "success"}

    def test_method_with_params(self):
        """파라미터를 포함한 메서드 호출 테스트."""
        mock_api = Mock()
        mock_api.get_price = Mock(return_value=100)

        mock_agent = Mock()
        mock_agent.stock_api = mock_api

        result = call_method(mock_agent, "stock_api.get_price", {"code": "005930"})
        assert result == 100
        mock_api.get_price.assert_called_once_with(code="005930")

    def test_invalid_method_path_format(self):
        """잘못된 메서드 경로 형식 테스트."""
        mock_agent = Mock()

        with pytest.raises(ValueError, match="Invalid method path: invalid"):
            call_method(mock_agent, "invalid", {})

    def test_missing_domain(self):
        """도메인이 없는 경우 테스트."""
        mock_agent = Mock(spec=[])

        with pytest.raises(AttributeError, match="Agent has no attribute 'nonexistent'"):
            call_method(mock_agent, "nonexistent.method", {})

    def test_missing_method(self):
        """메서드가 없는 경우 테스트."""
        mock_api = Mock(spec=[])
        mock_agent = Mock()
        mock_agent.test_domain = mock_api

        with pytest.raises(AttributeError, match="test_domain has no method 'nonexistent'"):
            call_method(mock_agent, "test_domain.nonexistent", {})

    def test_non_callable_attribute(self):
        """호출 불가능한 속성 테스트."""
        mock_api = Mock()
        mock_api.not_a_method = "just a string"

        mock_agent = Mock()
        mock_agent.test_domain = mock_api

        with pytest.raises(TypeError, match="test_domain.not_a_method is not callable"):
            call_method(mock_agent, "test_domain.not_a_method", {})


class TestHandleRequest:
    """handle_request 함수 테스트."""

    def test_valid_json_request(self):
        """유효한 JSON 요청 처리 테스트."""
        mock_agent = Mock()
        mock_agent.stock_api = Mock()
        mock_agent.stock_api.get_price = Mock(return_value={"price": 10000})

        request = {
            "method": "stock_api.get_price",
            "params": {"code": "005930"},
            "pretty": False
        }

        with patch('kis_agent.cli_bridge.output_json') as mock_output:
            handle_request(json.dumps(request), mock_agent)
            mock_output.assert_called_once()
            call_args = mock_output.call_args[0][0]
            assert call_args["success"] is True
            assert call_args["data"] == {"price": 10000}

    def test_invalid_json(self):
        """잘못된 JSON 요청 처리 테스트."""
        mock_agent = Mock()
        response = handle_request("not valid json", mock_agent)

        result = json.loads(response)
        assert result["success"] is False
        assert "Invalid JSON" in result["error"]
        assert result["code"] == "JSONDecodeError"

    def test_missing_method_field(self):
        """method 필드가 없는 경우 테스트."""
        mock_agent = Mock()
        request = {"params": {}}

        response = handle_request(json.dumps(request), mock_agent)
        result = json.loads(response)

        assert result["success"] is False
        assert "Missing 'method' field" in result["error"]
        assert result["code"] == "ValidationError"

    def test_method_execution_error(self):
        """메서드 실행 중 에러 발생 테스트."""
        mock_agent = Mock()
        mock_agent.stock_api = Mock()
        mock_agent.stock_api.get_price = Mock(side_effect=ValueError("Invalid code"))

        request = {
            "method": "stock_api.get_price",
            "params": {"code": "invalid"},
            "pretty": False
        }

        with patch('kis_agent.cli_bridge.output_json'):
            response = handle_request(json.dumps(request), mock_agent)
            result = json.loads(response)

            assert result["success"] is False
            assert "Invalid code" in result["error"]
            assert result["code"] == "ValueError"

    def test_default_params(self):
        """기본 파라미터 값 테스트."""
        mock_agent = Mock()
        mock_agent.test_api = Mock()
        mock_agent.test_api.method = Mock(return_value="result")

        request = {"method": "test_api.method"}

        with patch('kis_agent.cli_bridge.output_json'):
            handle_request(json.dumps(request), mock_agent)
            mock_agent.test_api.method.assert_called_once_with()

    def test_empty_params(self):
        """빈 파라미터 딕셔너리 테스트."""
        mock_agent = Mock()
        mock_agent.test_api = Mock()
        mock_agent.test_api.method = Mock(return_value="result")

        request = {"method": "test_api.method", "params": {}}

        with patch('kis_agent.cli_bridge.output_json'):
            handle_request(json.dumps(request), mock_agent)
            mock_agent.test_api.method.assert_called_once_with()


class TestOutputJson:
    """output_json 함수 테스트."""

    def test_output_without_notice(self, capsys):
        """공지사항 없이 출력 테스트."""
        data = {"success": True, "data": {"key": "value"}}

        with patch('kis_agent.cli_bridge._market_status', {"notice": None}):
            output_json(data, pretty=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result == data
        assert "_notice" not in result

    def test_output_with_notice(self, capsys):
        """공지사항 포함 출력 테스트."""
        data = {"success": True, "data": {"key": "value"}}

        with patch('kis_agent.cli_bridge._market_status', {"notice": "Market closed"}):
            output_json(data, pretty=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["_notice"] == "Market closed"

    def test_pretty_output(self, capsys):
        """pretty 요청이어도 브리지는 단일 라인으로 출력."""
        data = {"success": True, "data": {"nested": "value"}}

        with patch('kis_agent.cli_bridge._market_status', {"notice": None}):
            output_json(data, pretty=True)

        captured = capsys.readouterr()
        assert captured.out.count("\n") == 1
        result = json.loads(captured.out)
        assert result == data

    def test_unicode_handling(self, capsys):
        """유니코드 처리 테스트."""
        data = {"success": True, "data": {"message": "한글 테스트"}}

        with patch('kis_agent.cli_bridge._market_status', {"notice": None}):
            output_json(data, pretty=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["data"]["message"] == "한글 테스트"

    def test_notice_not_added_to_non_data_response(self, capsys):
        """데이터가 없는 응답에는 공지사항을 추가하지 않음."""
        data = {"success": False, "error": "Error message"}

        with patch('kis_agent.cli_bridge._market_status', {"notice": "Market closed"}):
            output_json(data, pretty=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "_notice" not in result


class TestCheckMarketStatus:
    """check_market_status 함수 테스트."""

    def test_market_status_caching(self):
        """시장 상태 캐싱 테스트."""
        mock_agent = Mock()
        mock_agent.stock_api = Mock()
        mock_agent.stock_api.is_holiday = Mock(return_value=False)

        # 첫 번째 호출
        check_market_status(mock_agent)
        call_count_1 = mock_agent.stock_api.is_holiday.call_count

        # 두 번째 호출 (캐시됨)
        check_market_status(mock_agent)
        call_count_2 = mock_agent.stock_api.is_holiday.call_count

        # 캐싱으로 인해 호출 횟수가 증가하지 않음
        assert call_count_1 == call_count_2

    def test_market_status_holiday_detection(self):
        """휴장일 감지 테스트."""
        mock_agent = Mock()
        mock_agent.stock_api = Mock()
        mock_agent.stock_api.is_holiday = Mock(return_value=True)

        with patch('kis_agent.cli_bridge._market_status', {
            "checked": False,
            "is_holiday": None,
            "last_business_day": None,
            "notice": None,
        }):
            check_market_status(mock_agent)

        # API가 호출되었음
        assert mock_agent.stock_api.is_holiday.called

    def test_market_status_api_failure_fallback(self):
        """API 실패 시 주말 체크 폴백 테스트."""
        mock_agent = Mock()
        mock_agent.stock_api = Mock()
        mock_agent.stock_api.is_holiday = Mock(side_effect=Exception("API Error"))

        with patch('kis_agent.cli_bridge._market_status', {
            "checked": False,
            "is_holiday": None,
            "last_business_day": None,
            "notice": None,
        }):
            # 예외가 발생하지 않아야 함
            try:
                check_market_status(mock_agent)
            except Exception as e:
                pytest.fail(f"check_market_status should not raise exception: {e}")


class TestLoadEnv:
    """load_env 함수 테스트."""

    def test_load_env_success(self):
        """환경변수 로드 성공 테스트."""
        with patch('dotenv.load_dotenv') as mock_load:
            with patch('os.path.exists', return_value=True):
                load_env()
                # load_dotenv가 최소 한 번 호출되어야 함
                assert mock_load.called

    def test_load_env_no_files(self):
        """환경파일이 없는 경우 테스트."""
        with patch('dotenv.load_dotenv') as mock_load:
            with patch('os.path.exists', return_value=False):
                load_env()
                # 파일이 없으면 load_dotenv가 호출되지 않음
                assert not mock_load.called


class TestCreateAgent:
    """create_agent 함수 테스트."""

    @patch('kis_agent.cli_bridge.load_env')
    def test_create_agent_with_env_vars(self, mock_load_env):
        """환경변수를 사용한 Agent 생성 테스트."""
        import os

        with patch('kis_agent.Agent') as mock_agent_class:
            with patch.dict(os.environ, {
                'KIS_APP_KEY': 'test_key',
                'KIS_APP_SECRET': 'test_secret',
                'KIS_ACCOUNT_NO': '12345678',
                'KIS_ACCOUNT_CODE': '01',
                'KIS_BASE_URL': 'https://test.example.com'
            }):
                create_agent()

                mock_agent_class.assert_called_once()
                call_kwargs = mock_agent_class.call_args[1]
                assert call_kwargs['app_key'] == 'test_key'
                assert call_kwargs['app_secret'] == 'test_secret'
                assert call_kwargs['account_no'] == '12345678'

    @patch('kis_agent.cli_bridge.load_env')
    def test_create_agent_with_default_values(self, mock_load_env):
        """기본값을 사용한 Agent 생성 테스트."""
        import os

        with patch('kis_agent.Agent') as mock_agent_class:
            with patch.dict(os.environ, {}, clear=True):
                create_agent()

                mock_agent_class.assert_called_once()
                call_kwargs = mock_agent_class.call_args[1]
                # 기본값 확인
                assert call_kwargs['app_key'] == ''
                assert call_kwargs['app_secret'] == ''
                assert call_kwargs['account_code'] == '01'
                assert 'koreainvestment.com' in call_kwargs['base_url']


class TestJSONRoundTrip:
    """JSON 직렬화/역직렬화 테스트."""

    def test_complex_data_serialization(self, capsys):
        """복잡한 데이터 구조 직렬화 테스트."""
        data = {
            "success": True,
            "data": {
                "stocks": [
                    {"code": "005930", "price": 70000, "change": 1.5},
                    {"code": "000660", "price": 35000, "change": -0.5},
                ],
                "timestamp": None,  # None 값 처리
                "float_value": 1234.567,
            }
        }

        with patch('kis_agent.cli_bridge._market_status', {"notice": None}):
            output_json(data, pretty=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["data"]["stocks"][0]["price"] == 70000
        assert result["data"]["float_value"] == 1234.567
        assert result["data"]["timestamp"] is None


class TestErrorHandling:
    """에러 처리 테스트."""

    def test_attribute_error_response(self):
        """AttributeError 응답 테스트."""
        mock_agent = Mock(spec=[])  # spec=[]로 모든 속성 없음

        request = {"method": "nonexistent.method", "params": {}}
        response = handle_request(json.dumps(request), mock_agent)

        result = json.loads(response)
        assert result["success"] is False
        assert "AttributeError" in result["code"]

    def test_type_error_response(self):
        """TypeError 응답 테스트."""
        mock_api = Mock()
        mock_api.not_callable = "string"

        mock_agent = Mock()
        mock_agent.test_domain = mock_api

        request = {"method": "test_domain.not_callable", "params": {}}
        response = handle_request(json.dumps(request), mock_agent)

        result = json.loads(response)
        assert result["success"] is False
        assert "TypeError" in result["code"]

    def test_generic_exception_response(self):
        """일반 예외 응답 테스트."""
        mock_agent = Mock()
        mock_agent.test_api = Mock()
        mock_agent.test_api.method = Mock(side_effect=RuntimeError("Unexpected error"))

        request = {"method": "test_api.method", "params": {}}
        response = handle_request(json.dumps(request), mock_agent)

        result = json.loads(response)
        assert result["success"] is False
        assert result["code"] == "RuntimeError"
        assert "Unexpected error" in result["error"]


class TestTimeoutHandling:
    """타임아웃 처리 테스트."""

    def test_timeout_error_response(self):
        """타임아웃 에러 응답 테스트."""
        import time

        mock_agent = Mock()
        mock_agent.test_api = Mock()

        def slow_method():
            time.sleep(5)  # 5초 대기
            return "result"

        mock_agent.test_api.method = Mock(side_effect=slow_method)

        request = {"method": "test_api.method", "params": {}, "timeout": 100}
        response = handle_request(json.dumps(request), mock_agent, timeout=100)

        # 타임아웃이 발생해야 함
        result = json.loads(response)
        assert result["success"] is False
        assert result["code"] == "TimeoutError"
        assert "timed out" in result["error"].lower()

    def test_timeout_parameter_in_request(self):
        """요청의 타임아웃 파라미터(ms) 테스트."""
        mock_agent = Mock()
        mock_agent.test_api = Mock()
        mock_agent.test_api.method = Mock(return_value="success")

        request = {"method": "test_api.method", "params": {}, "timeout": 5000}

        with patch('kis_agent.cli_bridge.output_json'):
            response = handle_request(json.dumps(request), mock_agent, timeout=10000)
            # 요청에 timeout 파라미터가 있으면 그것을 사용해야 함
            assert response == ""  # output_json에서 처리됨

    def test_default_timeout_value(self):
        """기본 타임아웃 값 30000ms 테스트."""
        mock_agent = Mock()
        mock_agent.test_api = Mock()
        mock_agent.test_api.method = Mock(return_value="success")

        request = {"method": "test_api.method", "params": {}}

        with patch('kis_agent.cli_bridge.output_json'):
            # 기본 30000ms 타임아웃으로 실행됨
            response = handle_request(json.dumps(request), mock_agent)
            assert response == ""

    def test_invalid_timeout_validation(self):
        """유효하지 않은 timeout은 ValidationError를 반환."""
        mock_agent = Mock()
        request = {"method": "test_api.method", "timeout": 0}

        response = handle_request(json.dumps(request), mock_agent)
        result = json.loads(response)

        assert result["success"] is False
        assert result["code"] == "ValidationError"


class TestLineBasedProtocol:
    """라인 기반 프로토콜 보장 테스트."""

    def test_pretty_request_still_returns_single_line_json(self, capsys):
        """pretty=True 요청도 응답은 한 줄 JSON이어야 함."""
        mock_agent = Mock()
        mock_agent.test_api = Mock()
        mock_agent.test_api.method = Mock(return_value={"price": 10000})

        request = {"method": "test_api.method", "pretty": True}

        with patch('kis_agent.cli_bridge._market_status', {"notice": None}):
            response = handle_request(json.dumps(request), mock_agent)

        assert response == ""
        captured = capsys.readouterr()
        assert captured.out.count("\n") == 1
        assert json.loads(captured.out) == {"success": True, "data": {"price": 10000}}
