# Hermes Agent 用户使用手册

Date: 2026-04-12

## 1. 文档目标

本文是一份面向最终用户与高级使用者的详细使用手册，重点回答下面这些实际问题：

- Hermes Agent 安装后第一步该做什么。
- 日常最常用的 `hermes` 命令有哪些。
- CLI、消息网关、MCP、技能、记忆、定时任务、Profile 应该怎么用。
- 配置文件、日志、会话库、记忆文件都放在哪里。
- 当模型不可用、网关起不来、会话太长、工具审批过多时，该怎么排查。

本文以 `hermes` 这个主入口为核心，尽量贴近真实使用场景来组织内容。

如果你还想理解项目内部结构，可以继续阅读：

- `docs/diagrams/hermes-project-architecture.svg`
- `docs/diagrams/hermes-request-tool-sequence.svg`
- `docs/project-architecture.md`
- `docs/contributor-reading-guide.md`
- `docs/architecture-comparison-hermes-codex-openclaw-claude-code.md`

### 1.1 适用对象

本文主要面向三类读者：

- 新用户：想先把 Hermes 跑起来，知道常用命令和配置放哪里
- 日常使用者：想把 CLI、会话、工具、日志、gateway、cron 用顺手
- 高级使用者：想进一步使用 skills、MCP、profiles、plugins、外部 memory

### 1.2 快速阅读路径

如果你不想一次性通读全文，可以按目标选择阅读顺序：

- 10 分钟快速上手：第 3、4、5、6、24 章
- 日常 CLI 使用：第 5、6、9、10、11、22 章
- 进阶自动化与扩展：第 12、13、15、16、17、19 章

### 1.3 按任务找章节

如果你是带着具体问题来的，先看这张“任务 -> 章节”索引会更快：

| 你现在要做什么 | 先看哪里 |
| --- | --- |
| 第一次安装、验证命令是否可用 | 第 3 章、第 24 章 |
| 想知道主命令、CLI 入口和最常用交互方式 | 第 5 章、第 6 章 |
| 想切模型、换 provider、配置 API key | 第 8 章、第 22 章 |
| 想打开/关闭工具、理解 toolset 和审批行为 | 第 9 章 |
| 想找会话历史、日志文件、排查运行异常 | 第 4 章、第 11 章、第 22 章 |
| 想安装和管理 skills | 第 12 章 |
| 想接插件、外部扩展或记忆 provider | 第 13 章、第 14 章 |
| 想把 Hermes 接到 Telegram / Slack / Discord 等平台 | 第 15 章 |
| 想配置定时任务 | 第 16 章 |
| 想接 MCP 工具生态 | 第 17 章 |
| 想接编辑器、ACP Server | 第 18 章 |
| 想做多实例隔离、不同身份/环境切换 | 第 19 章 |
| 想快速照着一套最小路径走通 | 第 24 章 |
| 想复现实测命令和 smoke 结果 | 第 26 章 |

如果你是从“先看图再看正文”进入这个手册，推荐顺序是：

1. `docs/diagrams/hermes-project-architecture.svg`
2. `docs/diagrams/hermes-request-tool-sequence.svg`
3. 回到本文第 3、5、9、11、15、17、19、24 章按需展开

---

## 2. 先用一句话认识 Hermes

Hermes Agent 是一个多入口的通用 Agent 运行时。你既可以：

- 在本地终端里用它，
- 也可以把它挂到 Telegram、Discord、Slack、WhatsApp、Signal 等消息平台，
- 还可以通过 MCP / ACP 让它和其他代理或编辑器协作。

对普通用户来说，最重要的入口通常是：

- `hermes`：主命令，进入交互式 CLI 或运行各种子命令
- `hermes-agent`：更底层的 agent 入口，偏编程/调试用途
- `hermes-acp`：作为 ACP server 供编辑器使用

绝大多数日常使用场景，都从 `hermes` 开始。

---

## 3. 安装与首次启动

### 3.1 快速安装

README 推荐的安装方式：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

安装完成后，重载 shell：

```bash
source ~/.bashrc
# 或
source ~/.zshrc
```

然后直接启动：

```bash
hermes
```

### 3.2 源码安装（适合开发者）

