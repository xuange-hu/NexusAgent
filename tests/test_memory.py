"""记忆工具与规划器路由单测：验证 Agent 的"有状态"能力。

覆盖 remember / recall / forget 的增删查、用法错误提示、
以及规划器对记忆前缀的识别（含"含数字不应被误判为算式"的回归）。
"""

from __future__ import annotations

import pytest

import agent
import tools
from agent import rule_based_plan, run


@pytest.fixture(autouse=True)
def _isolated_memory():
    """每个用例前后清空记忆，避免互相污染。"""
    tools.memory_clear()
    yield
    tools.memory_clear()


def test_remember_then_recall():
    assert run("remember name=Nexus") == "已记住 name"
    assert run("recall name") == "Nexus"


def test_recall_missing_key():
    assert run("recall nope") == "未记住: nope"


def test_remember_requires_equals_sign():
    out = run("remember 忘了写等号")
    assert "用法" in out


def test_remember_rejects_empty_key():
    assert "用法" in run("remember =value")


def test_remember_overwrites_same_key():
    run("remember city=Wuhan")
    run("remember city=Beijing")
    assert run("recall city") == "Beijing"


def test_forget_removes_entry():
    run("remember tmp=1")
    assert run("forget tmp") == "已遗忘 tmp"
    assert run("recall tmp") == "未记住: tmp"


def test_forget_missing_key():
    assert run("forget ghost") == "未记住: ghost"


def test_memory_persists_across_run_calls():
    """记忆是跨调用的状态——这正是它相对 calc/echo 的新能力。"""
    run("remember user=xuange")
    run("echo 中间做了别的事")
    assert run("recall user") == "xuange"


def test_memory_snapshot_and_clear():
    run("remember a=1")
    run("remember b=2")
    assert tools.memory_snapshot() == {"a": "1", "b": "2"}
    tools.memory_clear()
    assert tools.memory_snapshot() == {}


def test_memory_snapshot_returns_copy():
    run("remember k=v")
    snap = tools.memory_snapshot()
    snap["k"] = "mutated"
    assert tools.memory_snapshot()["k"] == "v", "快照应是副本，不能被外部改写"


def test_value_preserves_spaces_and_unicode():
    run("remember note=你好 世界")
    assert run("recall note") == "你好 世界"


# ---------------------------------------------------------------- 规划器路由


def test_planner_routes_memory_prefixes():
    assert rule_based_plan("remember a=1") == ("remember", "a=1")
    assert rule_based_plan("recall a") == ("recall", "a")
    assert rule_based_plan("forget a") == ("forget", "a")


def test_planner_prefix_beats_math_heuristic():
    """回归：含数字与运算符的记忆语句不应被误判为 calc。"""
    assert rule_based_plan("remember total=1+2") == ("remember", "total=1+2")


def test_memory_tools_are_registered():
    """导入 agent 时应一并注册记忆工具（tools 在 agent 末尾被导入）。"""
    desc = agent.registry.describe()
    for name in ("remember", "recall", "forget"):
        assert name in desc
