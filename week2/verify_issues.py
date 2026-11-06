"""通过真实stdio读取/预览，可显式执行#5状态操作；无参数时不访问凭据。"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from .github_issues import STATE_CHANGE_ISSUE


def show_tool_error(result, total: int):
    print(f"{total}/{total} 工具返回错误，流程已停止；写操作需按错误说明核对状态。")
    for content in result.content:
        if content.type == "text":
            print(content.text)


async def read_once(detail_number: int | None = None, preview_state: str | None = None,
                    apply_state: str | None = None) -> int:
    target_state = apply_state or preview_state
    total = 4 if detail_number is not None else 3
    if target_state is not None:
        total = 6 if apply_state is not None else 5
    transport = StdioTransport(command=sys.executable, args=["-m", "week2.server"],
                               cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False)
    print(f"1/{total} 正在启动本项目 MCP Server 并发现工具。", flush=True)
    async with Client(transport, timeout=50) as client:
        tools = await client.list_tools()
        names = [tool.name for tool in tools]
        if ("list_issues" not in names or (detail_number is not None and "get_issue" not in names)
                or (target_state is not None and "set_issue_state" not in names)):
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
            if target_state is None:
                print("4/4 MCP只读列表→详情串联成功；未修改Issue。")
            else:
                print(f"4/{total} 已读取#{selected['issue_number']}详情，正在默认预览目标状态{target_state}。", flush=True)
                # 故意不传dry_run，验证工具的默认值确实为预览。
                preview = await client.call_tool("set_issue_state", {
                    "issue_number": selected["issue_number"], "state": target_state,
                }, raise_on_error=False)
                if preview.is_error:
                    show_tool_error(preview, total)
                    return 1
                if (not isinstance(preview.data, dict) or preview.data.get("dry_run") is not True
                        or preview.data.get("applied") is not False):
                    print(f"{total}/{total} 返回结果不符合预览契约，不能视为未写入；流程已停止。")
                    return 1
                output["preview_result"] = preview.data
                if apply_state is None:
                    print("5/5 列表→详情→默认预览串联成功；applied=false。")
                else:
                    print(json.dumps({"preview_result": preview.data}, ensure_ascii=False, indent=2), flush=True)
                    print(f"5/6 显式执行#5目标状态{apply_state}；工具将重新读取、按需修改并回读。", flush=True)
                    execution = await client.call_tool("set_issue_state", {
                        "issue_number": selected["issue_number"], "state": apply_state, "dry_run": False,
                    }, raise_on_error=False)
                    if execution.is_error:
                        show_tool_error(execution, total)
                        return 1
                    output["execution_result"] = execution.data
                    data = execution.data
                    if (not isinstance(data, dict) or data.get("dry_run") is not False
                            or type(data.get("applied")) is not bool or type(data.get("would_change")) is not bool
                            or data["applied"] != data["would_change"]
                            or data.get("verified") is not True or data.get("verified_state") != apply_state):
                        print(json.dumps(output, ensure_ascii=False, indent=2))
                        print("6/6 执行结果未通过核验；可能已写入，停止且不自动重试。")
                        return 1
                    print("6/6 执行流程完成，回读状态符合目标；是否发送修改见applied。")
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read", action="store_true", help="启动MCP子进程并读取一页真实GitHub Issue")
    parser.add_argument("--detail", type=int, help="从本页结果中选择指定Issue编号，再调用详情工具")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--preview-state", choices=("open", "closed"), help="仅预览专用#5目标状态，不执行写入")
    action.add_argument("--apply-state", choices=("open", "closed"), help="显式执行专用#5目标状态，会按需发送真实修改请求")
    args = parser.parse_args()
    if args.detail is not None and (args.detail <= 0 or not args.read):
        parser.error("--detail 需要正整数编号，并与 --read 一起使用")
    if (args.preview_state is not None or args.apply_state is not None) and (not args.read or args.detail != STATE_CHANGE_ISSUE):
        parser.error("状态操作需要 --read --detail 5，仅限专用测试Issue")
    if not args.read:
        print("仅说明：未启动服务或读取凭据。--read读取列表，配合--detail读取详情；--read --detail 5 --preview-state closed仅预览；改用--apply-state closed会真实执行#5状态操作。不强制刷新令牌。")
        return 0
    try:
        return asyncio.run(read_once(args.detail, args.preview_state, args.apply_state))
    except KeyboardInterrupt:
        print("流程已中断；若使用--apply-state，可能已修改#5，请先读取核对，不自动重试。")
    except Exception:
        print("MCP客户端流程未完成；若使用--apply-state，不能断言未写入，请先读取#5核对，不自动重试。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
