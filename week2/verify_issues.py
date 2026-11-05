"""通过真实 stdio 调用只读列表工具；默认不启动服务或访问凭据。"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def read_once() -> int:
    transport = StdioTransport(command=sys.executable, args=["-m", "week2.server"],
                               cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False)
    print("1/3 正在启动本项目 MCP Server 并发现工具。", flush=True)
    async with Client(transport, timeout=50) as client:
        tools = await client.list_tools()
        names = [tool.name for tool in tools]
        if "list_issues" not in names:
            print("未发现 list_issues，未执行业务调用。")
            return 1
        print("2/3 已发现 list_issues；正在只读查询固定仓库第一页（含开关两种状态）。", flush=True)
        result = await client.call_tool("list_issues", {"state": "all", "page": 1, "page_size": 10}, raise_on_error=False)
        if result.is_error:
            print("3/3 工具返回错误，没有取得成功列表。")
            for content in result.content:
                if content.type == "text":
                    print(content.text)
            return 1
        print("3/3 MCP只读列表调用成功；未修改Issue。")
        print(json.dumps({"protocol": client.protocol_version, "tools": names, "result": result.data}, ensure_ascii=False, indent=2))
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read", action="store_true", help="启动MCP子进程并读取一页真实GitHub Issue")
    args = parser.parse_args()
    if not args.read:
        print("仅说明：未启动服务或读取凭据。加 --read 将通过MCP读取固定仓库第一页；不强制刷新或修改Issue。")
        return 0
    try:
        return asyncio.run(read_once())
    except KeyboardInterrupt:
        print("查询已中断。")
    except Exception:
        print("MCP客户端执行未完成，请核对解释器、服务启动及本机配置；未取得成功列表。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
