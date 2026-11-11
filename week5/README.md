# 第五周：Agent-Ready Codebases

当前状态（2026-11-11）：课堂可读文字核心已导读。用户暂不使用Factory，人工三仓库对比已核对第一项测试入口；用户随后反馈当前内容收益低，现压缩并停止继续展开比较，主线转Agent代码审查。保留现有证据，不安装/登录Droid或编造成熟度；官方三份Factory报告及人工完整比较均未完成，不能标整周作业完成。

## 已读取的原始材料

- [10/20官方讲义](https://docs.google.com/presentation/d/1yCxocmUrGIN7IrC42WB6NW08PtYYFLe1ombDj3Ay6_8/htmlpresent)：15页网页文字及备注，封面Fall2026。第三方目录仅用于发现原始链接；没有完成页面视觉核对、课堂录像或现场演示。
- [官方第五周作业](../course-assignments/week5/assignment.md)及writeup模板，远端master同路径已核对：三个有差异的仓库，运行Droid /readiness-report，保留原始报告并比较八个维度、成熟度、阻塞项及修复建议；分析占60分，三个样本不支持宽泛因果结论。
- [Factory指定阅读](https://factory.com/news/agent-readiness)：网页当前正文已读，八维度/五等级及评分说明已定位，尚未全部中文导读。不把厂商的能力或效果主张当作本项目实测。
- 讲义所列[Making Codebases Agent Ready视频](https://www.youtube.com/watch?v=ShuJ_CN6zr4)未取得正文/字幕；[Making Ergonomic Repositories](https://x.com/trybasis/status/2056881705269580023)本轮403，不宣称已读。

## 首节导读与当前断点

从第四周传递项目知识，推进到第五周检查环境是否支持实际执行和验证。讲义第5—8页讨论测试不足、过期文档、不可靠构建、复杂启动、观测与约定等阻塞；不能一律归因于模型。

结合第四周真实Ruff缺失作教学分析：项目有配置/命令、当前环境安装工具、实际检查成功是不同层次。该次任务明确不安装依赖，因此缺Ruff不能直接证明仓库没有配置或依赖声明，也不能要求模型违反任务约束安装。若目标转为新环境可复现检查，应先核对开发依赖声明、安装入口、解释器与检查命令，再选择最小修复，不用更多提示词掩盖运行前提。

## 八维度、等级与评分适用性

按官方作业与指定文章的八维度作中文教学归纳：风格/静态校验、构建、测试、文档、开发环境、代码质量、可观测性、安全与治理；用此前Python库和MCP案例解释职责，不冒充正式逐项评分。五级Functional/Documented/Standardized/Optimized/Autonomous是框架成熟度分类，不是模型任务成功率或执行授权。

版本差异已核对：[当前产品概览](https://docs.factory.com/agent-readiness/overview)列九维度，新增/调整分类涉及Task Discovery和Product & Experimentation，且不再单列旧版Code Quality；[产品页面](https://factory.com/product/agent-readiness)仍写八维度但包含Task Discovery，与课程版本也不同。不得将当前分类静默替换作业；实际报告保留原始类别、工具版本、仓库提交/环境和评估时间，再说明与作业的映射。指定文章的等级门槛措辞与当前概览也有差异，本节只教分层解锁，不用总通过率推定等级，不凭文字自行重算。

[报告命令文档](https://docs.factory.com/agent-readiness/readiness-report)已读：子应用维度的3/4可表示四个被评估应用中三个通过，不是模型成功率；运行报告会存储到Factory，不是纯本地离线评分。报告生成与自动修复是不同操作，本轮均未执行。

评分的解释边界：配置存在不等实际执行，文件新近修改不等内容准确；按项目类型核对不适用/跳过/失败的理由，不能把纯库缺少Web健康端点机械列为优先修复；分数不是实际任务成功率。先围绕目标任务找最小有效修复，不为提高分数增加无关基础设施。

环境阻塞优先级题已答：学习者选择先处理依赖，因为开发需要环境支持。方向合理；已补具体任务阻塞、区分声明/安装文档/解释器原因，以及新隔离环境按公开步骤成功运行测试的验收。不是所有环境项无条件优先，也未实施修复。

## 横向比较与证据质量

已读[Factory公开GitHub CLI报告](https://factory.com/agent-readiness/cli_cli)作为报告阅读示范，不是本机评分、上游源码审计或本次运行结果：devcontainer配置被判存在，但可运行性因缺CLI跳过；某些安全项因缺管理员API权限跳过。报告的unit_tests_runnable理由包括命令文档和发现测试，不能因此转述为完整套件实际通过。保留原始标签，同时检查每项解释能证明到哪一层。

三仓库比较先记录提交/工作树、工具/框架及评估时间、环境/权限/检查范围。失败、不适用、因条件不足未验证分别解释；不擅自改变工具原始分数，但附分析列，不把未验证自动记为缺陷。通过率分母与应用范围不同时，不能只比较百分比判断优劣。

官方Part II要求寻找共同问题、解释差异、选择每仓最低成本高收益修复并批评框架。三个有差异样本可提出假设，不能把语言、规模、维护者等同时变化归因为单一因素；没有看到某配置不是直接证明实际能力缺失。改进优先级以实际任务阻塞/影响/成本及可验证结果为依据，区别自动报告建议和本人判断。教学示例均非三个仓库的实际报告，不填造writeup数据。

## 后台工作流与隔离

依据此前成功读取的10/20第11—15页文字/备注继续中文导读，本轮重开讲义失败，没有新增视觉核对。后台执行改变等待方式，子代理改变任务委派，两者不是同义词；后台任务需有明确起点、可重建环境、检查入口与可取回结果。讲义的生产率数字未在本项目验证，不用来估算用户收益。

区分会话上下文、源码工作树、运行依赖/进程，以及数据库/端口/外部账号等资源。[Git官方worktree说明](https://git-scm.com/docs/git-worktree)确认linked worktree按提交检出，HEAD/index等独立但仍共享仓库部分状态；不自动复制父目录未提交修改或提供安全沙箱。已知旧知识简略衔接，新增重点是后台可重建与集成结果：分支A/B各自通过，不代表合并后通过，最终按集成状态做必要检查，避免把它当成无意义重复。

讲义中的hermetic build补充参考[Bazel官方概念](https://bazel.build/basics/hermeticity)：工具/依赖等输入受控，隔离宿主机隐含依赖，以同输入得到一致输出为目标；独立venv或容器不是自动成立的证明。无需给当前小库引入Bazel。教学假设示例为A重命名函数并修既有调用、B在旧基线新增旧名调用；两边各自通过仍可能在集成后失败，非本地已发生故障。云Agent/编排工具可接管环境创建与调度，仍需核对结果/边界，不为当前练习新增平台或启动代理。

10/20讲义可读文字的主要概念已分节导读，行政内容压缩，效率主张不作效果证明；视觉、视频、现场DEMO/链接工具及10/22客座另保留范围。不把课堂导读记成作业完成。

## 适配练习：三仓库人工证据对比

选择more-itertools、htmx、Slidev，对比Python工具库、JavaScript浏览器库与TypeScript多包项目。公开GitHub API核对默认分支、提交及仓库创建时间；创建时间不是项目起源，API size含Git仓库数据也不是当前源码行数，不将其直接当作代码规模。

| 仓库 | 固定提交 | GitHub仓库创建年份 | 本轮读取的第一条验证链 |
| --- | --- | --- | --- |
| more-itertools/more-itertools | ceafee8ce96f4bc1eb74c528bc247c91d648a0bb | 2012 | Makefile test目标调用python -m unittest -v；check/coverage/docs/package另有目标 |
| bigskysoftware/htmx | fa978b24e75fb03c137bf2cdae4fef0e711cf8a1 | 2020 | package.json的test串联lint、types-check和test:chrome；后者先playwright install chromium再运行浏览器测试，test:ci另含多浏览器 |
| slidevjs/slidev | 437f139ccd4c8482a193b217922e7800a5b3baec | 2021 | package.json test为vitest test；verify串联build/typecheck/lint/test，CONTRIBUTING明确workspace包需先构建dist |

固定版本原始依据：[more-itertools Makefile](https://github.com/more-itertools/more-itertools/blob/ceafee8ce96f4bc1eb74c528bc247c91d648a0bb/Makefile)、[htmx package.json](https://github.com/bigskysoftware/htmx/blob/fa978b24e75fb03c137bf2cdae4fef0e711cf8a1/package.json)、[Slidev package.json](https://github.com/slidevjs/slidev/blob/437f139ccd4c8482a193b217922e7800a5b3baec/package.json)与[CONTRIBUTING](https://github.com/slidevjs/slidev/blob/437f139ccd4c8482a193b217922e7800a5b3baec/CONTRIBUTING.md)。此前浮动分支文件已再用这些提交读取确认，不混为同一抓取。

本地准备：独立上游副本.tools/course-repos/week5-more-itertools克隆成功，HEAD=ceafee8、工作树干净、39个受Git跟踪文件，不复用第四周含自写指南/测试的fork。htmx/Slidev浅克隆无下载进展，经核对命令行只终止本轮对应两个clone进程树，未清理或覆盖目录；两者仅有不完整.git目录，不能当完整checkout，后续改读固定提交公开文件。网络原因未确诊，不归咎代码或Agent准备度。没有运行测试、项目安装脚本、依赖安装、提交上游修改或读取凭据。未运行Droid或模型请求。

第一项结论：测试入口名称不是检查范围；先读脚本展开、前置依赖和贡献说明，不能把三个test都当同等完整验证。配置/文档观察不等执行成功，htmx的测试命令还可触发浏览器安装。原拟继续CI与前置核对，现按用户收益反馈停止深入，不再等克隆/安装或凑三份人工评分；当前仅保留上述局部比较，不用人工表格替代官方三份原始报告。

后续教学取舍：对在职开发者压缩已有工程常识、减少仓库启动/测试入口的重复微问答，转向审查真实问题、安全边界、后台任务可靠性、效果评估和团队集成。保持官方材料核对与中文连续讲解，不能将教师自拟重点冒充完整课堂内容。
