class StrategyTrigger:
    """매매 전략 실행을 위한 간단한 트리거 클래스"""

    def __init__(self, client, account_info=None):
        self.client = client
        self.account_info = account_info or {}

    def check_entry_condition(self, code: str):
        return {"can_enter": True, "reason": "mock"}

    def execute_buy_order(self, code: str, qty: int):
        return {"order_id": "0000", "order_status": "mock"}

    def monitor_strategy(self, code: str):
        return {"strategy_status": "running", "current_position": 0, "profit_loss": 0}

    def check_exit_condition(self, code: str):
        if code == '000000':
            raise Exception('invalid code')
        return {"should_exit": False, "reason": "mock"}
