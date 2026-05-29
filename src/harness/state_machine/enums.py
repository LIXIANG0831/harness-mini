"""状态机枚举定义。"""

from enum import Enum


class TaskStatus(str, Enum):
    """任务级状态。"""
    IDLE = "idle"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class StepStatus(str, Enum):
    """步骤级状态。"""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"


class HookEvent(str, Enum):
    """Hook 事件类型。"""
    TRANSITION = "transition"        # 状态转移
    STEP_UPDATE = "step_update"      # 步骤状态更新
    CONTEXT_UPDATE = "context_update"  # 上下文变更
    COMPLETED = "completed"          # 任务完成
    FAILED = "failed"                # 任务失败
