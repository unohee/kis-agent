"""
메시지 핸들러 모듈 (Strategy Pattern)

다양한 타입의 WebSocket 메시지를 처리하는 핸들러들을 정의합니다.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageHandler(ABC):
    """
    메시지 핸들러 추상 기반 클래스

    Strategy Pattern을 구현하여 메시지 타입별로 처리 로직을 분리합니다.
    """

    @abstractmethod
    def can_handle(self, message: Dict[str, Any]) -> bool:
        """
        이 핸들러가 메시지를 처리할 수 있는지 확인

        Args:
            message: 처리할 메시지

        Returns:
            bool: 처리 가능 여부
        """
        pass

    @abstractmethod
    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        메시지 처리

        Args:
            message: 처리할 메시지

        Returns:
            Optional[Dict[str, Any]]: 처리 결과
        """
        pass


class TradeHandler(MessageHandler):
    """
    체결 데이터 핸들러

    주식 체결 데이터(H0STCNT0)를 처리합니다.
    """

    def __init__(self):
        """TradeHandler 초기화"""
        self.tr_id = "H0STCNT0"

    def can_handle(self, message: Dict[str, Any]) -> bool:
        """체결 메시지 확인"""
        return (
            message.get("tr_id") == self.tr_id
            or message.get("header", {}).get("tr_id") == self.tr_id
        )

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        체결 데이터 처리

        Args:
            message: 체결 메시지

        Returns:
            Optional[Dict[str, Any]]: 처리된 체결 데이터
        """
        body = message.get("body", {})
        output = body.get("output", {})

        if not output:
            logger.warning("체결 데이터에 output이 없습니다")
            return None

        return {
            "type": "trade",
            "code": output.get("stck_shrn_iscd"),
            "price": int(output.get("stck_prpr", 0)),
            "change": int(output.get("prdy_vrss", 0)),
            "change_rate": float(output.get("prdy_ctrt", 0)),
            "volume": int(output.get("acml_vol", 0)),
            "amount": int(output.get("acml_tr_pbmn", 0)),
            "time": output.get("stck_cntg_hour"),
            "timestamp": datetime.now().isoformat(),
        }


class OrderbookHandler(MessageHandler):
    """
    호가 데이터 핸들러

    주식 호가 데이터(H0STASP0)를 처리합니다.
    """

    def __init__(self):
        """OrderbookHandler 초기화"""
        self.tr_id = "H0STASP0"

    def can_handle(self, message: Dict[str, Any]) -> bool:
        """호가 메시지 확인"""
        return (
            message.get("tr_id") == self.tr_id
            or message.get("header", {}).get("tr_id") == self.tr_id
        )

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        호가 데이터 처리

        Args:
            message: 호가 메시지

        Returns:
            Optional[Dict[str, Any]]: 처리된 호가 데이터
        """
        body = message.get("body", {})
        output = body.get("output", {})

        if not output:
            logger.warning("호가 데이터에 output이 없습니다")
            return None

        asks = []
        bids = []

        # 매도호가 10단계
        for i in range(1, 11):
            ask_price = output.get(f"askp{i}")
            ask_volume = output.get(f"askp_rsqn{i}")
            if ask_price:
                asks.append({"price": int(ask_price), "volume": int(ask_volume or 0)})

        # 매수호가 10단계
        for i in range(1, 11):
            bid_price = output.get(f"bidp{i}")
            bid_volume = output.get(f"bidp_rsqn{i}")
            if bid_price:
                bids.append({"price": int(bid_price), "volume": int(bid_volume or 0)})

        return {
            "type": "orderbook",
            "code": output.get("stck_shrn_iscd"),
            "asks": asks,
            "bids": bids,
            "total_ask_volume": sum(ask["volume"] for ask in asks),
            "total_bid_volume": sum(bid["volume"] for bid in bids),
            "timestamp": datetime.now().isoformat(),
        }


