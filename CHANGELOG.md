# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/) 约定，版本号参考 [SemVer](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-10-11

### Added
- 极简但真实可运行的 Agent 骨架：
  - `ToolRegistry` 装饰器注册表（注册 / 调度 / 描述）。
  - 内置工具 `calc`（字符白名单 eval）、`echo`、`web_fetch`（仅标准库、`http/https` 校验）、`read_file`。
  - 离线规则规划器 `rule_based_plan`；`run()` 支持注入 `llm` 回调升级为自然语言驱动。
- 完整 `pytest` 单测：registry 行为、`calc`/`echo` 边界、规划器意图识别、`web_fetch`/`read_file` 的网络与文件 mock。
- CI 接入 `pytest`（`ubuntu-latest`，零运行时依赖）。

### Notes
- 这是一个**起点**：后续可扩展对话记忆、多 Agent 协作、MCP 工具接入、检索增强（RAG）。
  请勿将其视为完整产品。
