기여 가이드
==========

개발 환경 설정
-----------

1. 저장소 클론
~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/your-username/kis-agent.git
   cd kis-agent

2. 가상환경 설정
~~~~~~~~~~~~~

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows

3. 개발 의존성 설치
~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -e ".[dev]"

4. 환경 변수 설정
~~~~~~~~~~~~~

.. code-block:: bash

   cp .env.example .env
   # .env 파일을 편집하여 필요한 설정 추가

코드 스타일
---------

* Black을 사용한 코드 포맷팅
* isort를 사용한 import 정렬
* flake8을 사용한 코드 검사
* mypy를 사용한 타입 검사

테스트
-----

테스트 실행
~~~~~~~~~

.. code-block:: bash

   pytest tests/

코드 커버리지 확인
~~~~~~~~~~~~~~

.. code-block:: bash

   pytest --cov=src/kis tests/

문서화
-----

문서 빌드
~~~~~~~

.. code-block:: bash

   cd docs
   make html

문서 미리보기
~~~~~~~~~~

.. code-block:: bash

   cd docs
   python -m http.server -d _build/html

기여 프로세스
----------

1. 이슈 생성
~~~~~~~~~~

* 버그 리포트
* 기능 요청
* 문서 개선

2. 브랜치 생성
~~~~~~~~~~~

.. code-block:: bash

   git checkout -b feature/your-feature-name

3. 변경사항 커밋
~~~~~~~~~~~~

.. code-block:: bash

   git add .
   git commit -m "설명: 변경사항 요약"

4. Pull Request 생성
~~~~~~~~~~~~~~~~

* 변경사항 설명
* 관련 이슈 링크
* 테스트 결과
* 문서 업데이트 