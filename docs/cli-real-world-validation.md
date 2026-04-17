# Hermes CLI 真实用例验证记录

Date: 2026-04-17

## 1. 文档目标

这份文档记录 2026-04-17 在当前仓库上的一轮真实 CLI 用例验证，目标不是覆盖所有功能，而是回答下面 3 个更贴近日常开发的问题：

- 现在这个仓库里的 `hermes` 命令实际还能不能跑。
- 哪些高频开发向链路已经验证通过。
- 哪些行为已经暴露出真实问题，后续应优先修什么。

本文只记录已经实际执行过的命令与观察到的结果，不做“应该可以”“按理没问题”式推断。

## 2. 验证环境

- 仓库路径：`/Users/wangchao/workspace/hermes-agent`
- 分支：`dev`
- 提交：`bc52267d`
- 时间：`2026-04-17 01:24:44 CST`
- 运行前工作树：仅有未跟踪的 `.omx/`

说明：

- 这轮验证期间临时使用过 `.smoke-cli/` 作为隔离目录，结束后已删除
- 文中出现的 session id 来自真实运行结果，可用于后续 `hermes --resume`

## 3. 已验证通过的真实链路

### 3.1 Quiet 单次查询

命令：

```bash
source venv/bin/activate
./hermes chat -Q --source tool --max-turns 4 -q '请只回复 HERMES_SMOKE_OK'
```

结果：

```text
HERMES_SMOKE_OK
```

结论：

- 基础单次问答链路可用
- `-Q` 模式至少在这个最小场景下可返回可解析正文

### 3.2 Quiet + file 工具

命令：

```bash
source venv/bin/activate
./hermes chat -Q --source tool --max-turns 8 -t file \
  -q '请只使用 file 工具，统计 docs 目录下一级 markdown 文件数量，只回复数字'
```

结果：

```text
10
```

结论：

- `-Q` 与 `file` 工具能协同工作
- 模型在约束“只使用 file 工具”时可完成真实读取任务

### 3.3 `--plain` 交互模式

命令：

```bash
source venv/bin/activate
printf '请只回复 PLAIN_OK\n/exit\n' | ./hermes chat --plain
```

结果：

```text
PLAIN_OK
```

结论：

- `--plain` 模式可以用于脚本/管道类交互
- 最小问答场景下没有出现 banner、spinner 之类的额外污染

### 3.4 文件写读

结果摘要：

- 已做过一次“让 Hermes 创建/修改临时文件，再读回确认”的真实 smoke
- 文件写入与后续读取都返回了预期结果

结论：

- `file` 工具的写入链路在当前环境可用

### 3.5 代码库问答

结果摘要：

- 已做过一次面向当前仓库代码与文档的真实问答
- Hermes 能在真实仓库上下文中回答代码库相关问题

结论：

- 当前 CLI 不是只能做固定字符串返回，代码库读取与回答链路可用

### 3.6 `--resume`

结果摘要：

- 已做过一次 `--resume` 真实恢复会话测试
- 会话恢复本身成功
- 可用 session id：`20260417_002735_2081db`

结论：

- 会话恢复链路是通的

补充观察：

- `-Q` 模式下恢复会话时会额外打印 resumed 相关行，因此不完全适合作严格 parseable 输出场景

### 3.7 `--worktree`

结果摘要：

- worktree 的创建与清理动作本身成功
- 但随后在 `terminal` 工具里执行 `pwd`，返回的是主仓库路径，而不是 `.worktrees/...`

结论：

- `--worktree` 的资源生命周期基本可用
- 但“实际命令执行 cwd 是否真的切入 worktree”目前存在明显可疑点

### 3.8 `--checkpoints` + `/rollback`

命令：

```bash
mkdir -p .smoke-cli
printf 'version-1\n' > .smoke-cli/checkpoint_demo.txt

source venv/bin/activate
printf '请只使用 file 工具把 .smoke-cli/checkpoint_demo.txt 的内容改成 version-2，并且只回复 CHANGED\n/rollback 1 .smoke-cli/checkpoint_demo.txt\n/exit\n' \
  | ./hermes chat --plain --checkpoints -t file
```

关键结果：

```text
review diff
a/.smoke-cli/checkpoint_demo.txt → b/.smoke-cli/checkpoint_demo.txt
@@ -1 +1 @@
-version-1
+version-2
CHANGED
No checkpoints found for /Users/wangchao/workspace/hermes-agent
```

后续核对：

- `.smoke-cli/checkpoint_demo.txt` 实际内容仍是 `version-2`

结论：

- 文件改写动作成功
- 但这条真实链路里，`--checkpoints` 没有让 `/rollback` 找到可恢复点，属于已确认问题

### 3.9 技能预加载 `-s`

已安装技能：

