"""``kis order twap`` / ``kis order vwap`` — algorithmic order subcommands.

Split out of :mod:`kis_agent.cli.main` to keep that module under the repository's
per-file line budget. The handler resolves shared CLI helpers lazily so the two
modules do not import each other at load time.
"""

import sys
from pathlib import Path

__all__ = ["add_algo_parsers", "cmd_order_algo"]


def add_algo_parsers(order_sub) -> None:
    """Register the ``twap`` and ``vwap`` subcommands on the ``order`` parser.

    Args:
        order_sub: The ``order`` subparser action to attach to.
    """
    for algo, algo_help, default_duration, default_slices in (
        ("twap", "TWAP 분할주문 (시간 균등 분할)", 30, 6),
        ("vwap", "VWAP 분할주문 (거래량 비례 분할)", 60, 6),
    ):
        oa = order_sub.add_parser(algo, help=algo_help)
        oa.add_argument("code", help="종목코드 또는 종목명 (예: 005930, 삼성전자)")
        oa.add_argument(
            "--side", required=True, choices=["buy", "sell"], help="매수/매도"
        )
        oa.add_argument("--qty", type=int, required=True, help="총 주문수량")
        oa.add_argument(
            "--duration",
            type=int,
            default=default_duration,
            help=f"집행 시간(분, 기본 {default_duration})",
        )
        oa.add_argument(
            "--slices",
            type=int,
            default=default_slices,
            help=f"분할 횟수 (기본 {default_slices})",
        )
        oa.add_argument(
            "--type", default="best", help="주문유형 (best, limit, market, ioc, fok)"
        )
        oa.add_argument("--price", type=float, default=0, help="주문가격 (0=시장가)")
        oa.add_argument("--exchange", default="KRX", help="거래소 (KRX, NXT, SOR)")
        oa.add_argument(
            "--funding",
            default="cash",
            choices=["cash", "credit"],
            help="자금 구분 (cash=현금주문, credit=신용주문. 기본 cash)",
        )
        oa.add_argument(
            "--credit-type",
            default="",
            dest="credit_type",
            help="신용유형 (매수 기본 21=신용융자, 매도 기본 11=융자상환매도)",
        )
        oa.add_argument(
            "--loan-date",
            default="",
            dest="loan_dt",
            help="대출일자 YYYYMMDD (자기융자 22 매수에만 사용)",
        )
        oa.add_argument(
            "--credit-fallback",
            action="store_true",
            dest="credit_fallback",
            help="신용 주문이 거부되면 현금주문으로 재시도",
        )
        oa.add_argument(
            "--limit-price",
            type=float,
            default=0,
            dest="limit_price",
            help="지정가 가드 (매수: 초과 시 스킵, 매도: 미만 시 스킵)",
        )
        oa.add_argument(
            "--on-breach",
            default="skip",
            choices=["skip", "abort"],
            dest="on_breach",
            help="지정가 이탈 시 동작 (기본 skip)",
        )
        oa.add_argument(
            "--max-failures",
            type=int,
            default=3,
            dest="max_failures",
            help="연속 주문 실패 허용 횟수 (기본 3)",
        )
        oa.add_argument(
            "--no-session-guard",
            action="store_true",
            dest="no_session_guard",
            help="정규장(09:00-15:30) 제한 해제",
        )
        oa.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="주문을 전송하지 않고 스케줄만 시뮬레이션",
        )
        oa.add_argument(
            "--journal-dir",
            default="",
            dest="journal_dir",
            help="집행 원장 디렉터리 (기본 ~/.kis-agent/executions)",
        )
        oa.add_argument(
            "--no-journal",
            action="store_true",
            dest="no_journal",
            help="집행 원장 기록 비활성화 (권장하지 않음 — 죽으면 주문번호가 사라진다)",
        )
        oa.add_argument(
            "--ignore-incomplete",
            action="store_true",
            dest="ignore_incomplete",
            help="같은 종목의 미완료 집행 기록이 있어도 강행",
        )
        if algo == "vwap":
            oa.add_argument(
                "--profile-days",
                type=int,
                default=5,
                dest="profile_days",
                help="거래량 프로파일 산출 영업일 수 (기본 5)",
            )
        oa.add_argument("--yes", action="store_true", help="확인 없이 즉시 실행")
        oa.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")


