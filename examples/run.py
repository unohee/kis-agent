import argparse
import asyncio
import atexit  # atexit 추가
import json  # json 모듈 임포트
import logging  # 로깅 모듈 임포트
import os
import select  # 비동기 입력을 위한 select 모듈 임포트
import subprocess
import sys
import termios  # 터미널 속성 제어를 위한 termios 모듈 임포트

# import schedule # schedule 라이브러리 제거
import time
import tty  # 터미널 모드 변경을 위한 tty 모듈 임포트
from datetime import datetime, timedelta  # timedelta 추가
from datetime import time as dt_time

logging.basicConfig(
    level=logging.DEBUG,  # 디버그 레벨 포함
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/stock_monitor_2025-05-12.log"),
        logging.StreamHandler(sys.stdout),  # 콘솔에도 출력
    ],
)

# --- 로깅 설정 ---
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)
log_filename = os.path.join(
    log_directory, f"stock_monitor_{datetime.now().strftime('%Y-%m-%d')}.log"
)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
logger.addHandler(file_handler)
# --- 로깅 설정 끝 ---

# 현재 파일의 디렉토리 (프로젝트 루트)를 sys.path에 추가
# 이렇게 하면 같은 루트 디렉토리에 있는 다른 모듈(agent.py, auth.py 등)을 직접 import 가능
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# StockMonitor 임포트 경로 수정
# KIS_Agent 임포트 추가
from src.discord_notifier import DiscordNotifier

# StockMonitor.py 에서 설정 로드 함수 임포트 (경로 확인 필요)
# 만약 StockMonitor.py가 load_config 함수를 정의하고 있다면:
from src.StockMonitor import StockMonitor, load_config

# --- 전역 설정 로드 ---
config = load_config()  # config.json 로드
monitor_config = config.get("stock_monitor", {})  # stock_monitor 설정 가져오기
# --- 전역 설정 로드 끝 ---

# --- 디스코드 봇 초기화 ---
notifier = None
try:
    logging.info("디스코드 알림 봇 초기화 시도...")
    notifier = DiscordNotifier()
    notifier.run_in_thread()
    logging.info("디스코드 알림 봇 인스턴스 생성됨.")
except ValueError as e:
    logging.error(f"디스코드 알림 봇 초기화 실패: {e}")
    notifier = None  # 봇 초기화 실패 시 None으로 설정
except Exception:
    logging.exception("디스코드 알림 봇 설정 중 예기치 않은 오류 발생")
    notifier = None
# --- 디스코드 봇 초기화 끝 ---


# --- 프로그램 종료 시 정리 함수 ---
def cleanup():
    if notifier:
        logging.info("스크립트 종료. 디스코드 알림 봇 종료 중...")
        notifier.notify_shutdown()  # 종료 알림 보내기
        import time

        time.sleep(2)  # 메시지 전송 시간 확보
        notifier.stop()


atexit.register(cleanup)
# --- 종료 함수 끝 ---


# --- 결과 로깅 함수 (경로 변경) ---
def log_results_to_json(watchlist_data, filename=None):
    """모니터링 결과를 JSON Lines 형식으로 파일에 추가합니다."""
    if filename is None:
        # 파일명을 날짜별로 분리
        date_str = datetime.now().strftime("%Y%m%d")
        filename = os.path.join(log_directory, f"monitoring_results_{date_str}.jsonl")
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watchlist": watchlist_data,
        }
        with open(filename, "a", encoding="utf-8") as f:
            # ensure_ascii=False 로 유니코드 문자 유지, default=str 로 직렬화 불가능 객체 처리
            f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        logging.error(
            f"Failed to log results to JSON file '{filename}': {e}", exc_info=True
        )


# --- 결과 로깅 함수 수정 끝 ---