class IndexHandler(MessageHandler):
    """
    지수 데이터 핸들러

    지수 데이터(H0IF1000)를 처리합니다.
    """

    def __init__(self):
        """IndexHandler 초기화"""
        self.tr_id = "H0IF1000"
        self.index_names = {"0001": "KOSPI", "1001": "KOSDAQ", "2001": "KOSPI200"}

    def can_handle(self, message: Dict[str, Any]) -> bool:
        """지수 메시지 확인"""
        return (
            message.get("tr_id") == self.tr_id
            or message.get("header", {}).get("tr_id") == self.tr_id
        )

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        지수 데이터 처리

        Args:
            message: 지수 메시지

        Returns:
            Optional[Dict[str, Any]]: 처리된 지수 데이터
        """
        body = message.get("body", {})
        output = body.get("output", {})

        if not output:
            logger.warning("지수 데이터에 output이 없습니다")
            return None

        index_code = message.get("header", {}).get("tr_key", "")
        index_name = self.index_names.get(index_code, index_code)

        return {
            "type": "index",
            "code": index_code,
            "name": index_name,
            "value": float(output.get("bstp_nmix_prpr", 0)),
            "change": float(output.get("bstp_nmix_prdy_vrss", 0)),
            "change_rate": float(output.get("prdy_vrss_sign", 0)),
            "high": float(output.get("bstp_nmix_hgpr", 0)),
            "low": float(output.get("bstp_nmix_lwpr", 0)),
            "volume": int(output.get("acml_vol", 0)),
            "timestamp": datetime.now().isoformat(),
        }


class ProgramTradingHandler(MessageHandler):
    """
    프로그램매매 데이터 핸들러

    프로그램매매 데이터(H0GSCNT0)를 처리합니다.
    """

    def __init__(self):
        """ProgramTradingHandler 초기화"""
        self.tr_id = "H0GSCNT0"

    def can_handle(self, message: Dict[str, Any]) -> bool:
        """프로그램매매 메시지 확인"""
        return (
            message.get("tr_id") == self.tr_id
            or message.get("header", {}).get("tr_id") == self.tr_id
        )

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        프로그램매매 데이터 처리

        Args:
            message: 프로그램매매 메시지

        Returns:
            Optional[Dict[str, Any]]: 처리된 프로그램매매 데이터
        """
        body = message.get("body", {})
        output = body.get("output", {})

        if not output:
            logger.warning("프로그램매매 데이터에 output이 없습니다")
            return None

        return {
            "type": "program_trading",
            "code": output.get("stck_shrn_iscd"),
            "buy_amount": int(output.get("seln_pbmn", 0)),
            "sell_amount": int(output.get("shnu_pbmn", 0)),
            "net_amount": int(output.get("ntby_pbmn", 0)),
            "buy_volume": int(output.get("seln_vol", 0)),
            "sell_volume": int(output.get("shnu_vol", 0)),
            "net_volume": int(output.get("ntby_vol", 0)),
            "timestamp": datetime.now().isoformat(),
        }


class PingPongHandler(MessageHandler):
    """
    PINGPONG 메시지 핸들러

    연결 유지를 위한 PINGPONG 메시지를 처리합니다.
    """

    def can_handle(self, message: Dict[str, Any]) -> bool:
        """PINGPONG 메시지 확인"""
        return (
            message.get("type") == "PINGPONG"
            or message.get("header", {}).get("tr_id") == "PINGPONG"
        )

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        PINGPONG 처리

        Args:
            message: PINGPONG 메시지

        Returns:
            Optional[Dict[str, Any]]: PONG 응답
        """
        logger.debug("PINGPONG 메시지 수신")
        return {"type": "PONG", "timestamp": datetime.now().isoformat()}


class MessageHandlerRegistry:
    """
    메시지 핸들러 레지스트리

    여러 메시지 핸들러를 관리하고 적절한 핸들러로 메시지를 라우팅합니다.
    """

    def __init__(self):
        """MessageHandlerRegistry 초기화"""
        self.handlers: List[MessageHandler] = []
        self.default_handler: Optional[Callable] = None

        # 기본 핸들러 등록
        self._register_default_handlers()

    def _register_default_handlers(self):
        """기본 핸들러 등록"""
        self.register(TradeHandler())
        self.register(OrderbookHandler())
        self.register(IndexHandler())
        self.register(ProgramTradingHandler())
        self.register(PingPongHandler())

    def register(self, handler: MessageHandler):
        """
        핸들러 등록

        Args:
            handler: 등록할 메시지 핸들러
        """
        self.handlers.append(handler)
        logger.info(f"핸들러 등록: {handler.__class__.__name__}")

    def set_default_handler(self, handler: Callable):
        """
        기본 핸들러 설정

        Args:
            handler: 기본 핸들러 함수
        """
        self.default_handler = handler

    def process(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        메시지 처리

        적절한 핸들러를 찾아 메시지를 처리합니다.

        Args:
            message: 처리할 메시지

        Returns:
            Optional[Dict[str, Any]]: 처리 결과
        """
        # 적절한 핸들러 찾기
        for handler in self.handlers:
            if handler.can_handle(message):
                result = handler.handle(message)
                if result:
                    logger.debug(
                        f"{handler.__class__.__name__}가 메시지 처리: {result.get('type')}"
                    )
                return result

        # 기본 핸들러 실행
        if self.default_handler:
            return self.default_handler(message)

        logger.warning(f"처리할 수 없는 메시지 타입: {message.get('tr_id')}")
        return None
