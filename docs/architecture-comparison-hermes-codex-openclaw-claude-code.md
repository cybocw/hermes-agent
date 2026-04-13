# Hermes Agent 与 Codex / OpenClaw / Claude Code 的架构设计深度对比

Date: 2026-04-11

## 1. 文档目的

本文不是做“功能清单式”的横向罗列，而是站在架构设计视角，对以下 4 套系统进行对比：

- `Hermes Agent`
- `Codex`
- `OpenClaw`
- `Claude Code`

重点回答 5 个问题：

1. 每套系统的“架构重心”到底在哪里。
2. 它们如何处理 prompt / instructions / memory / sessions。
3. 它们如何组织工具、MCP、skills、plugins、subagents。
4. 它们如何做安全治理、审批、沙箱和多入口统一。
5. Hermes 如果继续演进，最值得借鉴哪些设计。

本文中：

- Hermes 的判断主要基于本仓库代码精读。
- Codex、OpenClaw、Claude Code 的判断主要基于截至 **2026-04-11** 可获取的官方文档与公开资料。
- 对官方文档没有明确写出的部分，我会明确标注为“推断”。

## 2. 一句话结论

如果只用一句话概括 4 套系统：

- **Hermes**：一个以 `AIAgent` 为运行时核心、强调 prompt cache、会话持久化和工具注册统一性的多入口 Agent 框架。
- **Codex**：一个以“本地开发代理 + 云端任务代理 + 多界面统一体验”为中心的现代 coding agent 产品栈。
- **OpenClaw**：一个以 **Gateway 控制平面** 为中心、把消息渠道、设备节点、任务调度、技能、会话和权限策略统一编排的 agent 操作系统。
- **Claude Code**：一个以 **本地开发工作流** 为中心、将 `CLAUDE.md` / settings / hooks / MCP / subagents 组合成强配置体系的 coding agent 平台。

更直接一点说：

- Hermes 最像的是 **OpenClaw**，因为两者都不只是“终端编码助手”，而是试图做通用 agent runtime。
- Hermes 在“代码运行时组织”上更像框架；Codex 与 Claude Code 在“开发者工作流产品化”上更成熟。
- OpenClaw 在“控制平面、渠道接入、队列与策略治理”上明显最激进。

## 3. 对比基线：4 套系统各自的架构重心

### 3.1 Hermes：以 `AIAgent` 为中心的运行时内核

Hermes 的中心不是 CLI，也不是 Gateway，而是 `run_agent.py` 中的 `AIAgent`。CLI、Gateway、ACP 都是外壳；真正的系统能力在运行时层集中：

- system prompt 构建与缓存
- 工具循环
- memory / compression
- transcript / usage / trajectory 持久化
- provider / fallback / callbacks 编排

这意味着 Hermes 的基本设计思路是：

> 先把 session 级 agent runtime 做强，再让多个入口复用它。

这是一种比较典型的“runtime-first”架构。

### 3.2 Codex：以“统一 coding agent 产品栈” 为中心

从官方资料看，Codex 的重心不是单个 CLI 进程，而是一个跨多界面的统一产品体系：

- 本地 `Codex CLI`
- IDE extension
- Codex app
- Codex cloud / web task delegation

Codex 的关键架构特征是：

- 本地模式：在用户机器上读写代码、运行命令
- 云端模式：为每个任务创建独立 cloud environment / sandbox
- 多界面尽量对齐 instructions、skills 与任务工作方式
- 强调 parallel agents、worktrees、automations、cloud tasks

所以 Codex 不是“一个 CLI 工具”，而是一个 **local + cloud hybrid 的 agent stack**。

### 3.3 OpenClaw：以 Gateway 控制平面为中心

OpenClaw 的架构重心和 Hermes / Codex / Claude Code 都不同。它最核心的是 **Gateway**：

- 所有消息面归 Gateway 所有
- 所有 session state 归 Gateway 所有
- CLI / app / web / automations / nodes 都连到 Gateway
- 会话路由、队列、tool policy、sandbox、cron、heartbeat 都围绕 Gateway 展开

