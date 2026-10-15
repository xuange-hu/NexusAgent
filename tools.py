"""真实可运行的内置工具：让 NexusAgent 的 demo 不止于 ``calc`` / ``echo``。

这些工具只用 Python 标准库，演示 Agent 如何把"外部能力"注册成可调度单元。
接入真实 LLM 后，模型会自己决定调用哪一个（见 agent.py 的 ``run(llm=...)``）。
"""

from __future__ import annotations

import json
import pathlib
import urllib.request

from agent import registry

_MAX_CHARS = 800


@registry.register("web_fetch", "抓取一个 http/https 网页的前若干字符，如 web_fetch https://example.com")
def web_fetch(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "仅支持 http/https 链接"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexusAgent/0.1"})
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 - 仅允许 http/https
            body = resp.read(2048).decode("utf-8", "replace")
        return body[:_MAX_CHARS]
    except Exception as exc:  # 演示用：返回错误而非崩溃
        return f"抓取失败: {exc}"


@registry.register("read_file", "读取本地文本文件的前若干字符，如 read_file ./README.md")
def read_file(path: str) -> str:
    p = pathlib.Path(path)
    if not p.is_file():
        return f"文件不存在: {path}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[:_MAX_CHARS]
    except Exception as exc:
        return f"读取失败: {exc}"


# --------------------------------------------------------------------------
# 记忆工具：演示 Agent 的"有状态"能力（跨轮次保留信息）。
# 进程内字典，重启即清空——刻意保持最小实现，便于替换为 Redis / SQLite。
# --------------------------------------------------------------------------

_MEMORY: dict[str, str] = {}


@registry.register("remember", "记住一个键值对，如 remember name=Nexus")
def remember(arg: str) -> str:
    if "=" not in arg:
        return "用法: remember <键>=<值>"
    key, _, value = arg.partition("=")
    key = key.strip()
    if not key:
        return "用法: remember <键>=<值>"
    _MEMORY[key] = value.strip()
    return f"已记住 {key}"


@registry.register("recall", "读取已记住的值，如 recall name")
def recall(key: str) -> str:
    key = key.strip()
    if not key:
        return "用法: recall <键>"
    return _MEMORY.get(key, f"未记住: {key}")


@registry.register("forget", "删除已记住的键，如 forget name")
def forget(key: str) -> str:
    key = key.strip()
    if _MEMORY.pop(key, None) is not None:
        return f"已遗忘 {key}"
    return f"未记住: {key}"


def memory_snapshot() -> dict[str, str]:
    """返回当前记忆快照（供测试与调试使用，生产可替换为持久化）。"""
    return dict(_MEMORY)


def memory_clear() -> None:
    """清空记忆（测试隔离用）。"""
    _MEMORY.clear()


def memory_save(path: str) -> str:
    """把记忆持久化到 JSON 文件。

    演示如何把进程内状态落盘——换成 SQLite / Redis 时，
    ``remember`` / ``recall`` 的对外契约无需改变。
    """
    try:
        p = pathlib.Path(path)
        if p.parent != pathlib.Path(""):
            p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(_MEMORY, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return f"已保存 {len(_MEMORY)} 条记忆到 {path}"
    except OSError as exc:
        return f"保存失败: {exc}"


def memory_load(path: str) -> str:
    """从 JSON 文件恢复记忆（**替换**当前记忆）。

    文件缺失或格式非法时保持现有记忆不变，只返回提示——不抛异常，
    避免一次坏文件毁掉整个 Agent 会话。
    """
    p = pathlib.Path(path)
    if not p.is_file():
        return f"文件不存在: {path}"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return f"读取失败: {exc}"
    if not isinstance(data, dict):
        return f"读取失败: {path} 顶层不是 JSON 对象"

    restored = {str(k): str(v) for k, v in data.items()}
    _MEMORY.clear()
    _MEMORY.update(restored)
    return f"已载入 {len(_MEMORY)} 条记忆"
