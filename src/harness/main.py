import asyncio
import os

from config import settings, validate

# 设置代理白名单（必须在导入 openai/openviking 前）
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

import openviking as ov
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
    SQLiteSession,
    SessionSettings,
)
from openai import AsyncOpenAI

from runtime import TaskStateMachine, PlanningTools, get_nudge_message
from build_in.tools import OvTools, ShellTools
from build_in.prompts import get_main_agent_instructions, get_skills_info

# ==================== 校验配置 ====================
validate()

# ==================== 模型客户端 ====================
client = AsyncOpenAI(base_url=settings.openai.base_url, api_key=settings.openai.api_key)
set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

# ==================== OpenViking 客户端 ====================
ov_client = ov.SyncHTTPClient(
    url=settings.ov.url,
    user_id=settings.ov.user_id,
    agent_id=settings.ov.agent_id,
)
ov_client.initialize()
# 确保记忆 session 存在
try:
    ov_client.get_session(settings.ov.mem_session, auto_create=True)
except Exception:
    pass

# ==================== 状态机 ====================
_sm = TaskStateMachine()
planning_tools = PlanningTools(state_machine=_sm)

# ==================== 初始化工具集 ====================
bash_tools = ShellTools()
ov_tools = OvTools(
    ov_client=ov_client,
    uri_user=settings.ov.uri_user,
    uri_agent=settings.ov.uri_agent,
    mem_session=settings.ov.mem_session,
)

TOOLS = (
    planning_tools.get_all_tools()
    + ov_tools.get_all_tools()
    + bash_tools.get_all_tools()
)


# ==================== Skills 预加载 ====================
SKILLS_INFO = get_skills_info(ov_client, settings.ov.uri_agent)


# ==================== 会话管理 ====================
session = SQLiteSession(
    session_id=settings.session.id,
    db_path=settings.session.db_path,
    session_settings=SessionSettings(
        limit=settings.session.limit  # 最大 Messages 条数
    )
)

# ==================== 智能体定义 ====================
main_agent = Agent(
    name="main_agent",
    model=settings.openai.model_name,
    instructions=get_main_agent_instructions(
        ov_user_id=settings.ov.user_id,
        ov_agent_id=settings.ov.agent_id,
        ov_mem_session=settings.ov.mem_session,
        skills_info=SKILLS_INFO,
    ),
    tools=TOOLS,
    handoffs=[
        # 可交接的Agent列表
    ],
)


# ==================== 终端 UI 辅助 ====================
def _print_banner():
    line = "─" * 60
    print(line)
    print(f"  🤖 Harness Mini  ·  model: {settings.openai.model_name}")
    print(f"  user: {settings.ov.user_id}    agent: {settings.ov.agent_id}    session: {settings.session.id}")
    print(f"  tools: {len(TOOLS)}    max_turns: {settings.runtime.max_turns}    nudge_max: {settings.runtime.nudge_max}")
    print(line)
    print("  输入消息开始对话；输入 quit / exit / q / 退出 / 再见 结束。")
    print(line)
    if SKILLS_INFO:
        print(f"📚 已加载 skills 索引:\n{SKILLS_INFO}")
        print(line)


def _print_reply(text: str):
    print(f"🤖 {text}\n", flush=True)


def _print_nudge(remaining: int, count: int):
    print(
        f"\n⚠️  计划未完成（剩余 {remaining} 步），自动推进 [{count}/{settings.runtime.nudge_max}]\n",
        flush=True,
    )


async def main():
    """主程序入口 - 交互式对话"""
    _print_banner()
    while True:
        try:
            user_input = input("\n👨🏻‍💻 ").strip()

            if user_input.lower() in {"quit", "exit", "退出", "q", "再见"}:
                print("\n👋🏻 再见！")
                break

            if not user_input:
                continue

            print(flush=True)

            result = await Runner.run(
                main_agent,
                input=user_input,
                session=session,
                max_turns=settings.runtime.max_turns,
            )
            _print_reply(result.final_output)

            # 保险机制：如果计划没跑完就回复了用户，自动 nudge 继续
            nudge_count = 0
            while _sm.is_running and nudge_count < settings.runtime.nudge_max:
                nudge_count += 1
                idx = _sm.current_step
                remaining = len(_sm.steps) - idx
                next_desc = _sm.steps[idx].desc
                _print_nudge(remaining, nudge_count)
                nudge_msg = get_nudge_message(remaining, idx, next_desc)
                result = await Runner.run(
                    main_agent,
                    input=nudge_msg,
                    session=session,
                    max_turns=settings.runtime.max_turns,
                )
                _print_reply(result.final_output)

        except KeyboardInterrupt:
            print("\n\n👋🏻 再见！")
            break
        except Exception as e:
            print(f"\n❌ [Error] {e}\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
