import os
import sys

# src 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # STONKS 폴더
if current_dir not in sys.path:
    sys.path.append(current_dir)

# PyKIS 프로젝트 경로 추가
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from kis_agent import Agent


def get_condition_stocks_dict():
    """조건검색식 종목 목록을 딕셔너리로 반환합니다.

    Returns:
        dict: {조건검색식명: [종목정보리스트]} 형태의 딕셔너리
    """
    # 환경변수에서 계좌 정보 로드
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        print("Error: 필수 환경변수가 설정되지 않았습니다.")
        print("다음 환경변수를 설정하세요:")
        print("  export KIS_APP_KEY='your_app_key'")
        print("  export KIS_APP_SECRET='your_app_secret'")
        print("  export KIS_ACCOUNT_NO='your_account_no'")
        print("  export KIS_ACCOUNT_CODE='01'  # 선택사항")
        return {}

    try:
        # Agent 인스턴스 생성
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
        )
    except Exception as e:
        print(f"Agent 생성 실패: {e}")
        return {}

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
    condition_stocks = {"기본조건검색식": []}  # 기본 조건검색식으로 설정

    for stock in stock_list:
        code = stock.get("code", "")
        name = stock.get("name", "")
        if code and name:  # 코드와 이름이 모두 있는 경우만 추가
            stock_info = {"code": code, "name": name, "종목코드": code, "종목명": name}
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
            name = stock.get("name", stock.get("종목명", "N/A"))
            code = stock.get("code", stock.get("종목코드", "N/A"))
            print(f"  {name} ({code})")


if __name__ == "__main__":
    main()
