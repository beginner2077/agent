"""第二周 MCP：列表、详情及默认预览的专用测试Issue状态操作。"""

from contextlib import asynccontextmanager
import json
from threading import Lock
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .github_issues import IssuesClient, MAX_PAGE, MAX_PAGE_SIZE, STATE_CHANGE_ISSUE, configured_client
from .oauth_login import OAuthError


def create_server(issues_client: IssuesClient | None = None) -> FastMCP:
    runtime = issues_client
    runtime_lock = Lock()

    @asynccontextmanager
    async def lifespan(server):
        try:
            yield {}
        finally:
            if runtime is not None:
                runtime.close()

    mcp = FastMCP(
        "CS146S GitHub Issues",
        instructions="ping仅检查本地通信；list_issues和get_issue只读查询beginner2077/agent。"
                     "详情使用列表返回的issue_number，拒绝PR；正文截断时不可当作全文。"
                     "set_issue_state仅操作#5，默认dry_run=true；明确执行时才传false，仅改变state并回读。"
                     "写入结果未知或核验失败时停止，先读状态，不盲目重试；预览不是执行授权。"
                     "PR已过滤，少于一页或空页仍需查看分页。错误不代表空列表；auth_required应独立登录。",
        lifespan=lifespan, mask_error_details=True, strict_input_validation=True,
    )

    def invoke(method: str, **arguments) -> dict:
        # 业务工具共用延迟初始化、客户端生命周期和安全错误边界。
        nonlocal runtime
        try:
            with runtime_lock:
                if runtime is None:
                    runtime = configured_client()
                active = runtime
            return getattr(active, method)(**arguments)
        except OAuthError as error:
            raise ToolError(json.dumps({"error": error.code, "message": str(error),
                                        "retryable": error.retryable}, ensure_ascii=False)) from None
        except Exception:
            raise ToolError(json.dumps({"error": "internal_error", "message": "工具执行失败，未取得结果。",
                                        "retryable": False}, ensure_ascii=False)) from None

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def ping() -> dict[str, str]:
        """确认本地 MCP 工具可调用；成功不代表 GitHub 已连接或 OAuth 已授权。"""
        return {"status": "ok", "scope": "local_mcp"}

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True})
    def list_issues(
        state: Literal["open", "closed", "all"] = "open",
        page: Annotated[int, Field(ge=1, le=MAX_PAGE, strict=True)] = 1,
        page_size: Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE, strict=True)] = 10,
    ) -> dict:
        """只读查询固定仓库的一页Issue，排除PR；标题超过200字符会标记截断。

        Args:
            state: open、closed或all。
            page: 上游页码，1至100。少量或空结果不代表没有下一页。
            page_size: 每页1至10条上游记录，过滤PR后可能减少。
        """
        return invoke("list_issues", state=state, page=page, page_size=page_size)

    @mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True})
    def get_issue(issue_number: Annotated[int, Field(gt=0, strict=True)]) -> dict:
        """只读取得固定仓库Issue详情；使用列表的issue_number，拒绝PR。

        正文最多返回4000字符，body_length为原长度，body_truncated说明是否截断。

        Args:
            issue_number: 列表返回的正整数编号，不是GitHub全局id。
        """
        return invoke("get_issue", issue_number=issue_number)

    @mcp.tool(title="测试Issue状态（默认预览）",
              annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": True})
    def set_issue_state(
        issue_number: Annotated[int, Field(ge=STATE_CHANGE_ISSUE, le=STATE_CHANGE_ISSUE, strict=True,
                                          json_schema_extra={"const": STATE_CHANGE_ISSUE})],
        state: Literal["open", "closed"],
        dry_run: Annotated[bool, Field(strict=True)] = True,
    ) -> dict:
        """固定仓库专用Issue #5的状态操作；默认预览，不发送PATCH。

        显式false才执行：先重新读取，已是目标则不写，否则只PATCH state并回读。
        applied表示修改响应已确认，verified表示随后回读符合目标；两者需分别判断。
        结果未知或verified=false时停止，不自动重试，也不据此断言没有写入。

        Args:
            issue_number: 从list_issues/get_issue取得的专用测试编号5。
            state: 计划的open或closed状态。
            dry_run: 默认true预览；仅在用户明确要求执行该目标时传false。
        """
        return invoke("set_issue_state", issue_number=issue_number, state=state, dry_run=dry_run)

    return mcp


mcp = create_server()


if __name__ == "__main__":
    # stdout 专供 MCP 协议消息，不能在这里添加普通 print 日志。
    mcp.run(transport="stdio", show_banner=False)
