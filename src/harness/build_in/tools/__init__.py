"""build_in.tools 工具集合的统一入口（capability 工具）。

每个类继承 BaseTools，构造时传入依赖、调用 get_all_tools() 拿到该集合的
function_tool 列表。

控制流工具（PlanningTools）属于 runtime 内核，从 `runtime` 包导入。

使用方式：
    from build_in.tools import OvTools, ShellTools

    ov = OvTools(
        ov_client=ov_client,
        uri_user=URI_USER,
        uri_agent=URI_AGENT,
        mem_session=OV_MEM_SESSION,
    )
    bash = ShellTools()

    agent_tools = ov.get_all_tools() + bash.get_all_tools()

新增工具集只需：
    1. 新建 my_tools.py，写若干 @function_tool 函数
    2. 写 class MyTools(BaseTools): __init__ 注入依赖，get_all_tools 返回列表
    3. 在本文件加一行 export
"""
from .base_tools import BaseTools
from .ov_tools import OvTools
from .shell_tools import ShellTools

__all__ = [
    "BaseTools",
    "OvTools",
    "ShellTools",
]