因此 OpenClaw 的核心思路是：

> 先有一个长期运行的控制平面，再把 agent、channels、nodes、automation 都挂在这条总线上。

它更像“agent 操作系统”或“agent control plane”，而不是单机 coding assistant。

### 3.4 Claude Code：以“开发工作流配置体系” 为中心

Claude Code 同样覆盖终端、IDE、桌面和浏览器，但它最鲜明的特点是 **配置层非常强**：

- `CLAUDE.md` 指令层
- hierarchical settings
- hooks
- MCP
- custom subagents
- permissions / managed settings

Claude Code 的核心组织方式是：

> 用一套强层级配置系统，把编码代理的行为、权限、扩展与团队治理表达清楚。

相比 Hermes 和 OpenClaw，它更少强调“长期运行的控制平面”，更多强调“同一个引擎如何在不同开发界面中保持一致行为”。

## 4. 核心差异一：系统边界与控制平面

### 4.1 Hermes：分布式外壳，共享一个运行时内核

Hermes 的控制结构大致如下：

```text
CLI / Gateway / ACP
        ↓
     AIAgent
        ↓
Prompt / Memory / Compression / Tools / SessionDB
```

特点：

- 控制权集中在 `AIAgent`
- 持久化由 `SessionDB` 和 gateway session context 分担
- Gateway 是重要入口，但不是绝对的 source of truth

这带来两个结果：

- 好处：代码复用强，runtime 逻辑清晰，CLI 和 Gateway 行为容易对齐
- 代价：当系统继续向“长期运行、多设备、多客户端控制平面”演进时，Gateway 的独立地位不如 OpenClaw 清晰

### 4.2 Codex：本地代理与云代理并行存在

Codex 的控制平面是“分层的”：

- 本地 CLI / IDE：本地读写和执行
- Cloud tasks：云端隔离环境执行
- App / Web：负责并行任务、审阅、调度与监督

官方资料没有像 OpenClaw 那样公开描述单一“Gateway”守护进程，因此基于公开资料，我更倾向于把 Codex 理解为：

- **体验层统一**
- **执行平面分裂**
  - local execution plane
  - cloud execution plane

这和 Hermes 最大不同在于：Hermes 更像一个统一运行时；而 Codex 从公开资料呈现出来的样子，更像一个 **统一产品体验下的多执行后端**。

### 4.3 OpenClaw：Gateway 是绝对 source of truth

OpenClaw 文档明确写了两件非常关键的事：

- Gateway 是长期运行的守护进程
- 所有 session state 归 Gateway 所有

这使它的控制平面比 Hermes 更“硬”：

- chat surfaces 统一归口
- 节点设备统一配对
- 会话队列统一管理
- session state / routing / approvals / cron / heartbeat 统一治理

从架构角度看，这是一种更强的 **server-centric / control-plane-centric** 设计。

### 4.4 Claude Code：没有 OpenClaw 式强控制平面，靠配置层统一

Claude Code 更像这样：

```text
Terminal / IDE / Desktop / Web
        ↓
   Claude Code engine
        ↓
CLAUDE.md + settings + MCP + hooks + subagents
```

它的“统一性”不是来自 Gateway，而是来自：

- 同一引擎
- 同一套 instructions
- 同一套 settings hierarchy
- 同一套 MCP / subagent / hooks 机制

所以：

- Hermes 偏 runtime-first
- Codex 偏 product-stack-first
- OpenClaw 偏 control-plane-first
- Claude Code 偏 config-system-first

## 5. 核心差异二：Instructions / Prompt / Memory 架构

### 5.1 Hermes：强调 prompt cache 稳定性与最小扰动

Hermes 在这块最鲜明的设计是：**system prompt 必须尽量稳定**。

它的实现思路是：

- system prompt 分层组装
- continuing session 优先复用缓存的 system prompt snapshot
- memory prefetch、plugin context 等尽量作为临时注入而非重建 system prompt
- context files 会做 prompt injection 扫描

这套设计非常“runtime engineering”：

