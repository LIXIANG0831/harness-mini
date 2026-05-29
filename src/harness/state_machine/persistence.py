"""持久化策略。

可以扩展为 OpenViking / SQLite / Redis 等不同实现，
只要遵循 save / load 接口即可。
"""

from __future__ import annotations
from typing import Optional

from .machine import TaskStateMachine


class FilePersistence:
    """简单的文件持久化策略。"""

    def __init__(self, path: str):
        self.path = path

    def save(self, sm: TaskStateMachine) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(sm.to_json())

    def load(self) -> Optional[TaskStateMachine]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return TaskStateMachine.from_json(f.read())
        except FileNotFoundError:
            return None
