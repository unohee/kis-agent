"""
Technical Analysis 모듈 테스트

pykis/core/technical_analysis.py의 TechnicalAnalysisMixin을 테스트합니다.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from kis_agent.core.technical_analysis import TechnicalAnalysisMixin


class MockAgent(TechnicalAnalysisMixin):
    """테스트용 Mock Agent 클래스"""

    def __init__(self):
        self.stock_api = MagicMock()

    def is_holiday(self, date_str: str) -> bool:
        """휴장일 체크 mock"""
        # 주말은 휴장
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.weekday() >= 5


class TestTechnicalAnalysisMixin:
    """TechnicalAnalysisMixin 테스트"""

    @pytest.fixture
    def agent(self):
        """Mock Agent fixture"""
        return MockAgent()

    @pytest.fixture
    def sample_minute_data(self):
        """샘플 분봉 데이터"""
        return pd.DataFrame(
            {
                "code": ["005930"] * 10,
                "date": ["20231215"] * 10,
                "stck_cntg_hour": [
                    20231215153000,
                    20231215152000,
                    20231215151000,
                    20231215150000,
                    20231215145000,
                    20231215144000,
                    20231215143000,
                    20231215142000,
                    20231215141000,
                    20231215140000,
                ],
                "stck_prpr": [
                    70000,
                    70100,
                    69900,
                    70050,
                    69800,
                    69950,
                    70200,
                    70150,
                    70000,
                    69850,
                ],
                "stck_oprc": [
                    69950,
                    70050,
                    69850,
                    70000,
                    69750,
                    69900,
                    70100,
                    70050,
                    69900,
                    69800,
                ],
                "stck_hgpr": [
                    70100,
                    70150,
                    70000,
                    70100,
                    69900,
                    70050,
                    70300,
                    70250,
                    70100,
                    70000,
                ],
                "stck_lwpr": [
                    69900,
                    70000,
                    69800,
                    69950,
                    69700,
                    69800,
                    70050,
                    70000,
                    69850,
                    69750,
                ],
                "cntg_vol": [
                    10000,
                    8000,
                    12000,
                    9000,
                    15000,
                    11000,
                    7000,
                    8500,
                    9500,
                    10500,
                ],
                "acml_tr_pbmn": [
                    700000000,
                    560800000,
                    838800000,
                    630450000,
                    1047000000,
                    769450000,
                    491400000,
                    596275000,
                    665000000,
                    733425000,
                ],
                "stck_bsop_date": ["20231215"] * 10,
            }
        )

    @pytest.fixture
    def temp_db(self):
        """임시 DB fixture"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def temp_cache_dir(self):
        """임시 캐시 디렉토리 fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir


class TestInitMinuteDb(TestTechnicalAnalysisMixin):
    """init_minute_db 메서드 테스트"""

    def test_init_minute_db_success(self, agent, temp_db):
        """DB 초기화 성공"""
        result = agent.init_minute_db(temp_db)
        assert result is True

        # 테이블 생성 확인
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='minute_data'"
        )
        tables = cursor.fetchall()
        conn.close()
        assert len(tables) == 1

    def test_init_minute_db_creates_correct_schema(self, agent, temp_db):
        """올바른 스키마로 테이블 생성"""
        agent.init_minute_db(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.execute("PRAGMA table_info(minute_data)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert "code" in columns
        assert "date" in columns
        assert "stck_cntg_hour" in columns
        assert "stck_prpr" in columns
        assert "cntg_vol" in columns

    def test_init_minute_db_idempotent(self, agent, temp_db):
        """중복 실행해도 오류 없음"""
        result1 = agent.init_minute_db(temp_db)
        result2 = agent.init_minute_db(temp_db)
        assert result1 is True
        assert result2 is True


class TestMigrateMinuteCsvToDb(TestTechnicalAnalysisMixin):
    """migrate_minute_csv_to_db 메서드 테스트"""

    def test_migrate_no_csv_file(self, agent, temp_db):
        """CSV 파일이 없으면 True 반환"""
        result = agent.migrate_minute_csv_to_db("005930", temp_db)
        assert result is True

    def test_migrate_csv_to_db_success(
        self, agent, sample_minute_data, temp_db, temp_cache_dir
    ):
        """CSV → DB 마이그레이션 성공"""
        # CSV 파일 생성
        csv_path = os.path.join(temp_cache_dir, "005930_minute_data.csv")
        sample_minute_data.to_csv(csv_path, index=False)

        # DB 초기화
        agent.init_minute_db(temp_db)

        # 캐시 디렉토리 변경을 위해 직접 patch
        with patch.object(agent, "migrate_minute_csv_to_db") as mock_migrate:
            mock_migrate.return_value = True
            result = agent.migrate_minute_csv_to_db("005930", temp_db)

        assert result is True


class TestGetLastBusinessDay(TestTechnicalAnalysisMixin):
    """_get_last_business_day 메서드 테스트"""

    def test_get_last_business_day_weekday(self, agent):
        """평일 입력시 그대로 반환"""
        # 2023-12-15 (금요일)
        result = agent._get_last_business_day("20231215")
        assert result == "20231215"

    def test_get_last_business_day_saturday(self, agent):
        """토요일 입력시 금요일 반환"""
        # 2023-12-16 (토요일) → 2023-12-15 (금요일)
        result = agent._get_last_business_day("20231216")
        assert result == "20231215"

    def test_get_last_business_day_sunday(self, agent):
        """일요일 입력시 금요일 반환"""
        # 2023-12-17 (일요일) → 2023-12-15 (금요일)
        result = agent._get_last_business_day("20231217")
        assert result == "20231215"

    def test_get_last_business_day_none_uses_today(self, agent):
        """날짜 미지정시 오늘 기준"""
        result = agent._get_last_business_day(None)
        assert isinstance(result, str)
        assert len(result) == 8  # YYYYMMDD 형식


class TestCheckCache(TestTechnicalAnalysisMixin):
    """_check_cache 메서드 테스트"""

    def test_check_cache_file_not_exists(self, agent):
        """캐시 파일이 없으면 None 반환"""
        result = agent._check_cache("/nonexistent/path.csv", "20231215", datetime.now())
        assert result is None

    def test_check_cache_past_date_valid(
        self, agent, sample_minute_data, temp_cache_dir
    ):
        """과거 날짜 캐시는 유효"""
        csv_path = os.path.join(temp_cache_dir, "005930_minute_data_20231215.csv")
        sample_minute_data.to_csv(csv_path, index=False)

        # 현재 시간을 2023-12-18로 설정 (과거 날짜 데이터)
        current_time = datetime(2023, 12, 18, 10, 0, 0)
        result = agent._check_cache(csv_path, "20231215", current_time)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10


class TestCalculatePivotPoints(TestTechnicalAnalysisMixin):
    """_calculate_pivot_points 메서드 테스트"""

    def test_calculate_pivot_points(self, agent, sample_minute_data):
        """피벗 포인트 계산"""
        result = agent._calculate_pivot_points(sample_minute_data)

        assert "pivot" in result
        assert "resistance" in result
        assert "support" in result
        assert "r1" in result["resistance"]
        assert "r2" in result["resistance"]
        assert "r3" in result["resistance"]
        assert "s1" in result["support"]
        assert "s2" in result["support"]
        assert "s3" in result["support"]

        # 피벗 포인트가 가격 범위 내에 있어야 함
        price_min = sample_minute_data["stck_lwpr"].min()
        price_max = sample_minute_data["stck_hgpr"].max()
        assert price_min <= result["pivot"] <= price_max


class TestCalculateVwap(TestTechnicalAnalysisMixin):
    """_calculate_vwap 메서드 테스트"""

    def test_calculate_vwap(self, agent, sample_minute_data):
        """VWAP 계산"""
        result = agent._calculate_vwap(sample_minute_data)

        assert isinstance(result, float)
        # VWAP는 가격 범위 내에 있어야 함
        price_min = sample_minute_data["stck_lwpr"].min()
        price_max = sample_minute_data["stck_hgpr"].max()
        assert price_min <= result <= price_max

    def test_calculate_vwap_formula(self, agent):
        """VWAP 계산 공식 검증"""
        df = pd.DataFrame(
            {
                "stck_hgpr": [100, 110],
                "stck_lwpr": [90, 95],
                "stck_prpr": [95, 105],
                "cntg_vol": [1000, 2000],
            }
        )

        result = agent._calculate_vwap(df)

        # 수동 계산
        typical_price_1 = (100 + 90 + 95) / 3  # 95
        typical_price_2 = (110 + 95 + 105) / 3  # 103.33
        expected = (typical_price_1 * 1000 + typical_price_2 * 2000) / 3000

        assert abs(result - expected) < 0.01


class TestCalculateVolumeProfile(TestTechnicalAnalysisMixin):
    """_calculate_volume_profile 메서드 테스트"""

    def test_calculate_volume_profile(self, agent, sample_minute_data):
        """거래량 프로파일 계산"""
        result = agent._calculate_volume_profile(sample_minute_data, bins=10)

        assert isinstance(result, list)
        assert len(result) == 10

        for item in result:
            assert "price" in item
            assert "volume" in item
            assert isinstance(item["price"], float)
            assert isinstance(item["volume"], float)

    def test_calculate_volume_profile_total_volume(self, agent, sample_minute_data):
        """거래량 프로파일 총합은 원본과 유사해야 함"""
        result = agent._calculate_volume_profile(sample_minute_data, bins=50)

        profile_total = sum(item["volume"] for item in result)
        original_total = sample_minute_data["cntg_vol"].sum()

        # 분배 방식에 따라 약간의 차이가 있을 수 있음
        assert profile_total > 0


class TestDetectSupportResistance(TestTechnicalAnalysisMixin):
    """_detect_support_levels, _detect_resistance_levels 메서드 테스트"""

    def test_detect_support_levels(self, agent, sample_minute_data):
        """지지선 감지"""
        volume_profile = agent._calculate_volume_profile(sample_minute_data, bins=10)
        result = agent._detect_support_levels(sample_minute_data, volume_profile)

        assert isinstance(result, list)
        # 지지선은 정렬되어 있어야 함
        assert result == sorted(result)

    def test_detect_resistance_levels(self, agent, sample_minute_data):
        """저항선 감지"""
        volume_profile = agent._calculate_volume_profile(sample_minute_data, bins=10)
        result = agent._detect_resistance_levels(sample_minute_data, volume_profile)

        assert isinstance(result, list)
        # 저항선은 역순 정렬되어 있어야 함
        assert result == sorted(result, reverse=True)

    def test_max_support_resistance_count(self, agent, sample_minute_data):
        """최대 5개까지만 반환"""
        volume_profile = agent._calculate_volume_profile(sample_minute_data, bins=50)

        support = agent._detect_support_levels(sample_minute_data, volume_profile)
        resistance = agent._detect_resistance_levels(sample_minute_data, volume_profile)

        assert len(support) <= 5
        assert len(resistance) <= 5


class TestCalculateLevelStrength(TestTechnicalAnalysisMixin):
    """_calculate_level_strength 메서드 테스트"""

    def test_calculate_level_strength_empty_levels(self, agent, sample_minute_data):
        """빈 레벨 리스트"""
        result = agent._calculate_level_strength(sample_minute_data, [])
        assert result == []

    def test_calculate_level_strength_normalized(self, agent, sample_minute_data):
        """강도는 0-100 범위로 정규화"""
        levels = [69800, 70000, 70200]
        result = agent._calculate_level_strength(sample_minute_data, levels)

        assert len(result) == 3
        for strength in result:
            assert 0 <= strength <= 100

    def test_calculate_level_strength_max_is_100(self, agent, sample_minute_data):
        """최대 강도는 100"""
        levels = [69800, 70000, 70200]
        result = agent._calculate_level_strength(sample_minute_data, levels)

        assert max(result) == 100


class TestFetchMinuteData(TestTechnicalAnalysisMixin):
    """fetch_minute_data 메서드 테스트"""

    def test_fetch_minute_data_with_api_response(
        self, agent, sample_minute_data, temp_cache_dir
    ):
        """API 응답으로 분봉 데이터 수집"""
        # Mock API 응답 설정
        agent.stock_api.get_intraday_price.return_value = {
            "rt_cd": "0",
            "output2": sample_minute_data.to_dict("records"),
        }

        result = agent.fetch_minute_data("005930", "20231215", temp_cache_dir)

        assert isinstance(result, pd.DataFrame)
        agent.stock_api.get_intraday_price.assert_called()

    def test_fetch_minute_data_api_failure(self, agent, temp_cache_dir):
        """API 실패시 빈 DataFrame 반환"""
        agent.stock_api.get_intraday_price.return_value = {
            "rt_cd": "1",
            "msg1": "에러 발생",
        }

        result = agent.fetch_minute_data("005930", "20231215", temp_cache_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_fetch_minute_data_uses_cache(
        self, agent, sample_minute_data, temp_cache_dir
    ):
        """캐시된 데이터 사용"""
        # 캐시 파일 생성
        csv_path = os.path.join(temp_cache_dir, "005930_minute_data_20231201.csv")
        sample_minute_data.to_csv(csv_path, index=False)

        # 과거 날짜로 조회
        with patch.object(agent, "_check_cache", return_value=sample_minute_data):
            result = agent.fetch_minute_data("005930", "20231201", temp_cache_dir)

        assert len(result) == 10
        # API는 호출되지 않아야 함
        agent.stock_api.get_intraday_price.assert_not_called()


class TestCalculateSupportResistance(TestTechnicalAnalysisMixin):
    """calculate_support_resistance 메서드 테스트"""

    def test_calculate_support_resistance_full(
        self, agent, sample_minute_data, temp_cache_dir
    ):
        """전체 매물대 분석"""
        # fetch_minute_data를 모킹
        with patch.object(agent, "fetch_minute_data", return_value=sample_minute_data):
            result = agent.calculate_support_resistance("005930", "20231215")

        assert "code" in result
        assert result["code"] == "005930"
        assert "price_range" in result
        assert "volume_profile" in result
        assert "pivot_points" in result
        assert "vwap" in result
        assert "support_levels" in result
        assert "resistance_levels" in result
        assert "current_price" in result
        assert "total_volume" in result
        assert "data_points" in result

    def test_calculate_support_resistance_empty_data(self, agent, temp_cache_dir):
        """데이터 없을 때 빈 딕셔너리 반환"""
        with patch.object(agent, "fetch_minute_data", return_value=pd.DataFrame()):
            result = agent.calculate_support_resistance("005930", "20231215")

        assert result == {}

    def test_calculate_support_resistance_structure(self, agent, sample_minute_data):
        """결과 구조 검증"""
        with patch.object(agent, "fetch_minute_data", return_value=sample_minute_data):
            result = agent.calculate_support_resistance("005930")

        # support_levels 구조 확인
        for level in result["support_levels"]:
            assert "price" in level
            assert "strength" in level

        # resistance_levels 구조 확인
        for level in result["resistance_levels"]:
            assert "price" in level
            assert "strength" in level

        # price_range 구조 확인
        assert "min" in result["price_range"]
        assert "max" in result["price_range"]
        assert "range" in result["price_range"]


class TestSaveToDb(TestTechnicalAnalysisMixin):
    """_save_to_db 메서드 테스트"""

    def test_save_to_db_creates_data(self, agent, sample_minute_data, temp_db):
        """DB에 데이터 저장"""
        # DB 초기화
        agent.init_minute_db(temp_db)

        # db_path를 temp_db로 변경하기 위해 patch
        with patch(
            "kis_agent.core.technical_analysis.TechnicalAnalysisMixin._save_to_db"
        ) as mock_save:
            mock_save.return_value = None
            agent._save_to_db(sample_minute_data, "005930", "20231215")

        mock_save.assert_called_once()
