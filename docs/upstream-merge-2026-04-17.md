# 官方 upstream 合并摘要（2026-04-17）

Date: 2026-04-17

本文记录 2026-04-17 将官方 `NousResearch/hermes-agent` 的最新 `upstream/main`
再次合并进本私有仓库 `dev` 分支的结果，方便后续继续维护私有分支时快速判断：

- 这次官方主要更新了什么
- 哪些变化对本私有分支最重要
- 合并时哪些冲突需要保留本地决策
- 这次合并后已经做过哪些验证

## 1. 合并结果

- 私有分支：`dev`
- 官方基线：`upstream/main`
- 合并提交：`f9ecc39a`
- 已并入的 upstream 头提交：`764536b6`

本次不是一次小补丁，而是一轮跨度较大的上游吸收，`git rev-list --left-right --count dev...upstream/main`
在合并前显示私有 `dev` 相对官方 `main` 落后较多，因此这次合并覆盖了 CLI、Gateway、Tool Gateway、
Google/Gemini 生态、web dashboard、plugins、TTS、测试体系等多个面。

## 2. 这次 upstream 最值得关注的更新

按影响面从大到小看，核心变化大致可以归纳为 7 组。

### 2.1 Gemini / Google 生态明显增强

本轮引入了较大体量的新模块：

- `agent/gemini_cloudcode_adapter.py`
- `agent/google_code_assist.py`
- `agent/google_oauth.py`

结合上游提交记录，主要意味着：

- Hermes 新增了 Google Gemini CLI OAuth / Cloud Code Assist 路径
- Google OAuth 相关认证能力进一步内建
- 与 Gemini 相关的 provider 接入和测试覆盖显著增强

这对私有分支的意义是：

- 运行时 provider 选择空间更大
- 后续如果要做企业内 Google 生态接入，会比之前更顺手
- 认证链路更复杂，后续修改 provider 相关代码时要优先回归 `auth/models/setup/runtime_provider`

### 2.2 Gateway 的稳定性修复很多

这次 upstream 对 Gateway 层修改很重，重点文件包括：

- `gateway/run.py`
- `gateway/platforms/matrix.py`
- `gateway/platforms/telegram.py`
- `gateway/platforms/base.py`
- `gateway/stream_consumer.py`

从提交信息和 diff 看，重点集中在：

- 队列消息与 active session guard 的处理
- Matrix E2EE / migration 相关 bugfix
- read receipts、thread fallback、duplicate reply suppression
- 流式输出和最终消息发送之间的边界修复
- approval / progress / background command 等交互细节

对私有分支最重要的是：上游正在持续修补“流式输出、预览消息、最终消息、排队消息”这条复杂链路，
因此任何私有定制只要碰到 `gateway/run.py`，都必须重新看一遍 upstream 近期语义是否变了。

### 2.3 Tool Gateway 从“隐藏能力”更像走向正式能力

上游近期围绕 Tool Gateway 做了多轮更新，能看到这些方向：

- subscription-based access 的进一步固化
- per-tool opt-in 语义更清晰
- 文档、setup、status、tools_config 相关路径都在跟进
- managed browser / modal / media / TTS 等通道周边测试也一起增加

这意味着 Hermes 正在把 Tool Gateway 从“高级附加能力”逐步做成“标准可配置能力层”，
后续你如果继续维护私有发行版，Tool Gateway 的可见性、收费/权限判断、fallback 行为会是长期敏感区。

### 2.4 Web Dashboard / Plugins 能力继续扩张

这次新增或强化了：

- `plugins/example-dashboard/...`
- `hermes_cli/plugins.py`
- `web/src/plugins/*`
- `web/src/themes/*`
- `website/docs/user-guide/features/dashboard-plugins.md`

说明上游对 dashboard plugin 体系已经不只是概念验证，而是朝着可发现、可注册、可切换主题、可展示状态的方向推进。

对私有分支的价值：

- 如果后续你想做企业内部面板、定制状态页、定制插件入口，这部分可以直接复用 upstream 的结构
- web 端插件注册与主题上下文已经开始成型，后续不要轻易绕开现有 registry/context 机制

### 2.5 CLI / 配置 / 模型切换体验仍在快速演进

影响较大的文件包括：

- `cli.py`
- `hermes_cli/main.py`
- `hermes_cli/config.py`
- `hermes_cli/models.py`
- `hermes_cli/model_switch.py`
- `hermes_cli/status.py`
- `hermes_cli/setup.py`

可以归纳出几个趋势：

- `/model`、provider 解析、runtime provider 选择在持续补强
- 配置项与默认行为仍在收敛中
- CWD、状态展示、approval UI、deprecated 警告等 CLI 体验在打磨
- Ollama Cloud、Copilot ACP、Google/Gemini 等 provider 界面更完整

对私有分支来说，这类改动风险不在“功能会不会多”，而在“本地脚本、文档、用户习惯是否还匹配”。
每次合并 upstream 后，都应该重跑一轮真实 CLI 用例。

### 2.6 TTS、媒体与多模态能力继续补齐

本轮上游能看到：

- Gemini TTS provider 增加
- `tools/tts_tool.py`、`tests/tools/test_tts_gemini.py` 增强
- 多模态/vision 参数解析相关测试增加

这说明 Hermes 已经越来越像“多能力代理运行时”，不再只是一个文本 CLI 壳。
如果私有版本以后考虑对接语音入口或企业内语音播报，这部分会越来越重要。

### 2.7 测试覆盖面继续扩大

这次上游新增或强化了大量测试，涉及：

- gateway 竞争条件与重复发送
- run_agent client 复用与并发中断
- browser cloud fallback
- approval heartbeat
- tool backend helpers
- honcho plugin
- Ollama Cloud provider
- Gemini Cloud Code

