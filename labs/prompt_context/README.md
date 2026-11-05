# 补充前置：指令、示例与外部资料对照

本练习支撑 CS146S Fall 2026 的上下文工程学习，不是改做 Fall 2025 正式作业。材料、运行器及离线验证已准备好，尚未运行真实模型实验；所有示例地址与接口规范均为虚构，脚本只调用 DeepSeek，不访问这些示例接口。

## 三类输入的作用

- 指令：目标、约束、未知信息处理及输出要求。
- 示例提示：一个示例称 one-shot，多个称 few-shot；通过具体输入/输出展示任务映射、边界处理和格式，不更新模型权重。
- 外部资料：当前任务所需的接口规范等事实。自动从资料库选取相关内容再供生成使用，是检索增强的信息流。

三者可同时进入同一请求。示例也可能包含事实，所以要控制示例不泄露测试目标；本练习给出两个其他服务的示例。

## 各组共用的指令与任务

```text
请根据提供的目标接口资料，给出查询用户姓名的调用方案。
只返回一个 JSON 对象，恰好包含 method、url、auth_header、result_path 四个字段。
字段值只能是字符串或 null。
只能依据与当前目标服务有关的资料填写事实；缺少依据的字段返回 null，不猜测。
result_path 用点分路径表示，url 应替换成指定用户的实际路径。
示例用于展示格式，不是当前目标服务的接口资料。
不要调用工具或访问网络。

目标服务：Directory，用户 ID：u42，目标：取得该用户的姓名。
```

## 可选示例：只用于有示例的组

```text
示例目标：取得 Status 服务的健康状态。
示例资料：GET https://status.example.test/ping，无需认证，响应为 {"healthy": true}。
示例输出：
{"method":"GET","url":"https://status.example.test/ping","auth_header":null,"result_path":"healthy"}

示例目标：查询 Weather 服务的城市天气。
示例资料：未提供。
示例输出：
{"method":null,"url":null,"auth_header":null,"result_path":null}
```

## 目标文档：只用于有目标文档的组

```text
Directory API v2：
按用户 ID 获取用户资料：GET https://directory.example.test/v2/members/{id}
认证要求：在请求头 X-Org-Key 中传入 API key。
响应示例：{"data":{"profile":{"display_name":"李明"}}}
```

## 四组输入

| 组 | 共用指令及任务 | 两个示例 | Directory 目标文档 |
| --- | --- | --- | --- |
| A | 有 | 无 | 无 |
| B | 有 | 有 | 无 |
| C | 有 | 无 | 有 |
| D | 有 | 有 | 有 |

同一模型、相同模式及有效采样设置、相同输出长度限制；各次都是独立请求，不能让后一组看到前一组的输出。各组先重复三次，仅作小样本观察，不凭少量结果宣称普遍提升。示例题与目标题不同，避免直接把目标答案作为示例。

## 评价标准

1. 格式：可解析为 JSON；恰好四个字段；类型符合要求。分别记录解析成功和 schema 符合，不用一个指标混在一起。
2. 事实依据：无目标文档时四字段均为 null 是合规的未知处理；填入没有依据的地址/头/字段应记为编造，不能因为看起来完整就加分。
3. 完成度：有目标文档时检查四项事实，正确方案应是下面的对象；字段顺序与空白无关。无文档组诚实返回未知是合规，但未完成具体调用方案，两种状态分开记录。

```json
{"method":"GET","url":"https://directory.example.test/v2/members/u42","auth_header":"X-Org-Key","result_path":"data.profile.display_name"}
```

以上正确对象仅用于评价，不能发送到待评估请求中。所有组的完整输入应排除本 README 的评价段；不得让模型自动读取整个目录或文件。

对照：A/B、C/D 比较增加示例的效果；A/C、B/D 比较增加目标文档的效果。不能只比较 A/D 后把所有变化都归功于示例。

本练习先由人选择是否注入固定文档，尚未实现自动检索。后续真正检索实验需额外检查是否选中相关且版本正确的资料；检索命中、模型正确使用资料、输出格式正确应分开评估。RAG 可以结合关键词、语义或混合检索，不以安装向量数据库作为本小步前置。

