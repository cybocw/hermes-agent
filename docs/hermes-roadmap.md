# Hermes Agent 架构演进路线图

Date: 2026-04-11

## 1. 文档目的

本文回答的是一个非常具体的问题：

> 如果 Hermes 继续从“一个功能丰富的 agent 项目”演进成“一个成熟的 agent operating runtime”，下一阶段最合理的架构路线应该是什么？

这份路线图不追求“列出所有想做的功能”，而是聚焦：

- 哪些底层能力最值得优先建设
- 这些能力之间的依赖关系是什么
- 哪些当前长板必须保护，不能在演进中被破坏
- 哪些工作应该先做成架构对象，再做成产品功能

## 2. 北极星

Hermes 的下一阶段北极星，不是简单变成另一个 Codex、OpenClaw 或 Claude Code，而是：

> 在保留 `AIAgent`、`SessionDB`、prompt cache、`registry + toolsets` 这些长板的前提下，把 Hermes 演进成一个具备环境抽象、策略平面、类型化子代理和统一自动化框架的 agent runtime。

换句话说，Hermes 应该继续强化“运行时基础设施”定位，而不是把重心过早转成表层交互功能堆叠。

## 3. 当前状态简述

基于当前代码，Hermes 已经具备以下强项：

- `AIAgent` 作为统一运行时内核
- `SessionDB`、lineage、compression continuation
- prompt cache 稳定性工程
- `tools/registry.py` + `model_tools.py` + `toolsets.py` 的工具骨架
- CLI / Gateway / ACP 多入口复用
- profile-safe 的状态路径治理

但下一阶段要真正迈向“平台级 runtime”，还缺少几块关键拼图：

- instruction 层与 config 层还没有彻底分离
- 权限、审批、sandbox、tool policy 还没有统一策略平面
- environment 还不是一等对象
- subagent 还偏通用委派，而不是类型化基础设施
- 自动化能力还分散在多个模块，没有统一抽象

所以路线图的重点不是“再加更多工具”，而是补齐这几块结构性缺口。

## 4. 演进原则

在推进任何 roadmap 之前，先明确 6 条原则。

### 4.1 保住 prompt cache 稳定前缀

任何改动都不能轻易破坏下面这个事实：

- continuing session 尽量复用已有稳定前缀
- system prompt 不应频繁重建
- 临时上下文应尽量和稳定前缀分层

如果这个约束被破坏，Hermes 会直接失去一个非常有辨识度的工程优势。

### 4.2 保住 `SessionDB` 的结构化状态价值

不要把 session 系统退化成简单 transcript 存储。

必须继续保留并强化：

- lineage
- snapshot
- compression continuation
- searchable history

### 4.3 先抽象中枢，再做产品壳层

如果一项能力最终会被 CLI、Gateway、ACP 共同使用，就应该优先抽成 runtime object，而不是先在单个入口做 UI 化实现。

### 4.4 显式优于隐式

接下来所有重要治理能力，应该逐步从“散落在代码中的约束”变成：

- 有对象
- 有配置
- 有优先级
- 有可解释性

### 4.5 兼容已有多入口和 profile 体系

新能力必须天然支持：

- CLI
- Gateway
- ACP
- 多 profile

不要再引入只能在某一个入口成立的局部机制。

### 4.6 用阶段化改造替代一次性重构

Hermes 现在已经有较大代码体量，不适合“大重写”。路线图应该以增量抽象为主：

- 先引入统一对象
- 再让旧逻辑迁移到新对象
- 最后再提升产品层表达

## 5. 路线总览

我建议把 Hermes 的下一阶段演进拆成 5 个主阶段：

1. 打牢观测与约束基础
2. 拆开 instruction 层与 config / policy 层
3. 把 environment 提升成一等对象
4. 把 subagent 和 automation 做成第一公民
5. 让多入口逐步汇聚到更清晰的控制平面

这 5 个阶段不是绝对串行，但优先级上建议遵循这个顺序。

## 6. 阶段一：打牢观测与约束基础

### 6.1 目标

先把 Hermes 当前最值钱的几块长板“量化”和“可观测化”，避免后续改造把优势悄悄弄丢。

### 6.2 建议交付

- 增加 prompt cache 相关诊断信息
  - cache hit / miss 统计
  - miss 的高层原因分类
  - 哪些输入块导致前缀失稳
- 增加 session lineage 可视化或 inspection 命令
  - session parent
  - compression origin
  - snapshot source
- 梳理 agent-level tools 与 registry tools 的边界文档
- 梳理 CLI / Gateway / ACP 对 `AIAgent` 的共享契约

### 6.3 主要落点

- `run_agent.py`
- `agent/prompt_builder.py`
- `agent/context_compressor.py`
- `hermes_state.py`
- `cli.py`
- `gateway/run.py`