- `~/.hermes/skills/dogfood/SKILL.md`

有效技能测试：

```bash
source venv/bin/activate
./hermes chat -s dogfood --max-turns 4 -q '请只回复 SKILL_OK'
```

关键结果：

- banner 中的 `Available Skills` 包含 `general: dogfood`
- 最终回答为 `SKILL_OK`
- session id：`20260417_005332_bed12b`

无效技能对照测试：

```bash
source venv/bin/activate
./hermes chat -s definitely_missing_skill --max-turns 2 -q 'hi'
```

结果：

```text
Error: Unknown skill(s): definitely_missing_skill
```

结论：

- `-s` 的技能名校验链路是正常的
- `dogfood` 被 Hermes 识别为有效技能

仍待确认的点：

- 在这轮真实输出中，没有稳定观察到 `Activated skills: dogfood` 这一行
- 所以目前只能确认“技能参数被接受并实际进入运行流程”，不能确认启动提示展示一定稳定

### 3.10 `sessions export`

命令：

```bash
source venv/bin/activate
./hermes sessions export --session-id 20260417_004943_f7bc56 .smoke-cli/session-export.json
```

结果：

```text
Exported 1 session to .smoke-cli/session-export.json
```

导出文件校验结果：

```text
session_id= 20260417_004943_f7bc56
source= cli
message_count= 2
messages_len= 2
first_roles= ['user', 'assistant']
```

结论：

- 单会话导出链路正常
- 导出结果是可解析的 JSON，且消息结构完整

### 3.11 让 Hermes 修改临时代码并实际运行

准备文件：

```python
def main():
    print("old")

if __name__ == "__main__":
    main()
```

让 Hermes 修改：

```bash
source venv/bin/activate
printf '请只使用 file 工具，把 .smoke-cli/calc.py 里的 old 改成 new，并且只回复 PATCHED\n/exit\n' \
  | ./hermes chat --plain -t file --max-turns 8
```

关键结果：

```text
review diff
a/.smoke-cli/calc.py → b/.smoke-cli/calc.py
@@ -1,5 +1,5 @@
 def main():
-    print("old")
+    print("new")

PATCHED
```

运行验证：

```bash
source venv/bin/activate
python3 .smoke-cli/calc.py
```

结果：

```text
new
```

结论：

- Hermes 在真实开发小场景里可以完成“改代码 -> 保存 -> 运行验证”的闭环

## 4. 当前已暴露的真实问题

按优先级，当前最值得继续追的是真实行为问题，而不是继续堆更多静态文档。

### 4.1 `--checkpoints` 与 `/rollback` 不匹配

现象：

- 打开 `--checkpoints` 后，文件修改成功
- 但执行 `/rollback` 时返回 `No checkpoints found for /Users/wangchao/workspace/hermes-agent`

影响：

- 用户会以为自己开启了“可回滚保护”，但在真实链路里并没有生效

### 4.2 `--worktree` 与终端 cwd 可能不一致

现象：

- worktree 创建/清理成功
- 但 `terminal` 中 `pwd` 仍回到主仓库路径

影响：

- 用户以为自己在隔离工作树里执行命令，实际却可能仍在主工作树操作

### 4.3 `-Q` 模式仍有额外输出泄漏

已观察到的泄漏类型：

- resumed 提示
- worktree 创建/清理提示
- ANSI 颜色控制字符

影响：

- `-Q` 不适合直接作为严格机器可解析接口，除非调用方自己再做清洗

### 4.4 技能激活提示展示不稳定

现象：

- 有效技能会被正确接受
- 无效技能会被正确拒绝
- 但有效技能启动时，不一定能看到 `Activated skills: ...` 提示

影响：

- 用户难以快速确认某个技能是否真的按预期预加载

## 5. 建议作为后续最小回归集的命令

如果后续要继续修 CLI 行为，建议优先反复回归下面这组命令：

```bash
source venv/bin/activate

./hermes chat -Q --source tool --max-turns 4 -q '请只回复 HERMES_SMOKE_OK'

./hermes chat -Q --source tool --max-turns 8 -t file \
  -q '请只使用 file 工具，统计 docs 目录下一级 markdown 文件数量，只回复数字'

printf '请只回复 PLAIN_OK\n/exit\n' | ./hermes chat --plain

./hermes chat --checkpoints -t file

./hermes chat --worktree

./hermes sessions export --session-id <session_id> -
```

如果你是接着本文继续定位问题，建议优先顺序是：

1. 查 `--checkpoints` 与 `/rollback` 的 checkpoint 写入/查找路径是否一致
2. 查 `--worktree` 进入聊天会话后，`terminal` 后端的 cwd 是在哪一层丢失的
3. 查 `-Q` 模式下哪些输出仍绕过了 quiet/parseable 分支

