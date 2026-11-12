# 第四周：陌生仓库勘察与CLAUDE.md

当前状态（2026-11-11）：两项用户模型任务与一次指南改进已归档；目标测试及指南修订提交2d8d34f已推自己的fork，目标根目录与[66行课程副本](CLAUDE.md)一致。[writeup事实草稿](writeup.md)已整理，待本人复核；完整CI、修订后模型效果、第四周课堂材料的全部覆盖及正式提交仍未完成。任务1本地935项通过；任务2仅新增一个测试方法，聚焦8项通过，Ruff缺失未完成；其报告范围错误已纠正，不写成所有报告都正确。

## 第四周课堂导读（2026-11-11，继续中）

已通过第三方课程目录找到原始链接，再直接读取[10月13日官方讲义的14页文字与备注](https://docs.google.com/presentation/d/152VaUifBKH4T6hxd6fCKKM9kJTSAuBmkF8zSYwuTYAo/htmlpresent)，封面确认Stanford Fall2026。第三方笔记仅作定位入口，不作为授课内容依据。官网首页可读，但本机HTTP连接超时、网页工具未展开Syllabus，故未宣称重新核完完整官网课表；10月15日客座课材料尚未独立核实。

讲义覆盖：第3—4页API/MCP/Skills比较；第7—8页四种定制方式与仓库规则；第9页Hooks；第10页Skills；第11页Subagents；第12页MCP用途；第13页上下文来源。当前先中文导读四种机制分工，结合已完成任务说明：常驻事实放CLAUDE.md，特定流程放Skill，事件触发的检查交给Hook，独立旁支工作可委派子代理。不是要求全部安装，也不把指南加载等同遵守。

补充核对[Anthropic定制方式说明](https://claude.com/resources/articles/steering-claude-code-skills-hooks-rules-subagents-and-more)与[Hooks指南的机制/事件相关段落](https://code.claude.com/docs/en/hooks-guide)：事件触发与处理器判断分别讨论；命令Hook可执行程序检查，prompt/agent类型仍使用模型判断。PreToolUse在工具前，PostToolUse在成功后，PostToolUseFailure对应失败；后置检查不回滚既有改动。以Ruff缺失说明启动检查失败和代码未通过检查不同，不能靠Hook配置自动消除环境缺口。

已继续核对[Hooks reference](https://code.claude.com/docs/en/hooks)的输入、matcher、PreToolUse决策与退出码段落，中文导读以简化Edit事件串联：harness向command处理器stdin发送JSON，matcher先选工具，脚本再查参数/路径，处理器向stdout返回结构化deny及理由，harness阻止并反馈模型。区分不作决定的exit0与显式allow；PreToolUse可用exit2/stderr阻止，普通检查错误不自动等于阻止，按事件/输出/失败配置判断。示例仅用于接口讲解，不是本机真实Hook日志或配置；匹配Edit/Write不覆盖Bash等写入通道。当前文档所述具体行为未在用户安装版本实测。

子代理核心已继续中文导读，补充核对[官方subagents文档](https://code.claude.com/docs/en/sub-agents)的启动上下文、工作目录和链式委派段落：普通新子代理依据委派消息工作，不能默认继承全部对话；fork是需分别讨论的例外。交接应含目标、准确目录/文件状态、范围/工具限制和返回证据。以只读调查聚焦测试是否附带doctest为自拟案例，返回结论、代码位置、是否实际执行及未确认项；主代理仍需核对是否适用于当前修改后的文件。上下文隔离不等于文件隔离，worktree仍需核对起点/未提交修改/外部共享资源；planner→implementer→reviewer通常有依赖，不应机械全并行，也不因角色名就赋予写权限或保证独立正确。未运行真实委派或设置模型。

四机制综合设计已导读：按问题选择机制，规则文件记录稳定事实与入口，Skill组织反复出现的流程，Hook触发合适范围的检查，子代理承担可独立验收的旁支。自拟工作流以修改→格式化→测试→只读审查→核对diff/报告串联，检查结果绑定文件状态；工具缺失保留未验证项，不擅自安装。命令和格式规则优先复用仓库现有Makefile/pyproject等来源，避免在规则/Skill/Hook中维护多套不同标准；不是要求当前仓库增加这些配置。补充核对best-practices的模型指令与harness执行、检查与边界相关段落。

综合题已收到学习者反馈：提出集中修改后再测试，方向合理；备选每次Edit新建子代理/worktree仍重复执行，且新worktree不自动携带未提交改动，已说明需绑定正确快照，失败后先修复复测，独立只读审查可考虑并行。本题为设计讨论，未开展真实并行或隔离实验，不标独立完整设计通过。

指定阅读[I Still Prefer MCP Over Skills](https://david.coffee/i-still-prefer-mcp-over-skills/)已读取网页文字，下一段中文导读重点是外部连接与流程知识的分工、远程部署/授权/升级的维护责任，以及Skill组合MCP的方案。以本项目stdio GitHub MCP和issue-evidence-report对照，区分已实现的服务端约束与提示规则。作者的远程MCP便利性是取舍观点，不将所有MCP等同零安装、自动OAuth、安全隔离或自动升级。补充核对[MCP 2025-11-25授权规范的范围](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)：客户端到HTTP MCP的授权与本项目server到GitHub的OAuth分别讨论，不将该规范冒充当前会话协商版本。

Factory指定阅读旧路径不可读，已定位并读取[当前AGENTS.md文档](https://docs.factory.com/harness/agents-md)，本节中文导读其可迁移原则：准确命令、可核验完成条件、生成目录边界、仅有真实差异才设嵌套规则，不复制多份同义入口。具体文件名兼容、发现触发和优先级是Droid行为，不跨客户端直接套用。对照[Claude memory官方文档](https://code.claude.com/docs/en/memory)的加载与AGENTS章节：CLAUDE文件内容会合并进上下文，不能把局部规则理解为删除上层文本；当前AGENTS原生支持也有版本/设置条件，不作“Claude永远不读AGENTS”的旧断言。文字加载、模型采纳与权限执行分别讨论；未检查或改变本机对应设置，也未创建嵌套文件。本项目现有66行单文件继续保留。下一步核对课堂上下文汇合图及本周覆盖清单；14页视觉布局、现场演示、链接示例与10/15客座来源仍未完整核对，不标整周完成。未创建Hook、安装依赖、启动子代理或调用模型。

上下文汇合导读：围绕此前已读第13页“The context story”来源清单，结合[Claude工作机制文档](https://code.claude.com/docs/en/how-claude-code-works)的上下文/工具循环段落作中文流程解释；示意不冒充原图视觉或当前实际HTTP请求。区分可访问文件与已送入模型的内容、工具定义与执行结果、Skill发现元数据与正文、Hook程序/权限配置与注入的反馈、子代理独立上下文与主会话接收的摘要。来源分类不等同role或固定字段位置，需实际抓包核对；历史保留不代表重新执行，磁盘变化不等自动同步已读快照。本轮重开Google讲义失败，未声称新增视觉核对。下一步优先核对10/15客座材料可用性与第四周覆盖边界，再决定后续安排；不重复测试或代填个人writeup。

### 本周收束：评价和维护定制

2026-11-11再次核对官网公开入口并按讲者、课程和日期检索，未取得可核验的10/15 Boris Cherny客座原始讲义或完整录像。第三方目录资源空缺及10/22摘要只能作为查找线索，不能证明官方未发布；摘要所链X页面本轮403。保留客座课缺口，不用其他访谈补成已读课程。

本节是依据已读材料和实际练习作的教学综合，不冒充客座讲义：评价定制时同时看任务正确性、实际成本和边界；加载/触发仅证明机制发生。已知Ruff缺失时，每次Edit继续启动它并不会得到格式检查结果；改善应考虑合并编辑后按阶段检查、明确运行前提，再衡量漏检和反馈延迟。规则修订先保留可检验的目标，选择同类任务和相近文件状态比较，每次调整一个主要因素；不能用两次不同任务或单次成功证明改善由规则导致。

维护时区分有效事实、流程指令和已失效的补丁：环境、命令、工具或模型变化后重新核对规则；临时故障不自动变成永久约束。当前66行指南未再改动，未新增Hook、实验或模型请求。接续综合迁移问题：一条要求每次Edit后跑全套测试的旧规则，在拆成多次Edit但最后聚焦测试通过的任务中，如何分别评价规则遵循与工程方案，并决定保留/修改哪一层。尚未收到本题回答，不标独立掌握。

综合迁移题反馈：学习者指出未逐次测试即未完全遵循，合并可能合理优化，报告应注明。判断核心正确；补充不能从日志推断优化动机，披露不代替遵循，聚焦测试不自动替代全套要求；历史执行无法补造，但可补当前必要验证后如实收尾。本题已答并反馈，不继续记为待答或完整独立设计验收。主线转第五周，客座/视觉/演示及其他原有缺口保留。

## 官方目标与边界

依据[本地官方作业](../course-assignments/week4/assignment.md)与[远端官方作业](https://github.com/mihail911/modern-software-dev-assignments/blob/master/week4/assignment.md)：选择陌生且非本人编写的开源仓库，fork后查清实际结构/命令/约定/生成目录，写一页左右AGENTS.md或CLAUDE.md，再观察两项小任务并提出有依据的改进。本项目继续Claude路线，优先CLAUDE.md。

本轮使用project-agent-bootstrap的先证据后规则核对方法；课程的单文件目标优先，不扩展成通用docs路由/知识卡体系。ponytail保持最小完整范围。不关联用户无关业务项目资料，不读取Codex源码，不照搬其他项目规则；目标上游的贡献约定仅用于判断选型与后续边界。

## 选型

- 官方候选TheAlgorithms/Python的当前远端pyproject声明requires-python>=3.15；本机根.venv实际Python3.12.14。为避免本周围绕运行时升级和大批依赖展开，未选该候选。
- 也只读考察yt-dlp的元数据和贡献说明，发现其上游明确不接收AI贡献，不选为本次练习目标；没有向其提交Issue、PR或修改。
- 课程允许自选非本人编写项目，因此选[more-itertools](https://github.com/more-itertools/more-itertools)：迭代工具库，源码和测试职责清楚，声明Python>=3.11。本机公开API根目录清单未见AGENTS.md/CLAUDE.md，仅确认根目录，不推断整个树没有子目录规则。
- 没有可用GitHub专用连接器或gh命令；现阶段用公开网页/只读HTTP核对。后续fork操作的方式另按实际工具确定，不用第二周固定agent仓库MCP假装能访问任意仓库。

## 初查证据与待验证项

来源为远端master公开文件，网页缓存时间不一；正式勘察要在fork的固定commit上再次核对，不能把这些页面当同一次完整快照。

| 观察 | 依据 | 当前层级 |
| --- | --- | --- |
| 是Python迭代工具库 | README.rst；more_itertools/__init__.py导出more与recipes | 远端资料/源码观察，非运行 |
| requires-python>=3.11 | pyproject.toml | 声明要求，本机3.12仅版本层面符合 |
| 测试入口使用unittest | tox.ini的{envpython} -m unittest -v；Makefile test目标 | 配置约定，尚未执行 |
| 格式行宽79，format保留引号风格 | pyproject.toml的tool.ruff | 声明约定，不凭通用习惯填88或统一单引号 |
| Makefile check含ruff及stubtest | Makefile | 有对应检查，不声称本机已装好或全部检查通过 |
| 文档构建输出docs/_build/html | Makefile docs目标及pyproject打包排除 | 生成目录线索，本地固定版本再核 |
| 版本配置及mypy检查存在 | setup.cfg | 只读到对应配置，未将其中命令当本轮执行指令 |

已读范围：远端README、pyproject、tox.ini、Makefile、setup.cfg、包__init__、空tests/__init__与根目录名。猜测.github/workflows/tests.yml未读到；CI文件路径、全部入口/调用关系、测试约定、完整生成/第三方目录和有效范围内已有Agent规则仍需精确发现，不能猜CI命令。

公开源：
- [pyproject.toml](https://github.com/more-itertools/more-itertools/blob/master/pyproject.toml)
- [tox.ini](https://github.com/more-itertools/more-itertools/blob/master/tox.ini)
- [Makefile](https://github.com/more-itertools/more-itertools/blob/master/Makefile)
- [包导出](https://github.com/more-itertools/more-itertools/blob/master/more_itertools/__init__.py)

## 教学步骤

1. 本次：区分项目形态、运行前提、配置中的命令和已实测结果。README带路，配置确认，CI进一步核对，实际运行提供执行证据。
2. 下一步：创建自己的fork、建立隔离本地checkout并固定commit；先读现有规则、工作树状态和相关证据，不一次性加载全部源码或docs。
3. 在目标环境验证准确命令，记录错误/输出和范围，整理一页CLAUDE.md；新文件按既有Git偏好纳管，课程阶段完成再commit/push。
4. 再让用户的Claude+DeepSeek运行两项明确小任务，核对是否使用说明中的命令和约定，基于观察做一次有依据的改进。教师自己的命令执行不能冒充学习者模型行为证据。

## 固定版本勘察与测试基线（2026-11-11）

- fork：<https://github.com/beginner2077/more-itertools>，API返回202及`fork=true`、父仓库`more-itertools/more-itertools`，随后成功克隆，提交号为上述基线。
- 本地路径：`.tools/course-repos/more-itertools/`，处于学习仓库忽略目录，拥有独立Git历史；`origin`指向自己的fork，`upstream`指向上游。只设置该副本的本地Git身份，未修改全局身份。
- 浏览器操作通道不可用，改用已有Git凭据管理器提供的认证核对账号并创建fork；凭据只在进程内存中使用，未输出或写入文件。未扩展第二周GitHub App授权。
- `git ls-files`检查未发现目标版本中的AGENTS.md或CLAUDE.md；检查前后`git status --porcelain`均为空。环境目录`.venv/`由目标自己的.gitignore忽略。
- 远端初查曾读到版本11.1.0；固定版本实际为11.2.1。这是重新核对基线的具体理由，不把网页缓存与本次源码混为同一快照。

在目标仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

实际结果：退出码0，`Ran 935 tests in 12.861s`，`OK`。环境由学习仓库Python3.12.14创建，未安装目标开发依赖或editable包；从仓库根目录导入的`more_itertools.__file__`指向本地源码。完整输出在本机忽略目录`.tools/course-repos/more-itertools-unittest-baseline.log`。此结果仅对应本次版本和解释器，不是多版本矩阵或CI全通过。

固定版本新增确认：

| 事实 | 依据 | 对规则文件的作用 |
| --- | --- | --- |
| CI实际入口为`.github/workflows/python-app.yml` | 工作流文件 | 不猜测tests.yml；CI运行coverage，3.11还执行静态检查、文档及打包 |
| 覆盖率门槛99% | Makefile的coverage目标 | unittest成功不等于覆盖率达到门槛 |
| 测试包含源码doctest | tests/test_more.py:44及tests/test_recipes.py:24的load_tests | 保留官方unittest入口；换测试发现方式可能改变覆盖范围 |
| 测试通过`import more_itertools as mi`调用公共接口 | 两份测试文件 | 涉及公共行为的任务需关注包导出，而非只看内部函数 |
| 源码旁有同名.pyi及py.typed | more_itertools目录 | 签名变化时核对类型声明；.pyi是受版本管理的源码，不是可随意删除的生成物 |
| 生成输出包括docs/_build、dist、build及覆盖率产物 | .gitignore、Makefile、pyproject | 后续规则需区分可编辑源码与生成结果 |

尚未执行：coverage及99%门槛检查、Ruff、stubtest、Sphinx构建、打包、多Python版本测试。尚未安装对应工具，不把命令存在写成验证通过。未向目标fork推送源码改动，未向上游发送Issue、PR或评论。

本节学习点：把“源码里看到了什么”“命令实际验证了什么”“哪些检查仍未做”分开，再把高价值、仓库特有的事实压缩为常驻规则。

## 指定阅读与CLAUDE.md第一版（2026-11-11）

已实际读取以下网页相关正文，未执行其中建议的产品功能或将示例当成本项目命令：

- [AGENTS.md格式](https://agents.md/)：普通Markdown，无强制字段；用于补充面向Agent的项目上下文。选择CLAUDE.md是当前客户端路线，不意味着两种文件在所有客户端中都有相同加载规则。
- [Writing a good CLAUDE.md](https://www.hlyr.dev/blog/writing-a-good-claude-md)：用途、定位与工作方法；简短、渐进披露、指向事实来源，格式检查交给工具。文章发表于2025年，其默认注入描述、指令数量经验值及对Skill的概括不作为本机协议事实或普遍上限。
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)：本次聚焦Keep CLAUDE.md short、可执行检查及模型指令与客户端约束的区别，未宣称整页所有功能均已导读/实测。当前官方允许/init生成初稿后删减，HumanLayer反对直接自动生成；二者取向不同。本课根据固定版本证据逐条编写，不把/init当必需或禁止命令。

当前常驻文件的范围：项目用途、公共导出/类型接口、目录定位、Windows虚拟环境的具体命令、unittest/doctest约定、迭代器消费时的断言、格式配置和生成目录边界。详细流程仍指向已有Makefile、工作流、源码与README，不建立另一套文档体系。

有意不写入：935项通过的历史结果、学习轨迹、完整API目录、通用编码口号、无关业务规范、凭据、本机绝对路径和全仓源码摘录。本次任务边界仍由具体提示提供；文件中的文字不构成客户端权限控制或测试必定执行的保证。

初稿共64行，目标根目录CLAUDE.md与week4/CLAUDE.md逐字节一致，SHA256=`23c424497a7532a2eb233db318221738c0841ff60824cf2d8823cfcda5c8db94`。目标副本只新增该文件，未改源码、测试、构建和CI配置；Markdown差异检查通过。除已实跑的全部unittest命令外，新增列出的聚焦、工具安装、静态检查、覆盖率、文档、打包及示例命令属于据仓库配置整理的命令，尚未在本环境逐项执行；使用`python -m`是为明确使用同一虚拟环境。未因文档变更重复全套测试。

初稿已单独提交并推送到自己的fork：`2a58f3f19b1cc7b962fd93a8b95ff9773a1fd1b5`，`docs:添加第四周仓库工作指南初稿`。此提交仅新增CLAUDE.md，用于固定两项任务之前的版本，后续改进可与之比较；不改上游，不把这次文档提交说成重新测试。

初稿完成时的安排：让用户Claude+DeepSeek先完成一项测试与解释任务，随后一项小改动，再据观察改进文件。该阶段尚无效果日志；后续证据见下方任务记录，不宣称优于无文件对照。正式writeup仍待两项观察及本人复核。

当前没有新增待答题，不标作业完成，不向上游提交贡献或自动添加课程协作者/提交Gradescope。前面的选型及远端初查段落为历史阶段，当前状态以本节为准。

## Part III任务1：提示与执行前提

开始前核对：目标HEAD仍为`2a58f3f`，工作树干净。用户级Superpowers为true，学习仓库局部为false，而目标副本此前没有局部设置；因此在目标`.claude/settings.local.json`仅写入同一插件的false覆盖，并在目标`.git/info/exclude`中忽略这个准确路径，延续学习者的局部禁用偏好。未修改命名DeepSeek配置、认证、模型映射或全局设置；不把配置文件已写入当作运行时插件状态验证。

在目标目录新开会话，不恢复旧对话：

```powershell
Set-Location -LiteralPath 'D:\pycharm\PyCharm 2026.2.4\workplace\agent\.tools\course-repos\more-itertools'
claude --settings "C:\Users\admin\.claude\settings-deepseek.json" --model haiku --strict-mcp-config
```

可先用`/context all`查看Memory files中的实际加载条目；这是当前官方memory文档推荐的核对方法，不把`/memory`中潜在路径列表等同于已加载。此处未替用户启动模型请求，也未要求代理抓取。

任务提示（刻意不提供标准命令、测试数量或预期结果）：

```text
在当前more-itertools仓库完成一次只读测试核验。

找到项目推荐的完整测试入口，使用本地已有虚拟环境执行。
结合实际测试加载代码，解释这次测试是否包含源码中的doctest示例。
最后报告：被测提交号、实际命令、测试结果，以及这些结果是否足以证明CI全部通过。

不要新增或修改源码、测试、文档和配置，不安装依赖，不提交或推送。
如果缺少运行条件或测试失败，报告实际问题，不修改文件或环境来修复。
只核验当前仓库，不读取父目录的学习记录或其他项目资料。
```

观察点：实际加载路径与行为分开记录；工具调用中的解释器/工作目录/命令、实际结果、doctest解释及CI结论均需核对。与文件一致不能证明行为仅由CLAUDE.md造成，也不能证明优于无文件。不按一次任务说明单独commit。

### 用户实际记录与反馈（2026-11-11）

证据为学习者粘贴的Claude输出，最终报告时间11:51。教师本轮只核对本地对应源码、工作流与Git状态，没有代跑测试或另发模型请求。

| 核对项 | 用户提供的实际证据 | 判断 |
| --- | --- | --- |
| 客户端纳入文件 | `/context all`显示Memory files下CLAUDE.md约890tokens；Skills列表为Built-in，未出现Superpowers条目 | 已观察到客户端报告加载；不能由此推断逐条遵循或服务端内部处理 |
| 版本和环境 | 实际Bash读取HEAD=2a58f3f19b1cc7b962fd93a8b95ff9773a1fd1b5，Python3.12.14，运行前后git status无输出 | 被测版本与独立环境可核对，Git工作树干净 |
| 测试入口 | `./.venv/Scripts/python.exe -m unittest -v`，输出重定向到mktemp临时文件，保存退出码 | 与初稿命令一致，没有把最终报告中的命令当执行证据 |
| 测试结果 | EXIT_CODE=0；日志统计显示Ran 935 tests in 12.227s、OK | 用户本次运行通过，与教师基线耗时分开记录 |
| doctest | 实际日志计数164，其中more114、recipes50；对应两个load_tests加入DocTestSuite的代码 | 包含这两个实现模块收集到的doctest，计数不是>>>示例行数 |
| 报告范围 | 最终明确不能证明完整CI通过，列出矩阵/coverage99%/静态检查/文档/打包未运行 | 核心边界正确 |

任务1核心要求通过：实际行为与初稿中的测试入口、已有虚拟环境和检查结果分开报告的约定一致。未看到安装依赖、修改源码、提交推送或Skill调用；不推广为所有未来任务都遵循，也不把符合行为归因于文件的独立因果效果。

两点精度反馈：

1. 最终表格“测试后文件改动：无”应收窄为“Git工作树干净，未见源码/测试/配置变更”。mktemp日志已实际写入，Python也可能产生忽略的缓存；git status不证明整个文件系统零写入。这不构成本题禁止修改源码/测试/文档/配置的违反。
2. 第一次普通测试统计为644，后按完整ok输出与doctest区分得到771，且771+164=935，最终报告已修正。它是输出统计修正，不是测试失败后的代码修复。grep定位>>>仅是辅助，收集与运行仍要以load_tests和测试日志为据。

观察到额外数轮统计命令；本题核心其实不要求精确拆分普通用例和doctest数量。候选改进是让指南更清楚地引导依据测试加载与汇总判断覆盖范围，避免将示例行数当用例数；暂不修改64行初稿，待第二项任务后综合选择一次有依据的改进。

下一步：安排第二项小改动，观察测试代码风格、改动边界和聚焦验证；当前不把整周或Part III标为全部完成。

## Part III任务2：提示与执行前提

教师已检查当前ChunkedTests全部方法及chunked实现，目标HEAD仍为2a58f3f、工作树干净。现有strict测试用list一次性消费并断言异常，未单独保护不完整尾组之前的完整分组能够依次返回。新增用例可防止未来将异常提前到创建迭代器时；这是现有行为的保护，不要求制造失败或修改实现。

在同一目标目录用原命令新开Claude会话，避免沿用任务1的只读任务限制；保留原命名配置、haiku映射、strict-mcp-config及已设置的局部插件禁用。可再次用/context all核对CLAUDE.md条目，不把任务1的加载记录外推为新会话事实。

给模型的提示不提供测试代码、类名或准确测试命令，让它结合仓库上下文完成：

```text
在当前more-itertools仓库，为chunked的strict=True行为补充一个测试。

使用range(5)作为输入，每组大小为2。新用例需验证：
1. 创建分块迭代器时不因最后一组不足而报错。
2. 前两次取值依次得到[0, 1]和[2, 3]。
3. 再次取值时抛出ValueError，而不是返回不足一组的[4]。

只允许在tests/test_more.py中新增一个测试方法，不改已有测试或其他文件。
沿用项目现有测试约定，完成后运行与改动对应的聚焦测试。
不要安装依赖，不提交或推送，不修改CLAUDE.md或配置，不读取父目录学习记录。
如果无法在允许范围内完成，报告实际原因，不扩大修改范围。

最后展示实际diff、执行的测试命令和结果，并说明验证范围。
```

观察点：是否放入已有的对应测试类，使用公共包入口及unittest断言；是否在消费时捕获异常；是否选择指南中的聚焦命令或合理等价命令；实际diff是否仅一个新增方法，是否如实说明验证范围。不要求原有测试先失败，不因该任务要求Ruff等未安装工具而扩展安装。

以上为执行前安排：教师没有提前写入测试或代跑模型任务，两项观察均针对64行初稿进行；后续结果与修订见下方。

### 用户实际记录与反馈（2026-11-11）

证据为学习者粘贴的实际Update、Bash、diff与13:58最终报告。本次任务结束时，HEAD仍为2a58f3f，工作树仅tests/test_more.py新增14行。教师随后只读核对diff与AST：去掉新增方法后，AST与HEAD原文件一致，既有代码未改变；未重跑模型的测试或安装工具。

| 核对项 | 实际记录 | 判断 |
| --- | --- | --- |
| 修改范围 | ChunkedTests新增test_strict_being_true_defers_error，14行，其他源码/旧测试不变 | 满足单方法、单文件边界 |
| 测试风格 | mi.chunked、self.assertEqual、self.assertRaisesRegex | 沿用公共入口及unittest约定 |
| 断言行为 | 构造后两次next取得[0,1]和[2,3]，第三次next在异常上下文内 | 覆盖要求的异常时序；构造处若提前异常会使测试报错，无需额外“未抛错”断言 |
| 实际验证 | ./.venv/Scripts/python.exe -m unittest -v tests.test_more.ChunkedTests；Ran 8 tests in 0.001s，OK | 整个ChunkedTests通过，不是只跑新增方法 |
| 静态检查 | ruff format --check tests/test_more.py启动失败，No module named ruff，退出1 | 缺工具，不是风格不合格；同一命令&&之后的ruff check未执行 |
| 约束遵守 | 记录未见安装、源码修改、CLAUDE修改、提交或推送 | 符合本次模型任务边界 |

评价：测试代码与聚焦验证的核心要求通过，最终报告范围有一处错误，不能记为报告完全正确。输出明确包含test_none、test_strict_false、test_strict_being_true_with_size_none等既有用例，报告却将strict=False和n=None作为“未覆盖”；准确表述应为“ChunkedTests的8项方法已执行通过；其他测试类、源码doctest、全套回归、覆盖率与其他CI检查本次未验证”。不能用任务1改动前的935项结果证明新增测试后完整套件已通过。

任务2未提供新的/context all记录，因此不单独宣称已验证新会话自动加载；仅记录它的实际行为与初稿相关约定一致。重复粘贴的Update/Bash片段不作为多次实际执行的证明，也不读取或采纳模型思考文本来补实际调用证据。

### 根据观察完成一次指南修订

两项模型任务结束后，教师新增一段针对当前仓库的范围说明：

> 聚焦范围按实际类/模块报告：上述类命令运行整个ChunkedTests（包括既有用例），不执行模块级load_tests()，不含额外注册的源码doctest；模块命令会加载对应doctest。

依据：任务1展示模块级load_tests加入源码doctest，任务2的类级命令运行8项但报告漏算既有场景。该差异符合[Python官方TestLoader说明](https://docs.python.org/3.12/library/unittest.html#unittest.TestLoader.loadTestsFromName)与[load_tests协议](https://docs.python.org/3.12/library/unittest.html#load-tests-protocol)。改进集中在仓库的测试范围，未增加通用口号、Hook、权限规则或工具依赖。

修订版66行，目标根目录与week4/CLAUDE.md同步；初稿仍可从fork提交2a58f3f取回。指南修订发生在模型任务之后，不属于模型任务2的文件改动，不能倒写成模型违反单文件约束。仅检查Markdown差异、路径与副本一致性，不因文档改动重复8项或935项测试，也不声称修订后的模型效果已验证。

以上为观察完成时状态；后续归档见下节，不向上游创建贡献，不标整周或正式提交完成。

## 作业练习阶段归档（2026-11-11）

两项试用和一次指南改进合并为一个有意义的阶段归档：目标fork提交`2d8d34fdf9880418ea40ed7532b0787f7cf1edff`，`test:补充分块异常时序测试并明确验证范围`，两文件新增16行（测试14行、指南2行），已推origin/master。没有再次修改或重跑已通过的测试；结果仍引用学习者的实际执行日志，不把提交动作当作新验证。

课程交付副本、[事实writeup](writeup.md)与上述观察一并整理到学习仓库。主观个人体会仍由本人复核，不冒充学习者独立作答。局部插件设置、虚拟环境、临时日志不上传；未添加上游协作者、提交课程平台或发出上游Issue/PR。

本阶段可迁移的方法：先用固定版本确定事实，再把反复有用的知识写成简短常驻上下文；用实际任务观察加载、工具行为与最终报告，分别评价；依据真实缺口修改规则，并保留尚未验证的范围。成功执行和准确报告都要核对，不能互相替代。

下一步先核对第四周官网课堂材料与当前作业的覆盖关系，补讲未导读的核心内容，再决定进入后续专题；不因作业交付文件齐备就默认整周已完成。

停止与异步检查补充（2026-11-12）：据当前[Hooks reference](https://code.claude.com/docs/en/hooks#stop)补Stop事件/阻止结束与反馈、stop_hook_active的含义；command Hook可自己执行检查，模型tool_use并非所有本机执行的完整记录。复用验证必须绑定相关输入状态、命令、范围与环境，不能把旧935项全套自动更新为新增后的完整验证。[异步Hook](https://code.claude.com/docs/en/hooks#run-hooks-in-the-background)启动后不等待、普通结果下一轮投递，不能事后阻止动作；每次触发可能形成独立检查进程。固定快照下迟到结果归原状态，同键去重/合并最新待测状态是教师设计分析，不宣称ClaudeCode内置或本机已启用。三节仅机制补充，无Hook安装、执行或性能实验，不补齐课堂视觉/演示和正式作业缺口；此分支收束。