### 6.4 成功标准

- 可以回答“为什么这次 cache 没命中”
- 可以追踪“这个 session 是从哪次 compression 续出来的”
- 可以明确区分“runtime 核心逻辑”和“入口壳层逻辑”

### 6.5 为什么先做这个

因为没有观测，后面的 environment / policy / subagent 改造很容易破坏现有长板，而且团队不会第一时间发现。

## 7. 阶段二：拆开 instruction 层与 config / policy 层

### 7.1 目标

把“给模型看的规则”和“给系统看的策略”彻底分开。

当前 Hermes 已经有：

- `AGENTS.md`
- context files
- skills
- 各类 callback / toolset / platform 限制

但这些能力的边界还不够清晰。下一步应该显式形成两层：

1. instruction layer
2. config / policy layer

### 7.2 建议交付

- 定义统一配置对象，例如：
  - permissions
  - sandbox
  - approval mode
  - MCP scope
  - plugin policy
  - tool policy
- 明确作用域层级，例如：
  - global
  - profile
  - project
  - platform
  - subagent
- 把现有散落在 callback、toolset、platform 中的治理逻辑逐步迁移到统一 policy 解释层

### 7.3 主要落点

- `hermes_cli/config.py`
- `cli.py`
- `gateway/run.py`
- `model_tools.py`
- `toolsets.py`
- `tools/approval.py`
- `tools/terminal_tool.py`
- `tools/mcp_tool.py`

### 7.4 成功标准

- 可以用统一配置回答“这个平台为什么能/不能调用这个工具”
- 审批、sandbox、tool visibility 不再散落在多处 if/else 中
- instruction 文件与权限配置不再混成同一语义层

### 7.5 阶段收益

- 安全治理会更清晰
- 团队协作成本更低
- 后面做 subagent policy、managed settings、企业部署会顺很多

## 8. 阶段三：把 environment 提升成一等对象

### 8.1 目标

把“当前工作目录 + provider + 若干工具”这种隐式执行上下文，升级为明确的 `Environment` 抽象。

这是 Hermes 未来支持更强本地/远程/云端任务模型的关键前提。

### 8.2 建议交付

- 设计环境对象，至少包含：
  - working directory
  - execution backend
  - network policy
  - filesystem scope
  - setup script
  - maintenance script
  - cached environment metadata
- 把现有 terminal backends 和运行环境能力，统一映射到 environment interface
- 明确 shared environment 与 isolated environment 的区别
- 明确 CLI / Gateway / ACP 使用 environment 的方式

### 8.3 主要落点

- `tools/environments/`
- `tools/terminal_tool.py`
- `tools/code_execution_tool.py`
- `tools/process_registry.py`
- `run_agent.py`
- `gateway/run.py`

### 8.4 成功标准

- 对 agent 来说，“在哪运行”不再是隐式上下文，而是显式对象
- 后续接入远程、容器、云端执行时，不需要在每个工具里重复发明一套参数语义
- environment 可以被 subagent 和 automation 复用

### 8.5 阶段收益

- 为云端委派任务铺路
- 为重依赖项目提供更清晰的环境生命周期
- 让多入口在执行面上更一致

## 9. 阶段四：把 subagent 做成第一公民

### 9.1 目标

把当前的通用委派能力，升级为类型化、可治理、可观测的 subagent 基础设施。

### 9.2 建议交付

- 增加 typed subagent profiles，例如：
  - planner
  - explorer
  - worker
  - reviewer
- 为每类 subagent 提供：
  - model preset
  - tool preset
  - sandbox preset
  - token / iteration budget
  - result contract
- 引入 context isolation 策略
- 引入 parent / child session contract
- 增加 subagent 生命周期观测：
  - started
  - running
  - blocked
  - completed
  - failed

### 9.3 主要落点

- `tools/delegate_tool.py`
- `run_agent.py`
- `model_tools.py`
- `gateway/session.py`
- `hermes_state.py`

### 9.4 成功标准

- 子代理不再只是“另起一个 agent 去跑”
- 主上下文污染显著减少
- 并行探索与并行实现可以被平台层看见、管理和复盘

### 9.5 阶段收益

- 复杂任务拆分更稳定
- 本地和多平台工作流体验会明显提升
- 后续做 automation orchestration 会更顺手

## 10. 阶段五：统一自动化框架

### 10.1 目标

把现在分散在 `cron/`、background process、gateway watcher、memory review、skill review 等位置的后台行为，统一收束到一套 automation 模型中。

### 10.2 建议交付

- 定义统一 automation object，区分：
  - precise schedule
  - periodic heartbeat
  - event hook
  - standing instruction
