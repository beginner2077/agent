"""MCP参数、结果和错误映射测试；上游只使用MockTransport。"""

import asyncio
import json
import sys

from fastmcp import Client
import httpx
import pytest

from week2 import github_issues as api
from week2 import server
from week2 import verify_issues as check


class Tokens:
    def access_token(self):
        return "fictional-access"


def make_server(status=200, calls=None, detail_status=200, number=4, current_state="open", writes=None):
    def endpoint(request):
        nonlocal current_state
        if request.method == "PATCH":
            assert writes is not None and number == 5
            payload = json.loads(request.content)
            assert set(payload) == {"state"} and payload["state"] in ("open", "closed")
            writes.append(payload)
            current_state = payload["state"]
        else:
            assert request.method == "GET"
        url = str(request.url).split("?")[0]
        assert url in (api.ISSUES_URL, api.ISSUES_URL + f"/{number}")
        if calls is not None:
            calls.append(url)
        if status != 200:
            return httpx.Response(status, text="private-response-body")
        row = {"number": number, "id": 999999, "title": "练习Issue", "state": current_state,
               "html_url": f"https://github.com/beginner2077/agent/issues/{number}", "body": "详情正文"}
        if url.endswith(f"/{number}"):
            return httpx.Response(200, json=row) if detail_status == 200 else httpx.Response(detail_status, text="private-response-body")
        return httpx.Response(200, json=[row])

    return server.create_server(api.IssuesClient(Tokens(), httpx.Client(transport=httpx.MockTransport(endpoint))))


def test_schema_validation_and_ping_do_not_load_credentials(monkeypatch):
    calls = []

    def unexpected():
        calls.append(True)
        raise AssertionError("must not load credentials")

    monkeypatch.setattr(server, "configured_client", unexpected)

    async def exercise():
        async with Client(server.create_server()) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            properties = tools["list_issues"].input_schema["properties"]
            assert set(properties) == {"state", "page", "page_size"}
            assert properties["page_size"]["maximum"] == 10
            assert tools["list_issues"].annotations.read_only_hint
            assert set(tools["get_issue"].input_schema["properties"]) == {"issue_number"}
            assert tools["get_issue"].annotations.read_only_hint
            preview_schema = tools["set_issue_state"].input_schema["properties"]
            assert preview_schema["dry_run"]["type"] == "boolean" and preview_schema["dry_run"]["default"] is True
            assert preview_schema["issue_number"]["const"] == 5
            assert not tools["set_issue_state"].annotations.read_only_hint
            assert tools["set_issue_state"].annotations.destructive_hint
            assert (await client.call_tool("ping", {})).data["status"] == "ok"
            for args in ({"page": 0}, {"page": "1"}, {"page": True}, {"page_size": 11},
                         {"state": "invalid"}, {"repository": "other/repo"}):
                result = await client.call_tool("list_issues", args, raise_on_error=False)
                assert result.is_error
            for args in ({"issue_number": 0}, {"issue_number": True}, {"issue_number": "4"},
                         {"issue_number": 4, "repository": "other/repo"}):
                assert (await client.call_tool("get_issue", args, raise_on_error=False)).is_error
            for args in ({"issue_number": 4, "state": "closed"}, {"issue_number": "5", "state": "closed"},
                         {"issue_number": 5.0, "state": "closed"},
                         {"issue_number": 5, "state": "all"},
                         {"issue_number": 5, "state": "closed", "dry_run": "true"},
                         {"issue_number": 5, "state": "closed", "dry_run": 0},
                         {"issue_number": 5, "state": "closed", "dry_run": 1}):
                assert (await client.call_tool("set_issue_state", args, raise_on_error=False)).is_error
                assert calls == [], f"invalid preview arguments reached credential loading: {args}"

    asyncio.run(exercise())
    assert calls == []


def test_success_is_structured_and_upstream_failure_is_mcp_error():
    async def exercise():
        async with Client(make_server()) as client:
            result = await client.call_tool("list_issues", {})
            assert not result.is_error and result.data["issues"][0]["issue_number"] == 4
        async with Client(make_server(401)) as client:
            result = await client.call_tool("list_issues", {}, raise_on_error=False)
            assert result.is_error
            message = next(item.text for item in result.content if item.type == "text")
            assert json.loads(message)["error"] == "auth_required"
            assert "private-response-body" not in message and "fictional-access" not in message

    asyncio.run(exercise())


def test_unexpected_factory_error_is_masked(monkeypatch, capsys):
    def failed():
        raise ValueError("fictional-private-credential")

    monkeypatch.setattr(server, "configured_client", failed)

    async def exercise():
        async with Client(server.create_server()) as client:
            result = await client.call_tool("list_issues", {}, raise_on_error=False)
            assert result.is_error
            text = next(item.text for item in result.content if item.type == "text")
            assert json.loads(text)["error"] == "internal_error"

    asyncio.run(exercise())
    printed = capsys.readouterr()
    assert "fictional-private-credential" not in printed.out + printed.err


def test_verifier_default_does_not_start_a_server(monkeypatch, capsys):
    def unexpected(**kwargs):
        raise AssertionError("must not start server")

    monkeypatch.setattr(sys, "argv", ["verify_issues"])
    monkeypatch.setattr(check, "StdioTransport", unexpected)
    assert check.main() == 0
    assert "未启动服务" in capsys.readouterr().out


def test_verifier_success_and_tool_failure(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["verify_issues", "--read"])
    for status in (200, 401):
        monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(status))
        assert check.main() == (0 if status == 200 else 1)
        printed = capsys.readouterr()
        assert "private-response-body" not in printed.out + printed.err


