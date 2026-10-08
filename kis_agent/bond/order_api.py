"""장내채권 주문/계좌 API

[장내채권] 주문/계좌 (domestic-bond/v1/trading/*). 주문은 POST, 재시도 없음,
캐시 없음(use_cache=False). 모의투자 미지원.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Union

from ..core.base_api import BaseAPI

_YN = ("Y", "N")
_ISIN = re.compile(r"^[A-Z0-9]{12}$")
_DATE = re.compile(r"^\d{8}$")
# ORD_SVR_DVSN_CD is documented as "Unique key(0)": always "0".
_ORD_SVR_DVSN_CD = "0"

# 정정취소구분코드 (RVSE_CNCL_DVSN_CD): "01: 정정, 02: 취소".
_AMEND_CANCEL = {"modify": "01", "cancel": "02"}

# 주문구분 (sell ORD_DVSN): 01 종목별, 02 일자별, 03 체결가별.
_SELL_ORD_DVSN = ("01", "02", "03")

PriceLike = Union[int, float, str, Decimal]


def _bond_code(code: Any) -> str:
    """Validate a 12-character bond code (ISIN, e.g. KR6095572D81)."""
    text = code.strip().upper() if isinstance(code, str) else ""
    if not _ISIN.match(text):
        raise ValueError(f"채권 종목코드는 12자리 영숫자여야 합니다: {code!r}")
    return text


def _quantity(quantity: Any) -> str:
    """Validate a positive integer order quantity and return it as a string."""
    if isinstance(quantity, bool) or not isinstance(quantity, (int, str)):
        raise ValueError(f"주문수량은 양의 정수여야 합니다: {quantity!r}")
    text = str(quantity).strip()
    if not text.isdigit() or int(text) <= 0:
        raise ValueError(f"주문수량은 양의 정수여야 합니다: {quantity!r}")
    return str(int(text))


def _price(price: Any) -> str:
    """Validate a positive finite bond unit price and return it as a string."""
    if isinstance(price, bool) or not isinstance(price, (int, float, str, Decimal)):
        raise ValueError(f"주문단가는 0보다 큰 숫자여야 합니다: {price!r}")
    try:
        value = Decimal(str(price).strip())
    except InvalidOperation:
        raise ValueError(f"주문단가는 0보다 큰 숫자여야 합니다: {price!r}") from None
    if not value.is_finite() or value <= 0:
        raise ValueError(f"주문단가는 0보다 큰 숫자여야 합니다: {price!r}")
    return format(value, "f")


def _yn(value: Any, name: str) -> str:
    if value not in _YN:
        raise ValueError(f"{name}는 'Y' 또는 'N'이어야 합니다: {value!r}")
    return value


class BondOrderAPI(BaseAPI):
    """장내채권 주문/계좌"""

    # ------------------------------------------------------------------ orders

    def buy_bond(
        self,
        code: str,
        quantity: int,
        price: PriceLike,
        samt_mket_ptci_yn: str = "N",
        bond_rtl_mket_yn: str = "N",
        contact_phone: str = "",
    ) -> Optional[Dict[str, Any]]:
        """장내채권 매수주문 [국내주식-124]

        실전투자 전용(모의투자 미지원). POST 주문이며 재시도·캐시를 하지 않는다.
        전송 전에 인자를 검증하고, 잘못되면 요청 없이 ValueError를 낸다.

        Args:
            code: 채권종목코드 (12자리, 예: "KR6095572D81")
            quantity: 주문수량 (양의 정수, ORD_QTY2)
            price: 주문단가 (0보다 큰 값, BOND_ORD_UNPR)
            samt_mket_ptci_yn: 소액시장참여여부 ("N": 일반시장, "Y": 소액시장). 기본 "N"
            bond_rtl_mket_yn: 채권소매시장여부 ("Y"/"N"). 기본 "N"
            contact_phone: 연락전화번호 (CTAC_TLNO, 선택)
        Returns:
            output: 주문 접수 결과 (주문번호 odno, 주문시각 ord_tmd 등)
        Raises:
            ValueError: 종목코드/수량/단가/Y,N 인자가 잘못된 경우 (요청 미전송)
        Example:
            >>> agent.bond.buy_bond("KR6095572D81", 10, 10460)
        """
        params = {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "PDNO": _bond_code(code),
            "ORD_QTY2": _quantity(quantity),
            "BOND_ORD_UNPR": _price(price),
            "SAMT_MKET_PTCI_YN": _yn(samt_mket_ptci_yn, "samt_mket_ptci_yn"),
            "BOND_RTL_MKET_YN": _yn(bond_rtl_mket_yn, "bond_rtl_mket_yn"),
            "IDCR_STFNO": "",
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": _ORD_SVR_DVSN_CD,
            "CTAC_TLNO": str(contact_phone),
        }
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/trading/buy",
            tr_id="TTTC0952U",
            params=params,
            method="POST",
            use_cache=False,
        )

    def sell_bond(
        self,
        code: str,
        quantity: int,
        price: PriceLike,
        ord_dvsn: str = "01",
        buy_date: str = "",
        buy_seq: str = "",
        sprx_yn: str = "N",
        samt_mket_ptci_yn: str = "N",
        bond_rtl_mket_yn: str = "N",
        contact_phone: str = "",
    ) -> Optional[Dict[str, Any]]:
        """장내채권 매도주문 [국내주식-123]

        실전투자 전용(모의투자 미지원). POST 주문이며 재시도·캐시를 하지 않는다.
        매도대행사반대매도여부(SLL_AGCO_OPPS_SLL_YN)는 항상 "N"으로 보낸다.

        Args:
            code: 채권종목코드 (12자리)
            quantity: 주문수량 (양의 정수)
            price: 주문단가 (0보다 큰 값)
            ord_dvsn: 주문구분. "01" 종목별(buy_date·buy_seq 공백), "02" 일자별
                (buy_date 필요, buy_seq는 "0"), "03" 체결가별(buy_date·buy_seq 필요).
                매수일자/순번은 잔고조회(get_bond_balance) 결과를 참조한다.
            buy_date: 매수일자 YYYYMMDD ("02"/"03" 에서 필수)
            buy_seq: 매수순번 ("03" 에서 필수, "02" 는 비우면 "0")
            sprx_yn: 분리과세여부 ("N": 종합과세, "Y": 분리과세). 기본 "N"
            samt_mket_ptci_yn: 소액시장참여여부 ("N": 일반시장, "Y": 소액시장). 기본 "N"
            bond_rtl_mket_yn: 채권소매시장여부 ("Y"/"N"). 기본 "N"
            contact_phone: 연락전화번호 (CTAC_TLNO, 선택)
        Returns:
            output: 주문 접수 결과 (주문번호 odno, 주문시각 ord_tmd 등)
        Raises:
            ValueError: 인자가 잘못되거나 ord_dvsn과 매수일자/순번이 맞지 않는 경우 (요청 미전송)
        Example:
            >>> agent.bond.sell_bond("KR6095572D81", 1, 10000.0)
        """
        if ord_dvsn not in _SELL_ORD_DVSN:
            raise ValueError(
                f"ord_dvsn은 '01'/'02'/'03' 중 하나여야 합니다: {ord_dvsn!r}"
            )
        buy_date = str(buy_date).strip()
        buy_seq = str(buy_seq).strip()
        if ord_dvsn == "01":
            if buy_date or buy_seq:
                raise ValueError(
                    "ord_dvsn '01'(종목별)은 buy_date·buy_seq를 비워야 합니다"
                )
        else:
            if not _DATE.match(buy_date):
                raise ValueError(f"buy_date는 YYYYMMDD여야 합니다: {buy_date!r}")
            if ord_dvsn == "02":
                if buy_seq not in ("", "0"):
                    raise ValueError(
                        "ord_dvsn '02'(일자별)는 buy_seq가 '0'이어야 합니다"
                    )
                buy_seq = "0"
            elif not buy_seq.isdigit():
                raise ValueError("ord_dvsn '03'(체결가별)은 숫자 buy_seq가 필요합니다")
        params = {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "ORD_DVSN": ord_dvsn,
            "PDNO": _bond_code(code),
            "ORD_QTY2": _quantity(quantity),
            "BOND_ORD_UNPR": _price(price),
            "SPRX_YN": _yn(sprx_yn, "sprx_yn"),
            "BUY_DT": buy_date,
            "BUY_SEQ": buy_seq,
            "SAMT_MKET_PTCI_YN": _yn(samt_mket_ptci_yn, "samt_mket_ptci_yn"),
            "SLL_AGCO_OPPS_SLL_YN": "N",
            "BOND_RTL_MKET_YN": _yn(bond_rtl_mket_yn, "bond_rtl_mket_yn"),
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": _ORD_SVR_DVSN_CD,
            "CTAC_TLNO": str(contact_phone),
        }
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/trading/sell",
            tr_id="TTTC0958U",
            params=params,
            method="POST",
            use_cache=False,
        )

    def modify_cancel_bond_order(
        self,
        action: str,
        code: str,
        orgn_odno: str,
        quantity: Optional[int] = None,
        price: Optional[PriceLike] = None,
        all_remaining: bool = False,
        contact_phone: str = "",
    ) -> Optional[Dict[str, Any]]:
        """장내채권 정정취소주문 [국내주식-125]

        실전투자 전용(모의투자 미지원). POST 주문이며 재시도·캐시를 하지 않는다.
        ``action``이 정정취소구분코드(RVSE_CNCL_DVSN_CD)를 결정한다.

        Args:
            action: "modify"(정정, 01) 또는 "cancel"(취소, 02). 기본값 없음.
            code: 채권종목코드 (12자리)
            orgn_odno: 원주문번호
            quantity: 주문수량. ``all_remaining=True`` 이면 지정하지 않는다
                (잔량전부, QTY_ALL_ORD_YN="Y", ORD_QTY2="0" 전송).
            price: 정정 주문단가 (정정 시 필수). 취소 시에는 무시되어 "0"으로 전송.
            all_remaining: 잔량 전부 정정/취소 여부
            contact_phone: 연락전화번호 (CTAC_TLNO, 선택)
        Returns:
            output: 정정/취소 접수 결과 (주문번호 odno 등)
        Raises:
            ValueError: 인자가 잘못된 경우 (요청 미전송)
        Example:
            >>> agent.bond.modify_cancel_bond_order("modify", "KR6095572D81", "0000015402", 2, 10460)
            >>> agent.bond.modify_cancel_bond_order("cancel", "KR6095572D81", "0000015402", all_remaining=True)
        """
        if action not in _AMEND_CANCEL:
            raise ValueError(
                f"action은 'modify' 또는 'cancel'이어야 합니다: {action!r}"
            )
        order_no = str(orgn_odno).strip() if orgn_odno is not None else ""
        if not order_no:
            raise ValueError("원주문번호(orgn_odno)가 필요합니다")
        if not isinstance(all_remaining, bool):
            raise ValueError(f"all_remaining은 bool이어야 합니다: {all_remaining!r}")
        if all_remaining:
            if quantity is not None:
                raise ValueError(
                    "all_remaining=True 이면 quantity를 지정할 수 없습니다"
                )
            qty = "0"
        else:
            if quantity is None:
                raise ValueError(
                    "quantity를 지정하거나 all_remaining=True 를 사용하세요"
                )
            qty = _quantity(quantity)
        if action == "modify":
            if price is None:
                raise ValueError("정정에는 price가 필요합니다")
            unit_price = _price(price)
        else:
            unit_price = "0"
        params = {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "PDNO": _bond_code(code),
            "ORGN_ODNO": order_no,
            "ORD_QTY2": qty,
            "BOND_ORD_UNPR": unit_price,
            "QTY_ALL_ORD_YN": "Y" if all_remaining else "N",
            "RVSE_CNCL_DVSN_CD": _AMEND_CANCEL[action],
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": _ORD_SVR_DVSN_CD,
            "CTAC_TLNO": str(contact_phone),
        }
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/trading/order-rvsecncl",
            tr_id="TTTC0953U",
            params=params,
            method="POST",
            use_cache=False,
        )

    # ----------------------------------------------------------------- queries

    def get_bond_psbl_rvsecncl(
        self,
        ord_dt: Optional[str] = None,
        odno: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """채권정정취소가능주문조회 [국내주식-126]

        정정/취소할 수 있는 미체결 채권 주문 목록을 조회한다. 연속조회는
        ``max_pages``까지 이어 붙인다.

        Args:
            ord_dt: 주문일자 YYYYMMDD (기본: 오늘)
            odno: 주문번호 (공백: 전체)
            max_pages: 최대 페이지 수
        Returns:
            output: list of 정정취소 가능 주문 (주문번호, 종목, 수량, 단가 등)
        Example:
            >>> agent.bond.get_bond_psbl_rvsecncl()
        """
        return self._paginate(
            "/uapi/domestic-bond/v1/trading/inquire-psbl-rvsecncl",
            "CTSC8035R",
            {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "ORD_DT": ord_dt or datetime.now().strftime("%Y%m%d"),
                "ODNO": odno,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
            cursor=[
                ("CTX_AREA_FK200", "ctx_area_fk200"),
                ("CTX_AREA_NK200", "ctx_area_nk200"),
            ],
            output_keys=("output",),
            max_pages=max_pages,
        )

    def get_bond_daily_ccld(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sll_buy_dvsn_cd: str = "%",
        sort_sqn_dvsn: str = "01",
        code: str = "",
        nccs_yn: str = "N",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """장내채권 주문체결내역 [국내주식-127]

        기간별 채권 주문/체결 내역을 조회한다. 조회 가능 기간은 1주일 이내이다.

        Args:
            start_date: 조회시작일자 YYYYMMDD (기본: 오늘)
            end_date: 조회종료일자 YYYYMMDD (기본: 오늘)
            sll_buy_dvsn_cd: 매도매수구분 ("%" 전체, "01" 매도, "02" 매수)
            sort_sqn_dvsn: 정렬순서 ("01" 주문순서, "02" 주문역순)
            code: 상품번호 (공백: 전체)
            nccs_yn: 미체결여부 ("N" 전체, "C" 체결, "Y" 미체결)
            max_pages: 최대 페이지 수
        Returns:
            output1: 합계 정보, output2: list of 주문/체결 내역
        Example:
            >>> agent.bond.get_bond_daily_ccld(nccs_yn="Y")
        """
        today = datetime.now().strftime("%Y%m%d")
        return self._paginate(
            "/uapi/domestic-bond/v1/trading/inquire-daily-ccld",
            "CTSC8013R",
            {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "INQR_STRT_DT": start_date or today,
                "INQR_END_DT": end_date or today,
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "SORT_SQN_DVSN": sort_sqn_dvsn,
                "PDNO": code,
                "NCCS_YN": nccs_yn,
                "CTX_AREA_NK200": "",
                "CTX_AREA_FK200": "",
            },
            cursor=[
                ("CTX_AREA_NK200", "ctx_area_nk200"),
                ("CTX_AREA_FK200", "ctx_area_fk200"),
            ],
            output_keys=("output1", "output2"),
            max_pages=max_pages,
        )

    def get_bond_balance(
        self,
        inqr_cndt: str = "00",
        code: str = "",
        buy_date: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """장내채권 잔고조회 [국내주식-198]

        보유 채권 잔고를 조회한다. 매도 주문(sell_bond)의 매수일자/순번은 이 결과를 참조한다.

        Args:
            inqr_cndt: 조회조건 ("00" 전체, "01" 상품번호단위)
            code: 상품번호 (공백 허용)
            buy_date: 매수일자 YYYYMMDD (공백 허용)
            max_pages: 최대 페이지 수
        Returns:
            output: list of 보유 잔고 (종목, 매수일자, 순번, 수량 등)
        Example:
            >>> agent.bond.get_bond_balance()
        """
        return self._paginate(
            "/uapi/domestic-bond/v1/trading/inquire-balance",
            "CTSC8407R",
            {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "INQR_CNDT": inqr_cndt,
                "PDNO": code,
                "BUY_DT": buy_date,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
            cursor=[
                ("CTX_AREA_FK200", "ctx_area_fk200"),
                ("CTX_AREA_NK200", "ctx_area_nk200"),
            ],
            output_keys=("output",),
            max_pages=max_pages,
        )

    def get_bond_psbl_order(
        self, code: str, price: PriceLike
    ) -> Optional[Dict[str, Any]]:
        """장내채권 매수가능조회 [국내주식-199]

        지정 종목·단가로 매수 가능한 금액/수량을 조회한다.

        Args:
            code: 채권종목코드 (예: "KR2033022D33")
            price: 채권주문단가
        Returns:
            output: 매수가능금액/수량
        Example:
            >>> agent.bond.get_bond_psbl_order("KR2033022D33", 1000)
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/trading/inquire-psbl-order",
            tr_id="TTTC8910R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": code,
                "BOND_ORD_UNPR": str(price),
            },
            use_cache=False,
        )
