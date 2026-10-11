"""NexusAgent 核心逻辑单测：ToolRegistry、离线规划器、run 编排。

全部离线、确定性，无需网络或 LLM。
"""

from __future__ import annotations

import agent
from agent import ToolRegistry, calc, echo, rule_based_plan, run


def test_registry_register_and_dispatch():
    reg = ToolRegistry()

    @reg.register("demo", "demo tool")
    def _demo(arg: str) -> str:
        return f"got:{arg}"

    assert "demo" in reg._tools
    assert reg.dispatch("demo", "x") == "got:x"


def test_registry_dispatch_unknown():
    reg = ToolRegistry()
    assert reg.dispatch("nope", "x").startswith("unknown tool")


def test_registry_describe_lists_all():
    reg = ToolRegistry()

    @reg.register("a", "tool a")
    def _a(arg: str) -> str:
        return arg

    @reg.register("b", "tool b")
    def _b(arg: str) -> str:
        return arg

    desc = reg.describe()
    assert "a" in desc and "b" in desc


def test_calc_basic_math():
    # 1+2*3 = 7（运算符优先级）
    assert calc("1+2*3") == "7"
    assert run("calc 1+2*3") == "7"


def test_calc_invalid_chars_rejected():
    assert calc("import os").startswith("只允许")
    assert calc("__import__('os')").startswith("只允许")


def test_calc_division_by_zero_returns_error():
    out = calc("1/0")
    assert "计算失败" in out


def test_echo_passthrough():
    assert echo("hello") == "hello"
    assert run("echo hello world") == "hello world"


def test_rule_based_plan_explicit_prefixes():
    assert rule_based_plan("calc 4+5") == ("calc", "4+5")
    assert rule_based_plan("web_fetch https://x") == ("web_fetch", "https://x")
    assert rule_based_plan("read_file ./README.md") == ("read_file", "./README.md")


def test_rule_based_plan_detects_math_expression():
    # 含数字与运算符但无显式前缀 -> 走 calc
    assert rule_based_plan("what is 3+4?") == ("calc", "what is 3+4?")


def test_rule_based_plan_fallback_to_echo():
    assert rule_based_plan("hello there") == ("echo", "hello there")


def test_run_with_llm_callback():
    # 模拟一个 LLM 规划器：把任何输入都路由到 echo
    def fake_llm(query, tool_desc):
        return "echo", query

    assert run("anything", llm=fake_llm) == "anything"


def test_run_offline_uses_rule_engine():
    # 离线模式默认走 rule_based_plan
    assert run("calc 2*3") == "6"
