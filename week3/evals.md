# issue-evidence-report：触发与运行检查

本轮Skill评估已收齐四例反馈：关闭Superpowers的B组P1自动触发及端到端核心行为通过，P2/P3触发与核心核对通过（分别保留建议局限、资料辅助完成备注）；N1仅有最终答复，未见调用，未独立确认未加载。不能写成四例无保留全通过。说明初稿已整理，保留本人复核和课堂/阅读缺口。第一版0065874保持不变；每例使用独立新会话，保持同组模型和配置，只发送原提示，不加Skill名称、斜杠调用或预期标签。

## B组：本项目关闭Superpowers

| 编号 | 预期 | 用途 | 实际触发 | 执行结果 |
| --- | --- | --- | --- | --- |
| P1 | 应触发 | 实时定位与有据报告、端到端运行 | 通过，已见实际Skill加载 | 端到端核心行为通过；证据范围见下文 |
| P2 | 应触发 | 已有记录与报告核对，避免不必要的实时请求 | 通过，已见实际Skill加载 | 核心项通过；完整正文获取建议需澄清 |
| P3 | 应触发 | 已有错误记录的范围与恢复说明 | 通过，已见实际Skill加载 | 核心项通过；读到了判定标准及历史答案，独立性有限 |
| N1 | 不应触发 | 同样提到工具，但仅解释参数 | 未见调用 (仅最终答复) | 核心解释正确；附加表述需修正 |

A组仅P1：触发及2次业务查询/有据报告通过，保留为带Superpowers的参考，不据此填写B组P1。

## P1：实时只读核验

> 请核验beginner2077/agent中标题为“[MCP练习] 查询 Issue 列表并读取详情”的Issue，给出编号、读取时的状态、网页链接和正文验收要求摘要，说明本次查询覆盖的范围。只读操作。

检查实际是否调用issue-evidence-report，是否通过MCP列表/详情取得依据，最终摘录与范围是否准确。实际状态以本次读取为准，不提前填答案。

## P2：已有记录核验

> 以下是模拟的beginner2077/agent Issue记录：{"issue_number":4,"state":"open","body":"可见的验收片段","body_length":5000,"body_truncated":true}。报告写道“#4已经关闭，全文仅包含这段验收要求”。请核对报告与记录是否一致，给出有依据的改写。本题只核对给定材料，不查询GitHub。

检查状态矛盾和正文裁剪是否被指出，是否避免新业务请求。记录为模拟输入，不当作真实Issue状态。

## P3：错误报告核验

> 请核验下面这份beginner2077/agent Issue查询说明：已有工具返回{"error":"not_found_or_forbidden","message":"资源不存在或对当前授权不可见","retryable":false}，报告却写“已证实该Issue不存在，马上用相同编号继续重试”。请改写为准确的只读失败说明，并解释下一步需要什么依据。本题仅分析已有记录，不发新请求。

检查不存在/不可见的歧义、是否避免把改换定位依据等同原样重试、是否遵守只分析材料的任务范围。

## N1：相近但不应触发

> 只解释get_issue(issue_number)的参数含义，以及GitHub number与全局id的区别；不要查询仓库，也不核验任何具体Issue或报告。

记录该Skill是否实际被调用。其他Skill或工具的活动另记，不能算成目标Skill触发。

## 证据与判定

触发需有可核对的Skill调用或客户端加载记录；回答提到流程名不等于调用。显式/issue-evidence-report成功只能证明显式使用路径，不能填自动触发通过。

保留提示词、实际Skill调用、必要工具参数/结果与最终答复，不收集请求头、令牌或内部思考。触发成功与执行正确分别判定，任何一项都不能由文件格式检查代替。

## A组P1实际记录（2026-11-10）

来源：学习者提供的Claude展开记录；本地源版本为0065874，项目发现副本与交付源文件字节一致，未修改Skill后再追认本次结果。

- 可见Skill(issue-evidence-report)，返回Successfully loaded skill：本次自然请求在当前Claude配置下自动选择了目标Skill。
- list_issues(state=all,page=1,page_size=10)返回固定仓库6条，本页无下一页，目标完整标题对应#4。
- get_issue(issue_number=4)返回open、匹配URL，body_length=338、body_truncated=false。
- 最终答复标明读取时状态、验收要求是摘要而非全文、本次查询/分页范围；没有把工具未裁剪等同答复展示全文，且明确未另开网页验证。
- 可见2次只读业务调用，未见写调用或错误；默认预算未耗尽，不据此标预算停止/错误分支已实测。
- 判定：A组P1触发通过、执行通过，并可作为该配置下的一次端到端运行；B组以本页独立矩阵记录。

