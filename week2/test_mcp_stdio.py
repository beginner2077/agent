"""通过真实子进程的 stdin/stdout 调用工具，不直接调用 ping 函数。"""

import asyncio
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


def test_list_and_call_over_stdio():
    async def exercise():
        transport = StdioTransport(
            command=sys.executable,
            args=[str(Path(__file__).with_name("server.py"))],
            keep_alive=False,
        )
        async with Client(transport, timeout=20) as client:
            assert client.protocol_version is not None
            # 发现工具和执行工具是两次不同的 MCP 请求。
            tools = await client.list_tools()
            assert [tool.name for tool in tools] == ["ping"]
            result = await client.call_tool("ping", {})
            assert result.data == {"status": "ok", "scope": "local_mcp"}
            print("protocol:", client.protocol_version)
            print("tools/list:", [tool.name for tool in tools])
            print("tools/call ping:", result.data)

    asyncio.run(exercise())
