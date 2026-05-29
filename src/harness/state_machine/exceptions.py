"""状态机异常定义。"""


class StateMachineError(Exception):
    """状态机基础异常。"""


class TransitionError(StateMachineError):
    """非法状态转移。"""
