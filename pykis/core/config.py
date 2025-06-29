import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class KISConfig:
    """API 인증 및 계좌 정보를 관리하는 설정 클래스"""

    APP_KEY: str = ""
    APP_SECRET: str = ""
    BASE_URL: str = ""
    ACCOUNT_NO: str = ""
    ACCOUNT_CODE: str = ""

    def __init__(self, env_path: str = ".env"):
        """환경 변수 파일(.env)에서 설정을 초기화합니다."""
        if not os.path.exists(env_path):
            raise FileNotFoundError(
                f"'{env_path}' 파일을 찾을 수 없습니다. '.env.example' 파일을 복사하여 설정 후 사용하세요."
            )
        load_dotenv(dotenv_path=env_path)

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
            raise Exception("필수 설정 값이 누락되었습니다. .env 파일의 내용을 확인하세요.")

__all__ = ["KISConfig"]
