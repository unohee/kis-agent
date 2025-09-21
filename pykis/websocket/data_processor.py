"""
실시간 데이터 처리 모듈

수신된 실시간 데이터를 처리하고 분석하는 모듈입니다.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    실시간 데이터 처리기

    WebSocket으로 수신된 데이터를 파싱, 복호화, 처리합니다.

    Attributes:
        aes_keys: TR ID별 AES 암호화 키 저장
        trade_history: 종목별 거래 이력
        latest_data: 종목별 최신 데이터
    """

    def __init__(self):
        """DataProcessor 초기화"""
        self.aes_keys: Dict[str, Tuple[bytes, bytes]] = {}  # {tr_id: (key, iv)}
        self.trade_history: Dict[str, List] = defaultdict(list)
        self.latest_data: Dict[str, Dict] = {}

    def process_message(self, raw_message: Any) -> Dict[str, Any]:
        """
        원시 메시지 처리

        Args:
            raw_message: WebSocket으로 수신된 원시 메시지

        Returns:
            Dict[str, Any]: 처리된 메시지 데이터

        Raises:
            json.JSONDecodeError: JSON 파싱 실패
            ValueError: 메시지 형식 오류
        """
        # 바이너리 메시지 처리
        if isinstance(raw_message, bytes):
            return self._process_binary_message(raw_message)

        # JSON 메시지 처리
        if isinstance(raw_message, str):
            return self._process_json_message(raw_message)

        raise ValueError(f"지원하지 않는 메시지 타입: {type(raw_message)}")

    def _process_json_message(self, message: str) -> Dict[str, Any]:
        """
        JSON 메시지 처리

        Args:
            message: JSON 문자열 메시지

        Returns:
            Dict[str, Any]: 파싱된 메시지

        Raises:
            json.JSONDecodeError: JSON 파싱 실패
        """
        data = json.loads(message)

        # PINGPONG 처리
        if data.get("header", {}).get("tr_id") == "PINGPONG":
            return {"type": "PINGPONG", "data": data}

        # AES 키 추출
        header = data.get("header", {})
        tr_id = header.get("tr_id")

        if header.get("tr_key"):
            # AES 키 저장
            key = b64decode(header["tr_key"])
            iv = b64decode(header.get("tr_iv", ""))
            self.aes_keys[tr_id] = (key, iv)

        return data

    def _process_binary_message(self, message: bytes) -> Dict[str, Any]:
        """
        바이너리 메시지 처리 (암호화된 메시지)

        Args:
            message: 바이너리 메시지

        Returns:
            Dict[str, Any]: 복호화된 메시지

        Raises:
            ValueError: 복호화 실패 또는 메시지 형식 오류
        """
        # 메시지 파싱
        header_length = int.from_bytes(message[0:2], byteorder="big")
        header_data = message[2 : 2 + header_length]
        body_data = message[2 + header_length :]

        header = json.loads(header_data.decode("utf-8"))
        tr_id = header.get("tr_id", "")

        # AES 복호화
        if tr_id in self.aes_keys and header.get("encrypt", "N") == "Y":
            key, iv = self.aes_keys[tr_id]
            decrypted_body = self._decrypt_aes(body_data, key, iv)
            body = json.loads(decrypted_body)
        else:
            body = json.loads(body_data.decode("utf-8"))

        return {
            "header": header,
            "body": body,
            "tr_id": tr_id,
            "timestamp": datetime.now().isoformat(),
        }

    def _decrypt_aes(self, encrypted_data: bytes, key: bytes, iv: bytes) -> str:
        """
        AES 복호화

        Args:
            encrypted_data: 암호화된 데이터
            key: AES 키
            iv: 초기화 벡터

        Returns:
            str: 복호화된 문자열

        Raises:
            ValueError: 복호화 실패
        """
        if not key or not iv:
            raise ValueError("AES 키 또는 IV가 없습니다")

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted.decode("utf-8")

    def parse_trade_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        체결 데이터 파싱

        Args:
            data: 처리된 메시지 데이터

        Returns:
            Optional[Dict[str, Any]]: 파싱된 체결 데이터
        """
        if data.get("tr_id") != "H0STCNT0":
            return None

        body = data.get("body", {})
        output = body.get("output", {})

        if not output:
            return None

        # 체결 데이터 추출
        trade_data = {
            "code": output.get("stck_shrn_iscd"),
            "name": output.get("stck_bsop_date"),  # 종목명
            "price": int(output.get("stck_prpr", 0)),
            "change": int(output.get("prdy_vrss", 0)),
            "change_rate": float(output.get("prdy_ctrt", 0)),
            "volume": int(output.get("acml_vol", 0)),
            "time": output.get("stck_cntg_hour"),
            "timestamp": datetime.now(),
        }

        # 거래 이력 저장
        code = trade_data["code"]
        if code:
            self.trade_history[code].append(trade_data)
            if len(self.trade_history[code]) > 1000:
                self.trade_history[code] = self.trade_history[code][-1000:]

            self.latest_data[code] = trade_data

        return trade_data

    def parse_orderbook_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        호가 데이터 파싱

        Args:
            data: 처리된 메시지 데이터

        Returns:
            Optional[Dict[str, Any]]: 파싱된 호가 데이터
        """
        if data.get("tr_id") != "H0STASP0":
            return None

        body = data.get("body", {})
        output = body.get("output", {})

        if not output:
            return None

        # 호가 데이터 추출
        orderbook_data = {
            "code": output.get("stck_shrn_iscd"),
            "ask_prices": [],
            "bid_prices": [],
            "ask_volumes": [],
            "bid_volumes": [],
            "timestamp": datetime.now(),
        }

        # 매도호가 10단계
        for i in range(1, 11):
            ask_price = output.get(f"askp{i}")
            ask_vol = output.get(f"askp_rsqn{i}")
            if ask_price:
                orderbook_data["ask_prices"].append(int(ask_price))
                orderbook_data["ask_volumes"].append(int(ask_vol or 0))

        # 매수호가 10단계
        for i in range(1, 11):
            bid_price = output.get(f"bidp{i}")
            bid_vol = output.get(f"bidp_rsqn{i}")
            if bid_price:
                orderbook_data["bid_prices"].append(int(bid_price))
                orderbook_data["bid_volumes"].append(int(bid_vol or 0))

        return orderbook_data

    def parse_index_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        지수 데이터 파싱

        Args:
            data: 처리된 메시지 데이터

        Returns:
            Optional[Dict[str, Any]]: 파싱된 지수 데이터
        """
        if data.get("tr_id") != "H0IF1000":
            return None

        body = data.get("body", {})
        output = body.get("output", {})

        if not output:
            return None

        # 지수 데이터 추출
        index_data = {
            "code": output.get("bstp_nmix_prpr"),
            "value": float(output.get("bstp_nmix_prpr", 0)),
            "change": float(output.get("bstp_nmix_prdy_vrss", 0)),
            "change_rate": float(output.get("prdy_vrss_sign", 0)),
            "timestamp": datetime.now(),
        }

        return index_data

    def calculate_indicators(self, code: str) -> Dict[str, Any]:
        """
        기술 지표 계산

        Args:
            code: 종목 코드

        Returns:
            Dict[str, Any]: 계산된 기술 지표
        """
        history = self.trade_history.get(code, [])

        if len(history) < 20:
            return {}

        prices = [trade["price"] for trade in history]

        # RSI 계산
        rsi = self._calculate_rsi(prices)

        # MACD 계산
        macd = self._calculate_macd(prices)

        return {
            "rsi": rsi,
            "macd": macd,
            "sma_20": sum(prices[-20:]) / 20 if len(prices) >= 20 else None,
        }

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """
        RSI 계산

        Args:
            prices: 가격 리스트
            period: RSI 기간

        Returns:
            Optional[float]: RSI 값
        """
        if len(prices) < period + 1:
            return None

        gains = []
        losses = []

        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-diff)

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def _calculate_macd(
        self, prices: List[float], fast: int = 12, slow: int = 26
    ) -> Optional[float]:
        """
        MACD 계산

        Args:
            prices: 가격 리스트
            fast: 빠른 EMA 기간
            slow: 느린 EMA 기간

        Returns:
            Optional[float]: MACD 값
        """
        if len(prices) < slow:
            return None

        # EMA 계산
        def calculate_ema(data: List[float], period: int) -> float:
            alpha = 2 / (period + 1)
            ema = data[0]
            for price in data[1:]:
                ema = price * alpha + ema * (1 - alpha)
            return ema

        ema_fast = calculate_ema(prices[-slow:], fast)
        ema_slow = calculate_ema(prices[-slow:], slow)

        return round(ema_fast - ema_slow, 2)
