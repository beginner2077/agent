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
            args=["-m", "week2.server"],
            cwd=str(Path(__file__).resolve().parents[1]),
            keep_alive=False,
        )
        async with Client(transport, timeout=20) as client:
            assert client.protocol_version is not None
            # 发现工具和执行工具是两次不同的 MCP 请求。
            tools = await client.list_tools()
            assert {tool.name for tool in tools} == {"ping", "list_issues", "get_issue"}
            result = await client.call_tool("ping", {})
            assert result.data == {"status": "ok", "scope": "local_mcp"}
            print("protocol:", client.protocol_version)
            print("tools/list:", [tool.name for tool in tools])
            print("tools/call ping:", result.data)

    asyncio.run(exercise())


def test_issue_call_over_real_stdio_with_mock_github():
    # 子进程运行真实工具和MCP协议，只替换上游HTTP及凭据，不读取本机配置。
    fixture_code = '''
import httpx
from week2.github_issues import IssuesClient
from week2.server import create_server
class Tokens:
    def access_token(self):
        return "fictional-access"
def endpoint(request):
    assert request.method == "GET" and request.url.host == "api.github.com"
    if request.url.path.endswith("/issues/4"):
        return httpx.Response(200, json={"number": 4, "title": "fixture", "state": "open", "body": "fixture body", "html_url": "https://github.com/beginner2077/agent/issues/4"})
    return httpx.Response(200, json=[
        {"pull_request": {}},
        {"number": 4, "title": "fixture", "state": "open", "html_url": "https://github.com/beginner2077/agent/issues/4"}
    ], headers={"Link": '<https://api.github.com/repos/beginner2077/agent/issues?page=2>; rel="next"'})
create_server(IssuesClient(Tokens(), httpx.Client(transport=httpx.MockTransport(endpoint)))).run(transport="stdio", show_banner=False)
'''

    async def exercise():
        transport = StdioTransport(command=sys.executable, args=["-c", fixture_code],
                                   cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False)
        async with Client(transport, timeout=20) as client:
            result = await client.call_tool("list_issues", {"page_size": 2})
            assert not result.is_error
            assert [item["issue_number"] for item in result.data["issues"]] == [4]
            assert result.data["pagination"]["next_page"] == 2
            assert result.data["pagination"]["upstream_count"] == 2
            assert result.data["pagination"]["returned_count"] == 1
            selected = result.data["issues"][0]["issue_number"]
            detail = await client.call_tool("get_issue", {"issue_number": selected})
            assert not detail.is_error
            assert detail.data["issue"]["issue_number"] == selected
            assert detail.data["issue"]["body"] == "fixture body"

    asyncio.run(exercise())
