"""Agent 离线规划与编排补充单测。

覆盖 ``rule_based_plan`` 中容易被破坏的路由顺序（记忆类前缀必须在
"含数字即 calc" 规则之前），以及 ``run`` 配合内存 LLM 回调时对记忆工具的真实调度。

全部离线、确定性。
"""

import agent
import tools
from agent import rule_based_plan, run


def test_rule_based_plan_remember_not_misrouted_to_calc():
    # "remember a=1+2" 含数字与运算符，但记忆前缀必须优先，否则会被误判为算式
    assert rule_based_plan("remember a=1+2") == ("remember", "a=1+2")


def test_rule_based_plan_recall_and_forget_prefixes():
    assert rule_based_plan("recall name") == ("recall", "name")
    assert rule_based_plan("forget name") == ("forget", "name")


def test_rule_based_plan_remember_with_math_value():
    assert rule_based_plan("remember total=10*2") == ("remember", "total=10*2")


def test_rule_based_plan_routing_is_case_insensitive_for_tool():
    # 前缀匹配对大小写不敏感（决定 tool 名），但 arg 保留原始大小写
    assert rule_based_plan("ECHO hello")[0] == "echo"
    assert rule_based_plan("CALC 1+1")[0] == "calc"


def test_rule_based_plan_math_without_prefix():
    assert rule_based_plan("what is 3*4?") == ("calc", "what is 3*4?")


def test_run_with_fake_llm_invokes_remember():
    tools.memory_clear()
    try:
        def fake_llm(query, tool_desc):
            return "remember", "city=Beijing"

        result = run("请记住城市", llm=fake_llm)
        assert result == "已记住 city"
        assert tools.recall("city") == "Beijing"
    finally:
        tools.memory_clear()


def test_run_with_fake_llm_unknown_tool_returns_unknown():
    def fake_llm(query, tool_desc):
        return "no_such_tool", "x"

    # 未知工具名应走到 registry 的 unknown 分支
    assert run("q", llm=fake_llm).startswith("unknown tool")


def test_run_offline_calc_and_echo():
    assert run("calc 2*3+1") == "7"
    assert run("echo hello") == "hello"
