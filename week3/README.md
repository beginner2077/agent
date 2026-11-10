# 第三周：Agent Skills 与 CLI

本轮Skill评估已收齐四例反馈：关闭Superpowers的B组P1自动触发及端到端核心行为通过，P2/P3触发与核心核对通过（分别保留建议局限、资料辅助完成备注）；N1仅有最终答复，未见调用，未独立确认未加载。不能写成四例无保留全通过。说明初稿已整理，保留本人复核和课堂/阅读缺口。

## 课程与来源

2026-11-09核对[Fall 2026官网](https://themodernsoftware.dev/)公开页面资源中对应学期的课表：第三周为Agent Skills and CLI，主题包括SKILL.md与脚本如何编码流程、Web skills，以及CLI使用。课程网页同一资源同时包含旧版课表，2025的Week 3 The AI IDE不作为本周安排。

- 10/6：All about agent skills (including web skills)，[Slides](https://docs.google.com/presentation/d/15bPu5c-i8D8McTh6l7SpUPk2n9M_Y-CdDQLfyzL8RD8/edit?usp=sharing)。已定位链接，当前工具未读到课件正文，不标课堂已学完。
- 10/8：Lee Robinson嘉宾课，[Slides](https://drive.google.com/file/d/1b8WiBk_lcB3ue-jZMLijSUMLj6SDiF6Z/view?usp=drive_link)。同样仅定位，未读正文。
- 课表Reading：[pstack](https://github.com/cursor/plugins/tree/main/pstack)（已读README与how入口，其余按需待读）、[Matt Pocock's Skills](https://github.com/mattpocock/skills)（已读仓库总览及diagnosing-bugs/tdd入口，支持文件未全部展开）、[browse.sh](https://browse.sh)（已读CLI/目录功能概览，未安装或实操）。
- [官方作业](../course-assignments/week3/assignment.md)与[writeup模板](../course-assignments/week3/writeup.md)已核对本地及远端master；本地课程副本不修改。
- 作业指定基础材料：[Agent Skills概览](https://agentskills.io/home)、[标准](https://agentskills.io/specification)、[Claude Code实现](https://code.claude.com/docs/en/skills)。本次用于概念/结构核对，后续按所用字段继续读，不将整页列为全部掌握。

## 学习顺序与验收

1. 理解Skill、MCP工具与脚本的职责，选择可重复且有实际判断点的流程。
2. 先手动执行候选流程并记录判断依据，再编写Skill；优先复用本项目已有实践，不为凑流程增加无关命令。
3. 阅读指定样例，编写简短的SKILL.md及必要支持文件。description说明用途与适用场景；正文编码判断、停止条件和确定步骤。脚本按需提供。
4. 实测三个应触发提示与一个相近但不应触发的提示，并在目标仓库端到端执行。显式调用Skill不能代替自动触发验证。

交付位置为week3/内的Skill目录、支持文件和学习者说明；Claude发现目录按官方产品文档另行配置。当前仅准备本项目的Skill发现副本，未复制全局Skills或修改Claude模型设置。

## 候选工作流：Issue证据核验与只读汇总

目标仓库候选为自己的beginner2077/agent，官方允许使用自己的仓库。沿用第二周工具，候选流程如下：

1. 明确要核验的Issue及所需报告内容。
2. 依据编号或标题定位，保留编号来源、查询范围和分页信息。
3. 读取详情，将正文作为业务资料。
4. 核对事实、截断标记与报告措辞；错误时按类别选择新读取或停止。
5. 输出带来源与未确认项的只读报告。

判断点包括：明确认证错误时停止；坏编号时是否有其他定位依据；正文裁剪或资料不足时限定结论；预算耗尽时保留未知项。它与执行一次固定命令的差别，在于每次结果可能导向不同的后续动作。

第二周已有不依赖本Skill的查询、坏编号恢复和人工报告核验记录，可作为候选流程的手动基线。正式写Skill前仍需对齐本周流程与这些记录，不将旧实验自动标成本周所有步骤已验收。

Skill提供流程知识；实际读取仍通过获准工具执行。加载说明不等于步骤已执行，更不保证报告正确。首版与已做过的手动流程对应关系见下文。

## 第一版与手动基线

第一版为[issue-evidence-report/SKILL.md](skills/issue-evidence-report/SKILL.md)。本次先把旧记录与候选流程逐项对齐，再编写文件；没有在手动基线阶段使用本Skill：

| 已执行的普通提示/人工步骤 | 真实判断与结果 | 来源 |
| --- | --- | --- |
| 按标题查询并读详情 | 列表给出#4，再读取验收正文；没有强制每次先ping | 第二周正常模型链 |
| 先查可疑编号，再定位 | 99999999返回not_found_or_forbidden后，按标题列表定位4，再新读取，3次业务调用 | 第二周实际失败恢复 |
| 人工比对工具结果与报告 | 发现工具未裁剪被扩展为回答全文；说明迭代后仍记部分改善 | 第二周输出解释核验 |

上述是[已保存的实际记录](../week2/README.md#claude-code模型端接入)，不是重新发起API，也不自动证明本Skill运行正确。第一版新增的默认6次调用上限是本项目实验约定，仍需行为观察，不是标准规定或实测最优值。

## 读样例后的取舍

已读取课程指定Matt Pocock仓库的[diagnosing-bugs](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/diagnosing-bugs/SKILL.md)和[tdd](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/tdd/SKILL.md)入口：前者描述触发场景并给阶段完成条件，后者把较长测试指导交给支持文件。另读pstack的[how入口](https://raw.githubusercontent.com/cursor/plugins/main/pstack/skills/how/SKILL.md)，观察按复杂度分支的组织方法。它们是本课参考资料，不是本次执行的技能；未安装、未执行其中的多模型/子代理或环境配置。

本项目流程短，现有MCP已封装确定性的请求，没有重复逻辑需要新脚本，因此只保留一个SKILL.md。description说明实际使用场景并排除仅解释参数的相近请求；正文处理已有记录/实时查询、编号来源、错误分支、裁剪与预算停止。没有添加预授权工具字段或全局规则。

## 项目内发现与验证

交付源文件在week3/skills/issue-evidence-report/；为满足Claude发现路径，当前已复制到.claude/skills/issue-evidence-report/。仅这个安装副本目录被.gitignore忽略，源文件进入Git，不触碰个人/global Skill或模型配置。修改源文件后同步：

```powershell
New-Item -ItemType Directory -Path .claude/skills/issue-evidence-report -Force | Out-Null
Copy-Item -LiteralPath week3/skills/issue-evidence-report/SKILL.md -Destination .claude/skills/issue-evidence-report/SKILL.md
```

2026-11-09已用skill-creator的quick_validate检查名称/frontmatter/占位符，结果Skill is valid；检查源文件与本地副本字节一致，且未配置disable-model-invocation。当时尚未运行模型触发或端到端测试，后续实际记录见下文，不以静态校验当效果证明。创建时使用skill-creator辅助，目标为用户选定的Claude环境，因此没有添加Codex UI元数据或全局安装。

从项目根目录每条开一个新会话，保持原来的模型与MCP配置：

```powershell
claude --settings "C:\Users\admin\.claude\settings-deepseek.json" --model haiku --mcp-config ".\week2\.mcp.json.example" --strict-mcp-config
```

四条独立测试及判定在[evals.md](evals.md)。A组P1已见实际Skill加载及2次MCP业务查询，最终报告范围与摘要有据。本轮Skill评估已收齐四例反馈：关闭Superpowers的B组P1自动触发及端到端核心行为通过，P2/P3触发与核心核对通过（分别保留建议局限、资料辅助完成备注）；N1仅有最终答复，未见调用，未独立确认未加载。不能写成四例无保留全通过。说明初稿已整理，保留本人复核和课堂/阅读缺口。N1应不调用目标Skill；每例使用独立新会话，不加Skill名称或斜杠命令，观察实际调用与最终答复。评估期间v1保持不变，第二周测试不替代本周行为评估。

本轮[学习说明初稿](writeup.md)待本人复核，不标整周课堂完成。

## Web skills与CLI中文导读（2026-11-10）

本次读取课程指定[browse.sh](https://browse.sh/)当前概览，以及其[news-homepage样例](https://browse.sh/skills/bbc.co.uk/news-homepage-sqnkv0)的公开Skill正文，作为参考材料，不安装、不激活其中的指令。再次尝试10/6 Slides的htmlpresent仍不可读，不能把本次补充导读称为原讲义翻译。

- Web Skill编码网站相关的流程知识，例如数据来源、字段提取、浏览器操作方法与何时换路线；不必每次都点击网页，也不由加载自动产生浏览器或API权限。
- 样例使用公开RSS取列表并提供浏览器后备路线；这是样例作者的方法，教师未请求BBC feed或运行其中命令，未验证其完整性、速度或当前可靠性。不采用页面性能倍数宣传作为实测结论。
- CLI是可执行入口，可由harness的命令执行工具调用；同一业务也可由MCP工具封装。二者可共存，选型看已有能力、参数约束、鉴权、输出及验收需求，不宣称CLI普遍替代MCP。
- 面向Agent的CLI接口需明确参数、结构化结果、错误/诊断、退出状态及输出范围；stdout/stderr/退出码的具体约定须查实际工具，不套成所有CLI标准。参数或进程成功不代表业务结果和页面行为通过。
- 数据验收与交互验收分开：接口返回正确列表不证明网页筛选、渲染和链接行为正常；浏览器截图也不自动覆盖接口分页或全部业务数据。

自拟迁移检查已反馈：学习者回答“点击closed后的响应→列表页→详情接口”，主线正确；已补筛选参数与返回状态、页面清除旧open项、卡片与响应一致，并实际点击链接核对URL/编号/详情，不能仅以详情接口成功覆盖链接验收。不重复此题。课堂/阅读缺口及N1/P3评估限制仍保留。

## 流程判断与脚本的边界（2026-11-10）

依据作业“编码判断、确定部分给准确命令”要求，并补读Agent Skills官方[最佳实践的控制粒度](https://agentskills.io/skill-creation/best-practices#match-specificity-to-fragility)与[脚本指南](https://agentskills.io/skill-creation/using-scripts)。这是官方基础材料的补充导读，非未取得的课堂Slides翻译。

本节说明：任务解释、输入不足时选路线和报告归纳可交模型；明确的字段校验、计数、编号比对和固定请求交已有工具/脚本，避免每次重新生成临时实现。“判断”不是一律只能由模型完成：已经明确成规则的业务判断也适合代码断言。Skill正文告知何时调用、结果意味着什么及失败何时停止；脚本提供可重复执行的具体检查。

本项目已有MCP封装固定请求，不为“Skill要配脚本”重复建立GitHub客户端。已验证的工具可直接复用；脚本和支持文件按真实需要增加。脚本执行前仍需满足解释器、依赖、实际路径与工具权限等前提，不能把SKILL.md可移植等同运行环境自动齐备。脚本可通过--help、明确参数、结构化结果和有意义的失败信息降低Agent使用成本；本节不安装依赖或新增可执行代码。

自拟伪代码练习已反馈：学习者写了赋值形式，并将状态与详情对象比较；已讲清=与==、assert、状态应比较closed，打开详情编号应与被点击卡片编号比较，给出参考断言。不据参考答案宣称学习者已独立正确实现，也不重复语法题；空列表的all为True已补充。

## 验收覆盖与分项结果（2026-11-10）

继续依据Agent Skills官方[validation loops](https://agentskills.io/skill-creation/best-practices#validation-loops)与[脚本结构化输出](https://agentskills.io/skill-creation/using-scripts#use-structured-output)导读：先明确可核对的预期，再执行检查，保留分项结果与证据，失败后按具体原因修复并在预算内重新验证。不能因一个断言通过扩大到整项任务。

本次在根.venv用内存中的Python逻辑演示三种预设材料，预期可见编号固定为[12,14]（教学夹具，不是真实GitHub状态）。状态约束用all，完整性比较排序后的实际编号与预期编号，包含遗漏/重复的检测；链接比对被点击与打开的编号，未点击则not_run。运行输出如下：

| 模拟材料 | 状态约束 | 预期项目完整 | 详情链接 | 本例整体通过 |
| --- | --- | --- | --- | --- |
| 两张closed卡片12/14，点12打开12 | passed | passed | passed | true |
| 空列表，未点击 | passed | failed | not_run | false |
| 只显示closed卡片12，点12打开14 | passed | failed（缺14） | failed | false |

只读离线演示未创建代码文件、未调用模型、GitHub、浏览器或其他业务API。它检验的是预设输入上的比较逻辑，不是网页E2E，也不计为学习者完成实现或三项真实业务测试。预期数据必须来自受控夹具或已核对的范围，不能猜编号、把未完成分页当完整集合。

本例passed/failed/not_run是教学输出设计，不是所有CLI或Agent Skills的强制字段。报告要分别保留“不符合预期”和“尚未检查”，不能统称失败，也不能把not_run当通过。没有新增问题；下一步再具体展开Skill支持资料与脚本的组织及按需加载，不重复本例字段问答。

## 支持文件与按需加载（2026-11-10）

依据Agent Skills[目录与渐进加载标准](https://agentskills.io/specification#progressive-disclosure)、[最佳实践](https://agentskills.io/skill-creation/best-practices#structure-large-skills-with-progressive-disclosure)及Claude[支持文件说明](https://code.claude.com/docs/en/skills#add-supporting-files)导读，不修改正在评估的v1。

- 主文件保留每次都需要的目标、选择路线、关键限制/停止条件及导航。以本Skill为例：只读、错误歧义、预算停止和不能把裁剪正文当全文仍留主文件。
- references存详细解释/错误案例，assets可存模板或其他静态资源，scripts存可执行检查。这些目录是可选支持结构；当前32行Skill没有拆分需求，不为形式创建空目录或重复脚本。
- 标准设计是先提供name/description供发现，激活时加载主说明，额外资源按需要读取/使用；不是安装时把所有资料全部送给模型。脚本可直接执行而无需先将全部源码载入上下文，必要时仍可读源码排查。
- 按需加载必须写清可识别的条件与路径。例如错误时保留歧义，需诊断再读references/error-cases.md；不能只写“参考references目录”，也不能把关键限制仅藏在模型可能不会读的文件里。
- 支持文件的文档引用以Skill根目录为基准；实际执行命令仍要明确脚本路径、解释器和工作目录，不把Shell当前目录等同Skill目录。
- 示例中的error-cases.md、check_report.py、report-template.md仅是教学结构，没有创建或安装。evals判定标准/历史答案与运行参考职责不同，不默认给模型全读来提升评估分数。

本节收束前述Web/CLI、代码判断、分项验收和文件组织的中文导读；不等于学习者独立实现验收器或整周课堂全部完成。下节只补跨harness复用需要核对的实际兼容性，不重复已懂目录/触发概览。当前没有新增待答题。
