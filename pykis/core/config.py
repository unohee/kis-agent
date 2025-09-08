import os
from dataclasses import dataclass
from dotenv import dotenv_values

@dataclass
class KISConfig:
    """API 인증 및 계좌 정보를 관리하는 설정 클래스"""

    APP_KEY: str = ""
    APP_SECRET: str = ""
    BASE_URL: str = ""
    ACCOUNT_NO: str = ""
    ACCOUNT_CODE: str = ""

    def __init__(self, env_path: str = None, app_key: str = None, app_secret: str = None, base_url: str = None, account_no: str = None, account_code: str = None):
        """
        설정을 초기화합니다.
        
        Args:
            env_path (str, optional): .env 파일 경로 (호환성 유지용)
            app_key (str): API 앱 키
            app_secret (str): API 앱 시크릿
            base_url (str): API 베이스 URL
            account_no (str): 계좌번호
            account_code (str): 계좌 상품코드
        
        Note:
            env_path가 제공되면 .env 파일에서 로드하고,
            개별 매개변수가 제공되면 해당 값을 사용합니다.
        """
        # env_path가 제공되면 .env 파일에서 로드 (호환성)
        if env_path is not None:
            if not os.path.exists(env_path):
                raise FileNotFoundError(
                    f"'{env_path}' 파일을 찾을 수 없습니다."
                )
            
            config = dotenv_values(dotenv_path=env_path)
            
            # .env 파일에서 값 로드 (개별 매개변수가 우선)
            self.APP_KEY = app_key or (
                config.get("APP_KEY") or config.get("KIS_APP_KEY") or 
                config.get("KIS_APPKEY") or config.get("MY_APP") or 
                os.environ.get("APP_KEY") or os.environ.get("KIS_APP_KEY") or ""
            )
            self.APP_SECRET = app_secret or (
                config.get("APP_SECRET") or config.get("KIS_APP_SECRET") or 
                config.get("KIS_APPSECRET") or config.get("MY_SEC") or 
                os.environ.get("APP_SECRET") or os.environ.get("KIS_APP_SECRET") or ""
            )
            self.BASE_URL = base_url or (
                config.get("KIS_BASE_URL") or config.get("BASE_URL") or 
                config.get("PROD_URL") or os.environ.get("KIS_BASE_URL") or 
                "https://openapi.koreainvestment.com:9443"
            )
            self.ACCOUNT_NO = account_no or (
                config.get("CANO") or config.get("KIS_ACCOUNT_NO") or 
                config.get("MY_ACCT_STOCK") or os.environ.get("CANO") or ""
            )
            self.ACCOUNT_CODE = account_code or (
                config.get("ACNT_PRDT_CD") or config.get("KIS_ACCOUNT_CODE") or 
                config.get("MY_PROD") or os.environ.get("ACNT_PRDT_CD") or ""
            )
        else:
            # 직접 매개변수 사용
            self.APP_KEY = app_key or ""
            self.APP_SECRET = app_secret or ""
            self.BASE_URL = base_url or "https://openapi.koreainvestment.com:9443"
            self.ACCOUNT_NO = account_no or ""
            self.ACCOUNT_CODE = account_code or ""
        
        self._validate()

    @property
    def account_stock(self) -> str:
        """계좌 번호 반환"""
        return self.ACCOUNT_NO

    @property
    def account_product(self) -> str:
        """계좌 상품 코드 반환"""
        return self.ACCOUNT_CODE
    
    @property
    def app_key(self) -> str:
        """APP KEY 반환"""
        return self.APP_KEY
    
    @property
    def app_secret(self) -> str:
        """APP SECRET 반환"""
        return self.APP_SECRET
    
    @property
    def account_no(self) -> str:
        """계좌 번호 반환"""
        return self.ACCOUNT_NO
    
    @property
    def account_product_code(self) -> str:
        """계좌 상품 코드 반환"""
        return self.ACCOUNT_CODE
    
    @property
    def is_real(self) -> bool:
        """실투자 여부 (BASE_URL로 판단)"""
        return "openapi.koreainvestment.com:9443" in self.BASE_URL

    def _validate(self) -> None:
        missing_fields = []
        if not self.APP_KEY:
            missing_fields.append("app_key")
        if not self.APP_SECRET:
            missing_fields.append("app_secret")
        if not self.BASE_URL:
            missing_fields.append("base_url")
        if not self.ACCOUNT_NO:
            missing_fields.append("account_no")
        if not self.ACCOUNT_CODE:
            missing_fields.append("account_code")
        
        if missing_fields:
            raise ValueError(
                f"필수 설정 값이 누락되었습니다: {', '.join(missing_fields)}\n"
                "필요한 모든 매개변수를 제공해주세요."
            )

__all__ = ["KISConfig"]
