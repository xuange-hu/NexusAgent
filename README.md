# NexusAgent

[![CI](https://github.com/xuange-hu/NexusAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/xuange-hu/NexusAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB)](https://www.python.org)

> 一个**极简但真实可运行**的 Agent 骨架：工具通过装饰器注册，Agent 循环按"规划 → 调度"执行。
> 零运行时依赖，离线规则模式即可跑通；接入 LLM 回调即升级为自然语言驱动。

**English**: A minimal but genuinely runnable Agent skeleton. Tools are registered via a decorator;
the agent loop plans-then-dispatches. Zero runtime dependencies — the offline rule mode runs as-is,
and plugging in an LLM callback upgrades it to natural-language driven.

## 能力一览

| 工具 | 说明 | 依赖 |
|---|---|---|
| `calc` | 计算数学表达式（字符白名单，规避 `eval` 任意执行风险） | 标准库 |
| `echo` | 原样返回输入，便于调试 | — |
| `web_fetch` | 抓取 http/https 网页前若干字符 | 标准库 |
| `read_file` | 读取本地文本文件前若干字符 | 标准库 |
| `remember` / `recall` / `forget` | **有状态**记忆：跨调用保留键值对 | 进程内字典 |

## 记忆工具（有状态）

```
> remember user=xuange
已记住 user
> echo 中间做了别的事
中间做了别的事
> recall user
xuange
```

记忆默认存在进程内字典里（重启即清空）。需要跨进程保留时，用配套的持久化函数：

```python
from tools import memory_save, memory_load

memory_save("./memory.json")   # 落盘
memory_load("./memory.json")   # 恢复（替换语义，坏文件不会破坏现有记忆）
```

底层换成 SQLite / Redis 时，`remember` / `recall` / `forget` 的对外契约无需改变。

## 接入真实 LLM

`llm_adapters.py` 用**标准库**把 OpenAI 兼容接口包装成 `run()` 需要的回调，
不引入任何 SDK，保持"零运行时依赖"。密钥从环境变量读取，且默认只允许 https 端点。

```python
from agent import run
from llm_adapters import make_openai_llm

llm = make_openai_llm(model="gpt-4o-mini")   # 读取 OPENAI_API_KEY
print(run("六乘七等于多少", llm=llm))
```

回调签名：`llm(query: str, tool_desc: str) -> (tool_name, arg)`。
模型输出会被稳健解析（容忍 markdown 围栏与前后废话），解析失败时退化为 `echo`。

## 路线图

- [ ] 对话记忆 / 多轮上下文
- [ ] 多 Agent 协作
- [ ] MCP 工具接入
- [ ] 检索增强（RAG）


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
