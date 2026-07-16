"""Real -> paper (mock) trading TR_ID mapping.

KIS OpenAPI serves paper trading from a separate host (``MOCK_BASE_URL``) and
requires *different* TR_IDs from the real-trading ones. Pointing ``base_url`` at
the paper host while still sending a real TR_ID makes the server reject the
request with ``모의투자 TR 이 아닙니다`` (HTTP 500, rt_cd 1).

The mapping below comes from the official spec workbook
``한국투자증권_오픈API_전체문서_20251212_030000.xlsx`` (KIS API portal):

- sheet ``API 목록`` columns ``실전 TR_ID`` / ``모의 TR_ID``
- per-API sheets, row 22 (``tr_id`` field description) for the per-country
  order TR_IDs that the summary sheet defers to the spec for

That workbook's 336 API rows break down as:

===================================  ====  ==================================
category                             rows  handling
===================================  ====  ==================================
``모의 TR_ID`` present                 43  mapped below
``모의 TR_ID`` = ``모의투자 미지원``    288  absent below -> raises
no TR_ID at all (OAuth/hashkey)         4  never routed through this module
``모의 TR_ID`` blank (ELW LP매매추이)     1  treated as unsupported (판정 불가)
===================================  ====  ==================================

Any TR_ID absent from ``REAL_TO_PAPER_TR`` is therefore treated as unsupported
on paper trading — a closed-world assumption that the workbook's exhaustive
enumeration justifies.

The workbook is too large to track in git, so ``scripts/extract_paper_tr_mapping.py``
regenerates this table from it and ``--check`` diffs the two;
``tests/unit/test_paper_trading.py`` runs that check when the workbook is present.
Re-run it after KIS publishes a new spec revision.

Cross-checked against the official sample repo (`open-trading-api`, commit
885dd4e, 2026-07-09). Every disagreement traced back to `legacy/`, which KIS no
longer keeps in sync; the workbook and the current samples agree with this table
throughout. Note when re-checking that `legacy/` (including its Postman
collections) is not evidence of the live paper contract:

- 미국 매도 ``TTTT1006U`` -> ``VTTT1001U``: the samples used to say
  ``VTTT1006U``, which exists in no other source. KIS corrected them to
  ``VTTT1001U`` in 885dd4e ("해외주식 주문 모의TR 업데이트"), matching the
  workbook and this table.
- 베트남 매도 ``TTTS0310U`` -> ``VTTS0310U``: ``legacy/Sample01/kis_ovrseastk.py:76``
  still says ``VTTS0311U`` — the TR its own line 60 gives 베트남 *매수*, i.e. a
  copy-paste error 885dd4e did not sweep up. The current samples
  (``examples_llm``, ``examples_user``) say ``VTTS0310U``.

Deliberately left unsupported, all claimed only by `legacy/` and absent from
both the workbook and the current samples:

- ``TTTS3018R`` 해외주식 미체결내역 — workbook: "※ 해외주식 미체결내역 API
  모의투자에서는 사용이 불가합니다". ``VTTS3018R`` appears in zero current
  samples; ``examples_llm/overseas_stock/inquire_nccs`` names no paper TR at all.
  Only ``legacy/`` and its Postman v1.6 collection ship it.
- ``JTCE1001U``/``JTCE1002U`` 선물옵션 야간 주문·정정취소 — workbook: "야간은
  모의투자 미제공". Zero hits in the current samples.
- Legacy (구) TR_IDs ``TTTC0801U``/``TTTC0802U``/``TTTC0803U``/``TTTC8001R``/
  ``CTSC9115R`` — zero hits in the current samples, and this codebase does not
  send them. KIS warns they may be blocked without notice.

If a paper account ever proves one of these live, add it here with that evidence.

The mapping is an explicit lookup table rather than a substitution rule. A rule
such as ``"V" + real[1:]`` would be wrong in three ways: it mangles the quote
TR_IDs that are identical on both environments, it invents non-existent TR_IDs
for the 288 unsupported APIs, and it breaks on ``TTTT1006U`` -> ``VTTT1001U``,
where the numeric part changes too.
"""