如果你是在仓库源码目录里直接使用 Hermes，推荐走可编辑安装：

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
python -m venv venv
source venv/bin/activate
python -m pip install -e .
```

这样做的好处是：

- 命令入口 `hermes`、`hermes-agent`、`hermes-acp` 会直接指向当前工作树
- 你修改源码后通常不需要重新安装
- 适合边开发、边测试、边跑 CLI

如果你准备跑测试，建议继续安装开发依赖：

```bash
python -m pip install -e .[dev]
```

### 3.3 安装后验证

安装完成后，建议至少做 3 个快速验证：

```bash
hermes --help
hermes chat --help
hermes chat --plain -q "请只回复 OK"
```

如果你还想验证 `--plain` 交互模式不会污染脚本输出，可以再跑一条：

```bash
printf '请只回复 OK\n/exit\n' | hermes chat --plain
```

预期结果：

- `hermes --help` 可以正常列出主命令
- `hermes chat --help` 可以正常列出 chat 子命令参数
- 两条 `--plain` 命令都应尽量只输出模型最终答案

### 3.4 Windows / WSL / Termux 提示

- Windows 原生环境不是主支持路径，推荐使用 WSL2。
- Android 侧推荐使用 Termux。
- Linux / macOS / WSL2 是最自然的使用环境。

### 3.5 首次配置建议顺序

第一次使用，建议按下面顺序完成初始化：

```bash
hermes setup
hermes model
hermes tools
hermes doctor
```

用途分别是：

- `hermes setup`：完整初始化向导
- `hermes model`：交互式选择默认模型与 provider
- `hermes tools`：配置哪些工具启用
- `hermes doctor`：检查依赖、配置和环境是否正常

### 3.6 第一次提问

交互式进入：

```bash
hermes
```

单次执行、拿到结果就退出：

```bash
hermes chat -q "帮我总结一下当前目录的项目结构"
```

带图片做单次提问：

```bash
hermes chat -q "描述这张图" --image ./example.png
```

---

## 4. Hermes Home：配置、日志和状态文件都在哪里

Hermes 的默认状态目录是：

```text
~/.hermes
```

如果启用了 profile，多实例目录通常是：

```text
~/.hermes/profiles/<name>
```

其中最重要的文件/目录如下：

| 路径 | 作用 |
| --- | --- |
| `~/.hermes/config.yaml` | 主配置文件 |
| `~/.hermes/.env` | API key 和其他敏感环境变量 |
| `~/.hermes/SOUL.md` | Agent 的 persona / 自我设定 |
| `~/.hermes/memories/MEMORY.md` | Agent 面向长期工作的通用记忆 |
| `~/.hermes/memories/USER.md` | 对用户偏好、背景信息等的长期记忆 |
| `~/.hermes/state.db` | SQLite 会话库，保存 session 与消息历史 |
| `~/.hermes/logs/agent.log` | 主日志 |
| `~/.hermes/logs/errors.log` | 仅错误/警告日志 |
| `~/.hermes/logs/gateway.log` | Gateway 运行日志 |
| `~/.hermes/skills/` | 已安装或本地技能 |
| `~/.hermes/cron/` | 定时任务相关状态 |
| `~/.hermes/profiles/` | 命名 profile 的目录 |

### 4.1 `config.yaml` 与 `.env` 的分工

建议把配置分成两类：

- `config.yaml`：行为、默认值、工具、显示、memory、gateway 等非敏感配置
- `.env`：API key、token、secret、URL 等敏感配置

常见思路是：

- “Hermes 怎么工作”放 `config.yaml`
- “Hermes 用什么凭据访问外部服务”放 `.env`

### 4.2 Profile 模式下的路径变化

当你使用：

```bash
hermes -p coder chat
```

或：

```bash
hermes profile use coder
```

之后，Hermes 会把当前实例的 `HERMES_HOME` 切到：

```text
~/.hermes/profiles/coder
```

也就是说：

- 这个 profile 拥有自己独立的 `config.yaml`
- 自己独立的 `.env`
- 自己独立的 `state.db`
- 自己独立的 skills、cron、logs、sessions、memories

这非常适合把“工作账号”“个人账号”“实验环境”“不同客户环境”彻底隔离开。

---

## 5. 最常用的 CLI 入口

### 5.1 进入交互式会话

```bash
hermes
```

这是最常见的用法。进入后你会得到一个带 slash command、自动补全和工具输出的交互式界面。

### 5.2 单次问题模式

```bash
hermes chat -q "给我写一个 bash 脚本，列出当前目录最大的 20 个文件"
```

这个模式适合：

- shell 脚本调用
- CI / 自动化流水线
- 你只想拿一段结果，不想进入交互 TUI

### 5.3 恢复旧会话

按 session ID 恢复：

```bash
hermes --resume <session_id>
```

按最近的 session name 继续：

```bash
hermes -c
```

按名称继续：

```bash
hermes -c "my project"
```

### 5.4 预加载技能、指定模型、指定工具集

```bash
hermes chat \
  -m anthropic/claude-sonnet-4 \
  -t web,file,browser \
  -s github-auth,repo-review
```

适用场景：

- 本轮任务只想开放特定工具
- 启动时就给 agent 附加特定技能
- 临时切换模型做一次高质量任务

### 5.5 Worktree 模式

```bash
hermes -w
```

或：

```bash
hermes chat --worktree
```

用途：

- 在同一个 Git 仓库中做并行 agent 工作
- 避免多个 agent / 终端互相覆盖工作树
- 更适合复杂编码任务或多分支试验

### 5.6 Quiet / Verbose / Checkpoints

静默模式：

```bash
hermes chat -q "输出 JSON" -Q
```

特点：

- 抑制 banner、spinner、工具预览
- 更适合脚本化调用

在当前版本里，`-Q` 更适合作为“程序接口”来用。实际 smoke 的推荐预期是：

- `stdout` 只包含最终答案正文
- 末尾追加一行 `session_id: ...`
- 不应混入 `[tool]`、`[done]`、spinner、reasoning 或 Rich box 边框

例如：

```bash
hermes chat -Q --source tool -q "请只回复 HELLO"
```

预期输出形态：

```text
HELLO

