# 最小本地检索练习

这是支撑 CS146S Fall 2026 上下文工程的补充练习，承接 [四组上下文实验](../prompt_context/README.md)。实现范围是“关键词检索 → 版本过滤 → 关联补全 → 准备模型输入”；没有调用模型，也没有执行虚构接口。

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

其他案例使用相同命令，将 `--case` 改为：

| 案例 | 可观察结果 |
| --- | --- |
| `paraphrase` | “这个人怎么称呼”没有词项命中，尽管库中有相关资料；暴露当前方法的限制 |
| `version_noise` | v1 的关键词重合更多，但被 v2 条件过滤；最终仍使用 v2 接口及认证 |
| `unknown_service` | 目标 Roster 没有资料，不借用 Directory 的文档 |

`score` 是查询词项与片段词项的重合数量，不是正确概率，也不是 BM25 或向量相似度。英文标识符保留整体，中文采用相邻双字，这是为观察流程而写的简化规则。没有同义词扩展、embedding、混合检索或重排；不能用本练习宣称验证了这些方法。

## 验证与边界

```powershell
.\.venv\Scripts\python.exe -m pytest labs/retrieval -q
```

2026-11-05：新增10项离线测试通过；与已有根环境练习合测共38项通过。检查覆盖上述五个案例、跨服务/版本引用拦截、循环与重复引用、索引和 top-k 参数，以及最终请求的正文。

“同义表达没有命中”在测试中被作为当前实现的已知行为记录；测试通过不等于所有题的检索质量达标。模型生成、真实语义检索效果及完整 RAG 端到端表现尚未验证。本练习不读取密钥、不联网，不安装新依赖，不更改原四组实验。

本小步先看 `split_auth` 的 selected、expanded 和实际输入，随后用 `missing_auth` 比较证据是否缺失。学习者运行及理解反馈仍待完成。
