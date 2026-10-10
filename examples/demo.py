"""NexusAgent 离线演示：展示工具注册与调度循环。

运行：``python examples/demo.py``
（web_fetch 需要网络；其余步骤完全离线。）
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import registry, run

import tools  # 副作用：注册 web_fetch / read_file


def main() -> None:
    print("NexusAgent 可用工具：\n" + registry.describe())
    print("\n--- 离线规则模式（无需 LLM）---")
    print("calc 1+2*3            ->", run("calc 1+2*3"))
    print("read_file ./README.md ->")
    print(run("read_file ./README.md")[:160])
    print("\n提示：接入 LLM 后，模型可自主决定调用 web_fetch / read_file 等任意工具；")
    print("      离线规则仅覆盖显式前缀（calc / web_fetch / read_file）。")


if __name__ == "__main__":
    main()
