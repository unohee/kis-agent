from dataclasses import dataclass


@dataclass
class KISConfig:
    """API 인증 및 계좌 정보를 관리하는 설정 클래스

    Note:
        .env 파일 지원이 제거되었습니다.
        API 키는 반드시 매개변수로 직정 전달해야 합니다.
    """

    APP_KEY: str = ""
    APP_SECRET: str = ""
    BASE_URL: str = ""
    ACCOUNT_NO: str = ""
    ACCOUNT_CODE: str = ""

    def __init__(
        self,
        app_key: str = None,
        app_secret: str = None,
        base_url: str = None,
        account_no: str = None,
        account_code: str = None,
    ):
        """
        설정을 초기화합니다.

        Args:
            app_key (str): API 앱 키 (필수)
            app_secret (str): API 앱 시크릿 (필수)
            base_url (str): API 베이스 URL (기본값: 실전투자 URL)
            account_no (str): 계좌번호 (필수)
            account_code (str): 계좌 상품코드 (필수)
        """
        # 매개변수 설정
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
