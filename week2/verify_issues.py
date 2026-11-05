"""通过真实 stdio 读取列表，可串联详情；默认不启动服务或访问凭据。"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


def show_tool_error(result, total: int):
    print(f"{total}/{total} 工具返回错误，查询未完成。")
    for content in result.content:
        if content.type == "text":
            print(content.text)


async def read_once(detail_number: int | None = None) -> int:
    total = 4 if detail_number is not None else 3
    transport = StdioTransport(command=sys.executable, args=["-m", "week2.server"],
                               cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False)
    print(f"1/{total} 正在启动本项目 MCP Server 并发现工具。", flush=True)
    async with Client(transport, timeout=50) as client:
        tools = await client.list_tools()
        names = [tool.name for tool in tools]
        if "list_issues" not in names or (detail_number is not None and "get_issue" not in names):
            print("未发现本次所需工具，未执行业务调用。")
            return 1
        print(f"2/{total} 已发现 list_issues；正在只读查询固定仓库第一页（含开关两种状态）。", flush=True)
        result = await client.call_tool("list_issues", {"state": "all", "page": 1, "page_size": 10}, raise_on_error=False)
        if result.is_error:
            show_tool_error(result, total)
            return 1
        output = {"protocol": client.protocol_version, "tools": names}
        if detail_number is None:
            output["result"] = result.data
            print("3/3 MCP只读列表调用成功；未修改Issue。")
        else:
            selected = next((item for item in result.data["issues"] if item["issue_number"] == detail_number), None)
            if selected is None:
                print(f"3/{total} 本页未找到目标#{detail_number}，未调用详情；请核对列表及分页范围。")
                return 1
            print(f"3/{total} 从列表取得issue_number={selected['issue_number']}，正在调用get_issue。", flush=True)
            detail = await client.call_tool("get_issue", {"issue_number": selected["issue_number"]}, raise_on_error=False)
            if detail.is_error:
                show_tool_error(detail, total)
                return 1
            output.update({"list_result": result.data, "detail_result": detail.data})
            print("4/4 MCP只读列表→详情串联成功；未修改Issue。")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read", action="store_true", help="启动MCP子进程并读取一页真实GitHub Issue")
    parser.add_argument("--detail", type=int, help="从本页结果中选择指定Issue编号，再调用详情工具")
    args = parser.parse_args()
    if args.detail is not None and (args.detail <= 0 or not args.read):
        parser.error("--detail 需要正整数编号，并与 --read 一起使用")
    if not args.read:
        print("仅说明：未启动服务或读取凭据。加 --read 读取列表，加 --read --detail 4 串联读取本页#4详情；不强制刷新或修改Issue。")
        return 0
    try:
        return asyncio.run(read_once(args.detail))
    except KeyboardInterrupt:
        print("查询已中断。")
    except Exception:
        print("MCP客户端执行未完成，请核对解释器、服务启动及本机配置；本次查询流程未完成。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
