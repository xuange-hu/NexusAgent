"""LLM 适配器单测：全程离线，用 mock 拦截 urlopen。

覆盖：JSON 解析（含代码围栏/废话/非法 JSON 退化）、缺密钥、非 https 端点拒绝、
以及 mock 成功响应时的完整调度路径。
"""

from __future__ import annotations

import json
import urllib.request
from unittest import mock

import pytest

import agent
import llm_adapters
from llm_adapters import _extract_plan, make_openai_llm


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


def test_extract_plan_plain_json():
    assert _extract_plan('{"tool": "calc", "arg": "1+2*3"}') == ("calc", "1+2*3")


def test_extract_plan_inside_markdown_fence():
    text = '```json\n{"tool": "echo", "arg": "hi"}\n```'
    assert _extract_plan(text) == ("echo", "hi")


def test_extract_plan_tolerates_surrounding_prose():
    text = '当然！我的选择是：\n{"tool": "web_fetch", "arg": "https://example.com"}\n希望有帮助。'
    assert _extract_plan(text) == ("web_fetch", "https://example.com")


def test_extract_plan_degrades_to_echo_on_invalid_json():
    tool, arg = _extract_plan("抱歉，我无法处理")
    assert tool == "echo"
    assert arg == "抱歉，我无法处理"


def test_extract_plan_empty_input():
    assert _extract_plan("") == ("echo", "")


def test_extract_plan_missing_tool_key_degrades():
    assert _extract_plan('{"arg": "x"}')[0] == "echo"


def test_extract_plan_null_arg_becomes_empty_string():
    assert _extract_plan('{"tool": "echo", "arg": null}') == ("echo", "")


def test_make_openai_llm_requires_api_key():
    llm = make_openai_llm()
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm("hi", "tools")


def test_make_openai_llm_rejects_insecure_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    llm = make_openai_llm(base_url="http://evil.example.com/v1")
    with pytest.raises(ValueError, match="不安全"):
        llm("hi", "tools")


def test_make_openai_llm_allows_localhost_debug(monkeypatch):
    """本地调试地址应被放行（http://localhost）。"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = json.dumps(
        {"choices": [{"message": {"content": '{"tool": "echo", "arg": "ok"}'}}]}
    ).encode("utf-8")

    llm = make_openai_llm(base_url="http://localhost:11434/v1")
    with mock.patch.object(urllib.request, "urlopen", return_value=fake):
        assert llm("hi", "tools") == ("echo", "ok")


def test_make_openai_llm_end_to_end_with_mock(monkeypatch):
    """mock 一次完整请求：验证 payload 构造、Authorization 头与结果解析。"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured = {}

    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = json.dumps(
        {"choices": [{"message": {"content": '{"tool": "calc", "arg": "6*7"}'}}]}
    ).encode("utf-8")

    def _spy(req, *a, **k):
        captured["url"] = req.full_url
        captured["auth"] = req.headers.get("Authorization")
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return fake

    llm = make_openai_llm(model="gpt-4o-mini")
    with mock.patch.object(urllib.request, "urlopen", side_effect=_spy):
        tool, arg = llm("六乘七等于多少", "calc: 计算")

    assert tool == "calc" and arg == "6*7"
    assert captured["url"].endswith("/chat/completions")
    assert captured["auth"] == "Bearer sk-test"
    assert captured["payload"]["model"] == "gpt-4o-mini"
    assert captured["payload"]["messages"][0]["role"] == "system"


def test_llm_callback_plugs_into_agent_run(monkeypatch):
    """适配器产出的 (tool, arg) 能被 agent.run 正确调度。"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = json.dumps(
        {"choices": [{"message": {"content": '{"tool": "calc", "arg": "2+3"}'}}]}
    ).encode("utf-8")

    llm = make_openai_llm()
    with mock.patch.object(urllib.request, "urlopen", return_value=fake):
        assert agent.run("随便问点什么", llm=llm) == "5"


def test_system_prompt_mentions_json_contract():
    assert '"tool"' in llm_adapters.SYSTEM_PROMPT
    assert '"arg"' in llm_adapters.SYSTEM_PROMPT
