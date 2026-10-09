# NexusAgent

极简、可运行的 AI Agent 骨架（Python）。本仓库原为空白占位，**当前为一个最小但真实的起点**，用于承载你后续的 Agent 方向项目。

## 特性

- 工具以装饰器注册（`@registry.register`），易于扩展；
- 两种运行模式：
  - **离线规则模式**（默认）：无需任何 API key，`calc` / `echo` 等本地工具即可跑通，适合演示与单测；
  - **LLM 模式**：传入 `llm` 回调即可切换到大模型规划，可对接 OpenAI / 智谱 GLM 等；
- 零运行时依赖（标准库实现）。

## 快速开始

```bash
python agent.py
# > calc 1+2*3
# 7
```

在代码中使用：

```python
import agent
agent.run("calc 1+2*3")          # '7'
agent.run("hello")               # 'hello'（echo）
```

## 目录结构

```
NexusAgent/
├── agent.py            # Agent 核心：工具注册表 + 运行循环
├── requirements.txt    # 依赖（当前为零依赖，可选 LLM SDK 见注释）
├── .github/workflows/  # 基础 CI（导入冒烟 + 示例运行）
└── LICENSE
```

## 路线图（待办）

- [ ] 接入真实 LLM 后端（智谱 GLM / OpenAI 兼容接口）
- [ ] 对话记忆（短期 / 长期）
- [ ] 多 Agent 协作（规划者 + 执行者）
- [ ] MCP 工具协议接入
- [ ] 检索增强（RAG）

> 这是一个脚手架，不是完整产品。欢迎在此之上扩展。
