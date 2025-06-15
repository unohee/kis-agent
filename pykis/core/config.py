import os
import yaml
from dataclasses import dataclass

@dataclass
class KISConfig:
    """API 인증 및 계좌 정보를 관리하는 설정 클래스"""

    APP_KEY: str = ""
    APP_SECRET: str = ""
    BASE_URL: str = ""
    ACCOUNT_NO: str = ""
    ACCOUNT_CODE: str = ""

    def __init__(self, config_path: str = "./credit/kis_devlp.yaml"):
        """환경 변수와 YAML 파일에서 설정을 초기화합니다."""
        cfg = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
            # 파일이 존재하면 환경 변수는 무시
            self.APP_KEY = cfg.get("app_key", "")
            self.APP_SECRET = cfg.get("app_secret", "")
            self.BASE_URL = cfg.get("base_url", "")
            self.ACCOUNT_NO = cfg.get("account_no", "")
            self.ACCOUNT_CODE = cfg.get("account_code", "")
        else:
            # 파일이 없을 때만 환경 변수 사용
            self.APP_KEY = os.getenv("KIS_APP_KEY", "")
            self.APP_SECRET = os.getenv("KIS_APP_SECRET", "")
            self.BASE_URL = os.getenv("KIS_BASE_URL", "")
            self.ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO", "")
            self.ACCOUNT_CODE = os.getenv("KIS_ACCOUNT_CODE", "")
        self._validate()

    @property
    def account_stock(self) -> str:
        """계좌 번호 반환"""
        return self.ACCOUNT_NO

    @property
    def account_product(self) -> str:
        """계좌 상품 코드 반환"""
        return self.ACCOUNT_CODE

    def _validate(self) -> None:
        if not all([self.APP_KEY, self.APP_SECRET, self.BASE_URL, self.ACCOUNT_NO, self.ACCOUNT_CODE]):
            raise Exception("필수 설정 값이 누락되었습니다")

__all__ = ["KISConfig"]
