"""NexusAgent — 极简可运行的 Agent 骨架。

本仓库原为空白占位仓库。该文件给出一个最小但真实可运行的 Agent 架构示例：

- 工具（Tool）通过装饰器注册到 ``ToolRegistry``；
- ``run`` 支持两种模式：
  * 无 LLM 时走本地 ``rule_based_plan``（离线可跑通，适合演示 / 单测）；
  * 传入 ``llm`` 回调时切换到 LLM 规划（可对接 OpenAI / 智谱 GLM 等）。

这是一个**起点**，后续可扩展：对话记忆、多 Agent 协作、MCP 工具接入、
检索增强（RAG）等。请勿将其视为完整产品。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[[str], str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str):
        def deco(func: Callable[[str], str]):
            self._tools[name] = Tool(name=name, description=description, func=func)
            return func

        return deco

    def dispatch(self, name: str, arg: str) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"unknown tool: {name}"
        return tool.func(arg)

    def describe(self) -> str:
        return "\n".join(f"- {t.name}: {t.description}" for t in self._tools.values())


registry = ToolRegistry()


@registry.register("calc", "计算数学表达式，如 calc 1+2*3")
def calc(expr: str) -> str:
    # 仅允许数字与基本运算符，规避 eval 的任意代码执行风险。
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        return "只允许数字与 + - * / ( ) ."
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 - 已做字符白名单
    except Exception as exc:  # noqa: BLE001 - 演示用：返回错误而非崩溃
        return f"计算失败: {exc}"


@registry.register("echo", "原样返回输入，便于调试")
def echo(text: str) -> str:
    return text


def rule_based_plan(query: str) -> tuple[str, str]:
    """无 LLM 时的本地规则规划：识别意图 -> (tool, arg)。"""
    q = query.strip()
    if q.lower().startswith("calc "):
        return "calc", q.split("calc ", 1)[-1]
    if any(ch.isdigit() for ch in q) and any(c in q for c in "+-*/()"):
        return "calc", q
    return "echo", q


def run(query: str, llm=None) -> str:
    """执行一次 agent 循环。

    ``llm`` 签名约定：``llm(query: str, tool_desc: str) -> (tool_name, arg)``。
    为 None 时使用本地规则引擎。
    """
    if llm is None:
        tool, arg = rule_based_plan(query)
    else:
        tool, arg = llm(query, registry.describe())
    return registry.dispatch(tool, arg)


def main() -> None:
    print("NexusAgent 最小骨架（离线规则模式）")
    print("可用工具：\n" + registry.describe())
    print("\n示例：calc 1+2*3 ->", run("calc 1+2*3"))
    print("输入 'exit' 退出。\n")
    while True:
        try:
            q = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if q.strip().lower() in {"exit", "quit"}:
            break
        print(run(q))


if __name__ == "__main__":
    main()