def run_monitor_once(target_date_str=None):
    """StockMonitor를 실행하고 결과를 로깅하며, 처리된 종목 데이터를 반환하는 함수\n
    Args:
        target_date_str (str, optional): 뉴스 검색 기준 날짜 (YYYYMMDD 형식). Defaults to None (오늘).
    """
    monitor = None
    processed_stocks_data = None
    print("--- Entering run_monitor_once ---")
    if target_date_str:
        print(f"--- Target Date for News Fetching: {target_date_str} ---")
    sys.stdout.flush()
    try:
        config = load_config()
        monitor_config = config.get("stock_monitor", {})
        display_threshold = monitor_config.get("final_score_threshold", 3.0)

        # StockMonitor 생성 시 target_date_str 전달
        monitor = StockMonitor(target_date_str=target_date_str)

        logging.warning("Starting stock monitoring process...")
        if notifier:
            notifier.queue_message(":mag: 스캔 시작...")

        print(" -> Starting scans...")
        sys.stdout.flush()
        monitor.scan_transaction_power()

        # 조건검색식 종목 처리 추가 (장시간과 관계없이 실행)
        print(" -> Processing condition stocks...")
        sys.stdout.flush()
        monitor.process_condition_stocks()

        print(" -> Generating final watchlist...")
        sys.stdout.flush()
        final_score_threshold = monitor_config.get("final_score_threshold", 3.0)
        # StockMonitor 내부에 generate_watchlist와 sort_watchlist가 있다고 가정
        monitor.generate_watchlist(final_score_threshold)
        monitor.sort_watchlist()
        logging.warning(
            f"Final watchlist generated with {len(monitor.watchlist)} items."
        )
        print(f" -> Final watchlist generated: {len(monitor.watchlist)} items")
        sys.stdout.flush()

        processed_stocks_data = (
            monitor.processed_stocks if hasattr(monitor, "processed_stocks") else []
        )

        logging.warning("Displaying processed stocks report...")
        print(" -> Calling display_detailed_watchlist_async...")
        sys.stdout.flush()
        asyncio.run(
            monitor.display_detailed_watchlist_async(threshold=display_threshold)
        )
        print(" -> Finished display_detailed_watchlist_async.")
        sys.stdout.flush()
        logging.warning("Finished displaying processed stocks report.")

        if monitor and monitor.watchlist:
            print(" -> Logging watchlist results...")
            sys.stdout.flush()
            # 로그에는 현재 시간 기록
            log_results_to_json(
                [
                    {**stock, "scan_target_date": target_date_str}
                    for stock in monitor.watchlist
                ]
            )
            logging.warning(
                f"Logged {len(monitor.watchlist)} WATCHLIST items to monitoring_results.jsonl (Target Date: {target_date_str})"
            )
            if notifier:
                # 새로운 notify_scan_results 메서드 사용
                notifier.notify_scan_results(monitor.watchlist, target_date_str)
            print(" -> Finished logging results.")
            sys.stdout.flush()

        logging.warning("Stock monitoring process finished successfully.")
        if notifier:
            notifier.queue_message(":white_check_mark: 스캔 성공적으로 완료.")

        return processed_stocks_data

    except Exception as e:
        logging.error(f"Error during monitoring process: {e}", exc_info=True)
        print(f"\nError during run_monitor_once: {e}")
        if notifier:
            notifier.notify_error(f"모니터링 중 오류 발생: {e}")
        sys.stdout.flush()
        return None
    finally:
        print("--- Exiting run_monitor_once ---")
        sys.stdout.flush()


def print_strength_ranking(scan_data, scan_type="Scan"):
    """주어진 스캔 데이터의 체결강도 순위를 출력하는 헬퍼 함수"""
    print(f"\n--- {scan_type} Strength Ranking ---")
    if not scan_data:
        print("No scan data available for ranking.")
        logging.warning(f"{scan_type} data was None, skipping strength ranking.")
        return
    try:
        strength_data = []
        for stock in scan_data:
            code = stock.get("code", "N/A")
            name = stock.get("name", "N/A")
            strength_val = stock.get("pch_strength")
            try:
                strength_float = (
                    float(strength_val) if strength_val is not None else -1.0
                )
            except (ValueError, TypeError):
                strength_float = -1.0
            strength_data.append(
                {"code": code, "name": name, "pch_strength": strength_float}
            )

        strength_data_sorted = sorted(
            strength_data, key=lambda x: x["pch_strength"], reverse=True
        )

        if not strength_data_sorted:
            print("No valid strength data found.")
        else:
            max_code_len_s = (
                max(len(s.get("code", "")) for s in strength_data_sorted)
                if strength_data_sorted
                else 6
            )
            max_name_len_s = (
                max(len(s.get("name", "")) for s in strength_data_sorted)
                if strength_data_sorted
                else 10
            )
            rank_h, code_h, name_h, strength_h = "Rank", "Code", "Name", "Strength"
            header = f"{rank_h:<5} {code_h:<{max_code_len_s}} {name_h:<{max_name_len_s}} {strength_h}"
            print("-" * len(header))
            print(header)
            print("-" * len(header))
            for i, stock_info in enumerate(strength_data_sorted):
                strength_val = stock_info["pch_strength"]
                if isinstance(strength_val, (int, float)) and strength_val != -1.0:
                    strength_str = f"{strength_val:.2f}"
                else:
                    strength_str = "N/A"
                print(
                    f"{i+1:<5} {stock_info['code']:<{max_code_len_s}} {stock_info['name']:<{max_name_len_s}} {strength_str}"
                )
            print("-" * len(header))
        logging.info(f"Displayed {scan_type} strength ranking.")
    except Exception as analysis_err:
        logging.error(
            f"Error analyzing {scan_type} data: {analysis_err}", exc_info=True
        )
        print(f"\nError analyzing {scan_type} data: {analysis_err}")


