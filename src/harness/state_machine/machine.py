"""核心状态机实现。"""

from __future__ import annotations
import json
import time
import uuid
from typing import Any, Optional

from .enums import TaskStatus, StepStatus, HookEvent
from .exceptions import StateMachineError, TransitionError
from .models import Step, HistoryEvent
from .transitions import ALLOWED_TRANSITIONS, Hook


class TaskStateMachine:
    """通用任务状态机。

    使用方式：
        sm = TaskStateMachine()
        sm.plan(goal="...", steps=["step1", "step2"])
        sm.start_step()
        sm.complete_step(result="...")
        ...

    Hook:
        sm.on(HookEvent.TRANSITION, lambda m, p: print(p))

    持久化：
        snapshot = sm.to_dict()
        sm2 = TaskStateMachine.from_dict(snapshot)
    """

    def __init__(self, task_id: Optional[str] = None):
        self.task_id: str = task_id or uuid.uuid4().hex[:8]
        self.goal: str = ""
        self.status: TaskStatus = TaskStatus.IDLE
        self.steps: list[Step] = []
        self.current_step: int = 0
        self.context: dict = {}  # 任务级共享变量（步骤之间传值）
        self.history: list[HistoryEvent] = []
        self.created_at: float = time.time()
        self.updated_at: float = self.created_at
        self._hooks: dict[str, list[Hook]] = {}

    # ---------- Hook 注册 ----------

    def on(self, event: HookEvent | str, hook: Hook) -> None:
        """注册 hook。event 推荐使用 HookEvent 枚举，也兼容字符串。"""
        key = event.value if isinstance(event, HookEvent) else event
        self._hooks.setdefault(key, []).append(hook)

    def _fire(self, event: HookEvent | str, payload: dict) -> None:
        key = event.value if isinstance(event, HookEvent) else event
        for hook in self._hooks.get(key, []):
            try:
                hook(self, payload)
            except Exception:
                pass  # hook 失败不影响主流程

    def _record(self, kind: HookEvent | str, payload: dict) -> None:
        key = kind.value if isinstance(kind, HookEvent) else kind
        self.updated_at = time.time()
        evt = HistoryEvent(ts=self.updated_at, kind=key, payload=payload)
        self.history.append(evt)
        self._fire(key, payload)

    # ---------- 状态转移核心 ----------

    def _transition(self, to: TaskStatus, reason: str = "") -> None:
        if to not in ALLOWED_TRANSITIONS.get(self.status, set()):
            raise TransitionError(f"非法转移: {self.status.value} → {to.value}")
        old = self.status
        self.status = to
        self._record(HookEvent.TRANSITION, {"from": old.value, "to": to.value, "reason": reason})

    # ---------- 公开 API: 任务级 ----------

    def plan(self, goal: str, steps: list[str]) -> None:
        """创建/重置任务计划。"""
        if not steps:
            raise ValueError("steps 不能为空")
        if self.status not in (TaskStatus.IDLE, TaskStatus.COMPLETED, TaskStatus.FAILED):
            raise TransitionError(f"当前状态 {self.status.value} 不能开始新计划，请先 reset()")
        self.goal = goal
        self.steps = [Step(desc=s) for s in steps]
        self.current_step = 0
        self.context = {}
        self._transition(TaskStatus.RUNNING, reason=f"plan:{goal[:30]}")

    def reset(self) -> None:
        """重置到 IDLE 状态。保留 history。"""
        old = self.status
        self.status = TaskStatus.IDLE
        self.steps = []
        self.current_step = 0
        self.goal = ""
        self.context = {}
        self._record(HookEvent.TRANSITION, {"from": old.value, "to": TaskStatus.IDLE.value, "reason": "reset"})

    def pause(self, reason: str = "") -> None:
        self._transition(TaskStatus.PAUSED, reason=reason or "user pause")

    def resume(self) -> None:
        if self.status != TaskStatus.PAUSED:
            raise TransitionError(f"只有 PAUSED 状态才能 resume，当前 {self.status.value}")
        self._transition(TaskStatus.RUNNING, reason="resume")

    def fail(self, reason: str = "") -> None:
        self._transition(TaskStatus.FAILED, reason=reason)

    # ---------- 公开 API: 步骤级 ----------

    def start_step(self) -> Step:
        """标记当前步骤开始执行。"""
        if self.status != TaskStatus.RUNNING:
            raise TransitionError(f"任务未运行，当前 {self.status.value}")
        if self.current_step >= len(self.steps):
            raise StateMachineError("已无步骤可执行")
        step = self.steps[self.current_step]
        if step.status != StepStatus.PENDING:
            return step  # 幂等
        step.status = StepStatus.RUNNING
        step.started_at = time.time()
        self._record(HookEvent.STEP_UPDATE, {"index": self.current_step, "status": step.status.value, "desc": step.desc})
        return step

    def complete_step(self, result: str = "") -> Optional[Step]:
        """标记当前步骤完成。返回下一步（若有），自动推进。

        如果是最后一步，会转到 COMPLETED。
        """
        if self.status != TaskStatus.RUNNING:
            raise TransitionError(f"任务未运行，当前 {self.status.value}")
        if self.current_step >= len(self.steps):
            raise StateMachineError("已无步骤可完成")
        step = self.steps[self.current_step]
        # 自动 start（容忍没调 start_step 直接完成）
        if step.status == StepStatus.PENDING:
            step.started_at = time.time()
        step.status = StepStatus.DONE
        step.result = result
        step.finished_at = time.time()
        self._record(HookEvent.STEP_UPDATE, {"index": self.current_step, "status": "done", "result": result[:200]})
        # 推进
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self._transition(TaskStatus.COMPLETED, reason="all steps done")
            self._fire(HookEvent.COMPLETED, {"task_id": self.task_id, "goal": self.goal})
            return None
        return self.steps[self.current_step]

    def fail_step(self, error: str) -> None:
        """标记当前步骤失败，整体转到 FAILED。"""
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            step.status = StepStatus.FAILED
            step.error = error
            step.finished_at = time.time()
            self._record(HookEvent.STEP_UPDATE, {"index": self.current_step, "status": "failed", "error": error[:200]})
        self.fail(reason=f"step {self.current_step} failed: {error[:100]}")
        self._fire(HookEvent.FAILED, {"task_id": self.task_id, "step": self.current_step, "error": error})

    def skip_step(self, reason: str = "") -> Optional[Step]:
        """跳过当前步骤。"""
        if self.status != TaskStatus.RUNNING or self.current_step >= len(self.steps):
            raise StateMachineError("不能跳过")
        step = self.steps[self.current_step]
        step.status = StepStatus.SKIPPED
        step.result = reason
        step.finished_at = time.time()
        self._record(HookEvent.STEP_UPDATE, {"index": self.current_step, "status": "skipped", "reason": reason})
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self._transition(TaskStatus.COMPLETED, reason="all steps consumed")
            return None
        return self.steps[self.current_step]

    # ---------- 上下文操作（步骤间传值） ----------

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value
        self._record(HookEvent.CONTEXT_UPDATE, {"key": key, "value_repr": repr(value)[:200]})

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    # ---------- 查询 ----------

    @property
    def is_running(self) -> bool:
        return self.status == TaskStatus.RUNNING

    @property
    def is_done(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

    @property
    def progress(self) -> tuple[int, int]:
        done = sum(1 for s in self.steps if s.status in (StepStatus.DONE, StepStatus.SKIPPED))
        return done, len(self.steps)

    def current(self) -> Optional[Step]:
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def format(self) -> str:
        """人类可读的状态展示。"""
        if self.status == TaskStatus.IDLE:
            return "(idle, 暂无任务)"
        lines = [f"📋 [{self.task_id}] {self.goal}", f"状态: {self.status.value}"]
        for i, s in enumerate(self.steps):
            mark = {
                StepStatus.DONE: "✅",
                StepStatus.RUNNING: "▶️",
                StepStatus.SKIPPED: "⏭️",
                StepStatus.FAILED: "❌",
                StepStatus.PENDING: "⬜",
            }[s.status]
            line = f"  {mark} {i+1}. {s.desc}"
            if s.result:
                line += f" — {s.result[:60]}"
            if s.error:
                line += f" [error: {s.error[:60]}]"
            lines.append(line)
        done, total = self.progress
        lines.append(f"\n进度: {done}/{total}")
        return "\n".join(lines)

    # ---------- 序列化 / 反序列化 ----------

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "context": dict(self.context),
            "history": [e.to_dict() for e in self.history],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "TaskStateMachine":
        sm = cls(task_id=d.get("task_id"))
        sm.goal = d.get("goal", "")
        sm.status = TaskStatus(d.get("status", "idle"))
        sm.steps = [Step.from_dict(s) for s in d.get("steps", [])]
        sm.current_step = d.get("current_step", 0)
        sm.context = dict(d.get("context", {}))
        sm.history = [HistoryEvent.from_dict(e) for e in d.get("history", [])]
        sm.created_at = d.get("created_at", time.time())
        sm.updated_at = d.get("updated_at", sm.created_at)
        return sm

    @classmethod
    def from_json(cls, s: str) -> "TaskStateMachine":
        return cls.from_dict(json.loads(s))