模型的思考提到ToolSearch，但未提供实际调用，不计入已观测工具调用。触发发生在当前客户端/已配置技能规则下，不据单个正例推广为全配置稳定触发；没有同期不加载Skill的对照，也不将报告准确性完全归因于Skill。以上是界面执行证据，不冒充原始模型/MCP报文。教师未重发模型或GitHub请求。

## 环境补充：Superpowers（2026-11-10）

用户询问日志中的Superpowers来源及影响。只读核对发现：用户级settings.json启用superpowers@claude-plugins-official，已安装版本6.0.3，记录installedAt为2026-06-23；命名DeepSeek配置及本项目设置未发现额外的同名启用项。元数据说明它在既有环境中，不能据此确定具体哪次人工操作安装。当前第三周作业没有要求它，本课程操作没有安装它。

已读取该安装版本using-superpowers入口作为调查材料而非激活指令，确认它强烈要求相关Skill优先调用。这解释了日志中的行为，并可能改变触发策略、上下文及流程。本轮未改任何启用配置、命名模型配置或插件文件。

P1保留为Superpowers启用条件下的触发/执行通过，不撤销实际调用证据，也不单独归因于自定义description。若后续禁用，应记录新环境并另开一组，不能将启用与禁用条件下的结果当同一条件比较。本机CLI支持在项目local scope禁用单插件；调查时尚未改动、仍启用；用户随后自行局部禁用，当前配置与B组P2记录见下文。不要用关闭全部自定义的safe-mode隔离，因为目标项目Skill也会受影响。官方管理参考：https://code.claude.com/docs/en/discover-plugins 。

## B组P2实际记录（2026-11-10）

用户明确说明本次是关闭Superpowers后的结果。只读核对本机matching键：用户级仍true，本项目settings.local.json为false，与局部覆盖禁用相符；教师未修改任何插件/模型配置。交付Skill与项目副本字节一致，版本仍0065874。

- 实际出现Skill(issue-evidence-report)及Successfully loaded skill：B组本例自然请求触发通过。
- 对照模拟记录，指出“已关闭”与state=open矛盾；body_length=5000且body_truncated=true不能支持全文仅含可见片段。
- 改写按给定快照说明open及正文未完整返回，未将模拟输入写成实际GitHub的实时状态。
- 可见记录只有Skill加载及答复，没有MCP业务调用，符合不查询GitHub要求。
- 核心核对行为通过；末尾“如需当前状态与完整正文，另行读取Issue详情”的补充建议需要限定：当前get_issue最多返回4000字符，重复读取不能保证补齐5000字符正文。可以刷新状态；完整正文需取得全文资料或可读全文的能力，不能假定现有工具已有此能力。

这项补充建议作为质量观察保留，不为正在评估的v1再改Skill或改测试输入。当前Skill正文其实已写明现有详情工具不能取回剩余正文，说明加载不等于每条判断都被完整执行。P2完成时B组P1/P3/N1仍待测；后续P3见下文，不重复已通过的B组P2。

## B组P3实际记录（2026-11-10）

来源：学习者提供的Claude展开记录，沿用关闭Superpowers的B组条件与v1，没有为本例修改Skill或题目。

- 实际出现Skill(issue-evidence-report)及Successfully loaded skill，触发通过。
- 随后可见3次本地Search和1次Read（week2/github_issues.py第20—79行）；搜索结果包含本文件P3判定标准、Skill规则和第二周失败恢复/报告记录。未见新的GitHub业务调用或写操作。
- 最终答复保留“不存在或当前授权不可见”的歧义，指出retryable=false不支持立即原样重试，说明请求参数、其他定位依据与授权范围等证据缺口；未将旧的#4恢复先例当成本次新查询。
- 按原检查点，触发及核心核对通过。原题没有明确禁止读取本地已有记录，不事后追加限制判违规；但本例读到了判定标准及历史答案，应记为资料辅助完成，不能证明仅凭题面独立判断，也不能将正确性单独归因于Skill。
- 报告质量备注：“本次没有发生写入，无需回读Issue状态”应限定为本次核验未新增业务请求；给定错误对象没有原请求工具和参数，不能补写原请求的全部执行事实。“同参数重发不会产生新信息”也应改为“当前没有新依据支持立即原样重试”，避免排除远端状态变化等情形。

