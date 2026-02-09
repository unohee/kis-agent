"""
테스트 모듈: inquire_daily_ccld 메서드 단위 테스트

생성일: 2025-10-05
목적: AccountAPI.inquire_daily_ccld 메서드의 모든 주요 로직 검증
    - TR_ID 선택 로직 (3개월 기준)
    - 페이지네이션 기능
    - output2 필드 처리
    - 연속조회 종료 조건
의존성: pytest, unittest.mock
테스트 상태: 완료
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import MagicMock, call, patch

import pytest

from pykis.account.api import AccountAPI
from pykis.core.exceptions import APIException

# ==================== Fixtures ====================


@pytest.fixture
def mock_client():
    """KISClient 목 객체 생성 픽스처."""
    client = MagicMock()
    client.is_real = True
    return client


@pytest.fixture
def account_info():
    """테스트용 계좌 정보 픽스처."""
    return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


@pytest.fixture
def account_api(mock_client, account_info):
    """AccountAPI 인스턴스 생성 픽스처."""
    return AccountAPI(
        client=mock_client,
        account_info=account_info,
        enable_cache=False,  # 캐시 비활성화로 테스트 단순화
    )


@pytest.fixture
def sample_output1_data():
    """API 응답의 output1 샘플 데이터."""
    return [
        {
            "ord_dt": "20251002",
            "ord_gno_brno": "01",
            "odno": "0000001",
            "orgn_odno": "",
            "ord_dvsn_name": "지정가",
            "sll_buy_dvsn_cd": "02",
            "sll_buy_dvsn_cd_name": "매수",
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "ord_qty": "10",
            "ord_unpr": "70000",
            "ord_tmd": "093000",
            "tot_ccld_qty": "10",
            "avg_prvs": "70000",
            "tot_ccld_amt": "700000",
            "cncl_yn": "N",
            "loan_dt": "",
            "rmn_qty": "0",
            "rjct_qty": "0",
        }
    ]


@pytest.fixture
def sample_output2_data():
    """API 응답의 output2 샘플 데이터."""
    return {
        "tot_ord_qty": "10",
        "tot_ccld_qty": "10",
        "tot_ccld_amt": "700000",
        "prsm_tlex_smtl": "1400",  # 수수료+세금
        "pchs_avg_pric": "70000",
    }


# ==================== TR_ID 선택 로직 테스트 ====================


class TestTRIDSelection:
    """TR_ID 선택 로직 테스트 클래스.

    3개월 기준으로 CTSC9215R 또는 TTTC0081R을 선택하는 로직을 검증합니다.
    """

    def test_tr_id_for_date_older_than_3_months(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """3개월 이전 날짜 조회 시 CTSC9215R TR_ID 사용 검증.

        조회 시작일이 현재로부터 3개월 이전인 경우,
        CTSC9215R TR_ID가 사용되는지 확인합니다.
        """
        # 4개월 전 날짜
        four_months_ago = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        # Mock 응답 설정
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": sample_output1_data,
            "output2": sample_output2_data,
        }

        # 단일 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date=four_months_ago, end_date=one_month_ago, pagination=False
        )

        # TR_ID 확인
        assert account_api.client.make_request.called
        call_args = account_api.client.make_request.call_args
        assert call_args[1]["tr_id"] == "CTSC9215R"
        assert result is not None
        assert result["rt_cd"] == "0"

    def test_tr_id_for_date_within_3_months(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """3개월 이내 날짜 조회 시 TTTC0081R TR_ID 사용 검증.

        조회 시작일이 현재로부터 3개월 이내인 경우,
        TTTC0081R TR_ID가 사용되는지 확인합니다.
        """
        # 2개월 전 날짜
        two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        today = datetime.now().strftime("%Y%m%d")

        # Mock 응답 설정
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": sample_output1_data,
            "output2": sample_output2_data,
        }

        # 단일 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date=two_months_ago, end_date=today, pagination=False
        )

        # TR_ID 확인
        assert account_api.client.make_request.called
        call_args = account_api.client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0081R"
        assert result is not None
        assert result["rt_cd"] == "0"

    def test_tr_id_pagination_older_than_3_months(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션 모드에서도 3개월 이전 날짜는 CTSC9215R 사용 검증."""
        # 4개월 전 날짜
        four_months_ago = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        # Mock 응답 설정 (데이터 없음으로 즉시 종료)
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "조회된 데이터가 없습니다",
            "output1": [],
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date=four_months_ago, end_date=one_month_ago, pagination=True
        )

        # TR_ID 확인
        assert account_api.client.make_request.called
        call_args = account_api.client.make_request.call_args
        assert call_args[1]["tr_id"] == "CTSC9215R"

    def test_tr_id_pagination_within_3_months(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션 모드에서도 3개월 이내 날짜는 TTTC0081R 사용 검증."""
        # 2개월 전 날짜
        two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        today = datetime.now().strftime("%Y%m%d")

        # Mock 응답 설정 (데이터 없음으로 즉시 종료)
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "조회된 데이터가 없습니다",
            "output1": [],
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date=two_months_ago, end_date=today, pagination=True
        )

        # TR_ID 확인
        assert account_api.client.make_request.called
        call_args = account_api.client.make_request.call_args
        assert call_args[1]["tr_id"] == "TTTC0081R"


# ==================== 단일 조회 테스트 ====================


class TestSingleQuery:
    """단일 조회 (pagination=False) 기능 테스트 클래스."""

    def test_single_query_success(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """단일 조회 성공 시나리오 검증.

        pagination=False로 단일 조회 시 정상 응답을 반환하는지 확인합니다.
        """
        # Mock 응답 설정
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": sample_output1_data,
            "output2": sample_output2_data,
        }

        # 단일 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=False
        )

        # 결과 검증
        assert result is not None
        assert result["rt_cd"] == "0"
        assert "output1" in result
        assert len(result["output1"]) == 1
        assert result["output1"][0]["pdno"] == "005930"

    def test_single_query_with_filters(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """필터 옵션과 함께 단일 조회 검증.

        종목코드, 매수/매도 구분 등 필터가 올바르게 전달되는지 확인합니다.
        """
        # Mock 응답 설정
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": sample_output1_data,
            "output2": sample_output2_data,
        }

        # 필터와 함께 단일 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001",
            end_date="20251002",
            pdno="005930",
            ord_dvsn_cd="02",  # 매수만
            pagination=False,
        )

        # 파라미터 확인
        call_args = account_api.client.make_request.call_args
        params = call_args[1]["params"]
        assert params["PDNO"] == "005930"
        assert params["SLL_BUY_DVSN_CD"] == "02"
        assert result is not None


# ==================== 페이지네이션 테스트 ====================


class TestPagination:
    """페이지네이션 (pagination=True) 기능 테스트 클래스."""

    def test_pagination_single_page(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션: 단일 페이지 (100건 미만) 처리 검증.

        데이터가 100건 미만일 때 단일 페이지로 종료되는지 확인합니다.
        """
        # Mock 응답 설정 (단일 페이지, 데이터 < 100건)
        # 각 항목이 고유한 odno를 가지도록 생성
        output1_data = [
            {**sample_output1_data[0], "odno": f"000000{i:03d}"} for i in range(50)
        ]

        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": output1_data,
            "output2": sample_output2_data,
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 결과 검증
        assert result is not None
        assert result["rt_cd"] == "0"
        assert len(result["output1"]) == 50
        assert result["output2"]["page_count"] == 1
        assert result["output2"]["total_count"] == 50

        # API 호출 횟수 확인 (1회)
        assert account_api.client.make_request.call_count == 1

    def test_pagination_multiple_pages(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션: 다중 페이지 처리 검증.

        연속조회를 통해 여러 페이지를 가져오는지 확인합니다.
        """

        # Mock 응답 설정 (3페이지)
        def make_request_side_effect(*args, **kwargs):
            headers = kwargs.get("headers", {})
            params = kwargs.get("params", {})

            # 첫 번째 페이지
            if not headers.get("tr_cont"):
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            # 두 번째 페이지
            elif params["CTX_AREA_FK100"] == "KEY1":
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000001{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY2",
                    "ctx_area_nk100": "KEY2",
                }
            # 세 번째 페이지 (마지막)
            else:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000002{i}", "pdno": "005930"}
                        for i in range(50)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 결과 검증
        assert result is not None
        assert result["rt_cd"] == "0"
        assert result["output2"]["page_count"] == 3
        assert result["output2"]["total_count"] == 250  # 100 + 100 + 50

        # API 호출 횟수 확인 (3회)
        assert account_api.client.make_request.call_count == 3

    def test_pagination_tr_cont_header(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션: tr_cont 헤더 설정 검증.

        첫 페이지는 빈 문자열, 이후 페이지는 "N"이 설정되는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            headers = kwargs.get("headers", {})

            if call_count == 1:
                # 첫 번째 호출: tr_cont 없음
                assert "tr_cont" not in headers
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # 두 번째 이후 호출: tr_cont = "N"
                assert headers.get("tr_cont") == "N"
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000001{i}", "pdno": "005930"}
                        for i in range(50)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        assert result is not None
        assert call_count == 2

    def test_pagination_continuation_key_extraction(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션: 연속조회 키 추출 검증.

        ctx_area_fk100, ctx_area_nk100이 올바르게 추출되고 다음 요청에 전달되는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            params = kwargs.get("params", {})

            if call_count == 1:
                # 첫 번째 호출: 빈 연속조회 키
                assert params["CTX_AREA_FK100"] == ""
                assert params["CTX_AREA_NK100"] == ""
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "CONTINUATION_FK_KEY",
                    "ctx_area_nk100": "CONTINUATION_NK_KEY",
                }
            elif call_count == 2:
                # 두 번째 호출: 이전 응답의 연속조회 키 사용
                assert params["CTX_AREA_FK100"] == "CONTINUATION_FK_KEY"
                assert params["CTX_AREA_NK100"] == "CONTINUATION_NK_KEY"
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000001{i}", "pdno": "005930"}
                        for i in range(50)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        assert result is not None
        assert call_count == 2


# ==================== 페이지네이션 종료 조건 테스트 ====================


class TestPaginationTermination:
    """페이지네이션 종료 조건 테스트 클래스.

    연속조회가 적절히 종료되는 조건들을 검증합니다.
    """

    def test_termination_by_msg1(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션 종료: msg1 메시지 확인.

        msg1에 "계속"이 포함되지 않으면 종료되는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # msg1이 "계속"을 포함하지 않음 -> 종료
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",  # "계속" 없음
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000001{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY2",  # 키가 있어도
                    "ctx_area_nk100": "KEY2",  # msg1 우선
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 종료 확인
        assert result is not None
        assert call_count == 2
        assert result["output2"]["page_count"] == 2

    def test_termination_by_empty_keys(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션 종료: 빈 연속조회 키.

        ctx_area_fk100, ctx_area_nk100이 모두 비어있으면 종료되는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # 연속조회 키가 비어있음 -> 종료
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",  # "계속"이 있어도
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000001{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",  # 빈 키
                    "ctx_area_nk100": "",  # 빈 키
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 종료 확인
        assert result is not None
        assert call_count == 2
        assert result["output2"]["page_count"] == 2

    def test_termination_by_less_than_100_records(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션 종료: 100건 미만 레코드.

        한 페이지에 100건 미만의 데이터가 반환되면 종료되는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # 100건 미만 -> 종료
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",  # "계속"이 있어도
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000001{i}", "pdno": "005930"}
                        for i in range(75)
                    ],  # 75건
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY2",  # 키가 있어도
                    "ctx_area_nk100": "KEY2",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 종료 확인
        assert result is not None
        assert call_count == 2
        assert result["output2"]["page_count"] == 2
        assert result["output2"]["total_count"] == 175  # 100 + 75

    def test_termination_by_max_pages(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """페이지네이션 종료: 최대 페이지 수 제한.

        max_pages에 도달하면 종료되는지 확인합니다.
        """
        # 항상 계속 조회 가능한 응답 반환
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "조회가 계속됩니다",
            "output1": [
                {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                for i in range(100)
            ],
            "output2": sample_output2_data,
            "ctx_area_fk100": "KEY",
            "ctx_area_nk100": "KEY",
        }

        # 최대 3페이지로 제한
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True, max_pages=3
        )

        # 종료 확인
        assert result is not None
        assert account_api.client.make_request.call_count == 3
        assert result["output2"]["page_count"] == 3


# ==================== output2 필드 테스트 ====================


class TestOutput2Fields:
    """output2 필드 처리 테스트 클래스.

    페이지네이션 시 output2에 포함되어야 할 필드들을 검증합니다.
    """

    def test_output2_contains_prsm_tlex_smtl(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """output2에 prsm_tlex_smtl (추정제비용합계) 포함 검증.

        수수료+세금 정보가 output2에 포함되는지 확인합니다.
        """
        # Mock 응답 설정
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": sample_output1_data,
            "output2": {
                **sample_output2_data,
                "prsm_tlex_smtl": "2500",  # 수수료+세금
            },
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # output2 검증
        assert result is not None
        assert "output2" in result
        assert "prsm_tlex_smtl" in result["output2"]
        assert result["output2"]["prsm_tlex_smtl"] == "2500"

    def test_output2_contains_pchs_avg_pric(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """output2에 pchs_avg_pric (매입평균가격) 포함 검증.

        매입평균가격 정보가 output2에 포함되는지 확인합니다.
        """
        # Mock 응답 설정
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output1": sample_output1_data,
            "output2": {
                **sample_output2_data,
                "pchs_avg_pric": "72000",  # 매입평균가격
            },
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # output2 검증
        assert result is not None
        assert "output2" in result
        assert "pchs_avg_pric" in result["output2"]
        assert result["output2"]["pchs_avg_pric"] == "72000"

    def test_output2_page_count_and_total_count(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """output2에 page_count와 total_count 정확성 검증.

        페이지네이션 시 페이지 수와 전체 레코드 수가 정확한지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000000{i}",
                            "pdno": "005930",
                            "ord_qty": "10",
                            "tot_ccld_qty": "10",
                            "tot_ccld_amt": "700000",
                        }
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            elif call_count == 2:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000001{i}",
                            "pdno": "005930",
                            "ord_qty": "10",
                            "tot_ccld_qty": "10",
                            "tot_ccld_amt": "700000",
                        }
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY2",
                    "ctx_area_nk100": "KEY2",
                }
            else:
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000002{i}",
                            "pdno": "005930",
                            "ord_qty": "10",
                            "tot_ccld_qty": "10",
                            "tot_ccld_amt": "700000",
                        }
                        for i in range(50)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # output2 검증
        assert result is not None
        assert "output2" in result
        assert result["output2"]["page_count"] == 3
        assert result["output2"]["total_count"] == 250  # 100 + 100 + 50

    def test_output2_aggregated_values(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """output2의 집계 값 (tot_ord_qty, tot_ccld_qty, tot_ccld_amt) 정확성 검증.

        여러 페이지의 데이터가 정확히 집계되는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # 첫 번째 페이지: 100건으로 연속조회 트리거
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000000{i:03d}",
                            "pdno": "005930",
                            "ord_qty": "10",
                            "tot_ccld_qty": "10",
                            "tot_ccld_amt": "700000",
                            "ord_tmd": "090000",
                        }
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # 두 번째 페이지: 50건으로 종료
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000001{i:03d}",
                            "pdno": "005930",
                            "ord_qty": "5",
                            "tot_ccld_qty": "5",
                            "tot_ccld_amt": "350000",
                            "ord_tmd": "100000",
                        }
                        for i in range(50)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # output2 집계 값 검증
        assert result is not None
        assert "output2" in result
        # 100 * 10 + 50 * 5 = 1000 + 250 = 1250
        assert result["output2"]["tot_ord_qty"] == "1250"
        assert result["output2"]["tot_ccld_qty"] == "1250"
        # 100 * 700000 + 50 * 350000 = 70000000 + 17500000 = 87500000
        assert result["output2"]["tot_ccld_amt"] == "87500000.0"


# ==================== 에지 케이스 테스트 ====================


class TestEdgeCases:
    """에지 케이스 및 예외 상황 테스트 클래스."""

    def test_empty_output1(self, account_api):
        """빈 결과 (output1 = []) 처리 검증.

        조회 결과가 없을 때 적절한 응답을 반환하는지 확인합니다.
        """
        # Mock 응답 설정 (빈 결과)
        account_api.client.make_request.return_value = {
            "rt_cd": "0",
            "msg_cd": "NO_DATA",
            "msg1": "조회된 데이터가 없습니다",
            "output1": [],
            "ctx_area_fk100": "",
            "ctx_area_nk100": "",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 빈 결과 검증
        assert result is not None
        assert result["rt_cd"] == "0"
        assert result["msg_cd"] == "NO_DATA"
        assert len(result["output1"]) == 0
        assert result["output2"]["total_count"] == 0

    def test_api_error_first_page(self, account_api):
        """첫 페이지 조회 실패 처리 검증.

        첫 페이지 조회 시 API 오류가 발생하면 None을 반환하는지 확인합니다.
        """
        # Mock 응답 설정 (오류)
        account_api.client.make_request.return_value = {
            "rt_cd": "1",
            "msg_cd": "ERROR",
            "msg1": "시스템 오류",
        }

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # None 반환 검증
        assert result is None

    def test_api_error_subsequent_page(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """후속 페이지 조회 실패 처리 검증.

        연속조회 중 오류 발생 시 현재까지의 데이터를 반환하는지 확인합니다.
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # 첫 페이지 성공
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {"ord_dt": "20251001", "odno": f"000000{i}", "pdno": "005930"}
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # 두 번째 페이지 실패
                return {"rt_cd": "1", "msg_cd": "ERROR", "msg1": "시스템 오류"}

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 첫 페이지 데이터는 반환됨
        assert result is not None
        assert result["rt_cd"] == "0"
        assert result["output2"]["page_count"] == 1
        assert result["output2"]["total_count"] == 100

    def test_duplicate_removal(self, account_api, sample_output2_data):
        """중복 레코드 제거 검증.

        페이지네이션 시 중복된 레코드가 제거되는지 확인합니다.
        (ord_dt, odno, pdno 조합으로 중복 판단)
        """
        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # 첫 번째 페이지: 100건으로 연속조회 트리거
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000000{i:03d}",
                            "pdno": "005930",
                            "ord_tmd": "090000",
                        }
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "KEY1",
                    "ctx_area_nk100": "KEY1",
                }
            else:
                # 두 번째 페이지: 일부 중복 포함하여 50건
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        # 중복: 마지막 10건 (90~99)
                        *[
                            {
                                "ord_dt": "20251001",
                                "odno": f"000000{i:03d}",
                                "pdno": "005930",
                                "ord_tmd": "090000",
                            }
                            for i in range(90, 100)
                        ],
                        # 새 데이터: 40건
                        *[
                            {
                                "ord_dt": "20251001",
                                "odno": f"000001{i:03d}",
                                "pdno": "005930",
                                "ord_tmd": "100000",
                            }
                            for i in range(40)
                        ],
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=True
        )

        # 중복 제거 검증: 100 (첫 페이지) + 40 (두 번째 페이지 신규) = 140
        # 10개는 중복으로 제거됨
        assert result is not None
        assert result["output2"]["total_count"] == 140

        # 유니크한 odno 확인
        odno_set = {item["odno"] for item in result["output1"]}
        assert len(odno_set) == 140

    def test_callback_function(
        self, account_api, sample_output1_data, sample_output2_data
    ):
        """콜백 함수 호출 검증.

        페이지별로 콜백 함수가 올바른 인자와 함께 호출되는지 확인합니다.
        """
        callback_calls = []

        def test_callback(
            page_num: int, page_data: List[Dict[str, Any]], ctx_info: Dict[str, Any]
        ) -> None:
            callback_calls.append(
                {
                    "page_num": page_num,
                    "data_count": len(page_data),
                    "fk100": ctx_info["FK100"],
                    "nk100": ctx_info["NK100"],
                    "total_rows": ctx_info["total_rows"],
                }
            )

        call_count = 0

        def make_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # 첫 번째 페이지: 100건으로 연속조회 트리거
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "조회가 계속됩니다",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000000{i:03d}",
                            "pdno": "005930",
                            "ord_tmd": "090000",
                        }
                        for i in range(100)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "FIRST_KEY",
                    "ctx_area_nk100": "FIRST_KEY",
                }
            else:
                # 두 번째 페이지: 30건으로 종료
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESS",
                    "msg1": "정상처리",
                    "output1": [
                        {
                            "ord_dt": "20251001",
                            "odno": f"000001{i:03d}",
                            "pdno": "005930",
                            "ord_tmd": "100000",
                        }
                        for i in range(30)
                    ],
                    "output2": sample_output2_data,
                    "ctx_area_fk100": "",
                    "ctx_area_nk100": "",
                }

        account_api.client.make_request.side_effect = make_request_side_effect

        # 콜백과 함께 페이지네이션 조회 실행
        result = account_api.inquire_daily_ccld(
            start_date="20251001",
            end_date="20251002",
            pagination=True,
            page_callback=test_callback,
        )

        # 콜백 호출 검증
        assert len(callback_calls) == 2

        # 첫 번째 페이지 콜백
        assert callback_calls[0]["page_num"] == 1
        assert callback_calls[0]["data_count"] == 100
        assert callback_calls[0]["fk100"] == "FIRST_KEY"
        assert callback_calls[0]["nk100"] == "FIRST_KEY"
        assert callback_calls[0]["total_rows"] == 100

        # 두 번째 페이지 콜백
        assert callback_calls[1]["page_num"] == 2
        assert callback_calls[1]["data_count"] == 30
        assert callback_calls[1]["fk100"] == ""
        assert callback_calls[1]["nk100"] == ""
        assert callback_calls[1]["total_rows"] == 30

    def test_exception_handling(self, account_api):
        """예외 처리 검증.

        inquire_daily_ccld는 예외 발생 시 로깅 후 None을 리턴합니다.
        (기존 주석의 @api_method(reraise=True)는 실제 구현과 다름)
        """
        # Mock 예외 발생
        account_api.client.make_request.side_effect = Exception("네트워크 오류")

        # 단일 조회 실행 - 예외 발생 시 None 리턴 검증
        result = account_api.inquire_daily_ccld(
            start_date="20251001", end_date="20251002", pagination=False
        )
        assert result is None, "예외 발생 시 None을 리턴해야 합니다"
