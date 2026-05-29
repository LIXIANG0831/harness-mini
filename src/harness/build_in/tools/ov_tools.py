"""OpenViking 三层渐进记忆系统的工具集合。

提供资源添加、记忆提取、检索（L0/L1/L2）、技能加载等能力。
通过 OvTools(BaseTools) 在构造时注入 ov_client 与 URI 配置后使用。
"""
import os
import uuid
from typing import List, Any

from agents import function_tool

from .base_tools import BaseTools

# 模块级变量：@function_tool 闭包通过此引用读取，由 OvTools.__init__ 注入
ov_client = None
URI_USER = None
URI_AGENT = None
OV_MEM_SESSION = None


@function_tool
def ov_add_resource(path: str, reason: str = "") -> str:
    """将本地文件或文件夹添加到 OpenViking 资源库中，后续可通过语义搜索检索到。"""
    print(f"🔧 [ov_add_resource] path={path} reason={reason}")
    if not os.path.exists(path):
        return f"路径不存在: {path}"
    reason = reason or os.path.basename(path)
    try:
        r = ov_client.add_resource(path, reason=reason)
        ov_client.wait_processed()
        print(f"🔧 [结果] {r['root_uri']}")
        return f"已添加资源: {r['root_uri']}"
    except Exception as e:
        return f"添加失败: {e}"


@function_tool
def ov_extract_memory(content: str) -> str:
    """提取并存储用户级记忆到 OpenViking 用户域。每次使用全新的一次性 session，避免历史污染。
    用于记住用户的个人信息、偏好、习惯、事件等重要信息。"""
    print(f"🔧 [ov_extract_memory] {content[:80]}")
    tmp_sid = f"extract-user-{uuid.uuid4().hex[:8]}"
    try:
        ov_client.get_session(tmp_sid, auto_create=True)
        ov_client.add_message(tmp_sid, role="user", content=content)
        ov_client.commit_session(tmp_sid)
        ov_client.wait_processed()
        try:
            ov_client.delete_session(tmp_sid)
        except Exception:
            pass
        print("🔧 [结果] 已提取用户记忆")
        return "已提取用户记忆"
    except Exception as e:
        return f"提取失败: {e}"


@function_tool
def ov_update_memory(uri: str, content: str, mode: str = "append") -> str:
    """更新 OpenViking 中指定 URI 的记忆文件内容。
    mode: append=追加内容（默认，安全）, replace=完全覆盖（危险，仅用于明确要重写整个文件时）。
    URI 格式如 viking://user/{userId}/memories/xxx.md。"""
    print(f"🔧 [ov_update_memory] uri={uri} mode={mode} content_len={len(content)}")
    if mode not in ("append", "replace"):
        return f"❌ mode 必须是 append 或 replace，收到 {mode}"
    try:
        ov_client.write(uri, content, mode=mode)
        print(f"🔧 [结果] {mode} 成功")
        return f"已{('追加' if mode == 'append' else '覆盖')}: {uri}"
    except Exception as e:
        return f"更新失败: {e}"


@function_tool
def ov_extract_experience(content: str) -> str:
    """提取并存储 Agent 经验记忆到 OpenViking Agent 域。每次使用全新的一次性 session。
    用于记录 Agent 学到的工作经验、行为准则、解决过的 case 等。"""
    print(f"🔧 [ov_extract_experience] {content[:80]}")
    tmp_sid = f"extract-agent-{uuid.uuid4().hex[:8]}"
    try:
        ov_client.get_session(tmp_sid, auto_create=True)
        ov_client.add_message(tmp_sid, role="assistant", content=f"[经验] {content}")
        ov_client.commit_session(tmp_sid)
        ov_client.wait_processed()
        try:
            ov_client.delete_session(tmp_sid)
        except Exception:
            pass
        print("🔧 [结果] 已提取 Agent 经验")
        return "已提取 Agent 经验"
    except Exception as e:
        return f"提取失败: {e}"


