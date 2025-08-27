"""
Stock Investor API - 투자자별 매매 정보 전용 모듈

투자자 유형별 매매 동향과 거래원 정보를 담당
- 투자자별 순매수 동향
- 거래원별 매매 정보  
- 외국인 매매 추이
"""

from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import logging
from ..core.client import KISClient, API_ENDPOINTS
from ..core.base_api import BaseAPI
from datetime import datetime


class StockInvestorAPI(BaseAPI):
    """투자자별 매매 정보 조회 전용 API 클래스"""

    def get_stock_investor(self, ticker: str = '', retries: int = 10, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """투자자별 매매동향 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "UN",
            "FID_INPUT_ISCD": ticker,
        }
        return self._make_request_dataframe(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR'],
            tr_id="FHKST01010900",
            params=params,
            retries=retries
        )

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """거래원별 매매 정보 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_MEMBER'],
            tr_id="FHKST01010600",
            params={
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_INPUT_ISCD": ticker,
            }
        )

    def get_member_transaction(self, code: str, mem_code: str) -> Optional[Dict[str, Any]]:
        """특정 거래원의 매매 내역 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_MEMBER'],
            tr_id="FHKST01010600",
            params={
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_MEM_CODE": mem_code
            }
        )

    def get_frgnmem_pchs_trend(self, code: str, date: str) -> Optional[Dict[str, Any]]:
        """외국인 매수 추이 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['FRGNMEM_PCHS_TREND'],
            tr_id="FHKST644400C0",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": date
            }
        )

    def get_foreign_broker_net_buy(self, code: str, foreign_brokers=None, date: str = None) -> Optional[tuple]:
        """
        거래원 정보를 활용해 외국계 증권사의 순매수(매수-매도) 합계를 집계합니다.
        
        Args:
            code: 종목코드
            foreign_brokers: 외국계 브로커명 리스트 (사용되지 않음, 자동 패턴 매칭)
            date: 조회일자(YYYYMMDD), None이면 당일, 특정 날짜면 해당 날짜 데이터 조회
            
        Returns:
            tuple: (순매수량, 상세정보 dict) 또는 None
                - 순매수량: 외국계 증권사 순매수량 (매수-매도)
                - 상세정보: {'brokers': [...], 'buy_total': int, 'sell_total': int}
        """
        # 날짜 파라미터가 있고 당일이 아닌 경우 외국계 순매수추이 API 사용
        if date and date != datetime.now().strftime('%Y%m%d'):
            return self._get_foreign_broker_historical(code, date)
        
        # 당일인 경우 기존 거래원 정보 방식 사용
        return self._get_foreign_broker_current(code, date)
    
    def _get_foreign_broker_historical(self, code: str, date: str) -> Optional[tuple]:
        """과거 날짜의 외국인 순매수 조회 (투자자별 매매 동향 기반)"""
        try:
            # get_stock_investor로 30일간 외국인 매매 데이터 조회
            investor_df = self.get_stock_investor(ticker=code)
            
            if investor_df is None or investor_df.empty:
                logging.warning(f"[{code}] 투자자별 매매 동향 데이터 조회 실패")
                return None
            
            # 해당 날짜 데이터 찾기
            target_data = investor_df[investor_df['stck_bsop_date'] == date]
            
            if target_data.empty:
                logging.warning(f"[{code}] {date} 날짜 데이터 없음 (최근 30일 범위 내에서만 조회 가능)")
                # 사용 가능한 날짜 범위 표시
                available_dates = investor_df['stck_bsop_date'].tolist()
                logging.info(f"[{code}] 사용 가능한 날짜: {available_dates[0]} ~ {available_dates[-1]}")
                return None
            
            # 외국인 매매 데이터 추출
            row = target_data.iloc[0]
            frgn_ntby_qty = int(row.get('frgn_ntby_qty', 0)) if row.get('frgn_ntby_qty') else 0
            frgn_buy_vol = int(row.get('frgn_shnu_vol', 0)) if row.get('frgn_shnu_vol') else 0
            frgn_sell_vol = int(row.get('frgn_seln_vol', 0)) if row.get('frgn_seln_vol') else 0
            
            details = {
                'brokers': [],  # 과거 날짜는 개별 거래원 정보 없음
                'buy_total': frgn_buy_vol,
                'sell_total': frgn_sell_vol,
                'total_brokers_found': 0,
                'query_date': date,
                'note': '투자자별 매매 동향 기반 외국인 전체 순매수 (과거 날짜)',
                'api_method': 'stock_investor',
                'data_range': f"{investor_df['stck_bsop_date'].iloc[0]} ~ {investor_df['stck_bsop_date'].iloc[-1]}"
            }
            
            logging.info(f"[{code}] {date} 외국인 순매수: {frgn_ntby_qty:,}주 (매수: {frgn_buy_vol:,}, 매도: {frgn_sell_vol:,})")
            return frgn_ntby_qty, details
            
        except Exception as e:
            logging.error(f"[{code}] 과거 날짜 외국인 순매수 조회 실패 ({date}): {e}")
            return None
    
    def _get_foreign_broker_current(self, code: str, date: str = None) -> Optional[tuple]:
        """당일 외국계 증권사 순매수 조회 (거래원 정보 기반)"""
        # 외국계 증권사 패턴 (실제 거래원명에서 확인된 것들)
        foreign_patterns = [
            'JP모간', '모간스탠리', '모건스탠리', '모간증권',
            '골드만', '골드만삭스', 
            '메릴린치', '메릴',
            'UBS', 'UBS코리아',
            'CS증권', '크레디트',
            'BNP', 'BNP파리바',
            'HSBC', 'HSBC증권',
            '도이치', '도이치은행',
            '노무라', '노무라증권',
            '다이와', '다이와증권',
            '씨티그룹', '씨티',
            '바클레이', '바클레이즈'
        ]
        
        # 거래원 정보 조회
        member_data = self.get_stock_member(code)
        if not member_data or 'output' not in member_data:
            logging.warning(f"[{code}] 거래원 정보 조회 실패")
            return None
        
        try:
            # 외국계 증권사 매매량 집계
            foreign_brokers = []
            total_buy = 0
            total_sell = 0
            
            members = member_data['output']
            if not isinstance(members, list):
                members = [members]
            
            for member in members:
                broker_name = member.get('hts_brkr_code', '')
                
                # 외국계 패턴 매칭
                is_foreign = any(pattern in broker_name for pattern in foreign_patterns)
                
                if is_foreign:
                    buy_qty = int(member.get('total_shnu_qty1', 0) or 0)  
                    sell_qty = int(member.get('total_seln_qty1', 0) or 0)
                    
                    total_buy += buy_qty
                    total_sell += sell_qty
                    
                    foreign_brokers.append({
                        'name': broker_name,
                        'buy': buy_qty,
                        'sell': sell_qty,
                        'net': buy_qty - sell_qty
                    })
            
            net_buy = total_buy - total_sell
            
            details = {
                'brokers': foreign_brokers,
                'buy_total': total_buy,
                'sell_total': total_sell,
                'total_brokers_found': len(foreign_brokers),
                'query_date': date or datetime.now().strftime('%Y%m%d'),
                'note': '거래원 정보 기반 외국계 증권사 순매수',
                'api_method': 'member_data'
            }
            
            logging.info(f"[{code}] 외국계 {len(foreign_brokers)}개사 순매수: {net_buy:,}주 (매수: {total_buy:,}, 매도: {total_sell:,})")
            return net_buy, details
            
        except Exception as e:
            logging.error(f"[{code}] 외국계 순매수 집계 실패: {e}")
            return None