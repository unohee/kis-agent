from typing import Optional, Dict, Any
from ..core.client import KISClient, API_ENDPOINTS
"""
program_trade_api.py - 프로그램 매매 정보 조회 전용 모듈

한국투자증권 API의 프로그램 매매 정보 조회 기능을 제공하는 모듈입니다.

이 모듈은 한국투자증권 OpenAPI를 통해 프로그램 매매 관련 정보를 조회합니다:
- 시간별 프로그램 매매 추이 (실시간 델타 등) - 종목별프로그램매매추이(체결) / FHPPG04650101
- 일별 프로그램 매매 집계 (당일 총 매수/매도량 등) - 종목별 프로그램매매추이(일별) / FHPPG04650200
- 기간별 프로그램 매매 상세 (차익/비차익 매매 내역)

✅ 의존:
- kis_core.KISClient: API 호출 핸들링

🔗 연관 모듈:
- agent_stock.py: 종목 시세 및 주문 처리
- account_api.py: 계좌 상태 및 주문 가능 금액 확인
- strategy_trigger.py: 실매수 조건 트리거 및 전략 연결

💡 사용 예시:
client = KISClient()
pgm_api = ProgramTradeAPI(client)
hourly_trend = pgm_api.get_program_trade_hourly_trend("005930")
daily_summary = pgm_api.get_program_trade_daily_summary("005930", "20240726")
"""