@function_tool
def ov_find(query: str, scope: str = "user") -> str:
    """在 OpenViking 中进行无状态语义搜索（不带 session 上下文）。scope: user=用户记忆, agent=Agent记忆, resource=资源库, all=全域。"""
    print(f"🔧 [ov_find] query={query} scope={scope}")
    scope_map = {
        "user": URI_USER,
        "agent": URI_AGENT,
        "resource": "viking://resources/",
        "all": "",
    }
    target = scope_map.get(scope.lower(), scope)
    try:
        r = ov_client.find(query, target_uri=target, limit=5, score_threshold=0.25)
        memories = list(getattr(r, "memories", []) or [])
        resources = list(getattr(r, "resources", []) or [])
        items = memories + resources
        print(f"🔧 [结果] memories={len(memories)} resources={len(resources)}")
        if not items:
            return "未找到相关结果"
        lines = []
        for item in items[:10]:
            score = getattr(item, "score", 0)
            uri = getattr(item, "uri", "")
            abbr = getattr(item, "abstract", "")
            lines.append(f"[{score:.2f}] {uri}")
            if abbr:
                lines.append(abbr[:300])
        return "\n\n".join(lines)
    except Exception as e:
        return f"搜索失败: {e}"


@function_tool
def ov_search(query: str, scope: str = "user") -> str:
    """在 OpenViking 中进行带 session 上下文的语义搜索（推荐用于对话场景，召回更准）。scope: user/agent/resource/all。"""
    print(f"🔧 [ov_search] query={query} scope={scope}")
    scope_map = {
        "user": URI_USER,
        "agent": URI_AGENT,
        "resource": "viking://resources/",
        "all": "",
    }
    target = scope_map.get(scope.lower(), scope)
    try:
        r = ov_client.search(
            query=query,
            target_uri=target,
            session_id=OV_MEM_SESSION,
            limit=5,
            score_threshold=0.25,
        )
        memories = list(getattr(r, "memories", []) or [])
        resources = list(getattr(r, "resources", []) or [])
        items = memories + resources
        print(f"🔧 [结果] memories={len(memories)} resources={len(resources)}")
        if not items:
            return "未找到相关结果"
        lines = []
        for item in items[:10]:
            score = getattr(item, "score", 0)
            uri = getattr(item, "uri", "")
            abbr = getattr(item, "abstract", "")
            lines.append(f"[{score:.2f}] {uri}")
            if abbr:
                lines.append(abbr[:300])
        return "\n\n".join(lines)
    except Exception as e:
        return f"搜索失败: {e}"


@function_tool
def ov_read(uri: str) -> str:
    """(L2 详情) 读取 OpenViking 中任意 URI 的完整文件内容。注意：这是最重量的读取方式，优先用 ov_overview 获取概览后再决定是否调用此工具。"""
    print(f"🔧 [ov_read L2] uri={uri}")
    try:
        content = ov_client.read(uri)
        print(f"🔧 [结果] 读取到 {len(content)} 字符")
        return content
    except Exception:
        try:
            content = ov_client.abstract(uri)
            print(f"🔧 [结果] abstract {len(content)} 字符")
            return content
        except Exception as e:
            return f"读取失败: {e}"


@function_tool
def ov_rm(uri: str, recursive: bool = False) -> str:
    """删除 OpenViking 中指定 URI 的文件或目录。用于清理错误或过时的记忆。
    recursive=True 时递归删除目录。仅在确认无误时使用。"""
    print(f"🔧 [ov_rm] uri={uri} recursive={recursive}")
    try:
        ov_client.rm(uri, recursive=recursive)
        print("🔧 [结果] 删除成功")
        return f"已删除: {uri}"
    except Exception as e:
        return f"删除失败: {e}"


@function_tool
def ov_ls(uri: str = "") -> str:
    """列出 OpenViking 中指定 URI 目录下的内容。用于浏览记忆结构、查找文件。不传 uri 时列出所有顶级域。"""
    uri = uri or "viking://"
    print(f"🔧 [ov_ls] uri={uri}")
    try:
        items = ov_client.ls(uri)
        print(f"🔧 [结果] {len(items)} 项")
        if not items:
            return "目录为空"
        lines = []
        for e in items:
            is_dir = e.get("isDir", False)
            name = e.get("name", "")
            child_uri = e.get("uri", "")
            marker = "📁" if is_dir else "📄"
            lines.append(f"{marker} {name}  →  {child_uri}")
        return "\n".join(lines)
    except Exception as e:
        return f"列出失败: {e}"