- 不是简单地拼 prompt
- 而是在用工程方式维护缓存命中率和长会话成本

这点比另外三家都更显式。

### 5.2 Codex：AGENTS.md 指令链 + skills + rules，更像“项目契约层”

Codex 官方文档里最值得注意的点是：

- `AGENTS.md` 是一等机制
- 支持 global scope + project scope + nested override
- 从项目根一路走到当前目录
- 有大小上限和 fallback 文件名配置

这使 Codex 的 instructions 更像一种 **层级化项目契约**：

- 全局默认
- 仓库共享规范
- 子目录专属 override

它和 Hermes 的差异在于：

- Hermes 更强调“运行时如何安全、稳定地组 prompt”
- Codex 更强调“项目上下文与团队约束如何被结构化发现并加载”

### 5.3 OpenClaw：workspace bootstrap injection 更重、更广

OpenClaw 的 system prompt 设计更“重”：

- 每轮注入 `AGENTS.md`
- `SOUL.md`
- `TOOLS.md`
- `IDENTITY.md`
- `USER.md`
- `HEARTBEAT.md`
- `MEMORY.md`
- brand-new workspace 还会有 `BOOTSTRAP.md`

同时它还会注入技能列表、文档入口、runtime/sandbox 信息。

这说明 OpenClaw 的思路是：

> 让 agent 在每一轮都带着足够多的身份、工作区、自动化、人格和工具语义上下文启动。

优点：

- agent 更“像一个长期驻留角色”
- 任务切换和多渠道行为更一致

代价：

- prompt 体积更容易膨胀
- 需要更多 compaction / queue / routing 工程来对冲上下文成本

### 5.4 Claude Code：`CLAUDE.md` + hierarchical settings 的双轨制

Claude Code 把“行为指令”和“系统配置”分成了两条线：

- `CLAUDE.md`：偏自然语言规则、项目常识、工作流说明
- `settings.json`：偏权限、工具、插件、MCP、managed policy

并且 `CLAUDE.md` 还有多级作用域：

- managed
- project
- user
- local

这是一个非常成熟的设计点，因为它清楚地区分了：

- “给模型看的工作知识”
- “给系统看的控制配置”

相比之下：

- Hermes 这两类信息仍然在若干文件与 runtime 逻辑里分散表达
- OpenClaw 的 bootstrap 文件更丰富，但边界也更混合
- Codex 的 `AGENTS.md` 更偏 instructions，系统配置另走 config / approvals / rules

### 5.5 总结

这 4 套系统在 instruction/prompt 设计上的哲学差异很明显：

- **Hermes**：最强调 prompt cache 稳定性与运行时复用
- **Codex**：最强调项目级 instructions 的层级发现与团队协作
- **OpenClaw**：最强调 workspace persona / memory / automation 的全量 bootstrap
- **Claude Code**：最强调 instruction 层与 config 层的明确分离

## 6. 核心差异三：工具、Skills、Plugins、MCP 的组织方式

### 6.1 Hermes：registry + toolsets 是中枢

Hermes 的优势非常明确：

- `tools/registry.py` 是单一事实来源
- `model_tools.py` 负责发现、解析、schema 修补、sync/async bridge
- `toolsets.py` 负责不同平台、场景下的工具暴露
- 再叠加 plugin、MCP、skills

这是典型的 **runtime-managed tool surface**。

优点：

- 工具暴露面和 schema 一致性比较强
- 平台差异可以通过 toolset 表达
- 可以在 agent 级和 registry 级做双层路由

### 6.2 Codex：MCP / skills / subagents 更面向开发者工作流

Codex 的扩展面主要体现在：

- MCP server
- skills
- subagents
- app-level automations

从架构上看，Codex 没有把“通用插件平台”摆在最中心的位置，而是更关注：

- 如何把常见开发工作流抽象成 skill
- 如何让第三方工具通过 MCP 接进来
- 如何通过 subagents 分解复杂任务

这是一种更“产品化”的扩展体系：

