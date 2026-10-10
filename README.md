# NexusAgent

[![CI](https://github.com/xuange-hu/NexusAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/xuange-hu/NexusAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB)](https://www.python.org)

> 一个**极简但真实可运行**的 Agent 骨架：工具通过装饰器注册，Agent 循环按"规划 → 调度"执行。
> 零运行时依赖，离线规则模式即可跑通；接入 LLM 回调即升级为自然语言驱动。

**English**: A minimal but genuinely runnable Agent skeleton. Tools are registered via a decorator;
the agent loop plans-then-dispatches. Zero runtime dependencies — the offline rule mode runs as-is,
and plugging in an LLM callback upgrades it to natural-language driven.

---

## ✨ 它演示了什么 / What it demonstrates

- **Tool Registry（工具注册表）**：`@registry.register(name, description)` 把一个函数变成可调度工具。
- **Agent Loop（智能体循环）**：`run(query, llm=None)` 先规划出 `(tool, arg)`，再 `dispatch`。
- **两种模式**：
  - 无 LLM → 本地规则规划（识别 `calc` / `web_fetch` / `read_file` 前缀）。
  - 传入 `llm` 回调 → 由模型决定调用哪个工具（可对接 OpenAI / 智谱 GLM 等）。
- **内置真实工具**：`calc`（安全白名单求值）、`web_fetch`（标准库抓取）、`read_file`（读本地文件）。

## 🚀 运行 / Run

```bash
python examples/demo.py
# calc 1+2*3            -> 7
# read_file ./README.md -> (README 前 160 字符)
```

交互模式：

```bash
python agent.py
> calc 1+2*3
7
> exit
```

## 🔌 接入 LLM（示例） / Plug in an LLM

```python
import agent

def my_llm(query: str, tool_desc: str):
    # 调用你的模型，返回 (tool_name, arg)
    ...
    return "web_fetch", "https://example.com"

print(agent.run("把 example.com 首页前 200 字给我", llm=my_llm))
```

## 🧭 扩展路线 / Roadmap

- 对话记忆（短期 / 长期）
- 多 Agent 协作（规划者 + 执行者）
- MCP 工具接入（复用 [agent-scan](https://github.com/xuange-hu/agent-scan) 的生态）
- 检索增强（RAG）

> 这是一个**起点**，不是完整产品。请勿将其直接用于生产。
