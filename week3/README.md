# 第三周：Agent Skills 与 CLI

当前阶段：第一版Skill已编写并放入项目发现目录，格式检查通过，自动触发及端到端运行待实测。第二周[说明初稿](../week2/writeup.md)保留待复核项，不据此标所有课堂/阅读完成。

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

2026-11-09已用skill-creator的quick_validate检查名称/frontmatter/占位符，结果Skill is valid；检查源文件与本地副本字节一致，且未配置disable-model-invocation。未运行模型触发或端到端测试，不以静态校验当效果证明。创建时使用skill-creator辅助，目标为用户选定的Claude环境，因此没有添加Codex UI元数据或全局安装。

从项目根目录每条开一个新会话，保持原来的模型与MCP配置：

```powershell
claude --settings "C:\Users\admin\.claude\settings-deepseek.json" --model haiku --mcp-config ".\week2\.mcp.json.example" --strict-mcp-config
```

四条独立测试及判定在[evals.md](evals.md)。先测P1；不加Skill名字或斜杠命令，观察模型是否自行调用issue-evidence-report，并保留Skill调用、必要MCP结果和最终答复。仅看到/read或Skill正文不自动视为目标调用；若客户端明确通过读取载入指令，可记录实际加载途径，不能假定与自动Skill路由相同。显式调用可用于另行排障，但不填成自动触发通过。其余3例仍待执行，第二周150项测试不替代本周Skill评估。