- 扩展点更少，但用户心智更清晰
- 更偏 use-case 驱动，而不是框架驱动

### 6.3 OpenClaw：工具 / skills / plugins 三层结构最完整

OpenClaw 官方文档明确把三者区分开：

1. tools：typed function
2. skills：`SKILL.md`，教 agent 何时、如何使用工具
3. plugins：可打包 channel、provider、tools、skills、语音等

这和 Hermes 很像，但比 Hermes 更“产品化命名”：

- Hermes 也是 tools + skills + plugins + MCP
- OpenClaw 则把这些概念直接写成面向用户的主导航

并且 OpenClaw 的 plugin 能力范围更大，已经不仅是 tool 扩展，而是完整平台扩展。

### 6.4 Claude Code：MCP、hooks、subagents、plugins 的组合式扩展

Claude Code 的扩展模型比 Hermes 更模块化：

- MCP：外部工具和数据源
- hooks：生命周期自动化与策略拦截
- subagents：能力分工
- plugins：分发扩展能力
- skills：补充型流程知识

Claude Code 的一个明显优势是：

> 扩展点都挂在清晰的配置体系下。

这让团队协作、企业部署和局部覆盖更容易。

### 6.5 总结

如果看“内部实现优雅度”，Hermes 的 `registry + toolsets` 很强。

如果看“平台化程度”，OpenClaw 更强。

如果看“开发者易理解、易配置”，Claude Code 更清晰。

如果看“围绕 coding workflow 的扩展实用性”，Codex 当前更聚焦。

## 7. 核心差异四：安全、审批、沙箱、权限治理

### 7.1 Hermes：有安全机制，但缺少统一的策略平面

Hermes 当然不是没有安全控制：

- terminal tool 有危险命令检测
- clarify / approval callback 可由平台介入
- toolsets 决定可用工具范围
- 某些 agent-level tools 会被特殊拦截
- context files 有 prompt injection 扫描

但 Hermes 当前更像：

- runtime 内部有多处 guardrail
- 平台层也有一些 callback 和约束
- 但缺少像 OpenClaw / Claude Code 那样明确的 **policy hierarchy**

这意味着 Hermes 的安全更偏“实现内约束”，不是“策略系统”。

### 7.2 Codex：审批模式与 cloud internet policy 很成熟

Codex 在安全治理上的优点主要体现在两条线上：

1. **本地侧**
   - `Read-only`
   - `Auto`
   - `Full Access`
2. **云端侧**
   - agent phase 默认断网
   - setup phase 可以联网装依赖
   - 可按 environment 控制 internet access、域名和方法

这使 Codex 的安全模型很清晰：

- 对本地开发者：靠 approval modes + sandbox scope
- 对云端任务：靠 environment policy + network control

并且这种模型对工程团队很自然，因为：

- 本地任务和云任务本来就有不同风险边界

### 7.3 OpenClaw：四者里最强的策略治理体系

OpenClaw 的治理系统是四者中最完整的：

- tool policy
- sandbox
- elevated escape hatch
- exec approval
- gateway-level ACL
- sender / channel / agent / provider / subagent 多层限制

而且它明确规定：

- tool allow/deny 先于 sandbox
- sandbox 不会“复活”被 deny 的工具
- elevated 是显式逃生口
- approval 可以落到 UI，也可以转发到聊天渠道

这已经不是“开发助手安全”了，而是 **生产级 agent policy plane**。

### 7.4 Claude Code：最适合团队治理与企业落地

Claude Code 的安全设计非常像企业软件：

- `permissions.deny`
- managed settings
- server-managed / OS-managed policies
- project-scoped MCP 需要 approval
- hook / plugin / MCP 都有作用域和优先级

相比 OpenClaw：

- Claude Code 更偏“工作站和团队治理”
- OpenClaw 更偏“控制平面和多渠道操作治理”

相比 Hermes：

- Claude Code 的权限系统明显更结构化、更容易大规模部署

## 8. 核心差异五：Subagents / Orchestration 架构

### 8.1 Hermes：有子代理能力，但还偏“通用委派”

