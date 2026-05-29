"""状态机数据模型。"""

from __future__ import annotations
from dataclasses import dataclass, field

from .enums import StepStatus


@dataclass
class Step:
    """单个执行步骤。"""
    desc: str
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "desc": self.desc,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Step":
        return cls(
            desc=d["desc"],
            status=StepStatus(d.get("status", "pending")),
            result=d.get("result", ""),
            error=d.get("error", ""),
            started_at=d.get("started_at", 0.0),
            finished_at=d.get("finished_at", 0.0),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass
class HistoryEvent:
    """状态变更历史记录。"""
    ts: float
    kind: str  # "transition" | "step_update" | "context_update"
    payload: dict

    def to_dict(self) -> dict:
        return {"ts": self.ts, "kind": self.kind, "payload": dict(self.payload)}

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEvent":
        return cls(ts=d["ts"], kind=d["kind"], payload=dict(d.get("payload", {})))
