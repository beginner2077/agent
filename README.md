# CS146S Fall 2026 学习项目

**当前教学调整（2026-11-04）：** 用户已确认遵循 Fall 2026；按官方对应课堂、阅读与作业推进，2025 代码及中文笔记仅作补充。先紧凑补讲模型基础、提示/上下文及评估，见 [课程覆盖核对](COURSE_COVERAGE_AUDIT.md)，随后返回第二周 MCP 断点；既有实践保留，不重做旧版整套作业。

从课程开始独立学习，不引用其他业务项目的 docs、AGENTS 或 Skill 模板。练习代码放在本项目中，保留已有 PyCharm `main.py`。

**当前练习（2026-11-05）：** [指令、示例与外部资料四组对照](labs/prompt_context/README.md)已完成12次真实请求；[最小本地检索练习](labs/retrieval/README.md)现已实现关键词匹配、版本过滤、关联补全与模型输入预览，新增10项离线测试通过，生成阶段尚未调用模型。用户最新授权：新增代码自动加入 Git；完整练习、专题或独立修复验证后，再自主 commit 和 push，提交说明使用中文，不按每轮问答提交。凭据和原始运行记录继续忽略；已推送历史保留。

**当前进度以 [学习交接](LEARNING_HANDOFF.md) 和 [第一周覆盖清单](WEEK1_LEARNING_CHECKLIST.md) 为准。** 已选择 Claude Code + DeepSeek。第二周课堂文字稿及指定阅读核心已中文导读，官方MCP作业选用GitHub App用户OAuth，测试仓库为 [beginner2077/agent](https://github.com/beginner2077/agent)。初始学习内容已推送至 `main`，练习 Issue [#4](https://github.com/beginner2077/agent/issues/4)、[#5](https://github.com/beginner2077/agent/issues/5)、[#6](https://github.com/beginner2077/agent/issues/6) 已创建；[工具契约与练习入口](week2/README.md)已记录。GitHub App 已注册，仅安装到 `agent`（已通过 API 核对）；仓库外本机配置已保存，状态检查通过；独立 MCP 环境及最小 stdio 协议测试已通过；OAuth 首次真实登录已成功，缓存及安装范围已只读核对；按需静默刷新逻辑及失败分支已实现，第二周47项测试通过，真实刷新待验证；GitHub业务工具尚未实现。第一周视频/X原文、部分材料与正式writeup等缺口继续保留，不以局部检查代替整周验收。基础可简讲，新概念与前置不能跳过。

已完成练习：[第一周 Part I：多文件修复与失败恢复](labs/week1_trace/README.md)。初始导入错误已修复，当前 6 项测试通过；代理轨迹保留了失败、两次 Edit 及再次验证的证据。

## 环境

- 项目解释器：`.venv\Scripts\python.exe`，Python 3.12.14。
- 课程依赖：使用官方仓库的 `pyproject.toml` 和 `poetry.lock` 安装到 `.venv`。
- 工具环境：`.tools`，独立安装 Poetry 2.5.1、export 插件 1.10.1、mitmproxy 12.3.1。
- 系统已有：Git 2.53.0、Node 22.20.0、Codex CLI 0.163.0（此前检查）；Claude Code 本次实测为 2.1.316，分析提示与工具时以本次版本和抓取为准。
- Codex 本机状态显示使用 ChatGPT 登录。用户此前提供主模型 `deepseek-v4-pro`、Haiku 映射 `deepseek-v4-flash` 的配置说明。实际使用命名配置文件；首次成功抓取的请求字段 `model` 为 `deepseek-v4-flash`，HTTP 200，响应为 `PROXY_OK`。该值记录客户端请求的模型，不证明服务端内部实现或后续所有请求的模型。

两个虚拟环境复用了本机已有 Python 3.12.14 基础解释器；其位置在 Codex runtime 的 dependencies/python 下。若移除或清理该基础解释器，需要用仍可用的 Python 3.12 重建环境，课程代码不受影响。

官方示例采用 Conda + Poetry；此处用标准 `venv` 达到独立 Python 3.12 环境的同样目的，无需再安装 Anaconda。uv、Docker、Ollama 服务等按后续实际课程任务增加，当前不要求它们。

本次 Poetry 直接下载遇到 PyPI 连接失败，改用官方 export 插件从原锁文件导出，再通过 pip 校验哈希安装；没有重新解析版本或修改上游锁文件。

2026-11-02 验证：课程依赖、FastAPI 内存请求、SQLite、两个环境的 pip check 均通过。抓取脚本现已适配 DeepSeek，通过本地模拟转发、替身 CLI、异常清理和代理身份检查；这些检查未发送真实模型请求。发现并停止了本项目仍占用端口的旧 Anthropic 代理。PyCharm 本身可正常打开，但桌面控制连接不可用，IDE 当前解释器选择未经自动核实。

## 开始使用

在本目录的 PowerShell 终端运行：

```powershell
.\scripts\enter.ps1
python scripts/check_env.py
```

如本机执行策略拒绝本地脚本，只对当前终端执行 `Set-ExecutionPolicy -Scope Process Bypass`，然后重新运行；不修改用户级或系统级策略。

PyCharm 项目解释器选择本项目 `.venv\Scripts\python.exe`。在 Settings → Project → Python Interpreter 中添加 Existing environment 并选择该文件；不要选择 WindowsApps 的 python.exe 占位程序。

## 课程材料

- [课程官网（Fall 2026）](https://themodernsoftware.dev/)
- [官方作业仓库](https://github.com/mihail911/modern-software-dev-assignments)
- 本机官方仓库：`course-assignments/`，独立克隆，不修改上游作业或代填答案。
- 下载基线：`df18839a8174ca57edad89c03948bd295459c9c0`；日期：2026-11-02。
- 第一周入口：`course-assignments/week1/assignment.md`；作答提纲：`course-assignments/week1/writeup.md`。

课程从第一周 Agent 轨迹观察开始，实际练习路线与适配边界按交接文档选择；不提前实现复杂 Agent、Hook 框架或多 Agent 系统。后续在本项目新建会话，通过交接文档恢复进度。

## 第一周抓取工具（Claude Code + DeepSeek 自学适配）

先在本项目的一个 PowerShell 终端启动代理，保持该终端运行：

```powershell
.\scripts\start-proxy.ps1
```

再在本项目的另一个终端启动新的 Claude Code 会话：

```powershell
.\scripts\trace-claude.ps1
```

该入口默认使用用户实际启动 Claude 时指定的 `%USERPROFILE%\.claude\settings-deepseek.json`，不回落到默认认证配置。也可显式指定：

```powershell
.\scripts\trace-claude.ps1 -SettingsFile 'C:\Users\admin\.claude\settings-deepseek.json'
```

`start-proxy.ps1` 监听 `127.0.0.1:58888`，上游固定为 `https://api.deepseek.com`。客户端临时基址为 `http://127.0.0.1:58888/anthropic`，因此 Messages 请求保留 `/anthropic/v1/messages` 路径。端口被占用时脚本直接报错，不复用未知代理。

`trace-claude.ps1` 先用系统 `curl.exe` 绕过系统代理，检查 `deepseek_proxy.py` 提供的本地 `/_cs146s/upstream` 标识；标识不符就拒绝启动 Claude Code。就绪检查由代理本地响应，不验证 DeepSeek 的远端连接或模型额度。脚本在本机加载所选配置，保留其认证、模型和其他字段，只覆盖 `env.ANTHROPIC_BASE_URL`，再以临时 `--settings` 文件启动。配置文件中的基址会覆盖终端环境变量，不能只设置终端变量来切换代理。

临时配置可能包含凭据，写入前先将临时目录 ACL 限制为当前用户；配置内容不输出到对话或日志。正常退出或脚本异常时删除临时文件及目录、恢复进程环境，不修改原文件或全局配置。若整个宿主进程被强制终止，清理逻辑可能无法运行，应在本机检查 `%TEMP%\cs146s-claude-*` 残留，勿上传。

本次教学会话携带 `--safe-mode --strict-mcp-config`，以减少定制影响；实际抓取的系统消息仍列有 Skills、Agent 和延迟工具目录，不能仅凭参数推断所有目录都已关闭或消失。分析时记录实验条件与实际负载，不能把本次提示和工具清单当作所有 Claude Code 会话的固定内容。界面地址为 `http://127.0.0.1:8081`，如需登录，使用代理启动日志打印的本地链接。结束时退出 Claude Code，再在代理终端按 Ctrl+C。未修改系统代理或安装系统信任证书。

原始抓取保存在项目外 `%LOCALAPPDATA%\CS146S\captures\时间戳-随机标识\session.flows`；已核对一次真实 `POST /anthropic/v1/messages` 返回 HTTP 200，并将 SSE 文本片段拼接后确认响应为 `PROXY_OK`。这类文件可能包含凭据、完整提示和源码，只在本地分析，不加入仓库或直接上传。

### 重新打开历史抓取（离线）

`start-proxy.ps1` 每次新建抓取文件；重启后界面为空，不表示旧文件丢失，旧记录也不会自动载入。本次课程抓取位于下面的路径，已确认可完整读取 36 条 flow，包含 Part I 修复会话。

在项目根目录运行，保持终端打开：

```powershell
$taskSavedCapture = Join-Path $env:LOCALAPPDATA 'CS146S\captures\20261102-112742-e2d36a82\session.flows'
$taskProxyConfig = Join-Path $env:LOCALAPPDATA 'CS146S\mitmproxy'
.\.tools\Scripts\mitmweb.exe --no-server -r $taskSavedCapture --web-host 127.0.0.1 --web-port 8081 --no-web-open-browser --set "confdir=$taskProxyConfig"
```

打开该终端新打印的本地链接；每次启动的页面令牌可能不同，不复用旧登录链接。选中请求后，地址栏 `#/flows/<ID>/request` 中的 ID 是 mitmproxy Flow ID，不是服务商的 request_id。当前分析请求为 `ca61ff49-aee1-4780-af3c-26ebf1d5b4a1`，对照请求为 `55e9ec12-cd5b-4e75-9b7b-7d89e3ee61cd`。

`--no-server -r` 仅载入历史文件供查看，不启动转发代理或重新发送模型请求，也不覆盖源抓取文件。准备新抓取时先在此终端按 Ctrl+C 关闭离线查看，再启动 `start-proxy.ps1`，避免占用相同的 8081 端口。

## 9/22 课堂示例：DeepSeek Flash 适配

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe .\.tools\lecture-9-22-official.py
```

此文件是独立的课堂 mini harness，不会启动 Claude Code。它读取 `%USERPROFILE%\.claude\settings-deepseek.json` 的认证与服务地址，固定使用 `deepseek-flash`，不需要 `OPENAI_API_KEY`，也不修改 Claude 配置。虽然使用 OpenAI 兼容 SDK，实际请求发往 DeepSeek 的 `https://api.deepseek.com/responses`，依据 [DeepSeek 官方 Responses 文档](https://api-docs.deepseek.com/guides/responses_api/)。

调试时选择 `.venv\Scripts\python.exe`，工作目录设为项目根。在程序显示 `You:` 后向运行终端输入自然语言，不在 Python 表达式求值框输入。输入位于当前适配版第 278 行；第 284 行可检查 `user_msg`，第 292 行会调用模型。

原版保存在 `.tools/lecture-9-22-official.original.py`；适配前的中文注释版保存在 `.tools/lecture-9-22-official.before-deepseek.py`。当前版保留原工具、文本调用协议和循环，调整了提供商配置及初始指令角色（`developer` → `system`）。7 项离线模拟测试与真实配置的空输入启动检查已通过；没有发送真实模型请求，真实服务调用仍待用户运行验证。

## 重建环境

下面的 `python3.12.exe` 代表一份已安装且可用的 Python 3.12 可执行文件，请替换为实际路径。先停止正在使用环境的程序，不覆盖已有环境；环境损坏时先重命名保留旧目录。

```powershell
python3.12.exe -m venv .venv
python3.12.exe -m venv .tools
.\.tools\Scripts\python.exe -m pip install -r requirements-tools.txt
git clone --depth 1 https://github.com/mihail911/modern-software-dev-assignments.git course-assignments
.\scripts\enter.ps1
$taskRequirements = Join-Path (Get-Location).Path '.tools\course-requirements.txt'
poetry --directory .\course-assignments export --with dev -f requirements.txt -o $taskRequirements
python -m pip install --require-hashes --no-deps -r $taskRequirements
python scripts/check_env.py
```

克隆得到的可能是更新版本，需要与本次基线比较。环境和官方仓库副本均不进入本项目 Git 跟踪；本项目不会自动暂存、提交、推送或安装 Git hooks。