session_id: 20260412_xxxxxx_xxxxxx
```

开启文件系统 checkpoint：

```bash
hermes chat --checkpoints
```

作用：

- 在潜在破坏性文件修改前做检查点
- 后续可用 `/rollback` 恢复

限制本轮最大 agent 迭代：

```bash
hermes chat --max-turns 30
```

### 5.7 Plain 交互模式：适合脚本、SSH 和管道

如果你想要一个更适合脚本和远程终端的纯文本交互式会话，可以用：

```bash
hermes chat --plain
```

这个模式尤其适合：

- 通过 SSH、tmux、CI runner 或日志采集系统远程使用 Hermes
- 需要把 Hermes 输出继续喂给别的程序处理
- 希望交互式会话也尽量保持稳定、干净、可解析

这个模式会关闭 `prompt_toolkit` UI、spinner 和大部分交互装饰，也不会再显示那块大的 Hermes 启动 banner。助手回复也会尽量直接输出纯文本，不再包 Rich 响应框。

如果 `stdin/stdout` 不是 TTY（例如你通过管道、脚本或 CI 调用），`--plain` 还会进一步压缩输出，尽量减少启动提示、prompt、流式边框、工具 preparing/progress 状态行和退出摘要对结果文本的污染。

和 `-Q` 的区别是：

- `-Q`：更适合单次提问，抑制大部分装饰输出
- `--plain`：更适合持续交互，会把澄清、审批、sudo 等交互都切成纯文本风格

如果你希望长期默认启用 plain 模式，可以在 shell 配置里加入：

```bash
export HERMES_PLAIN_REPL=1
```

然后重新加载 shell：

```bash
source ~/.zshrc
# 或
source ~/.bashrc
```

需要脚本化驱动时，也可以直接通过标准输入喂给 Hermes：

```bash
printf '请只回复 OK\n/exit\n' | hermes chat --plain
```

---

## 6. CLI 内的 Slash Commands

进入交互式 CLI 后，最常见的控制方式是 slash command，也就是 `/xxx`。

> 注意：不是所有 slash command 都同时适用于 CLI 和消息网关。下面会注明适用范围。

### 6.1 会话类命令

| 命令 | 适用范围 | 作用 |
| --- | --- | --- |
| `/new` / `/reset` | CLI + Gateway | 新建会话 |
| `/clear` | CLI | 清屏并新建会话 |
| `/history` | CLI | 查看当前对话历史 |
| `/save` | CLI | 保存当前对话 |
| `/retry` | CLI + Gateway | 重试上一条消息 |
| `/undo` | CLI + Gateway | 撤销上一轮 user/assistant 交换 |
| `/title [name]` | CLI + Gateway | 给当前 session 起标题 |
| `/branch [name]` / `/fork [name]` | CLI + Gateway | 从当前 session 分叉一个新分支 |
| `/compress` | CLI + Gateway | 手动压缩上下文 |
| `/rollback [number]` | CLI + Gateway | 列出或恢复文件系统 checkpoint |
| `/stop` | CLI + Gateway | 停止后台进程 |
| `/background <prompt>` / `/bg <prompt>` | CLI + Gateway | 后台运行一个 prompt |
| `/btw <question>` | CLI + Gateway | 使用当前上下文问一个临时侧问题，不持久化 |
| `/queue <prompt>` / `/q <prompt>` | CLI + Gateway | 把 prompt 排到下一轮，不打断当前任务 |
| `/status` | CLI + Gateway | 查看当前 session 信息 |
| `/profile` | CLI + Gateway | 查看当前 profile 名称与 home 目录 |
| `/resume [name]` | CLI + Gateway | 恢复一个已命名会话 |
| `/sethome` | Gateway | 把当前聊天设置为 home channel |
| `/approve [session\|always]` | Gateway | 批准等待中的危险命令 |
| `/deny` | Gateway | 拒绝等待中的危险命令 |

### 6.2 配置类命令

| 命令 | 适用范围 | 作用 |
| --- | --- | --- |
| `/config` | CLI | 显示当前配置 |
| `/model [model] [--global]` | CLI + Gateway | 切换本 session 模型，或写入全局 |
| `/provider` | CLI + Gateway | 查看 provider 状态 |
| `/personality [name]` | CLI + Gateway | 设置人格/预设 persona |
| `/statusbar` / `/sb` | CLI | 切换状态栏 |
| `/verbose` | CLI | 切换工具进度显示级别 |
| `/yolo` | CLI + Gateway | 跳过危险命令审批 |
| `/reasoning [level\|show\|hide]` | CLI + Gateway | 调整推理强度与显示 |
| `/fast [normal\|fast\|status]` | CLI + Gateway | 切换 provider 的快速模式 |
| `/skin [name]` | CLI | 查看或切换界面皮肤 |
| `/voice [on\|off\|tts\|status]` | CLI + Gateway | 打开/关闭语音相关模式 |

### 6.3 工具与技能类命令

| 命令 | 适用范围 | 作用 |
| --- | --- | --- |
| `/tools [list\|disable\|enable] [name...]` | CLI | 管理工具启用状态 |
| `/toolsets` | CLI | 列出可用 toolset |
| `/skills` | CLI | 搜索、安装、检查和管理技能 |
| `/cron [subcommand]` | CLI | 管理定时任务 |
| `/reload-mcp` | CLI + Gateway | 重新加载 MCP server 配置 |
| `/browser [connect\|disconnect\|status]` | CLI | 连接到本地 Chrome CDP |
| `/plugins` | CLI | 查看插件状态 |

### 6.4 信息类命令

| 命令 | 适用范围 | 作用 |
| --- | --- | --- |
| `/commands [page]` | Gateway | 分页浏览所有命令和技能 |
| `/help` | CLI + Gateway | 显示帮助 |
| `/usage` | CLI + Gateway | 查看 token 用量和速率限制 |
| `/insights [days]` | CLI + Gateway | 查看用量分析 |
| `/platforms` / `/gateway` | CLI | 查看各消息平台状态 |
| `/paste` | CLI | 从剪贴板附加图片 |
| `/image <path>` | CLI | 为下一条消息附加本地图像 |
| `/update` | Gateway | 从聊天界面触发更新 |

### 6.5 退出类命令

| 命令 | 适用范围 | 作用 |
| --- | --- | --- |
| `/quit` / `/exit` / `/q` | CLI | 退出 CLI |

### 6.6 常用 slash command 组合

开始一个新任务：

```text
/new
/title repo cleanup
/model openrouter:openai/gpt-4.1
```

会话过长时：

```text
/usage
/compress
```

多任务并行时：

```text
/background 帮我整理一下这个模块的 TODO
/queue 等主任务结束后，顺便检查测试覆盖率
```

---

## 7. 顶层命令总览

除了进入交互式会话，`hermes` 还提供很多顶层子命令。

### 7.1 高频命令

| 命令 | 作用 |
| --- | --- |
| `hermes chat` | 启动交互式或单次 CLI 会话 |
| `hermes model` | 交互式选择默认模型 |
| `hermes setup` | 完整安装向导 |
| `hermes config` | 查看/编辑配置 |
| `hermes tools` | 配置不同平台启用的工具 |
| `hermes skills` | 安装、搜索和管理技能 |
| `hermes memory` | 配置外部记忆 provider |
| `hermes mcp` | 管理 MCP server |
| `hermes gateway` | 启动和管理消息网关 |
| `hermes cron` | 管理定时任务 |
| `hermes sessions` | 管理会话历史 |
| `hermes logs` | 查看日志 |
| `hermes doctor` | 环境诊断 |
| `hermes status` | 查看组件状态 |
| `hermes profile` | 管理 profile |
| `hermes update` | 更新 Hermes |
| `hermes uninstall` | 卸载 Hermes |

### 7.2 其他专用命令

还有一些更专用的入口，例如：

- `hermes login`
- `hermes logout`
- `hermes auth`
- `hermes plugins`
- `hermes pairing`
- `hermes webhook`
- `hermes claw`
- `hermes acp`
- `hermes completion`
- `hermes logs`
- `hermes dump`

这些命令通常是针对某一类进阶场景，例如网关授权、OpenClaw 迁移、插件安装、Shell 补全、编辑器集成等。

---

## 8. 模型、Provider 与认证

Hermes 的模型层分成三个问题：

1. 用哪个 provider
2. 默认模型是什么
3. provider 的凭据从哪里来

### 8.1 交互式选择默认模型

```bash
hermes model
```

这是最适合新用户的方式。它会帮助你：

- 选择 provider
- 选择默认模型
- 处理某些 provider 的登录流程

### 8.2 在命令行临时指定模型

```bash
hermes chat -m anthropic/claude-sonnet-4
```

或者在会话内：

```text
/model anthropic/claude-sonnet-4
```

### 8.3 登录型 provider

当前 `hermes login` 帮助里可以看到的 provider 有：

```bash
hermes login --provider nous
hermes login --provider openai-codex
```

如果你使用 OAuth / device flow 类型的 provider，这条命令最方便。

### 8.4 API key 型 provider

很多 provider 更常见的接入方式是把 key 放进 `~/.hermes/.env`，例如：

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- 以及项目内支持的其他 provider key

你也可以运行：

```bash
hermes config env-path
```

查看当前 `.env` 实际路径。

### 8.5 Provider 凭据池

Hermes 支持 pooled credentials：

```bash
hermes auth add <provider>
hermes auth list
hermes auth remove <provider> <token_or_index>
hermes auth reset <provider>
```

适用场景：

- 同一个 provider 有多组凭据
- 你希望在多个凭据之间切换或轮换
- 某些凭据被打满之后，需要 reset exhaustion 状态

### 8.6 `config.yaml` 中最常见的模型相关区域

从默认配置结构看，最重要的顶层段包括：

- `model`
- `providers`
- `fallback_providers`
- `smart_model_routing`
- `auxiliary`

这意味着 Hermes 不只支持一个固定模型，还支持：

- 默认模型
- provider 级配置
- fallback provider 链
- 辅助模型
- 智能模型路由

### 8.7 用 `config set` 快速改单项配置

```bash
hermes config set model anthropic/claude-sonnet-4
hermes config set terminal.backend docker
hermes config set logging.level DEBUG
```

`config set` 支持用点路径写嵌套字段，例如 `terminal.backend`。

---

## 9. 工具、Toolsets 与安全审批

Hermes 的一个核心能力，是让模型在会话中调用真实工具。

### 9.1 管理工具

查看工具状态：

```bash
hermes tools list
```

启用工具：

```bash
hermes tools enable web memory browser
```

禁用工具：

```bash
hermes tools disable browser
```

查看各平台启用概览：

```bash
hermes tools --summary
```

如果你直接运行：

```bash
hermes tools
```

会进入交互式配置界面。

### 9.2 常见 Toolsets

根据 `toolsets.py`，Hermes 内建了一批常见工具集。用户最常接触到的有：

| Toolset | 用途 |
| --- | --- |
| `web` | 搜索与网页提取 |
| `search` | 只做搜索，不做抽取 |
| `vision` | 图像理解 |
| `image_gen` | 图片生成 |
| `terminal` | 命令执行与进程管理 |
| `file` | 读写文件、patch、搜索 |
| `browser` | 浏览器自动化 |
| `skills` | 技能浏览/查看/管理 |
| `memory` | 持久记忆 |
| `session_search` | 搜索过往会话 |
| `clarify` | 追问、澄清 |
| `code_execution` | 执行 Python 脚本式工具调用 |
| `delegation` | 子代理委派 |
| `cronjob` | 定时任务管理 |
| `messaging` | 跨平台发送消息 |
| `tts` | 文本转语音 |
| `homeassistant` | 智能家居集成 |
| `debugging` | 终端 + 文件 + Web 的调试组合 |
| `safe` | 不含 terminal 的较安全组合 |

### 9.2.1 高频可选能力配置矩阵

很多用户会遇到一种情况：包已经装好了，但某些 toolset 还是没有出现，或者出现了也暂时不可用。Hermes 这里经常不是“缺 pip 包”，而是 **缺 provider 凭据、缺运行模式、或者还没完成 gateway 配置**。

下面这张表可以直接用来排查：

| 能力 | 需要满足什么条件 | 关键配置入口 | 常见误区 |
| --- | --- | --- | --- |
| `web` | 选择一个 backend，并至少满足其一：`EXA_API_KEY` / `PARALLEL_API_KEY` / `TAVILY_API_KEY` / `FIRECRAWL_API_KEY` / `FIRECRAWL_API_URL`；或使用 Nous 托管 Firecrawl | `hermes tools`；`config.yaml` 里的 `web.backend`；`.env` 里的对应 key | 只装了依赖但没配 backend/key，`web` 依然不会真正可用 |
| `image_gen` | 配置 `FAL_KEY`，或走 Nous 托管 FAL 队列 | `hermes tools`；`.env` 里的 `FAL_KEY` | 装了 `fal_client` 不等于图片生成已开通 |
| `messaging` | 完成 `hermes gateway setup`，至少配置一个平台 token，并启动 `hermes gateway start`；如果要按平台名直发，最好再设 home channel | `hermes gateway setup`；平台 token；`/sethome` | 这不是普通 CLI tool。`send_message` 在本地 CLI 下通常要求 gateway 正在运行 |
| `cronjob` | 在交互式 CLI、Gateway 会话，或带执行确认环境里运行 | `hermes cron ...`、CLI 会话、Gateway 会话 | 不是“任意非交互 shell 都自动开放”的 toolset，它有运行模式门槛 |
| `homeassistant` | 配置 `HASS_URL` 与 `HASS_TOKEN` | `hermes tools`；`.env` | 只有 URL 没有 token 时，HA 工具仍不可用 |
| `rl` | Python `>= 3.11`、`tinker-atropos` 代码/依赖可用、同时配置 `TINKER_API_KEY` 和 `WANDB_API_KEY` | `hermes tools`；`.env`；仓库子模块/依赖 | 这不是只装一个 extras 就能跑通的功能；训练链路还依赖外部服务 |

建议的排查顺序：

```bash
hermes tools --summary
hermes doctor
```

如果是消息平台与跨渠道发送，再额外检查：

```bash
hermes gateway status
hermes logs gateway -f
```

经验上可以先这样理解：

- 工具没显示：优先看 key / backend / 平台是否配置。
- 工具显示了但调用被拒：优先看是不是运行模式门槛，例如 Gateway 未启动、当前不是交互式会话、没有 home channel。
- 研究类功能优先先配 `web`；自动化通知优先先配 `gateway + messaging + cronjob`；重功能训练链路再考虑 `rl`。

### 9.3 在单轮会话里限制工具范围

```bash
hermes chat -t web,file
```

这很适合：

- 只允许检索和写文档
- 禁止 terminal/browsing 进入某些任务
- 做精细化权限控制

### 9.4 危险命令审批

Hermes 对高风险命令有审批机制。

典型体验是：

- 当模型准备执行高风险终端命令时，系统会要求确认
- 在 Gateway 中，可用 `/approve` 或 `/deny`
- 在 CLI 中，通常会出现本地交互确认流程

### 9.5 YOLO 模式

你可以显式跳过审批：

```bash
hermes --yolo
```

或在会话中：

```text
/yolo
```

建议：

- 仅在你完全信任当前任务与当前工作目录时使用
- 默认不要长期打开
- 在生产环境、重要仓库、系统目录里尤其要谨慎

### 9.6 命令 allowlist

Hermes 支持命令 allowlist。相关配置通常位于：

- `config.yaml` 中的 `approvals`
- `config.yaml` 中的 `command_allowlist`

适用场景：

- 某些只读命令你想默认放行
- 某些固定脚本你不想反复确认

### 9.7 文件系统 checkpoint 与回滚

如果你担心自动修改文件，可以在会话开始时打开：

```bash
hermes chat --checkpoints
```

然后在会话里：

```text
/rollback
```

就可以查看或恢复 checkpoint。

---

## 10. 配置管理：`hermes config`

### 10.1 查看配置

```bash
hermes config show
# 或直接
hermes config
```

### 10.2 编辑配置文件

```bash
hermes config edit
```

这会用你的 `$EDITOR` 打开配置文件。

### 10.3 查看配置文件路径

```bash
hermes config path
hermes config env-path
```

### 10.4 检查和迁移配置

```bash
hermes config check
hermes config migrate
```

适用场景：

- 升级版本后新增了配置项
- 老配置结构与当前版本不完全兼容
- 想确认有没有缺失值、过时字段或格式问题

### 10.5 默认配置里有哪些大类

从当前默认配置结构看，用户最值得知道的分组包括：

- `model`
- `toolsets`
- `agent`
- `terminal`
- `browser`
- `compression`
- `display`
- `privacy`
- `tts`
- `stt`
- `voice`
- `memory`
- `delegation`
- `skills`
- `honcho`
- `timezone`
- `approvals`
- `command_allowlist`
- `security`
- `cron`
- `logging`

你不需要一次性理解全部配置；更推荐按需求逐步改。

---

## 11. 会话、历史、日志与排障

### 11.1 会话管理

查看最近会话：

```bash
hermes sessions list
```

按来源筛选：

```bash
hermes sessions list --source cli
hermes sessions list --source telegram
```

限制条数：

```bash
hermes sessions list --limit 20
```

给会话改名：

```bash
hermes sessions rename <session_id> "Repo cleanup pass 2"
```

导出历史：

```bash
hermes sessions export ./sessions.jsonl
# 或导出单个会话到 stdout
hermes sessions export --session-id <session_id> -
```

删除或清理历史：

```bash
hermes sessions delete <session_id>
hermes sessions prune
```

交互式浏览：

```bash
hermes sessions browse
```

### 11.2 `state.db` 是什么

Hermes 使用 SQLite 的 `state.db` 来保存：

- session 元信息
- 全部消息历史
- message source（cli / telegram / discord 等）
- title
- token 计数
- 成本/计费信息
- lineage / parent_session_id

它不是一个“临时文件”，而是 Hermes 的正式历史数据库。

### 11.3 查看日志

主日志：

```bash
hermes logs
```

查看错误日志：

```bash
hermes logs errors
```

查看 Gateway 日志：

```bash
hermes logs gateway -n 100
```

实时跟随：

```bash
hermes logs -f
```

按级别过滤：

```bash
hermes logs --level WARNING
```

按 session 过滤：

```bash
hermes logs --session abc123
```

按时间过滤：

```bash
hermes logs --since 1h
```

### 11.4 环境自检

```bash
hermes doctor
```

自动尝试修复：

```bash
hermes doctor --fix
```

适合用在：

- 刚安装完
- 升级后不能启动
- 模型调不通
- `config.yaml` 怀疑有格式问题
- `SOUL.md` / `state.db` / 目录结构缺失

### 11.5 状态与统计

查看总体状态：

```bash
hermes status
```

查看更多细节：

```bash
hermes status --all
hermes status --deep
```

查看使用洞察：

```bash
hermes insights
```

---

## 12. Skills：把经验和流程变成可复用能力

Hermes 的技能系统可以理解为：

- 一段可复用的操作说明
- 一套结构化工作流
- 一个可以被 slash command 或启动参数加载的任务模板

### 12.1 浏览和搜索技能

```bash
hermes skills browse
hermes skills search memory
```

### 12.2 安装技能

```bash
hermes skills install openai/skills/skill-creator
```

也可以加：

```bash
hermes skills install <identifier> --yes
```

适合 TUI / 脚本环境。

### 12.3 检查与更新技能

```bash
hermes skills list
hermes skills check
hermes skills update
```

### 12.4 卸载技能

```bash
hermes skills uninstall <skill-name>
```

### 12.5 启动时预加载技能

```bash
hermes -s github-auth,repo-review
```

或：

```bash
hermes chat -s github-auth -s repo-review
```

### 12.6 在会话中使用技能

CLI 内常见入口：

```text
/skills
/<skill-name>
```

Hermes 会把某些技能直接暴露成 slash command，用起来会像“内建命令”。

### 12.7 技能适合做什么

非常适合沉淀下面这类经验：

- 固定的代码审查流程
- 某个 API 的接入步骤
- 某个团队约定的发布 SOP
- 某类研究/分析模板
- 某类迁移脚本的使用守则

---

## 13. 插件与外部扩展

技能更像“提示与工作流扩展”，插件更像“代码级扩展”。

### 13.1 安装插件

```bash
hermes plugins install anpicasso/hermes-plugin-chrome-profiles
```

也支持 Git URL。

### 13.2 查看、启用、禁用插件

```bash
hermes plugins list
hermes plugins enable <plugin>
hermes plugins disable <plugin>
```

### 13.3 更新或移除插件

```bash
hermes plugins update <plugin>
hermes plugins remove <plugin>
```

适用场景：

- 你需要仓库外部的新功能
- 想以插件形式扩展 provider、memory、工具或平台行为

---

## 14. Memory：内建记忆与外部记忆 Provider

### 14.1 内建记忆始终存在

Hermes 的 built-in memory 默认就有，两份核心文件是：

- `~/.hermes/memories/MEMORY.md`
- `~/.hermes/memories/USER.md`

你可以把它们理解为：

- `MEMORY.md`：Agent 对长期任务、偏好、项目背景的持续笔记
- `USER.md`：对用户本人的画像、习惯、长期需求的总结

### 14.2 `SOUL.md` 的定位

`SOUL.md` 不等同于 memory。

它更接近：

- persona
- identity
- 语气与价值取向
- 长期稳定的系统级自我描述

所以一个常见模式是：

- `SOUL.md`：定义“你是谁”
- `USER.md`：定义“用户是谁”
- `MEMORY.md`：定义“我们一起积累了什么”

### 14.3 外部记忆 Provider

Hermes 还支持外部 memory provider：

```bash
hermes memory setup
hermes memory status
hermes memory off
```

当前帮助信息中提到的 provider 包括：

- `honcho`
- `openviking`
- `mem0`
- `hindsight`
- `holographic`
- `retaindb`
- `byterover`

注意：

- 同一时间只能激活一个外部 provider
- 内建 memory 仍然始终存在

---

## 15. Messaging Gateway：让 Hermes 进入聊天平台

如果你不想一直守在终端里，可以启动 Gateway，让 Hermes 在消息平台上工作。

### 15.1 Gateway 的基本命令

```bash
hermes gateway run
hermes gateway start
hermes gateway stop
hermes gateway restart
hermes gateway status
hermes gateway install
hermes gateway uninstall
hermes gateway setup
```

含义通常是：

- `run`：前台运行
- `start`：作为服务启动
- `stop`：停止服务
- `restart`：重启服务
- `status`：看服务状态
- `install`：安装为系统服务
- `setup`：配置消息平台

### 15.2 常见平台

从 README 和仓库结构看，Hermes 覆盖了多个消息平台。最常见的包括：

- Telegram
- Discord
- Slack
- WhatsApp
- Signal

实际启用哪个平台，取决于：

- 你是否完成了该平台的 credential 配置
- 对应 gateway adapter 是否在当前环境里可运行
- 你的 `config.yaml` / `.env` 是否填写正确

### 15.3 Gateway 与 CLI 的关系

Gateway 不是另一套 agent，而是另一层入口。也就是说：

- 你在 CLI 里使用的很多 slash command，在 Gateway 里也能用
- session history 会进入同一套 `state.db`
- 不同平台会写不同的 `source` 标签

### 15.4 Home Channel

在 Gateway 里，你可以使用：

```text
/sethome
```

把当前聊天设置为这个 profile 的 home channel。

这适合：

- 定时任务回传
- 长期通知
- 统一汇报出口

### 15.5 Gateway 排障建议

先看状态：

```bash
hermes gateway status
```

再看日志：

```bash
hermes logs gateway -f
```

如果是首次部署失败，优先再跑一次：

```bash
hermes gateway setup
hermes doctor
```

### 15.6 OpenAI 兼容 API server 快速验证

如果你的 `~/.hermes/config.yaml` 和 `~/.hermes/.env` 已经配好模型 provider，最稳妥的验证方式是起一个隔离的 `HERMES_HOME`，这样不会影响你默认 profile 的运行状态。

示例：

```bash
mkdir -p /tmp/hermes-gw-e2e
cp ~/.hermes/config.yaml /tmp/hermes-gw-e2e/config.yaml
cp ~/.hermes/.env /tmp/hermes-gw-e2e/.env

