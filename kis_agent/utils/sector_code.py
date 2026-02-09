"""
업종코드 마스터 데이터 다운로드 및 파싱

한국투자증권 마스터 파일 서버에서 업종코드(idxcode.mst)를 다운로드하고
파싱하여 DataFrame 또는 Dict 형태로 반환합니다.

데이터 출처: https://new.real.download.dws.co.kr/common/master/idxcode.mst.zip

코스피 업종코드 (market_div=0):
    0001: 종합              0002: 대형주            0003: 중형주            0004: 소형주
    0005: 음식료·담배       0006: 섬유·의류         0007: 종이·목재         0008: 화학
    0009: 제약              0010: 비금속            0011: 금속              0012: 기계·장비
    0013: 전기·전자         0014: 의료·정밀기기     0015: 운송장비·부품     0016: 유통
    0017: 전기·가스         0018: 건설              0019: 운송·창고         0020: 통신
    0021: 금융              0024: 증권              0025: 보험              0026: 일반서비스
    0027: 제조              0028: 부동산            0029: IT 서비스         0030: 오락·문화
    0163: 고배당50          0164: 배당성장50        0165: 우선주            0195: 코스피 TR
    0241: 코스피 고배당 50 TR                       0242: 코스피 배당성장 50 TR
    0244: 코스피200제외 코스피지수                  0503: VKOSPI

코스닥 업종코드 (market_div=1):
    1001: KOSDAQ            1002: 코스닥 대형주     1003: 코스닥 중형주     1004: 코스닥 소형주
    1006: 일반서비스        1009: 제조              1010: 건설              1011: 유통
    1013: 운송·창고         1014: 금융              1015: 오락·문화         1019: 음식료·담배
    1020: 섬유·의류         1021: 종이·목재         1022: 출판·매체복제     1023: 화학
    1024: 제약              1025: 비금속            1026: 금속              1027: 기계·장비
    1028: 전기·전자         1029: 의료·정밀기기     1030: 운송장비·부품     1031: 기타제조
    1032: 통신              1033: IT 서비스         1042: 우량기업          1043: 벤처기업
    1044: 중견기업          1045: 기술성장기업      1049: 코스닥 글로벌     1196: 코스닥 TR
    1331: 코스닥 150 거버넌스
"""

import contextlib
import os
import ssl
import tempfile
import urllib.request
import zipfile
from typing import Dict, Optional

import pandas as pd

# 업종코드 MST 파일 URL
SECTOR_CODE_URL = "https://new.real.download.dws.co.kr/common/master/idxcode.mst.zip"

# 업종코드 구조 (업종코드정보.h 참조)
# idx_div[1]: 시장구분값 (ex: 00002에서 맨 앞 0)
# idx_code[4]: 업종코드 (ex: 00002에서 0002)
# idx_name[40]: 업종명


def download_sector_code_mst(download_dir: Optional[str] = None) -> str:
    """
    업종코드 MST 파일 다운로드

    Args:
        download_dir: 다운로드 디렉토리 (기본: 임시 디렉토리)

    Returns:
        다운로드된 MST 파일 경로
    """
    if download_dir is None:
        download_dir = tempfile.gettempdir()

    # SSL 인증서 검증 비활성화 (한투 서버 호환)
    ssl._create_default_https_context = ssl._create_unverified_context

    zip_path = os.path.join(download_dir, "idxcode.zip")
    mst_path = os.path.join(download_dir, "idxcode.mst")

    # 다운로드
    urllib.request.urlretrieve(SECTOR_CODE_URL, zip_path)

    # 압축 해제
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(download_dir)

    # zip 파일 삭제
    os.remove(zip_path)

    return mst_path


