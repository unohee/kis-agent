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

from .ws_types import SubscriptionType


class RealtimeDataParser:
    """실시간 데이터 파싱 헬퍼 - 웹소켓 수신 데이터를 딕셔너리로 변환"""

    # 국내주식 체결 데이터 필드 (H0STCNT0)
    STOCK_TRADE_FIELDS = [
        "mksc_shrn_iscd",
        "stck_cntg_hour",
        "stck_prpr",
        "prdy_vrss_sign",
        "prdy_vrss",
        "prdy_ctrt",
        "wghn_avrg_stck_prc",
        "stck_oprc",
        "stck_hgpr",
        "stck_lwpr",
        "askp1",
        "bidp1",
        "cntg_vol",
        "acml_vol",
        "acml_tr_pbmn",
        "seln_cntg_csnu",
        "shnu_cntg_csnu",
        "ntby_cntg_csnu",
        "cttr",
        "seln_cntg_smtn",
        "shnu_cntg_smtn",
        "ccld_dvsn",
        "shnu_rate",
        "prdy_vol_vrss_acml_vol_rate",
        "oprc_hour",
        "oprc_vrss_prpr_sign",
        "oprc_vrss_prpr",
        "hgpr_hour",
        "hgpr_vrss_prpr_sign",
        "hgpr_vrss_prpr",
        "lwpr_hour",
        "lwpr_vrss_prpr_sign",
        "lwpr_vrss_prpr",
        "bsop_date",
        "new_mkop_cls_code",
        "trht_yn",
        "askp_rsqn1",
        "bidp_rsqn1",
        "total_askp_rsqn",
        "total_bidp_rsqn",
        "vol_tnrt",
        "prdy_smns_hour_acml_vol",
        "prdy_smns_hour_acml_vol_rate",
        "hour_cls_code",
        "mrkt_trtm_cls_code",
        "vi_stnd_prc",
    ]

    # 국내주식 호가 데이터 필드 (H0STASP0)
    STOCK_ORDERBOOK_FIELDS = [
        "mksc_shrn_iscd",
        "bsop_hour",
        "hour_cls_code",
        "askp1",
        "askp2",
        "askp3",
        "askp4",
        "askp5",
        "askp6",
        "askp7",
        "askp8",
        "askp9",
        "askp10",
        "bidp1",
        "bidp2",
        "bidp3",
        "bidp4",
        "bidp5",
        "bidp6",
        "bidp7",
        "bidp8",
        "bidp9",
        "bidp10",
        "askp_rsqn1",
        "askp_rsqn2",
        "askp_rsqn3",
        "askp_rsqn4",
        "askp_rsqn5",
        "askp_rsqn6",
        "askp_rsqn7",
        "askp_rsqn8",
        "askp_rsqn9",
        "askp_rsqn10",
        "bidp_rsqn1",
        "bidp_rsqn2",
        "bidp_rsqn3",
        "bidp_rsqn4",
        "bidp_rsqn5",
        "bidp_rsqn6",
        "bidp_rsqn7",
        "bidp_rsqn8",
        "bidp_rsqn9",
        "bidp_rsqn10",
        "total_askp_rsqn",
        "total_bidp_rsqn",
        "ovtm_total_askp_rsqn",
        "ovtm_total_bidp_rsqn",
        "antc_cnpr",
        "antc_cnqn",
        "antc_vol",
        "antc_cntg_vrss",
        "antc_cntg_vrss_sign",
        "antc_cntg_prdy_ctrt",
        "acml_vol",
        "total_askp_rsqn_icdc",
        "total_bidp_rsqn_icdc",
        "ovtm_total_askp_icdc",
        "ovtm_total_bidp_icdc",
        "stck_deal_cls_code",
    ]

    # 지수 데이터 필드 (H0IF1000)
    INDEX_FIELDS = [
        "bsop_hour",
        "bstp_nmix_prpr",
        "bstp_nmix_prdy_vrss",
        "prdy_vrss_sign",
        "bstp_nmix_prdy_ctrt",
        "acml_vol",
        "acml_tr_pbmn",
        "bstp_nmix_oprc",
        "bstp_nmix_hgpr",
        "bstp_nmix_lwpr",
        "ascn_issu_cnt",
        "uplm_issu_cnt",
        "stnr_issu_cnt",
        "down_issu_cnt",
        "lslm_issu_cnt",
    ]

    # 프로그램매매 데이터 필드 (H0GSCNT0)
    PROGRAM_TRADE_FIELDS = [
        "mksc_shrn_iscd",
        "bsop_hour",
        "seln_cntg_qty",
        "seln_cntg_amt",
        "shnu_cntg_qty",
        "shnu_cntg_amt",
        "ntby_cntg_qty",
        "ntby_cntg_amt",
        "seln_hoka_rsqn",
        "shnu_hoka_rsqn",
        "ntby_hoka_rsqn",
    ]

    # 회원사별 매매동향 필드 (H0MBCNT0)
    MEMBER_TRADE_FIELDS = [
        "mksc_shrn_iscd",
        "bsop_hour",
        "glob_ntby_qty",
        "glob_ntby_tr_pbmn",
        "glob_seln_qty",
        "glob_shnu_qty",
        "sscr_ntby_qty",
        "sscr_ntby_tr_pbmn",
        "sscr_seln_qty",
        "sscr_shnu_qty",
        "frgn_ntby_qty",
        "frgn_ntby_tr_pbmn",
        "frgn_seln_qty",
        "frgn_shnu_qty",
        "orgn_ntby_qty",
        "orgn_ntby_tr_pbmn",
        "orgn_seln_qty",
        "orgn_shnu_qty",
    ]

    # 지수 예상체결 필드 (H0UPANC0)
    INDEX_EXPECTED_FIELDS = [
        "bsop_hour",
        "bstp_nmix_sdpr",
        "bstp_nmix_antc_cnpr",
        "bstp_nmix_antc_cntg_vrss",
        "antc_cntg_vrss_sign",
        "bstp_nmix_antc_cntg_ctrt",
        "antc_vol",
    ]

    # 종목 예상체결 필드 (H0UNANC0)
    STOCK_EXPECTED_FIELDS = [
        "mksc_shrn_iscd",
        "bsop_hour",
        "antc_cnpr",
        "antc_cntg_vrss",
        "antc_cntg_vrss_sign",
        "antc_cntg_prdy_ctrt",
        "antc_vol",
        "stck_sdpr",
    ]

    # NXT 장운영정보 필드 (H0NXMKO0)
    MARKET_OPERATION_NXT_FIELDS = [
        "mksc_shrn_iscd",
        "trht_yn",
        "tr_susp_reas_cntt",
        "mkop_cls_code",
        "antc_mkop_cls_code",
        "mrkt_trtm_cls_code",
        "divi_app_cls_code",
        "iscd_stat_cls_code",
        "vi_cls_code",
        "ovtm_vi_cls_code",
        "exch_cls_code",
    ]

    # NXT 프로그램매매 필드 (H0NXPGM0)
    PROGRAM_TRADE_NXT_FIELDS = [
        "mksc_shrn_iscd",
        "stck_cntg_hour",
        "seln_cnqn",
        "seln_tr_pbmn",
        "shnu_cnqn",
        "shnu_tr_pbmn",
        "ntby_cnqn",
        "ntby_tr_pbmn",
        "seln_rsqn",
        "shnu_rsqn",
        "whol_ntby_qty",
    ]

    @classmethod
    def parse(cls, sub_type: SubscriptionType, values: List[str]) -> Dict[str, Any]:
        """실시간 데이터 파싱 - sub_type에 맞는 필드 매핑 적용"""
        ST = SubscriptionType

        field_map = {
            ST.STOCK_TRADE: cls.STOCK_TRADE_FIELDS,
            ST.STOCK_ASK_BID: cls.STOCK_ORDERBOOK_FIELDS,
            ST.STOCK_EXPECTED: cls.STOCK_EXPECTED_FIELDS,
            ST.INDEX: cls.INDEX_FIELDS,
            ST.INDEX_EXPECTED: cls.INDEX_EXPECTED_FIELDS,
            ST.PROGRAM_TRADE: cls.PROGRAM_TRADE_FIELDS,
            ST.MEMBER_TRADE: cls.MEMBER_TRADE_FIELDS,
            ST.STOCK_TRADE_NXT: cls.STOCK_TRADE_FIELDS,
            ST.STOCK_ASK_BID_NXT: cls.STOCK_ORDERBOOK_FIELDS,
            ST.STOCK_EXPECTED_NXT: cls.STOCK_EXPECTED_FIELDS,
            ST.PROGRAM_TRADE_NXT: cls.PROGRAM_TRADE_NXT_FIELDS,
            ST.MARKET_OPERATION_NXT: cls.MARKET_OPERATION_NXT_FIELDS,
            ST.MEMBER_TRADE_NXT: cls.MEMBER_TRADE_FIELDS,
        }

        fields = field_map.get(sub_type)
        if not fields:
            return {f"field_{i}": v for i, v in enumerate(values)}

        result = {}
        for i, field_name in enumerate(fields):
            if i < len(values):
                result[field_name] = cls._convert_value(values[i], field_name)
        return result

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
        ]

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