source venv/bin/activate
export HERMES_HOME=/tmp/hermes-gw-e2e
export API_SERVER_ENABLED=true
export API_SERVER_HOST=127.0.0.1
export API_SERVER_PORT=8642
export API_SERVER_KEY=replace-with-local-test-key
export MESSAGING_CWD=$PWD

hermes gateway run
```

启动后，建议至少验证 3 条链路。

1）健康检查：

```bash
curl http://127.0.0.1:8642/health
```

预期会返回类似：

```json
{"status":"ok","platform":"hermes-agent"}
```

2）OpenAI 兼容聊天接口：

```bash
curl \
  -H "Authorization: Bearer replace-with-local-test-key" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8642/v1/chat/completions \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"请只回复 GATEWAY_OK"}]}'
```

如果模型配置正常，响应正文里应该能看到 `GATEWAY_OK`。

3）异步 run + SSE 事件流：

```bash
curl \
  -H "Authorization: Bearer replace-with-local-test-key" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8642/v1/runs \
  -d '{"input":"请读取 pyproject.toml，只回复 version=<版本号>","tools":["file"]}'
```

这个接口会先返回 `run_id`。拿到 `run_id` 后，可以继续订阅：

```bash
curl -N \
  -H "Authorization: Bearer replace-with-local-test-key" \
  http://127.0.0.1:8642/v1/runs/<run_id>/events
