# Hermes Agent 图表资源

Date: 2026-04-16

这个目录用于存放项目文档里的可视化产物，以及对应的可维护源文件。

当前包含：

- `hermes-project-architecture.json`：架构图源数据
- `hermes-project-architecture.svg`：可直接在 GitHub / Markdown 中嵌入的矢量图
- `hermes-project-architecture.png`：方便在 IM、文档系统或截图场景中复用的位图版本
- `hermes-request-tool-sequence.json`：请求到工具执行时序图源数据
- `hermes-request-tool-sequence.svg`：请求时序图矢量版
- `hermes-request-tool-sequence.png`：请求时序图位图版
- `render_sequence_svg.py`：把 JSON 时序描述渲染为 SVG 的轻量脚本

## 1. 当前图表

### 1.1 项目总体架构图

文件：

- `docs/diagrams/hermes-project-architecture.svg`
- `docs/diagrams/hermes-project-architecture.png`

用途：

- 给 `docs/project-architecture.md` 提供一张总览图
- 帮助新维护者快速理解“入口 -> 壳层 -> AIAgent -> Prompt/Tooling -> 状态/后端”的关系

### 1.2 请求到工具执行的时序图

文件：

- `docs/diagrams/hermes-request-tool-sequence.svg`
- `docs/diagrams/hermes-request-tool-sequence.png`

用途：

- 给 `docs/project-architecture.md` 和 `docs/user-manual.md` 提供“入口请求 -> tool loop -> 持久化 -> 输出”的典型链路视图
- 帮助维护者在阅读 `run_agent.py`、`model_tools.py`、`tools/registry.py` 前先建立动态执行心智模型

## 2. 如何重新生成

图源使用 `fireworks-tech-graph` skill 的模板生成。当前仓库里保留了 JSON 源文件，后续需要调整图时，建议直接改 JSON 再重新导出。

生成 SVG：

```bash
python3 /Users/wangchao/.codex/skills/fireworks-tech-graph/scripts/generate-from-template.py \
  architecture \
  docs/diagrams/hermes-project-architecture.svg \
  "$(cat docs/diagrams/hermes-project-architecture.json)"
```

优先导出等比 PNG：

```bash
rsvg-convert -w 2000 docs/diagrams/hermes-project-architecture.svg \
  -o docs/diagrams/hermes-project-architecture.png
```

如果本机暂时没有 `rsvg-convert`，在 macOS 上也可以退回到 Quick Look 缩略图方案：

```bash
qlmanage -t -s 2000 -o docs/diagrams docs/diagrams/hermes-project-architecture.svg
mv docs/diagrams/hermes-project-architecture.svg.png docs/diagrams/hermes-project-architecture.png
```

时序图目前走仓库内脚本渲染，便于维护参与者、消息、激活块和注释：

```bash
python3 docs/diagrams/render_sequence_svg.py \
  docs/diagrams/hermes-request-tool-sequence.json \
  docs/diagrams/hermes-request-tool-sequence.svg

rsvg-convert -w 2000 docs/diagrams/hermes-request-tool-sequence.svg \
  -o docs/diagrams/hermes-request-tool-sequence.png
```

## 3. 维护约定

- 优先修改 `.json` 图源，不要直接手改生成后的 `.svg`
- 新增图表时，尽量同时提交 `json + svg + png`
- 如果新增图表被上层文档引用，记得同步更新 `docs/README.md`
- 如果图是时序图，优先维护 `render_sequence_svg.py + *.json` 这组可重复生成的输入
