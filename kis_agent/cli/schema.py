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