def get_highest_similarity_news(stock):
    """Retrieve the news item with the highest similarity score for the given stock."""
    news_summary = stock.get("news_items_summary", [])
    if not news_summary:
        return None
    # Sort news items by similarity score in descending order and return the top one
    highest_similarity_news = max(
        news_summary, key=lambda x: x.get("relevance_score", 0), default=None
    )
    return highest_similarity_news


def main():
    # CLI 옵션 처리
    parser = argparse.ArgumentParser(description="Stock Monitor Runner")
    parser.add_argument(
        "--trade-monitor",
        action="store_true",
        help="Top 코드 실시간 WebSocket 모니터링 시작",
    )
    args, remaining_args = parser.parse_known_args()
    market_open = dt_time(9, 0)
    market_close = dt_time(15, 30)
    now_dt = datetime.now()
    now_time = now_dt.time()

    agent = None
    is_holiday_today = None
    try:
        print("Initializing KIS Agent for holiday check...")
        sys.stdout.flush()
        # Load account_info from environment variables
        app_key = os.environ.get("KIS_APP_KEY")
        app_secret = os.environ.get("KIS_APP_SECRET")
        account_no = os.environ.get("KIS_ACCOUNT_NO")
        account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

        if not all([app_key, app_secret, account_no]):
            print("Error: Required environment variables not set")
            print("Please set: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO")
            sys.exit(1)

        from kis_agent import Agent

        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
        )
        today_str = now_dt.strftime("%Y%m%d")
        print(f"Checking if today ({today_str}) is a holiday...")
        sys.stdout.flush()
        is_holiday_today = agent.is_holiday(today_str)

        scan_target_date = None
        processed_data_for_ranking = None
        initial_watchlist_codes = []

        if is_holiday_today is True:
            print(f"\nToday ({today_str}) is a market holiday.")
            logging.warning(
                f"Market holiday ({today_str}). Finding last trading day for news fetching."
            )
            sys.stdout.flush()

            # --- 마지막 거래일 찾기 ---
            last_trading_day = None
            check_date = now_dt.date() - timedelta(days=1)
            attempts = 0
            max_attempts = 30
            while attempts < max_attempts:
                if check_date.weekday() >= 5:
                    check_date -= timedelta(days=1)
                    continue
                check_date_str = check_date.strftime("%Y%m%d")
                is_check_day_holiday = None
                try:
                    is_check_day_holiday = agent.is_holiday(check_date_str)
                except Exception as holiday_check_err:
                    logging.error(
                        f"Error checking holiday for {check_date_str}: {holiday_check_err}. Stopping search."
                    )
                    break
                if is_check_day_holiday is False:
                    last_trading_day = check_date_str
                    print(f"Found last trading day for news: {last_trading_day}")
                    sys.stdout.flush()
                    break
                elif is_check_day_holiday is True:
                    check_date -= timedelta(days=1)
                    attempts += 1
                else:
                    logging.warning(
                        f"Holiday check failed for {check_date_str}. Stopping search."
                    )
                    break
                time.sleep(0.5)
            # --- 마지막 거래일 찾기 끝 ---

            if last_trading_day:
                scan_target_date = last_trading_day
                print(
                    f"\n--- Performing Scan on Holiday (News Date: {scan_target_date}) ---"
                )
                try:
                    # 휴장일 스캔 실행
                    processed_data_for_ranking = run_monitor_once(
                        target_date_str=scan_target_date
                    )
                except Exception as holiday_scan_err:
                    logging.error(
                        f"Error during holiday scan: {holiday_scan_err}", exc_info=True
                    )
                    print(f"\nError during holiday scan: {holiday_scan_err}")
                    processed_data_for_ranking = None  # 오류 시 None 처리

                # 휴일 스캔 결과 분석 및 출력
                print_strength_ranking(
                    processed_data_for_ranking, scan_type="Holiday Scan"
                )
                print("Exiting after holiday scan and analysis.")
                sys.exit(0)  # 휴장일 스캔 후 종료
            else:
                print(
                    "Could not determine last trading day. Cannot perform holiday scan."
                )
                logging.warning("Failed to determine last trading day. Exiting.")
                if notifier:
                    notifier.queue_message(
                        ":x: 마지막 거래일을 찾지 못해 휴일 스캔 불가."
                    )
                sys.exit(0)

        elif is_holiday_today is False:
            print(f"Today ({today_str}) is a trading day. Proceeding...")
            sys.stdout.flush()
            # 장 시작 전에는 마지막 거래일로 뉴스 날짜 설정
            if now_time < market_open:
                scan_target_date = agent.today  # 마지막 거래일
            else:
                scan_target_date = None  # 장 중 및 이후엔 오늘 기준

            print("\n--- Performing Initial Scan (Trading Day Confirmed) ---")
            try:
                # 개장일 초기 스캔 실행
                processed_data_for_ranking = run_monitor_once(
                    target_date_str=scan_target_date
                )
            except Exception as init_scan_err:
                logging.error(
                    f"Error during initial requested scan: {init_scan_err}",
                    exc_info=True,
                )
                print(f"\nError during initial requested scan: {init_scan_err}")
                processed_data_for_ranking = None

            # 초기 스캔 완료 후 watchlist 코드 추출
            if processed_data_for_ranking:
                initial_watchlist_codes = [
                    s.get("code") for s in processed_data_for_ranking[:10]
                ]  # 상위 10개
            # 초기 스캔 결과 분석 및 출력
            print_strength_ranking(processed_data_for_ranking, scan_type="Initial Scan")
            print("\n--- Initial Scan Finished ---")

        else:  # is_holiday_today is None
            logging.warning("Holiday check failed. Assuming closed.")
            print("\nWarning: Holiday check failed. Assuming closed. Exiting.")
            if notifier:
                notifier.notify_error("휴장일 확인 API 오류", critical=True)
            sys.exit(0)

    except Exception:
        # ... (Agent 초기화 오류 처리 동일) ...
        sys.exit(1)

    # --- 시간 기준 오프라인 모드 결정 ---
    is_trading_hours = market_open <= now_time <= market_close
    offline_mode = not is_trading_hours

    if offline_mode:
        print("\n--- Market is currently closed. Entering Wait/Final Scan Mode ---")
        if not is_trading_hours and now_time >= market_close:
            print("Market closed. Transitioning to post-market monitoring mode.")
            logging.warning(
                "Market closed. Transitioning to post-market monitoring mode."
            )
            start_online_monitoring(agent, initial_watchlist_codes, args, project_root)
            sys.exit(0)
        elif now_time < market_open:
            # Pre-market scans will start at 08:55; show dynamic countdown until then
            target_first_scan = datetime.combine(now_dt.date(), dt_time(8, 55))
            now_start = datetime.now()
            if now_start < target_first_scan:
                print(
                    f"Pre-market scans will start at {target_first_scan.strftime('%H:%M')}."
                )
                sys.stdout.flush()
                while True:
                    now_loop = datetime.now()
                    if now_loop >= target_first_scan:
                        break
                    # Countdown to 08:55
                    left_time = target_first_scan - now_loop
                    mm, ss = divmod(int(left_time.total_seconds()), 60)
                    sys.stdout.write(f"\r스캔 시작까지 {mm:02d}:{ss:02d} 남았습니다.")
                    sys.stdout.flush()
                    time.sleep(1)
                print()  # Move to next line after countdown
            print(
                "Starting pre-market scheduled scans every 90 seconds until market open."
            )
            sys.stdout.flush()
            next_scan_time = datetime.now()
            scan_interval = timedelta(seconds=90)
            while True:
                now = datetime.now()
                if now.time() >= market_open:
                    print(
                        "\nMarket open reached; transitioning to online monitoring mode."
                    )
                    sys.stdout.flush()
                    break
                # Display countdown to market open in-place
                time_left_open = datetime.combine(now.date(), market_open) - now
                mm, ss = divmod(int(time_left_open.total_seconds()), 60)
                sys.stdout.write(f"\r장 개장까지 {mm:02d}:{ss:02d} 남았습니다.")
                sys.stdout.flush()
                # When it's time, perform a scheduled scan
                if now >= next_scan_time:
                    print(
                        f"\n--- Pre-Market Scheduled Scan at {now.strftime('%H:%M:%S')} ---"
                    )
                    sys.stdout.flush()
                    try:
                        scheduled_data = run_monitor_once(target_date_str=agent.today)
                        print_strength_ranking(
                            scheduled_data, scan_type="Pre-Market Scheduled Scan"
                        )
                    except Exception as sched_err:
                        logging.error(
                            f"Error during pre-market scheduled scan: {sched_err}",
                            exc_info=True,
                        )
                        print(f"\nError during pre-market scheduled scan: {sched_err}")
                    next_scan_time = now + scan_interval
                time.sleep(1)
            # After market open, transition to online monitoring mode
            start_online_monitoring(agent, initial_watchlist_codes, args, project_root)
            sys.exit(0)

        sys.exit(0)

    else:  # 온라인 모드
        start_online_monitoring(agent, initial_watchlist_codes, args, project_root)

    # Modify the notification logic to include the highest similarity news
    for stock in processed_data_for_ranking or []:
        highest_similarity_news = get_highest_similarity_news(stock)
        notifier.notify_new_stock(
            stock_code=stock["code"],
            stock_name=stock["name"],
            score=stock["score"],
            reason=stock["conditions_met"],
            highest_similarity_news=highest_similarity_news,
        )


