# 第四周：陌生仓库勘察与CLAUDE.md

当前状态（2026-11-11）：已创建[fork](https://github.com/beginner2077/more-itertools)，克隆并固定勘察基线`ceafee8ce96f4bc1eb74c528bc247c91d648a0bb`；独立Python3.12.14环境运行935项unittest测试通过，未修改目标源码。尚未编写CLAUDE.md，也未运行完整CI检查或用户模型的两项任务。

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

本节学习点：把“源码里看到了什么”“命令实际验证了什么”“哪些检查仍未做”分开，再把高价值、仓库特有的事实压缩为常驻规则。下一节先导读第四周指定材料中关于CLAUDE.md内容取舍的原则，结合当前证据写约一页文件；两项模型任务仍留待文件就绪后由用户的Claude+DeepSeek运行。

当前没有新增待答题；没有创建目标规则文件或正式writeup占位稿，不标作业完成，不向上游提交贡献或自动添加课程协作者/提交Gradescope。前面的选型及远端初查表为历史阶段，当前状态以本节为准。
