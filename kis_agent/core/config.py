import os
from dataclasses import dataclass

from .constants import MOCK_BASE_URL, REAL_BASE_URL, resolve_environment


@dataclass
class KISConfig:
    """API 인증 및 계좌 정보를 관리하는 설정 클래스.

    환경변수 자동 로드를 지원한다.

    - `KISConfig(app_key=..., ...)`로 매개변수 직접 전달 가능.
    - `KISConfig.from_env()`로 환경변수에서 일괄 로드 가능 (KIS_* prefix만 인식).
    - `.env` 파일은 `kis_agent.core.auth` 임포트 시 자동 로드된다 (override=False — 기존 환경변수 우선).
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
        paper: bool = None,
    ):
        self.APP_KEY = app_key or ""
        self.APP_SECRET = app_secret or ""
        # base_url이 없으면 paper / KIS_PAPER / KIS_BASE_URL로 결정한다.
        # 여기서 REAL_BASE_URL로 바로 떨어뜨리면 진입점마다 동작이 갈린다.
        self.BASE_URL, _ = resolve_environment(base_url=base_url, paper=paper)
        self.ACCOUNT_NO = account_no or ""
        self.ACCOUNT_CODE = account_code or ""

        self._validate()

    @classmethod
    def from_env(cls) -> "KISConfig":
        """환경변수에서 KISConfig를 생성한다.

        인식하는 환경변수 (KIS_* prefix 전용 — legacy MY_*/PROD_URL 등은 인식하지 않음):

        - `KIS_APP_KEY` (필수)
        - `KIS_APP_SECRET` (필수)
        - `KIS_ACCOUNT_NO` (필수)
        - `KIS_ACCOUNT_CODE` (선택, 기본 "01")
        - `KIS_PAPER` (선택, 1/true/yes/on 이면 모의투자)
        - `KIS_BASE_URL` (선택, 기본 실전투자 URL)

        Raises:
            ValueError: 필수 환경변수가 누락된 경우, `KIS_PAPER` 값이
                올바르지 않은 경우, 또는 `KIS_PAPER`와 `KIS_BASE_URL`이
                서로 모순되는 경우.
        """
        # base_url을 넘기지 않으면 __init__이 KIS_PAPER/KIS_BASE_URL을 해석한다.
        return cls(
            app_key=os.environ.get("KIS_APP_KEY", ""),
            app_secret=os.environ.get("KIS_APP_SECRET", ""),
            account_no=os.environ.get("KIS_ACCOUNT_NO", ""),
            account_code=os.environ.get("KIS_ACCOUNT_CODE", "01"),
        )

    @property
    def account_stock(self) -> str:
        return self.ACCOUNT_NO

    @property
    def account_product(self) -> str:
        return self.ACCOUNT_CODE

    @property
    def app_key(self) -> str:
        return self.APP_KEY

    @property
    def app_secret(self) -> str:
        return self.APP_SECRET

    @property
    def account_no(self) -> str:
        return self.ACCOUNT_NO

    @property
    def account_product_code(self) -> str:
        return self.ACCOUNT_CODE

    @property
    def is_real(self) -> bool:
        """실전투자 여부 (BASE_URL이 실전 URL과 일치하면 True)."""
        return MOCK_BASE_URL not in self.BASE_URL

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
                "필요한 모든 매개변수를 제공하거나 KIS_APP_KEY/KIS_APP_SECRET/"
                "KIS_ACCOUNT_NO 환경변수를 설정한 뒤 KISConfig.from_env()를 사용하세요."
            )


__all__ = ["KISConfig"]
