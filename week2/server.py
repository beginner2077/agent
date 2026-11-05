"""第二周第一小步：只验证本地 MCP 通信，不连接 GitHub。"""

from fastmcp import FastMCP


mcp = FastMCP(
    "CS146S GitHub Issues",
    instructions="当前只提供本地通信检查，尚不能查询或修改 GitHub Issue。",
)


@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
def ping() -> dict[str, str]:
    """确认本地 MCP 工具可调用；成功不代表 GitHub 已连接或 OAuth 已授权。"""
    return {"status": "ok", "scope": "local_mcp"}


if __name__ == "__main__":
    # stdout 专供 MCP 协议消息，不能在这里添加普通 print 日志。
    mcp.run(transport="stdio", show_banner=False)
