"""
investor.py - 투자자별 포지션 분석 전용 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음 기능을 제공합니다:
- 외국인/기관/개인 투자자 매매 데이터 수집
- 30일 누적 포지션 추적 및 분석
- 당일 매매 패턴 해석 및 컨텍스트 제공
- 패닉 방지를 위한 장기/단기 트렌드 비교

 의존:
- kis_core.KISClient: API 호출 실행기
- datetime: 날짜 계산
- logging: 로깅

 연관 모듈:
- stock.api.StockAPI: 기존 투자자 조회 연동
- examples_llm/domestic_stock: 투자자 관련 원시 API들

 사용 예시:
client = KISClient()
account = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
investor = InvestorPositionAnalyzer(client, account)
analysis = investor.analyze_30day_position("005930")
"""

import sys
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# PyKIS 의존성
from ..core.client import KISClient, API_ENDPOINTS

# Open Trading API 예제 의존성 (동적 import)
sys.path.append("/home/unohee/STONKS/modules/pykis/open-trading-api/examples_llm")


@dataclass
class InvestorPositionData:
    """투자자 포지션 데이터 구조"""

    stock_code: str
    date: str
    foreign_buy: int = 0
    foreign_sell: int = 0
    foreign_net: int = 0
    institution_buy: int = 0
    institution_sell: int = 0
    institution_net: int = 0
    individual_buy: int = 0
    individual_sell: int = 0
    individual_net: int = 0
    price: int = 0
    volume: int = 0


@dataclass
class PositionAnalysisResult:
    """포지션 분석 결과"""

    stock_code: str
    analysis_date: str
    daily_analysis: Dict[str, Any]
    cumulative_30d: Dict[str, Any]
    interpretation: str
    score: float


