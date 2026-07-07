---
name: cursor-agent
description: "把高 token 消耗的活委派给 Cursor 的 cursor-agent CLI(即 `agent`,位于 ~/.local/bin/agent)当子代理跑。适用场景:任务会烧掉大量 token —— 读大文件、批量/重复的多文件改动、大范围重构、大上下文分析、长文本生成 —— 且足够自包含可以外包;因为本账户下 cursor-agent 是【按次收费,不按 token 收费】,所以把烧 token 的活丢过去最划算。以下说法也应触发本技能:用/跑 cursor-agent、委派给 cursor、让 cursor 去做、丢给 cursor 跑、offload to cursor、delegate to cursor。工作流:先列任务清单,再【一次委派一个任务】(极繁琐时最多 2 个并行,绝不超过 2)。默认模型 composer-2.5。只用 headless(-p)模式。"
---
# 把任务委派给 cursor-agent(子代理)

`cursor-agent`(别名 `agent`,路径 `~/.local/bin/agent`)是 Cursor 的命令行编码代理。在本账户下它
**按次调用收费,不按 token 收费**。这正是使用它的全部理由:把**高 token 消耗**的活(读大文件、批量/
重复改动、大范围重构、大上下文分析、长文本输出)丢给它,省下我自己的 token 预算 —— 每次委派只算**一次调用**,
不管它内部啃掉多少 token。

## 什么时候用
- 任务**很费 token**,并且足够自包含、可以整块交出去。
- 用户明确说:用 cursor-agent / 委派给 cursor / 让 cursor 去做。

如果任务很小、token 花费很低,就直接自己做,别浪费一次调用。

## 核心工作流(重点)
1. **先列任务清单。** 把工作拆成一个个具体、能独立跑的任务,并展示给用户。
2. **一次只委派一个任务。** 默认严格**串行** —— 一个任务一次 `cursor-agent` 调用,读完结果再进行下一个。
3. **并行上限 = 2。** 只有当工作**极其**繁琐/庞大时,才最多 **2 个**并行(各自用后台 Bash 调用启动)。**绝不超过 2。**
4. **先验证再汇报。** 每次调用后,先确认它确实完成了任务,再向用户总结结果,然后继续下一个。

「一次一个 / 最多 2 个」这条规则直接对应按次收费 —— 务必遵守。

## 命令模板
永远用 headless(`-p`)。**在本环境里交互模式会卡死 —— 绝不要不带 `-p` 直接跑 `agent`。**

```bash
cursor-agent -p --output-format text --trust --force \
  --model composer-2.5 \
  --workspace <工作目录的绝对路径> \
  "<清晰、自包含的任务说明>"
```

各参数的原因:
- `-p` —— 非交互,把结果打到 stdout。拥有**全部工具权限**:读、写、执行 shell。
- `--trust` —— 信任当前工作区(headless 专用;不加会卡在信任提示上)。
- `--force` —— 所有工具调用都不询问直接执行(**完全自主**:改文件、跑命令)。本账户**默认无沙箱**,所以它是真的在磁盘上执行。
- `--model composer-2.5` —— 默认模型(见下方说明)。
- `--workspace <绝对路径>` —— 指定目标目录,优先用它而不是 `cd`。要加更多根目录用 `--add-dir <路径>`。

如果 `cursor-agent` 不在 PATH 上,用绝对路径 `~/.local/bin/agent`。

### 怎么写任务说明
这段 prompt **就是全部交底** —— cursor-agent 看不到我们的对话。必须写清楚:目标、涉及的确切文件/路径、
约束条件,以及"做完"的标准。它是无人值守运行的,所以要**明确、自包含**。

## 模型说明(改 `--model` 前必读)
- **默认 `composer-2.5`** —— 无需 Max Mode 即可用。除非另有要求,保持它。
- ⚠️ 几乎所有标着 **"1M"** 的模型(GPT-5.5、Sonnet 5、Opus 4.8、GPT-5.4、Grok 4.3……)都要求开
  **Max Mode**,而它当前在 `~/.cursor/cli-config.json` 里是**关闭**的。headless 传这些模型会立刻报
  `ActionRequiredError: Max Mode Required`。用户没开 Max Mode 前,**不要**切到 1M 模型。
- 如果确实需要替代模型,这些非 1M 模型同样免 Max Mode:`gpt-5.2`、`claude-4.5-sonnet`、
  `gemini-3.1-pro`、`composer-2.5-fast`。
- 列出全部模型:`cursor-agent --list-models`。

## 对已委派任务的多轮追问
- `--continue "…"` —— 在最近一次 cursor-agent 会话上继续追加。
- `--resume [chatId] "…"` —— 恢复指定会话。
- `cursor-agent create-chat` —— 预先创建一个 chat 拿到 ID,方便之后指定。

## 输出处理
- `--output-format text`(这里的默认)最易读、最好转述。
- 需要程序化解析结果时,用 `--output-format json`(或 `stream-json` 配合 `--stream-partial-output`)。

## 红线
- **一次一个任务;最多 2 个并行** —— 绝不超过 2。
- 只委派**确实费 token**或**用户明确要求**的活 —— **每次调用都花钱**。
- `--force` + 无沙箱 = 它是真的会写文件、跑命令。把每个任务严格限定在它的 `--workspace` 里。
- 永远用 `-p`;绝不启动交互模式。
