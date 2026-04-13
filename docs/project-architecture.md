# Hermes Agent 项目架构精读

Date: 2026-04-11

## 1. 文档目标

本文基于对仓库核心代码与现有文档的精读，整理 Hermes Agent 的项目架构、运行链路、核心抽象、扩展机制与关键设计约束，帮助新维护者快速回答以下问题：

- 这个项目到底由哪些子系统组成。
- 一条用户消息如何从入口流转到模型、工具和持久化层。
- CLI、Gateway、ACP、技能、插件、MCP、记忆系统之间是如何拼接起来的。
- 为什么某些实现看起来“绕”，但其实是在为 prompt cache、并发安全、多平台复用或低成本运行服务。

本文不覆盖所有功能细节，而是聚焦“结构、边界、调用链、扩展点”。

## 2. 项目定位

Hermes Agent 是一个多界面、多后端、多扩展面的通用 AI Agent 框架。它不是单纯的聊天壳，也不是单纯的工具调用器，而是把以下能力装配在同一个运行时里：

- 多入口交互：CLI、消息网关、ACP 编辑器接入。
- 多模型后端：OpenAI 兼容、Anthropic Messages、Codex Responses 等。
- 多工具体系：文件、终端、Web、Browser、TTS、Cron、代码执行、子代理委派等。
- 长期状态：SQLite 会话库、跨会话检索、记忆、用户画像、技能沉淀。
- 扩展能力：插件、MCP 服务、技能目录、外部记忆提供者、平台适配器。
- 运行环境抽象：本地、Docker、SSH、Modal、Daytona、Singularity 等。

从仓库结构看，它更像一个“Agent Runtime + Interface Shell + Extension Platform”的组合体。

## 3. 入口与运行形态

`pyproject.toml` 暴露了 3 个核心入口：

- `hermes = hermes_cli.main:main`
- `hermes-agent = run_agent:main`
- `hermes-acp = acp_adapter.entry:main`

这 3 个入口分别对应不同使用姿势：

| 入口 | 主要文件 | 作用 |
| --- | --- | --- |
| `hermes` | `hermes_cli/main.py` | 主命令入口，分发到 CLI、gateway、setup、doctor、cron 等子命令 |
| `hermes-agent` | `run_agent.py` | 直接运行核心 agent 循环，偏底层/调试/编程接口 |
| `hermes-acp` | `acp_adapter/` | 编辑器协议适配层，给 VS Code / Zed / JetBrains 一类宿主使用 |

在实际架构上，常见运行模式有 4 种：

1. 交互式 CLI：`hermes` -> `cli.py` -> `AIAgent`
2. Messaging Gateway：`hermes gateway` -> `gateway/run.py` -> `AIAgent`
3. ACP Server：`hermes-acp` -> ACP 适配层 -> `AIAgent`
4. 研究/批处理：`batch_runner.py`、`environments/` 等直接复用 agent 与工具体系

## 4. 总体分层

可以把 Hermes Agent 粗略拆成 6 层：

```text
Entrypoints
  hermes_cli/main.py | run_agent.py | acp_adapter/
        |
Interface Layer
  cli.py | gateway/run.py | acp_adapter/
        |
Agent Runtime Layer
  run_agent.py (AIAgent)
        |
Prompt / Memory / Compression / Routing
  agent/prompt_builder.py
  agent/memory_manager.py
  agent/context_compressor.py
  agent/model_metadata.py
        |
Tool & Extension Layer
  model_tools.py
  tools/registry.py
  toolsets.py
  tools/*.py
  tools/mcp_tool.py
  hermes_cli/plugins.py
  agent/skill_commands.py
        |
Persistence / Session / Infra
  hermes_state.py
  gateway/session.py
  hermes_constants.py
  cron/
  tools/process_registry.py
```

其中最重要的事实是：

- `run_agent.py` 是核心运行时。
- `model_tools.py + tools/registry.py + toolsets.py` 构成工具发现与调度中枢。
- `cli.py` 与 `gateway/run.py` 是两套上层外壳，但底层尽量复用相同 agent 能力。
- `hermes_state.py` 提供跨界面的统一会话存储与检索基础。

## 5. 核心调用链

### 5.1 CLI 链路

典型路径如下：

```text
hermes
  -> hermes_cli/main.py
  -> cli.py (HermesCLI)
  -> 创建/复用 AIAgent
  -> AIAgent.run_conversation()
  -> 模型响应 / 工具调用 / 会话持久化
  -> CLI 渲染输出
```

CLI 层负责：