def cmd_order_algo(args, algorithm: str):
    """TWAP/VWAP 알고리즘 주문 실행 — 지정 시간 동안 분할 집행.

    Args:
        args: ``kis order twap|vwap`` 파서가 만든 네임스페이스.
        algorithm: ``"twap"`` 또는 ``"vwap"``.
    """
    # main과의 순환 임포트를 피하려고 호출 시점에 가져온다. 속성 조회가 호출
    # 시점에 일어나므로 테스트의 ``kis_agent.cli.main.*`` 패치도 그대로 먹는다.
    from kis_agent.cli import main as cli_main
    from kis_agent.execution import run_twap, run_vwap
    from kis_agent.execution.journal import find_incomplete_runs
    from datetime import datetime

    from kis_agent.execution.runner import krx_regular_session
    from kis_agent.execution.schedule import (
        build_twap_schedule,
        build_vwap_schedule,
    )

    code = cli_main._resolve(args.code)
    side = args.side.lower()
    order_type = cli_main._DOMESTIC_ORDER_TYPES.get(args.type, args.type)
    price = int(args.price) if args.price else 0

    # 시장가/최유리 계열은 가격을 실어 보내지 않는다 (order buy/sell과 동일 규칙)
    if order_type in ("01", "03", "05", "06"):
        price = 0

    journal_dir = Path(args.journal_dir).expanduser() if args.journal_dir else None

    # 같은 종목·같은 방향의 미완료 집행이 남아 있으면 먼저 멈춘다. 미완료
    # 원장은 "주문이 이미 나간 채로 프로세스가 죽었다"의 서명이고, 그걸 보지
    # 않고 같은 부모 주문을 다시 내는 것이 포지션이 조용히 두 배가 되는 경로다.
    # 반대 방향은 막지 않는다 — 크래시 직후 가장 하고 싶은 일이 청산이다.
    # 토큰을 만들기 전에 검사해 헛된 인증을 피한다.
    if not args.dry_run and not args.ignore_incomplete:
        incomplete = find_incomplete_runs(code, base_dir=journal_dir, side=side)
        if incomplete:
            cli_main._out(
                {
                    "error": (
                        f"{code} {side} 방향에 완료되지 않은 집행 기록이 "
                        f"{len(incomplete)}건 있습니다. 이미 나간 주문을 "
                        "확인한 뒤 진행하세요 (kis order list / kis trades로 "
                        "실제 접수 여부 확인, 강행하려면 --ignore-incomplete)."
                    ),
                    "code": "IncompleteExecutionFound",
                    "data": {
                        "incompleteRuns": [
                            {
                                "runId": r.run_id,
                                "journalPath": str(r.path),
                                "side": r.side,
                                "submittedQuantity": r.submitted_quantity,
                                "totalQuantity": r.total_quantity,
                                "orderNumbers": r.order_numbers,
                                "startedAt": r.started_at,
                                "summary": r.describe(),
                            }
                            for r in incomplete
                        ]
                    },
                }
            )
            sys.exit(1)

    agent = cli_main._create_agent()
    name = cli_main._get_name(agent, code)
    side_label = "매수" if side == "buy" else "매도"
    algo_label = algorithm.upper()
    type_label = {v: k for k, v in cli_main._DOMESTIC_ORDER_TYPES.items()}.get(
        order_type, order_type
    )

    per_slice = max(1, args.qty // max(1, args.slices))
    details = {
        "알고리즘": f"{algo_label} 분할주문",
        "종목": f"{code} ({name})" if name else code,
        "구분": side_label,
        "총수량": f"{args.qty:,}주",
        "분할": f"{args.slices}회 (슬라이스당 약 {per_slice:,}주)",
        "집행시간": f"{args.duration}분",
        "주문유형": type_label,
        "가격": f"{price:,}원" if price else "시장가",
        "거래소": args.exchange.upper(),
        "자금구분": (
            "신용주문" + (f" (유형 {args.credit_type})" if args.credit_type else "")
            if args.funding == "credit"
            else "현금주문"
        ),
        "지정가 가드": (
            f"{args.limit_price:,.0f}원 ({args.on_breach})"
            if args.limit_price
            else "없음"
        ),
        "정규장 제한": "해제" if args.no_session_guard else "적용 (09:00-15:30)",
        "모드": "DRY-RUN (주문 미전송)" if args.dry_run else "실주문",
    }
    if args.funding == "credit" and args.credit_fallback:
        details["신용 거부 시"] = "현금주문으로 폴백"
    if algorithm == "vwap":
        details["거래량 프로파일"] = f"과거 {args.profile_days}영업일"

    # STO-1731: a schedule that runs past the close loses its tail slices to
    # the session guard. The prompt used to show 집행시간 and 정규장 제한 as
    # two unrelated strings — multiply them and the operator would have
    # approved a 33% shortfall. Compute the real number before asking.
    if not args.no_session_guard:
        try:
            from datetime import timedelta as _td

            begin = datetime.now()  # the runner defaults start to now
            if algorithm == "twap":
                preview = build_twap_schedule(
                    total_quantity=args.qty,
                    slices=args.slices,
                    start=begin,
                    duration=_td(minutes=args.duration),
                )
            else:
                preview = build_vwap_schedule(
                    total_quantity=args.qty,
                    slices=args.slices,
                    start=begin,
                    duration=_td(minutes=args.duration),
                    weights=None,
                )
            outside = [sl for sl in preview if not krx_regular_session(sl.scheduled_at)]
            if outside:
                lost = sum(sl.quantity for sl in outside)
                details["⚠ 마감 초과"] = (
                    f"슬라이스 {len(outside)}개({lost:,}주)가 정규장 밖 — "
                    f"집행되지 않고 유실됩니다"
                )
        except ValueError:
            # invalid qty/slices/duration — the runner's own validation
            # reports it properly; the preview must not mask that error
            pass

    if not args.yes and not cli_main._confirm_order(
        f"{algo_label} {side_label}", details
    ):
        cli_main._out({"cancelled": True, "message": "주문이 취소되었습니다"})
        return

    # 집행은 duration 만큼 블로킹된다. stdout은 최종 JSON 전용으로 두고,
    # 진행 상황은 stderr로 흘려보내 LLM 파싱 계약을 깨지 않는다.
    def _progress(slice_result):
        # 주문번호를 여기 싣는 이유: 원장이 어떤 이유로든 실패해도 터미널
        # 스크롤백에는 남아야 한다. 죽은 집행을 대사할 때 이게 유일한 단서일 수 있다.
        order_ref = (
            f" 주문번호 {slice_result.order_no}" if slice_result.order_no else ""
        )
        sys.stderr.write(
            f"  [{algo_label}] 슬라이스 {slice_result.index + 1} "
            f"{slice_result.quantity:,}주 → {slice_result.status}{order_ref}"
            f"{' (' + slice_result.message + ')' if slice_result.message else ''}\n"
        )
        sys.stderr.flush()

    common = {
        "code": code,
        "side": side,
        "quantity": args.qty,
        "duration_minutes": args.duration,
        "slices": args.slices,
        "order_type": order_type,
        "price": price,
        "exchange": args.exchange.upper(),
        "funding": args.funding,
        "credit_type": args.credit_type or None,
        "loan_dt": args.loan_dt,
        "credit_fallback_to_cash": args.credit_fallback,
        "limit_price": args.limit_price if args.limit_price else None,
        "on_price_breach": args.on_breach,
        "max_consecutive_failures": args.max_failures,
        "dry_run": args.dry_run,
        "restrict_to_session": not args.no_session_guard,
        "progress": _progress,
        "journal_dir": journal_dir,
        "journal_enabled": not args.no_journal,
        # CLI는 토큰을 만들기 전에 이미 선검사했다 (--ignore-incomplete도 거기서 처리).
        "check_incomplete": False,
    }

    if not args.no_journal:
        sys.stderr.write(
            f"  [{algo_label}] 집행 원장: "
            f"{journal_dir or '~/.kis-agent/executions'} 아래에 기록됩니다\n"
        )
        sys.stderr.flush()

    try:
        if algorithm == "twap":
            result = run_twap(agent, **common)
        else:
            result = run_vwap(agent, profile_days=args.profile_days, **common)
    except ValueError as e:
        cli_main._out({"error": str(e), "code": "ValueError"})
        sys.exit(1)
    except Exception as e:
        cli_main._out({"error": str(e), "code": type(e).__name__})
        sys.exit(1)

    payload = result.to_dict()
    payload["name"] = name
    cli_main._out({"data": {"algoOrder": payload}}, args.pretty)

    # 부분 집행/중단은 종료코드로도 알린다 — 스크립트가 성공으로 오독하면 안 된다.
    # simulated(dry-run 전체 완료)도 성공이다 — STO-1731 이전에는 completed로
    # 위장해 있었을 뿐이다.
    if result.status not in ("completed", "simulated"):
        sys.exit(2)
