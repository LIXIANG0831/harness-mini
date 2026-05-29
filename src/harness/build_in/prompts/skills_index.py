"""Skills 索引加载：扫描当前 Agent 的 skills 目录，构造给 instructions 使用的索引文本。"""


def load_skills_index(ov_client, agent_uri: str) -> str:
    """读取当前 Agent 的 skills 目录，返回 skill 名 + abstract 列表，注入到 instructions。

    Args:
        ov_client: OpenViking 客户端实例
        agent_uri: 当前 Agent 的 URI（例如 "viking://agent/Rebecca/"）

    Returns:
        格式化后的 skills 索引文本；若没有 skills 则返回占位提示。
    """
    skills_uri = f"{agent_uri}skills/"
    try:
        items = ov_client.ls(skills_uri)
    except Exception:
        return "(当前 Agent 暂无 skills)"
    if not items:
        return "(当前 Agent 暂无 skills)"
    lines = ["---"]
    for e in items:
        if not e.get("isDir", False):
            continue
        name = e.get("name", "")
        uri = e.get("uri", "")
        try:
            abstract = ov_client.abstract(uri).strip()
        except Exception:
            abstract = ""
        lines.append(f"- **{name}** (`{uri}`): \n{abstract[:200]}")
    lines.append("---")
    return "\n".join(lines) if lines else "(当前 Agent 暂无 skills)"
