"""第二周 MCP：本地 ping，以及固定测试仓库的只读 Issue 列表。"""

from contextlib import asynccontextmanager
import json
from threading import Lock
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from .github_issues import IssuesClient, MAX_PAGE, MAX_PAGE_SIZE, configured_client
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
        instructions="ping仅检查本地通信；list_issues只读查询beginner2077/agent的一页Issue。"
                     "PR已过滤，少于一页或空页仍需查看分页。错误不代表空列表；auth_required应独立登录。",
        lifespan=lifespan, mask_error_details=True, strict_input_validation=True,
    )

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
        nonlocal runtime
        try:
            with runtime_lock:
                if runtime is None:
                    runtime = configured_client()
                active = runtime
            return active.list_issues(state, page, page_size)
        except OAuthError as error:
            raise ToolError(json.dumps({"error": error.code, "message": str(error),
                                        "retryable": error.retryable}, ensure_ascii=False)) from None
        except Exception:
            # 配置或上游异常可能携带凭据，只返回受控错误，不转发异常原文。
            raise ToolError(json.dumps({"error": "internal_error", "message": "工具执行失败，未取得列表。",
                                        "retryable": False}, ensure_ascii=False)) from None

    return mcp


mcp = create_server()


if __name__ == "__main__":
    # stdout 专供 MCP 协议消息，不能在这里添加普通 print 日志。
    mcp.run(transport="stdio", show_banner=False)
