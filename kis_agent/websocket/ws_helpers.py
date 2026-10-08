"""
WebSocket Helper Classes - 데이터 파싱 및 저장 헬퍼

ws_agent.py에서 분리된 헬퍼 클래스들:
- RealtimeDataParser: 실시간 데이터 파싱
- RealtimeDataStore: 실시간 데이터 저장소
- WSAgentWithStore: 저장소 포함 WebSocket Agent

Created: 2026-01-03
Purpose: LOC gate 준수를 위해 ws_agent.py에서 분리
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .ws_fields import FIELDS
from .ws_types import KEYLESS_TR_IDS, SubscriptionType


class RealtimeDataParser:
    """실시간 데이터 파싱 헬퍼 - 웹소켓 수신 데이터를 딕셔너리로 변환"""

    # 선물·옵션을 제외한 피드의 컬럼은 공식 문서 기준 ``ws_fields.FIELDS``가 정본이다.
    # 아래 이름들은 하위 호환용 별칭 (KRX 기준 레이아웃).
    STOCK_TRADE_FIELDS = list(FIELDS["H0STCNT0"])
    STOCK_ORDERBOOK_FIELDS = list(FIELDS["H0STASP0"])
    INDEX_FIELDS = list(FIELDS["H0UPCNT0"])
    PROGRAM_TRADE_FIELDS = list(FIELDS["H0STPGM0"])
    MEMBER_TRADE_FIELDS = list(FIELDS["H0STMBC0"])
    INDEX_EXPECTED_FIELDS = list(FIELDS["H0UPANC0"])
    STOCK_EXPECTED_FIELDS = list(FIELDS["H0UNANC0"])
    MARKET_OPERATION_NXT_FIELDS = list(FIELDS["H0NXMKO0"])
    PROGRAM_TRADE_NXT_FIELDS = list(FIELDS["H0NXPGM0"])

    # KRX 야간선물 체결 필드 (H0MFCNT0) [실시간-064]
    NIGHT_FUTURES_TRADE_FIELDS = [
        "futs_shrn_iscd",
        "bsop_hour",
        "futs_prdy_vrss",
        "prdy_vrss_sign",
        "futs_prdy_ctrt",
        "futs_prpr",
        "futs_oprc",
        "futs_hgpr",
        "futs_lwpr",
        "last_cnqn",
        "acml_vol",
        "acml_tr_pbmn",
        "hts_thpr",
        "mrkt_basis",
        "dprt",
        "nmsc_fctn_stpl_prc",
        "fmsc_fctn_stpl_prc",
        "spead_prc",
        "hts_otst_stpl_qty",
        "otst_stpl_qty_icdc",
        "oprc_hour",
        "oprc_vrss_prpr_sign",
        "oprc_vrss_nmix_prpr",
        "hgpr_hour",
        "hgpr_vrss_prpr_sign",
        "hgpr_vrss_nmix_prpr",
        "lwpr_hour",
        "lwpr_vrss_prpr_sign",
        "lwpr_vrss_nmix_prpr",
        "shnu_rate",
        "cttr",
        "esdg",
        "otst_stpl_rgbf_qty_icdc",
        "thpr_basis",
        "futs_askp1",
        "futs_bidp1",
        "askp_rsqn1",
        "bidp_rsqn1",
        "seln_cntg_csnu",
        "shnu_cntg_csnu",
        "ntby_cntg_csnu",
        "seln_cntg_smtn",
        "shnu_cntg_smtn",
        "total_askp_rsqn",
        "total_bidp_rsqn",
        "prdy_vol_vrss_acml_vol_rate",
        "dynm_mxpr",
        "dynm_llam",
        "dynm_prc_limt_yn",
    ]

    # KRX 야간선물 호가 필드 (H0MFASP0) [실시간-065]
    NIGHT_FUTURES_ORDERBOOK_FIELDS = [
        "futs_shrn_iscd",
        "bsop_hour",
        "futs_askp1",
        "futs_askp2",
        "futs_askp3",
        "futs_askp4",
        "futs_askp5",
        "futs_bidp1",
        "futs_bidp2",
        "futs_bidp3",
        "futs_bidp4",
        "futs_bidp5",
        "askp_csnu1",
        "askp_csnu2",
        "askp_csnu3",
        "askp_csnu4",
        "askp_csnu5",
        "bidp_csnu1",
        "bidp_csnu2",
        "bidp_csnu3",
        "bidp_csnu4",
        "bidp_csnu5",
        "askp_rsqn1",
        "askp_rsqn2",
        "askp_rsqn3",
        "askp_rsqn4",
        "askp_rsqn5",
        "bidp_rsqn1",
        "bidp_rsqn2",
        "bidp_rsqn3",
        "bidp_rsqn4",
        "bidp_rsqn5",
        "total_askp_csnu",
        "total_bidp_csnu",
        "total_askp_rsqn",
        "total_bidp_rsqn",
        "total_askp_rsqn_icdc",
        "total_bidp_rsqn_icdc",
    ]

    # KRX 야간옵션 체결 필드 (H0EUCNT0) [실시간-032]
    NIGHT_OPTION_TRADE_FIELDS = [
        "optn_shrn_iscd",
        "bsop_hour",
        "optn_prpr",
        "prdy_vrss_sign",
        "optn_prdy_vrss",
        "prdy_ctrt",
        "optn_oprc",
        "optn_hgpr",
        "optn_lwpr",
        "last_cnqn",
        "acml_vol",
        "acml_tr_pbmn",
        "hts_thpr",
        "hts_otst_stpl_qty",
        "otst_stpl_qty_icdc",
        "oprc_hour",
        "oprc_vrss_prpr_sign",
        "oprc_vrss_nmix_prpr",
        "hgpr_hour",
        "hgpr_vrss_prpr_sign",
        "hgpr_vrss_nmix_prpr",
        "lwpr_hour",
        "lwpr_vrss_prpr_sign",
        "lwpr_vrss_nmix_prpr",
        "shnu_rate",
        "prmm_val",
        "invl_val",
        "tmvl_val",
        "delta",
        "gama",
        "vega",
        "theta",
        "rho",
        "hts_ints_vltl",
        "esdg",
        "otst_stpl_rgbf_qty_icdc",
        "thpr_basis",
        "unas_hist_vltl",
        "cttr",
        "dprt",
        "mrkt_basis",
        "optn_askp1",
        "optn_bidp1",
        "askp_rsqn1",
        "bidp_rsqn1",
        "seln_cntg_csnu",
        "shnu_cntg_csnu",
        "ntby_cntg_csnu",
        "seln_cntg_smtn",
        "shnu_cntg_smtn",
        "total_askp_rsqn",
        "total_bidp_rsqn",
        "prdy_vol_vrss_acml_vol_rate",
        "dynm_mxpr",
        "dynm_prc_limt_yn",
        "dynm_llam",
    ]

    # KRX 야간옵션 호가 필드 (H0EUASP0) [실시간-033]
    NIGHT_OPTION_ORDERBOOK_FIELDS = [
        "optn_shrn_iscd",
        "bsop_hour",
        "optn_askp1",
        "optn_askp2",
        "optn_askp3",
        "optn_askp4",
        "optn_askp5",
        "optn_bidp1",
        "optn_bidp2",
        "optn_bidp3",
        "optn_bidp4",
        "optn_bidp5",
        "askp_csnu1",
        "askp_csnu2",
        "askp_csnu3",
        "askp_csnu4",
        "askp_csnu5",
        "bidp_csnu1",
        "bidp_csnu2",
        "bidp_csnu3",
        "bidp_csnu4",
        "bidp_csnu5",
        "askp_rsqn1",
        "askp_rsqn2",
        "askp_rsqn3",
        "askp_rsqn4",
        "askp_rsqn5",
        "bidp_rsqn1",
        "bidp_rsqn2",
        "bidp_rsqn3",
        "bidp_rsqn4",
        "bidp_rsqn5",
        "total_askp_csnu",
        "total_bidp_csnu",
        "total_askp_rsqn",
        "total_bidp_rsqn",
        "total_askp_rsqn_icdc",
        "total_bidp_rsqn_icdc",
    ]

    @classmethod
    def parse(cls, sub_type: SubscriptionType, values: List[str]) -> Dict[str, Any]:
        """실시간 데이터 파싱 - sub_type에 맞는 필드 매핑 적용"""
        ST = SubscriptionType

        field_map = {
            # KRX 야간선물/옵션 (선물·옵션은 공식 레이아웃 정비 범위 밖)
            ST.NIGHT_FUTURES_TRADE: cls.NIGHT_FUTURES_TRADE_FIELDS,
            ST.NIGHT_FUTURES_ASK_BID: cls.NIGHT_FUTURES_ORDERBOOK_FIELDS,
            ST.NIGHT_OPTION_TRADE: cls.NIGHT_OPTION_TRADE_FIELDS,
            ST.NIGHT_OPTION_ASK_BID: cls.NIGHT_OPTION_ORDERBOOK_FIELDS,
        }

        fields = FIELDS.get(sub_type.value) or field_map.get(sub_type)
        if not fields:
            return {f"field_{i}": v for i, v in enumerate(values)}

        result = {}
        for i, field_name in enumerate(fields):
            if i < len(values):
                result[field_name] = cls._convert_value(values[i], field_name)
        return result

    _STRING_SUFFIXES = (
        "_hour",
        "_time",
        "_date",
        "_dt",
        "_ymd",
        "_hms",
        "_id",
        "_code",
        "_iscd",
    )

    @classmethod
    def _convert_value(cls, value: str, field: str) -> Any:
        """필드 값 타입 변환 - 숫자 필드는 int/float로 변환"""
        if not value:
            return None

        numeric_keywords = [
            "prpr",
            "pric",
            "vol",
            "qty",
            "amt",
            "rsqn",
            "smtn",
            "csnu",
            "ctrt",
            "rate",
            "pbmn",
            "cnpr",
            "cnqn",
            "hgpr",
            "lwpr",
            "oprc",
            "vrss",
            "nmix",
            "icdc",
            # 선물/옵션 공통
            "askp",
            "bidp",
            "basis",
            "dprt",
            "esdg",
            "cttr",
            "stpl",
            # 옵션 그릭스/가치
            "delta",
            "gama",
            "vega",
            "theta",
            "rho",
            "prmm_val",
            "invl_val",
            "tmvl_val",
            "vltl",
            "spead",
            "mxpr",
            "llam",
            # ETF NAV / 장내채권 / ELW
            "nav",
            "ert",
            "ytm",
            "drtn",
            "cnvx",
            "unpr",
            # 해외주식 (HDFS*)
            "last",
            "open",
            "high",
            "low",
            "diff",
            "pbid",
            "pask",
            "vbid",
            "vask",
            "evol",
            "tvol",
            "tamt",
            "bvol",
            "avol",
            "bdvl",
            "advl",
            "dbid",
            "dask",
            "mamt",
            "strn",
        ]

        # 시각·일자·코드·ID는 숫자처럼 보여도 문자열이다 ("093015" 앞자리 0 보존).
        if field.endswith(cls._STRING_SUFFIXES):
            return value

        for keyword in numeric_keywords:
            if keyword in field:
                try:
                    return float(value) if "." in value else int(value)
                except ValueError:
                    return value
        return value

    @classmethod
    def parse_stock_trade(cls, values: List[str]) -> Dict[str, Any]:
        """국내주식 체결 데이터 파싱"""

        return cls.parse(SubscriptionType.STOCK_TRADE, values)

    @classmethod
    def parse_stock_orderbook(cls, values: List[str]) -> Dict[str, Any]:
        """국내주식 호가 데이터 파싱"""

        return cls.parse(SubscriptionType.STOCK_ASK_BID, values)

    @classmethod
    def parse_index(cls, values: List[str]) -> Dict[str, Any]:
        """지수 데이터 파싱"""

        return cls.parse(SubscriptionType.INDEX, values)

    @classmethod
    def parse_program_trade(cls, values: List[str]) -> Dict[str, Any]:
        """프로그램매매 데이터 파싱"""

        return cls.parse(SubscriptionType.PROGRAM_TRADE, values)

    @classmethod
    def parse_member_trade(cls, values: List[str]) -> Dict[str, Any]:
        """회원사 매매동향 데이터 파싱"""

        return cls.parse(SubscriptionType.MEMBER_TRADE, values)

    @classmethod
    def parse_stock_expected(cls, values: List[str]) -> Dict[str, Any]:
        """종목 예상체결 데이터 파싱"""

        return cls.parse(SubscriptionType.STOCK_EXPECTED, values)

    @classmethod
    def parse_index_expected(cls, values: List[str]) -> Dict[str, Any]:
        """지수 예상체결 데이터 파싱"""

        return cls.parse(SubscriptionType.INDEX_EXPECTED, values)

    @classmethod
    def parse_night_futures_trade(cls, values: List[str]) -> Dict[str, Any]:
        """야간선물 체결 데이터 파싱"""
        return cls.parse(SubscriptionType.NIGHT_FUTURES_TRADE, values)

    @classmethod
    def parse_night_futures_orderbook(cls, values: List[str]) -> Dict[str, Any]:
        """야간선물 호가 데이터 파싱"""
        return cls.parse(SubscriptionType.NIGHT_FUTURES_ASK_BID, values)

    @classmethod
    def parse_night_option_trade(cls, values: List[str]) -> Dict[str, Any]:
        """야간옵션 체결 데이터 파싱"""
        return cls.parse(SubscriptionType.NIGHT_OPTION_TRADE, values)

    @classmethod
    def parse_night_option_orderbook(cls, values: List[str]) -> Dict[str, Any]:
        """야간옵션 호가 데이터 파싱"""
        return cls.parse(SubscriptionType.NIGHT_OPTION_ASK_BID, values)


class RealtimeDataStore:
    """실시간 데이터 저장소 - 종목별/타입별 최신 데이터 저장"""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self._latest: Dict[str, Dict[Any, Dict[str, Any]]] = {}
        self._history: Dict[str, Dict[Any, List[Dict[str, Any]]]] = {}
        self._stats = {"total_updates": 0, "codes_tracked": 0, "last_update_time": None}

    def update(
        self, sub_type: Any, code: str, data: Dict[str, Any], keep_history: bool = False
    ) -> None:
        """데이터 업데이트"""
        now = datetime.now()
        data_with_timestamp = {**data, "_updated_at": now}

        if code not in self._latest:
            self._latest[code] = {}
            self._stats["codes_tracked"] += 1
        self._latest[code][sub_type] = data_with_timestamp

        if keep_history:
            if code not in self._history:
                self._history[code] = {}
            if sub_type not in self._history[code]:
                self._history[code][sub_type] = []
            self._history[code][sub_type].append(data_with_timestamp)
            if len(self._history[code][sub_type]) > self.max_history:
                self._history[code][sub_type].pop(0)

        self._stats["total_updates"] += 1
        self._stats["last_update_time"] = now

    def get(
        self, code: str, sub_type: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """최신 데이터 조회"""
        if code not in self._latest:
            return None
        if sub_type is None:
            return self._latest[code].copy()
        return self._latest[code].get(sub_type)

    def get_trade(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.STOCK_TRADE)

    def get_orderbook(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.STOCK_ASK_BID)

    def get_expected(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.STOCK_EXPECTED)

    def get_index(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.INDEX)

    def get_program_trade(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.PROGRAM_TRADE)

    def get_member_trade(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.MEMBER_TRADE)

    def get_night_futures_trade(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.NIGHT_FUTURES_TRADE)

    def get_night_futures_orderbook(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.NIGHT_FUTURES_ASK_BID)

    def get_night_option_trade(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.NIGHT_OPTION_TRADE)

    def get_night_option_orderbook(self, code: str) -> Optional[Dict[str, Any]]:
        return self.get(code, SubscriptionType.NIGHT_OPTION_ASK_BID)

    def get_history(
        self, code: str, sub_type: Any, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """히스토리 데이터 조회"""
        if code not in self._history or sub_type not in self._history[code]:
            return []
        history = self._history[code][sub_type]
        return list(reversed(history[-limit:])) if limit else list(reversed(history))

    def get_all_codes(self) -> List[str]:
        return list(self._latest.keys())

    def get_stats(self) -> Dict[str, Any]:
        return self._stats.copy()

    def clear(self, code: Optional[str] = None) -> None:
        if code:
            self._latest.pop(code, None)
            self._history.pop(code, None)
        else:
            self._latest.clear()
            self._history.clear()
            self._stats["codes_tracked"] = 0


class WSAgentWithStore:
    """데이터 저장소가 포함된 WebSocket Agent - WSAgent 상속"""

    def __init__(
        self,
        approval_key: str,
        keep_history: bool = False,
        max_history: int = 100,
        **kwargs,
    ):
        # Lazy import to avoid circular dependency
        from .ws_agent import WSAgent

        # Create base WSAgent as composition instead of inheritance
        self._base_agent = WSAgent(approval_key, **kwargs)
        self.store = RealtimeDataStore(max_history=max_history)
        self.keep_history = keep_history
        self._setup_auto_store_handlers()

    def _setup_auto_store_handlers(self) -> None:
        """자동 저장 핸들러 설정"""

        def create_store_handler(sub_type):
            def handler(data: Any, metadata: Dict):
                if isinstance(data, list):
                    if sub_type.value in KEYLESS_TR_IDS:
                        # 첫 컬럼이 키가 아닌 피드: WSAgent가 특정한 구독 키 (없으면 저장 안 함)
                        code = metadata.get("tr_key", "")
                    else:
                        code = data[0] if data else metadata.get("tr_key", "")
                    parsed = RealtimeDataParser.parse(sub_type, data)
                else:
                    code = metadata.get("tr_key", "")
                    parsed = data if isinstance(data, dict) else {"raw": data}
                if code:
                    self.store.update(sub_type, code, parsed, self.keep_history)

            return handler

        for sub_type in SubscriptionType:
            self._base_agent.register_handler(sub_type, create_store_handler(sub_type))

    def __getattr__(self, name: str):
        """Delegate to base WSAgent"""
        return getattr(self._base_agent, name)


__all__ = ["RealtimeDataParser", "RealtimeDataStore", "WSAgentWithStore"]
