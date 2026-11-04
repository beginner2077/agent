# 第二周实操：GitHub Issues MCP Server

依据：[官方第二周作业](../course-assignments/week2/assignment.md)。本目录是当前学习项目的实现位置，不修改官方仓库副本，不代填正式 writeup。用户已授权将当前学习内容提交到下述仓库，并创建练习 Issue。

## 当前状态

测试仓库已指定为 [beginner2077/agent](https://github.com/beginner2077/agent)。目前只有工具契约与分步实施草案；GitHub App 尚未注册，FastMCP/MCP 依赖未安装，服务与 OAuth 代码尚未实现。以下是计划行为，不是已经运行通过的功能。

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

使用 GitHub App 的用户授权码流程及可过期用户访问令牌，以覆盖授权码交换、缓存和刷新。使用 `state` 校验与 PKCE S256；回调地址需要与 App 注册配置匹配。

App 安装仅选择上述测试仓库。计划权限为 Repository `Issues: Read and write`，以及 GitHub App 必需的 Metadata 读取权限；不额外申请 Contents、Pull requests 或管理权限。写操作是本练习申请 Issues 写权限的原因。

GitHub App 使用注册时配置的细粒度权限，不沿用传统 OAuth App 的 `repo` scope；用户令牌同时受用户自身权限和 App 权限约束。

首次登录由独立的本机授权入口完成。Server 使用缓存令牌，必要时刷新并保存刷新结果；授权失效且无法刷新时返回 `auth_required` 等可操作错误，不在工具调用中打开浏览器。

Client Secret、访问令牌与刷新令牌只在本机配置或缓存中管理，不写进示例配置、模型提示或日志。缓存位置、忽略规则和权限保护在实现前明确。

## 小步实施与验收

1、测试仓库、当前内容发布与练习 Issue 创建已完成；下一步注册并限权安装 GitHub App。

2、选定、安装并记录 FastMCP/SDK 版本；用最小 stdio 例子核对实际协议支持，保持课堂脚本的 DeepSeek 配置。

3、实现独立 OAuth 登录、缓存与刷新；用模拟端点验证交换/刷新/失效分支，再验证真实授权。

4、逐个实现工具。通过 MCP Client 调用 `tools/list` 和 `tools/call`，验证 schema、输出裁剪、PR 排除、预览零写入及结构化错误。

5、在个人测试仓库完成真实链式演示、一个失败恢复案例和指定测试 Issue 的写入演示。记录实际调用与结果，不用模拟结果替代真实证据。

6、由学习者组织正式 writeup；后续发布按明确的任务范围执行，不将本次发布授权扩展为自动提交每一步练习。

## 已核对的官方资料

- [GitHub App 用户授权与权限](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
- [GitHub App 访问令牌刷新](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens)
- [GitHub Issues REST API](https://docs.github.com/en/rest/issues/issues)
- [FastMCP 快速入门](https://gofastmcp.com/getting-started/quickstart)
- [官方参考 Fetch Server](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)：已读说明、工具参数/注册、错误返回和 stdio 启动关键段；作为设计参考，没有运行该服务。
