#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
분봉 데이터 크롤러 예제

이 스크립트는 종목명과 기간을 입력받아 해당 기간의 분봉 데이터를 수집하고
{종목코드}_candles.db 파일로 저장합니다.

사용법:
    python minute_candle_crawler.py

기능:
    - 종목명 입력 (한글 또는 종목코드)
    - 기간 설정 (시작일~종료일)
    - 분봉 데이터 자동 수집
    - SQLite DB 저장
    - 진행 상황 표시
    - 영업일 자동 계산
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crawler.log', encoding='utf-8')
    ]
)

class MinuteCandleCrawler:
    def __init__(self):
        """크롤러 초기화"""
        self.agent = Agent()
        self.stock_code = None
        self.stock_name = None
        self.start_date = None
        self.end_date = None
        self.db_path = None
        
    def get_stock_code_from_name(self, name_or_code: str) -> str:
        """종목명 또는 종목코드로 종목코드 조회"""
        # 이미 6자리 코드면 그대로 반환
        if len(name_or_code) == 6 and name_or_code.isdigit():
            return name_or_code
            
        # 종목명으로 검색
        try:
            # 종목 검색 API 호출
            result = self.agent.get_stock_price(name_or_code)
            if result and 'output' in result:
                return name_or_code  # 검색 성공시 입력값이 유효한 코드
        except:
            pass
            
        # 주요 종목 매핑
        stock_mapping = {
            '삼성전자': '005930',
            '카카오': '035720',
            'SK하이닉스': '000660',
            'NAVER': '035420',
            '네이버': '035420',
            'LG에너지솔루션': '373220',
            '현대차': '005380',
            '기아': '000270',
            'POSCO홀딩스': '005490',
            '포스코홀딩스': '005490',
            '삼성바이오로직스': '207940',
            '셀트리온': '068270',
            'LG화학': '051910',
            '현대모비스': '012330',
            '삼성SDI': '006400'
        }
        
        return stock_mapping.get(name_or_code, name_or_code)
    
    def get_business_days(self, start_date: str, end_date: str) -> list:
        """영업일 목록 생성"""
        business_days = []
        current = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        while current <= end:
            date_str = current.strftime('%Y%m%d')
            
            # 주말 제외
            if current.weekday() < 5:  # 월~금
                # 휴장일 확인
                try:
                    is_holiday = self.agent.is_holiday(date_str)
                    if is_holiday is False:  # 영업일
                        business_days.append(date_str)
                except:
                    # API 호출 실패 시 주말만 제외
                    business_days.append(date_str)
            
            current += timedelta(days=1)
        
        return business_days
    
    def setup_database(self):
        """데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 분봉 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS minute_candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    open_price INTEGER NOT NULL,
                    high_price INTEGER NOT NULL,
                    low_price INTEGER NOT NULL,
                    close_price INTEGER NOT NULL,
                    volume INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code, datetime)
                )
            ''')
            
            # 인덱스 생성
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_datetime ON minute_candles(code, datetime)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON minute_candles(date)')
            
            conn.commit()
            conn.close()
            
            logging.info(f"데이터베이스 초기화 완료: {self.db_path}")
            
        except Exception as e:
            logging.error(f"데이터베이스 초기화 실패: {e}")
            raise
    
    def save_minute_data(self, df: pd.DataFrame, date: str):
        """분봉 데이터를 데이터베이스에 저장"""
        if df.empty:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 데이터 변환
            processed_data = []
            for _, row in df.iterrows():
                # 시간 정보 파싱
                time_str = str(row['stck_cntg_hour'])
                if len(time_str) >= 14:  # YYYYMMDDHHMMSS 형식
                    date_part = time_str[:8]
                    time_part = time_str[8:14]
                    datetime_str = f"{date_part} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                else:
                    datetime_str = f"{date} {time_str.zfill(6)[:2]}:{time_str.zfill(6)[2:4]}:{time_str.zfill(6)[4:6]}"
                
                processed_data.append({
                    'code': self.stock_code,
                    'date': date,
                    'time': time_str.zfill(6),
                    'datetime': datetime_str,
                    'open_price': int(row['stck_oprc']),
                    'high_price': int(row['stck_hgpr']),
                    'low_price': int(row['stck_lwpr']),
                    'close_price': int(row['stck_prpr']),
                    'volume': int(row['cntg_vol'])
                })
            
            # 기존 데이터 삭제
            conn.execute('DELETE FROM minute_candles WHERE code = ? AND date = ?', 
                        (self.stock_code, date))
            
            # 새 데이터 삽입
            conn.executemany('''
                INSERT OR REPLACE INTO minute_candles 
                (code, date, time, datetime, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [(d['code'], d['date'], d['time'], d['datetime'], 
                   d['open_price'], d['high_price'], d['low_price'], 
                   d['close_price'], d['volume']) for d in processed_data])
            
            conn.commit()
            conn.close()
            
            logging.info(f"[{date}] 분봉 데이터 {len(processed_data)}건 저장 완료")
            
        except Exception as e:
            logging.error(f"[{date}] 분봉 데이터 저장 실패: {e}")
    
    def crawl_minute_data(self):
        """분봉 데이터 수집"""
        business_days = self.get_business_days(self.start_date, self.end_date)
        total_days = len(business_days)
        
        if total_days == 0:
            print("📅 수집할 영업일이 없습니다.")
            return
        
        print(f"📊 수집 시작: {self.stock_name}({self.stock_code})")
        print(f"📅 기간: {self.start_date} ~ {self.end_date}")
        print(f"📈 총 영업일: {total_days}일")
        print(f"💾 저장 경로: {self.db_path}")
        print("=" * 60)
        
        success_count = 0
        failed_dates = []
        
        for i, date in enumerate(business_days, 1):
            try:
                print(f"[{i:3d}/{total_days}] {date} 수집 중...", end=" ")
                
                # 분봉 데이터 수집
                df = self.agent.fetch_minute_data(self.stock_code, date)
                
                if not df.empty:
                    # 데이터베이스 저장
                    self.save_minute_data(df, date)
                    print(f"✅ 완료 ({len(df)}건)")
                    success_count += 1
                else:
                    print("❌ 데이터 없음")
                    failed_dates.append(date)
                
                # API 호출 간격 (서버 부하 방지)
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                failed_dates.append(date)
                logging.error(f"[{date}] 수집 실패: {e}")
        
        # 수집 결과 요약
        print("=" * 60)
        print(f"✅ 수집 완료!")
        print(f"📊 성공: {success_count}/{total_days}일")
        print(f"💾 저장 위치: {self.db_path}")
        
        if failed_dates:
            print(f"❌ 실패한 날짜: {', '.join(failed_dates)}")
        
        # 저장된 데이터 통계
        self.show_statistics()
    
    def show_statistics(self):
        """저장된 데이터 통계 표시"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 전체 데이터 개수
            cursor.execute('SELECT COUNT(*) FROM minute_candles WHERE code = ?', (self.stock_code,))
            total_count = cursor.fetchone()[0]
            
            # 날짜별 데이터 개수
            cursor.execute('''
                SELECT date, COUNT(*) 
                FROM minute_candles 
                WHERE code = ? 
                GROUP BY date 
                ORDER BY date
            ''', (self.stock_code,))
            
            date_counts = cursor.fetchall()
            
            conn.close()
            
            print(f"\n📊 저장된 데이터 통계:")
            print(f"   총 분봉 개수: {total_count:,}건")
            print(f"   수집된 날짜: {len(date_counts)}일")
            
            if date_counts:
                print(f"   첫 번째 날짜: {date_counts[0][0]} ({date_counts[0][1]}건)")
                print(f"   마지막 날짜: {date_counts[-1][0]} ({date_counts[-1][1]}건)")
                
                # 평균 분봉 개수
                avg_count = total_count / len(date_counts)
                print(f"   일평균 분봉: {avg_count:.1f}건")
            
        except Exception as e:
            logging.error(f"통계 조회 실패: {e}")
    
    def run(self):
        """크롤러 실행"""
        print("🚀 분봉 데이터 크롤러")
        print("=" * 40)
        
        # 1. 종목 입력
        while True:
            stock_input = input("📈 종목명 또는 종목코드를 입력하세요: ").strip()
            if not stock_input:
                print("❌ 종목을 입력해주세요.")
                continue
                
            self.stock_code = self.get_stock_code_from_name(stock_input)
            
            # 종목 정보 확인
            try:
                stock_info = self.agent.get_stock_price(self.stock_code)
                if stock_info and 'output' in stock_info:
                    self.stock_name = stock_info['output'].get('hts_kor_isnm', stock_input)
                    print(f"✅ 종목 확인: {self.stock_name} ({self.stock_code})")
                    break
                else:
                    print(f"❌ 종목을 찾을 수 없습니다: {stock_input}")
            except Exception as e:
                print(f"❌ 종목 조회 실패: {e}")
        
        # 2. 기간 입력
        print("\n📅 수집 기간 설정")
        
        while True:
            start_input = input("시작일 (YYYYMMDD): ").strip()
            if len(start_input) == 8 and start_input.isdigit():
                self.start_date = start_input
                break
            print("❌ 올바른 형식으로 입력하세요 (예: 20240101)")
        
        while True:
            end_input = input("종료일 (YYYYMMDD): ").strip()
            if len(end_input) == 8 and end_input.isdigit():
                if end_input >= self.start_date:
                    self.end_date = end_input
                    break
                else:
                    print("❌ 종료일은 시작일보다 늦어야 합니다.")
            else:
                print("❌ 올바른 형식으로 입력하세요 (예: 20240131)")
        
        # 3. 데이터베이스 경로 설정
        self.db_path = f"{self.stock_code}_candles.db"
        
        # 4. 확인 및 실행
        print(f"\n🔍 설정 확인")
        print(f"   종목: {self.stock_name} ({self.stock_code})")
        print(f"   기간: {self.start_date} ~ {self.end_date}")
        print(f"   저장: {self.db_path}")
        
        confirm = input("\n수집을 시작하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 수집을 취소했습니다.")
            return
        
        # 5. 데이터베이스 초기화
        self.setup_database()
        
        # 6. 데이터 수집 시작
        print("\n🚀 데이터 수집 시작...")
        start_time = datetime.now()
        
        self.crawl_minute_data()
        
        end_time = datetime.now()
        elapsed = end_time - start_time
        
        print(f"\n⏱️ 총 소요 시간: {elapsed}")
        print(f"🎉 수집 완료!")

def main():
    """메인 함수"""
    try:
        crawler = MinuteCandleCrawler()
        crawler.run()
    except KeyboardInterrupt:
        print("\n❌ 사용자가 수집을 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        logging.error(f"크롤러 실행 오류: {e}")

if __name__ == "__main__":
    main() 