这对私有分支是好事：以后很多 merge 冲突虽然烦，但更容易靠回归测试守住语义。

## 3. 本次合并时的关键冲突决策

这次真实冲突文件一共 4 个：

- `gateway/run.py`
- `tools/delegate_tool.py`
- `tests/run_agent/test_run_agent.py`
- `tests/tools/test_terminal_tool_requirements.py`

### 3.1 `gateway/run.py`

最终决策是“吸收 upstream 的结构性修复，同时保留本地已证明有意义的发送语义”。

实际落点：

- 保留 upstream 对 queued message / duplicate suppression / stream wait 的处理框架
- 最终保留 `response_previewed` 在非流式 preview 场景下可视为“已发送”的语义
- 没有改成“必须 `_sc.already_sent` 才算 preview delivered”的严格口径，因为这会打破现有测试语义

原因：

- `PreviewedResponseAgent` 这类路径本来就依赖 interim callback 直接发送最终文案
- 如果把 `response_previewed` 过度绑定到 stream consumer 状态，会错误地把“已经通过 adapter 发出”的文本当成未发出

### 3.2 `tools/delegate_tool.py`

最终保留了两边各自合理的部分：

- upstream 的 `wait(..., FIRST_COMPLETED)` 轮询模型
- 私有分支对 parseable / quiet 情况下 suppress batch progress 的行为

原因：

- upstream 修复的是“父代理中断后，等待子任务 forever”的真实阻塞问题
- 私有分支的输出抑制则是为了保证安静模式/可解析输出不被 batch progress 污染

### 3.3 `tests/run_agent/test_run_agent.py`

处理方式是两边新增测试都保留，不做删减。

保留范围包括：

- 私有分支新增的 runtime provider / explicit model / CLI main 相关测试
- upstream 新增的 memory provider cadence / memory context sanitization 相关测试

### 3.4 `tests/tools/test_terminal_tool_requirements.py`

最终保留了私有分支基于 registry active `check_fn.__globals__` 的 patch 思路，
但额外补了一层 `tool_backend_helpers.managed_nous_tools_enabled` 的 mock。

原因：

- 仅 patch 终端模块自身 globals，在 full suite / reload 场景下不一定覆盖到 helper 内部实际调用点
- 加一层 helper patch 后，才能稳定命中 managed Modal 的可用性判断

## 4. 合并后已经做过的验证

本次不是只解决冲突就结束，而是实际跑了多轮验证。

### 4.1 语法与导入级验证

已执行：

```bash
source venv/bin/activate
python3 -m py_compile gateway/run.py tools/delegate_tool.py tests/run_agent/test_run_agent.py tests/tools/test_terminal_tool_requirements.py
python3 -m py_compile gateway/run.py tests/tools/test_terminal_tool_requirements.py tests/tools/test_delegate.py
```

### 4.2 冲突高风险区域的回归测试

已执行并通过：

```bash
source venv/bin/activate
python3 -m pytest tests/run_agent/test_run_agent.py -q
python3 -m pytest tests/tools/test_terminal_tool_requirements.py tests/tools/test_delegate.py tests/gateway/test_duplicate_reply_suppression.py tests/gateway/test_run_progress_topics.py tests/gateway/test_voice_command.py -q
```

实际结果：

- `tests/run_agent/test_run_agent.py`：`267 passed`
- 上述聚合回归集：`283 passed`

### 4.3 更大范围全量测试

本次合并后还额外启动了：

```bash
source venv/bin/activate
python3 -m pytest tests/ -q
```

这个全量结果应和本文件写入时的终端输出一起查看；若你再次打开本仓库继续维护，建议优先看最近一次终端记录或补跑一次。

## 5. 对私有分支维护的直接影响

这次合并以后，私有分支的维护重点可以收敛到下面几条：

### 5.1 `gateway/run.py` 仍然是最敏感的私有改造点

因为它同时承载：

- streaming
- preview commentary
- final send suppression
- queued follow-up
- background review release
- interrupt / pending event

这类文件一旦跟 upstream 长期偏离，后续每次合并成本都会持续上升。

### 5.2 provider/auth/runtime 的耦合继续变强

Google/Gemini、Ollama Cloud、Copilot ACP、Tool Gateway、runtime provider 都在同一轮持续演进，
意味着后续如果私有版本要做“默认 provider 策略”或“企业内 provider 封装”，最好单独抽出回归清单。

### 5.3 web/dashboard/plugin 生态值得继续跟

这部分 upstream 现在还在快速生长，私有分支如果有运营面板、内部插件、企业主题系统需求，
尽量顺着已有 registry/theme/context 机制扩展，而不是另起一套。

## 6. 建议的后续动作

如果继续沿着这条私有分支长期维护，建议后续固定做 4 件事：

1. 每次 upstream 合并后，至少补跑一轮 CLI 真实用例
2. 把 `gateway/run.py` 的私有语义差异单独沉淀成回归测试
3. 对 provider/auth/runtime 切换路径维护一份专项验证清单
4. 对 dashboard/plugin/theme 体系建立最小 smoke test，避免上游继续演进时私有分支悄悄脱节

## 7. 一句话结论

这次 upstream 合并不是简单“同步一下官方代码”，而是把 Hermes 最近一轮围绕
Gateway 稳定性、Google/Gemini 接入、Tool Gateway 成熟化、web/dashboard/plugin 演进、
以及更完整测试覆盖的更新一起吸收进了私有分支；合并后私有 `dev` 已重新站到新的官方基线上，
后续维护成本会比继续长时间漂移更低。
