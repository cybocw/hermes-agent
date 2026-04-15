# Hermes Agent 文档导航

Date: 2026-04-12

这个 `docs/` 目录里已经不止有“零散说明”，而是逐步形成了 4 类文档：

- 新用户使用文档：告诉你怎么安装、配置、排障、日常使用
- 架构精读文档：解释系统为什么这样设计
- 贡献者导读文档：告诉你改功能时先看哪里
- 演进与对比文档：帮助做架构判断、路线评审与竞品分析

如果你第一次进入这个仓库，建议不要直接随机打开文件，而是按目标阅读。

## 1. 从哪个文档开始读

### 1.1 我只是想把 Hermes 用起来

优先读：

1. `README.md`
2. `docs/user-manual.md`
3. `docs/acp-setup.md`（如果你要接编辑器）

其中：

- `README.md` 适合先建立整体印象
- `docs/user-manual.md` 是最完整的用户侧操作说明
- `docs/user-manual.md` 里的“9.2.1 高频可选能力配置矩阵”适合排查为什么某些 toolset 还不能用

### 1.2 我想读懂项目架构

优先读：

1. `docs/diagrams/hermes-project-architecture.svg`
2. `docs/diagrams/hermes-request-tool-sequence.svg`
3. `docs/project-architecture.md`
4. `docs/hermes-highlights.md`
5. `docs/architecture-comparison-hermes-codex-openclaw-claude-code.md`
6. `docs/hermes-roadmap.md`

阅读目的分别是：

- `docs/diagrams/hermes-project-architecture.svg`：先用一张图建立入口、壳层、运行时、工具与状态底座的关系
- `docs/diagrams/hermes-request-tool-sequence.svg`：再看一条典型请求如何进入 AIAgent、触发 tool loop、落到持久化层
- `docs/project-architecture.md`：先建立系统全貌与调用链
- `docs/hermes-highlights.md`：看 Hermes 现阶段最值得保留的长板
- `docs/architecture-comparison-hermes-codex-openclaw-claude-code.md`：看 Hermes 和 Codex / OpenClaw / Claude Code 的设计差异
- `docs/hermes-roadmap.md`：看后续演进时哪些方向最值得优先补齐

### 1.3 我准备开始改代码

优先读：

1. `docs/contributor-reading-guide.md`
2. `docs/project-architecture.md`
3. 仓库根目录 `AGENTS.md`

建议顺序是：

- 先用 `docs/contributor-reading-guide.md` 建立“改某类功能时该去哪里看”的地图
- 再用 `docs/project-architecture.md` 理解运行时、工具、Gateway、状态层是怎么拼起来的
- 最后结合 `AGENTS.md` 和测试体系开始动手

## 2. 重点文档索引

| 文档 | 适合谁 | 重点内容 |
| --- | --- | --- |
| `docs/diagrams/hermes-project-architecture.svg` | 新维护者、架构评审 | 一张图看入口、壳层、AIAgent、中枢模块与状态/后端关系 |
| `docs/diagrams/hermes-request-tool-sequence.svg` | 新维护者、调试调用链的人 | 一条请求如何进入 `run_conversation()`、触发工具调用、写回会话与输出壳层 |
| `docs/user-manual.md` | 用户、运维、重度使用者 | 安装、CLI、Gateway、skills、MCP、cron、profiles、排障 |
| `docs/project-architecture.md` | 维护者、架构评审 | 分层结构、主调用链、工具中枢、状态底座、扩展机制 |
| `docs/contributor-reading-guide.md` | 新贡献者 | 按功能类型定位代码入口与阅读顺序 |
| `docs/hermes-highlights.md` | 架构评审、作者 | Hermes 当前最强的工程亮点与护城河 |
| `docs/architecture-comparison-hermes-codex-openclaw-claude-code.md` | 做横向架构对比的人 | Hermes 与 Codex / OpenClaw / Claude Code 的深度对比 |
| `docs/hermes-roadmap.md` | 维护者、规划者 | 未来架构演进方向与优先级 |
| `docs/acp-setup.md` | 编辑器集成用户 | ACP 接入与使用说明 |
| `docs/migration/` | 迁移用户 | 从旧方案或其他生态迁移 |
| `docs/skins/` | 想改 CLI 视觉风格的人 | 皮肤/主题相关说明 |
| `docs/plans/` | 开发者 | 历史设计/实施计划沉淀 |

