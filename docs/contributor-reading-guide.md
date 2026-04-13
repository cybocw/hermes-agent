# Hermes Agent 新贡献者阅读路线与模块速查

Date: 2026-04-11

这是一份面向新贡献者的快速上手文档。它和 `docs/project-architecture.md` 的关系是：

- `docs/project-architecture.md` 负责解释“为什么这样设计”。
- 本文负责回答“我要改一个功能时，先看哪里、再看哪里”。

如果你是第一次进入这个仓库，建议先用本文建立地图，再去读 `docs/project-architecture.md` 补足整体理解。

## 1. 先建立整体心智模型

先记住一句话：

> Hermes Agent = `AIAgent` 运行时 + 多入口壳层 + 工具/插件/MCP/技能扩展面 + SQLite 会话与记忆体系。

如果你暂时只能记住 5 个文件，优先记住这 5 个：

1. `run_agent.py`：运行时中枢，所有能力最终都会汇到这里。
2. `model_tools.py`：工具发现、筛选、schema 修补、dispatch 桥接。
3. `tools/registry.py`：工具注册表，所有工具的统一入口。
4. `toolsets.py`：哪些工具在什么平台/场景下可见。
5. `hermes_state.py`：会话持久化、FTS 检索、session lineage。

## 2. 15 分钟快速阅读路线

如果你只想快速定位系统边界，按下面顺序读：

1. `README.md`
2. `pyproject.toml`
3. `run_agent.py`
4. `model_tools.py`
5. `tools/registry.py`
6. `toolsets.py`
7. `hermes_state.py`
8. `cli.py`
9. `gateway/run.py`

读完这 9 个文件，通常已经能回答：

- 用户输入是怎么进入 agent 的。
- tool schema 是怎么暴露给模型的。
- 工具调用最终落到哪里执行。
- 为什么 Gateway 会缓存 `AIAgent` 实例。
- 为什么 compression 会改变 session 结构。

## 3. 60 分钟精读路线

如果你准备真正改代码，建议继续补读以下模块：

### 3.1 Prompt 与上下文

- `agent/prompt_builder.py`
- `agent/context_compressor.py`
- `agent/model_metadata.py`

要理解的核心点：

- system prompt 是分层拼装的，不是一段硬编码字符串。
- prompt cache 稳定性是高优先级约束。
- context compression 不是简单截断，而是“压缩并续链成新 session”。

### 3.2 Memory 与技能

- `agent/memory_manager.py`
- `agent/skill_commands.py`
- `tools/memory_tool.py`
- `tools/skills_tool.py`

要理解的核心点：

- 内建 memory 和外部 memory provider 可以同时存在，但外部 provider 最多一个。
- skill 既是 prompt 侧能力，也是 CLI / Gateway 可触发的工作流入口。

### 3.3 扩展机制

- `tools/mcp_tool.py`
- `hermes_cli/plugins.py`
- `tools/delegate_tool.py`

要理解的核心点：

- MCP 是“外部服务工具桥接”。
- plugin 是“本地运行时扩展”。
- delegate 是“子 agent 协作”，不是普通工具的简单包装。

## 4. 模块关系速查

下面这张“谁依赖谁”的简化图，适合在改代码前先过一遍：

```text
User / Platform Input
  -> cli.py | gateway/run.py | acp_adapter/
  -> run_agent.py (AIAgent)
  -> agent/prompt_builder.py
  -> model_tools.py
  -> tools/registry.py
  -> tools/*.py / tools/mcp_tool.py / plugins
  -> hermes_state.py / gateway/session.py
```

可以进一步记成下面几组关系：

- 入口层：`hermes_cli/main.py`、`cli.py`、`gateway/run.py`、`acp_adapter/`
- 运行时：`run_agent.py`
- Prompt / Memory / Compression：`agent/`
- 工具分发：`model_tools.py` + `tools/registry.py` + `toolsets.py`
- 扩展面：`tools/mcp_tool.py`、`hermes_cli/plugins.py`、`agent/skill_commands.py`
- 持久化：`hermes_state.py`、`gateway/session.py`

## 5. 常见改动场景：先看哪些文件

### 5.1 我想新增一个工具

先看：

1. `tools/registry.py`
2. `model_tools.py`
3. `toolsets.py`
4. 任意一个相近的 `tools/*.py`

通常需要动的地方：

- 新建 `tools/your_tool.py`
- 在 `model_tools.py` 的工具发现路径中导入它
- 在 `toolsets.py` 中把它挂到合适的 toolset

如果这个工具依赖 agent 内部状态，不一定能只走 registry；先对照 `run_agent.py` 里 `todo`、`memory`、`session_search`、`delegate_task`、`clarify` 的处理方式。

### 5.2 我想改一个工具为什么“看得见但不能用”

先看：

1. `toolsets.py`
2. `model_tools.py`
3. `tools/registry.py`
4. 目标工具文件里的 `check_requirements()`

优先排查：

- 该工具是否在当前 toolset 中
- 环境变量是否齐全
- schema 是否被动态裁剪
- 当前平台是否使用了不同的聚合 toolset

### 5.3 我想新增一个 slash command

先看：

1. `hermes_cli/commands.py`
2. `cli.py`
3. `gateway/run.py`

经验规律：

- 命令定义在 `hermes_cli/commands.py`
- CLI dispatch 在 `cli.py`
- Gateway 可用命令还要在 `gateway/run.py` 增加处理

如果只是给现有命令加 alias，通常只改 `hermes_cli/commands.py` 即可。

### 5.4 我想改 system prompt 或上下文文件装载

先看：

1. `run_agent.py`
2. `agent/prompt_builder.py`
3. `agent/context_compressor.py`

先问自己两个问题：

