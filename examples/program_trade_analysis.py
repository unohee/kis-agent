#!/usr/bin/env python3
"""
프로그램 매매 종합 분석 스크립트

이 스크립트는 PyKIS의 기본 API를 활용하여 프로그램 매매 데이터를 분석하고
종합적인 인사이트를 제공합니다.

기능:
- 29일 누적 순매수량 계산
- 당일 프로그램 매매 비율 분석
- 매수/매도 비중 계산
- 프로그램 매매 트렌드 분석
"""

import sys

sys.path.append('..')

import random
import time
from datetime import datetime
from typing import Any, Dict, Optional

from pykis.core.agent import Agent


class ProgramTradeAnalyzer:
    """프로그램 매매 데이터 분석기"""

    def __init__(self, agent: Optional[Agent] = None):
        """
        분석기 초기화

        Args:
            agent: PyKIS Agent 인스턴스 (None이면 자동 생성)
        """
        self.agent = agent or Agent()

    def analyze_program_trade(self, code: str, ref_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        프로그램 매매 정보를 종합적으로 분석합니다.

        Args:
            code (str): 종목 코드 (예: "005930")
            ref_date (Optional[str]): 기준 일자 (YYYYMMDD 형식, 기본값: 현재 일자)

        Returns:
            Optional[Dict[str, Any]]: 프로그램 매매 분석 결과
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

        Example:
            >>> analyzer = ProgramTradeAnalyzer()
            >>> result = analyzer.analyze_program_trade("005930", "20240726")
        """
        if ref_date is None:
            ref_date = datetime.now().strftime("%Y%m%d")

        # 최대 5번까지 재시도하며 데이터 조회
        max_retries = 5
        res = None
        for _attempt in range(max_retries):
            res = self.agent.get_program_trade_daily_summary(code, ref_date)
            if res and isinstance(res, dict) and 'output' in res and isinstance(res['output'], list):
                break
            time.sleep(random.uniform(0.05, 0.15))  # 초당 7~20개 사이

        if not res or 'output' not in res or not isinstance(res['output'], list) or len(res['output']) == 0:
            return None

        return self._calculate_program_trade_metrics(res['output'], ref_date)

    def _calculate_program_trade_metrics(self, rows: list, ref_date: str) -> Optional[Dict[str, Any]]:
        """
        프로그램 매매 지표 계산 (내부 메서드)

        Args:
            rows: API 응답 데이터
            ref_date: 기준 일자

        Returns:
            계산된 프로그램 매매 지표
        """
        target_row = None
        net29_qty = 0
        net29_amt = 0

        # 기준일 데이터 찾기 및 29일 누적 계산
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

    def get_program_trade_trend(self, code: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        프로그램 매매 트렌드 분석

        Args:
            code: 종목 코드
            days: 분석 기간 (일)

        Returns:
            트렌드 분석 결과
        """
        # 여기에 추가 분석 로직 구현 가능
        pass

    def compare_program_trade(self, codes: list, ref_date: Optional[str] = None) -> Dict[str, Any]:
        """
        여러 종목의 프로그램 매매 비교 분석

        Args:
            codes: 종목 코드 리스트
            ref_date: 기준 일자

        Returns:
            비교 분석 결과
        """
        results = {}
        for code in codes:
            results[code] = self.analyze_program_trade(code, ref_date)
        return results


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔬 프로그램 매매 종합 분석 스크립트")
    print("=" * 60)

    # 분석기 초기화
    analyzer = ProgramTradeAnalyzer()

    # 테스트 종목들
    test_stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, 네이버

    print("\n 개별 종목 분석:")
    for stock in test_stocks:
        print(f"\n🏢 종목: {stock}")
        result = analyzer.analyze_program_trade(stock)
        if result:
            print(f"    29일 누적: {result['net29']:,}주")
            print(f"    당일 순매수: {result['today']:,}주")
            print(f"    당일 매수비율: {result['today_ratio']}%")
            print(f"    총 거래량: {result['program_day_total_volume']:,}주")
        else:
            print("    데이터 조회 실패")

    print("\n 비교 분석:")
    comparison = analyzer.compare_program_trade(test_stocks)
    for code, data in comparison.items():
        if data:
            print(f"   {code}: 매수비율 {data['today_ratio']}%, 순매수 {data['today']:,}주")

    print("\n 분석 완료!")


if __name__ == "__main__":
    main()
