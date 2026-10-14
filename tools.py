"""真实可运行的内置工具：让 NexusAgent 的 demo 不止于 ``calc`` / ``echo``。

这些工具只用 Python 标准库，演示 Agent 如何把"外部能力"注册成可调度单元。
接入真实 LLM 后，模型会自己决定调用哪一个（见 agent.py 的 ``run(llm=...)``）。
"""

from __future__ import annotations

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
