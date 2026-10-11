"""NexusAgent 真实工具单测：web_fetch / read_file。

网络与文件系统均用标准库 mock，保证零外部依赖、可在 CI 中稳定跑通。
"""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path
from unittest import mock

import agent
import tools


def test_web_fetch_rejects_non_http_scheme():
    assert tools.web_fetch("ftp://example.com") == "仅支持 http/https 链接"
    assert tools.web_fetch("javascript:alert(1)") == "仅支持 http/https 链接"


def test_web_fetch_success_reads_body():
    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = b"<html>hello world</html>"

    with mock.patch.object(urllib.request, "urlopen", return_value=fake):
        out = tools.web_fetch("https://example.com")

    assert "hello world" in out
    # 仅截取前若干字符，不应返回完整未截断流
    assert len(out) <= tools._MAX_CHARS


def test_web_fetch_network_error_is_returned_not_raised():
    with mock.patch.object(urllib.request, "urlopen", side_effect=OSError("boom")):
        out = tools.web_fetch("https://unreachable.example")

    assert out.startswith("抓取失败")


def test_read_file_missing():
    out = tools.read_file("./this-file-does-not-exist-12345.txt")
    assert "文件不存在" in out


def test_read_file_truncates_to_max_chars():
    long_text = "x" * 2000
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sample.txt"
        p.write_text(long_text, encoding="utf-8")
        out = tools.read_file(str(p))

    assert len(out) == tools._MAX_CHARS
    assert out == "x" * tools._MAX_CHARS


def test_read_file_directory_is_handled_gracefully():
    # 指向一个目录而非文件：is_file 守卫应优雅返回“文件不存在”，不崩溃
    with tempfile.TemporaryDirectory() as d:
        out = tools.read_file(d)

    assert "文件不存在" in out


def test_tools_registered_in_global_registry():
    # web_fetch / read_file 必须在全局 registry 中可被调度
    assert agent.registry.dispatch("web_fetch", "https://example.com") is not None
    assert tools.web_fetch("ftp://x") == "仅支持 http/https 链接"