class ProgramTradeAPI:
    """
    한국투자증권 API의 프로그램 매매 정보 조회 기능을 제공하는 클래스입니다.

    이 클래스는 시간별/일별/기간별 프로그램 매매 정보를 조회하는 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신을 담당하는 클라이언트

    Example:
        >>> client = KISClient()
        >>> pgm_api = ProgramTradeAPI(client)
        >>> hourly_trend = pgm_api.get_program_trade_hourly_trend("005930")
        >>> daily_summary = pgm_api.get_program_trade_daily_summary("005930", "20240726")
    """

    def __init__(self, client, account_info=None):
        """
        ProgramTradeAPI를 초기화합니다.

        Args:
            client (KISClient): API 통신을 담당하는 클라이언트
            account_info (dict, optional): 계좌 정보
        """
        self.client = client
        self.account_info = account_info or {}

    def get_program_trade_hourly_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """
        종목별프로그램매매추이(체결) - 시간별 프로그램 매매 추이를 조회합니다.

        Args:
            code (str): 종목 코드 (예: "005930")

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
                - 성공 시: 시간별 프로그램 매매 추이 정보를 포함한 응답 데이터
                - 실패 시: None

        Note:
            이 API는 특정 '일자'를 지정하지 않고 호출 시, 당일의 시간대별 프로그램 매매 현황을 반환합니다.
            주요 응답 필드 (output 리스트의 각 항목):
            - bsop_hour: 영업 시간 (HHMMSS)
            - whol_ntby_vol_icdc: 전체 순매수 거래량 증감 (이전 시간 대비 델타)

        Example:
            >>> api.get_program_trade_hourly_trend("005930")
        """
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock",
            tr_id="FHPPG04650101", # 종목별프로그램매매추이(체결)
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
        )

    def get_program_trade_daily_summary(self, code: str, date_str: str) -> Optional[Dict[str, Any]]:
        """
        종목별 프로그램매매추이(일별) - 일별 프로그램 매매 집계를 조회합니다.

        Args:
            code (str): 종목 코드 (예: "005930")
            date_str (str): 조회 일자 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
                - 성공 시: 일별 프로그램 매매 집계 정보를 포함한 응답 데이터
                - 실패 시: None

        Note:
            이 API는 특정 '일자'를 지정하여 해당일의 프로그램 매매 총 집계 현황을 반환합니다.
            주요 응답 필드 (output 리스트의 첫 번째 항목 예상):
            - stck_bsop_date: 주식 영업 일자
            - prgr_shnu_vol: 프로그램 순매수 체결 수량 (일별 총계)
            - prgr_seln_vol: 프로그램 순매도 체결 수량 (일별 총계)

        Example:
            >>> api.get_program_trade_daily_summary("005930", "20240726")
        """
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock-daily",
            tr_id="FHPPG04650200", # 종목별 프로그램매매추이(일별)
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": date_str # 기준일자 (YYYYMMDD)
            }
        )

    def get_program_trade_period_detail(self, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """
        프로그램 매매 일별 상세 (기간별)를 조회합니다.

        Args:
            start_date (str): 시작 일자 (YYYYMMDD 형식)
            end_date (str): 종료 일자 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
                - 성공 시: 기간별 프로그램 매매 상세 정보를 포함한 응답 데이터
                - 실패 시: None

        Example:
            >>> api.get_program_trade_period_detail("20240701", "20240726")
        """
        return self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/comp-program-trade-daily",
            tr_id="FHPPG04600000", # 프로그램매매종합추이(기간)
            params={
                "FID_MRKT_CLS_CODE": "", # 시장 분류 코드 (전체는 공백)
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_COND_MRKT_DIV_CODE": "J" # J: 주식
            }
        )

    def get_pgm_trade(self, code: str, ref_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        프로그램 매매 정보를 종합적으로 조회합니다.

        Args:
            code (str): 종목 코드 (예: "005930")
            ref_date (Optional[str]): 기준 일자 (YYYYMMDD 형식, 기본값: 현재 일자)

        Returns:
            Optional[Dict[str, Any]]: 프로그램 매매 정보
                - net29: 29일 누적 순매수량
                - today: 당일 순매수량
                - today_ratio: 당일 매수 비율
                - program_today_volume: 당일 프로그램 매매량
                - program_ratio: 프로그램 매매 비율
                - net29_amt: 29일 누적 순매수금액
                - today_amt: 당일 순매수금액
                - today_amt_ratio: 당일 순매수금액 비율
                - program_day_shnu_vol: 당일 프로그램 매수량
                - program_day_seln_vol: 당일 프로그램 매도량
                - program_day_total_volume: 당일 프로그램 총 거래량
                - program_day_buy_ratio: 당일 프로그램 매수 비율

        Note:
            최대 5번까지 재시도하며, 각 시도 간 0.05~0.15초의 랜덤한 대기 시간을 가집니다.

        Example:
            >>> api.get_pgm_trade("005930", "20240726")
        """
        if ref_date is None:
            from datetime import datetime
            ref_date = datetime.now().strftime("%Y%m%d")

        import time
        import random

        max_retries = 5
        res = None
        for attempt in range(max_retries):
            res = self.get_program_trade_daily_summary(code, ref_date)
            if res and isinstance(res, dict) and 'output' in res and isinstance(res['output'], list):
                break
            time.sleep(random.uniform(0.05, 0.15))  # 초당 7~20개 사이
        if not res or 'output' not in res or not isinstance(res['output'], list) or len(res['output']) == 0:
            return None

        rows = res['output']
        target_row = None
        net29_qty = 0
        net29_amt = 0

        for row in rows:
            date = row.get('stck_bsop_date')
            if date == ref_date:
                target_row = row
            elif date and date < ref_date:
                net29_qty += int(row.get('whol_smtn_ntby_qty', 0))
                net29_amt += abs(int(row.get('whol_smtn_ntby_tr_pbmn', 0)))

        if not target_row:
            return None

        try:
            today_net_qty = int(target_row.get('whol_smtn_ntby_qty', 0))
            today_net_amt = int(target_row.get('whol_smtn_ntby_tr_pbmn', 0))
            shnu_vol = int(target_row.get('whol_smtn_shnu_vol', 0))
            seln_vol = int(target_row.get('whol_smtn_seln_vol', 0))
        except ValueError:
            return None

        total_vol = shnu_vol + seln_vol
        buy_ratio = (shnu_vol / total_vol * 100) if total_vol > 0 else None

        return {
            'net29': net29_qty,
            'today': today_net_qty,
            'today_ratio': round(buy_ratio, 2) if buy_ratio is not None else None,
            'program_today_volume': today_net_qty,
            'program_ratio': round(buy_ratio, 2) if buy_ratio is not None else None,
            'net29_amt': net29_amt,
            'today_amt': today_net_amt,
            'today_amt_ratio': round(today_net_amt / net29_amt * 100, 2) if net29_amt else None,
            'program_day_shnu_vol': shnu_vol,
            'program_day_seln_vol': seln_vol,
            'program_day_total_volume': total_vol,
            'program_day_buy_ratio': round(buy_ratio, 2) if buy_ratio is not None else None
        }

    # 기존 인터페이스 호환용 메서드
    def get_program_trade_summary(self, code: str, ref_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """get_pgm_trade의 기존 명칭을 유지하기 위한 래퍼"""
        return self.get_pgm_trade(code, ref_date)

# 주석 처리된 get_program_trade_summary는 삭제 또는 실제 API 명세에 맞게 재구현 필요
# class ProgramTradeAPI:
# ... (기존 get_program_trade_detail -> get_program_trade_period_detail 로 변경)
# ... (get_program_trade_ratio -> get_pgm_trade 로 변경)\n# 기존 호환성을 위해 별칭 제공
ProgramTrade = ProgramTradeAPI