## 运行方法

从项目根目录的 PowerShell 运行。先预览四组实际请求体，不读取密钥，不创建客户端，也不发送请求：

```powershell
.\.venv\Scripts\python.exe labs/prompt_context/run_experiment.py
```

确认输入后，运行真实实验：

```powershell
.\.venv\Scripts\python.exe labs/prompt_context/run_experiment.py --run
```

运行器使用项目现有 OpenAI Python SDK 作为 DeepSeek Responses 客户端，目标地址为 `https://api.deepseek.com/responses`。它从 `%USERPROFILE%\.claude\settings-deepseek.json` 的 `env` 读取 `ANTHROPIC_AUTH_TOKEN` 或 `ANTHROPIC_API_KEY`，并核对其中的地址属于官方 DeepSeek；不回落到其他配置或 `OPENAI_API_KEY`。模型固定 `deepseek-flash`，不继承配置中的 Pro 模型，也不修改 Claude 配置。

本实验显式请求非思考模式 `reasoning.effort=none`、`temperature=0.2`、`top_p=1.0`、`max_output_tokens=512`，四组相同。DeepSeek Responses 的 temperature 在思考模式下不生效；Flash 的 top_p 在非思考模式固定 1.0，思考模式下限为 0.95，不能照搬数学示意的 top_p=0.8。日志同时保留请求参数与响应回显；回显缺失时应记为未知，不能仅凭请求字段断言服务端实际条件。

每轮按 A、B、C、D 顺序交错运行，共三轮，最多 12 次请求。每次只有相同的系统指令和本组新建的 user 消息；不经过 Claude Code，不携带项目文档、其他组回复或 README 的评价答案，不提供工具。输出格式由提示约束，没有启用强制 JSON schema，便于观察格式错误。遇到接口错误、未完成响应或意外工具调用时停止，不自动重试；按 Ctrl+C 可以中断。

## 查看结果与离线验证

每次真实运行单独写入已被 Git 忽略的 `traces/prompt-context/<UTC时间>-<随机后缀>/`：

- `results.jsonl`：每次请求体、模型文本、响应 ID/模型/模式/采样参数/用量等回显、评分或错误类型；不保存密钥和认证请求头。
- `summary.json`：四组汇总。中断时已逐条写入的记录保留，汇总可能尚未生成。

终端也会显示汇总表。`API完成` 计数不代表任务完成；`JSON可解析` 与 `结构合规` 分别统计。`有依据/可判定` 只评价结构合规的回复，不能把结构错误算作已经判定的事实错误；`0/0` 表示没有可判定回复。`任务完成` 仅表示有文档时四字段全部正确，不代表真实接口调用成功。无文档组全 null 可以有依据，但任务完成数仍为零。

先比较 A/B 与 C/D 的示例效果，再比较 A/C 与 B/D 的资料效果，结合原始回复解释失败类别。每组仅三次且只有一道题，即使全部正确，也不能推出示例普遍有效。可以将终端汇总发回学习会话，不要发送本机密钥配置。

离线验证命令：

```powershell
.\.venv\Scripts\python.exe -m pytest labs/prompt_context -q
```

2026-11-05：15 项离线测试通过，覆盖输入隔离、评分、SDK 请求格式及错误处理；SDK 请求由本地模拟响应接收，未发送真实模型请求。这些测试验证运行器，不作为四组模型效果的实验结果。自动检索环节仍未实现。

## 技术来源

- [Google：Prompt engineering 与 few-shot](https://developers.google.com/machine-learning/crash-course/llm/tuning)
- [RAG 原始论文](https://arxiv.org/abs/2005.11401)：本轮只读摘要以核对概念，未完成论文导读。
- [Anthropic：检索增强的信息流及关键词/语义检索](https://www.anthropic.com/research/contextual-retrieval)
- [DeepSeek Responses 兼容说明](https://api-docs.deepseek.com/guides/responses_api/)