- 读取 `config.yaml`、`.env`、皮肤、模型配置。
- 维护 REPL、slash command、状态栏、spinner、语音模式、历史记录。
- 将用户输入包装成一次 agent turn。
- 把 tool progress、thinking、reasoning 等事件映射到 TUI 展示。

### 5.2 Gateway 链路

典型路径如下：

```text
gateway message
  -> gateway/run.py (GatewayRunner)
  -> platform adapter
  -> gateway/session.py (SessionStore / SessionContext)
  -> 创建或复用 AIAgent
  -> AIAgent.run_conversation()
  -> DeliveryRouter 回发平台消息
```

Gateway 层额外解决的是：

- 多平台消息接入与回传。
- 会话映射、home channel、来源上下文注入。
- 每个 chat/session 的 agent 缓存与打断控制。
- 审批流程、后台任务、语音回复、计划任务投递。

### 5.3 关键设计点

虽然 Gateway 会为每条消息创建新的业务处理流程，但代码里专门维护了 session 级 `AIAgent` cache，原因是：

- system prompt 必须稳定，才能命中 prompt cache。
- 如果每轮都重新构造 agent 与 system prompt，会把 memory 的实时变更混入历史会话，导致前缀缓存失效、成本飙升。

这也是仓库里多处强调“不要轻易重建 system prompt”的核心背景。

## 6. AIAgent: 运行时核心

`run_agent.py` 中的 `AIAgent` 是整个项目的调度中心。它同时承担：

- 模型客户端选择与 API mode 适配。
- system prompt 构建与缓存。
- 多轮工具调用循环。
- 上下文压缩。
- 记忆预取与写回。
- 使用量、成本、轨迹、会话持久化。
- fallback model / provider 恢复。
- 子代理委派与 iteration budget 管理。

### 6.1 AIAgent 的主要输入

初始化时，`AIAgent` 会接收大量运行时参数，例如：

- 模型与 provider 信息。
- 启用/禁用的 toolsets。
- session id、platform、callbacks。
- prompt 相关选项：ephemeral prompt、prefill messages、reasoning config。
- 记忆、会话 DB、checkpoint、fallback、credential pool 等运行组件。

这说明 `AIAgent` 不是“只做模型调用”的轻对象，而是“一个 session 级 agent runtime”。

### 6.2 `run_conversation()` 主循环

`run_conversation()` 可以概括为以下阶段：

1. 恢复主 provider 运行时，清理上轮 fallback 状态。
2. 清洗用户输入，重置 turn 级计数器和预算。
3. 加载/恢复历史消息，并从历史中恢复 todo 状态。
4. 构建或复用缓存的 system prompt。
5. 必要时做预压缩，避免小上下文模型直接爆窗。
6. 预取插件上下文和外部 memory provider 上下文。
7. 进入 LLM -> tool calls -> tool results -> 再次 LLM 的循环。
8. 响应完成后同步 memory、持久化 transcript、usage、trajectory 等结果。

它不是简单的 while loop，而是一个包含大量保护逻辑的状态机：

- invalid JSON / invalid tool / empty content / scratchpad 不完整等重试。
- context overflow 时自动压缩。
- 用户中断时跳出或跳过后续工具。
- tool batch 安全时并发，否则顺序执行。
- 某些工具调用前自动做 checkpoint。

### 6.3 Agent 级工具拦截

虽然工具 schema 统一注册在 registry 中，但有几类工具不能直接走通用 dispatch，而要在 agent 层拦截，因为它们依赖 agent 内部状态：

- `todo`
- `memory`
- `session_search`
- `delegate_task`
- `clarify` 也需要平台 callback 配合

因此，工具体系是“两级路由”：

1. agent 级工具：由 `AIAgent` 直接处理。
2. 普通工具：交给 `model_tools.handle_function_call()` -> `tools.registry.dispatch()`。

### 6.4 并发工具执行

`AIAgent._execute_tool_calls()` 会根据 tool batch 是否“安全独立”决定是否并行执行：

- 读型工具更容易并发。
- 文件类工具只有路径不重叠时才适合并发。
- 有用户交互、副作用、顺序依赖时退回串行执行。

这类设计兼顾了两件事：

- 尽量缩短多工具轮次的 wall clock time。
- 避免两个写操作或两个相互依赖的工具竞争同一状态。

## 7. Prompt 架构

Prompt 体系分散在 `run_agent.py` 与 `agent/prompt_builder.py` 中，其中 `AIAgent._build_system_prompt()` 是总装配入口。

### 7.1 System Prompt 的组成