def start_online_monitoring(agent, initial_watchlist_codes, args, project_root):
    print("\n--- Entering Online Monitoring Mode ---")
    if args.trade_monitor and initial_watchlist_codes:
        print(f"Starting trade-monitor for codes: {initial_watchlist_codes}")
        subprocess.Popen(
            [
                sys.executable,
                os.path.join(project_root, "KIS_WS.py"),
                "--codes",
                *initial_watchlist_codes,
                "--hts-id",
                agent.user,
            ]
        )
    print(
        "Stock monitoring started. Runs 90 seconds after the previous scan finishes (between 09:00 and 15:30)."
    )
    print("Press 'c' to trigger an immediate scan. Press Ctrl+C to exit.")
    next_scan_time_online = datetime.now()
    scan_interval_online = timedelta(seconds=90)
    last_countdown_len_online = 0
    old_settings_online = termios.tcgetattr(sys.stdin.fileno())
    market_closed_notified = False
    # --- Add daily scan tracking ---
    last_scan_date = datetime.now().date()
    try:
        tty.setcbreak(sys.stdin.fileno())
        while True:
            loop_now_dt_online = datetime.now()
            # --- Daily scan logic: detect new trading day and schedule 08:55 scan ---
            current_date = loop_now_dt_online.date()
            if current_date != last_scan_date:
                last_scan_date = current_date
                today_str = current_date.strftime("%Y%m%d")
                if not agent.is_holiday(today_str):
                    print(
                        f"New trading day detected: {today_str}. Scheduling 08:55 pre-market scan."
                    )
                    target_time = datetime.combine(current_date, dt_time(8, 55))
                    while datetime.now() < target_time:
                        time.sleep(1)
                    print("Performing pre-market scan...")
                    run_monitor_once(target_date_str=today_str)
                    print_strength_ranking([], scan_type="Pre-Market Auto Scan")
            scan_now_online = False
            time_left = next_scan_time_online - loop_now_dt_online
            seconds_left = (
                int(time_left.total_seconds()) if time_left.total_seconds() > 0 else 0
            )
            mm, ss = divmod(seconds_left, 60)
            countdown_msg = f"다음 스캔까지 {mm:02d}:{ss:02d} 남았습니다."
            sys.stdout.write(
                "\r"
                + countdown_msg
                + " " * max(0, last_countdown_len_online - len(countdown_msg))
            )
            sys.stdout.flush()
            last_countdown_len_online = len(countdown_msg)
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                ch = sys.stdin.read(1)
                if ch.lower() == "c":
                    scan_now_online = True
            if loop_now_dt_online >= next_scan_time_online:
                scan_now_online = True
            now_time = datetime.now().time()
            if scan_now_online:
                if dt_time(9, 0) < now_time < dt_time(15, 30):
                    print(" " * last_countdown_len_online + "\r", end="")
                    last_countdown_len_online = 0
                    run_monitor_once()
                    next_scan_time_online = datetime.now() + scan_interval_online
                    print(
                        f"Scan finished. Next scan scheduled around {next_scan_time_online.strftime('%H:%M:%S')}."
                    )
                    # Reset the market closed notification flag if market is open again
                    market_closed_notified = False
                else:
                    if not market_closed_notified:
                        print(
                            "장시간 외입니다. 감시 루프는 유지되지만 스캔은 중단됩니다."
                        )
                        market_closed_notified = True
            else:
                # If market is open again, reset the notification flag so message can appear next time it closes
                if dt_time(9, 0) < now_time < dt_time(15, 30):
                    market_closed_notified = False
            time.sleep(0.5)
            # Removed market close check to allow scanning after 15:30
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings_online)


if __name__ == "__main__":
    # Schedule 라이브러리 확인 제거
    main()
