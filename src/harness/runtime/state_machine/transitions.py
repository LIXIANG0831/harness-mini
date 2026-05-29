"""状态转移规则与 hook 类型定义。

修改 ALLOWED_TRANSITIONS 即可改变状态机拓扑。
"""

from __future__ import annotations
from typing import Callable, TYPE_CHECKING

from .enums import TaskStatus

if TYPE_CHECKING:
    from .machine import TaskStateMachine


# 允许的状态转移图
ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.IDLE:      {TaskStatus.PLANNING, TaskStatus.RUNNING},
    TaskStatus.PLANNING:  {TaskStatus.RUNNING, TaskStatus.IDLE, TaskStatus.FAILED},
    TaskStatus.RUNNING:   {TaskStatus.PAUSED, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.RUNNING},
    TaskStatus.PAUSED:    {TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.IDLE},
    TaskStatus.FAILED:    {TaskStatus.IDLE, TaskStatus.PLANNING},
    TaskStatus.COMPLETED: {TaskStatus.IDLE, TaskStatus.PLANNING},
}


# Hook 函数签名
Hook = Callable[["TaskStateMachine", dict], None]