system prompt 不是一段固定模板，而是分层组装：

1. 身份层：优先使用 `SOUL.md`，否则退回默认 identity。
2. 工具行为层：memory、session search、skills 等工具启用时追加行为指导。
3. provider/model 行为层：例如 GPT/Codex、Gemini/Gemma 的执行纪律指导。
4. 用户/平台层：CLI 或 gateway 传入的 system message。
5. 持久记忆层：`MEMORY.md`、`USER.md`、外部 memory provider 的 prompt block。
6. 技能索引和上下文文件层。
7. 冻结的日期时间与平台格式提示。

### 7.2 Context Files 的装载优先级

`agent/prompt_builder.py` 中的 project context 文件是有优先级的，只会选第一类命中的来源：

1. `.hermes.md` / `HERMES.md`（向上走到 git root）
2. `AGENTS.md` / `agents.md`（当前目录）
3. `CLAUDE.md` / `claude.md`
4. `.cursorrules` / `.cursor/rules/*.mdc`

此外，`SOUL.md` 走的是独立通道，优先作为身份槽位注入。

### 7.3 Prompt Injection 防护

比较值得注意的是，context 文件装载前会经过扫描：

- 可疑 prompt injection 模式。
- 隐形 Unicode。
- 隐藏 HTML 注释或疑似 secret exfiltration 模式。

命中后不会“照单全收”，而是以 blocked 占位文本替代。这说明 Hermes 把本地 context file 也视为潜在攻击面，而不是绝对可信输入。

### 7.4 Prompt Cache 稳定性

仓库里反复强调一个原则：

- system prompt 必须尽量稳定。
- 插件临时上下文、prefill messages、memory prefetch 一类内容尽量在 API 调用时注入到 user turn，而不是重写 system prompt。

这是 Hermes 控制 token 成本的关键设计约束之一。

## 8. Memory 与上下文压缩

### 8.1 MemoryManager

`agent/memory_manager.py` 将记忆抽象成 provider：

- 内建 provider 永远存在。
- 最多允许 1 个外部 provider 并存。
- provider 可以提供 system prompt block、prefetch、sync、tool schema。

这个抽象的价值在于：

- 让“记忆”不再和单一实现耦合。
- 允许插件型记忆后端接入，同时避免多个外部 provider 同时注入导致 schema 膨胀和语义冲突。

### 8.2 Memory 的三个阶段

从调用链看，memory 主要出现在三个时点：

1. system prompt 构建期：注入稳定的持久记忆。
2. turn 开始前：prefetch 与当前 query 相关的背景记忆。
3. turn 完成后：同步本轮新信息到 memory provider。

这种拆分把“长期稳定知识”和“本轮临时召回上下文”分开了。

### 8.3 Context Compression

`agent/context_compressor.py` 是长会话生存能力的关键模块。其策略大致是：

1. 先裁剪旧 tool output。
2. 保护最前面的关键消息。
3. 按 token 预算保护最近的尾部消息。
4. 用辅助模型把中间大段 turn 总结成结构化摘要。
5. 多次压缩时迭代更新摘要，而不是重复从零总结。

### 8.4 压缩不是“原地改写”，而是“会话分裂”

`AIAgent._compress_context()` 里有一个非常重要的设计：

- 压缩后会生成新的 `session_id`。
- 新旧 session 通过 `parent_session_id` 串起来。
- system prompt snapshot 会同步到新的 session。

这意味着 Hermes 并不是简单把旧消息替换掉，而是把“被压缩后的继续会话”建成新 session，并维护 lineage。这对后续的 session search、标题继承、历史追踪都很重要。

## 9. 工具体系

工具体系由 3 个核心文件共同构成：

- `tools/registry.py`
- `model_tools.py`
- `toolsets.py`

### 9.1 `tools/registry.py`: 单一事实来源

每个 `tools/*.py` 文件在 import 时调用 `registry.register(...)` 注册：

- tool 名称
- 所属 toolset
- JSON schema
- handler
- 可用性检查函数
- 环境变量要求
- 是否异步

因此 registry 是工具元数据与 dispatch 的唯一事实来源。

### 9.2 `model_tools.py`: 发现、筛选、桥接

`model_tools.py` 当前更像“胶水层”，主要负责：

- import 所有内建工具模块，触发注册。
- 触发 MCP 工具发现。
- 触发 plugin 工具发现。
- 根据 enabled/disabled toolsets 解析本轮可用工具。
- 动态修补某些 schema 描述，避免模型看到不存在的跨工具引用。
- 统一 sync/async handler 的桥接执行。