```

正常情况下你会看到 `tool.started`、`tool.completed`、`message.delta`、`run.completed` 等事件。验证结束后，前台 `hermes gateway run` 可直接 `Ctrl+C` 停掉。

---

## 16. Cron：定时自动化

Hermes 内建 cron 能力，可以把 prompt 变成周期性任务。

### 16.1 查看帮助命令

```bash
hermes cron list
hermes cron status
```

### 16.2 创建任务

```bash
hermes cron create "0 9 * * *" "每天早上 9 点总结昨天的 Git 提交"
```

也支持更自然的 schedule：

```bash
hermes cron create "30m" "每 30 分钟检查一次服务状态"
hermes cron create "every 2h" "每 2 小时汇总错误日志"
```

### 16.3 常用选项

```bash
hermes cron create "0 9 * * *" \
  --name morning-report \
  --deliver telegram \
  --skill report-writer \
  "每天上午 9 点发日报"
```

你还可以附带：

- `--deliver`：指定投递目标
- `--repeat`：重复次数
- `--skill`：附加一个或多个技能
- `--script`：把脚本 stdout 注入每轮 prompt

### 16.4 编辑与执行

```bash
hermes cron edit <job_id>
hermes cron pause <job_id>
hermes cron resume <job_id>
hermes cron run <job_id>
hermes cron remove <job_id>
```

### 16.5 适合做的自动化任务

- 日报 / 周报 / 巡检
- 夜间备份提醒
- 定期日志摘要
- 定时研究汇总
- 定时向某个平台推送结果

---

## 17. MCP：接入外部工具生态

MCP 是 Hermes 扩展工具能力的重要入口。

### 17.1 常见命令

```bash
hermes mcp list
hermes mcp add <name>
hermes mcp test <name>
hermes mcp configure <name>
hermes mcp remove <name>
hermes mcp serve
```

### 17.2 新增一个 MCP server

基于 URL：

```bash
hermes mcp add github --url https://example.com/sse
```

基于 stdio command：

```bash
hermes mcp add github --command npx --args @modelcontextprotocol/server-github
```

支持的认证参数包括：

- `--auth oauth`
- `--auth header`

### 17.2.1 基于仓库示例接入 FastMCP

这个仓库已经提供了一个最小 FastMCP 示例：

```text
examples/fastmcp/minimal_server.py
```

它暴露了 3 个简单工具：

- `ping`
- `list_docs`
- `preview_doc`

如果你想把它接入 Hermes，建议在 `~/.hermes/config.yaml` 中配置一个 stdio MCP server，并顺手把 FastMCP 的 banner / INFO 日志关掉：

```yaml
mcp_servers:
  fastmcp_demo:
    command: <repo-root>/venv/bin/fastmcp
    args:
      - run
      - --no-banner
      - --log-level
      - ERROR
      - <repo-root>/examples/fastmcp/minimal_server.py:mcp
    enabled: true
