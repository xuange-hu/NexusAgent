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