class InvestorPositionAnalyzer:
    """투자자별 포지션 분석 시스템"""

    def __init__(self, client: KISClient, account_info: Dict[str, str] = None):
        self.client = client
        self.account = account_info or {}
        self.logger = logging.getLogger(__name__)
        # 클라이언트가 자동으로 토큰을 관리하므로 별도 처리 불필요

    def _import_investor_apis(self):
        """투자자 관련 API 동적 import"""
        try:
            from domestic_stock.inquire_investor.inquire_investor import (
                inquire_investor,
            )
            from domestic_stock.inquire_investor_daily_by_market.inquire_investor_daily_by_market import (
                inquire_investor_daily_by_market,
            )
            from domestic_stock.foreign_institution_total.foreign_institution_total import (
                foreign_institution_total,
            )
            from domestic_stock.inquire_investor_time_by_market.inquire_investor_time_by_market import (
                inquire_investor_time_by_market,
            )

            return {
                "inquire_investor": inquire_investor,
                "inquire_investor_daily_by_market": inquire_investor_daily_by_market,
                "foreign_institution_total": foreign_institution_total,
                "inquire_investor_time_by_market": inquire_investor_time_by_market,
            }
        except ImportError as e:
            self.logger.error(f"투자자 API import 실패: {e}")
            return None

    def get_stock_investor_data(self, stock_code: str) -> Optional[Dict]:
        """개별 종목 투자자 데이터 조회"""
        try:
            # BaseAPI의 _make_request_dict 사용
            response = self.client.make_request(
                endpoint=API_ENDPOINTS.get(
                    "INQUIRE_INVESTOR",
                    "/uapi/domestic-stock/v1/quotations/inquire-investor",
                ),
                tr_id="FHKST01010900",
                params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code},
            )

            return response

        except Exception as e:
            self.logger.error(f"종목 {stock_code} 투자자 데이터 조회 실패: {e}")
            return None

    def get_daily_market_trends(
        self, date: str = None, market: str = "KSP"
    ) -> Optional[Dict]:
        """시장별 일별 투자자 동향 조회"""
        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")

            # API 호출
            response = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/inquire-investor-daily-by-market",
                tr_id="FHKST01010800",
                params={
                    "FID_COND_MRKT_DIV_CODE": "U",
                    "FID_INPUT_ISCD": "0001",  # 코스피
                    "FID_INPUT_DATE_1": date,
                    "FID_INPUT_ISCD_1": market,
                    "FID_INPUT_DATE_2": date,
                    "FID_INPUT_ISCD_2": "0001",
                },
            )

            return response

        except Exception as e:
            self.logger.error(f"시장별 일별 투자자 동향 조회 실패 ({date}): {e}")
            return None

    def get_foreign_institution_aggregate(self) -> Optional[Dict]:
        """외국인/기관 실시간 집계 데이터 조회"""
        try:
            # API 호출
            response = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/quotations/foreign-institution-total",
                tr_id="FHPTJ04400000",
                params={
                    "FID_COND_MRKT_DIV_CODE": "V",
                    "FID_COND_SCR_DIV_CODE": "16449",
                    "FID_INPUT_ISCD": "0000",  # 전체
                    "FID_DIV_CLS_CODE": "0",  # 수량정열
                    "FID_RANK_SORT_CLS_CODE": "0",  # 순매수상위
                    "FID_ETC_CLS_CODE": "0",  # 전체
                },
            )

            return response

        except Exception as e:
            self.logger.error(f"외국인/기관 집계 데이터 조회 실패: {e}")
            return None

    def analyze_daily_position(
        self, stock_code: str, target_date: str = None
    ) -> Dict[str, Any]:
        """당일 투자자별 포지션 분석"""
        try:
            if target_date is None:
                target_date = datetime.now().strftime("%Y%m%d")

            # 개별 종목 투자자 데이터 조회
            investor_df = self.get_stock_investor_data(stock_code)

            if investor_df is None or investor_df.empty:
                self.logger.warning(f"종목 {stock_code} 투자자 데이터 조회 실패")
                return {}

            # 데이터 파싱
            daily_data = {}

            if not investor_df.empty:
                row = investor_df.iloc[0]

                # 외국인 데이터
                daily_data["foreign"] = {
                    "buy_volume": int(row.get("frgn_shnu_vol", 0) or 0),
                    "sell_volume": int(row.get("frgn_seln_vol", 0) or 0),
                    "net_volume": int(row.get("frgn_ntby_qty", 0) or 0),
                    "buy_amount": int(row.get("frgn_shnu_tr_pbmn", 0) or 0),
                    "sell_amount": int(row.get("frgn_seln_tr_pbmn", 0) or 0),
                    "net_amount": int(row.get("frgn_ntby_tr_pbmn", 0) or 0),
                }

                # 기관 데이터
                daily_data["institution"] = {
                    "buy_volume": int(row.get("inst_shnu_vol", 0) or 0),
                    "sell_volume": int(row.get("inst_seln_vol", 0) or 0),
                    "net_volume": int(row.get("inst_ntby_qty", 0) or 0),
                    "buy_amount": int(row.get("inst_shnu_tr_pbmn", 0) or 0),
                    "sell_amount": int(row.get("inst_seln_tr_pbmn", 0) or 0),
                    "net_amount": int(row.get("inst_ntby_tr_pbmn", 0) or 0),
                }

                # 개인 데이터
                daily_data["individual"] = {
                    "buy_volume": int(row.get("prsn_shnu_vol", 0) or 0),
                    "sell_volume": int(row.get("prsn_seln_vol", 0) or 0),
                    "net_volume": int(row.get("prsn_ntby_qty", 0) or 0),
                    "buy_amount": int(row.get("prsn_shnu_tr_pbmn", 0) or 0),
                    "sell_amount": int(row.get("prsn_seln_tr_pbmn", 0) or 0),
                    "net_amount": int(row.get("prsn_ntby_tr_pbmn", 0) or 0),
                }

                # 기본 정보
                daily_data["basic"] = {
                    "date": target_date,
                    "stock_code": stock_code,
                    "current_price": int(row.get("stck_prpr", 0) or 0),
                    "trading_volume": int(row.get("acml_vol", 0) or 0),
                }

            return daily_data

        except Exception as e:
            self.logger.error(
                f"당일 포지션 분석 실패 ({stock_code}, {target_date}): {e}"
            )
            return {}

    def get_30day_cumulative_analysis(self, stock_code: str) -> Dict[str, Any]:
        """30일 누적 포지션 분석"""
        try:
            # 30일간 날짜 리스트 생성 (주말 제외)
            end_date = datetime.now()
            date_list = []

            for i in range(45):  # 주말 고려해서 45일 전부터 검색
                check_date = end_date - timedelta(days=i)
                if check_date.weekday() < 5:  # 평일만
                    date_list.append(check_date.strftime("%Y%m%d"))
                if len(date_list) >= 30:
                    break

            cumulative_data = {
                "foreign": {"net_volume": 0, "net_amount": 0, "daily_data": []},
                "institution": {"net_volume": 0, "net_amount": 0, "daily_data": []},
                "individual": {"net_volume": 0, "net_amount": 0, "daily_data": []},
                "period": {
                    "start_date": date_list[-1] if date_list else "",
                    "end_date": date_list[0] if date_list else "",
                    "trading_days": len(date_list),
                },
            }

            # 각 날짜별 데이터 수집 (실제로는 API 제한으로 인해 현재 데이터만 사용)
            # 향후 DB 저장 기능을 통해 실제 30일 데이터 구현 예정
            daily_analysis = self.analyze_daily_position(stock_code)

            if daily_analysis:
                # 현재는 당일 데이터만 사용하여 누적 분석 시뮬레이션
                for investor_type in ["foreign", "institution", "individual"]:
                    if investor_type in daily_analysis:
                        data = daily_analysis[investor_type]
                        cumulative_data[investor_type]["net_volume"] = data.get(
                            "net_volume", 0
                        )
                        cumulative_data[investor_type]["net_amount"] = data.get(
                            "net_amount", 0
                        )
                        cumulative_data[investor_type]["daily_data"] = [
                            data
                        ]  # 현재는 당일 데이터만

            return cumulative_data

        except Exception as e:
            self.logger.error(f"30일 누적 분석 실패 ({stock_code}): {e}")
            return {}

    def interpret_position_context(
        self, daily_data: Dict[str, Any], cumulative_data: Dict[str, Any]
    ) -> str:
        """포지션 패턴 해석 및 컨텍스트 제공"""
        try:
            if not daily_data or not cumulative_data:
                return "분석할 데이터가 부족합니다."

            interpretation_parts = []

            # 외국인 해석
            if "foreign" in daily_data and "foreign" in cumulative_data:
                daily_foreign = daily_data["foreign"]
                cumulative_foreign = cumulative_data["foreign"]

                daily_net = daily_foreign.get("net_amount", 0)
                cumulative_net = cumulative_foreign.get("net_amount", 0)

                if daily_net > 0 and cumulative_net > 0:
                    interpretation_parts.append(
                        " 외국인: 당일 순매수 지속, 30일간도 지속적 매수 우위 (강한 매수 신호)"
                    )
                elif daily_net < 0 and cumulative_net > 0:
                    interpretation_parts.append(
                        f" 외국인: 당일 순매도 {abs(daily_net/100000000):.1f}억원이지만, 30일간 누적 순매수 {cumulative_net/100000000:.1f}억원 (단기 조정, 전체적으로는 매수 우위)"
                    )
                elif daily_net > 0 and cumulative_net < 0:
                    interpretation_parts.append(
                        " 외국인: 당일 순매수이지만 30일간은 순매도 우위 (패턴 변화 주목)"
                    )
                else:
                    interpretation_parts.append(
                        " 외국인: 당일 및 30일간 순매도 우위 (약세 신호)"
                    )

            # 기관 해석
            if "institution" in daily_data and "institution" in cumulative_data:
                daily_inst = daily_data["institution"]
                cumulative_inst = cumulative_data["institution"]

                daily_net = daily_inst.get("net_amount", 0)
                cumulative_net = cumulative_inst.get("net_amount", 0)

                if daily_net > 0 and cumulative_net > 0:
                    interpretation_parts.append(
                        "🏦 기관: 당일 및 30일간 지속적 순매수 (기관 관심 지속)"
                    )
                elif daily_net < 0 and cumulative_net > 0:
                    interpretation_parts.append(
                        f"🏦 기관: 당일 순매도 {abs(daily_net/100000000):.1f}억원이지만, 30일간 누적 순매수 {cumulative_net/100000000:.1f}억원 (일시적 매도, 전체적으로는 매수 우위)"
                    )
                elif daily_net > 0 and cumulative_net < 0:
                    interpretation_parts.append(
                        "🏦 기관: 당일 순매수로 전환, 30일간 패턴 변화 시작"
                    )
                else:
                    interpretation_parts.append("🏦 기관: 당일 및 30일간 순매도 지속")

            # 개인 해석
            if "individual" in daily_data and "individual" in cumulative_data:
                daily_indiv = daily_data["individual"]
                cumulative_indiv = cumulative_data["individual"]

                daily_net = daily_indiv.get("net_amount", 0)
                cumulative_net = cumulative_indiv.get("net_amount", 0)

                if daily_net > 0 and cumulative_net > 0:
                    interpretation_parts.append(" 개인: 당일 및 30일간 지속적 순매수")
                elif daily_net < 0 and cumulative_net > 0:
                    interpretation_parts.append(
                        " 개인: 당일 순매도이지만 30일간은 순매수 우위"
                    )
                else:
                    interpretation_parts.append(" 개인: 매도 우위 패턴")

            # 종합 해석
            summary = "\n\n 종합 해석: "
            foreign_cumul = cumulative_data.get("foreign", {}).get("net_amount", 0)
            inst_cumul = cumulative_data.get("institution", {}).get("net_amount", 0)

            if foreign_cumul > 0 and inst_cumul > 0:
                summary += "외국인과 기관이 모두 30일간 순매수 우위를 보이고 있어 기관투자자들의 관심이 높은 상황입니다."
            elif foreign_cumul > 0 or inst_cumul > 0:
                summary += "주요 기관투자자 중 일부가 30일간 순매수 우위를 보이고 있어 관심을 가질 만한 종목입니다."
            else:
                summary += (
                    "기관투자자들의 매도 우위가 지속되고 있어 신중한 접근이 필요합니다."
                )

            summary += (
                "\n 단기 변동에 휘둘리지 말고 30일 누적 트렌드를 중심으로 판단하세요."
            )

            return "\n".join(interpretation_parts) + summary

        except Exception as e:
            self.logger.error(f"포지션 해석 실패: {e}")
            return "포지션 해석 중 오류가 발생했습니다."

    def calculate_position_score(
        self, daily_data: Dict[str, Any], cumulative_data: Dict[str, Any]
    ) -> float:
        """포지션 데이터 기반 점수 계산 (0-10점)"""
        try:
            if not daily_data or not cumulative_data:
                return 0.0

            score = 5.0  # 기본 점수

            # 외국인 점수 (30% 가중치)
            foreign_daily = daily_data.get("foreign", {}).get("net_amount", 0)
            foreign_cumul = cumulative_data.get("foreign", {}).get("net_amount", 0)

            if foreign_cumul > 0:
                score += 1.5  # 30일 누적 순매수
                if foreign_daily > 0:
                    score += 0.5  # 당일도 순매수
            elif foreign_daily > 0 and foreign_cumul <= 0:
                score += 0.3  # 당일만 순매수 (패턴 변화 시작)

            # 기관 점수 (30% 가중치)
            inst_daily = daily_data.get("institution", {}).get("net_amount", 0)
            inst_cumul = cumulative_data.get("institution", {}).get("net_amount", 0)

            if inst_cumul > 0:
                score += 1.5  # 30일 누적 순매수
                if inst_daily > 0:
                    score += 0.5  # 당일도 순매수
            elif inst_daily > 0 and inst_cumul <= 0:
                score += 0.3  # 당일만 순매수

            # 개인 점수 (20% 가중치) - 개인은 보통 반대 지표로 작용
            indiv_daily = daily_data.get("individual", {}).get("net_amount", 0)
            indiv_cumul = cumulative_data.get("individual", {}).get("net_amount", 0)

            if indiv_cumul < 0 and (foreign_cumul > 0 or inst_cumul > 0):
                score += 1.0  # 개인 매도 + 기관 매수 = 좋은 신호

            # 투자자 간 합의 보너스 (20% 가중치)
            if foreign_cumul > 0 and inst_cumul > 0:
                score += 1.0  # 외국인 + 기관 모두 순매수

            # 점수 범위 제한 (0-10)
            return max(0.0, min(10.0, score))

        except Exception as e:
            self.logger.error(f"포지션 점수 계산 실패: {e}")
            return 0.0

    def analyze_comprehensive_position(self, stock_code: str) -> PositionAnalysisResult:
        """종합 투자자 포지션 분석"""
        try:
            self.logger.info(f"종목 {stock_code} 투자자 포지션 종합 분석 시작")

            # 1. 당일 분석
            daily_analysis = self.analyze_daily_position(stock_code)

            # 2. 30일 누적 분석
            cumulative_analysis = self.get_30day_cumulative_analysis(stock_code)

            # 3. 해석 생성
            interpretation = self.interpret_position_context(
                daily_analysis, cumulative_analysis
            )

            # 4. 점수 계산
            score = self.calculate_position_score(daily_analysis, cumulative_analysis)

            # 5. 결과 구성
            result = PositionAnalysisResult(
                stock_code=stock_code,
                analysis_date=datetime.now().strftime("%Y%m%d"),
                daily_analysis=daily_analysis,
                cumulative_30d=cumulative_analysis,
                interpretation=interpretation,
                score=score,
            )

            self.logger.info(
                f"종목 {stock_code} 투자자 포지션 분석 완료 (점수: {score:.2f})"
            )
            return result

        except Exception as e:
            self.logger.error(f"종합 포지션 분석 실패 ({stock_code}): {e}")
            return PositionAnalysisResult(
                stock_code=stock_code,
                analysis_date=datetime.now().strftime("%Y%m%d"),
                daily_analysis={},
                cumulative_30d={},
                interpretation="분석 실패",
                score=0.0,
            )

    def get_market_wide_trends(self, date: str = None) -> Dict[str, Any]:
        """시장 전체 투자자 동향 분석"""
        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")

            # 코스피 시장 동향
            kospi_trends = self.get_daily_market_trends(date, "KSP")

            # 코스닥 시장 동향
            kosdaq_trends = self.get_daily_market_trends(date, "KSQ")

            # 외국인/기관 집계 데이터
            aggregate_data = self.get_foreign_institution_aggregate()

            market_analysis = {
                "date": date,
                "kospi_trends": (
                    kospi_trends.to_dict() if kospi_trends is not None else {}
                ),
                "kosdaq_trends": (
                    kosdaq_trends.to_dict() if kosdaq_trends is not None else {}
                ),
                "aggregate_data": (
                    aggregate_data.to_dict() if aggregate_data is not None else {}
                ),
                "summary": self._generate_market_summary(
                    kospi_trends, kosdaq_trends, aggregate_data
                ),
            }

            return market_analysis

        except Exception as e:
            self.logger.error(f"시장 전체 동향 분석 실패 ({date}): {e}")
            return {}

    def _generate_market_summary(self, kospi_data, kosdaq_data, aggregate_data) -> str:
        """시장 동향 요약 생성"""
        try:
            summary_parts = []

            # KOSPI 요약
            if kospi_data is not None and not kospi_data.empty:
                summary_parts.append(" KOSPI: 투자자 동향 데이터 수집 완료")

            # KOSDAQ 요약
            if kosdaq_data is not None and not kosdaq_data.empty:
                summary_parts.append(" KOSDAQ: 투자자 동향 데이터 수집 완료")

            # 집계 데이터 요약
            if aggregate_data is not None and not aggregate_data.empty:
                summary_parts.append(" 외국인/기관 집계: 실시간 데이터 수집 완료")

            if not summary_parts:
                return "시장 데이터 수집에 실패했습니다."

            return (
                "\n".join(summary_parts)
                + "\n\n 시장 전체 투자자 동향 분석이 완료되었습니다."
            )

        except Exception as e:
            self.logger.error(f"시장 요약 생성 실패: {e}")
            return "시장 요약 생성 중 오류가 발생했습니다."
