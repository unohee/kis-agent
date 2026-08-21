"""``kis order twap`` / ``kis order vwap`` — algorithmic order subcommands.

Split out of :mod:`kis_agent.cli.main` to keep that module under the repository's
per-file line budget. The handler resolves shared CLI helpers lazily so the two
modules do not import each other at load time.
"""

import sys

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

    code = cli_main._resolve(args.code)
    side = args.side.lower()
    order_type = cli_main._DOMESTIC_ORDER_TYPES.get(args.type, args.type)
    price = int(args.price) if args.price else 0

    # 시장가/최유리 계열은 가격을 실어 보내지 않는다 (order buy/sell과 동일 규칙)
    if order_type in ("01", "03", "05", "06"):
        price = 0

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

    if not args.yes and not cli_main._confirm_order(
        f"{algo_label} {side_label}", details
    ):
        cli_main._out({"cancelled": True, "message": "주문이 취소되었습니다"})
        return

    # 집행은 duration 만큼 블로킹된다. stdout은 최종 JSON 전용으로 두고,
    # 진행 상황은 stderr로 흘려보내 LLM 파싱 계약을 깨지 않는다.
    def _progress(slice_result):
        sys.stderr.write(
            f"  [{algo_label}] 슬라이스 {slice_result.index + 1} "
            f"{slice_result.quantity:,}주 → {slice_result.status}"
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
    }

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
    if result.status not in ("completed",):
        sys.exit(2)
