from .trade import ProgramTradeAPI

# 기존 호환성을 위한 별칭
ProgramAPI = ProgramTradeAPI
ProgramTrade = ProgramTradeAPI

__all__ = ["ProgramTradeAPI", "ProgramAPI", "ProgramTrade"]
