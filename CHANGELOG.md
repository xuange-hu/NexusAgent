# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/) 约定，版本号参考 [SemVer](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2026-10-14

### Added
- **有状态记忆工具** `remember` / `recall` / `forget`（进程内字典，可替换为持久化），
  演示 Agent 跨调用保留信息的能力。
- `llm_adapters.py`：用标准库实现的 OpenAI 兼容 LLM 适配器（零 SDK 依赖），
  密钥走环境变量、默认仅允许 https 端点、输出稳健解析（容忍代码围栏，失败退化为 echo）。
- 规划器支持 `remember` / `recall` / `forget` 前缀，且优先级高于"含数字即 calc"启发式。
- 记忆持久化：`memory_save` / `memory_load`（JSON 落盘，替换语义；文件缺失或格式非法时
  保持现有记忆并只返回提示，不抛异常）。
- 导入 `agent` 时自动注册全部工具（含记忆工具）。

### Tests
- 新增 `tests/test_memory.py`（记忆增删查、用法错误、跨调用状态、快照隔离）与
  `tests/test_llm_adapter.py`（JSON 解析、缺密钥、非 https 拒绝、mock 端到端调度）。
- 测试总数 19 → 46。

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