## 3. 推荐阅读路径

### 路线 A：新用户

1. `README.md`
2. `docs/user-manual.md`
3. `hermes setup`
4. `hermes doctor`

### 路线 B：二次开发者

1. `docs/contributor-reading-guide.md`
2. `docs/diagrams/hermes-project-architecture.svg`
3. `docs/diagrams/hermes-request-tool-sequence.svg`
4. `docs/project-architecture.md`
5. `run_agent.py`
6. `model_tools.py`
7. `tools/registry.py`
8. `toolsets.py`

### 路线 C：做架构评审或产品对比

1. `docs/diagrams/hermes-project-architecture.svg`
2. `docs/diagrams/hermes-request-tool-sequence.svg`
3. `docs/project-architecture.md`
4. `docs/hermes-highlights.md`
5. `docs/architecture-comparison-hermes-codex-openclaw-claude-code.md`
6. `docs/hermes-roadmap.md`

## 4. 这份目录怎么维护

后续新增文档时，建议至少同步更新这里的两处：

- “重点文档索引”
- “推荐阅读路径”

这样 `docs/README.md` 就能持续充当这个目录的统一入口，而不是让新文档再次分散。

## 5. 已实测链路（2026-04-12）

这批文档不是只靠静态阅读整理出来的，下面这些链路已经在当前仓库里做过实际 smoke：

- Quiet 单次查询：`hermes chat -Q --source tool --max-turns 8 -s hermes-agent,codex,claude-code -t file -q '...'` 已验证 stdout 可保持 parseable，只输出答案正文和 `session_id`
- Delegation 子代理：`hermes chat -Q --source tool --max-turns 12 -t delegation,file -q '必须先调用 delegate_task ...'` 已验证 parseable quiet 模式下子代理不会再泄漏 spinner / `[tool]` / reasoning 行
- MCP 接入：`hermes mcp list` 与 `hermes mcp test fastmcp_demo` 已通过；`fastmcp_demo` 当前可连通并发现 3 个工具
- MCP 实际调用：`hermes chat -Q -t fastmcp_demo -q '只能使用可用的 MCP 工具 ...'` 已成功列出 `docs/` 文档并预览 `docs/hermes-highlights.md`
- 多工具组合：`terminal + file`、`delegation + terminal + file`、`fastmcp_demo + file` 三条真实查询都已返回预期结果，说明工具编排链路当前是通的
- Gateway 管理面：`hermes gateway --help` 与 `hermes gateway status` 已验证可用；默认环境当前显示“未启动”，但隔离 `HERMES_HOME` 的 API server 端到端 smoke 已通过
- Gateway API server：已实测 `/health`、`/v1/chat/completions`、`/v1/runs` + SSE 事件流；`/v1/chat/completions` 返回过 `GATEWAY_OK`，`/v1/runs` 事件流里出现过 `tool.started`、`tool.completed`、`reasoning.available`、`run.completed`
- 构建与安装：`python -m build --wheel --sdist` 已成功产出 wheel / sdist，且 wheel 已在临时虚拟环境中安装并验证 `hermes --help` 可运行

如果你要继续手动验证，最推荐的顺序是：

1. `hermes chat -Q -q "请只回复 HELLO"`
2. `hermes mcp test fastmcp_demo`
3. `hermes chat -Q -t fastmcp_demo -q "请列出 docs 下的 markdown 文件数量，只回复数字"`
4. `hermes gateway status`
5. 需要验证 OpenAI 兼容接口时，按 `docs/user-manual.md` 第 15.6 节启动隔离 gateway API smoke
