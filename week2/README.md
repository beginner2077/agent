# 第二周实操：GitHub Issues MCP Server

教学推进说明（2026-11-04）：学习者已确认主线为 Fall 2026。本目录实操断点保留；先按 [覆盖核对](../COURSE_COVERAGE_AUDIT.md) 紧凑补必要基础，再继续真实刷新和业务工具。以下“下一小步”是恢复实操时的断点，不代表另换旧版课程。

依据：[官方第二周作业](../course-assignments/week2/assignment.md)。本目录是当前学习项目的实现位置，不修改官方仓库副本，不代填正式 writeup。用户已授权将当前学习内容提交到下述仓库，并创建练习 Issue。

## 当前状态

测试仓库为 [beginner2077/agent](https://github.com/beginner2077/agent)。GitHub App 所有者 `beginner2077`，App ID `5608184`，Client ID `Iv23liKKXW1SNhxqjN1I`（均为应用标识，不是密钥）。首次真实 OAuth 登录已完成，缓存、账号、安装范围与权限已只读核对。独立 MCP 环境及本地 stdio 测试已通过。按需静默刷新逻辑已实现并通过离线测试，尚未真实刷新或接入 MCP 业务工具；以下业务工具契约仍为计划行为。

当前发布使用 Git 的独立登录，不代表第二周 MCP 的 GitHub App OAuth 已完成。提交作者仅在本仓库设置为 `beginner2077 <97858703+beginner2077@users.noreply.github.com>`，不更改全局 Git 身份。

2026-11-04：首次学习内容提交 `cbc41c9` 已推送至 `main`；13 项离线测试通过（第一周修复 6 项、课堂 DeepSeek 适配 7 项）。通过 Git Credential Manager 完成 Git 登录，再通过 GitHub REST API 创建并逐个读取核对下列练习 Issue；这不属于已实现 MCP 服务的运行证据。

| 练习 Issue | 后续用途 | 创建后核对状态 |
| --- | --- | --- |
| [#4 查询列表并读取详情](https://github.com/beginner2077/agent/issues/4) | `list_issues → get_issue` 只读链式演示 | open |
| [#5 专用状态变更测试](https://github.com/beginner2077/agent/issues/5) | 验证默认预览零写入；后续关闭、读取、重新打开 | open |
| [#6 错误结果与授权失效恢复](https://github.com/beginner2077/agent/issues/6) | 参数错误及授权恢复，先用模拟端点覆盖 | open |

当前只创建练习数据，未执行关闭/重开、撤销授权或修改权限。上述状态是创建后读取的结果，后续练习应重新查询实际状态。

## 目标和范围

在一个用户指定的个人专用测试仓库中，列出 Issue、读取详情、预览并修改指定测试 Issue 的开关状态。代码通过 stdio 向 Claude Code 提供工具，由 DeepSeek 模型使用。

仓库通过本机配置固定为 `owner/repo`，工具参数不暴露任意仓库选择。不读取或修改其他项目的代码、提交、PR、评论、标签或设置。GitHub 的 Issues 列表可能含 PR，列表需排除 PR，详情与写操作也需拒绝 PR 对象。

## 三个组合工具的契约草案

| 工具 | 输入 | 输出与串联 | 操作性质 |
| --- | --- | --- | --- |
| `list_issues` | `state` 为 `open/closed/all`，有界分页参数 | 精简列表：`issue_number/title/state/url` 及分页信息 | 只读 |
| `get_issue` | `issue_number`，取自列表的同名字段，必须为正整数 | 精简详情：编号、标题、正文、状态、URL；正文限长时明确标记 | 只读 |
| `set_issue_state` | 同一 `issue_number`，`state` 为 `open/closed`，`dry_run=True` | 默认返回当前状态、目标状态和计划请求；关闭预览时才更新并报告实际结果 | 可写 |

`issue_number` 对应 GitHub 返回的 `number`，不是全局 `id`，也不是 MCP 请求的 JSON-RPC ID。

计划串联：`list_issues → get_issue → set_issue_state(dry_run=True)`。正式写入演示只针对用户明确指定的测试 Issue；真实写操作的目标与内容先完整展示，再执行。

默认预览分支不得发出修改请求。标注 `readOnlyHint` 用于说明工具性质；具体仓库和写入限制仍由代码校验，不能只依赖提示或注解。

## OAuth 和权限

注册配置指导（2026-11-04）：App 名称为 `beginner2077-cs146s-mcp`（用户授权页已确认），Homepage 使用本仓库 URL；回调地址为 `http://127.0.0.1:8765/callback`，不启用通配匹配。用户实际页面在 Identifying and authorizing users 分组中称此字段为 Redirect URI，官方文档称 Callback URL，二者在此指同一用途。当前独立登录入口按同一地址启动回调监听。指导保留用户令牌过期，不开启安装时自动 OAuth 或 Device Flow；关闭 Webhook Active，Setup URL 留空。已收到注册成功及仅安装 agent 的确认，尚未逐项核实实际配置；注册、安装和 OAuth 授权是分别完成的步骤。

使用 GitHub App 的用户授权码流程及可过期用户访问令牌，以覆盖授权码交换、缓存和刷新。使用 `state` 校验与 PKCE S256；回调地址需要与 App 注册配置匹配。

App 安装仅选择上述测试仓库。计划权限为 Repository `Issues: Read and write`，以及 GitHub App 必需的 Metadata 读取权限；不额外申请 Contents、Pull requests 或管理权限。写操作是本练习申请 Issues 写权限的原因。

GitHub App 使用注册时配置的细粒度权限，不沿用传统 OAuth App 的 `repo` scope；用户令牌同时受用户自身权限和 App 权限约束。

首次登录由独立的本机授权入口完成。后续 Server 将通过 `TokenStore.access_token()` 读取缓存，必要时刷新；刷新逻辑已实现，Server 接入尚未完成。授权失效且无法安全刷新时返回 `auth_required` 等可操作错误，不在工具调用中打开浏览器。

Client Secret、访问令牌与刷新令牌只在本机配置或缓存中管理，不写进示例配置、模型提示或日志。缓存位置、忽略规则和权限保护在实现前明确。

### 本机配置准备

2026-11-04 已创建 `%LOCALAPPDATA%\CS146S\github-mcp\.env`：填写了上述 Client ID、回调地址和固定仓库，`GITHUB_CLIENT_SECRET` 初始留空。目录已关闭 ACL 继承，仅为当前 Windows 用户保留完全控制权限，并核对文件继承后的 ACL；位于 Git 工作区之外。仓库中的 [.env.example](.env.example) 不含密钥，真实 `.env` 也受忽略规则保护。

学习者在 GitHub App 设置的 Client secrets 区域生成 Client Secret，然后仅在本机编辑上述文件的 `GITHUB_CLIENT_SECRET=` 一行；无需发送给助教。可在 PowerShell 运行：

```powershell
notepad "$env:LOCALAPPDATA\CS146S\github-mcp\.env"
```

学习者回复“已保存”后的首次只读检查结果：配置文件存在、Client Secret 非空、Client ID/回调/仓库匹配、目录 ACL 符合预期；该次检查没有打印配置值或发出 OAuth 请求；后续真实登录证据见下文。[oauth_login.py](oauth_login.py) 显式读取此文件，若进程已设置相应 `GITHUB_` 环境变量，则环境变量优先；不自动搜索其他项目配置，不修改 Claude 命名配置或全局环境变量。令牌缓存位置为同一受限目录的 `tokens.json`，现已由首次真实登录创建。不得通过打印配置或缓存内容来验证；检查时只返回必要的状态信息，不输出凭据。

## 本地 MCP 最小验证

这是在业务工具与 OAuth 之前的自拟前置检查，不代表官方第二周作业已验收。仅提供 `ping` 工具，返回 `status=ok, scope=local_mcp`，不读取凭据、不访问 GitHub、不调用模型。

本轮使用独立的 `week2/.venv`，保留第一周根目录 `.venv` 的依赖。直接依赖版本见 [requirements.txt](requirements.txt)：FastMCP 4.1.6、MCP SDK 2.3.0；版本已从 PyPI 元数据核对。重建与检查命令均从项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m venv week2/.venv
.\week2\.venv\Scripts\python.exe -m pip install -r week2/requirements.txt
.\week2\.venv\Scripts\python.exe -m pytest week2/test_mcp_stdio.py -q -s
```

[server.py](server.py) 用 `@mcp.tool(...)` 注册工具，用 `mcp.run(transport="stdio")` 处理协议消息；`show_banner=False` 仅隐藏启动横幅。单独启动命令为 `.\week2\.venv\Scripts\python.exe week2/server.py`，此时服务等待 MCP 请求，不是自然语言输入框。

[test_mcp_stdio.py](test_mcp_stdio.py) 通过 `StdioTransport` 启动真实服务器子进程，先 `tools/list` 再 `tools/call`，检验工具名及返回内容。`ping` 是自定义工具名，请求方法仍为 `tools/call`；这里没有调用 Client 的协议级 `ping()`。测试打印的版本/工具名/结果是读取返回对象后的摘要，不是原始协议报文。SDK 自动选择协议版本，测试输出实际协商值，不预先假定旧版 `initialize` 流程。

2026-11-04 验证结果：上述 pytest 命令返回 `1 passed in 1.60s`；实际协商协议为 `2026-07-28`，`tools/list` 返回 `['ping']`，`tools/call` 结果为 `{'status': 'ok', 'scope': 'local_mcp'}`。独立环境 `python -m pip check` 返回 `No broken requirements found.`。此项测试只覆盖测试客户端到本地 Server 的协议链路；GitHub 授权、业务工具和 Claude Code 集成需要各自的验证证据。

## 独立 OAuth 首次登录

从项目根目录执行：

```powershell
.\week2\.venv\Scripts\python.exe week2/oauth_login.py
```

程序先绑定 `127.0.0.1:8765`，打印授权链接；学习者手动在浏览器打开，使用 beginner2077 在五分钟内完成授权。浏览器回到本机后，程序校验 `state`，用 `code + client_secret + code_verifier` 请求固定的 GitHub 令牌端点，再只读调用 `/user` 核对账号，最后原子保存令牌。链接中只含 PKCE S256 挑战值，不含 verifier 或 Client Secret；`offline_access` 请求可过期令牌及刷新令牌，不用于授予仓库业务权限。

`state` 把回调与本次登录请求关联，PKCE 把授权码与本次程序持有的 verifier 关联。回调页面只报告“已收到回调”；终端 `3/3 登录成功` 才表示换取令牌、核对账号和本机保存均已完成。

HTTP 回调日志不会记录带 code 的 URL；错误不输出远端响应正文或凭据。缓存及临时文件均位于受限目录，Windows ACL 仅授权当前用户；保存失败保留旧文件。授权码交换失败不会自动重试同一码，网络结果不确定时重新运行登录入口。账号不匹配时不保存新令牌。初次登录负责获得和保存令牌，按需刷新由下节 `TokenStore` 负责。

离线验证命令：`.\week2\.venv\Scripts\python.exe -m pytest week2 -q`。2026-11-04 返回 **23 passed in 1.62s**（22 项 OAuth 用例及 1 项 stdio 测试），`pip check` 通过。测试使用 RFC 7636 PKCE 向量、虚构配置、MockTransport、临时缓存及本机临时端口；这些测试没有调用真实 GitHub 授权或令牌端点。

真实验证（2026-11-04 09:07 UTC）：学习者已运行登录命令并反馈 `3/3 登录成功`。只读核对真实 `tokens.json`：访问/刷新令牌均非空且当时未过期，Client ID/仓库匹配，缓存 ACL 仅当前用户。随后仅使用 GET `/user`、`/user/installations`、`/user/installations/178480617/repositories`，确认账号 beginner2077、App ID 5608184、安装 ID 178480617、`repository_selection=selected`、关联仓库仅 beginner2077/agent，权限为 `issues=write` 和 `metadata=read`，安装未暂停。这是当前首次登录与安装范围的真实证据；没有写入 GitHub、刷新令牌或验证 MCP 业务工具。关联仓库清单不等于断言其他公共数据都不可读取。

## 按需静默刷新

学习者对“远端刷新成功但本地保存失败后，能否把旧缓存当作有效凭据”的回答“不能”达标。GitHub 的旧令牌对已经失效；原子写入仅保护文件完整性，无法回滚远端轮换。

[token_store.py](token_store.py) 的 `TokenStore.access_token()` 供后续业务 API 客户端调用，不是后台定时任务，也不会打开浏览器。读取时核对应用、仓库、令牌结构与过期时间；剩余有效期大于 60 秒时复用访问令牌，临近过期时用刷新令牌换新令牌对，原子保存后才返回新访问令牌。

| 分支 | 行为 |
| --- | --- |
| 刷新令牌过期、授权被拒绝、响应缺失或内容不完整 | `auth_required`，提示独立登录命令 |
| 连接未建立或 HTTP 429 | 标记 `retryable=True`，由调用方稍后重试，本函数不自动循环 |
| 应用凭据错误 | `client_config_invalid`，提示修正本机配置并重启 |
| 远端成功但本机保存失败 | `token_cache_write_failed`，不回退旧凭据；当前实例拒绝继续使用该旧刷新令牌 |
| 同一缓存被其他实例更新 | `token_busy`，可稍后重试 |

读缓存、刷新和保存处于同一个 OS 文件锁内，同一实例另有线程锁。首次登录保存也使用同一锁文件。重新登录写入不同令牌后，当前实例可读取新缓存恢复。过期时间只是本机判断，无法证明令牌没有被远端撤销；后续 API 客户端仍需处理实际 401。

首次兑换和刷新共用 `oauth_login.tokens_from_payload()` 校验，`OAuthError` 新增 `retryable` 状态。本轮 `.\week2\.venv\Scripts\python.exe -m pytest week2 -q` 返回 **47 passed in 1.87s**（此前 23 项 + 24 项刷新用例），涵盖轮换两个令牌、临界过期、缓存损坏、失败重试策略、远端成功后写入失败、重新登录恢复及两个实例争用锁。所有刷新请求均使用 MockTransport 和虚构令牌，未访问真实刷新端点。

另用禁止联网的客户端检查了真实缓存复用：返回现有访问令牌，网络请求为 0，`tokens.json` 字节未改变。只证明当时正常复用，尚未验证真实刷新、实际 API 401 处理或 MCP 业务工具集成。下一小步先完成一次真实刷新验证，再实现首个 GitHub 工具。

## 独立真实刷新验证入口

本次验证的是后续 MCP 工具依赖的授权模块，尚未通过 MCP 工具调用，也没有模型参与。已有首次登录成果保留，无需为测试手动改缓存过期时间。

从项目根目录先运行说明模式，不读取配置或缓存、不联网：

```powershell
.\week2\.venv\Scripts\python.exe -m week2.verify_refresh
```

执行一次真实验证：

```powershell
.\week2\.venv\Scripts\python.exe -m week2.verify_refresh --refresh
```

`--refresh` 即使访问令牌尚未过期，也会显式消费当前刷新令牌，请求并保存新令牌对；成功后旧令牌对失效。只运行一次并观察结果，遇到失败先核对错误阶段，不连续重复强制刷新。该命令读取已有本机 `.env` 和 `tokens.json`，不会打开浏览器，不请求新权限或执行 Issue 写操作。

流程为：

```text
读取并校验已有缓存
  → TokenStore.access_token(force_refresh=True)
  → GitHub 返回新令牌对，原子保存
  → 回读缓存，比较两枚令牌是否变化及访问令牌是否匹配返回值
  → 用当前访问令牌 GET /user，只读核对 beginner2077
```

[verify_refresh.py](verify_refresh.py) 最终只输出账号和布尔检查结果，不输出凭据、前后缀或摘要。`cached_access_token_matches` 只表示缓存访问令牌与本次方法返回值一致；两枚令牌变化另外比较。若刷新已保存而账号核对失败，会明确报告这个阶段，不回滚到旧令牌。若缓存被其他进程更新导致回读核对失败，会停止，不自动再次刷新。验证期间不要同时启动第二次强制刷新。

`TokenStore.access_token()` 默认仍按剩余有效期决定复用或刷新；新增的仅关键字参数 `force_refresh=True` 供显式验证使用，不作为 MCP 工具参数对模型暴露。复用既有缓存校验、OS 锁、刷新响应校验和原子保存逻辑，没有新增依赖。

2026-11-05 离线验证：原47项保持通过，新增9项检查，共 **56 passed in 1.80s**。新增检查覆盖未到期时显式刷新、只读账号核对、两枚令牌变化、账号核对失败保留已保存状态、端点拒绝不重试、默认模式零凭据读取以及命令入口。所有请求使用 MockTransport 和虚构令牌；默认说明模式已实际运行，未读取或更新真实令牌。真实验证待学习者执行上述 `--refresh` 命令，反馈三阶段输出及布尔摘要，不发送本机配置或缓存内容。

## 小步实施与验收

1、测试仓库、初始发布、练习 Issue、App 注册和首次真实 OAuth 登录已完成；安装范围与 Issues/Metadata 权限已通过该 App 用户令牌只读核对。

2、已在独立环境安装固定版本 FastMCP/SDK，最小 stdio 协议测试通过，记录了实际版本；课堂脚本的 DeepSeek 配置未改。

3、独立 OAuth 首次登录与缓存已真实验证；静默刷新及失败分支已实现，新增真实刷新验证入口，56项离线测试通过，下一步由学习者验证一次真实刷新。

4、逐个实现工具。通过 MCP Client 调用 `tools/list` 和 `tools/call`，验证 schema、输出裁剪、PR 排除、预览零写入及结构化错误。

5、在个人测试仓库完成真实链式演示、一个失败恢复案例和指定测试 Issue 的写入演示。记录实际调用与结果，不用模拟结果替代真实证据。

6、由学习者组织正式 writeup；后续发布按明确的任务范围执行，不将本次发布授权扩展为自动提交每一步练习。

## 已核对的官方资料

- [GitHub App 用户授权与权限](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
- [GitHub App 访问令牌刷新](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens)
- [GitHub Issues REST API](https://docs.github.com/en/rest/issues/issues)
- [FastMCP 快速入门](https://gofastmcp.com/getting-started/quickstart)
- [官方参考 Fetch Server](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)：已读说明、工具参数/注册、错误返回和 stdio 启动关键段；作为设计参考，没有运行该服务。
