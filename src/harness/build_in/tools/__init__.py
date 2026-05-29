"""build_in.tools 工具集合的统一入口。

使用方式：
    from harness.build_in.tools import init_tools, get_all_tools
    init_tools(ov_client, URI_USER, URI_AGENT, OV_MEM_SESSION, state_machine)
    tools = get_all_tools()
"""
from . import ov_tools, planning_tools, base_tools


def init_tools(ov_client, uri_user, uri_agent, mem_session, state_machine):
    """初始化所有需要外部依赖的工具模块。"""
    ov_tools.init_ov_tools(ov_client, uri_user, uri_agent, mem_session)
    planning_tools.init_planning_tools(state_machine)


def get_all_tools():
    """返回所有可用的 function_tool 列表（顺序与 main.py 中保持一致）。"""
    return [
        # ====================== OV 文件系统 ======================
        ov_tools.ov_add_resource,
        ov_tools.ov_extract_memory,
        ov_tools.ov_extract_experience,
        ov_tools.ov_update_memory,
        ov_tools.ov_rm,
        ov_tools.ov_ls,
        ov_tools.ov_find,
        ov_tools.ov_search,
        ov_tools.ov_overview,
        ov_tools.ov_read,
        ov_tools.ov_load_skill,
        ov_tools.ov_add_skill,
        # ====================== 任务执行规划 ======================
        planning_tools.plan_task,
        planning_tools.next_step,
        planning_tools.skip_step,
        planning_tools.fail_current_step,
        planning_tools.get_plan_status,
        # ====================== 基础工具 ======================
        base_tools.run_bash,
    ]


__all__ = ["init_tools", "get_all_tools", "ov_tools", "planning_tools", "base_tools"]
