"""MethodDiscoveryMixin의 조회·출력·분류 경로 테스트."""

from kis_agent.core.method_discovery import MethodDiscoveryMixin


class _Discovery(MethodDiscoveryMixin):
    def get_stock_price(self):
        """현재가 문서."""


def test_categories_usage_and_broker_classification(capsys):
    agent = _Discovery()
    simple = agent.get_all_methods(category="stock")
    assert set(simple) == {"stock", "_summary"}
    assert agent.get_all_methods(category="unknown")["error"]
    assert agent.search_methods("price")
    agent.show_method_usage("get_stock_price")
    assert "현재가 문서" in capsys.readouterr().out
    agent.show_method_usage("not-found")
    assert "찾을 수 없습니다" in capsys.readouterr().out
    assert agent.classify_broker(None) == "N/A"
    assert agent.classify_broker("골드만삭스") == "외국계"
    assert agent.classify_broker("키움증권") == "리테일/국내기관"
    assert agent.classify_broker("무명") == "기타"