def parse_sector_code_mst(mst_path: str) -> pd.DataFrame:
    """
    업종코드 MST 파일 파싱

    Args:
        mst_path: MST 파일 경로

    Returns:
        DataFrame with columns: ['market_div', 'sector_code', 'full_code', 'sector_name']
    """
    records = []

    with open(mst_path, encoding="cp949") as f:
        for row in f:
            if len(row) < 6:
                continue

            market_div = row[0:1]  # 시장구분 1자리 (0=코스피, 1=코스닥, 2=기타)
            sector_code = row[1:5]  # 업종코드 4자리
            full_code = row[0:5]  # 전체코드 5자리
            sector_name = row[5:].strip()  # 업종명 (가변 길이)

            records.append(
                {
                    "market_div": market_div,
                    "sector_code": sector_code,
                    "full_code": full_code,
                    "sector_name": sector_name,
                }
            )

    return pd.DataFrame(records)


def get_sector_codes(
    download_dir: Optional[str] = None, as_dict: bool = False
) -> pd.DataFrame | Dict[str, str]:
    """
    업종코드 마스터 데이터 조회

    한국투자증권 서버에서 업종코드 MST 파일을 다운로드하고 파싱합니다.

    Args:
        download_dir: 다운로드 디렉토리 (기본: 임시 디렉토리)
        as_dict: True면 {코드: 이름} Dict 반환, False면 DataFrame 반환

    Returns:
        DataFrame 또는 Dict

    Example:
        >>> df = get_sector_codes()
        >>> print(df.head())
           market_div sector_code full_code    sector_name
        0           0        0001     00001         코스피
        1           0        0002     00002         대형주
        ...

        >>> codes = get_sector_codes(as_dict=True)
        >>> print(codes['0001'])
        코스피
    """
    mst_path = download_sector_code_mst(download_dir)
    df = parse_sector_code_mst(mst_path)

    # MST 파일 삭제
    with contextlib.suppress(OSError):
        os.remove(mst_path)

    if as_dict:
        return dict(zip(df["sector_code"], df["sector_name"]))

    return df


def get_sector_code_by_market(market: str = "kospi") -> pd.DataFrame:
    """
    시장별 업종코드 조회

    Args:
        market: 시장 구분
            - "kospi" 또는 "0": 코스피 업종
            - "kosdaq" 또는 "1": 코스닥 업종
            - "other" 또는 "2": 기타 지수 (KOSPI200 등)
            - "all": 전체

    Returns:
        해당 시장의 업종코드 DataFrame
    """
    df = get_sector_codes()

    market_map = {
        "kospi": "0",
        "kosdaq": "1",
        "other": "2",
        "0": "0",
        "1": "1",
        "2": "2",
    }

    if market.lower() == "all":
        return df

    market_div = market_map.get(market.lower(), "0")
    return df[df["market_div"] == market_div]


# 주요 업종코드 상수 (자주 사용되는 코드)
# 참고: API 호출 시 market_div를 포함한 전체 코드(full_code) 사용
# 시장구분: 0=코스피, 1=코스닥, 2=KOSPI200관련, 3=KSQ150관련, 4=KRX, 6=기타, 7=동일가중
SECTOR_CODES = {
    # 코스피 주요 업종 (market_div=0)
    "KOSPI": "0001",  # 종합
    "KOSPI_LARGE": "0002",  # 대형주
    "KOSPI_MEDIUM": "0003",  # 중형주
    "KOSPI_SMALL": "0004",  # 소형주
    # 코스닥 주요 업종 (market_div=1)
    "KOSDAQ": "1001",  # KOSDAQ
    "KOSDAQ_LARGE": "1002",  # 코스닥 대형주
    "KOSDAQ_MEDIUM": "1003",  # 코스닥 중형주
    "KOSDAQ_SMALL": "1004",  # 코스닥 소형주
    # KOSPI200 관련 (market_div=2)
    "KOSPI200": "2001",  # KOSPI200
    "KOSPI100": "2007",  # KOSPI100
    "KOSPI50": "2008",  # KOSPI50
    # KOSDAQ150 관련 (market_div=3)
    "KOSDAQ150": "3003",  # KSQ150 (KOSDAQ 150)
    "KOSDAQ150_TR": "3197",  # 코스닥 150 TR
    # KRX 지수 (market_div=4)
    "KRX100": "4001",  # KRX100
    "KRX300": "4300",  # KRX300
}
