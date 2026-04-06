# Created: 2026-04-06
# Purpose: 선물옵션 종목 마스터 다운로드/캐싱/검색
# Dependencies: urllib, zipfile (표준 라이브러리만 사용)
"""
선물옵션 종목 마스터 유틸리티

한국투자증권 마스터파일 서버에서 지수선물옵션/상품선물옵션 전종목을
다운로드하고 로컬 캐시에 저장한다.
단축코드(A01606) 또는 종목명(F 202606)으로 검색 가능.

마스터파일 종류:
  - fo_idx_code_mts.mst: 지수 선물/옵션 (KOSPI200, 미니, 코스닥150, 위클리 등)
  - fo_com_code.mst: 상품 선물/옵션 (금, 돈육, 달러 등)
"""

import csv
import io
import logging
import ssl
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

# 마스터파일 URL
_MASTER_URLS = {
    "index": "https://new.real.download.dws.co.kr/common/master/fo_idx_code_mts.mst.zip",
    "commodity": "https://new.real.download.dws.co.kr/common/master/fo_com_code.mst.zip",
}

# 캐시 디렉토리
_CACHE_DIR = Path.home() / ".kis_agent" / "master"

# 메모리 캐시
_futures_cache: List[Dict[str, str]] = []
_cache_date: Optional[str] = None

# 지수선물옵션 상품종류 코드
_IDX_TYPE_MAP = {
    "1": "지수선물",
    "2": "지수SP",
    "3": "스타선물",
    "4": "스타SP",
    "5": "지수콜옵션",
    "6": "지수풋옵션",
    "7": "변동성선물",
    "8": "변동성SP",
    "9": "섹터선물",
    "A": "섹터SP",
    "B": "미니선물",
    "C": "미니SP",
    "D": "미니콜옵션",
    "E": "미니풋옵션",
    "J": "코스닥150콜옵션",
    "K": "코스닥150풋옵션",
    "L": "위클리콜옵션",
    "M": "위클리풋옵션",
}

# 월물구분코드
_MONTH_TYPE_MAP = {
    "0": "연결선물",
    "1": "최근월물",
    "2": "차근월물",
    "3": "차차근월물",
    "4": "차차차근월물",
}


def _get_cache_path() -> Path:
    """캐시 CSV 경로."""
    return _CACHE_DIR / "futures.csv"