@function_tool
def ov_overview(uri: str) -> str:
    """(L1 概览) 读取 OpenViking 中指定 URI 的概览内容（约 1k tokens）。包含目录结构、各章节摘要和子文档访问指引，用于理解内容范围后再决定是否加载 L2 详情。"""
    print(f"🔧 [ov_overview L1] uri={uri}")
    try:
        content = ov_client.overview(uri)
        print(f"🔧 [结果] overview {len(content)} 字符")
        return content
    except Exception as e:
        return f"概览读取失败: {e}"


@function_tool
def ov_add_skill(path: str) -> str:
    """将本地 skill 添加到当前 Agent 的 skills 目录。
    path 可以是：
    - 包含 SKILL.md 的目录（推荐，会一并打包辅助文件）
    - 单个 SKILL.md 文件
    技能会自动归到 viking://agent/{agentId}/skills/ 下，后续可通过 ov_load_skill 加载。"""
    print(f"🔧 [ov_add_skill] path={path}")
    if not os.path.exists(path):
        return f"路径不存在: {path}"
    try:
        r = ov_client.add_skill(path)
        ov_client.wait_processed()
        print(f"🔧 [原始返回] {r!r}")
        if isinstance(r, dict):
            uri = r.get("uri") or r.get("root_uri") or "unknown"
            aux = r.get("auxiliary_files", [])
            aux_count = len(aux) if isinstance(aux, (list, tuple)) else (aux if isinstance(aux, int) else 0)
        else:
            uri = str(r)
            aux_count = 0
        print(f"🔧 [结果] {uri} aux={aux_count}")
        msg = f"已添加 skill: {uri}"
        if aux_count:
            msg += f"，辅助文件 {aux_count} 个"
        return msg
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"🔧 [异常] {type(e).__name__}: {e}\n{tb}")
        return f"添加 skill 失败 ({type(e).__name__}): {e}"


@function_tool
def ov_load_skill(skill_uri: str) -> str:
    """按需加载某个 skill 的完整内容。当 instructions 中的 skill 列表提示某个 skill 与当前任务相关时，调用此工具获取 SKILL.md 全文。
    skill_uri 格式: viking://agent/{agentId}/skills/{skill-name}/ 或具体的 SKILL.md URI。"""
    print(f"🔧 [ov_load_skill] uri={skill_uri}")
    try:
        if not skill_uri.endswith(".md"):
            items = ov_client.ls(skill_uri)
            skill_md = next(
                (e["uri"] for e in items if e.get("name", "").lower() == "skill.md"),
                None,
            )
            target = skill_md or skill_uri
        else:
            target = skill_uri
        content = ov_client.read(target)
        print(f"🔧 [结果] skill 加载 {len(content)} 字符")
        return content
    except Exception:
        try:
            content = ov_client.overview(skill_uri)
            print(f"🔧 [结果] overview {len(content)} 字符")
            return content
        except Exception as e:
            return f"加载 skill 失败: {e}"


class OvTools(BaseTools):
    """OpenViking 三层记忆系统工具集。

    构造时传入 ov_client / uri_user / uri_agent / mem_session 即完成初始化。
    """

    def __init__(self, ov_client, uri_user: str, uri_agent: str, mem_session: str):
        # 注入到模块级变量，供 @function_tool 闭包读取
        globals()["ov_client"] = ov_client
        globals()["URI_USER"] = uri_user
        globals()["URI_AGENT"] = uri_agent
        globals()["OV_MEM_SESSION"] = mem_session

    def get_all_tools(self) -> List[Any]:
        return [
            ov_add_resource,
            ov_extract_memory,
            ov_extract_experience,
            ov_update_memory,
            ov_rm,
            ov_ls,
            ov_find,
            ov_search,
            ov_overview,
            ov_read,
            ov_load_skill,
            ov_add_skill,
        ]
