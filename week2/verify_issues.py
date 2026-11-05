"""通过真实stdio读取列表/详情并可预览状态；默认不启动服务或访问凭据。"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from .github_issues import STATE_CHANGE_ISSUE


def show_tool_error(result, total: int):
    print(f"{total}/{total} 工具返回错误，查询未完成。")
    for content in result.content:
        if content.type == "text":
            print(content.text)


async def read_once(detail_number: int | None = None, preview_state: str | None = None) -> int:
    total = 5 if preview_state is not None else (4 if detail_number is not None else 3)
    transport = StdioTransport(command=sys.executable, args=["-m", "week2.server"],
                               cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False)
    print(f"1/{total} 正在启动本项目 MCP Server 并发现工具。", flush=True)
    async with Client(transport, timeout=50) as client:
        tools = await client.list_tools()
        names = [tool.name for tool in tools]
        if ("list_issues" not in names or (detail_number is not None and "get_issue" not in names)
                or (preview_state is not None and "set_issue_state" not in names)):
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
            if preview_state is None:
                print("4/4 MCP只读列表→详情串联成功；未修改Issue。")
            else:
                print(f"4/5 已读取#{selected['issue_number']}详情，正在默认预览目标状态{preview_state}。", flush=True)
                # 故意不传dry_run，验证工具的默认值确实为预览。
                preview = await client.call_tool("set_issue_state", {
                    "issue_number": selected["issue_number"], "state": preview_state,
                }, raise_on_error=False)
                if preview.is_error:
                    show_tool_error(preview, total)
                    return 1
                if preview.data.get("dry_run") is not True or preview.data.get("applied") is not False:
                    print("5/5 返回结果不符合预览契约，不能视为未写入；流程已停止。")
                    return 1
                output["preview_result"] = preview.data
                print("5/5 列表→详情→默认预览串联成功；applied=false。")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read", action="store_true", help="启动MCP子进程并读取一页真实GitHub Issue")
    parser.add_argument("--detail", type=int, help="从本页结果中选择指定Issue编号，再调用详情工具")
    parser.add_argument("--preview-state", choices=("open", "closed"), help="仅预览专用#5目标状态，不执行写入")
    args = parser.parse_args()
    if args.detail is not None and (args.detail <= 0 or not args.read):
        parser.error("--detail 需要正整数编号，并与 --read 一起使用")
    if args.preview_state is not None and (not args.read or args.detail != STATE_CHANGE_ISSUE):
        parser.error("--preview-state 需要 --read --detail 5，当前只预览专用测试Issue")
    if not args.read:
        print("仅说明：未启动服务或读取凭据。加 --read 读取列表；加 --detail 4 串联详情；加 --detail 5 --preview-state closed 预览状态。详情及预览需与 --read 一起使用，不强制刷新或修改Issue。")
        return 0
    try:
        return asyncio.run(read_once(args.detail, args.preview_state))
    except KeyboardInterrupt:
        print("查询已中断。")
    except Exception:
        print("MCP客户端执行未完成，请核对解释器、服务启动及本机配置；本次查询流程未完成。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