def test_list_to_detail_uses_one_lazy_client_and_returned_issue_number(monkeypatch):
    calls, initializations = [], []
    # 连续两个工具调用共用一个延迟加载的客户端。
    def factory():
        initializations.append(True)
        def endpoint(request):
            calls.append(request.url.path)
            row = {"number": 4, "id": 999999, "title": "fixture", "state": "open", "body": "正文",
                   "html_url": "https://github.com/beginner2077/agent/issues/4"}
            return httpx.Response(200, json=row if request.url.path.endswith("/4") else [row])
        return api.IssuesClient(Tokens(), httpx.Client(transport=httpx.MockTransport(endpoint)))

    monkeypatch.setattr(server, "configured_client", factory)

    async def exercise():
        async with Client(server.create_server()) as client:
            listed = await client.call_tool("list_issues", {})
            number = listed.data["issues"][0]["issue_number"]
            detail = await client.call_tool("get_issue", {"issue_number": number})
            assert detail.data["issue"]["issue_number"] == number
            assert detail.data["issue"]["body"] == "正文"

    asyncio.run(exercise())
    assert initializations == [True]
    assert calls == ["/repos/beginner2077/agent/issues", "/repos/beginner2077/agent/issues/4"]


def test_detail_verifier_chains_from_list_and_stops_if_target_absent(monkeypatch, capsys):
    for number in (4, 99):
        calls = []
        monkeypatch.setattr(sys, "argv", ["verify_issues", "--read", "--detail", str(number)])
        monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(calls=calls))
        assert check.main() == (0 if number == 4 else 1)
        printed = capsys.readouterr()
        if number == 4:
            assert calls == [api.ISSUES_URL, api.ISSUES_URL + "/4"]
            assert "4/4 MCP只读列表→详情串联成功" in printed.out
        else:
            assert calls == [api.ISSUES_URL] and "本页未找到目标#99" in printed.out


def test_detail_verifier_does_not_report_success_after_detail_error(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(sys, "argv", ["verify_issues", "--read", "--detail", "4"])
    monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(calls=calls, detail_status=404))
    assert check.main() == 1
    printed = capsys.readouterr()
    assert calls == [api.ISSUES_URL, api.ISSUES_URL + "/4"]
    assert "not_found_or_forbidden" in printed.out
    assert "串联成功" not in printed.out and "private-response-body" not in printed.out + printed.err


def test_preview_verifier_chains_three_tools_and_only_uses_get(monkeypatch, capsys):
    for current_state in ("open", "closed"):
        calls = []
        monkeypatch.setattr(sys, "argv", ["verify_issues", "--read", "--detail", "5", "--preview-state", "closed"])
        monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(calls=calls, number=5, current_state=current_state))
        assert check.main() == 0
        assert calls == [api.ISSUES_URL, api.ISSUES_URL + "/5", api.ISSUES_URL + "/5"]
        printed = capsys.readouterr()
        assert "5/5 列表→详情→默认预览串联成功" in printed.out
        assert '"dry_run": true' in printed.out and '"applied": false' in printed.out
        assert "fictional-access" not in printed.out + printed.err


def test_verifier_rejects_preview_result_claiming_applied(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["verify_issues", "--read", "--detail", "5", "--preview-state", "closed"])
    monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(number=5))
    monkeypatch.setattr(api.IssuesClient, "set_issue_state", lambda *args, **kwargs: {"dry_run": True, "applied": True})
    assert check.main() == 1
    printed = capsys.readouterr()
    assert "不能视为未写入" in printed.out
    assert "默认预览串联成功" not in printed.out


@pytest.mark.parametrize("initial,target", [("open", "closed"), ("closed", "open"), ("closed", "closed")])
def test_apply_cli_previews_then_writes_if_needed_and_verifies(monkeypatch, capsys, initial, target):
    calls, writes = [], []
    monkeypatch.setattr(sys, "argv", ["verify_issues", "--read", "--detail", "5", "--apply-state", target])
    monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(calls=calls, number=5, current_state=initial, writes=writes))
    assert check.main() == 0
    assert writes == ([{"state": target}] if initial != target else [])
    assert len(calls) == (6 if initial != target else 4)
    output = capsys.readouterr().out
    assert '"preview_result"' in output and '"execution_result"' in output
    assert '"verified": true' in output and "6/6 执行流程完成" in output


def test_apply_cli_does_not_report_success_when_write_is_unverified(monkeypatch, capsys):
    original = api.IssuesClient.set_issue_state
    def unverified(self, issue_number, state, dry_run=True):
        if dry_run:
            return original(self, issue_number, state)
        return {"dry_run": False, "applied": True, "would_change": True, "verified": False, "verified_state": None}
    monkeypatch.setattr(api.IssuesClient, "set_issue_state", unverified)
    monkeypatch.setattr(sys, "argv", ["verify_issues", "--read", "--detail", "5", "--apply-state", "closed"])
    monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: make_server(number=5))
    assert check.main() == 1
    output = capsys.readouterr().out
    assert '"applied": true' in output and "可能已写入" in output
    assert "执行流程完成" not in output


@pytest.mark.parametrize("arguments", [
    ["--apply-state", "closed"], ["--read", "--detail", "4", "--apply-state", "closed"],
    ["--read", "--detail", "5", "--apply-state", "closed", "--preview-state", "closed"],
])
def test_invalid_apply_cli_arguments_stop_before_startup(monkeypatch, arguments):
    monkeypatch.setattr(sys, "argv", ["verify_issues", *arguments])
    monkeypatch.setattr(check, "StdioTransport", lambda **kwargs: pytest.fail("must not start server"))
    with pytest.raises(SystemExit) as error:
        check.main()
    assert error.value.code == 2
