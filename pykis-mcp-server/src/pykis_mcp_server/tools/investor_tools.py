"""Investor & program trading MCP tools"""

from typing import Any, Dict

from ..errors import InvalidParameterError, validate_api_response
from ..server import get_agent, server


@server.tool()
async def get_stock_investor(code: str) -> Dict[str, Any]:
    """종목별 투자자 매매동향"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_stock_investor(code)
    return validate_api_response(result, "투자자 매매동향 조회")


@server.tool()
async def get_investor_daily_by_market(
    fid_cond_mrkt_div_code: str = "U",
    fid_input_iscd: str = "0001",
    fid_input_date_1: str = "",
    fid_input_iscd_1: str = "KSP",
    fid_input_date_2: str = "",
    fid_input_iscd_2: str = "0001",
) -> Dict[str, Any]:
    """시장별 투자자 일별 매매동향"""
    agent = get_agent()
    result = agent.get_investor_daily_by_market(
        fid_cond_mrkt_div_code,
        fid_input_iscd,
        fid_input_date_1,
        fid_input_iscd_1,
        fid_input_date_2,
        fid_input_iscd_2,
    )
    return validate_api_response(result, "시장별 투자자 일별 동향 조회")


@server.tool()
async def get_investor_time_by_market(
    fid_input_iscd: str = "999", fid_input_iscd_2: str = "S001"
) -> Dict[str, Any]:
    """시장별 투자자 시간대별 매매동향"""
    agent = get_agent()
    result = agent.get_investor_time_by_market(fid_input_iscd, fid_input_iscd_2)
    return validate_api_response(result, "시장별 투자자 시간대별 동향 조회")


@server.tool()
async def get_foreign_broker_net_buy(
    code: str, foreign_brokers: list, date: str
) -> Dict[str, Any]:
    """외국인/기관 순매수 조회"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_foreign_broker_net_buy(code, foreign_brokers, date)
    return {"success": True, "data": result}


@server.tool()
async def get_stock_member(code: str) -> Dict[str, Any]:
    """증권사별 매매동향"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_stock_member(code)
    return validate_api_response(result, "증권사별 매매동향 조회")


@server.tool()
async def get_member_transaction(
    code: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    """증권사 기간별 거래"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_member_transaction(code, start_date, end_date)
    return validate_api_response(result, "증권사 기간별 거래 조회")


@server.tool()
async def get_program_trade_by_stock(code: str, date: str = "") -> Dict[str, Any]:
    """종목별 프로그램 매매"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_program_trade_by_stock(code, date)
    return validate_api_response(result, "프로그램 매매 조회")


@server.tool()
async def get_program_trade_daily_summary(code: str, date: str = "") -> Dict[str, Any]:
    """프로그램 매매 일별 요약"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_program_trade_daily_summary(code, date)
    return validate_api_response(result, "프로그램 매매 일별 요약 조회")


@server.tool()
async def get_program_trade_market_daily(
    start_date: str, end_date: str
) -> Dict[str, Any]:
    """시장 프로그램 매매"""
    agent = get_agent()
    result = agent.get_program_trade_market_daily(start_date, end_date)
    return validate_api_response(result, "시장 프로그램 매매 조회")


@server.tool()
async def get_program_trade_hourly_trend(code: str = "") -> Dict[str, Any]:
    """프로그램 매매 시간대별 추세"""
    agent = get_agent()
    result = agent.get_program_trade_hourly_trend(code)
    return validate_api_response(result, "프로그램 매매 시간대별 추세 조회")


