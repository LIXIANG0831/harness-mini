"""工具基类。

所有工具集合（OV、Planning、Bash 等）继承 BaseTools，
在 __init__ 中接收依赖、实现 get_all_tools() 返回 function_tool 列表。

使用：
    ov = OvTools(ov_client=..., uri_user=..., uri_agent=..., mem_session=...)
    tools = ov.get_all_tools()
"""
from abc import ABC, abstractmethod
from typing import Any, List


class BaseTools(ABC):
    """工具集合抽象基类。子类在构造时完成依赖注入，并实现 get_all_tools()。"""

    @abstractmethod
    def get_all_tools(self) -> List[Any]:
        """返回该工具集对外暴露的 function_tool 列表。"""
        raise NotImplementedError
