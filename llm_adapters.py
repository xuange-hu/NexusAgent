"""可选的 LLM 适配器：把 OpenAI 兼容接口包装成 ``agent.run`` 需要的回调。

``agent.run(query, llm=...)`` 约定的回调签名为::

    llm(query: str, tool_desc: str) -> (tool_name, arg)

本模块仅用标准库实现，**不引入任何 SDK 依赖**（保持仓库"零运行时依赖"的承诺）。
密钥一律从环境变量读取，绝不硬编码；默认只允许 https 端点。

用法::

    from agent import run
    from llm_adapters import make_openai_llm

    llm = make_openai_llm(model="gpt-4o-mini")   # 读取 OPENAI_API_KEY
    print(run("今天北京天气怎么样", llm=llm))
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Callable, Dict, Tuple

DEFAULT_BASE_URL = "https://api.openai.com/v1"

SYSTEM_PROMPT = (
    "你是一个工具调度器。根据用户的问题和可用工具列表，"
    '只返回一个 JSON 对象：{"tool": "<工具名>", "arg": "<参数>"}。'
    "不要返回任何解释或其它文字。"
)

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def _extract_plan(text: str) -> Tuple[str, str]:
    """从模型输出里稳健地解析出 ``(tool, arg)``。

    容忍 markdown 代码围栏与前后废话；解析失败时退化为 echo，
    保证调用方永远拿到一个合法的工具名，不会抛异常。
    """
    if not text:
        return "echo", ""
    match = _JSON_OBJECT.search(text)
    if not match:
        return "echo", text.strip()
    try:
        data: Dict[str, Any] = json.loads(match.group(0))
    except (ValueError, TypeError):
        return "echo", text.strip()
    tool = str(data.get("tool", "")).strip()
    arg = data.get("arg", "")
    if not tool:
        return "echo", text.strip()
    return tool, "" if arg is None else str(arg)


def make_openai_llm(
    model: str = "gpt-4o-mini",
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: int = 20,
) -> Callable[[str, str], Tuple[str, str]]:
    """返回一个 OpenAI 兼容的 ``llm`` 回调。

    Args:
        model: 模型名。
        base_url: 覆盖端点；也可由 ``OPENAI_BASE_URL`` 提供。
        api_key: 覆盖密钥；缺省读 ``OPENAI_API_KEY``。
        timeout: 请求超时（秒）。
    """

    def llm(query: str, tool_desc: str) -> Tuple[str, str]:
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError("缺少 OPENAI_API_KEY 环境变量")

        url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/") + "/chat/completions"

        # 安全：默认只允许 https，避免明文传输密钥（本地调试地址除外）
        if not url.startswith("https://") and not re.match(
            r"^https?://(localhost|127\.0\.0\.1)(:\d+)?", url
        ):
            raise ValueError(f"不安全的端点（仅允许 https 或本地调试地址）: {url}")

        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"可用工具:\n{tool_desc}\n\n用户问题: {query}",
                },
            ],
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - 已校验 https
            body = json.loads(resp.read().decode("utf-8"))

        content = body["choices"][0]["message"]["content"]
        return _extract_plan(content)

    return llm