- 定义统一的 automation execution record
- automation 与 session、environment、policy、subagent 建立明确关联
- 统一后台执行的通知、结果投递和失败恢复

### 10.3 主要落点

- `cron/`
- `tools/process_registry.py`
- `gateway/run.py`
- `gateway/session.py`
- `agent/skill_commands.py`
- `run_agent.py`

### 10.4 成功标准

- 后台能力不再是零散特性，而是同一套模型下的不同触发方式
- 平台之间可以共享 automation 语义
- automation 可以复用 environment、policy、subagent 这些前面阶段的基础设施

### 10.5 阶段收益

- 能力更容易理解
- 更容易做企业级治理
- 更容易把 Hermes 从“对话代理”扩展成“持续运行代理”

## 11. 阶段六：多入口汇聚到更清晰的控制平面

### 11.1 目标

不是把 Hermes 立刻改造成 OpenClaw 式的强 Gateway 中心系统，而是让 CLI、Gateway、ACP 逐步围绕更清晰的共享控制对象收敛。

### 11.2 建议交付

- 明确 session control API
- 明确 environment control API
- 明确 subagent orchestration API
- 明确 policy resolution API
- 让 CLI / Gateway / ACP 都优先复用这些共享控制对象

### 11.3 主要落点

- `run_agent.py`
- `cli.py`
- `gateway/run.py`
- `gateway/session.py`
- `acp_adapter/`

### 11.4 成功标准

- 新能力优先落到共享控制对象，而不是单入口特化逻辑
- CLI、Gateway、ACP 对 session / environment / approvals / subagent 的理解逐步一致
- Hermes 的“平台感”开始强于“单入口功能感”

### 11.5 重要说明

这一阶段不建议一开始就追求“大 Gateway 重构”。

更合理的方式是：

- 先统一控制对象
- 再考虑是否需要更强中心化控制平面

否则容易把系统复杂度一下子拉太高。

## 12. 推荐实施顺序

如果按优先级排序，我建议是：

1. 观测与约束基础
2. config / policy layer
3. environment object
4. typed subagents
5. automation framework
6. control-plane convergence

原因很简单：

- 没有观测，容易误伤现有优势
- 没有 policy layer，environment 和 subagent 很难治理
- 没有 environment，automation 和远程执行会缺少统一宿主
- 没有 typed subagent，复杂任务 orchestration 很难产品化
- 只有前面几层都出来了，多入口控制平面收敛才不会变成空中楼阁

## 13. 这条路线最需要避免的误区

### 13.1 不要先追求 UI 感，而忽略 runtime 对象

很多能力看起来很适合先做命令、按钮、面板，但如果底层对象没抽出来，后面只会越改越散。

### 13.2 不要为了加快功能上线，破坏 prompt cache 约束

Hermes 的一个核心优势就在这里，不能因为“更灵活的 prompt 拼装”而把优势换没了。

### 13.3 不要在每个入口里各自做 policy

如果 CLI 一套、Gateway 一套、ACP 一套，后面治理成本会非常高。

### 13.4 不要把 environment 做成 terminal tool 的私有概念

它应该是全系统对象，不只是命令执行时的参数包装。

### 13.5 不要把 subagent 只当性能优化手段

subagent 更重要的价值是：

- 角色分工
- 上下文隔离
- 权限隔离
- 结果契约化

## 14. 最终判断

Hermes 的下一阶段，不应该以“再变得更像某个竞品”为目标，而应该以“把已经萌芽的运行时优势做实”为目标。

如果路线正确，Hermes 会逐步长成这样一个系统：

- 上层是 CLI / Gateway / ACP / automation 等多入口
- 中层是 session、policy、environment、subagent、memory、tool orchestration 等共享控制对象
- 底层是 `AIAgent`、`SessionDB`、prompt cache、registry/toolsets 这些核心基础设施

到了那个阶段，Hermes 的定位就会更清楚：

> 不是一个功能很多的 agent 项目，而是一个真正有平台骨架的 agent runtime。

## 15. 参考文档

- `docs/project-architecture.md`
- `docs/contributor-reading-guide.md`
- `docs/hermes-highlights.md`
- `docs/architecture-comparison-hermes-codex-openclaw-claude-code.md`

## 16. 参考代码

- `run_agent.py`
- `model_tools.py`
- `toolsets.py`
- `tools/registry.py`
- `tools/approval.py`
- `tools/terminal_tool.py`
- `tools/code_execution_tool.py`
- `tools/process_registry.py`
- `tools/delegate_tool.py`
- `agent/prompt_builder.py`
- `agent/context_compressor.py`
- `hermes_state.py`
- `cli.py`
- `gateway/run.py`
- `gateway/session.py`
- `hermes_cli/config.py`
- `acp_adapter/`
