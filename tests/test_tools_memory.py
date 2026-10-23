"""NexusAgent 记忆工具与文件/网络工具的离线单测。

覆盖 ``tools.py`` 中的纯逻辑：
- ``remember`` / ``recall`` / ``forget`` / ``memory_snapshot`` / ``memory_clear``；
- ``memory_save`` / ``memory_load`` 的落盘往返与各类错误分支；
- ``web_fetch`` 截断到 ``_MAX_CHARS``、``read_file`` 读取真实文件内容。

全部离线，文件系统落盘只写到模块级 ``_TMP`` 目录（不使用会自动删除的
tempfile.TemporaryDirectory，规避沙箱 safe-delete 在清理时的 WinError 32）。
"""

import os
import pathlib
import sys
from unittest import mock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import agent  # noqa: E402  (导入即触发 tools 注册)
import tools  # noqa: E402


# ----------------------------------------------------------------- 安全临时目录
# 不使用 TemporaryDirectory：沙箱 safe-delete 在退出清理时会抛 WinError 32。
# 改为在模块加载时创建、开头尽力清理旧残留、且永不自动删除。
_TMP = os.path.join(os.path.dirname(__file__), f".smoke-{os.getpid()}")


def _cleanup_leftovers():
    base = os.path.dirname(__file__)
    for name in os.listdir(base):
        if name.startswith(".smoke-"):
            p = os.path.join(base, name)
            try:
                if os.path.isdir(p):
                    import shutil

                    shutil.rmtree(p)
                else:
                    os.remove(p)
            except OSError:
                pass


_cleanup_leftovers()
os.makedirs(_TMP, exist_ok=True)


@pytest.fixture(autouse=True)
def _clear_memory():
    tools.memory_clear()
    yield
    tools.memory_clear()


# ----------------------------------------------------------------- 记忆基本行为

def test_remember_and_recall():
    assert tools.remember("name=Nexus") == "已记住 name"
    assert tools.recall("name") == "Nexus"


def test_remember_requires_equal_sign():
    assert tools.remember("noequalsign").startswith("用法")
    assert tools.remember("=onlyvalue").startswith("用法")


def test_remember_empty_key_rejected():
    assert tools.remember("=value").startswith("用法")


def test_recall_empty_key_usage():
    assert tools.recall("").startswith("用法")


def test_forget_unknown_key():
    assert tools.forget("ghost") == "未记住: ghost"


def test_forget_existing_key():
    tools.remember("k=v")
    assert tools.forget("k") == "已遗忘 k"
    assert tools.recall("k") == "未记住: k"


def test_memory_snapshot_is_independent_copy():
    tools.remember("a=1")
    snap = tools.memory_snapshot()
    snap["a"] = "mutated"
    # 修改快照不应影响内部状态
    assert tools.recall("a") == "1"
    assert tools.memory_snapshot() == {"a": "1"}


def test_memory_clear_empties_state():
    tools.remember("a=1")
    tools.memory_clear()
    assert tools.memory_snapshot() == {}


# ----------------------------------------------------------------- 落盘往返

def test_memory_save_and_load_roundtrip():
    tools.remember("name=Nexus")
    tools.remember("role=agent")
    path = os.path.join(_TMP, "mem.json")
    assert tools.memory_save(path).startswith("已保存")

    tools.memory_clear()
    assert tools.recall("name") == "未记住: name"

    assert tools.memory_load(path).startswith("已载入")
    assert tools.recall("name") == "Nexus"
    assert tools.recall("role") == "agent"


def test_memory_load_missing_file():
    path = os.path.join(_TMP, "does-not-exist.json")
    assert tools.memory_load(path).startswith("文件不存在")


def test_memory_load_invalid_json():
    path = os.path.join(_TMP, "bad.json")
    pathlib.Path(path).write_text("this is { not json", encoding="utf-8")
    assert tools.memory_load(path).startswith("读取失败")


def test_memory_load_non_dict_top_level():
    path = os.path.join(_TMP, "list.json")
    pathlib.Path(path).write_text("[1, 2, 3]", encoding="utf-8")
    msg = tools.memory_load(path)
    assert "顶层不是 JSON 对象" in msg


def test_memory_save_oserror_is_returned_not_raised():
    path = os.path.join(_TMP, "readonly.json")
    with mock.patch.object(
        pathlib.Path, "write_text", side_effect=OSError("disk full")
    ):
        assert tools.memory_save(path).startswith("保存失败")


# ----------------------------------------------------------------- web_fetch / read_file

def test_web_fetch_truncates_to_max_chars():
    fake = mock.MagicMock()
    fake.__enter__.return_value = fake
    fake.read.return_value = b"x" * 2048  # 实际读取 2048 字节

    # tools 内部使用 urllib.request.urlopen
    with mock.patch.object(tools.urllib.request, "urlopen", return_value=fake):
        out = tools.web_fetch("https://example.com")

    assert len(out) == tools._MAX_CHARS
    assert out == "x" * tools._MAX_CHARS


def test_read_file_real_content():
    path = os.path.join(_TMP, "sample.txt")
    pathlib.Path(path).write_text("hello nexus", encoding="utf-8")
    assert tools.read_file(path) == "hello nexus"


def test_read_file_truncates_long_content():
    path = os.path.join(_TMP, "long.txt")
    pathlib.Path(path).write_text("y" * 2000, encoding="utf-8")
    out = tools.read_file(path)
    assert len(out) == tools._MAX_CHARS
    assert out == "y" * tools._MAX_CHARS


def test_read_file_directory_is_handled_gracefully():
    # 指向目录：is_file 守卫优雅返回"文件不存在"
    assert "文件不存在" in tools.read_file(_TMP)