def _ssl_context() -> ssl.SSLContext:
    """SSL 컨텍스트 (한투 서버 호환)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _download_index_master() -> List[Dict[str, str]]:
    """지수 선물옵션 마스터파일 다운로드 및 파싱.

    파일 형식: 파이프(|) 구분
    상품종류|단축코드|표준코드|한글종목명|ATM구분|행사가|월물구분코드|기초자산단축코드|기초자산명
    """
    url = _MASTER_URLS["index"]
    with urllib.request.urlopen(url, context=_ssl_context(), timeout=30) as resp:
        content = resp.read()

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        raw = zf.read(zf.namelist()[0])

    symbols = []
    for line in raw.decode("cp949").strip().split("\n"):
        parts = line.split("|")
        if len(parts) < 9:
            continue

        product_type = parts[0].strip()
        symbols.append({
            "code": parts[1].strip(),
            "std_code": parts[2].strip(),
            "name": parts[3].strip(),
            "atm": parts[4].strip(),
            "strike": parts[5].strip(),
            "month_type": parts[6].strip(),
            "underlying_code": parts[7].strip(),
            "underlying_name": parts[8].strip(),
            "product_type": product_type,
            "product_type_name": _IDX_TYPE_MAP.get(product_type, product_type),
            "market": "index",
        })

    return symbols


def _download_commodity_master() -> List[Dict[str, str]]:
    """상품 선물옵션 마스터파일 다운로드 및 파싱.

    파일 형식: 고정폭 + 파이프 혼합
    상품구분(1) + 상품종류(1) + 단축코드(9) + 표준코드(12) + 한글종목명(32)
    + ... + 월물구분코드(1) + 기초자산단축코드(3) + 기초자산명(...)
    """
    url = _MASTER_URLS["commodity"]
    with urllib.request.urlopen(url, context=_ssl_context(), timeout=30) as resp:
        content = resp.read()

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        raw = zf.read(zf.namelist()[0])

    symbols = []
    for line in raw.decode("cp949").strip().split("\n"):
        if len(line) < 55:
            continue

        product_group = line[0:1]
        product_type = line[1:2]
        code = line[2:11].strip()
        std_code = line[11:23].strip()
        name = line[23:55].strip()

        # 나머지 부분에서 월물구분코드, 기초자산 추출
        rest = line[55:].lstrip()
        month_type = rest[8:9] if len(rest) > 8 else ""
        underlying_code = rest[9:12].strip() if len(rest) > 11 else ""
        underlying_name = rest[12:].strip() if len(rest) > 12 else ""

        symbols.append({
            "code": code,
            "std_code": std_code,
            "name": name,
            "atm": "",
            "strike": "",
            "month_type": month_type,
            "underlying_code": underlying_code,
            "underlying_name": underlying_name,
            "product_type": f"{product_group}{product_type}",
            "product_type_name": f"상품{product_type}",
            "market": "commodity",
        })

    return symbols


def _save_cache(symbols: List[Dict[str, str]]) -> None:
    """CSV로 캐시 저장."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _get_cache_path()
    fieldnames = [
        "code", "std_code", "name", "atm", "strike",
        "month_type", "underlying_code", "underlying_name",
        "product_type", "product_type_name", "market",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(symbols)
    logger.info(f"선물옵션 마스터 캐시 저장: {len(symbols)}개 → {path}")


def _load_cache() -> List[Dict[str, str]]:
    """CSV 캐시 로드."""
    path = _get_cache_path()
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _is_cache_fresh() -> bool:
    """캐시가 오늘 날짜인지 확인."""
    path = _get_cache_path()
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime.strftime("%Y%m%d") == datetime.now().strftime("%Y%m%d")


def load_futures(
    force_refresh: bool = False,
    markets: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    선물옵션 마스터 로드 (캐시 우선, 하루 1회 갱신).

    Args:
        force_refresh: 캐시 무시하고 새로 다운로드
        markets: 로드할 시장 ["index", "commodity"]. None이면 전체.

    Returns:
        [{"code": "A01606", "name": "F 202606", "product_type_name": "지수선물", ...}, ...]
    """
    global _futures_cache, _cache_date

    today = datetime.now().strftime("%Y%m%d")

    # 메모리 캐시 히트
    if _futures_cache and _cache_date == today and not force_refresh:
        return _filter_markets(_futures_cache, markets)

    # 파일 캐시 히트
    if not force_refresh and _is_cache_fresh():
        _futures_cache = _load_cache()
        _cache_date = today
        if _futures_cache:
            logger.info(f"선물옵션 마스터 캐시 로드: {len(_futures_cache)}개")
            return _filter_markets(_futures_cache, markets)

    # 다운로드
    try:
        symbols: List[Dict[str, str]] = []

        idx_result = _download_index_master()
        symbols.extend(idx_result)
        logger.info(f"지수선물옵션 종목 수집: {len(idx_result)}개")

        com_result = _download_commodity_master()
        symbols.extend(com_result)
        logger.info(f"상품선물옵션 종목 수집: {len(com_result)}개")

        if symbols:
            _save_cache(symbols)
            _futures_cache = symbols
            _cache_date = today
        return _filter_markets(symbols, markets)

    except Exception as e:
        logger.warning(f"선물옵션 마스터 다운로드 실패: {e}")
        cached = _load_cache()
        if cached:
            _futures_cache = cached
            _cache_date = today
            logger.info(f"만료된 캐시 사용: {len(cached)}개")
            return _filter_markets(cached, markets)
        return []


def _filter_markets(
    symbols: List[Dict[str, str]],
    markets: Optional[List[str]],
) -> List[Dict[str, str]]:
    """시장 필터링."""
    if not markets:
        return symbols
    return [s for s in symbols if s.get("market") in markets]


def search(
    query: str,
    limit: int = 20,
    product_types: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    단축코드 또는 종목명으로 검색.

    Args:
        query: 검색어 (단축코드 또는 종목명 부분 매칭)
        limit: 최대 결과 수
        product_types: 필터링할 상품종류 이름 리스트
                      (예: ["지수선물", "미니선물"])

    Returns:
        매칭된 종목 리스트
    """
    symbols = load_futures()
    if not symbols:
        return []

    # 상품종류 필터
    if product_types:
        pt_lower = [pt.lower() for pt in product_types]
        symbols = [
            s for s in symbols
            if s.get("product_type_name", "").lower() in pt_lower
        ]

    q = query.strip().upper()

    # 단축코드 정확 매칭
    for s in symbols:
        if s["code"].upper() == q:
            return [s]

    # 종목명 검색
    q_lower = query.strip().lower()
    exact, prefix, partial = [], [], []

    for s in symbols:
        name_lower = s["name"].lower()
        code_lower = s["code"].lower()
        if name_lower == q_lower:
            exact.append(s)
        elif name_lower.startswith(q_lower) or code_lower.startswith(q_lower):
            prefix.append(s)
        elif q_lower in name_lower or q_lower in code_lower:
            partial.append(s)

    return (exact + prefix + partial)[:limit]


def get_current_futures(
    product: Literal["kospi200", "mini", "kosdaq150"] = "kospi200",
) -> Optional[Dict[str, str]]:
    """
    현재 근월물 선물 종목 조회.

    Args:
        product: 상품 종류

    Returns:
        근월물 종목 정보 dict 또는 None
    """
    type_map = {
        "kospi200": "지수선물",
        "mini": "미니선물",
        "kosdaq150": "섹터선물",
    }
    product_type_name = type_map.get(product, "지수선물")

    symbols = load_futures()
    candidates = [
        s for s in symbols
        if s.get("product_type_name") == product_type_name
        and s.get("month_type") == "1"  # 최근월물
    ]

    return candidates[0] if candidates else None


def get_futures_by_month_type(
    month_type: str = "1",
    product_type_name: str = "지수선물",
) -> List[Dict[str, str]]:
    """
    월물구분코드로 선물 종목 필터링.

    Args:
        month_type: "0"=연결, "1"=최근월물, "2"=차근월물, ...
        product_type_name: 상품종류명

    Returns:
        매칭된 종목 리스트
    """
    symbols = load_futures()
    return [
        s for s in symbols
        if s.get("month_type") == month_type
        and s.get("product_type_name") == product_type_name
    ]


def resolve_futures_code(query: str) -> Optional[str]:
    """
    종목코드 또는 종목명을 단축코드로 변환.

    Args:
        query: 단축코드, 종목명, 또는 "F 202606" 형태

    Returns:
        단축코드 (예: "A01606") 또는 None
    """
    q = query.strip()

    # 이미 단축코드 형태면 그대로
    results = search(q, limit=1)
    if results:
        return results[0]["code"]
    return None
