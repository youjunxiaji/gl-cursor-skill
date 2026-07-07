---
name: cursor-agent
description: "把高 token 消耗、且自包含的活委派给 Cursor 的 cursor-agent CLI(别名 `agent`,位于 ~/.local/bin/agent)执行 —— 本账户下它【按次收费,不按 token 收费】,所以读大文件、批量/重复多文件改动、大范围重构、大上下文分析、长文本生成这类烧 token 的活丢给它最划算。本 skill 同时教你(无论你是 Codex、Claude Code 还是 OpenCode)如何把 cursor-agent 注册成你自己可调用的原生子智能体,以及何时调用。触发词:用/跑 cursor-agent、委派给 cursor、让 cursor 去做、丢给 cursor 跑、offload to cursor、delegate to cursor。工作流:先列任务清单,一次只委派一个(极繁琐时最多 2 个并行,绝不超过 2),先验证再汇报。默认模型 composer-2.5,只用 headless(-p)模式。"
---
# 把重活委派给 cursor-agent(跨工具子智能体指南)

`cursor-agent`(别名 `agent`,路径 `~/.local/bin/agent`)是 Cursor 的命令行编码代理。在本账户下它
**按次调用收费,不按 token 收费**。这就是使用它的全部理由:把**高 token 消耗**的活丢给它,
每次委派只算**一次调用**,不管它内部啃掉多少 token —— 从而省下你自己的 token 预算。

本文件有两个用途:
1. **何时 / 如何调用**它(命令模板 + 委派纪律)—— 见下方"命令模板""工作流""红线"。
2. **如何把它注册成你这个工具里的原生子智能体** —— 见"注册成原生子智能体",按你正在运行的工具
   (Codex / Claude Code / OpenCode)选对应小节。

---

## 什么时候用
- 任务**很费 token**,并且足够自包含、能整块交出去(读大文件、批量/重复多文件改动、大范围重构、
  大上下文分析、长文本生成)。
- 用户明确说:用 cursor-agent / 委派给 cursor / 让 cursor 去做 / offload to cursor。

任务很小、token 花费很低,就直接自己做,别浪费一次调用。

## 工作流(重点)
1. **先列任务清单。** 把工作拆成一个个具体、能独立跑的任务,展示给用户。
2. **一次只委派一个。** 默认严格**串行** —— 一个任务一次调用,读完并验证结果再进行下一个。
3. **并行上限 = 2。** 只有工作**极其**繁琐/庞大时,才最多 **2 个**并行(各自后台启动)。**绝不超过 2。**
4. **先验证再汇报。** 每次调用后,先确认它确实完成了任务(看 `git diff`、读改动的文件、检查产物),
   再向用户总结,然后继续下一个。

「一次一个 / 最多 2 个」这条规则直接对应按次收费 —— 务必遵守。

## 命令模板(永远用 headless `-p`)
**交互模式在无人值守环境会卡死 —— 绝不要不带 `-p` 直接跑 `agent`。**

```bash
cursor-agent -p --output-format text --trust --force \
  --model composer-2.5 \
  --workspace <工作目录的绝对路径> \
  "<清晰、完全自包含的任务说明>"
```

各参数:
- `-p` —— 非交互,结果打到 stdout;拥有全部工具权限(读、写、执行 shell)。
- `--trust` —— 信任当前工作区(headless 专用;不加会卡在信任提示上)。
- `--force`(别名 `--yolo`)—— 所有工具调用不询问直接执行。本账户**默认无沙箱**,它是真的在磁盘上
  改文件、跑命令。**把每个任务严格限定在它的 `--workspace` 里。**
- `--model composer-2.5` —— 默认模型(见下方"模型说明")。
- `--workspace <绝对路径>` —— 目标目录,优先用它而不是 `cd`;要加更多根目录用 `--add-dir <路径>`。

如果 `cursor-agent` 不在 PATH 上,用绝对路径 `~/.local/bin/agent`。

### 按任务形态切换
- **只读分析 / 规划**(不想让它改文件):加 `--plan`(或 `--mode plan`)—— 更便宜也更安全,它无法写盘。
- **有风险或要并行改文件**:加 `-w`(`--worktree`),让它在隔离的 git worktree
  (`~/.cursor/worktrees/<repo>/<name>`)里跑,而不是动实时工作树;用 `--worktree-base <ref>` 指定基线。

### 怎么写任务说明
这段 prompt **就是全部交底** —— cursor-agent 看不到你和用户的对话。必须写清楚:目标、涉及的确切
文件/路径、约束条件,以及"做完"的标准。它无人值守运行,所以要**明确、自包含**。

### 模型说明(改 `--model` 前必读)
- **默认 `composer-2.5`** —— Cursor 原生、快、无需 Max Mode。除非另有要求,保持它。
- ⚠️ 几乎所有标 **"1M"** 的模型(GPT-5.5、Sonnet 5、Opus 4.8、GPT-5.4、Grok 4.3……)都要开
  **Max Mode**,而它默认在 `~/.cursor/cli-config.json` 里是**关闭**的。headless 传这些模型会立刻报
  `ActionRequiredError: Max Mode Required`。用户没开 Max Mode 前**不要**切到 1M 模型。
- 免 Max Mode 的替代:`gemini-3.1-pro`(CLI 当前存储的默认)、`gpt-5.2`、`claude-4.5-sonnet`、
  `composer-2.5-fast`。列出全部:`cursor-agent --list-models`。

