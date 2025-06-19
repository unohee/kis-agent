"""
⚠️ DEPRECATED: 이 파일은 더 이상 사용되지 않습니다.
대신 pykis.program.trade 모듈의 ProgramTradeAPI를 사용하세요.

from pykis.program.trade import ProgramTradeAPI
"""

# 기존 호환성을 위한 재수출
from .trade import ProgramTradeAPI

# 모든 내용을 주석 처리하고 trade.py로 리다이렉트
__all__ = ['ProgramTradeAPI'] 