Hermes 已经有：

- `delegate_task`
- child agent
- iteration budget
- 并发工具和子任务保护

但从抽象层次看，它更像：

- 一个通用委派能力
- 而不是一套“类型化的 subagent 生态”

也就是说，Hermes 有 subagent capability，但不像 Codex / Claude Code / OpenClaw 那么“第一公民化”。

### 8.2 Codex：把 subagents 当成复杂任务的标准解法

Codex 官方文档对 subagents 的定位非常明确：

- 可并行
- 可自定义 agent
- orchestrator 负责收集结果
- 只在用户明确要求时才生成

这说明 Codex 把 subagents 当成：

> 解决高并行、长任务、复杂 feature planning 的标准架构机制。

### 8.3 OpenClaw：subagents 与 session / queue / sandbox / policy 深度耦合

OpenClaw 的 subagents 不是孤立能力，而是与以下机制联动：

- session isolation
- queue lanes
- tool policy
- sandbox policy
- delivery routing
- gateway announces

因此它的 subagent 更像“控制平面中的一种特殊 session 类型”。

这种设计很强，但复杂度也明显更高。

### 8.4 Claude Code：最强调“用 subagent 隔离上下文污染”

Claude Code 官方文档对 subagents 的价值说得很清楚：

- 保护主上下文
- 限制工具能力
- 路由到更便宜/更快模型
- 让不同子任务在独立窗口里工作

Claude Code 在这块的设计理念很先进：

> subagent 不只是并行执行器，还是上下文治理工具。

这点对 Hermes 很有借鉴意义。

## 9. 核心差异六：Session 与长期状态

### 9.1 Hermes：`SessionDB` 是强项

Hermes 在 session/state 上有一个明显长板：

- SQLite + WAL + FTS5
- session lineage
- system prompt snapshot
- compression continuation

特别是“压缩后新建 session 并保留 parent lineage”这一点，非常工程化。

这使 Hermes 在：

- 长会话
- 跨会话检索
- 历史可追踪性

方面的设计非常成熟。

### 9.2 OpenClaw：Gateway 持有会话真相，但持久化模型更偏操作系统风格

OpenClaw 的 session 由 Gateway 统一所有：

- store 文件
- JSONL transcript
- reset / cleanup / compaction

它的状态系统更像运行平台的状态管理，而不是 Hermes 这种“数据库型 agent memory substrate”。

### 9.3 Codex：公开资料更强调任务线程与环境，不强调可检索会话数据库

Codex 官方资料强调：

- thread / project / agent parallelism
- cloud task environments
- app / CLI / IDE 的跨界面任务连续性

但目前公开资料没有像 Hermes 那样公开一套很清晰的 session DB 设计。因此这里我的判断是：

- Codex 更重视 **任务线程 + diff + review flow**
- Hermes 更重视 **会话语义 + transcript store + searchable lineage**

这部分属于基于公开资料的合理推断。

### 9.4 Claude Code：更强调 instructions / config / MCP continuity，而非显式 session store

Claude Code 的公开文档里，长期上下文更多通过这些机制表达：

- `CLAUDE.md`
- auto memory
- settings
- subagents
- MCP

它没有像 Hermes 那样把“session 数据库”作为公开主概念强调，因此从公开文档的表达方式看，它更像：

- 强配置 continuity
- 较弱显式的 session / transcript store 心智

同样，这部分属于文档可见度上的推断，而不是内部实现断言。

## 10. 核心差异七：自动化与后台执行

### 10.1 Hermes：已经有 cron / background process，但抽象还不够统一

Hermes 有：

- `cron/`
- background terminal processes
- gateway watcher / notifications
- batch runner

但是这些能力在产品心智上没有像 OpenClaw 或 Codex 那样被收束成统一概念。

### 10.2 Codex：Automations 是 app-level 一等能力

Codex app 已经把 automations 提升为显式产品能力：

- 定时运行
- 结合 skills
- 后台执行
- review queue 回看结果

这比 Hermes 当前“有能力但没形成主心智”的状态更完整。