from typing import Dict, Set

__all__ = [
    "REAL_TO_PAPER_TR",
    "PaperTradingNotSupportedError",
    "resolve_tr_id",
    "is_paper_supported",
]


class PaperTradingNotSupportedError(Exception):
    """Raised when an API without a paper-trading TR_ID is called on paper trading.

    KIS does not serve most of its APIs on the paper-trading host. Failing here
    is deliberate: sending the real TR_ID would only earn a generic HTTP 500
    ``모의투자 TR 이 아닙니다`` from the server after a network round-trip.
    """

    def __init__(self, tr_id: str):
        self.tr_id = tr_id
        super().__init__(
            f"TR_ID '{tr_id}' 는 모의투자를 지원하지 않습니다 "
            f"(KIS 공식 문서 기준 모의투자 미지원 API). "
            f"실전투자로 호출하거나, 모의투자를 지원하는 다른 API를 사용하세요."
        )


# Quote/market-data TR_IDs that are identical on both environments. Listed
# explicitly so that they resolve to themselves instead of raising.
_IDENTICAL_TR: Set[str] = {
    # 국내주식 시세
    "FHKST01010100",  # 주식현재가 시세
    "FHKST01010200",  # 주식현재가 호가/예상체결
    "FHKST01010300",  # 주식현재가 체결
    "FHKST01010400",  # 주식현재가 일자별
    "FHKST01010600",  # 주식현재가 회원사
    "FHKST01010900",  # 주식현재가 투자자
    "FHKST03010100",  # 국내주식기간별시세(일/주/월/년)
    "FHKST03010200",  # 주식당일분봉조회
    "FHPST01060000",  # 주식현재가 당일시간대별체결
    "FHPST02310000",  # 주식현재가 시간외시간별체결
    "FHPST02320000",  # 주식현재가 시간외일자별주가
    "FHKEW15010000",  # ELW 현재가 시세
    "FHKUP03500100",  # 국내주식업종기간별시세(일/주/월/년)
    # 선물옵션 시세
    "FHMIF10000000",  # 선물옵션 시세
    "FHMIF10010000",  # 선물옵션 시세호가
    "FHKIF03020100",  # 선물옵션기간별시세(일/주/월/년)
    # 해외주식 시세
    "HHDFS00000300",  # 해외주식 현재체결가
    "HHDFS76240000",  # 해외주식 기간별시세
    "HHDFS76410000",  # 해외주식조건검색
    "FHKST03030100",  # 해외주식 종목/지수/환율기간별시세(일/주/월/년)
    # 실시간 시세 (웹소켓) — 체결통보와 달리 실전/모의 동일
    "H0STCNT0",  # 국내주식 실시간체결가 (KRX)
    "H0STASP0",  # 국내주식 실시간호가 (KRX)
}


