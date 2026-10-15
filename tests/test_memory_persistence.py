"""记忆持久化单测：save / load 的往返、错误处理与替换语义。

全程使用临时目录，不触网、不污染仓库。
"""

from __future__ import annotations

import json

import pytest

import tools
from tools import memory_load, memory_save


@pytest.fixture(autouse=True)
def _isolated_memory():
    tools.memory_clear()
    yield
    tools.memory_clear()


def _seed():
    tools.remember("user=xuange")
    tools.remember("city=Wuhan")


def test_save_then_load_roundtrip(tmp_path):
    _seed()
    p = tmp_path / "memory.json"
    assert "已保存 2 条记忆" in memory_save(str(p))

    tools.memory_clear()
    assert tools.memory_snapshot() == {}

    assert "已载入 2 条记忆" in memory_load(str(p))
    assert tools.memory_snapshot() == {"user": "xuange", "city": "Wuhan"}


def test_save_creates_parent_directories(tmp_path):
    _seed()
    p = tmp_path / "nested" / "dir" / "memory.json"
    assert "已保存" in memory_save(str(p))
    assert p.is_file()


def test_saved_file_is_valid_utf8_json(tmp_path):
    tools.remember("note=你好 世界")
    p = tmp_path / "m.json"
    memory_save(str(p))
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data == {"note": "你好 世界"}


def test_load_missing_file_keeps_memory(tmp_path):
    tools.remember("keep=me")
    out = memory_load(str(tmp_path / "nope.json"))
    assert "文件不存在" in out
    assert tools.memory_snapshot() == {"keep": "me"}, "坏输入不应破坏现有记忆"


def test_load_invalid_json_keeps_memory(tmp_path):
    tools.remember("keep=me")
    p = tmp_path / "broken.json"
    p.write_text("{ not json ", encoding="utf-8")
    assert "读取失败" in memory_load(str(p))
    assert tools.memory_snapshot() == {"keep": "me"}


def test_load_non_object_json_is_rejected(tmp_path):
    p = tmp_path / "list.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert "读取失败" in memory_load(str(p))
    assert tools.memory_snapshot() == {}


def test_load_replaces_rather_than_merges(tmp_path):
    """载入是替换语义：旧键不应残留，避免状态混淆。"""
    tools.remember("stale=old")
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"fresh": "new"}), encoding="utf-8")
    memory_load(str(p))
    assert tools.memory_snapshot() == {"fresh": "new"}


def test_load_coerces_values_to_strings(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"n": 42, "b": True}), encoding="utf-8")
    memory_load(str(p))
    snap = tools.memory_snapshot()
    assert snap["n"] == "42" and snap["b"] == "True"
