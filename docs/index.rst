KIS_AGENT 문서
=============

한국투자증권 API를 Python으로 쉽게 사용할 수 있는 래퍼 라이브러리입니다.

.. toctree::
   :maxdepth: 2
   :caption: 목차:

   installation
   usage
   api
   contributing

설치
----

.. code-block:: bash

   pip install kis-agent

주요 기능
--------

* 계좌 잔고 조회
* 주식 시세 조회
* 프로그램 매매 정보 조회
* 조건검색식 종목 조회
* 실시간 시세 조회

사용 예시
--------

.. code-block:: python

   from kis.agent import KIS_Agent

   # KIS_Agent 초기화
   agent = KIS_Agent(account_info={
       'CANO': '계좌번호',
       'ACNT_PRDT_CD': '계좌상품코드'
   })

   # 주식 가격 조회
   price = agent.get_stock_price("005930")  # 삼성전자

   # 계좌 잔고 조회
   balance = agent.get_account_balance()

인덱스와 테이블
-------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 