### 10.3 OpenClaw：Heartbeat + Cron + Standing Orders 是体系化设计

OpenClaw 的自动化是四者里最系统的：

- Heartbeat：周期性主会话唤醒
- Cron：精确时点任务
- Standing Orders：稳定长期指令
- Hooks：事件驱动

它已经把“后台 agent 行为”抽象成完整自动化框架，而不是零散功能。

### 10.4 Claude Code：更偏事件与 CI/CD 自动化

Claude Code 的自动化更偏：

- hooks
- non-interactive CLI
- CI/CD

它不是 OpenClaw 那种“常驻生活化代理”，而是“工程工作流自动化代理”。

## 11. 深度结论：Hermes 相比三者的真实位置

### 11.1 Hermes 更像谁？

从架构亲缘性看：

1. **最像 OpenClaw**
2. 其次是 **Claude Code**
3. 最不像的是 **Codex**

原因：

- Hermes 和 OpenClaw 都是“通用 agent runtime + 多入口 + 状态/工具/自动化”的大框架
- Hermes 和 Claude Code 都很重视本地工作流、instructions、MCP、subagents、hooks/skills 一类开发体验
- Codex 则更像统一产品栈，local/cloud 双执行面更强，工程产品化程度更高

### 11.2 Hermes 的优势

和这三者相比，Hermes 当前的明显优势有：

- `AIAgent` 中枢清晰
- `SessionDB` 设计很强
- prompt cache 稳定性意识很强
- `registry + toolsets` 的内核设计比较干净
- memory / compression / persistence 的工程意识很足

### 11.3 Hermes 的短板

和这三者相比，Hermes 当前较明显的短板是：

- 缺少像 OpenClaw 那样统一、显式的 policy plane
- 缺少像 Claude Code 那样清晰的 settings hierarchy / managed policy 体系
- 缺少像 Codex 那样成熟的 local/cloud 双执行面与 environment object
- 子代理仍偏通用委派，不够“类型化”和“工作流产品化”
- 自动化能力分散，尚未形成像 Heartbeat / Automations 那样的主心智

## 12. 对 Hermes 最有价值的演进建议

如果站在架构演进视角，我认为 Hermes 最值得吸收的不是“照搬功能”，而是吸收下面 6 个设计方向。

### 12.1 借鉴 Claude Code：把 instructions 层和 config 层彻底分开

建议方向：

- 保留 `AGENTS.md` / context files / skills 作为“给模型看的指令层”
- 单独建立更统一的“系统配置层”：
  - permissions
  - sandbox
  - MCP scope
  - plugin policy
  - managed settings

收益：

- 团队协作更清晰
- 安全策略更容易外部化
- runtime 逻辑更少混入策略判断

### 12.2 借鉴 Codex：把 environment 提升成一等对象

建议方向：

- 为 Hermes 增加明确的 environment 抽象，而不只是 provider / cwd / tools 的组合
- 支持：
  - setup script
  - maintenance script
  - cached env snapshot
  - network policy
  - shared / isolated env

收益：

- 更容易支持“云端委派任务”
- 更容易支持重型依赖项目
- 更容易把 ACP / CLI / Gateway 的执行环境统一起来

### 12.3 借鉴 OpenClaw：建立统一 policy plane

建议方向：

- 用统一配置表达：
  - global tool policy
  - per-platform policy
  - per-agent policy
  - per-provider policy
  - subagent policy
  - sandbox policy
  - elevated exec policy

收益：

- 让“哪些工具能被谁在什么场景调用”变成显式系统，而不是散落在 callback、toolset、platform 逻辑里

### 12.4 借鉴 Claude Code + Codex：把 subagent 做成第一公民

建议方向：

- 增加 typed subagent profiles
- 增加 per-subagent model/tool/sandbox presets
- 增加 context isolation 策略
- 增加可视化或结构化的 subagent result contract

收益：

- 复杂任务拆分更稳
- 主上下文更干净
- 并行探索 / 并行实现更可控

### 12.5 借鉴 OpenClaw：把自动化抽象成统一框架

