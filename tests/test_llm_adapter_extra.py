"""LLM 适配器补充单测：错误路径、环境变量、超时透传、更多 _extract_plan 边界。

全程离线，``urllib.request.urlopen`` 用 mock 拦截。覆盖：
- ``_extract_plan`` 的贪婪匹配退化、空白环绕 tool、arg 为非字符串/缺省/嵌套；
- ``make_openai_llm`` 从环境变量读取 api_key / base_url、把 timeout 透传给 urlopen、
  urlopen 抛 ``URLError`` / ``TimeoutError`` 时应向上传播（适配器不做重试）、
  非 https 且非本地地址被拒、base_url 尾部斜杠规范化。
"""

import json
import urllib.error
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


# ----------------------------------------------------------------- _extract_plan

def test_extract_plan_greedy_multi_object_degrades_to_echo():
    # 两个 JSON 对象时，贪婪匹配 {.*} 会吞掉中间文本，整体非法 JSON -> echo
    text = 'a {"tool":"x","arg":"1"} b {"tool":"y","arg":"2"}'
    tool, arg = _extract_plan(text)
    assert tool == "echo"


def test_extract_plan_whitespace_around_tool_stripped():
    assert _extract_plan('{"tool": "  calc  ", "arg": "1+1"}') == ("calc", "1+1")


def test_extract_plan_arg_as_number_coerced_to_str():
    assert _extract_plan('{"tool":"echo","arg":123}') == ("echo", "123")


def test_extract_plan_missing_arg_key_defaults_empty():
    assert _extract_plan('{"tool":"calc"}') == ("calc", "")


def test_extract_plan_empty_object_degrades_to_echo():
    # 空对象没有 tool 字段，退化为 echo，且 arg 为原始文本本身
    assert _extract_plan("{}") == ("echo", "{}")


def test_extract_plan_nested_value_json_serialized():
    tool, arg = _extract_plan('{"tool":"echo","arg":{"a":1}}')
    assert tool == "echo"
    assert "a" in arg  # 嵌套对象被 str() 化，不再抛异常


def test_extract_plan_surrounding_whitespace_and_newlines():
    text = '\n\n  {"tool": "web_fetch", "arg": "https://x"}  \n'
    assert _extract_plan(text) == ("web_fetch", "https://x")


# ----------------------------------------------------------------- make_openai_llm

def _ok_response(content: str):
    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = json.dumps(
        {"choices": [{"message": {"content": content}}]}
    ).encode("utf-8")
    return fake


def test_make_openai_llm_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    with mock.patch.object(
        urllib.request, "urlopen", return_value=_ok_response('{"tool":"echo","arg":"hi"}')
    ):
        assert make_openai_llm()("q", "tools") == ("echo", "hi")


def test_make_openai_llm_reads_base_url_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://my.gateway/v1")

    captured = {}

    def _spy(req, *a, **k):
        captured["url"] = req.full_url
        return _ok_response('{"tool":"echo","arg":"x"}')

    with mock.patch.object(urllib.request, "urlopen", side_effect=_spy):
        make_openai_llm()("q", "tools")

    assert captured["url"].startswith("https://my.gateway/v1/chat/completions")


def test_make_openai_llm_passes_timeout_to_urlopen(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")

    captured = {}

    def _spy(req, *a, **k):
        captured["timeout"] = k.get("timeout")
        return _ok_response('{"tool":"echo","arg":"x"}')

    with mock.patch.object(urllib.request, "urlopen", side_effect=_spy):
        make_openai_llm(timeout=42)("q", "tools")

    assert captured["timeout"] == 42


def test_make_openai_llm_trailing_slash_base_url_normalized(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")

    captured = {}

    def _spy(req, *a, **k):
        captured["url"] = req.full_url
        return _ok_response('{"tool":"echo","arg":"x"}')

    with mock.patch.object(urllib.request, "urlopen", side_effect=_spy):
        make_openai_llm(base_url="https://api.example.com/v1/")("q", "tools")

    assert captured["url"] == "https://api.example.com/v1/chat/completions"


def test_make_openai_llm_urlerror_propagates(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    with mock.patch.object(
        urllib.request, "urlopen", side_effect=urllib.error.URLError("nope")
    ):
        with pytest.raises(urllib.error.URLError):
            make_openai_llm()("q", "tools")


def test_make_openai_llm_timeout_error_propagates(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    with mock.patch.object(
        urllib.request, "urlopen", side_effect=TimeoutError("timed out")
    ):
        with pytest.raises(TimeoutError):
            make_openai_llm()("q", "tools")


def test_make_openai_llm_rejects_ftp_scheme(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    with pytest.raises(ValueError, match="不安全"):
        make_openai_llm(base_url="ftp://evil.example.com/v1")("q", "tools")


def test_make_openai_llm_auth_header_uses_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")

    captured = {}

    def _spy(req, *a, **k):
        captured["auth"] = req.headers.get("Authorization")
        return _ok_response('{"tool":"echo","arg":"x"}')

    with mock.patch.object(urllib.request, "urlopen", side_effect=_spy):
        make_openai_llm()("q", "tools")

    assert captured["auth"] == "Bearer sk-secret"


def test_llm_callback_feeds_agent_run_end_to_end(monkeypatch):
    """适配器产出的 (tool, arg) 能驱动 agent.run 执行真实工具。"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")

    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = json.dumps(
        {"choices": [{"message": {"content": '{"tool": "calc", "arg": "2+3"}'}}]}
    ).encode("utf-8")

    llm = make_openai_llm()
    with mock.patch.object(urllib.request, "urlopen", return_value=fake):
        assert agent.run("随便问", llm=llm) == "5"