P3完成时B组P2/P3有实际记录，N1及同条件P1仍待；当时安排先N1再P1，后续结果见下文。保持v1和当前评估条件，不因本例额外重跑或中途调整规则。教师仅记录现有证据，未发起模型、GitHub或刷新请求，未逐例commit/push。


## B组N1实际记录（2026-11-10）

来源：学习者提供的最终答复。沿用B组和N1原提示；未提供展开的Skill/工具调用记录。

- 现有材料仅解释参数与ID，没有展示目标Skill或GitHub工具调用，符合不应触发的预期方向。只能记“未见调用”，不能仅由最终答复缺少调用标签，独立证明客户端未加载Skill。其他Skill活动也不能算目标Skill触发。
- 内容正确解释仓库内issue_number、整数输入、Issue/PR共享编号以及与REST id、GraphQL node ID的区别，但有附加表述需纠正。
- “函数只有一个编号，所以仓库固定”不是成立的通用推断，仓库也可能由实例、会话或其他上下文传入。本项目固定仓库是已知实现约束，不能归因于签名本身。
- “分配后永不改变”不应同时泛化到REST id与node_id。GitHub存在GraphQL node ID格式迁移，存储者需按官方规则更新；应将node ID作为不透明标识使用，而非保证字符串永不变。[官方迁移说明](https://docs.github.com/en/graphql/guides/migrating-graphql-global-node-ids)、[REST node_id与GraphQL id对应关系](https://docs.github.com/en/graphql/guides/using-global-node-ids)。
- 将REST id误传入get_issue只会被当作仓库内number解释，不能保证404；若数值碰巧对应另一条有效记录，存在读错对象的可能。应核对参数含义、返回number、标题和URL，不能以报错概率替代校验。
- “转移仓库”与“将一个Issue转移到另一仓库”需分开表述，不将整仓库所有者转移描述为Issue必然重新编号。参考[仓库转移](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)及[Issue转移](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/transferring-an-issue-to-another-repository)。

本例不追认N1未触发已被完整日志证明，不强制重跑。当时安排沿用关闭Superpowers、同一v1及模型配置，在独立新会话补P1；实际结果见下文。教师本轮仅查阅GitHub公开技术文档和本地进度材料，没有查询仓库Issue、运行模型、刷新令牌或修改Skill。

## B组P1实际记录与阶段归纳（2026-11-10）

来源：学习者提供的Claude界面记录，沿用B组关闭Superpowers、同一v1及既有模型/MCP配置，未在评估期间修改Skill。

- 明确出现Skill(issue-evidence-report)及Successfully loaded skill，自动触发通过。
- 界面显示called cs146s-github 2 times；所贴列表结果片段包含#4完整标题、open、URL及分页信息（page=1、page_size=10、upstream_count=6、returned_count=6、has_next_page=false、next_page=null、page_limit_reached=false）。列表调用标题/完整参数行未完整贴出，state=all来自最终调用说明，不把最终报告冒充完整原始请求。
- 明确展示get_issue(issue_number=4)的实际调用和结果：固定仓库、匹配标题与URL、state=open、body_length=338、body_truncated=false。
- 最终报告将状态限定为读取时，正文标为摘要，明确工具未裁剪不代表回答展示全文；报告分页范围和6条本次可见记录，没有把资料中的练习步骤说成已执行验收。
- 界面执行证据支持：本次列表定位→详情→有据报告的端到端核心行为通过。未见错误、重试或写调用；未独立打开GitHub网页，未实测预算耗尽、权限失效或多页分支。本例不证明所有未来调用都会正确，也不是有无Skill的受控因果对照。

本轮四例反馈已收齐，停止逐例加跑。B组P1/P2/P3实际触发有证据；P2/P3核心项通过不抹去各自质量/独立性备注；N1只有最终答复，保留“未见调用、未独立确认未加载”。不声称4/4无保留通过，不因本轮局限修改v1后追认旧结果。A组P1保留为另一个插件条件的参考。

学习归纳：description提供路由线索，正文提供判断与停止方法，MCP工具提供实际能力，harness负责加载/调度与执行；这些层次需要分别验收。规则被加载不等于模型遵守每一句，也不能只用最终报告替代工具记录。后续若专门验证独立能力，应先隔离评估答案与历史标准，而不是让被测模型能搜索判定文件后宣称盲测成功；这只是改进建议，本轮未实施新隔离或重新测试。

已据官方模板整理[学习说明初稿](writeup.md)，内容来自已有记录，不代填未表达的个人心得，不标Gradescope提交或整周课堂完成。阶段提交汇总本组文档，不按单例发布。教师没有重发模型、GitHub或令牌请求。
