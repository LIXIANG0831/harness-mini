"""智能体指令模板管理模块。

包含主智能体 instructions 模板与技能索引加载。
任务规划相关的提示词（如 nudge）属于 runtime 内核，从 `runtime.planning` 导入。
"""
from .instructions import get_main_agent_instructions
from .skills_info import get_skills_info

__all__ = [
    "get_main_agent_instructions",
    "get_skills_info",
]
