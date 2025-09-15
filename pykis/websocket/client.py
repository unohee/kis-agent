import websockets
import json
import requests
import os
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
from datetime import datetime, date
from collections import defaultdict
import pandas as pd
import sys
import select
from dotenv import load_dotenv
import logging

from ..core.client import KISClient
import warnings
from ..stock.api import StockAPI

# 로깅 레벨을 INFO로 설정
logging.basicConfig(level=logging.INFO)

class KisWebSocket:
    """
    한국투자증권 실시간 웹소켓 클라이언트
    """
    def __init__(self, client: KISClient, account_info: dict, stock_codes: list = None, purchase_prices: dict = None, 
                 enable_index: bool = True, enable_program_trading: bool = True, enable_ask_bid: bool = False):
        """
        Args:
            client (KISClient): API 클라이언트 객체
            account_info (dict): 계좌 정보 딕셔너리
            stock_codes (list, optional): 구독할 종목코드 리스트. Defaults to None.
            purchase_prices (dict, optional): 매수 정보 딕셔너리 {'종목코드': (매입가격, 보유 수량)}. Defaults to None.
            enable_index (bool): 지수 실시간 데이터 구독 여부. Defaults to True.
            enable_program_trading (bool): 프로그램매매 실시간 데이터 구독 여부. Defaults to True.
            enable_ask_bid (bool): 호가 실시간 데이터 구독 여부. Defaults to False.
        """
        # Deprecated 안내: 새로운 WebSocket 클라이언트 사용 유도
        warnings.warn(
            "KisWebSocket은 deprecated입니다. 실사용은 RefactoredWebSocketClient 또는 WebSocketClientFactory를 사용하세요.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.client = client
        self.account_info = account_info
        self.stock_api = StockAPI(client=client, account_info=account_info)
        self.url = 'ws://ops.koreainvestment.com:21000'  # 고정 URL
        self.stock_codes = stock_codes or []
        
        # 기능 활성화 플래그
        self.enable_index = enable_index
        self.enable_program_trading = enable_program_trading
        self.enable_ask_bid = enable_ask_bid
        
        self.approval_key = None
        self.aes_key = None
        self.aes_iv = None
        
        # 체결 데이터 및 trade history 초기화
        self.latest_trade = {code: None for code in self.stock_codes}
        self.trade_history = {code: [] for code in self.stock_codes}
        self.prev_indicators = {code: (None, None) for code in self.stock_codes}
        
        # 실시간 지수 데이터 저장소
        self.latest_index = {}  # {'KOSPI200': data, 'KOSPI': data, 'KOSDAQ': data}
        
        # 실시간 프로그램매매 데이터 저장소  
        self.latest_program_trading = {}  # {종목코드: 프로그램매매 데이터}
        
        # 실시간 호가 데이터 저장소
        self.latest_ask_bid = {}  # {종목코드: 호가 데이터}
        
        # 매입 정보: {'종목코드': (매입가격, 보유 수량)}
        self.purchase_prices = purchase_prices or {}
        # 현재 구독중인 종목 집합 (웹소켓 구독 요청을 보낸 종목)
        self.subscribed_stocks = set(self.stock_codes)
        # 새롭게 추가: 종목명을 저장할 딕셔너리
        self.stock_names = {}
        # 추가: 당일 시가 저장용
        self.open_prices = {}
        # 로그 디렉토리 및 파일 설정
        self.log_dir = 'logs/websocket'
        os.makedirs(self.log_dir, exist_ok=True)
        date_str = date.today().strftime('%Y%m%d')
        self.trade_log_file = os.path.join(self.log_dir, f'trade_history_{date_str}.jsonl')
        # Add persistent raw websocket log file for replay/debugging
        self.raw_log_file = os.path.join(self.log_dir, f'raw_ws_{date_str}.log')

        # For live display: track line offsets for each stock
        self.display_lines = {}
        self.console_base_line = 3  # adjust if needed

        # Heartbeat: track last websocket receive time
        self.last_ws_recv_time = datetime.now()
        
        # 마지막 고 조회 시간 추가
        self.last_balance_check = datetime.now()
        
        # 잔고 정보 저장용
        self.balance_info = None
        
        # 초기 예수금 저장용
        self.initial_cash_balance = None

    @staticmethod
    def clear_console():
        os.system('cls' if os.name in ('nt', 'dos') else 'clear')

    @staticmethod
    def format_price(price):
        """
        숫자형 문자열이면 천단위 구분기호를 붙여 반환합니다.
        소수점이 있는 경우 그대로, 아니면 정수형 포맷으로 출력합니다.
        """
        try:
            # 소수점 제거 후 숫자인지 검사
            if price.replace('.', '', 1).isdigit():
                if '.' in price:
                    return f"{float(price):,}"
                else:
                    return f"{int(price):,}"
            else:
                return price
        except ValueError:
            return price

    def get_approval(self):
        """
        REST API를 통해 웹소켓 접속 승인키(approval_key)를 가져옵니다.
        """
        self.approval_key = self.client.get_ws_approval_key()
        logging.info(f"승인키 발급 완료: {self.approval_key}")
        if not self.approval_key:
            raise ValueError("approval_key를 답에서 추출하지 못했습니다.")
        return self.approval_key

    def update_trade_history(self, stock_code, trade_time, price, trade_strength=None):
        """
        trade_history에 추가하고 JSONL로 로그 기록
        """
        # 기존 trade_history 업데이트
        if stock_code not in self.trade_history:
            self.trade_history[stock_code] = []
        self.trade_history[stock_code].append((trade_time, price, trade_strength))
        if len(self.trade_history[stock_code]) > 1000:
            self.trade_history[stock_code] = self.trade_history[stock_code][-1000:]
        # JSONL 로그 기록
        try:
            log_entry = {
                'timestamp': trade_time.isoformat(),
                'code': stock_code,
                'price': price,
                'strength': trade_strength
            }
            with open(self.trade_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            logging.error(f"Failed to write trade log: {e}")

    def compute_RSI(self, stock_code, period=14):
        """
        trade_history의 가격정보를 이용하여 RSI를 계산합니다.
        데이터가 충분하지 않으면 None을 반환합니다.
        """
        trades = self.trade_history.get(stock_code, [])
        if len(trades) < period + 1:
            return None
        prices = [price for _, price, _ in trades]
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

    def ema(self, prices, span):
        """
        단순 EMA 계산 (초기값은 첫 가격 사용)
        """
        alpha = 2 / (span + 1)
        ema_value = prices[0]
        for price in prices[1:]:
            ema_value = price * alpha + ema_value * (1 - alpha)
        return ema_value

    def compute_MACD(self, stock_code, span_short=12, span_long=26):
        """
        MACD를 계산합니다.
        충분한 데이터가 있지 않으면 None 반환.
        """
        trades = self.trade_history.get(stock_code, [])
        if len(trades) < span_long:
            return None
        prices = [price for _, price, _ in trades]
        # 최근 span_long개의 데이터를 가지고 EMA 계산
        ema_short = self.ema(prices[-span_long:], span_short)
        ema_long = self.ema(prices[-span_long:], span_long)
        macd = ema_short - ema_long
        return round(macd, 2)

    def compute_candles(self, stock_code, interval_minutes=1):
        """
        trade_history를 그룹화하여 지정한 분(interval_minutes) 기준 캔들(OHLC)을 계산합니다.
        체결강도는 무시합니다.
        반환 값은 (시작시간, open, high, low, close) 튜플의 리스트입니다.
        """
        trades = self.trade_history.get(stock_code, [])
        if not trades:
            return []
        candles = defaultdict(list)
        for trade in trades:
            # trade: (t, price, trade_strength) - trade_strength 무시
            t, price = trade[0], trade[1]
            minute = t.replace(second=0, microsecond=0)
            if interval_minutes > 1:
                new_min = (t.minute // interval_minutes) * interval_minutes
                minute = t.replace(minute=new_min, second=0, microsecond=0)
            candles[minute].append(price)
        candle_list = []
        for time_key in sorted(candles.keys()):
            prices = candles[time_key]
            open_price = prices[0]
            high_price = max(prices)
            low_price = min(prices)
            close_price = prices[-1]
            candle_list.append((time_key, open_price, high_price, low_price, close_price))
        return candle_list
    
    def compute_RSI_candles(self, stock_code, period=14):
        """
        1분봉 캔들(완료된 캔들과 진행중인 캔들)의 close 가격을 이용해 RSI를 계산합니다.
        충분한 캔들이 없으면 None 반환.
        """
        from datetime import datetime
        candles = self.compute_candles(stock_code, interval_minutes=1)
        current_minute = datetime.now().replace(second=0, microsecond=0)
        # 완료 캔들뿐만 아니라 현재 진행중인 캔들도 포함
        selected_candles = [candle for candle in candles if candle[0] <= current_minute]
        # if len(selected_candles) < period + 1:
        #     print(f"[DEBUG] {stock_code}: 부족한 분봉 데이터, {len(selected_candles)}개 있음, 필요: {period+1}")
        #     return None
        prices = [candle[4] for candle in selected_candles]  # candle[4]는 close 가격
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
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

    def compute_MACD_candles(self, stock_code, span_short=12, span_long=26):
        """
        1분봉 캔들의 close 가격을 사용하여 MACD를 계산합니다.
        충분한 캔들이 없으면 None 반환.
        """
        from datetime import datetime
        candles = self.compute_candles(stock_code, interval_minutes=1)
        current_minute = datetime.now().replace(second=0, microsecond=0)
        # 완료 캔들과 진행중인 캔들을 모두 사용
        selected_candles = [candle for candle in candles if candle[0] <= current_minute]
        if len(selected_candles) < span_long:
            return None
        prices = [candle[4] for candle in selected_candles]
        # EMA 계산을 위해 최근 span_long 개의 가격 사용
        ema_short = self.ema(prices[-span_long:], span_short)
        ema_long  = self.ema(prices[-span_long:], span_long)
        macd = ema_short - ema_long
        return round(macd, 2)

    def compute_MACD_oscillator_candles(self, stock_code, span_short=12, span_long=26, signal_span=9):
        """
        1분봉 캔들의 close 가격을 기반으로 MACD Oscillator(= MACD Histogram)를 계산합니다.
        계산 방식:
        1. 각 캔들에 대해 MACD = EMA_short - EMA_long
        2. MACD Signal = EMA(macd_series, signal_span)
        3. MACD Oscillator = 최신 MACD - 최신 MACD Signal
        충분한 캔들이 없으면 None 반환.
        """
        from datetime import datetime
        candles = self.compute_candles(stock_code, interval_minutes=1)
        current_minute = datetime.now().replace(second=0, microsecond=0)
        selected_candles = [candle for candle in candles if candle[0] <= current_minute]
        if len(selected_candles) < span_long:
            return None
        prices = [candle[4] for candle in selected_candles]
        macd_values = []
        for i in range(span_long - 1, len(prices)):
            window = prices[i - span_long + 1: i + 1]
            ema_short = self.ema(window, span_short)
            ema_long = self.ema(window, span_long)
            macd_values.append(ema_short - ema_long)
        if len(macd_values) < signal_span:
            return None
        signal = self.ema(macd_values[-signal_span:], signal_span)
        oscillator = macd_values[-1] - signal
        return round(oscillator, 2)

    def compute_ATR(self, stock_code, period=14, interval_minutes=1):
        """
        1분봉 캔들을 기반으로 ATR(Average True Range)를 계산합니다.
        충분한 데이터가 없으면 None을 반환합니다.
        """
        candles = self.compute_candles(stock_code, interval_minutes)
        if len(candles) < period + 1:
            return None
        true_ranges = []
        previous_close = candles[0][4]
        for candle in candles[1:]:
            _, o, h, l, c = candle
            tr = max(h - l, abs(h - previous_close), abs(l - previous_close))
            true_ranges.append(tr)
            previous_close = c
        atr = sum(true_ranges[-period:]) / period
        return round(atr, 2)

    def compute_trade_strength_candle(self, stock_code, interval_minutes=1):
        """
        trade_history의 체결강도 데이터를 기반으로 지정한 분(interval_minutes) 기준 평균 체결강도를 계산합니다.
        반환 값은 (시작시간, 평균 체결강도) 튜플의 리스트입니다.
        """
        trades = self.trade_history.get(stock_code, [])
        if not trades:
            return []
        strength_candles = defaultdict(list)
        for trade in trades:
            if len(trade) >= 3 and trade[2] is not None:
                t, strength = trade[0], trade[2]
                minute = t.replace(second=0, microsecond=0)
                if interval_minutes > 1:
                    new_min = (t.minute // interval_minutes) * interval_minutes
                    minute = t.replace(minute=new_min, second=0, microsecond=0)
                strength_candles[minute].append(strength)
        result = []
        for time_key in sorted(strength_candles.keys()):
            strengths = strength_candles[time_key]
            avg_strength = sum(strengths) / len(strengths)
            result.append((time_key, avg_strength))
        return result
    
    def print_domestic_hoga(self, data):
        """
        국내주식 호가 10단계 (상위/하위) 전체를 보기 좋게 출력합니다.
        """
        recv = data.split('^')
        sell_prices = recv[3:13]
        buy_prices = recv[13:23]
        sell_qty = recv[23:33]
        buy_qty = recv[33:43]

        print("=" * 40)
        print("      매도호가       |     잔량")
        print("-" * 40)
        for i in range(9, -1, -1):
            print(f"{i+1:>2} | {self.format_price(sell_prices[i]):>10} | {self.format_price(sell_qty[i]):>10}")
        print("-" * 40)
        for i in range(10):
            print(f"{i+1:>2} | {self.format_price(buy_prices[i]):>10} | {self.format_price(buy_qty[i]):>10}")
        print("      매수호가       |     잔량")
        print("=" * 40)
        print(f"총 매도 잔량: {self.format_price(recv[43])} | 총 매수 잔량: {self.format_price(recv[44])}")
        print(f"예상 체결가: {self.format_price(recv[47])} | 예상 체결량: {self.format_price(recv[48])} | 대비: {recv[52]}%")
        print("=" * 40)

    def print_program_trade_summary(self, data_cnt, data):
        """
        국내주식 실시간 프로그램매매 요약 정보를 사람이 읽기 쉽게 출력합니다.
        """
        menulist = "종목코드|체결시간|매도체결량|매도대금|매수체결량|매수대금|순매수체결량|순매수대금|매도호가잔량|매수호가잔량|전체순매수호가잔량"
        labels = menulist.split('|')
        pValue = data.split('^')
        i = 0
        print("========== 실시간 프로그램매매 ==========")
        for cnt in range(data_cnt):
            print("### [%d / %d]" % (cnt + 1, data_cnt))
            for label in labels:
                print("%-13s[%s]" % (label, pValue[i]))
                i += 1
        print("=========================================")

    def get_index_name(self, index_code):
        """
        지수 코드를 지수 이름으로 변환합니다.
        """
        index_map = {
            '0001': 'KOSPI',
            '1001': 'KOSDAQ', 
            '2001': 'KOSPI200',
            '1029': 'KOSPI200',  # 또 다른 코스피200 코드
        }
        return index_map.get(index_code, f"INDEX_{index_code}")

    def display_ask_bid_info(self, stock_code, data):
        """
        실시간 호가 정보를 간결하게 표시합니다.
        """
        try:
            recv = data.split('^')
            if len(recv) >= 50:
                # 매도호가 1~5단계만 표시 (간결화)
                sell_prices = recv[3:8]  # 상위 5단계만
                buy_prices = recv[13:18]  # 상위 5단계만
                
                name = self.stock_names.get(stock_code, stock_code)
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"[{current_time}] 호가 - {name}({stock_code})")
                print(f"매도5: {self.format_price(sell_prices[4]):<10} | 매수1: {self.format_price(buy_prices[0]):<10}")
                print(f"매도1: {self.format_price(sell_prices[0]):<10} | 매수5: {self.format_price(buy_prices[4]):<10}")
                print("-" * 50)
        except Exception as e:
            logging.error(f"호가 데이터 처리 오류 ({stock_code}): {e}")
            raise

    def display_index_info(self, index_name, index_data):
        """
        실시간 지수 정보를 표시합니다.
        """
        try:
            if len(index_data) >= 10:
                current_time = datetime.now().strftime('%H:%M:%S')
                index_value = self.format_price(index_data[1])  # 현재 지수값
                change = index_data[2]  # 전일대비
                change_rate = index_data[3]  # 등락률
                
                # 부호 처리
                change_str = f"+{change}" if not change.startswith(('+', '-')) else change
                change_rate_str = f"+{change_rate}" if not change_rate.startswith(('+', '-')) else change_rate
                
                print(f"[{current_time}] {index_name}: {index_value} ({change_str}, {change_rate_str}%)")
        except Exception as e:
            logging.error(f"지수 데이터 처리 오류 ({index_name}): {e}")
            raise

    def display_program_trading_info(self, stock_code, data):
        """
        실시간 프로그램매매 정보를 표시합니다.
        """
        try:
            recv = data.split('^')
            if len(recv) >= 11:
                name = self.stock_names.get(stock_code, stock_code)
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # 프로그램매매 주요 지표
                sell_volume = self.format_price(recv[2])     # 매도체결량
                buy_volume = self.format_price(recv[4])      # 매수체결량
                net_volume = self.format_price(recv[6])      # 순매수체결량
                net_amount = self.format_price(recv[7])      # 순매수대금
                
                print(f"[{current_time}] 프로그램매매 - {name}({stock_code})")
                print(f"  매도량: {sell_volume} | 매수량: {buy_volume}")
                print(f"  순매수량: {net_volume} | 순매수대금: {net_amount}")
                print("-" * 50)
        except Exception as e:
            logging.error(f"프로그램매매 데이터 처리 오류 ({stock_code}): {e}")

    def display_trade_summary(self):
        # 계산 로직은 모두 trade_summary에 있음. 반환 값은
        # (종목코드, 종목명, 체결가, 거래량, 체결강도, 매입가격, 보유수량, 평가금액, 매입가 대비,
        #  RSI, MACD, ATR, 시가 대비 변동, 20 EMA, 120 EMA) 튜플로 구성된 dict입니다.
        summary = self.trade_summary()
        import sys
        sys.stdout.write("\033[H\033[J")  # 화면 클리어
        for code, data in summary.items():
            # data 인덱스별로 값 할당 (None이면 "N/A" 처리)
            stock_code   = data[0] if data[0] is not None else "N/A"
            stock_name   = data[1] if data[1] is not None else "N/A"
            close_price  = f"{data[2]:,.2f}" if (data[2] is not None and isinstance(data[2], (int, float))) else "N/A"
            volume       = data[3] if data[3] is not None else "N/A"
            strength     = data[4] if data[4] is not None else "N/A"
            avg_price    = f"{data[5]:,.2f}" if (data[5] is not None and isinstance(data[5], (int, float))) else "N/A"
            quantity     = data[6] if data[6] is not None else "N/A"
            eval_amt     = f"{data[7]:,.2f}" if (data[7] is not None and isinstance(data[7], (int, float))) else "N/A"
            purch_change = f"{data[8]:.2f}%" if (data[8] is not None) else "N/A"
            rsi_val      = data[9] if data[9] is not None else "N/A"
            macd_val     = data[10] if data[10] is not None else "N/A"
            atr_val      = data[11] if data[11] is not None else "N/A"
            daily_change = f"{data[12]:.2f}%" if (data[12] is not None) else "N/A"
            ema20        = f"{data[13]:,.2f}" if (data[13] is not None and isinstance(data[13], (int, float))) else "N/A"
            ema120       = f"{data[14]:,.2f}" if (data[14] is not None and isinstance(data[14], (int, float))) else "N/A"

            print(f"{stock_code} ({stock_name})")
            print(f"체결가: {close_price} | 거래량: {volume} | 체결강도: {strength}")
            print(f"보유 -> 매입가: {avg_price} | 수량: {quantity} | 평가금액: {eval_amt} | 매입가 대비: {purch_change}")
            print(f"지표 -> RSI: {rsi_val} | MACD: {macd_val} | ATR: {atr_val} | 시가 대비: {daily_change}")
            print(f"이동평균 -> 20 EMA: {ema20} | 120 EMA: {ema120}")
            print("-" * 50)
            sys.stdout.flush()

    # 새로 추가: trade_summary 함수 (프린트 없이 튜플로 데이터 반환)
    def trade_summary(self):
        """
        각 종목에 대한 보조지표 및 체결 데이터를 튜플로 반환합니다.
        반환 형식:
        {코드: (종목코드, 종목명, 체결가, 거래량, 체결강도, 매입가격, 보유수량, 평가금액, 매입가 대비,
        RSI, MACD, ATR, 시가 대비 변동, 20 EMA, 120 EMA)}
        """
        summary = {}
        for code in self.stock_codes:
            # 종목코드와 종목명
            stock_name = self.stock_names.get(code, code)
            if self.latest_trade.get(code):
                trade_values = self.latest_trade[code].split('^')
                stock_code = trade_values[0]
                close_price = trade_values[2]
                volume = trade_values[12] if len(trade_values) > 12 else None
                trade_strength = trade_values[18] if len(trade_values) > 18 else None
                try:
                    cp_val = float(close_price)
                except Exception:
                    cp_val = None
            else:
                stock_code = code
                close_price = None
                volume = None
                trade_strength = None
                cp_val = None

            # 보유 정보
            if code in self.purchase_prices and cp_val is not None:
                try:
                    avg_price, quantity = self.purchase_prices[code]
                    eval_amt = cp_val * quantity
                    purchase_change = ((cp_val - avg_price) / avg_price * 100) if avg_price != 0 else None
                except Exception:
                    avg_price, quantity, eval_amt, purchase_change = None, None, None, None
            else:
                avg_price = quantity = eval_amt = purchase_change = None

            # 보조지표 계산 (RSI, MACD, ATR)
            rsi = self.compute_RSI_candles(code)
            macd = self.compute_MACD_candles(code)
            atr = self.compute_ATR(code)
            rsi_val = rsi if rsi is not None else None
            macd_val = macd if macd is not None else None
            atr_val = atr if atr is not None else None

            # 당일 시가 대비 변동률
            open_price = self.open_prices.get(code, None)
            if cp_val is not None and open_price is not None and open_price != 0:
                daily_change = ((cp_val - open_price) / open_price * 100)
            else:
                daily_change = None

            # 20 EMA, 120 EMA 계산 (1분봉 캔들 기준)
            one_min_candles = self.compute_candles(code, interval_minutes=1)
            ema20, ema120 = None, None
            if one_min_candles:
                price_list = [candle[4] for candle in one_min_candles]
                if len(price_list) >= 20:
                    ema20 = int(round(self.ema(price_list[-20:], 20)))
                if len(price_list) >= 120:
                    ema120 = int(round(self.ema(price_list[-120:], 120)))

            summary[code] = (stock_code, stock_name, cp_val, volume, trade_strength,
                             avg_price, quantity, eval_amt, purchase_change,
                             rsi_val, macd_val, atr_val, daily_change, ema20, ema120)
        return summary

    async def update_holdings_loop(self):
        from ..account.api import AccountAPI
        account_api = AccountAPI(client=self.client, auth=self.auth)
        while True:
            try:
                holdings = account_api.get_account_balance()['output1']
                if holdings:
                    new_purchase_info = {h['pdno']: (float(h['pchs_avg_pric']), int(h['hldg_qty'])) for h in holdings if int(h['hldg_qty']) > 0}
                    new_holdings = set(new_purchase_info.keys())
                    current_holdings = set(self.stock_codes)

                    # 신규 종목 추가
                    for ticker in new_holdings - current_holdings:
                        self.stock_codes.append(ticker)
                        self.latest_trade[ticker] = None
                        self.trade_history[ticker] = []
                        self.prev_indicators[ticker] = (None, None)
                        # 신규 종목 추가 시 historical data 로드
                        self.load_historical_data_for_stock(ticker)
                        if hasattr(self, "ws") and self.ws:
                            senddata_trade = {
                                "header": {
                                    "approval_key": self.approval_key,
                                    "custtype": "P",
                                    "tr_type": "1",
                                    "content-type": "utf-8"
                                },
                                "body": {
                                    "input": {
                                        "tr_id": "H0STCNT0",
                                        "tr_key": ticker
                                    }
                                }
                            }
                            await self.ws.send(json.dumps(senddata_trade))
                            self.subscribed_stocks.add(ticker)

                    # 매도(보유종목 감시 해제) 처리 : 이전에 감시하던 종목 중 now_holdings에 없는 종목 제거
                    for ticker in list(current_holdings - new_holdings):
                        if ticker in self.subscribed_stocks:
                            # 구독 해제 전송
                            senddata_unsub = {
                                "header": {
                                    "approval_key": self.approval_key,
                                    "custtype": "P",
                                    "tr_type": "1",
                                    "content-type": "utf-8"
                                },
                                "body": {
                                    "input": {
                                        "tr_id": "H0STCNT0_UNSUB",
                                        "tr_key": ticker
                                    }
                                }
                            }
                            await self.ws.send(json.dumps(senddata_unsub))
                            self.subscribed_stocks.remove(ticker)
                        # 데이터 삭제
                        if ticker in self.stock_codes:
                            self.stock_codes.remove(ticker)
                        self.latest_trade.pop(ticker, None)
                        self.trade_history.pop(ticker, None)
                        self.prev_indicators.pop(ticker, None)
                        self.purchase_prices.pop(ticker, None)
                        self.stock_names.pop(ticker, None)
                        self.open_prices.pop(ticker, None)
                    
                    self.purchase_prices = new_purchase_info
                    # 추가: 보유종목의 종목명 재조회
                    self.fetch_stock_names()
            except Exception as e:
                logging.error(f"update_holdings_loop: {e}")
            await asyncio.sleep(10)

    def handle_message(self, data):
        """
        수신된 웹소켓 메시지를 처리합니다.
        - 체결 데이터(H0STCNT0): 현재가와 기술적 지표 업데이트
        - 호가 데이터(H0STASP0): 실시간 호가창 정보 (선택적)
        - 지수 데이터(H0IF1000): 실시간 지수 정보 (코스피200 등)
        - 프로그램매매(H0GSCNT0): 실시간 프로그램매매 추이
        - 체결통보(H0STCNI0, H0STCNI9): 기존 처리 유지
        - JSON 메시지: PINGPONG, SUBSCRIBE SUCCESS, AES 키 처리
        """
        if data[0] in ('0', '1'):
            recv_parts = data.split('|')
            trid = recv_parts[1]
            
            if trid == "H0STCNT0":
                # 체결 데이터 저장
                stock_code = recv_parts[3].split('^')[0]
                self.latest_trade[stock_code] = recv_parts[3]
                
                # trade_history에도 저장 (기술적 지표 계산을 위해)
                try:
                    trade_data = recv_parts[3].split('^')
                    if len(trade_data) >= 19:
                        time_str = trade_data[1]
                        price_str = trade_data[2]
                        strength_str = trade_data[18]
                        
                        # 시간 파싱 (HHMMSS 형태)
                        from datetime import datetime
                        current_date = datetime.now().strftime('%Y%m%d')
                        trade_time = datetime.strptime(f"{current_date}{time_str}", '%Y%m%d%H%M%S')
                        
                        price = float(price_str)
                        strength = float(strength_str) if strength_str else None
                        
                        # trade_history에 추가
                        self.update_trade_history(stock_code, trade_time, price, strength)
                except Exception as e:
                    logging.error(f"체결 데이터 파싱 오류: {e}")
                
                # 현재가와 기술적 지표 업데이트
                self.update_price_and_indicators()
                
            elif trid == "H0STASP0" and self.enable_ask_bid:
                # 호가 데이터 처리
                stock_code = recv_parts[3].split('^')[0]
                self.latest_ask_bid[stock_code] = recv_parts[3]
                if len(recv_parts[3].split('^')) >= 50:
                    self.display_ask_bid_info(stock_code, recv_parts[3])
                    
            elif trid == "H0IF1000" and self.enable_index:
                # 지수 데이터 처리 (코스피200, 코스피, 코스닥 등)
                index_data = recv_parts[3].split('^')
                if len(index_data) >= 10:
                    index_code = index_data[0]  # 지수 코드
                    index_name = self.get_index_name(index_code)
                    self.latest_index[index_name] = recv_parts[3]
                    self.display_index_info(index_name, index_data)
                    
            elif trid == "H0GSCNT0" and self.enable_program_trading:
                # 프로그램매매 실시간 데이터 처리
                stock_code = recv_parts[3].split('^')[0]
                self.latest_program_trading[stock_code] = recv_parts[3]
                self.display_program_trading_info(stock_code, recv_parts[3])
                
            elif trid in ["H0STCNI0", "H0STCNI9"]:
                # 기존 체결통보 메시지를 이용해 신규 종목 추가
                stock_code = recv_parts[3].split('^')[0]
                if stock_code not in self.stock_codes:
                    logging.info(f"실시간 체결통보로 {stock_code} 신규 추가")
                    self.stock_codes.append(stock_code)
                    self.latest_trade[stock_code] = recv_parts[3]
                    self.trade_history[stock_code] = []
                    self.prev_indicators[stock_code] = (None, None)
                    # 신규 종목 추가 시 구독 요청 메시지 전송
                    if hasattr(self, "ws") and self.ws:
                        senddata_trade = {
                            "header": {
                                "approval_key": self.approval_key,
                                "custtype": "P",
                                "tr_type": "1",
                                "content-type": "utf-8"
                            },
                            "body": {
                                "input": {
                                    "tr_id": "H0STCNT0",
                                    "tr_key": stock_code
                                }
                            }
                        }
                        asyncio.create_task(self.ws.send(json.dumps(senddata_trade)))
                        self.subscribed_stocks.add(stock_code)
                        
        elif data.startswith('{'):
            # JSON 메시지 처리 (예: PINGPONG, SUBSCRIBE SUCCESS, AES키 등)
            json_obj = json.loads(data)
            trid = json_obj["header"].get("tr_id")
            tr_key = json_obj["header"].get("tr_key")
            if trid == "PINGPONG":
                pass  # PINGPONG 메시지 출력 제거
            elif json_obj["body"].get("msg1") == "SUBSCRIBE SUCCESS":
                logging.info(f"구독 성공: {trid} ({tr_key})")
            elif trid in ["H0STCNI0", "H0STCNI9"]:
                self.aes_key = json_obj["body"]["output"].get("key")
                self.aes_iv = json_obj["body"]["output"].get("iv")

    def format_trade_string(self, raw: str) -> str:
        """
        체결 데이터 문자열을 사람이 읽기 쉬운 요약 문자열로 변환합니다.
        """
        values = raw.split('^')
        code = values[0]
        time = values[1]
        hms = f"{time[:2]}:{time[2:4]}:{time[4:]}"
        try:
            price = int(values[2])
            diff = int(values[4])
            rate = float(values[5])
            strength = float(values[18])
            total_val = float(values[14]) / 1e8
            name = self.stock_names.get(code, "")
            label = f"[{code} | {name}]" if name and name != code else f"[{code}]"
            rsi = self.compute_RSI_candles(code)
            macd = self.compute_MACD_candles(code)
            rsi_str = f" | RSI: {rsi:.2f}" if rsi is not None else ""
            macd_str = f" | MACD: {macd:+.2f}" if macd is not None else ""
            return (
                f"{label} {hms} 체결가 {price:>8,}원 ({diff:+,}, {rate:+.2f}%) | "
                f"누적 {total_val:>8.1f}억 | 강도 {strength:>6.2f}%{rsi_str}{macd_str}"
            )
        except Exception as e:
            name = self.stock_names.get(code, "")
            label = f"[{code} | {name}]" if name and name != code else f"[{code}]"
            return f"{label} {hms} 체결 정보 파싱 실패: {e}"

    def stocksigningnotice(self, data, key, iv):
        """
        체결통보 메시지 처리 (AES256 복호화).
        필요한 경우 여기에 추가 처리를 할 수 있습니다.
        """
        decrypted = self.aes_cbc_base64_dec(key, iv, data)
        # 체결통보 출력 제거
        pass

    @staticmethod
    def aes_cbc_base64_dec(key, iv, cipher_text):
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))

    def load_historical_data(self):
        # fetch_ohlcv_dataframe을 이용하여 과거 데이터를 불러옵니다.
        for code in self.stock_codes:
            try:
                df = self.stock_api.get_daily_price(code)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # 'stck_cntg_hour' 컬럼을 datetime으로 변환하여 'time'으로 사용
                    df['time'] = pd.to_datetime(df['stck_bsop_date'].astype(str) + df['stck_cntg_hour'].astype(str),
                                                format='%Y%m%d%H%M%S', errors='coerce')
                    # 체결가는 'stck_prpr'
                    for _, row in df.iterrows():
                        # row['time']는 datetime, row['stck_prpr']는 체결가 (문자열일 수 있으므로 float 형변환)
                        t = row['time']
                        if pd.isnull(t):
                            continue
                        close_price = float(row['stck_clpr'])
                        # 체결강도는 과거 데이터에서는 없으므로 None 처리
                        self.trade_history[code].append((t, close_price, None))
            except Exception as e:
                logging.error(f"{code} 과거 데이터 로딩 오류: {e}")

    def fetch_stock_names(self):
        """
        REST API를 호출하여 각 종목의 이름(종목명)을 가져와 stock_names에 저장합니다.
        """
        for ticker in self.stock_codes:
            try:
                # 이미 이름이 있고 값이 비어있지 않은 경우만 조회
                if ticker not in self.stock_names or not self.stock_names[ticker]:
                    res = self.stock_api.get_stock_info(ticker)
                    stock_name = ticker  # fallback
                    if isinstance(res, pd.DataFrame):
                        if not res.empty and "prdt_name" in res.columns:
                            stock_name = res["prdt_name"].iloc[0]
                    # 무조건 self.stock_names[ticker]에 할당
                    self.stock_names[ticker] = stock_name
            except Exception as e:
                logging.error(f"종목명 REST 호출 오류: {e}")

    # 새롭게 추가: 각 종목의 당일 시가만 조회하여 open_prices에 저장
    def fetch_open_prices(self):
        for ticker in self.stock_codes:
            try:
                res = self.stock_api.get_stock_price(ticker)['output']
                open_price_str = res.get("stck_oprc", "").strip()
                if open_price_str:
                    self.open_prices[ticker] = float(open_price_str)
            except Exception as e:
                logging.error(f"시가 데이터 호출 오류 ({ticker}): {e}")

    def unsubscribe_all(self):
        """
        웹소켓의 모든 종목 구독을 해제하는 메시지를 전송합니다.
        (여기서는 "H0STCNT0_UNSUB"라는 tr_id를 사용합니다. 실제 API 명세에 따라 수정하세요.)
        """
        if not hasattr(self, "ws") or not self.ws:
            return
        for ticker in self.stock_codes:
            senddata_unsub = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STCNT0_UNSUB",  # 구독 해제 메시지 (예시)
                        "tr_key": ticker
                    }
                }
            }
            # 비동기로 전송 (여러 메시지를 병렬로 보내기 위함)
            asyncio.create_task(self.ws.send(json.dumps(senddata_unsub)))

    async def poll_final_price(self):
        """
        장 종료(15:20 이후)엔 최초 한 번 웹소켓 구독을 해제한 후, 
        REST API로 최신 종가를 주기적으로 업데이트합니다.
        """
        from datetime import datetime, time
        unsubscribed = False
        while True:
            now_time = datetime.now().time()
            if now_time >= time(15, 20):
                if not unsubscribed:
                    self.unsubscribe_all()
                    unsubscribed = True
                for ticker in self.stock_codes:
                    try:
                        res = self.stock_api.get_stock_price(ticker)
                        final_price_str = res.get("stck_prpr", "").strip()
                        if final_price_str:
                            final_price = float(final_price_str)
                            trade_time = datetime.now().strftime('%H%M%S')
                            self.latest_trade[ticker] = f"{ticker}^{trade_time}^{final_price}"
                    except Exception as e:
                        logging.error("최종 가격 REST 호출 오류:", e)
                await asyncio.sleep(1)  # 장 종료 시 1초 대기
            else:
                unsubscribed = False  # 장중이면 해제 플래그 초기화
                await asyncio.sleep(0.2)
    async def monitor_esc(self):
        """
        ESC키 입력 시 웹소켓 종료 및 프로그램 종료
        (Windows에서 msvcrt 모듈 이용)
        """
        try:
            import msvcrt
        except ImportError:
            # Windows가 아닌 경우 대체 구현 필요
            return
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC 키
                    logging.info("ESC 키 입력 감지. 웹소켓 구독 종료 및 프로그램 종료합니다.")
                    if hasattr(self, "ws") and self.ws:
                        await self.ws.close()
                    import sys
                    sys.exit(0)
            await asyncio.sleep(0.1)
    async def monitor_exit(self):
        """
        ESC 키(Windows: msvcrt, 비 Windows: sys.stdin) 또는 ctrl+d(빈 문자열 입력)를 감지하면
        웹소켓 연결을 종료하고 프로그램을 종료합니다.
        """
        try:
            # Windows용: msvcrt 모듈 사용
            import msvcrt
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\x1b':  # ESC 키
                        logging.info("ESC 키 입력 감지. 웹소켓 구독 종료 및 프로그램 종료합니다.")
                        if hasattr(self, "ws") and self.ws:
                            await self.ws.close()
                        import sys
                        sys.exit(0)
                await asyncio.sleep(0.1)
        except ImportError:
            # 비 Windows용: select()를 사용하여 non-blocking sys.stdin 감지 (ctrl+d는 빈 문자열)
            while True:
                dr, dw, de = select.select([sys.stdin], [], [], 0)
                if dr:
                    ch = sys.stdin.read(1)
                    if ch == '\x1b' or ch == '':  # ESC 또는 ctrl+d 감지
                        logging.info("ESC 또는 ctrl+d 감지. 웹소켓 구독 종료 및 프로그램 종료합니다.")
                        if hasattr(self, "ws") and self.ws:
                            await self.ws.close()
                        sys.exit(0)
                await asyncio.sleep(0.1)
    def display_live_trade(self, code, formatted_str):
        print(formatted_str)
        
    def load_historical_data_for_stock(self, ticker):
        try:
            df = self.stock_api.get_daily_price(ticker)
            if df is not None and not df.empty:
                df['time'] = pd.to_datetime(df['stck_bsop_date'].astype(str) + df['stck_cntg_hour'].astype(str), format='%Y%m%d%H%M%S', errors='coerce')
                for _, row in df.iterrows():
                    t = row['time']
                    if pd.isnull(t):
                        continue
                    close_price = float(row['stck_clpr'])
                    self.trade_history[ticker].append((t, close_price, None))
        except Exception as e:
            logging.error(f"{ticker} historical data 로드 오류: {e}")

    def should_exit(self, stock_code):
        try:
            trade = self.latest_trade.get(stock_code)
            if not trade:
                return False
            close_price = float(trade.split('^')[2])
            if stock_code not in self.purchase_prices:
                return False
            avg_price, quantity = self.purchase_prices[stock_code]
            profit_ratio = (close_price - avg_price) / avg_price * 100
            
            # 수익률 체크
            if profit_ratio < 3:
                return False
                
            # RSI 체크
            rsi_now = self.compute_RSI_candles(stock_code)
            rsi_prev = self.prev_indicators.get(stock_code, (None, None))[0]
            
            # RSI 하락 체크
            rsi_falling = rsi_prev is not None and rsi_now is not None and rsi_now < rsi_prev
            
            # 체결강도 체크
            strength_series = self.compute_trade_strength_candle(stock_code)
            strength_falling = False
            if len(strength_series) >= 3:
                recent_strength = [val for _, val in strength_series[-3:]]
                strength_falling = recent_strength[-1] < recent_strength[0]
            
            # ATR 체크
            atr = self.compute_ATR(stock_code)
            atr_high = atr and atr >= 0.5
            
            # 디버그 로그
            logging.info(f"\n[EXIT CHECK] {stock_code}")
            logging.info(f"수익률: {profit_ratio:.2f}%")
            logging.info(f"RSI: {rsi_now:.1f} (이전: {rsi_prev:.1f if rsi_prev else 'N/A'})")
            if len(strength_series) >= 3:
                logging.info(f"체결강도: {recent_strength[-1]:.1f} (3분전: {recent_strength[0]:.1f})")
            logging.info(f"ATR: {atr:.2f if atr else 'N/A'}")
            
            # 모든 조건 만족 시 익절 신호
            if rsi_falling and strength_falling and atr_high:
                logging.info(f"[TRIGGER] 익절 조건 만족: {stock_code}")
                logging.info(f"- 수익률: {profit_ratio:.2f}%")
                logging.info(f"- RSI 하락: {rsi_prev:.1f} -> {rsi_now:.1f}")
                logging.info(f"- 체결강도 하락: {recent_strength[0]:.1f} -> {recent_strength[-1]:.1f}")
                logging.info(f"- ATR: {atr:.2f}")
                return True
                
            # 이전 RSI 저장
            self.prev_indicators[stock_code] = (rsi_now, None)
            
        except Exception as e:
            logging.error(f"should_exit({stock_code}) 실패: {e}")
        return False

    def execute_exit_orders(self):
        from ..account.api import AccountAPI
        account_api = AccountAPI(client=self.client, account_info=self.account_info)

        for code in self.stock_codes:
            if self.should_exit(code):
                try:
                    avg_price, qty = self.purchase_prices.get(code, (0, 0))
                    if qty <= 0:
                        continue
                    logging.info(f"[ORDER] {code}: 시장가 매도")
                    logging.info(f"- 수량: {qty:,}주")
                    logging.info(f"- 매입가: {avg_price:,.2f}원")
                    res = account_api.order_stock_cash(
                        ticker=code,
                        price="0",
                        quantity=str(qty),
                        order_type="01"
                    )
                    logging.info(f"[INFO] 응답: {res.get('msg1', '') if res else '응답 없음'}")
                except Exception as e:
                    logging.error(f"주문 실패: {code}, {e}")

    async def exit_watch_loop(self):
        while True:
            try:
                self.execute_exit_orders()
            except Exception as e:
                logging.error(f"exit_watch_loop: {e}")
            await asyncio.sleep(5)

    def is_ws_active(self, timeout_seconds=60):
        """
        Returns True if the last WebSocket receive was within timeout_seconds.
        """
        return (datetime.now() - self.last_ws_recv_time).total_seconds() < timeout_seconds

    def load_initial_balance(self):
        """
        초기 잔고 정보를 한 번만 로드
        """
        from ..account.api import AccountAPI
        account_api = AccountAPI(client=self.client, account_info=self.account_info)
        balance = account_api.get_account_balance()
        output1 = balance.get('output1')
        if output1 is not None and output1:
            self.balance_info = pd.DataFrame(output1)
            # 초기 수금 저장
            if 'output2' in balance and balance.get('output2'):
                self.initial_cash_balance = int(balance['output2'][0]['dnca_tot_amt'])
            return True
        return False

    def update_price_and_indicators(self):
        """
        현재가와 기술적 지표만 업데이트하여 표시
        """
        if self.balance_info is None:
            return

        # 1분마다 잔고 정보 업데이트
        now = datetime.now()
        if (now - self.last_balance_check).total_seconds() >= 60:
            from ..account.api import AccountAPI
            account_api = AccountAPI(client=self.client, account_info=self.account_info)
            balance = account_api.get_account_balance()
            if balance and balance.get('output1'):
                self.balance_info = pd.DataFrame(balance['output1'])
                # 예수금도 함께 업데이트
                if 'output2' in balance and balance.get('output2'):
                    self.initial_cash_balance = int(balance['output2'][0]['dnca_tot_amt'])
            self.last_balance_check = now

        # 화면 클리어
        os.system('cls' if os.name in ('nt', 'dos') else 'clear')
        
        print("\n========== [보유 종목 잔고] ==========")
        print(f"{'종목명':<12} {'코드':<8} {'수량':>8} {'매입가':>12} {'현재가':>12} {'평가금액':>14} {'손익':>12} {'수익률':>8} {'RSI':>6} {'MACD':>8}")
        print("-" * 100)
        
        total_eval_amt = 0
        total_pfls_amt = 0
        total_pchs_amt = 0
        
        for _, item in self.balance_info.iterrows():
            code = item['pdno']
            name = item['prdt_name']
            quantity = int(item['hldg_qty'])
            
            # 수량이 0인 종목은 건너뛰기
            if quantity <= 0:
                continue
                
            avg_price = float(item['pchs_avg_pric'])
            
            # 현재가 업데이트 (웹소켓 데이터 사용)
            trade = self.latest_trade.get(code)
            if trade:
                current_price = float(trade.split('^')[2])
                eval_amt = int(current_price * quantity)  # 정수로 변환
                eval_pfls_amt = int(eval_amt - (avg_price * quantity))  # 정수로 변환
                rate_of_change = ((current_price - avg_price) / avg_price * 100)
            else:
                # 웹소켓 데이터가 없는 경우 잔고 데이터 사용
                current_price = float(item['prpr'])
                eval_amt = int(item['evlu_amt'])
                eval_pfls_amt = int(item['evlu_pfls_amt'])
                rate_of_change = float(item['evlu_pfls_rt'])
            
            # 총액 계산
            total_eval_amt += eval_amt
            total_pfls_amt += eval_pfls_amt
            total_pchs_amt += int(avg_price * quantity)
            
            # 기술적 지표 계산
            rsi = self.compute_RSI_candles(code)
            macd = self.compute_MACD_candles(code)
            rsi_str = f"{rsi:.1f}" if rsi is not None else "N/A"
            macd_str = f"{macd:+.2f}" if macd is not None else "N/A"
            
            print(f"{name:<12} {code:<8} {quantity:>8,} {avg_price:>12,.2f} {current_price:>12,.2f} {eval_amt:>14,d} {eval_pfls_amt:>12,d} {rate_of_change:>7.2f}% {rsi_str:>6} {macd_str:>8}")
        
        print("-" * 100)
        # 전체 수익률 계산
        total_profit_rate = (total_pfls_amt / total_pchs_amt * 100) if total_pchs_amt > 0 else 0
        
        # 예수금은 저장된 값 사용
        cash_amt = self.initial_cash_balance if self.initial_cash_balance is not None else 0
        
        print(f"총 평가금액: {total_eval_amt:,d}원 | 총 손익금액: {total_pfls_amt:,d}원 | 전체 수익률: {total_profit_rate:.2f}%")
        print(f"예수금 잔액: {cash_amt:,d}원 | 총 자산: {total_eval_amt + cash_amt:,d}원")
        print("=" * 100 + "\n")

    def display_balance_info(self):
        """
        초기 잔고 정보를 표시하고, 이후에는 update_price_and_indicators를 호출
        """
        if self.balance_info is None:
            if not self.load_initial_balance():
                logging.error("잔고 정보를 가져오지 못했습니다.")
                return
        self.update_price_and_indicators()

    async def connect(self):
        """
        웹소켓 순수 체결정보(H0STCNT0)와 호가창(H0STASP0) 구독만 테스트하는 간소화 버전.
        """
        self.get_approval()
        logging.info("\n" + "="*50)
        logging.info("[INFO] 실시간 체결 정보 표시 시작")
        logging.info("="*50 + "\n")
        
        # 초기 데이터 로드
        self.load_historical_data()
        self.fetch_stock_names()
        self.fetch_open_prices()
        self.load_initial_balance()  # 초기 잔고 정보 로드
        self.display_balance_info()  # 초기 화면 표시

        from datetime import datetime, time as dt_time
        import asyncio
        import sys

        while True:  # 자동 재연결을 위한 외부 루프
            try:
                async with websockets.connect(self.url, ping_interval=30, ping_timeout=30) as websocket:
                    self.ws = websocket
                    logging.info("\n" + "-"*50)
                    logging.info("[INFO] 웹소켓 연결 성공. 구독 요청 시작...")
                    logging.info("-"*50 + "\n")
                    sys.stdout.flush()
                    
                    # 지수 구독 (활성화된 경우)
                    if self.enable_index:
                        index_codes = ['0001', '1001', '2001']  # KOSPI, KOSDAQ, KOSPI200
                        for index_code in index_codes:
                            index_name = self.get_index_name(index_code)
                            logging.info(f"[INFO] {index_name}({index_code}) 지수 구독 요청 중...")
                            sys.stdout.flush()
                            senddata_index = {
                                "header": {
                                    "approval_key": self.approval_key,
                                    "custtype": "P",
                                    "tr_type": "1",
                                    "content-type": "utf-8"
                                },
                                "body": {
                                    "input": {
                                        "tr_id": "H0IF1000",
                                        "tr_key": index_code
                                    }
                                }
                            }
                            await websocket.send(json.dumps(senddata_index))
                            logging.info(f"[INFO] {index_name} 지수 구독 요청 완료")
                            sys.stdout.flush()
                            await asyncio.sleep(0.1)
                    
                    # 종목별 구독 요청 전송
                    for stock_code in self.stock_codes:
                        logging.info(f"[INFO] {stock_code} 구독 요청 중...")
                        sys.stdout.flush()
                        
                        # 체결정보(H0STCNT0) 구독
                        senddata_trade = {
                            "header": {
                                "approval_key": self.approval_key,
                                "custtype": "P",
                                "tr_type": "1",
                                "content-type": "utf-8"
                            },
                            "body": {
                                "input": {
                                    "tr_id": "H0STCNT0",
                                    "tr_key": stock_code
                                }
                            }
                        }
                        await websocket.send(json.dumps(senddata_trade))
                        logging.info(f"[INFO] {stock_code} 체결정보 구독 요청 완료")
                        sys.stdout.flush()
                        
                        # 호가창(H0STASP0) 구독 (활성화된 경우)
                        if self.enable_ask_bid:
                            senddata_hoga = {
                                "header": {
                                    "approval_key": self.approval_key,
                                    "custtype": "P",
                                    "tr_type": "1",
                                    "content-type": "utf-8"
                                },
                                "body": {
                                    "input": {
                                        "tr_id": "H0STASP0",
                                        "tr_key": stock_code
                                    }
                                }
                            }
                            await websocket.send(json.dumps(senddata_hoga))
                            logging.info(f"[INFO] {stock_code} 호가창 구독 요청 완료")
                            sys.stdout.flush()
                            
                        # 프로그램매매(H0GSCNT0) 구독 (활성화된 경우)
                        if self.enable_program_trading:
                            senddata_program = {
                                "header": {
                                    "approval_key": self.approval_key,
                                    "custtype": "P",
                                    "tr_type": "1",
                                    "content-type": "utf-8"
                                },
                                "body": {
                                    "input": {
                                        "tr_id": "H0GSCNT0",
                                        "tr_key": stock_code
                                    }
                                }
                            }
                            await websocket.send(json.dumps(senddata_program))
                            logging.info(f"[INFO] {stock_code} 프로그램매매 구독 요청 완료")
                            sys.stdout.flush()
                            
                        await asyncio.sleep(0.1)  # 구독 요청 간 약간의 딜레이
                    
                    logging.info("\n" + "-"*50)
                    logging.info("[INFO] 모든 구독 요청 완료. 데이터 수신 대기 중...")
                    logging.info("-"*50 + "\n")
                    sys.stdout.flush()

                    while True:
                        # 장 종료 후(15:30)에는 데이터 수신을 일시 중단하고, 다음 거래일 9:00까지 대기
                        now = datetime.now()
                        if now.time() > dt_time(15, 30):
                            logging.info("[INFO] 장 종료 감지됨. 다음 거래일까지 대기 중...")
                            sys.stdout.flush()
                            while True:
                                await asyncio.sleep(30)
                                if datetime.now().time() < dt_time(9, 0):
                                    break
                            continue
                        try:
                            data = await asyncio.wait_for(websocket.recv(), timeout=30)
                            self.last_ws_recv_time = datetime.now()
                            
                            # PINGPONG 메시지는 처리하지 않음
                            if 'PINGPONG' in data:
                                continue
                                
                            # 구독 성공 메시지 확인
                            if 'SUBSCRIBE SUCCESS' in data:
                                continue
                                
                            # 체결 데이터 처리
                            self.handle_message(data)
                            
                        except asyncio.TimeoutError:
                            try:
                                pong_waiter = await websocket.ping()
                                await asyncio.wait_for(pong_waiter, timeout=10)
                                continue
                            except Exception as e:
                                logging.warning(f"ping/pong 오류: {e}")
                                sys.stdout.flush()
                                raise e
                                
            except Exception as e:
                logging.warning(f"웹소켓 연결 문제 발생: {e}. 자동 재연결 시도 중...")
                sys.stdout.flush()
                await asyncio.sleep(5)