建议方向：

- 把现有 `cron/`、background tasks、gateway watcher、memory review、skill review 统一到一个 automation 层
- 区分：
  - precise schedule
  - periodic heartbeat
  - event hooks
  - standing instructions

收益：

- 能力更好理解
- 平台间更容易复用
- 后台 agent 行为更可治理

### 12.6 保留 Hermes 自己的长板：继续强化 SessionDB + prompt cache

不要学坏的一点是：

- Hermes 当前对 prompt cache 稳定性和 session lineage 的重视，是它非常有辨识度的工程优势

建议继续加强：

- session snapshot / replay
- compaction lineage visualization
- session search / memory search 联动
- prompt cache 命中和失效诊断

这部分反而是 Codex / Claude Code / OpenClaw 公开资料里没有像 Hermes 这样清晰展开的。

## 13. 最终判断

如果把 4 套系统放在一张“架构地图”上：

- **Codex** 代表的是：面向现代工程团队的 local/cloud 一体化 coding agent 产品栈
- **OpenClaw** 代表的是：以 Gateway 为中心的 agent control plane / automation OS
- **Claude Code** 代表的是：以 instructions + settings + hooks + MCP 为核心的强配置 coding agent 平台
- **Hermes** 代表的是：以 `AIAgent` 运行时、统一工具注册、SQLite session substrate、prompt cache 工程为核心的通用 agent 框架

所以 Hermes 最合理的演进方向不是简单“变成另一个 Codex / Claude Code / OpenClaw”，而是：

> 继续保留 runtime 与 session 工程的优势，同时吸收 Codex 的 environment 抽象、OpenClaw 的 policy plane、Claude Code 的 config hierarchy。

如果这样演进，Hermes 会比现在更像一个真正成熟的 **agent operating runtime**，而不只是一个功能很多的 agent 项目。

## 14. 参考资料

### Hermes（本仓库）

- `run_agent.py`
- `model_tools.py`
- `toolsets.py`
- `tools/registry.py`
- `agent/prompt_builder.py`
- `agent/context_compressor.py`
- `agent/memory_manager.py`
- `hermes_state.py`
- `cli.py`
- `gateway/run.py`
- `gateway/session.py`
- `hermes_cli/plugins.py`
- `tools/mcp_tool.py`
- `docs/project-architecture.md`

### Codex（官方）

- Codex CLI: <https://developers.openai.com/codex/cli>
- Codex CLI features / approval modes: <https://developers.openai.com/codex/cli/features>
- Codex AGENTS.md: <https://developers.openai.com/codex/guides/agents-md>
- Codex subagents: <https://developers.openai.com/codex/subagents>
- Codex MCP: <https://developers.openai.com/codex/mcp>
- Codex cloud: <https://developers.openai.com/codex/cloud>
- Codex cloud environments: <https://developers.openai.com/codex/cloud/environments>
- Codex internet access: <https://developers.openai.com/codex/cloud/internet-access>
- Codex app announcement: <https://openai.com/index/introducing-the-codex-app/>

### OpenClaw（官方）

- Gateway architecture: <https://docs.openclaw.ai/concepts/architecture>
- Command queue: <https://docs.openclaw.ai/concepts/queue>
- Session management: <https://docs.openclaw.ai/concepts/session>
- System prompt: <https://docs.openclaw.ai/concepts/system-prompt>
- Tools and plugins: <https://docs.openclaw.ai/tools>
- Sandboxing: <https://docs.openclaw.ai/gateway/sandboxing>
- Exec approvals: <https://docs.openclaw.ai/tools/exec-approvals>

### Claude Code（官方）

- Overview: <https://code.claude.com/docs/en/overview>
- Settings: <https://code.claude.com/docs/en/settings>
- Memory / CLAUDE.md: <https://code.claude.com/docs/en/memory>
- Subagents: <https://code.claude.com/docs/en/sub-agents>
- Hooks: <https://code.claude.com/docs/en/hooks>
- MCP: <https://code.claude.com/docs/en/mcp>
