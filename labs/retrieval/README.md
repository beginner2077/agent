# 最小本地检索练习

这是支撑 CS146S Fall 2026 上下文工程的补充练习，承接 [四组上下文实验](../prompt_context/README.md)。已实现“关键词检索 → 版本过滤 → 关联补全 → 准备模型输入”，并提供两案生成验证入口。教师只完成离线验证，真实生成实验待学习者运行；未执行虚构接口。

## 先观察一个完整案例

在项目根目录 PowerShell 中运行：

```powershell
.\.venv\Scripts\python.exe -m labs.retrieval.retrieval --case split_auth
```

代码中的资料是预先手动分好的虚构片段。接口与认证规则分属两块；检索过程会输出一个 JSON 对象和一行运行边界说明：

- `retrieval.query/filters`：实际检索词，以及服务和版本条件。
- `candidates`：符合条件且有词项重合的候选及分数，按分数排序；同分按 ID 排序。
- `selected`：初次选中的 `directory-v2-member`。
- `expanded`：根据明确引用补充的 `directory-v2-auth`。
- `unresolved_refs`：无法补全或范围不匹配的引用，本案例为空。
- `context_ids`：最终上下文包含的两块资料。
- `prepared_request.input[0].content`：准备发送的实际文本，包含两个片段的版本、标题和正文。

默认 `top_k=1` 只限制初次检索选择；关联补全可增加片段，所以最终有两块。认证正文来自原有认证资料，不是程序生成的业务规则。这里只准备请求，`prepared_request` 不能作为模型已执行的证据。

## 再比较缺少认证的案例

```powershell
.\.venv\Scripts\python.exe -m labs.retrieval.retrieval --case missing_auth
```

本案例保留 v2 接口和一份 v1 干扰资料，但没有 v2 认证正文。应看到关联引用的 `reason=missing`，上下文中不出现 `X-Org-Key` 或旧版 `Authorization`。提示仍要求缺少依据的字段返回 null；由于没有运行模型，这里尚不能证明模型真的返回了 null。

教师已本地运行并核对这个案例：`selected` 仍有接口片段，`expanded` 为空，`unresolved_refs` 报告缺失的认证引用。注意 `unresolved_refs` 是程序侧诊断，目前没有自动复制到模型输入；模型能收到的资料以 `prepared_request.input[0].content` 为准，其中只有接口正文和“参见本版本全局认证章节”的引用，没有认证规则正文。

按已有指令，本案例预期模型返回 GET、代入 u42 的 v2 地址、`data.profile.display_name`，而 `auth_header` 为 null。这是基于材料制定的预期，不是已经观察到的模型回复。应区分“程序知道资料缺失”“请求中明确给了哪些信息”和“模型实际如何回答”；若要验证第三项，下一阶段才执行模型端实验。学习者尚未提供这一步的运行结果。

其他案例使用相同命令，将 `--case` 改为：

| 案例 | 可观察结果 |
| --- | --- |
| `paraphrase` | “这个人怎么称呼”没有词项命中，尽管库中有相关资料；暴露当前方法的限制 |
| `version_noise` | v1 的关键词重合更多，但被 v2 条件过滤；最终仍使用 v2 接口及认证 |
| `unknown_service` | 目标 Roster 没有资料，不借用 Directory 的文档 |

`score` 是查询词项与片段词项的重合数量，不是正确概率，也不是 BM25 或向量相似度。英文标识符保留整体，中文采用相邻双字，这是为观察流程而写的简化规则。没有同义词扩展、embedding、混合检索或重排；不能用本练习宣称验证了这些方法。

## 验证两案的实际生成

运行器默认只预览两案输入，不读取密钥或请求模型：

```powershell
.\.venv\Scripts\python.exe -m labs.retrieval.run_generation
```

执行真实模型实验：

```powershell
.\.venv\Scripts\python.exe -m labs.retrieval.run_generation --run
```

仅比较 `split_auth` 和 `missing_auth`，交错各三次，最多六次请求。每次重新检索及组装一条独立 user 消息，不携带其他次回复、评价答案或程序侧的 `unresolved_refs`。两案相同的已知事实都应填写；缺认证时，只有 `auth_header` 应保持 null，而不是忽略已有资料把所有字段都置为 null。

| 本地评价项 | 含义 |
| --- | --- |
| API完成 | 接口返回完成状态及允许的输出类型，不代表业务正确 |
| 结构合规 | 可解析 JSON、恰好四字段、值为字符串或 null；完整日志另含 JSON 解析结果 |
| 有依据/可判定 | 仅评价结构合规回复；所有填写值都得到本案资料支持，null 允许表示未知 |
| 符合本案预期 | 完整案四字段正确；缺认证案三个已知字段正确且认证为 null |
| 完整方案 | 四字段都有依据且完整，缺认证案即便符合预期也不计为完整方案 |

例如，在缺认证案中猜中 `X-Org-Key` 仍属于无依据输出，不能因为它恰好等于另一案的正确认证头就加分；全 null 可以没有编造，但没有充分使用已知事实。评价采用本练习固定字段值，其他语义等价写法需人工复核，不代表通用方案正确性判定器。

运行器复用上一实验的配置及单次请求处理：只从 `%USERPROFILE%\.claude\settings-deepseek.json` 取官方 DeepSeek 地址和认证，模型固定 `deepseek-flash`，显式非思考模式、temperature=0.2、top_p=1、输出上限512；不修改 Claude 配置。使用 OpenAI SDK 连接 DeepSeek，不连接 OpenAI 服务，不提供工具或访问示例接口。

请求体、检索轨迹、原始模型文本、响应 ID/模型/模式/采样参数/用量回显、评分及错误写入被 Git 忽略的 `traces/retrieval-generation/<UTC时间>-<随机后缀>/results.jsonl`，汇总写入同目录 `summary.json`。不保存密钥或认证请求头。接口错误、未完成响应或意外输出类型会停止，不自动重试；错误只保存类型及状态码，不输出 SDK 错误正文。Ctrl+C 中断时保留已逐条写入的记录，汇总可能尚未生成。程序返回0表示实验请求流程跑完，不表示模型所有回答通过评价。

完成后将终端两案汇总发回学习会话。每案三次只是小样本观察，不能推出模型总能正确承认未知；还需核对原始回复和服务回显。

## 验证与边界

```powershell
.\.venv\Scripts\python.exe -m pytest labs/retrieval -q
```

2026-11-05：本地检索原有10项测试通过；本阶段新增15项生成验证离线测试，通过本地模拟响应检查依据敏感评分、独立请求、默认预览、运行入口、错误停止及日志。本目录共25项，与已有根环境练习合测共53项通过；上一四组实验的15项也保持通过。命令入口的默认预览已实际运行，真实六次生成请求尚未发送。

“同义表达没有命中”在测试中被作为当前实现的已知行为记录；测试通过不等于所有题的检索质量达标。真实模型生成、语义检索效果及完整 RAG 端到端表现尚未验证。原 `retrieval` 命令只本地运行，`run_generation --run` 才读取命名配置并请求 DeepSeek；没有安装新依赖，四组实验请求内容及评分规则未更改，两运行器共用单次请求处理。

本小步下一步由学习者运行两案生成实验并反馈汇总，区分“有据”“符合本案预期”和“完整方案”。