```

这样做的好处是：

- `hermes chat` 启动时不会先被 FastMCP banner 污染
- `--plain` 模式下输出更干净
- 只在 FastMCP 真出错时才更容易注意到异常

配置后可以先做 2 个快速检查：

```bash
source venv/bin/activate
hermes mcp list
hermes mcp test fastmcp_demo
```

如果要直接验证 Hermes 是否能调到这个 MCP，可以执行：

```bash
source venv/bin/activate
hermes chat -Q -t fastmcp_demo -q \
  "请调用 mcp_fastmcp_demo_ping 工具，参数 message=hello-from-hermes，并只返回 echoed 的值。"
```

预期应返回：

```text
hello-from-hermes
```

当前仓库已经额外做过一条更接近真实使用的 smoke：

```bash
source venv/bin/activate
hermes chat -Q -t fastmcp_demo -q \
  "只能使用可用的 MCP 工具。先列出 docs 下的 markdown 文档，再预览 docs/hermes-highlights.md，最后只输出两行：doc_count=<文档数>；preview=<预览首句或前一行要点，不加解释。>"
```

一次实测结果是：

```text
doc_count=9
preview=Hermes 的最大亮点，不是“工具很多”，而是它已经具备了一个成熟 `agent runtime` 的雏形：

session_id: 20260412_162127_ffe4d9
```

接入到 Hermes 后，常见的工具名形态会变成：

- `mcp_fastmcp_demo_ping`
- `mcp_fastmcp_demo_list_docs`
- `mcp_fastmcp_demo_preview_doc`

例如你可以让 Hermes：

- 调 `mcp_fastmcp_demo_list_docs` 列出仓库文档
- 调 `mcp_fastmcp_demo_preview_doc` 预览某个 `docs/*.md`
- 先用 `mcp_fastmcp_demo_ping` 做健康检查，再继续执行复杂任务

### 17.3 配置某个 MCP server 暴露哪些工具

```bash
hermes mcp configure github
```

这通常会进入一个交互配置流程。

### 17.4 重新加载 MCP

如果你已经修改配置并且想让当前会话重新感知：

```text
/reload-mcp
```

### 17.5 把 Hermes 自己暴露为 MCP server

```bash
hermes mcp serve
```

这适合把 Hermes 作为“被别的代理调用的后端”。

---

## 18. ACP：供编辑器接入

如果你想让 Hermes 被 VS Code、Zed、JetBrains 一类宿主通过 ACP 使用，可以运行：

```bash
hermes acp
```

这属于更偏集成场景的用法。仓库里已有专门说明：

- `docs/acp-setup.md`

如果你是普通终端用户，可以先不必关注 ACP。

---

## 19. Profiles：多实例隔离

Profile 是 Hermes 的一项非常重要的能力。一个 profile 就是一套完全独立的 Hermes 实例。

### 19.1 为什么要用 Profile

适合下面这些场景：

- 工作 / 个人环境隔离
- 不同客户或项目完全隔离
- 一个 profile 用稳定配置，一个 profile 用实验配置
- 不同消息平台绑定到不同人格/技能/模型组合

### 19.2 常用命令

```bash
hermes profile list
hermes profile create coder
hermes profile use coder
hermes profile show coder
hermes profile rename old new
hermes profile export coder
hermes profile import ./coder.tar.gz
hermes profile delete coder
```

### 19.3 创建 Profile

创建一个全新 profile：

```bash
hermes profile create coder
```

复制当前 active profile 的核心配置：

```bash
hermes profile create coder --clone
```

完整复制当前 profile：

```bash
hermes profile create coder --clone-all
```

从指定 profile 复制：

```bash
hermes profile create analyst --clone-from coder
```

### 19.4 使用 Profile

临时切换：

```bash
hermes -p coder chat
```

设置成 sticky default：

```bash
hermes profile use coder
```

### 19.5 Wrapper Alias

Profile 可以创建包装脚本，例如：

```text
~/.local/bin/coder
```

本质上执行的是：

```bash
hermes -p coder "$@"
```

也就是说，你以后可以直接：

```bash
coder chat
coder gateway status
```

### 19.6 导出与导入

导出：

```bash
hermes profile export coder
```

导入：

```bash
hermes profile import ./coder.tar.gz
```

这很适合：

- 备份 profile
- 跨机器迁移
- 给同事分发一套预配置环境

---

## 20. OpenClaw 迁移

如果你来自 OpenClaw，可以使用：

```bash
hermes claw migrate
```

预演迁移：

```bash
hermes claw migrate --dry-run
```

其他常见形式：

```bash
hermes claw migrate --preset user-data
hermes claw migrate --overwrite
```

Hermes 会尝试迁移：

- `SOUL.md`
- memory 文件
- skills
- allowlist
- 平台配置
- API keys
- 其他工作区定制

仓库内的迁移说明见：

- `docs/migration/openclaw.md`

---

## 21. 推荐工作流

### 21.1 本地编码工作流

```bash
hermes -w
```

进入后建议：

```text
/model <你常用的 coding model>
/tools enable file terminal browser memory
/title repo feature-x
```

推荐配套：

- 开启 worktree
- 视情况开启 `--checkpoints`
- 不要默认开 `/yolo`
- 大任务时用 `/background` 和 `/queue`

### 21.2 研究/资料整理工作流

启动：

```bash
hermes chat -t web,file,skills -s literature-review
```

会话中建议：

```text
/usage
/compress
```

适合：

- 桌面研究
- 网页抓取总结
- 生成 markdown 报告
- 长时间上下文研究任务

### 21.3 远程消息工作流

本地或服务器上启动：

```bash
hermes gateway setup
hermes gateway start
```

然后：

- 在 Telegram / Discord / Slack 等平台与 Hermes 对话
- 用 `/sethome` 设定汇报频道
- 用 `hermes cron create ... --deliver ...` 做定时通知

### 21.4 自动化工作流

```bash
hermes cron create "0 9 * * *" --deliver telegram "发送今日重点事项提醒"
```

推荐与下列能力组合：

- skills
- memory
- gateway
- logs
- profiles

---

## 22. 常见问题与排障建议

### 22.1 `hermes` 能启动，但模型调用失败

优先检查：

```bash
hermes model
hermes doctor
hermes config check
hermes logs errors
```

通常问题集中在：

- provider 没配置好
- `.env` 没有正确 key
- 默认模型字符串不对
- base URL / auth 失效

### 22.2 Gateway 起不来

先看：

```bash
hermes gateway status
hermes logs gateway -f
```

然后再检查：

```bash
hermes doctor
```

### 22.3 危险命令审批太频繁

可选做法：

- 调整 `approvals` / `command_allowlist`
- 在可控环境里临时用 `--yolo`
- 只给当前任务开放更少的 toolsets

### 22.4 会话太长、响应变慢、上下文过载

可以：

```text
/usage
/compress
```

也可以重新开一个分支：

```text
/branch cleanup-pass-2
```

### 22.5 想彻底隔离不同项目/身份

直接上 profile：

```bash
hermes profile create work
hermes profile create personal
hermes profile use work
```

### 22.6 想看 Hermes 当前到底在改哪里、存了什么

优先查看：

```bash
hermes config path
hermes config env-path
hermes profile show <name>
hermes logs
```

以及：

- `~/.hermes/state.db`
- `~/.hermes/memories/`
- `~/.hermes/logs/`

---

## 23. 维护与升级

### 23.1 查看版本

```bash
hermes version
```

### 23.2 升级

```bash
hermes update
```

### 23.3 卸载

```bash
hermes uninstall
```

### 23.4 Shell 补全

```bash
hermes completion bash
hermes completion zsh
```

这个命令会打印补全脚本，你可以把它接到自己的 shell 配置里。

### 23.5 查看日志文件列表

```bash
hermes logs list
```

---

## 24. 一个最小但完整的上手路线

如果你想在 10 分钟内把 Hermes 用起来，建议按这个顺序：

1. 安装 Hermes
2. 运行 `hermes setup`
3. 运行 `hermes model`
4. 运行 `hermes doctor`
5. 启动 `hermes`
6. 用 `/model`、`/title`、`/help` 熟悉当前会话
7. 用 `hermes sessions list`、`hermes logs` 熟悉状态与排障
8. 按需再接入 `skills`、`gateway`、`cron`、`mcp`、`profile`

如果你是重度用户，推荐第二阶段再引入：

- `profiles`
- `gateway`
- `cron`
- `mcp`
- `plugins`
- 外部 memory provider

---

## 25. 相关文档

仓库里和本文最相关的文档包括：

- `docs/project-architecture.md`：项目总体架构精读
- `docs/contributor-reading-guide.md`：新贡献者阅读路线
- `docs/hermes-highlights.md`：Hermes 的架构亮点
- `docs/hermes-roadmap.md`：后续演进路线图
- `docs/acp-setup.md`：ACP 接入说明
- `docs/migration/openclaw.md`：OpenClaw 迁移说明

如果你的目标是“会用”，优先看本文。

如果你的目标是“会改”，再继续读架构文档。

---

## 26. 2026-04-12 实测命令与结果

下面这些命令已经在当前仓库环境里真实跑过，可作为继续使用时的最小回归集。

### 26.1 Quiet + file + skills

命令：

```bash
source venv/bin/activate
hermes chat -Q --source tool --max-turns 8 \
  -s hermes-agent,codex,claude-code \
  -t file \
  -q "请读取 pyproject.toml 和 hermes_cli/commands.py，只回答三行：version=<pyproject中的版本>；command_defs=<COMMAND_REGISTRY中命令数量>；files=<你读取的两个文件名，逗号分隔，不要加任何解释。>"
```

实测结果：

```text
version=0.8.0
command_defs=47
files=pyproject.toml,hermes_cli/commands.py

session_id: 20260412_161722_0fa74c
```

说明：

- 这个用例验证了 `-Q`、skills 预加载、file 工具和 parseable stdout 能一起工作
- 当前预期是 stdout 只有结果正文和 `session_id`

### 26.2 Quiet + delegation + file

命令：

```bash
source venv/bin/activate
hermes chat -Q --source tool --max-turns 12 \
  -t delegation,file \
  -q "必须先调用 delegate_task，让一个子代理完成任务。子代理只能读取 pyproject.toml 与 docs/README.md，然后把结果返回给你。你最后只输出两行：version=<pyproject中的版本>；docs_readme_mentions=<docs/README.md 中出现 Hermes 的次数或近似统计整数>。不要解释。>"
```

实测结果：

```text
version=0.8.0
docs_readme_mentions=7

session_id: 20260412_162938_dde710
```

说明：

- 这个链路覆盖了 parent agent、`delegate_task`、child agent 和 file 工具
- 已额外修复一个回归：parseable quiet 模式下，child agent 不再泄漏 `[tool]` / spinner / reasoning 行

### 26.3 MCP server 连接

命令：

```bash
source venv/bin/activate
hermes mcp list
hermes mcp test fastmcp_demo
```

实测结果摘要：

- `fastmcp_demo` 当前已启用
- transport 为 `stdio`
- 成功连接
- 发现 3 个工具：`ping`、`list_docs`、`preview_doc`

### 26.4 Gateway 管理状态

命令：

```bash
source venv/bin/activate
hermes gateway status
```

当前结果：

```text
✗ Gateway is not running
```

这说明当前环境里 gateway 服务尚未启动；如果你要继续使用消息平台入口，可以继续执行：

```bash
hermes gateway
# 或
hermes gateway install
```

### 26.5 Gateway API server 端到端链路

这轮额外做过一次隔离 `HERMES_HOME` 的真实 API smoke：临时目录里复制已有 `config.yaml` 和 `.env`，再用 `API_SERVER_ENABLED=true` 启动 `hermes gateway run`，避免污染默认环境。

实测结果摘要：

- `GET /health` 返回 `200 OK`，body 为 `{"status": "ok", "platform": "hermes-agent"}`
- `POST /v1/chat/completions` 返回 `200 OK`，请求 `请只回复 GATEWAY_OK` 时实际返回了 `GATEWAY_OK`
- `POST /v1/runs` 返回 `202 Accepted`
- `GET /v1/runs/<run_id>/events` 返回 `200 OK`，事件流里出现 `tool.started`、`tool.completed`、`message.delta`、`reasoning.available`、`run.completed`
- 该 run 实际调用过 `read_file`，预览目标是 `pyproject.toml`，最终输出为 `version=0.8.0`

补充说明：

- 这个用例说明 Hermes 的 Gateway 不只是“能启动”，而是 OpenAI 兼容接口、异步任务接口和 SSE 事件流都已经跑通过
- 默认 profile 当前仍然是“gateway 未常驻启动”的状态；上面的 smoke 是隔离环境验证，不会改变你主环境的服务状态

### 26.6 构建与 wheel 安装验证

命令：

```bash
source venv/bin/activate
python -m build --wheel --sdist
```

实测结果摘要：

- 成功产出 `dist/hermes_agent-0.8.0-py3-none-any.whl`
- 成功产出 `dist/hermes_agent-0.8.0.tar.gz`
- wheel 已在临时虚拟环境里安装并验证 `hermes --help` 可运行
- 构建过程中有 `project.license` TOML table 的弃用告警，但不影响当前构建成功
