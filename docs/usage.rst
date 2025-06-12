사용 가이드
==========

기본 사용법
---------

KIS_Agent 초기화
~~~~~~~~~~~~~

.. code-block:: python

   from kis.agent import KIS_Agent

   # KIS_Agent 초기화
   agent = KIS_Agent(account_info={
       'CANO': '계좌번호',
       'ACNT_PRDT_CD': '계좌상품코드'
   })

주식 시세 조회
~~~~~~~~~~~

.. code-block:: python

   # 현재가 조회
   price = agent.get_stock_price("005930")  # 삼성전자

   # 일별 가격 조회
   daily_prices = agent.get_daily_price("005930")

계좌 잔고 조회
~~~~~~~~~~~

.. code-block:: python

   # 계좌 잔고 조회
   balance = agent.get_account_balance()

   # 현금 잔고 조회
   cash = agent.get_cash_available()

   # 총 자산 조회
   total = agent.get_total_asset()

프로그램 매매 정보 조회
-------------------

.. code-block:: python

   from kis.program.trade import ProgramTradeAPI

   # ProgramTradeAPI 초기화
   pgm_api = ProgramTradeAPI(client)

   # 프로그램 매매 정보 조회
   result = pgm_api.get_pgm_trade("005930", ref_date="20250516")

조건검색식 종목 조회
----------------

.. code-block:: python

   from kis.stock.condition import ConditionAPI

   # ConditionAPI 초기화
   condition = ConditionAPI(client)

   # 조건검색식 목록 조회
   conditions = condition.get_condition_list()

   # 특정 조건검색식의 종목 조회
   stocks = condition.get_condition_stocks("조건검색식_이름")

고급 사용법
---------

실시간 시세 조회
~~~~~~~~~~~~

.. code-block:: python

   from kis.stock.market import StockAPI

   # StockAPI 초기화
   stock = StockAPI(client, account_info)

   # 호가 조회
   orderbook = stock.get_orderbook("005930")

   # 투자자 정보 조회
   investor = stock.get_stock_investor("005930")

에러 처리
-------

.. code-block:: python

   try:
       price = agent.get_stock_price("005930")
   except Exception as e:
       print(f"에러 발생: {e}")

재시도 로직
--------

.. code-block:: python

   from kis.core.client import KISClient

   # KISClient 초기화 (자동 재시도 활성화)
   client = KISClient(verbose=True, max_retries=3) 