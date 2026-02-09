"""
계좌 관련 데이터 모델 정의

주문체결 조회 등 계좌 관련 API 응답 데이터 구조를 정의합니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class OrderExecutionItem:
    """주문체결 항목 데이터 모델"""

    # 기본 정보
    ord_dt: str  # 주문일자 (YYYYMMDD)
    ord_gno_brno: str  # 주문채번지점번호
    odno: str  # 주문번호
    orgn_odno: str  # 원주문번호
    ord_dvsn_name: str  # 주문구분명

    # 매매 구분
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (01:매도, 02:매수)
    sll_buy_dvsn_cd_name: str  # 매도매수구분코드명

    # 종목 정보
    pdno: str  # 상품번호 (종목코드)
    prdt_name: str  # 상품명

    # 주문 정보
    ord_qty: str  # 주문수량
    ord_unpr: str  # 주문단가
    ord_tmd: str  # 주문시각 (HHMMSS)

    # 체결 정보
    tot_ccld_qty: str  # 총체결수량
    avg_prvs: str  # 평균가
    tot_ccld_amt: str  # 총체결금액
    cncl_yn: str  # 취소여부 (Y/N)

    # 추가 정보
    loan_dt: Optional[str] = None  # 대출일자
    ordr_empno: Optional[str] = None  # 주문자사번
    ord_dvsn_cd: Optional[str] = None  # 주문구분코드
    cnc_cfrm_qty: Optional[str] = None  # 취소확인수량
    rmn_qty: Optional[str] = None  # 잔여수량
    rjct_qty: Optional[str] = None  # 거부수량
    ccld_cndt_name: Optional[str] = None  # 체결조건명
    inqr_ip_addr: Optional[str] = None  # 조회IP주소
    cpbc_ordp_ord_rcit_dvsn_cd: Optional[str] = None  # 전산주문표주문접수구분코드
    cpbc_ordp_infm_mthd_dvsn_cd: Optional[str] = None  # 전산주문표통보방법구분코드
    infm_tmd: Optional[str] = None  # 통보시각
    ctac_tlno: Optional[str] = None  # 연락전화번호
    prdt_type_cd: Optional[str] = None  # 상품유형코드
    excg_dvsn_cd: Optional[str] = None  # 거래소구분코드
    cpbc_ordp_mtrl_dvsn_cd: Optional[str] = None  # 전산주문표자료구분코드
    ord_orgno: Optional[str] = None  # 주문조직번호
    rsvn_ord_end_dt: Optional[str] = None  # 예약주문종료일자
    excg_id_dvsn_cd: Optional[str] = None  # 거래소ID구분코드
    stpm_cndt_pric: Optional[str] = None  # 스톱지정가조건가격
    stpm_efct_occr_dtmd: Optional[str] = None  # 스톱지정가효력발생상세시각

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @property
    def is_buy(self) -> bool:
        """매수 여부"""
        return self.sll_buy_dvsn_cd == "02"

    @property
    def is_sell(self) -> bool:
        """매도 여부"""
        return self.sll_buy_dvsn_cd == "01"

    @property
    def is_executed(self) -> bool:
        """체결 완료 여부"""
        try:
            return int(self.tot_ccld_qty) > 0 and self.cncl_yn != "Y"
        except (ValueError, TypeError):
            return False

    @property
    def is_cancelled(self) -> bool:
        """취소 여부"""
        return self.cncl_yn == "Y"

    @property
    def execution_rate(self) -> float:
        """체결률 (%)"""
        try:
            ord_qty = float(self.ord_qty)
            ccld_qty = float(self.tot_ccld_qty)
            if ord_qty > 0:
                return (ccld_qty / ord_qty) * 100
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0  # 숫자 변환 실패 시 기본값 반환
        return 0.0

    def get_order_datetime(self) -> Optional[datetime]:
        """주문 일시를 datetime 객체로 반환"""
        try:
            dt_str = f"{self.ord_dt} {self.ord_tmd}"
            return datetime.strptime(dt_str, "%Y%m%d %H%M%S")
        except (ValueError, TypeError):
            return None


@dataclass
class OrderExecutionSummary:
    """주문체결 요약 정보"""

    tot_ord_qty: str  # 총주문수량
    tot_ccld_qty: str  # 총체결수량
    tot_ccld_amt: str  # 총체결금액
    prsm_tlex_smtl: str  # 추정제비용합계
    pchs_avg_pric: str  # 매입평균가격

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return self.__dict__.copy()

    @property
    def total_order_qty(self) -> int:
        """총주문수량 (정수)"""
        try:
            return int(self.tot_ord_qty)
        except (ValueError, TypeError):
            return 0

    @property
    def total_executed_qty(self) -> int:
        """총체결수량 (정수)"""
        try:
            return int(self.tot_ccld_qty)
        except (ValueError, TypeError):
            return 0

    @property
    def total_executed_amount(self) -> float:
        """총체결금액 (실수)"""
        try:
            return float(self.tot_ccld_amt)
        except (ValueError, TypeError):
            return 0.0

    @property
    def estimated_fees(self) -> float:
        """추정제비용합계 (실수)"""
        try:
            return float(self.prsm_tlex_smtl)
        except (ValueError, TypeError):
            return 0.0

    @property
    def average_price(self) -> float:
        """매입평균가격 (실수)"""
        try:
            return float(self.pchs_avg_pric)
        except (ValueError, TypeError):
            return 0.0


@dataclass
class OrderExecutionResponse:
    """주문체결조회 API 응답 데이터 모델"""

    rt_cd: str  # 성공 실패 여부
    msg_cd: str  # 응답코드
    msg1: str  # 응답메세지
    output1: List[OrderExecutionItem]  # 상세 데이터 리스트
    output2: Optional[OrderExecutionSummary] = None  # 요약 데이터
    ctx_area_fk100: Optional[str] = None  # 연속조회키 FK100
    ctx_area_nk100: Optional[str] = None  # 연속조회키 NK100

    @property
    def is_success(self) -> bool:
        """성공 여부"""
        return self.rt_cd == "0"

    @property
    def has_more_data(self) -> bool:
        """추가 데이터 존재 여부 (연속조회 가능)"""
        return bool(self.ctx_area_fk100 or self.ctx_area_nk100)

    @property
    def total_items(self) -> int:
        """조회된 항목 수"""
        return len(self.output1)

    def get_buy_orders(self) -> List[OrderExecutionItem]:
        """매수 주문만 필터링"""
        return [item for item in self.output1 if item.is_buy]

    def get_sell_orders(self) -> List[OrderExecutionItem]:
        """매도 주문만 필터링"""
        return [item for item in self.output1 if item.is_sell]

    def get_executed_orders(self) -> List[OrderExecutionItem]:
        """체결된 주문만 필터링"""
        return [item for item in self.output1 if item.is_executed]

    def get_cancelled_orders(self) -> List[OrderExecutionItem]:
        """취소된 주문만 필터링"""
        return [item for item in self.output1 if item.is_cancelled]

    def get_orders_by_stock(self, pdno: str) -> List[OrderExecutionItem]:
        """특정 종목의 주문만 필터링"""
        return [item for item in self.output1 if item.pdno == pdno]

    @classmethod
    def from_api_response(cls, response_dict: dict) -> "OrderExecutionResponse":
        """API 응답 딕셔너리로부터 객체 생성"""
        output1_data = response_dict.get("output1", [])
        output1_items = [OrderExecutionItem(**item) for item in output1_data]

        output2_data = response_dict.get("output2")
        output2_summary = (
            OrderExecutionSummary(**output2_data) if output2_data else None
        )

        return cls(
            rt_cd=response_dict.get("rt_cd", ""),
            msg_cd=response_dict.get("msg_cd", ""),
            msg1=response_dict.get("msg1", ""),
            output1=output1_items,
            output2=output2_summary,
            ctx_area_fk100=response_dict.get("CTX_AREA_FK100"),
            ctx_area_nk100=response_dict.get("CTX_AREA_NK100"),
        )
