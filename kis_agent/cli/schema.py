"""GraphQL SDL 스키마 — LLM introspection용.

kis schema 명령에서 출력되는 스키마입니다.
LLM이 사용 가능한 필드와 타입을 자동으로 파악할 수 있도록
한글 description을 포함합니다.
"""

SCHEMA_SDL = '''\
"""한국투자증권 API — LLM Agent용 CLI Interface"""

# === 명령어 ===
# kis price <code>                    국내 주식 현재가
# kis price <code> --daily --days=30  일별 시세
# kis balance [--holdings]            계좌 잔고
# kis orderbook <code>                호가 10호가
# kis overseas <excd> <symb>          해외주식 시세
# kis overseas <excd> <symb> --detail PER/PBR/시총 등 상세
# kis futures <code>                  선물옵션 시세
# kis order buy 005930 --qty 10 --price 70000  지정가 매수
# kis order sell 005930 --qty 10 --type market 시장가 매도
# kis order cancel <주문번호>          주문 취소
# kis order list                       미체결 조회
# kis trades                          당일 체결내역
# kis trades --from -7d               최근 7일 체결
# kis trades --from -30d --profit     기간별 실현손익
# kis query <domain> <method> [args]  API 직접 호출
# kis schema [type]                   스키마 출력

type Stock {
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """현재가 정보"""
  price: StockPrice
  """일별 시세"""
  daily(days: Int): [DailyPrice!]
  """호가 (매수/매도 10호가)"""
  orderbook: Orderbook
  """투자자별 매매동향"""
  investors: InvestorTrend
}

type StockPrice {
  """현재가"""
  currentPrice: String!
  """전일대비"""
  change: String
  """전일대비부호 (1:상한 2:상승 3:보합 4:하한 5:하락)"""
  changeSign: String
  """등락률 (%)"""
  changeRate: String
  """시가"""
  open: String
  """고가"""
  high: String
  """저가"""
  low: String
  """상한가"""
  upperLimit: String
  """하한가"""
  lowerLimit: String
  """누적거래량"""
  volume: String
  """누적거래대금"""
  tradingValue: String
  """PER"""
  per: String
  """PBR"""
  pbr: String
  """EPS"""
  eps: String
  """BPS"""
  bps: String
  """시가총액 (억)"""
  marketCap: String
  """상장주수"""
  listedShares: String
  """외국인보유비율"""
  foreignHoldingRate: String
  """52주 최고가"""
  week52High: String
  """52주 최저가"""
  week52Low: String
}

type DailyPrice {
  """영업일자"""
  date: String!
  """종가"""
  close: String
  """시가"""
  open: String
  """고가"""
  high: String
  """저가"""
  low: String
  """거래량"""
  volume: String
  """등락률"""
  changeRate: String
  """전일대비"""
  change: String
}

type Orderbook {
  """매도호가 [{price, volume}, ...]"""
  asks: [OrderbookLevel!]!
  """매수호가 [{price, volume}, ...]"""
  bids: [OrderbookLevel!]!
  """총매도잔량"""
  totalAskVolume: String
  """총매수잔량"""
  totalBidVolume: String
  """예상체결가"""
  expectedPrice: String
}

type InvestorTrend {
  """개인 순매수"""
  personalNetBuy: String
  """외국인 순매수"""
  foreignNetBuy: String
  """기관 순매수"""
  institutionalNetBuy: String
}

type Account {
  """계좌 잔고 요약"""
  balance: AccountBalance
  """보유 종목 목록"""
  holdings: [Holding!]
}

type AccountBalance {
  """예수금총액"""
  depositTotal: String
  """유가증권평가금액"""
  stockEvalAmount: String
  """총평가금액"""
  totalEvalAmount: String
  """순자산금액"""
  netAssetAmount: String
  """매입금액합계"""
  totalPurchaseAmount: String
  """평가손익합계"""
  totalProfitLoss: String
  """자산증감수익률"""
  assetChangeRate: String
}

type Holding {
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """보유수량"""
  quantity: String
  """매입평균가"""
  avgPrice: String
  """현재가"""
  currentPrice: String
  """평가금액"""
  evalAmount: String
  """평가손익"""
  profitLoss: String
  """수익률 (%)"""
  profitRate: String
}

type OverseasStock {
  """종목 심볼"""
  symbol: String!
  """거래소 (NAS, NYS, AMS, TSE, HKS, SHS, SZS, HSX, HNX)"""
  exchange: String!
  """현재가"""
  price: OverseasPrice
  """현재가 상세 (PER/PBR/시총)"""
  priceDetail: OverseasPriceDetail
}

type OverseasPrice {
  """현재가"""
  currentPrice: String
  """전일종가"""
  prevClose: String
  """전일대비"""
  change: String
  """등락률"""
  changeRate: String
  """거래량"""
  volume: String
}

type OverseasPriceDetail {
  """현재가"""
  currentPrice: String
  """PER"""
  per: String
  """PBR"""
  pbr: String
  """EPS"""
  eps: String
  """시가총액"""
  marketCap: String
  """52주 최고"""
  high52w: String
  """52주 최저"""
  low52w: String
}

type FuturesContract {
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """현재가"""
  price: FuturesPrice
}

type FuturesPrice {
  """현재가"""
  currentPrice: String
  """전일대비"""
  change: String
  """등락률"""
  changeRate: String
  """시가"""
  open: String
  """고가"""
  high: String
  """저가"""
  low: String
  """거래량"""
  volume: String
  """미결제약정"""
  openInterest: String
  """내재변동성 (옵션)"""
  impliedVolatility: String
  """델타"""
  delta: String
  """감마"""
  gamma: String
  """세타"""
  theta: String
  """베가"""
  vega: String
}

# === 해외선물 ===
# kis futures CLM26 --overseas     WTI 원유선물
# kis futures ESM26 --overseas     E-mini S&P500
# kis futures NQM26 --overseas     E-mini NASDAQ
# kis futures GCM26 --overseas     금 선물 (COMEX)
# kis futures SIM26 --overseas     은 선물 (COMEX)

type OverseasFutures {
  """종목코드 (예: CLM26, ESM26)"""
  code: String!
  """현재가"""
  price: OverseasFuturesPrice
  """호가 (매수/매도 5단계)"""
  orderbook: OverseasFuturesOrderbook
}

type OverseasFuturesPrice {
  """현재가"""
  currentPrice: String
  """전일종가"""
  prevClose: String
  """전일대비"""
  change: String
  """등락률"""
  changeRate: String
  """시가"""
  open: String
  """고가"""
  high: String
  """저가"""
  low: String
  """거래량"""
  volume: String
  """미결제약정"""
  openInterest: String
  """거래소"""
  exchange: String
  """통화"""
  currency: String
  """매수호가"""
  bidPrice: String
  """매도호가"""
  askPrice: String
}

# === 주문 ===
# kis order buy 005930 --qty 10 --price 70000          지정가 매수
# kis order buy 005930 --qty 10 --type market           시장가 매수
# kis order sell 005930 --qty 10 --type best            최유리지정가 매도
# kis order buy AAPL --qty 5 --price 230 --overseas NAS 해외 지정가 매수
# kis order cancel 0014898200                           주문 취소
# kis order modify 0014898200 --price 72000             주문 정정
# kis order list                                        미체결 목록

enum DomesticOrderType {
  """국내주식 주문유형"""
  limit
  """시장가"""
  market
  """조건부지정가"""
  cond
  """최유리지정가"""
  best
  """장전시간외"""
  pre
  """장후시간외"""
  after
  """IOC지정가"""
  ioc
  """FOK지정가"""
  fok
}

enum OverseasOrderType {
  """해외주식 주문유형"""
  limit
  """LOO (장개시지정가)"""
  loo
  """LOC (장마감지정가)"""
  loc
  """MOO (장개시시장가, 매도만)"""
  moo
  """MOC (장마감시장가, 매도만)"""
  moc
}

type OrderResult {
  """주문 상태 (accepted)"""
  status: String!
  """주문번호"""
  orderNo: String!
  """주문시각"""
  time: String
  """매수/매도"""
  side: String
  """종목코드"""
  code: String
  """종목명"""
  name: String
  """주문수량"""
  qty: Int
  """주문가격"""
  price: String
  """주문유형"""
  type: String
}

type PendingOrder {
  """주문일자"""
  date: String
  """주문시각"""
  time: String
  """주문번호"""
  orderNo: String!
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """매수/매도"""
  side: String
  """주문유형"""
  orderType: String
  """주문수량"""
  orderQty: String
  """주문가격"""
  orderPrice: String
  """체결수량"""
  filledQty: String
  """잔여수량"""
  remainQty: String
}

# === 알고리즘 분할주문 (TWAP / VWAP) ===
# kis order twap 005930 --side buy --qty 1000 --duration 30 --slices 6
# kis order vwap 005930 --side buy --qty 1000 --duration 120 --profile-days 5
# kis order twap 005930 --side buy --qty 1000 --limit-price 70000  지정가 가드
# kis order twap 005930 --side buy --qty 1000 --funding credit     신용 분할매수
# kis order twap 005930 --side buy --qty 1000 --dry-run            스케줄만 확인
# 명령은 --duration 만큼 블로킹된다. 종료코드: 0 전량, 2 부분/중단, 1 오류.

enum AlgoOrderStatus {
  """모든 슬라이스 접수 완료 (실주문)"""
  completed
  """dry-run 전체 완료 — 주문이 한 건도 전송되지 않았다"""
  simulated
  """일부 슬라이스가 스킵되거나 실패"""
  partial
  """가드에 걸려 스케줄 도중 중단"""
  aborted
  """Ctrl+C로 중단"""
  cancelled
}

enum AlgoSliceStatus {
  """주문 접수됨 (체결 아님 — KIS rt_cd=0은 접수). 구버전 값: filled"""
  accepted
  """dry-run 시뮬레이션 (주문 미전송)"""
  simulated
  """가드로 건너뜀"""
  skipped
  """주문 거부 또는 예외"""
  failed
  """선행 문제로 미실행"""
  cancelled
}

enum AlgoSliceReason {
  """지정가 가드 위반"""
  price_limit
  """정규장 시간 밖"""
  outside_session
  """가드 확인용 현재가 조회 실패"""
  price_unavailable
  """주문 API 거부 또는 예외"""
  order_rejected
  """Ctrl+C"""
  interrupted
  """선행 슬라이스 문제로 미실행"""
  upstream_abort
}

type AlgoOrderSlice {
  """스케줄 내 순번 (0부터)"""
  index: Int!
  """예정 제출 시각 (ISO 8601)"""
  scheduledAt: String!
  """실제 제출 시각. 가드로 스킵되면 null"""
  submittedAt: String
  """이 슬라이스의 주문수량"""
  quantity: Int!
  """슬라이스 상태"""
  status: AlgoSliceStatus!
  """accepted/simulated가 아닐 때의 기계 판독용 사유"""
  reason: AlgoSliceReason
  """주문번호"""
  orderNo: String
  """가드 확인 시점의 현재가. 지정가 가드를 쓸 때만 채워진다"""
  referencePrice: Float
  """응답 메시지. 신용→현금 폴백 같은 특이사항이 [대괄호]로 덧붙는다"""
  message: String
}

type AlgoOrderResult {
  """알고리즘 (twap | vwap)"""
  algorithm: String!
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """매수/매도 (buy | sell)"""
  side: String!
  """집행 결과"""
  status: AlgoOrderStatus!
  """dry-run 여부. true면 주문이 한 건도 전송되지 않았다"""
  dryRun: Boolean!
  """요청한 총 주문수량"""
  totalQuantity: Int!
  """주문이 접수된 수량 (체결 아님 — 지정가 미체결분 포함. 체결수량은 별도 조회)"""
  submittedQuantity: Int!
  """스킵·실패로 집행되지 못한 수량 (뒤 슬라이스로 이월되지 않는다)"""
  unfilledQuantity: Int!
  """집행 시작 시각 (ISO 8601)"""
  startedAt: String
  """집행 종료 시각 (ISO 8601)"""
  finishedAt: String
  """슬라이스 개수"""
  sliceCount: Int!
  """거래량 프로파일 출처, 중단 사유 등 부가 설명"""
  notes: [String!]!
  """슬라이스별 결과"""
  slices: [AlgoOrderSlice!]!
}

# === 거래내역 ===
# kis trades                          당일 체결내역
# kis trades --from -7d               최근 7일
# kis trades --from -30d --sell       최근 30일 매도만
# kis trades --from 2026-01-01 --profit   실현손익
# kis trades --from -30d --profit --daily-profit  일별 손익

type TradeExecution {
  """주문일자 (YYYY-MM-DD)"""
  date: String!
  """주문시각 (HH:MM:SS)"""
  time: String
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """매수/매도"""
  side: String
  """주문유형 (지정가, 시장가 등)"""
  orderType: String
  """주문수량"""
  orderQty: String
  """주문가격"""
  orderPrice: String
  """체결수량"""
  filledQty: String
  """체결평균가"""
  avgPrice: String
  """체결금액"""
  filledAmount: String
  """잔여수량"""
  remainQty: String
  """취소여부"""
  cancelled: String
  """주문번호"""
  orderNo: String
}

type TradeSummary {
  """총주문수량"""
  totalOrderQty: String
  """총체결수량"""
  totalFilledQty: String
  """총체결금액"""
  totalFilledAmount: String
  """총제비용"""
  totalFees: String
}

type PeriodProfit {
  """종목코드"""
  code: String!
  """종목명"""
  name: String
  """매매구분"""
  side: String
  """매수수량"""
  buyQty: String
  """매수금액"""
  buyAmount: String
  """매도수량"""
  sellQty: String
  """매도금액"""
  sellAmount: String
  """실현손익"""
  realizedPL: String
  """실현수익률 (%)"""
  realizedPLRate: String
  """제비용"""
  totalFees: String
}

type DailyProfit {
  """영업일 (YYYY-MM-DD)"""
  date: String!
  """실현손익"""
  realizedPL: String
  """실현수익률 (%)"""
  realizedPLRate: String
  """매도금액"""
  sellAmount: String
  """매수금액"""
  buyAmount: String
  """제비용"""
  totalFees: String
}

# 거래소별 종목코드 예시:
# CME: ESM26(S&P500), NQM26(NASDAQ), 6EM26(유로FX)
# NYMEX: CLM26(WTI원유), NGM26(천연가스)
# COMEX: GCM26(금), SIM26(은), HGM26(구리)
# EUREX: FGBLM26(독일국채)
# ICE: DXM26(달러인덱스)
# 월물코드: F(1월) G(2월) H(3월) J(4월) K(5월) M(6월)
#           N(7월) Q(8월) U(9월) V(10월) X(11월) Z(12월)
'''


def get_schema(type_name=None) -> str:
    """스키마 출력. type_name이 지정되면 해당 타입만 반환."""
    if not type_name:
        return SCHEMA_SDL

    lines = SCHEMA_SDL.split("\n")
    result = []
    capturing = False
    depth = 0

    for i, line in enumerate(lines):
        if not capturing:
            import re

            m = re.match(r"^(type|enum|input)\s+(\w+)", line)
            if m and m.group(2) == type_name:
                capturing = True
                depth = 0
                # 바로 위 doc comment 포함
                j = i - 1
                docs = []
                while j >= 0 and (lines[j].startswith('"""') or lines[j].strip() == ""):
                    docs.insert(0, lines[j])
                    j -= 1
                if docs and docs[0].startswith('"""'):
                    result.extend(docs)

        if capturing:
            result.append(line)
            depth += line.count("{") - line.count("}")
            if depth == 0 and "}" in line:
                break

    if result:
        return "\n".join(result)

    # 타입 없으면 사용 가능한 목록
    import re

    types = re.findall(r"^(?:type|enum|input)\s+(\w+)", SCHEMA_SDL, re.MULTILINE)
    return f'Type "{type_name}" not found. Available: {", ".join(types)}'
