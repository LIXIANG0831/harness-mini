"""任务规划相关的提示词模板。"""


def build_nudge_message(remaining: int, current_idx: int, current_desc: str) -> str:
    """构造"计划未完成自动推进"时给智能体的提示。

    Args:
        remaining: 剩余步骤数
        current_idx: 当前步骤索引（0-based）
        current_desc: 当前步骤描述

    Returns:
        提醒智能体继续执行下一步的指令文本。
    """
    return (
        f"你的计划还有 {remaining} 步未完成，当前应执行第 {current_idx + 1} 步: {current_desc}。"
        f"立即执行此步骤，并在执行后调用 next_step()。不要直接回复用户。"
    )
