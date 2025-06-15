import logging
from typing import Dict, List, Optional, Any
from ..core.client import KISClient, API_ENDPOINTS

"""
program_trade.py - 프로그램 매매 API 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 프로그램 매매 시간대별 추이 조회
- 프로그램 매매 일별 요약 조회
- 프로그램 매매 기간별 상세 조회

✅ 의존:
- client.py: API 클라이언트

🔗 연관 모듈:
- agent.py: KIS API 통합 에이전트

💡 사용 예시:
program = ProgramTradeAPI(client)
trend = program.get_program_trade_hourly_trend(code="005930")
"""

class ProgramTradeAPI:
    def __init__(self, client: KISClient):
        self.client = client

    def get_program_trade_hourly_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """프로그램 매매 시간대별 추이 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock",
                tr_id="FHPPG04650101",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code
                }
            )
        except Exception as e:
            logging.error(f"프로그램 매매 시간대별 추이 조회 실패: {e}")
            return None

    def get_program_trade_daily_summary(self, code: str, date: str) -> Optional[Dict[str, Any]]:
        """프로그램 매매 일별 요약 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock-daily",
                tr_id="FHPPG04650200",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code,
                    "FID_INPUT_DATE_1": date
                }
            )
        except Exception as e:
            logging.error(f"프로그램 매매 일별 요약 조회 실패: {e}")
            return None

    def get_program_trade_period_detail(self, code: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """프로그램 매매 기간별 상세 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/program-trade-by-stock-period",
                tr_id="FHPPG04600000",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": code,
                    "FID_INPUT_DATE_1": start_date,
                    "FID_INPUT_DATE_2": end_date
                }
            )
        except Exception as e:
            logging.error(f"프로그램 매매 기간별 상세 조회 실패: {e}")
            return None

    def get_pgm_trade(self, code: str, ref_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
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

# 주석 처리된 get_program_trade_summary는 삭제 또는 실제 API 명세에 맞게 재구현 필요
# class ProgramTradeAPI:
# ... (기존 get_program_trade_detail -> get_program_trade_period_detail 로 변경)
# ... (get_program_trade_ratio -> get_pgm_trade 로 변경)