@server.tool()
async def get_program_trade_period_detail(
    code: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    """프로그램 매매 기간 상세"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_program_trade_period_detail(code, start_date, end_date)
    return validate_api_response(result, "프로그램 매매 기간 상세 조회")


@server.tool()
async def get_frgnmem_pchs_trend(stock_code: str) -> Dict[str, Any]:
    """외국인 매수 추세 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 외국인 매수 추세 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_frgnmem_pchs_trend(stock_code)
    return validate_api_response(result, "외국인 매수 추세 조회")


@server.tool()
async def get_frgnmem_trade_estimate(
    stock_code: str, cls_code: str = "0"
) -> Dict[str, Any]:
    """외국인 매매 추정 조회

    Args:
        stock_code: 종목코드 6자리
        cls_code: 분류코드 (0=전체)

    Returns:
        Dict: 외국인 매매 추정 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_frgnmem_trade_estimate(stock_code, cls_code)
    return validate_api_response(result, "외국인 매매 추정 조회")


@server.tool()
async def get_frgnmem_trade_trend(
    stock_code: str, cls_code: str = "0", period: str = "D"
) -> Dict[str, Any]:
    """외국인 매매 추세 조회

    Args:
        stock_code: 종목코드 6자리
        cls_code: 분류코드 (0=전체)
        period: 기간구분 (D=일별)

    Returns:
        Dict: 외국인 매매 추세 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_frgnmem_trade_trend(stock_code, cls_code, period)
    return validate_api_response(result, "외국인 매매 추세 조회")


@server.tool()
async def get_investor_trade_by_stock_daily(
    stock_code: str, start_date: str = "", end_date: str = ""
) -> Dict[str, Any]:
    """종목별 투자자 일별 매매동향 조회

    Args:
        stock_code: 종목코드 6자리
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)

    Returns:
        Dict: 투자자별 일별 매매동향
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_investor_trade_by_stock_daily(stock_code, start_date, end_date)
    return validate_api_response(result, "투자자 일별 매매동향 조회")


@server.tool()
async def get_investor_trend_estimate(
    market: str = "0", investor: str = "1000"
) -> Dict[str, Any]:
    """투자자별 추정 동향 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)
        investor: 투자자구분 (1000=개인, 9000=외국인 등)

    Returns:
        Dict: 투자자별 추정 동향
    """
    agent = get_agent()
    result = agent.get_investor_trend_estimate(market, investor)
    return validate_api_response(result, "투자자 추정 동향 조회")


@server.tool()
async def get_investor_program_trade_today(market: str = "0") -> Dict[str, Any]:
    """당일 투자자 프로그램 매매 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)

    Returns:
        Dict: 당일 투자자 프로그램 매매 데이터
    """
    agent = get_agent()
    result = agent.get_investor_program_trade_today(market)
    return validate_api_response(result, "당일 투자자 프로그램 매매 조회")


@server.tool()
async def analyze_broker_accumulation(
    broker_name: str, days: int = 7, top_n: int = 10
) -> Dict[str, Any]:
    """특정 증권사의 기간별 매집 종목 분석

    지정된 증권사가 최근 N일간 가장 많이 순매수한 종목을 분석합니다.
    주요 거래량 상위 종목을 대상으로 분석합니다.

    Args:
        broker_name: 증권사명 (예: "모건스탠리", "JP모건", "골드만삭스")
        days: 분석 기간 (기본값: 7일)
        top_n: 상위 N개 종목 반환 (기본값: 10)

    Returns:
        Dict: 매집 분석 결과
            - broker: 증권사명
            - period: 분석 기간
            - top_accumulated: 순매수 상위 종목 리스트
                - code: 종목코드
                - name: 종목명
                - net_buy_volume: 순매수량
                - net_buy_amount: 순매수금액
            - analysis_date: 분석 일시
    """
    from datetime import datetime, timedelta

    agent = get_agent()

    # 분석 기간 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # 거래량 상위 종목 조회 (분석 대상)
    top_volume = agent.get_volume_rank("0", "0", "0")
    if not top_volume or top_volume.get("rt_cd") != "0":
        return {
            "success": False,
            "message": "거래량 상위 종목 조회 실패",
            "error_code": "VOLUME_RANK_FAILED",
        }

    # 상위 50개 종목에 대해 증권사별 거래 분석
    accumulation_data = []
    stocks = top_volume.get("output", [])[:50]

    for stock in stocks:
        code = stock.get("mksc_shrn_iscd", stock.get("stck_shrn_iscd", ""))
        name = stock.get("hts_kor_isnm", "")

        if not code or len(code) != 6:
            continue

        try:
            # 증권사별 기간 거래 조회
            member_data = agent.get_member_transaction(code, start_str, end_str)
            if not member_data or member_data.get("rt_cd") != "0":
                continue

            # 지정 증권사 찾기
            for member in member_data.get("output", []):
                member_name = member.get("mbcr_name", "")
                if broker_name.lower() in member_name.lower():
                    net_buy = int(member.get("ntby_qty", 0))
                    net_amount = int(member.get("ntby_tr_pbmn", 0))

                    if net_buy > 0:  # 순매수인 경우만
                        accumulation_data.append(
                            {
                                "code": code,
                                "name": name,
                                "net_buy_volume": net_buy,
                                "net_buy_amount": net_amount,
                                "broker_detail": member_name,
                            }
                        )
                    break
        except Exception:
            continue

    # 순매수량 기준 정렬
    accumulation_data.sort(key=lambda x: x["net_buy_volume"], reverse=True)

    return {
        "success": True,
        "broker": broker_name,
        "period": f"{start_str} ~ {end_str}",
        "days": days,
        "analyzed_stocks": len(stocks),
        "top_accumulated": accumulation_data[:top_n],
        "analysis_date": datetime.now().isoformat(),
    }


@server.tool()
async def analyze_foreign_institutional_flow(
    days: int = 5, top_n: int = 20
) -> Dict[str, Any]:
    """외국인/기관 동시 순매수 종목 분석

    최근 N일간 외국인과 기관이 동시에 순매수한 종목을 찾습니다.
    두 주체가 동시에 매수하는 종목은 강한 상승 신호로 해석됩니다.

    Args:
        days: 분석 기간 (기본값: 5일)
        top_n: 상위 N개 종목 반환 (기본값: 20)

    Returns:
        Dict: 동시 순매수 분석 결과
            - consensus_buys: 동시 순매수 종목 리스트
                - code: 종목코드
                - name: 종목명
                - foreign_net_buy: 외국인 순매수량
                - institution_net_buy: 기관 순매수량
                - total_net_buy: 합계 순매수량
                - price_change: 기간 수익률
    """
    from datetime import datetime, timedelta

    agent = get_agent()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # 거래량 상위 종목 조회
    top_volume = agent.get_volume_rank("0", "0", "0")
    if not top_volume or top_volume.get("rt_cd") != "0":
        return {"success": False, "message": "거래량 상위 종목 조회 실패"}

    consensus_data = []
    stocks = top_volume.get("output", [])[:100]

    for stock in stocks:
        code = stock.get("mksc_shrn_iscd", stock.get("stck_shrn_iscd", ""))
        name = stock.get("hts_kor_isnm", "")

        if not code or len(code) != 6:
            continue

        try:
            # 투자자별 매매동향 조회
            investor_data = agent.get_investor_trade_by_stock_daily(
                code, start_str, end_str
            )
            if not investor_data or investor_data.get("rt_cd") != "0":
                continue

            # 외국인/기관 순매수 집계
            foreign_net = 0
            institution_net = 0

            for day_data in investor_data.get("output", []):
                foreign_net += int(day_data.get("frgn_ntby_qty", 0))
                institution_net += int(day_data.get("orgn_ntby_qty", 0))

            # 둘 다 순매수인 경우만
            if foreign_net > 0 and institution_net > 0:
                # 현재가 조회로 수익률 계산
                price_data = agent.get_stock_price(code)
                price_change = 0
                if price_data and price_data.get("rt_cd") == "0":
                    price_change = float(
                        price_data.get("output", {}).get("prdy_ctrt", 0)
                    )

                consensus_data.append(
                    {
                        "code": code,
                        "name": name,
                        "foreign_net_buy": foreign_net,
                        "institution_net_buy": institution_net,
                        "total_net_buy": foreign_net + institution_net,
                        "price_change": price_change,
                    }
                )
        except Exception:
            continue

    # 합계 순매수량 기준 정렬
    consensus_data.sort(key=lambda x: x["total_net_buy"], reverse=True)

    return {
        "success": True,
        "period": f"{start_str} ~ {end_str}",
        "days": days,
        "analyzed_stocks": len(stocks),
        "consensus_buys": consensus_data[:top_n],
        "analysis_date": datetime.now().isoformat(),
    }


@server.tool()
async def detect_volume_spike(
    threshold: float = 3.0, top_n: int = 20
) -> Dict[str, Any]:
    """거래량 급등 종목 탐지

    당일 거래량이 20일 평균 대비 N배 이상인 종목을 찾습니다.
    거래량 급등은 주가 변동의 선행 지표가 될 수 있습니다.

    Args:
        threshold: 평균 대비 배수 (기본값: 3.0 = 300%)
        top_n: 상위 N개 종목 반환 (기본값: 20)

    Returns:
        Dict: 거래량 급등 종목 리스트
            - volume_spikes: 급등 종목 리스트
                - code: 종목코드
                - name: 종목명
                - current_volume: 당일 거래량
                - avg_volume: 20일 평균 거래량
                - volume_ratio: 거래량 비율
                - price_change: 등락률
    """
    agent = get_agent()

    # 거래량 상위 종목 조회
    top_volume = agent.get_volume_rank("0", "0", "0")
    if not top_volume or top_volume.get("rt_cd") != "0":
        return {"success": False, "message": "거래량 상위 종목 조회 실패"}

    spike_data = []
    stocks = top_volume.get("output", [])[:100]

    for stock in stocks:
        code = stock.get("mksc_shrn_iscd", stock.get("stck_shrn_iscd", ""))
        name = stock.get("hts_kor_isnm", "")
        current_volume = int(stock.get("acml_vol", 0))

        if not code or len(code) != 6 or current_volume == 0:
            continue

        try:
            # 일봉 데이터로 20일 평균 거래량 계산
            daily_data = agent.inquire_daily_price(code, "D", "1")
            if not daily_data or daily_data.get("rt_cd") != "0":
                continue

            volumes = []
            for candle in daily_data.get("output", [])[:20]:
                vol = int(candle.get("acml_vol", 0))
                if vol > 0:
                    volumes.append(vol)

            if len(volumes) < 5:
                continue

            avg_volume = sum(volumes) / len(volumes)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            if volume_ratio >= threshold:
                price_change = float(stock.get("prdy_ctrt", 0))

                spike_data.append(
                    {
                        "code": code,
                        "name": name,
                        "current_volume": current_volume,
                        "avg_volume": int(avg_volume),
                        "volume_ratio": round(volume_ratio, 2),
                        "price_change": price_change,
                    }
                )
        except Exception:
            continue

    # 거래량 비율 기준 정렬
    spike_data.sort(key=lambda x: x["volume_ratio"], reverse=True)

    return {
        "success": True,
        "threshold": threshold,
        "analyzed_stocks": len(stocks),
        "volume_spikes": spike_data[:top_n],
        "analysis_date": __import__("datetime").datetime.now().isoformat(),
    }


@server.tool()
async def find_price_momentum(
    period: int = 5, min_change: float = 5.0, top_n: int = 20
) -> Dict[str, Any]:
    """가격 모멘텀 종목 탐색

    최근 N일간 지속적으로 상승하며 특정 수익률 이상인 종목을 찾습니다.

    Args:
        period: 분석 기간 (기본값: 5일)
        min_change: 최소 누적 수익률 % (기본값: 5.0%)
        top_n: 상위 N개 종목 반환 (기본값: 20)

    Returns:
        Dict: 모멘텀 종목 리스트
            - momentum_stocks: 모멘텀 종목 리스트
                - code: 종목코드
                - name: 종목명
                - period_return: 기간 수익률
                - up_days: 상승일 수
                - current_price: 현재가
    """
    agent = get_agent()

    # 등락률 상위 종목 조회
    top_gainers = agent.get_fluctuation_rank("0", "1", "0")  # 상승 종목만
    if not top_gainers or top_gainers.get("rt_cd") != "0":
        return {"success": False, "message": "등락률 순위 조회 실패"}

    momentum_data = []
    stocks = top_gainers.get("output", [])[:100]

    for stock in stocks:
        code = stock.get("mksc_shrn_iscd", stock.get("stck_shrn_iscd", ""))
        name = stock.get("hts_kor_isnm", "")

        if not code or len(code) != 6:
            continue

        try:
            # 일봉 데이터로 기간 수익률 및 상승일 계산
            daily_data = agent.inquire_daily_price(code, "D", "1")
            if not daily_data or daily_data.get("rt_cd") != "0":
                continue

            candles = daily_data.get("output", [])[:period]
            if len(candles) < period:
                continue

            # 상승일 수 계산
            up_days = 0
            for candle in candles:
                if float(candle.get("prdy_vrss", 0)) > 0:
                    up_days += 1

            # 기간 수익률 계산
            if candles:
                start_price = float(candles[-1].get("stck_oprc", 0))
                end_price = float(candles[0].get("stck_clpr", 0))
                period_return = (
                    ((end_price - start_price) / start_price * 100)
                    if start_price > 0
                    else 0
                )
            else:
                period_return = 0

            if period_return >= min_change and up_days >= period * 0.6:
                momentum_data.append(
                    {
                        "code": code,
                        "name": name,
                        "period_return": round(period_return, 2),
                        "up_days": up_days,
                        "total_days": period,
                        "current_price": (
                            int(candles[0].get("stck_clpr", 0)) if candles else 0
                        ),
                    }
                )
        except Exception:
            continue

    # 기간 수익률 기준 정렬
    momentum_data.sort(key=lambda x: x["period_return"], reverse=True)

    return {
        "success": True,
        "period": period,
        "min_change": min_change,
        "analyzed_stocks": len(stocks),
        "momentum_stocks": momentum_data[:top_n],
        "analysis_date": __import__("datetime").datetime.now().isoformat(),
    }


@server.tool()
async def analyze_market_breadth() -> Dict[str, Any]:
    """시장 폭(Market Breadth) 분석

    시장 전체의 상승/하락 종목 비율, 거래량 분포 등을
    분석하여 시장 전반의 건강도를 평가합니다.

    Returns:
        Dict: 시장 폭 분석 결과
            - advance_decline: 상승/하락 종목 수
            - advance_ratio: 상승 비율
            - volume_analysis: 거래량 분석
            - market_sentiment: 시장 심리 (Bullish/Bearish/Neutral)
    """
    agent = get_agent()

    # 시장 등락 현황 조회
    market_data = agent.get_market_fluctuation()
    if not market_data or market_data.get("rt_cd") != "0":
        return {"success": False, "message": "시장 등락 현황 조회 실패"}

    output = market_data.get("output", {})

    # 상승/하락/보합 종목 수
    advancing = int(output.get("uplm_cnt", 0)) + int(output.get("uplm_cls_cnt", 0))
    declining = int(output.get("dnlm_cnt", 0)) + int(output.get("dnlm_cls_cnt", 0))
    unchanged = int(output.get("stnr_cnt", 0))
    total = advancing + declining + unchanged

    advance_ratio = (advancing / total * 100) if total > 0 else 0

    # 시장 심리 판단
    if advance_ratio >= 60:
        sentiment = "Bullish (강세)"
    elif advance_ratio <= 40:
        sentiment = "Bearish (약세)"
    else:
        sentiment = "Neutral (중립)"

    # 거래량 상위 종목의 상승/하락 분석
    volume_rank = agent.get_volume_rank("0", "0", "0")
    volume_advancing = 0
    volume_declining = 0

    if volume_rank and volume_rank.get("rt_cd") == "0":
        for stock in volume_rank.get("output", [])[:50]:
            change = float(stock.get("prdy_ctrt", 0))
            if change > 0:
                volume_advancing += 1
            elif change < 0:
                volume_declining += 1

    return {
        "success": True,
        "advance_decline": {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "total": total,
        },
        "advance_ratio": round(advance_ratio, 2),
        "volume_leaders": {
            "advancing": volume_advancing,
            "declining": volume_declining,
            "ratio": (
                round(volume_advancing / 50 * 100, 2)
                if volume_advancing + volume_declining > 0
                else 0
            ),
        },
        "market_sentiment": sentiment,
        "analysis_date": __import__("datetime").datetime.now().isoformat(),
    }
