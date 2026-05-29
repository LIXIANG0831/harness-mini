"""通用任务状态机包。

设计原则：
- 状态 + 上下文 + 转移 三层分离
- 所有状态变更记录到 history，支持回溯审计
- 可序列化为 dict/JSON，方便持久化
- 支持 hooks（transition / step_update / context_update / completed / failed）
- 转移由"守卫函数"控制，非法转移会抛 TransitionError

模块布局：
- enums:        TaskStatus / StepStatus / HookEvent
- exceptions:   StateMachineError / TransitionError
- models:       Step / HistoryEvent
- transitions:  ALLOWED_TRANSITIONS / Hook 类型别名
- machine:      TaskStateMachine 核心类
- persistence:  FilePersistence 持久化策略

最常用的 API 都从包根直接导出，外部用 `from state_machine import X` 即可。
"""

from .enums import TaskStatus, StepStatus, HookEvent
from .exceptions import StateMachineError, TransitionError
from .models import Step, HistoryEvent
from .transitions import ALLOWED_TRANSITIONS, Hook
from .machine import TaskStateMachine
from .persistence import FilePersistence

__all__ = [
    # 枚举
    "TaskStatus",
    "StepStatus",
    "HookEvent",
    # 异常
    "StateMachineError",
    "TransitionError",
    # 模型
    "Step",
    "HistoryEvent",
    # 转移
    "ALLOWED_TRANSITIONS",
    "Hook",
    # 主类
    "TaskStateMachine",
    # 持久化
    "FilePersistence",
]
