# Created: 2026-04-01
# Purpose: KRX 종목 마스터 다운로드/캐싱/검색
# Dependencies: urllib, zipfile (표준 라이브러리만 사용)
"""
KRX 종목 마스터 유틸리티

한국투자증권 마스터파일 서버에서 KOSPI/KOSDAQ 전종목 코드+이름을 다운로드하고
로컬 캐시에 저장한다. 종목코드 또는 종목명(부분 매칭)으로 검색 가능.
"""

import csv
import io
import logging
import ssl
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 마스터파일 URL
_MASTER_URLS = {
    "kospi": "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
    "kosdaq": "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
}

# 캐시 디렉토리
_CACHE_DIR = Path.home() / ".kis_agent" / "master"

# 메모리 캐시
_stock_cache: List[Dict[str, str]] = []
_cache_date: Optional[str] = None


def _get_cache_path() -> Path:
    """캐시 CSV 경로."""
    return _CACHE_DIR / "stocks.csv"


def _download_master(exchange: str) -> List[Dict[str, str]]:
    """마스터파일 다운로드 및 파싱 (동기)."""
    url = _MASTER_URLS[exchange]

    # SSL 인증서 검증 비활성화 (한투 서버 호환)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(url, context=ctx, timeout=30) as resp:
        content = resp.read()

    # ZIP 압축 해제
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            raw = zf.read(zf.namelist()[0])
    except zipfile.BadZipFile:
        raw = content

    # 파싱: EUC-KR, 고정 폭 (0-8: 단축코드, 21-60: 한글종목명)
    symbols = []
    for line in raw.split(b"\n"):
        if len(line) < 61:
            continue
        code = line[0:9].decode("euc-kr", errors="ignore").strip()
        name = line[21:61].decode("euc-kr", errors="ignore").strip()
        if len(code) > 6:
            code = code[-6:]
        if code and name and len(code) == 6:
            symbols.append({
                "code": code,
                "name": name,
                "market": "코스피" if exchange == "kospi" else "코스닥",
            })

    return symbols


def _save_cache(stocks: List[Dict[str, str]]) -> None:
    """CSV로 캐시 저장."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _get_cache_path()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name", "market"])
        writer.writeheader()
        writer.writerows(stocks)
    logger.info(f"종목 마스터 캐시 저장: {len(stocks)}개 → {path}")


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


def load_stocks(force_refresh: bool = False) -> List[Dict[str, str]]:
    """
    종목 마스터 로드 (캐시 우선, 하루 1회 갱신).

    Returns:
        [{"code": "005930", "name": "삼성전자", "market": "코스피"}, ...]
    """
    global _stock_cache, _cache_date

    today = datetime.now().strftime("%Y%m%d")

    # 메모리 캐시 히트
    if _stock_cache and _cache_date == today and not force_refresh:
        return _stock_cache

    # 파일 캐시 히트
    if not force_refresh and _is_cache_fresh():
        _stock_cache = _load_cache()
        _cache_date = today
        if _stock_cache:
            logger.info(f"종목 마스터 캐시 로드: {len(_stock_cache)}개")
            return _stock_cache

    # 다운로드
    try:
        stocks = []
        for exchange in ("kospi", "kosdaq"):
            result = _download_master(exchange)
            stocks.extend(result)
            logger.info(f"{exchange} 종목 수집: {len(result)}개")

        if stocks:
            _save_cache(stocks)
            _stock_cache = stocks
            _cache_date = today
        return stocks

    except Exception as e:
        logger.warning(f"마스터 다운로드 실패: {e}")
        # 파일 캐시 폴백 (만료되었더라도)
        cached = _load_cache()
        if cached:
            _stock_cache = cached
            _cache_date = today
            logger.info(f"만료된 캐시 사용: {len(cached)}개")
            return cached
        return []


def search(query: str, limit: int = 20) -> List[Dict[str, str]]:
    """
    종목코드 또는 종목명으로 검색.

    정확 매칭 → 이름이 검색어로 시작 → 부분 매칭 순으로 정렬.

    Args:
        query: 검색어 (종목코드 6자리 또는 종목명 부분 매칭)
        limit: 최대 결과 수

    Returns:
        [{"code": "005930", "name": "삼성전자", "market": "코스피"}, ...]
    """
    stocks = load_stocks()
    if not stocks:
        return []

    q = query.strip().upper()

    # 종목코드 정확 매칭 우선
    for s in stocks:
        if s["code"] == q:
            return [s]

    # 종목명 검색: 정확 → 접두사 → 부분 매칭 순서
    q_lower = query.strip().lower()
    exact = []
    prefix = []
    partial = []

    for s in stocks:
        name_lower = s["name"].lower()
        if name_lower == q_lower:
            exact.append(s)
        elif name_lower.startswith(q_lower):
            prefix.append(s)
        elif q_lower in name_lower or q_lower in s["code"].lower():
            partial.append(s)

    return (exact + prefix + partial)[:limit]


def resolve_code(query: str) -> Optional[str]:
    """
    종목코드 또는 종목명을 종목코드로 변환.
    6자리 숫자면 그대로 반환. 아니면 종목명으로 검색해서 첫 번째 결과 반환.

    Args:
        query: 종목코드 또는 종목명

    Returns:
        6자리 종목코드 또는 None
    """
    q = query.strip()
    if len(q) == 6 and q.isdigit():
        return q

    results = search(q, limit=1)
    if results:
        return results[0]["code"]
    return None