特别值得注意的两个点：

- `execute_code` 的 schema 会根据本轮真实可用工具动态收缩。
- `browser_navigate` 的描述会在 Web 工具不可用时剥离相关提示，避免模型幻觉式调用缺失工具。

这说明 Hermes 很重视“暴露给模型的工具描述必须与真实运行态一致”。

### 9.3 `toolsets.py`: 工具分组与平台分发

`toolsets.py` 定义了：

- 叶子 toolset，如 `web`、`file`、`browser`、`memory`、`delegation`
- 场景 toolset，如 `debugging`、`safe`
- 平台聚合 toolset，如 `hermes-cli`、`hermes-telegram`、`hermes-gateway`

其中 `_HERMES_CORE_TOOLS` 是 CLI 与消息平台共享的核心工具集合。这样做的好处是：

- 新增/移除共享工具时，只改一处。
- 平台 toolset 可以在共享基线上再叠加各自差异。
- 插件 toolset 也能无缝并入 resolve 逻辑。

### 9.4 MCP 工具

`tools/mcp_tool.py` 是另一条重要扩展通道：

- 从配置加载 MCP server。
- 连接 stdio 或 HTTP transport。
- 把 MCP tools 注册到 Hermes registry。
- 处理 `notifications/tools/list_changed`，动态刷新工具列表。

这意味着 MCP 在 Hermes 里不是“旁路能力”，而是注册表内的一等工具来源。

### 9.5 插件工具

`hermes_cli/plugins.py` 允许从 3 个来源发现插件：

- `~/.hermes/plugins/`
- `./.hermes/plugins/`（显式 opt-in）
- `hermes_agent.plugins` entry points

插件可以：

- 注册工具。
- 注册 hook。
- 注入 CLI 子命令。
- 往当前对话注入消息。

因此插件系统和 MCP 系统都能扩展工具，但它们的边界不同：

- MCP 更偏“外部服务桥接”。
- plugin 更偏“本地运行时扩展”。

## 10. 状态持久化与会话系统

### 10.1 `hermes_state.py` / `SessionDB`

`SessionDB` 是统一的 SQLite 会话存储，能力包括：

- session 生命周期管理。
- messages 存储。
- system prompt snapshot 存储。
- usage / cost / reasoning 字段持久化。
- FTS5 全文检索。
- parent session lineage。

实现上还做了几件工程化处理：

- WAL 模式提升并发读写体验。
- 显式 `BEGIN IMMEDIATE` + 应用层随机退避，减轻多进程争锁时的 convoy 问题。
- 周期性被动 checkpoint，避免 WAL 无界膨胀。

### 10.2 Gateway Session Context

`gateway/session.py` 维护的是“消息来源上下文”，包括：

- 来源平台
- chat/user/thread 元信息
- home channels
- PII redaction 逻辑
- 当前 session 的动态上下文 prompt

也就是说：

- `SessionDB` 偏“持久化事实库”。
- `gateway/session.py` 偏“平台来源与路由上下文”。

两者服务不同维度，但最终都影响到 `AIAgent` 的行为。

## 11. CLI、Gateway、ACP 的边界

### 11.1 CLI

`cli.py` 是交互式终端壳，重点在：

- `prompt_toolkit` + Rich 的体验层。
- slash command 调度。
- tool progress 与 reasoning 展示。
- 多 session 交互、状态栏、皮肤、语音控制。

CLI 的特点是“本地即时交互体验最强”，因此包含大量 UI 逻辑，但底层 agent 与工具体系尽量不和 UI 强耦合。

### 11.2 Gateway

`gateway/run.py` 是一个多平台消息调度器，重点在：

- 平台 adapter 生命周期。
- session store、delivery router、pairing、hooks。
- 运行中 agent cache、后台任务、审批、语音、重连。

Gateway 的架构关键词不是“界面”，而是“路由和编排”。

### 11.3 ACP

虽然本文没有展开 ACP 代码细节，但从入口与 toolset 设计可以看出：

- ACP 复用同一个 agent runtime。
- 它更像“编辑器宿主适配层”。
- `hermes-acp` 的 toolset 明显偏代码与文件相关，少了 messaging/clarify 一类 UI 依赖工具。

## 12. 技能系统

技能相关能力分散在几个层面：

- 工具层：`tools/skills_tool.py`、`tools/skill_manager_tool.py`
- 命令层：`agent/skill_commands.py`
- prompt 层：`agent/prompt_builder.py` 会把技能索引信息加入 system prompt

