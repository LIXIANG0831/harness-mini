"""Bash 命令执行工具模块。"""
import subprocess
from typing import List, Any

from agents import function_tool

from .base_tools import BaseTools


@function_tool
def run_bash(command: str) -> str:
    """在本地执行 shell 命令并返回执行结果。可用于运行脚本、文件操作等。注意：命令在当前工作目录执行。"""
    print(f"🔧 [执行命令] {command}")
    try:
        r = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = ""
        if r.stdout:
            output += r.stdout
        if r.stderr:
            output += f"[stderr]\n{r.stderr}"
        if r.returncode != 0:
            output += f"\n[退出码] {r.returncode}"
        result = output.strip() or f"(命令执行完成，无输出)"
        print(f"🔧 [执行结果] returncode={r.returncode} {output[:1000]}")
        return result
    except subprocess.TimeoutExpired:
        return "❌ 命令执行超时（120秒）"
    except Exception as e:
        return f"❌ 命令执行失败: {e}"


class ShellTools(BaseTools):
    """Bash 工具集：本地命令执行。无外部依赖。"""

    def get_all_tools(self) -> List[Any]:
        return [run_bash]
