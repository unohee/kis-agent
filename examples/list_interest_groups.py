import sys
import os
import yaml

# src 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # STONKS 폴더
if current_dir not in sys.path:
    sys.path.append(current_dir)

from src.agent import KIS_Agent
import json

def get_condition_stocks_dict():
    """조건검색식 종목 목록을 딕셔너리로 반환합니다.
    
    Returns:
        dict: {조건검색식명: [종목정보리스트]} 형태의 딕셔너리
    """
    # 계좌 정보 로드
    cred_path = os.path.join(project_root, 'credit', 'kis_devlp.yaml')
    with open(cred_path, 'r', encoding='utf-8') as f:
        cred_cfg = yaml.safe_load(f)
    account_info = {"CANO": cred_cfg["my_acct_stock"], "ACNT_PRDT_CD": cred_cfg["my_prod"]}
    
    # KIS_Agent 인스턴스 생성
    agent = KIS_Agent(account_info=account_info, verbose=False)
    
    # Agent를 통한 조건검색 결과 조회
    stocks = agent.get_condition_stocks("unohee", seq=0, tr_cont="N")
    
    if not stocks:
        print("조건검색식 종목 조회 실패")
        return {}
        
    stock_list = stocks
    if not stock_list:
        print("조건검색식 종목이 없습니다.")
        return {}
    
    # StockMonitor.py에서 기대하는 형태로 변환
    # {조건검색식명: [종목정보리스트]} 형태
    condition_stocks = {
        "기본조건검색식": []  # 기본 조건검색식으로 설정
    }
    
    for stock in stock_list:
        code = stock.get('code', '')
        name = stock.get('name', '')
        if code and name:  # 코드와 이름이 모두 있는 경우만 추가
            stock_info = {
                'code': code,
                'name': name,
                '종목코드': code,
                '종목명': name
            }
            condition_stocks["기본조건검색식"].append(stock_info)
            
    return condition_stocks

def main():
    # 조건검색식 종목 목록 조회
    condition_stocks_dict = get_condition_stocks_dict()
    
    if not condition_stocks_dict:
        return
        
    print("\n=== 조건검색식 종목 목록 ===")
    for condition_name, stocks in condition_stocks_dict.items():
        print(f"\n[{condition_name}]")
        for stock in stocks:
            name = stock.get('name', stock.get('종목명', 'N/A'))
            code = stock.get('code', stock.get('종목코드', 'N/A'))
            print(f"  {name} ({code})")

if __name__ == "__main__":
    main() 