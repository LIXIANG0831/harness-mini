"""任务规划工具：基于 TaskStateMachine 暴露给 LLM 的控制流原语。

与 build_in.tools 下的 capability 工具不同，这里的工具直接操作 runtime
内核状态机（_sm），是 harness 控制流的一部分，因此与 state_machine 同
属 runtime 包。
"""
import json
from typing import List, Any

from agents import function_tool

from build_in.tools.base_tools import BaseTools
from runtime.state_machine import TaskStatus

# 模块级变量：@function_tool 闭包通过此引用读取，由 PlanningTools.__init__ 注入
_sm = None


@function_tool
def plan_task(goal: str, steps: str) -> str:
    """为复杂任务创建执行计划。
    goal: 任务目标描述
    steps: JSON 数组格式的步骤列表，每个步骤是一个字符串。例如: '["步骤1", "步骤2", "步骤3"]'
    创建计划后，使用 next_step 逐步推进执行。"""
    print(f"🔧 [plan_task] goal={goal}")
    try:
        step_list = json.loads(steps)
        if not isinstance(step_list, list) or not step_list:
            return "❌ steps 必须是非空 JSON 数组"
    except json.JSONDecodeError:
        return "❌ steps 格式错误，需要 JSON 数组，如 '[\"步骤1\", \"步骤2\"]'"
    if _sm.status != TaskStatus.IDLE:
        _sm.reset()
    _sm.plan(goal=goal, steps=step_list)
    total = len(step_list)
    print(f"🔧 [结果] 已创建 {total} 步计划 (task_id={_sm.task_id})")
    lines = [f"📋 任务计划已创建: {goal}", f"共 {total} 步:"]
    for i, s in enumerate(step_list):
        lines.append(f"  {i+1}. {s}")
    lines.append("")
    lines.append(f"▶️ 立即执行第 1 步: {step_list[0]}")
    lines.append("⚠️ 严格规则：执行完此步骤后，下一个工具调用【必须】是 next_step()，不要直接回复用户。")
    return "\n".join(lines)


@function_tool
def next_step(result: str = "") -> str:
    """标记当前步骤完成并推进到下一步。在执行完每一步后【立即】调用此工具。
    result: 当前步骤的执行结果摘要（必填）。
    返回下一步的描述，或者任务完成的通知。"""
    if not _sm.is_running:
        return "❌ 没有正在执行的计划，请先用 plan_task 创建"
    idx = _sm.current_step
    step = _sm.steps[idx]
    print(f"🔧 [next_step] 完成第 {idx+1} 步: {step.desc}")
    next_s = _sm.complete_step(result=result)
    if next_s is None:
        return f"✅ 全部 {len(_sm.steps)} 步已完成！可以给用户最终回复了。\n\n{_sm.format()}"
    remaining = len(_sm.steps) - _sm.current_step
    progress = f"[{_sm.current_step}/{len(_sm.steps)}]"
    return (
        f"{progress} ✅ 第 {idx+1} 步已记录\n"
        f"\n▶️ 立即执行第 {_sm.current_step+1} 步: {next_s.desc}\n"
        f"⚠️ 还有 {remaining} 步未完成，禁止直接回复用户。执行此步后【必须】再次调用 next_step()。"
    )


@function_tool
def skip_step(reason: str = "") -> str:
    """跳过当前步骤（当步骤不适用或已无需执行时）。"""
    if not _sm.is_running:
        return "❌ 没有正在执行的计划"
    idx = _sm.current_step
    print(f"🔧 [skip_step] 跳过第 {idx+1} 步: {_sm.steps[idx].desc}")
    next_s = _sm.skip_step(reason=reason)
    if next_s is None:
        return f"✅ 全部步骤已处理完毕。\n\n{_sm.format()}"
    remaining = len(_sm.steps) - _sm.current_step
    return f"⏭️ 已跳过。下一步: {next_s.desc} (还有 {remaining} 步)"


@function_tool
def fail_current_step(error: str) -> str:
    """标记当前步骤失败，整个任务进入 FAILED 状态。"""
    if not _sm.is_running:
        return "❌ 没有正在执行的计划"
    idx = _sm.current_step
    print(f"🔧 [fail_step] 第 {idx+1} 步失败: {error[:80]}")
    _sm.fail_step(error=error)
    return f"❌ 第 {idx+1} 步失败: {error}\n\n{_sm.format()}\n\n可以告知用户失败原因，或用 plan_task 重新规划。"


@function_tool
def get_plan_status() -> str:
    """查看当前任务计划的执行状态。"""
    return _sm.format()


class PlanningTools(BaseTools):
    """任务规划工具集。构造时传入 TaskStateMachine 实例。"""

    def __init__(self, state_machine):
        globals()["_sm"] = state_machine

    def get_all_tools(self) -> List[Any]:
        return [
            plan_task,
            next_step,
            skip_step,
            fail_current_step,
            get_plan_status,
        ]