### 多轮追问
- `--continue "…"` —— 在最近一次会话上继续。
- `--resume <chatId> "…"` —— 恢复指定会话;`cursor-agent create-chat` 可预先拿到一个 chatId。
- 需要程序化解析结果(含 chatId)时,用 `--output-format json`。

---

## 注册成原生子智能体
上面的"命令模板"已经能让你直接调用 cursor-agent。如果你想把它变成一个**有名字、可反复派发的原生
子智能体**,按你正在运行的工具选下面对应的小节创建一个定义文件即可。三个工具的核心思路一样:
**一个只有 shell 权限的瘦子智能体,唯一职责就是运行 cursor-agent CLI 并回传结果。**

> 说明:这些子智能体是"执行器"。让它跑 Haiku / 便宜模型这类薄封装最划算 —— 真正的重活在 cursor-agent
> 内部完成(按次计费),封装本身几乎不花钱,而且它会替你吃掉 cursor-agent 的海量输出、只回精简摘要,
> 保护你的主上下文。

### Claude Code
建议路径:`~/.claude/agents/cursor-agent.md`(用户级)或 `.claude/agents/cursor-agent.md`(项目级)。
主智能体通过内置 **Agent 工具**按 `description` 自动派发。

```markdown
---
name: cursor-agent
description: 把高 token 消耗、自包含的重活(读大文件、批量改动、大重构、大上下文分析、长文本生成)委派给 Cursor 的 cursor-agent CLI 执行并回传精简结果。
tools: Bash
model: haiku
---
你是 cursor-agent CLI 的调度器。收到任务后,用 Bash 运行(把 <task> 换成完整自包含的任务说明,
<abs> 换成工作目录绝对路径):

cursor-agent -p --output-format text --trust --force --model composer-2.5 --workspace <abs> "<task>"

等它跑完,验证任务确实完成(git diff / 读改动文件),然后把精简结果回传给主智能体。
不要自己动手解任务,也不要粘贴 cursor-agent 的全部原始输出 —— 只回摘要 + 关键产物 + 出现的报错。
```

`tools: Bash` 授予 shell;`model: haiku` 让封装便宜。省略 `tools` 会继承父级全部工具。

### OpenCode
建议路径:`~/.config/opencode/agents/cursor-agent.md`(全局)或 `.opencode/agents/cursor-agent.md`
(项目级)。文件名即子智能体名。主智能体通过 **`task` 工具**(`subagent_type: cursor-agent`)派发,
或用户用 `@cursor-agent` 手动召唤。

```markdown
---
description: 把高 token 消耗、自包含的重活委派给 Cursor 的 cursor-agent CLI 执行并回传精简结果。
mode: subagent
model: anthropic/claude-haiku-4-5
permission:
  bash: allow
  edit: deny
---
你是 cursor-agent CLI 的调度器。收到任务后,用 bash 运行(把 <task> 换成完整自包含的任务说明,
<abs> 换成工作目录绝对路径):

cursor-agent -p --output-format text --trust --force --model composer-2.5 --workspace <abs> "<task>"

等它跑完,验证任务确实完成,然后把精简结果回传给主智能体。
不要自己动手解任务,也不要粘贴 cursor-agent 的全部原始输出 —— 只回摘要 + 关键产物 + 出现的报错。
```

关键:`mode: subagent` 必填;`permission.bash: allow` 授予 shell(也可用
`bash: { "*": "ask", "cursor-agent *": "allow" }` 做细粒度)。`model` 用 `provider/model` 格式。

### Codex
**首选(受支持):把本 skill 当技能用。** Codex 原生支持 Agent Skills —— 本 skill 装到
`~/.codex/skills/cursor-agent/`(或项目级 `.codex/skills/cursor-agent/`)后,Codex 会通过 `skill`
工具按需加载它;遇到适合外包的重活,就直接按上面的"命令模板"运行 cursor-agent CLI。Codex 的 shell
需要在 `workspace-write`(或更高)sandbox 下才能真正执行。这是 Codex 上最稳的方式,无需额外配置。

**进阶(实验性):agent roles 多智能体。** Codex 还有"agent roles"机制,可生成真正独立的子智能体:
在 `~/.codex/config.toml` 写一个角色表,并(可选)放一个角色配置层文件 `~/.codex/agents/cursor-agent.toml`
(它是一份**局部 config.toml**,用来固定 model、sandbox 等),主智能体通过 `spawn_agent` / 多智能体
工具生成它:

```toml
# ~/.codex/config.toml
[agents.cursor-agent]
description = "把高 token 消耗的重活委派给 Cursor 的 cursor-agent CLI 执行。"
config_file = "./agents/cursor-agent.toml"   # 相对本 config.toml 解析;这是一份局部 config 层
nickname_candidates = ["Cursor"]
```

⚠️ **`[agents.*]` 目前未写进 Codex 官方 `docs/config.md`,字段与行为可能变动。** 不要把本文的字段
当稳定 API 照抄 —— 以 <https://developers.openai.com/codex> 的最新说明为准。**若不确定,就用上面的
"首选"技能方式**,它已受官方支持且跨工具一致。

---

## 红线
- **一次一个任务;最多 2 个并行** —— 绝不超过 2。
- 只委派**确实费 token**或**用户明确要求**的活 —— **每次调用都花钱**。
- `--force` + 无沙箱 = 它真的会写文件、跑命令。把每个任务严格限定在它的 `--workspace` 里。
- 永远用 `-p`;绝不启动交互模式。
- 子智能体是执行器:让它**回传精简摘要**,不要把 cursor-agent 的原始海量输出灌进主上下文。
