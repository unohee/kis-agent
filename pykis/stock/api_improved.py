"""
개선된 StockAPI - 통합 예외 처리 시스템 적용 예시

DEPRECATION NOTICE:
- 이 파일의 `StockAPI`는 실험적/예시용 구현으로, 프로덕션 경로에서는 사용하지 않습니다.
- 공식 진입점은 `pykis.stock.StockAPI`(Facade)입니다. 테스트/문서 목적으로만 유지됩니다.
"""

from datetime import datetime
from typing import Any, Dict

import pandas as pd

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS, KISClient
from ..core.exceptions import (
    APIException,
    ExceptionHandler,
    ValidationException,
    ensure_not_none,
    ensure_type,
    handle_exceptions,
)


class StockAPI(BaseAPI, ExceptionHandler):
    """
    개선된 종목 단위 시세 조회 및 주문 클래스

    모든 예외는 traceback과 함께 로깅되고 raise됩니다.
    None 반환 대신 명시적인 예외를 발생시킵니다.
    """

    def __init__(self, client: KISClient, account: Dict):
        """
        Args:
            client: KIS 클라이언트 인스턴스
            account: 계좌 정보 {"CANO": "계좌번호", "ACNT_PRDT_CD": "상품코드"}

        Raises:
            ValidationException: client 또는 account가 잘못된 경우
        """
        # [DEPRECATION] 실험/예시용 구현 경고
        import warnings

        warnings.warn(
            "pykis.stock.api_improved.StockAPI 는 deprecated/experimental 입니다. pykis.stock.StockAPI(Facade)를 사용하세요.",
            DeprecationWarning,
            stacklevel=2,
        )

        # 입력 검증
        ensure_not_none(client, "client")
        ensure_not_none(account, "account")
        ensure_type(account, dict, "account")

        if "CANO" not in account or "ACNT_PRDT_CD" not in account:
            raise ValidationException("account는 CANO와 ACNT_PRDT_CD를 포함해야 합니다")

        BaseAPI.__init__(self, client)
        ExceptionHandler.__init__(self, "pykis.stock.StockAPI")

        self.account = account
        self.CANO = account["CANO"]
        self.ACNT_PRDT_CD = account["ACNT_PRDT_CD"]

    @handle_exceptions(context="API 요청 실행 (Dict 반환)", reraise_as=APIException)
    def _make_request_dict(
        self, endpoint: str, tr_id: str, params: dict, retries: int = 5
    ) -> Dict:
        """
        공통 요청 함수: 응답을 Dict으로 변환

        Raises:
            APIException: API 호출 실패 또는 응답 오류
        """
        response = self.client.make_request(
            endpoint=endpoint, tr_id=tr_id, params=params, retries=retries
        )

        # 응답 검증
        if not response:
            raise APIException(
                f"API 응답이 없습니다. endpoint={endpoint}, tr_id={tr_id}"
            )

        if response.get("rt_cd") != "0":
            error_msg = response.get("msg1", "알 수 없는 오류")
            error_code = response.get("rt_cd", "UNKNOWN")
            raise APIException(f"API 오류 발생: [{error_code}] {error_msg}")

        return response

    @handle_exceptions(
        context="API 요청 실행 (DataFrame 반환)", reraise_as=APIException
    )
    def _make_request_dataframe(
        self, endpoint: str, tr_id: str, params: dict, retries: int = 5
    ) -> pd.DataFrame:
        """
        공통 요청 함수: 응답을 DataFrame으로 변환

        Raises:
            APIException: API 호출 실패 또는 응답 오류
        """
        response = self._make_request_dict(endpoint, tr_id, params, retries)

        output = response.get("output", [])
        if isinstance(output, dict):
            return pd.DataFrame([output])
        elif isinstance(output, list):
            if not output:
                # 빈 리스트인 경우 빈 DataFrame 반환
                return pd.DataFrame()
            return pd.DataFrame(output)
        else:
            raise APIException(f"예상치 못한 output 타입: {type(output)}")

    @handle_exceptions(context="주식 현재가 조회", reraise_as=APIException)
    def get_stock_price(self, code: str) -> Dict:
        """
        주식 현재가 조회

        Args:
            code: 종목코드 (6자리)

        Returns:
            현재가 정보 딕셔너리

        Raises:
            ValidationException: 잘못된 종목코드
            APIException: API 호출 실패
        """
        # 종목코드 검증
        ensure_not_none(code, "종목코드")
        ensure_type(code, str, "종목코드")

        if len(code) != 6:
            raise ValidationException(f"종목코드는 6자리여야 합니다: {code}")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    @handle_exceptions(context="일별 시세 조회", reraise_as=APIException)
    def get_daily_price(
        self, code: str, period: str = "D", org_adj_prc: str = "1"
    ) -> Dict[str, Any]:
        """
        일별 시세 조회

        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미사용, 1: 수정주가 사용)

        Returns:
            일별 시세 정보 딕셔너리

        Raises:
            ValidationException: 잘못된 파라미터
            APIException: API 호출 실패
        """
        # 파라미터 검증
        ensure_not_none(code, "종목코드")
        ensure_type(code, str, "종목코드")

        if len(code) != 6:
            raise ValidationException(f"종목코드는 6자리여야 합니다: {code}")

        if period not in ["D", "W", "M", "Y"]:
            raise ValidationException(
                f"잘못된 기간구분: {period}. D, W, M, Y 중 하나여야 합니다."
            )

        if org_adj_prc not in ["0", "1"]:
            raise ValidationException(
                f"잘못된 수정주가구분: {org_adj_prc}. 0 또는 1이어야 합니다."
            )

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_ITEMCHARTPRICE"],
            tr_id="FHKST01010400",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_period_div_code": period,
                "fid_org_adj_prc": org_adj_prc,
            },
        )

    @handle_exceptions(context="주식 회원사 정보 조회")
    def get_stock_member(self, ticker: str, retries: int = 10) -> Dict:
        """
        주식 회원사 정보 조회

        Args:
            ticker: 종목코드
            retries: 재시도 횟수

        Returns:
            회원사 정보 딕셔너리

        Raises:
            ValidationException: 잘못된 종목코드
            APIException: 모든 재시도 실패 후 발생
        """
        ensure_not_none(ticker, "종목코드")
        ensure_type(ticker, str, "종목코드")

        last_exception = None

        for attempt in range(retries):
            try:
                response = self.client.make_request(
                    endpoint=API_ENDPOINTS["INQUIRE_MEMBER"],
                    tr_id="FHKST01010600",
                    params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker},
                    retries=1,  # 내부 재시도는 1회만
                )

                if response and response.get("rt_cd") == "0":
                    output = response.get("output", [])
                    if output:
                        response["output"] = output
                        return response
                    else:
                        # 데이터가 없는 경우
                        self._log_warning(f"회원사 정보가 없습니다: {ticker}")
                        return {"output": [], "rt_cd": "0", "msg1": "데이터 없음"}

            except Exception as e:
                last_exception = e
                self._log_warning(
                    f"주식 회원사 조회 실패 (시도 {attempt+1}/{retries}): {e}"
                )

                # 마지막 시도가 아니면 계속
                if attempt < retries - 1:
                    continue

        # 모든 재시도 실패 후 예외 발생
        if last_exception:
            raise APIException(
                f"{retries}회 재시도 후에도 회원사 정보 조회 실패: {ticker}"
            ) from last_exception
        else:
            raise APIException(f"회원사 정보 조회 실패: {ticker}")

    @handle_exceptions(context="외국인 순매수량 조회", reraise_as=APIException)
    def get_foreign_net_buy(self, code: str, date: str = None) -> tuple:
        """
        특정 날짜의 외국인 순매수량 조회

        Args:
            code: 종목코드
            date: 조회 날짜 (YYYYMMDD 형식, None이면 오늘)

        Returns:
            (순매수량, 상세정보Dict) 튜플

        Raises:
            ValidationException: 잘못된 입력
            APIException: API 호출 실패
        """
        ensure_not_none(code, "종목코드")
        ensure_type(code, str, "종목코드")

        if date and len(date) != 8:
            raise ValidationException(f"날짜는 YYYYMMDD 형식이어야 합니다: {date}")

        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        # API 호출
        response = self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_TRADE"],
            tr_id="FHKST01010900",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": date,
                "fid_input_date_2": date,
                "fid_period_div_code": "D",
                "fid_org_adj_prc": "0",
            },
        )

        output = response.get("output", [])
        if not output:
            return 0, {"date": date, "frgn_ntby_qty": 0, "message": "데이터 없음"}

        # 가장 최근 데이터 사용
        latest = output[0] if isinstance(output, list) else output

        frgn_ntby_qty = int(latest.get("frgn_ntby_qty", 0))

        details = {
            "date": latest.get("stck_bsop_date", date),
            "frgn_ntby_qty": frgn_ntby_qty,
            "frgn_ntby_tr_pbmn": int(latest.get("frgn_ntby_tr_pbmn", 0)),
            "frgn_hldn_qty": int(latest.get("frgn_hldn_qty", 0)),
            "frgn_hldn_rate": float(latest.get("frgn_hldn_rate", 0)),
        }

        return frgn_ntby_qty, details

    @handle_exceptions(context="국내 휴장일 조회", reraise_as=APIException)
    def get_holidays(self, year: str = None) -> pd.DataFrame:
        """
        국내 휴장일 정보 조회

        Args:
            year: 조회년도 (YYYY 형식, None이면 현재년도)

        Returns:
            휴장일 정보 DataFrame

        Raises:
            ValidationException: 잘못된 연도
            APIException: API 호출 실패
        """
        if year is None:
            year = str(datetime.now().year)

        if len(year) != 4 or not year.isdigit():
            raise ValidationException(f"연도는 YYYY 형식이어야 합니다: {year}")

        params = {"BASS_DT": f"{year}0101", "CTX_AREA_NK": "", "CTX_AREA_FK": ""}

        # DataFrame으로 반환
        return self._make_request_dataframe(
            endpoint=API_ENDPOINTS["INQUIRE_HOLIDAY"], tr_id="CTCA0903R", params=params
        )


# 사용 예시를 보여주는 헬퍼 함수
def example_usage():
    """
    새로운 예외 처리 시스템 사용 예시
    """
    from ..core.client import KISClient

    # 클라이언트 초기화
    client = KISClient()
    account = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    # StockAPI 인스턴스 생성
    stock_api = StockAPI(client, account)

    try:
        # 현재가 조회
        price_info = stock_api.get_stock_price("005930")
        print(f"삼성전자 현재가: {price_info}")

    except ValidationException as e:
        # 입력 검증 오류
        print(f"입력 오류: {e}")

    except APIException as e:
        # API 호출 오류 (전체 traceback이 로그에 기록됨)
        print(f"API 오류: {e}")

    except Exception as e:
        # 예상치 못한 오류 (전체 traceback이 로그에 기록됨)
        print(f"예상치 못한 오류: {e}")

    # 외국인 순매수 조회
    try:
        net_buy, details = stock_api.get_foreign_net_buy("005930")
        print(f"외국인 순매수: {net_buy}, 상세: {details}")

    except APIException as e:
        # 모든 예외는 traceback과 함께 로깅됨
        print(f"조회 실패: {e}")


__all__ = ["StockAPI", "example_usage"]