REAL_TO_PAPER_TR: Dict[str, str] = {
    # === 국내주식 주문/계좌 ===
    "TTTC0011U": "VTTC0011U",  # 주식주문(현금) 매도
    "TTTC0012U": "VTTC0012U",  # 주식주문(현금) 매수
    "TTTC0013U": "VTTC0013U",  # 주식주문(정정취소)
    "TTTC0081R": "VTTC0081R",  # 주식일별주문체결조회 (3개월이내)
    "CTSC9215R": "VTSC9215R",  # 주식일별주문체결조회 (3개월이전)
    "TTTC8434R": "VTTC8434R",  # 주식잔고조회
    "TTTC8908R": "VTTC8908R",  # 매수가능조회
    # === 선물옵션 (주간 주문만 모의 지원, 야간은 미제공) ===
    "CTFO6118R": "VTFO6118R",  # 선물옵션 잔고현황
    "TTTO1101U": "VTTO1101U",  # 선물옵션 주문 (주간 매수/매도)
    "TTTO1103U": "VTTO1103U",  # 선물옵션 정정취소주문 (주간)
    "TTTO5105R": "VTTO5105R",  # 선물옵션 주문가능
    "TTTO5201R": "VTTO5201R",  # 선물옵션 주문체결내역조회
    # === 해외주식 계좌 ===
    "TTTS3012R": "VTTS3012R",  # 해외주식 잔고
    "TTTS3007R": "VTTS3007R",  # 해외주식 매수가능금액조회
    "TTTS3035R": "VTTS3035R",  # 해외주식 주문체결내역
    "CTRP6504R": "VTRP6504R",  # 해외주식 체결기준현재잔고
    # === 해외주식 주문 (미국) ===
    "TTTT1002U": "VTTT1002U",  # 미국 매수
    "TTTT1006U": "VTTT1001U",  # 미국 매도 — 번호까지 바뀌는 유일한 예외
    "TTTT1004U": "VTTT1004U",  # 미국 정정취소
    "TTTT3014U": "VTTT3014U",  # 미국 예약매수
    "TTTT3016U": "VTTT3016U",  # 미국 예약매도
    "TTTT3017U": "VTTT3017U",  # 미국 예약주문 취소접수
    # === 해외주식 주문 (아시아) ===
    "TTTS0308U": "VTTS0308U",  # 일본 매수
    "TTTS0307U": "VTTS0307U",  # 일본 매도
    "TTTS0202U": "VTTS0202U",  # 상해 매수
    "TTTS1005U": "VTTS1005U",  # 상해 매도
    "TTTS1002U": "VTTS1002U",  # 홍콩 매수
    "TTTS1001U": "VTTS1001U",  # 홍콩 매도
    "TTTS0305U": "VTTS0305U",  # 심천 매수
    "TTTS0304U": "VTTS0304U",  # 심천 매도
    "TTTS0311U": "VTTS0311U",  # 베트남 매수
    "TTTS0310U": "VTTS0310U",  # 베트남 매도
    "TTTS3013U": "VTTS3013U",  # 중국/홍콩/일본/베트남 예약주문
    # === 해외주식 정정취소 (아시아) ===
    "TTTS1003U": "VTTS1003U",  # 홍콩 정정취소
    "TTTS0309U": "VTTS0309U",  # 일본 정정취소
    "TTTS0302U": "VTTS0302U",  # 상해 취소
    "TTTS0306U": "VTTS0306U",  # 심천 취소
    "TTTS0312U": "VTTS0312U",  # 베트남 취소
    # === 실시간 체결통보 (웹소켓) — V 치환이 아니라 끝자리 0 -> 9 ===
    "H0STCNI0": "H0STCNI9",  # 국내주식 실시간체결통보
    "H0IFCNI0": "H0IFCNI9",  # 선물옵션 실시간체결통보
    "H0GSCNI0": "H0GSCNI9",  # 해외주식 실시간체결통보
}

# TR_IDs identical on both environments map to themselves.
REAL_TO_PAPER_TR.update({tr: tr for tr in _IDENTICAL_TR})


def is_paper_supported(tr_id: str) -> bool:
    """Return whether ``tr_id`` is available on paper trading."""
    return tr_id in REAL_TO_PAPER_TR


def resolve_tr_id(tr_id: str, is_real: bool) -> str:
    """Resolve ``tr_id`` for the target environment.

    Args:
        tr_id: The real-trading TR_ID a caller passed.
        is_real: ``True`` for real trading, ``False`` for paper trading.

    Returns:
        ``tr_id`` unchanged on real trading, or its paper-trading counterpart.

    Raises:
        PaperTradingNotSupportedError: On paper trading, when the API has no
            paper-trading TR_ID.
    """
    if is_real:
        return tr_id

    # Already a paper TR_ID (a caller resolved it itself) — pass through.
    if tr_id in REAL_TO_PAPER_TR.values():
        return tr_id

    try:
        return REAL_TO_PAPER_TR[tr_id]
    except KeyError:
        raise PaperTradingNotSupportedError(tr_id) from None
