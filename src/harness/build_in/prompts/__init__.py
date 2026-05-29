"""智能体指令模板管理模块。

包含主智能体 instructions 模板、技能索引加载、规划相关提示词等。
"""
from .instructions import get_main_agent_instructions
from .skills_index import load_skills_index
from .planning import build_nudge_message

__all__ = [
    "get_main_agent_instructions",
    "load_skills_index",
    "build_nudge_message",
]