技能系统本质上承担的是“程序化经验沉淀”角色：

- `SKILL.md` 是可复用流程说明书。
- CLI/Gateway 会把技能扫描为 slash command。
- 技能 invocation 本质上是把技能正文与运行时注释注入当前对话。
- 技能可以带 supporting files、config 变量、setup note。

因此它不是简单的 snippet 系统，而是“轻量工作流知识包”。

## 13. 配置、Profile 与路径约束

### 13.1 配置入口分散但有清晰边界

常见配置入口包括：

- `~/.hermes/config.yaml`
- `~/.hermes/.env`
- CLI fallback 配置
- gateway 配置映射

同时，`load_cli_config()`、`hermes_cli/config.py`、gateway 自己的配置装载路径并不完全相同。阅读和改动配置逻辑时，必须先判断自己处在哪个入口上下文里。

### 13.2 Profile 先于模块 import

`hermes_cli/main.py` 中 `_apply_profile_override()` 的位置非常关键：

- 它在多数 Hermes 模块 import 之前就设置 `HERMES_HOME`。
- 原因是很多模块会在 import 时缓存路径常量。

这属于典型的“启动时序决定架构正确性”的点，一旦改坏，profiles 就会整体失效。

### 13.3 路径必须走 `get_hermes_home()`

代码中专门抽出 `hermes_constants.py` 管理这些路径，是因为：

- profile 模式下 `~/.hermes` 不再是唯一根目录。
- 用户态显示路径与真实路径也可能不同。

因此：

- 代码路径用 `get_hermes_home()`。
- 用户可见提示用 `display_hermes_home()`。

## 14. 关键设计约束与维护注意事项

结合代码实现，以下约束最值得维护者牢记：

### 14.1 不要随意破坏 prompt cache 稳定性

不要在每轮都重建 system prompt，也不要把应当临时注入的内容改成持久 system prompt 内容。

### 14.2 Agent 级工具和普通工具不是一回事

`todo`、`memory`、`delegate_task`、`session_search` 这类工具依赖运行时状态，不能简单下放到通用 registry dispatch。

### 14.3 Tool schema 必须反映真实可用集

如果 schema 描述里提到一个当前 session 不可用的工具，模型就很容易 hallucinate 调用它。`model_tools.py` 已经在做这件事，新增工具时也要遵守这个原则。

### 14.4 压缩会改写 session 结构，不只是消息内容

context compression 会带来新 session 和 lineage 变化，因此任何与 session id、标题、历史恢复有关的逻辑都要考虑压缩后的续链场景。

### 14.5 Gateway 场景下 agent 生命周期和 CLI 不同

Gateway 是“消息驱动、多会话、多平台”，很多看似多余的 cache、锁、pending map，都是为了这个场景服务的，不应按 CLI 的直觉轻易简化。

## 15. 推荐阅读路径

如果是新贡献者，建议按以下顺序读代码：

1. `README.md`
2. `pyproject.toml`
3. `run_agent.py`
4. `model_tools.py`
5. `tools/registry.py`
6. `toolsets.py`
7. `agent/prompt_builder.py`
8. `agent/context_compressor.py`
9. `hermes_state.py`
10. `cli.py`
11. `gateway/run.py`
12. `gateway/session.py`
13. `hermes_cli/plugins.py`
14. `agent/memory_manager.py`

如果你的改动目标不同，可以按专题阅读：

- 工具开发：`tools/registry.py` -> `model_tools.py` -> `toolsets.py` -> 目标 `tools/*.py`
- 会话与记忆：`run_agent.py` -> `hermes_state.py` -> `agent/memory_manager.py` -> `gateway/session.py`
- CLI 命令：`hermes_cli/commands.py` -> `cli.py` -> `hermes_cli/main.py`
- 插件与扩展：`hermes_cli/plugins.py` -> `tools/mcp_tool.py` -> `agent/skill_commands.py`

## 16. 总结

Hermes Agent 的核心思想不是把所有能力堆进一个大文件，而是在一个统一 agent runtime 周围，构建：

- 多入口接口层
- 稳定的 prompt 与 session 机制
- 一致的工具注册与 toolset 解析机制
- 可扩展的插件、技能、MCP、记忆提供者体系
- 面向长会话与多平台场景的持久化和压缩策略

如果只看单个模块，Hermes 会显得“为什么这么多状态、这么多缓存、这么多钩子”。但从整体上看，这些设计基本都在解决同一类问题：

- 让 agent 在多轮、多平台、多工具、多扩展环境中还能保持稳定、低成本、可恢复、可演进。