- 这部分内容是“稳定前缀”还是“临时 turn 注入”？
- 这个改动会不会破坏 prompt cache？

只要你对第二个问题没有把握，就不要轻易改 system prompt 构建策略。

### 5.5 我想改记忆系统

先看：

1. `agent/memory_manager.py`
2. `tools/memory_tool.py`
3. `run_agent.py`
4. `plugins/memory/`

要特别注意：

- 内建 memory 的写入和外部 provider 的同步桥接是两回事。
- memory prompt block、prefetch、turn 后 sync 分属不同阶段。

### 5.6 我想改 Gateway 多平台行为

先看：

1. `gateway/run.py`
2. `gateway/session.py`
3. `gateway/platforms/`

重点关注：

- session key 如何映射
- `AIAgent` cache 何时复用/失效
- 中断、审批、后台任务、投递路由是否受影响

### 5.7 我想改 session / 搜索 / 压缩

先看：

1. `hermes_state.py`
2. `run_agent.py`
3. `agent/context_compressor.py`

一定要记住：

- compression 之后会新建 session，并通过 `parent_session_id` 形成 lineage
- 这会影响 session search、session 列表、标题延续和历史恢复

## 6. 关键文件一行说明

这是一个适合搜索前先翻的速查表：

| 文件 | 一句话说明 |
| --- | --- |
| `run_agent.py` | `AIAgent` 运行时、工具循环、压缩、memory、持久化、fallback |
| `model_tools.py` | 工具发现、toolset 解析、schema 修补、sync/async 执行桥接 |
| `toolsets.py` | 平台/场景到工具集合的映射 |
| `tools/registry.py` | 工具注册、可用性检查、dispatch |
| `agent/prompt_builder.py` | system prompt 分层组装、技能索引、context files 装载 |
| `agent/context_compressor.py` | 长会话压缩与摘要策略 |
| `agent/memory_manager.py` | 内建 memory 与外部 memory provider 编排 |
| `hermes_state.py` | SQLite 会话库、FTS5、session lineage |
| `cli.py` | 交互式 CLI 外壳 |
| `hermes_cli/commands.py` | slash command 注册表 |
| `hermes_cli/main.py` | 主命令入口、profile override、子命令分发 |
| `gateway/run.py` | 多平台消息编排、agent cache、投递与审批 |
| `gateway/session.py` | 平台会话上下文与来源信息 |
| `hermes_cli/plugins.py` | 本地插件扫描、hook、CLI 扩展、工具注册 |
| `tools/mcp_tool.py` | MCP server 连接、工具发现、动态刷新 |
| `agent/skill_commands.py` | skill slash command 扫描与注入辅助 |

## 7. 最容易踩坑的设计约束

以下是这个仓库最不适合“直觉式简化”的地方：

### 7.1 不要轻易重建 system prompt

很多看似可以“每轮重新算一遍”的逻辑，实际上会破坏 prompt cache，尤其是在 Gateway 场景。

### 7.2 不要把所有工具都当成 registry 工具

`todo`、`memory`、`session_search`、`delegate_task`、`clarify` 明显依赖 agent 运行时状态，处理路径和普通工具不同。

### 7.3 不要硬编码 `~/.hermes`

这个项目支持 profiles。路径代码应该优先走 `get_hermes_home()`，用户可见路径优先走 `display_hermes_home()`。

### 7.4 不要忽略 compression 对 session 结构的影响

compression 不只是“消息变短了”，而是“会话关系变了”。

### 7.5 不要在 schema 里描述不存在的工具

`model_tools.py` 已经专门做了部分 schema 动态修补；如果你的描述里暗示模型可以调用一个当前不可用的工具，模型很容易真的去调用它。

## 8. 推荐的改动前检查清单

提交代码前，至少问自己下面几个问题：

- 我改动的是入口层、运行时、工具层还是持久化层？
- 这个改动会不会破坏 prompt cache？
- 这个改动会不会改变 session lineage 或 session id 语义？
- 这个能力是不是应该放在 plugin / MCP / skill，而不是直接塞进 core？
- 当前改动是不是同时影响 CLI 和 Gateway？

## 9. 一个简单的阅读策略

如果你不是做全面重构，而只是修一个 feature / bug，推荐用下面的策略：

1. 先找入口：这个问题是从 CLI、Gateway、tool call 还是 session 恢复进来的？
2. 再找中枢：它最后有没有进入 `run_agent.py`？
3. 再找注册点：这个能力是不是由 registry、toolset、plugin 或 MCP 暴露出来的？
4. 最后再看持久化：是否涉及 `hermes_state.py` 或 gateway session context？

这样读代码通常比“按目录从头翻到尾”更快。

## 10. 配套文档

建议和本文配合阅读：

- `docs/project-architecture.md`
- `AGENTS.md`
- `README.md`

如果你准备改某个专题，可以再补读：

- CLI / 皮肤 / 命令：`cli.py`、`hermes_cli/commands.py`、`hermes_cli/main.py`
- 工具 / toolset：`model_tools.py`、`tools/registry.py`、`toolsets.py`
- 会话 / memory / 压缩：`run_agent.py`、`hermes_state.py`、`agent/memory_manager.py`、`agent/context_compressor.py`
- 扩展：`hermes_cli/plugins.py`、`tools/mcp_tool.py`、`agent/skill_commands.py`

## 11. 总结

对新贡献者来说，这个项目最重要的不是一开始就看懂所有功能，而是先抓住三件事：

- 中枢在 `run_agent.py`
- 工具体系在 `model_tools.py`、`tools/registry.py`、`toolsets.py`
- 长期状态在 `hermes_state.py` 与 memory / compression 相关模块

只要先把这三条线建立起来，再去读具体功能，Hermes 的复杂度会明显下降。
