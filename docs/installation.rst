설치 가이드
==========

요구사항
-------

* Python 3.8 이상
* pip (Python 패키지 관리자)

설치 방법
--------

pip를 사용한 설치
~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install kis-agent

개발 버전 설치
~~~~~~~~~~~~

소스 코드에서 직접 설치하려면:

.. code-block:: bash

   git clone https://github.com/your-username/kis-agent.git
   cd kis-agent
   pip install -e .

개발 의존성 설치
~~~~~~~~~~~~~

개발 도구와 문서화 도구를 포함한 모든 의존성을 설치하려면:

.. code-block:: bash

   pip install -e ".[dev]"

환경 설정
--------

1. `.env` 파일 생성:

.. code-block:: bash

   cp .env.example .env

2. `.env` 파일에 API 키와 계좌 정보 설정:

.. code-block:: text

   KIS_APP_KEY=your_app_key_here
   KIS_APP_SECRET=your_app_secret_here
   KIS_ACCOUNT_STOCK=your_stock_account_here
   KIS_ACCOUNT_PRODUCT=your_account_product_here

문제 해결
--------

일반적인 문제
~~~~~~~~~~~

1. 인증 오류
   * API 키와 시크릿이 올바르게 설정되었는지 확인
   * 계좌 정보가 올바른지 확인

2. 설치 오류
   * Python 버전이 3.8 이상인지 확인
   * pip가 최신 버전인지 확인

3. 실행 오류
   * 가상환경이 활성화되어 있는지 확인
   * 필요한 모든 의존성이 설치되어 있는지 확인 