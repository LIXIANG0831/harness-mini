"""包的命令行入口与自测。

运行: python -m state_machine
"""

from .enums import HookEvent
from .machine import TaskStateMachine


def _self_test() -> None:
    sm = TaskStateMachine()
    sm.on(HookEvent.TRANSITION, lambda m, p: print(f"  [hook] {p['from']} → {p['to']}"))

    sm.plan(goal="测试任务", steps=["读文件", "处理数据", "写结果"])
    print(sm.format())
    print()

    sm.start_step()
    sm.set_context("file_size", 1024)
    sm.complete_step(result="读取了 1024 字节")

    sm.complete_step(result="处理完成")
    sm.complete_step(result="写入桌面")

    print(sm.format())
    print(f"\n上下文: {sm.context}")
    print(f"历史事件数: {len(sm.history)}")

    # 序列化测试
    snapshot = sm.to_json()
    print("\n序列化后字节数:", len(snapshot))
    sm2 = TaskStateMachine.from_json(snapshot)
    print("恢复后状态:", sm2.status.value, sm2.progress)


if __name__ == "__main__":
    _self_test()
