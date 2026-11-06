"""固定仓库列表的离线业务测试：所有上游响应均为虚构数据。"""

import json
import time

import httpx
import pytest

from week2 import github_issues as api
from week2 import oauth_login as oauth
from week2.oauth_login import OAuthError


class Tokens:
    def __init__(self):
        self.calls = 0

    def access_token(self):
        self.calls += 1
        return "fictional-access"


def issue(number=4, **changes):
    row = {"id": 999999, "number": number, "title": "练习Issue", "state": "open",
           "html_url": f"https://github.com/beginner2077/agent/issues/{number}",
           "body": "omitted-private-body", "user": {"private": "omitted-profile"}}
    row.update(changes)
    return row


def test_request_is_bounded_and_result_excludes_pr_body_profile_and_credentials():
    tokens = Tokens()
    calls = []

    def endpoint(request):
        calls.append(request)
        assert request.method == "GET" and str(request.url).split("?")[0] == api.ISSUES_URL
        assert dict(request.url.params) == {"state": "all", "page": "2", "per_page": "3", "sort": "created", "direction": "desc"}
        assert request.headers["Authorization"] == "Bearer fictional-access"
        return httpx.Response(200, json=[issue(title="长" * 220), {"pull_request": {}}, issue(5, state="closed")],
                              headers={"Link": f'<{api.ISSUES_URL}?page=3&per_page=3>; rel="next"'})

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        result = api.IssuesClient(tokens, http).list_issues("all", 2, 3)
    assert tokens.calls == 1 and len(calls) == 1
    assert [item["issue_number"] for item in result["issues"]] == [4, 5]
    assert result["issues"][0]["title"] == "长" * 200
    assert result["issues"][0]["title_truncated"]
    assert result["pagination"] == {"page": 2, "page_size": 3, "upstream_count": 3,
                                    "returned_count": 2, "has_next_page": True,
                                    "next_page": 3, "page_limit_reached": False}
    public = json.dumps(result)
    for excluded in ("fictional-access", "omitted-private-body", "omitted-profile", "999999"):
        assert excluded not in public


@pytest.mark.parametrize("changes", [{"state": "invalid"}, {"page": 0}, {"page": 101},
                                     {"page": True}, {"page": "1"}, {"page_size": 0}, {"page_size": 11}])
def test_invalid_arguments_do_not_get_credentials_or_make_requests(changes):
    tokens = Tokens()
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(tokens, http).list_issues(**changes)
    assert error.value.code == "invalid_arguments" and tokens.calls == 0


@pytest.mark.parametrize("page", [1, 100])
def test_pr_only_page_preserves_upstream_next_page_and_local_limit(page):
    def endpoint(request):
        return httpx.Response(200, json=[{"pull_request": {}}],
                              headers={"Link": f'<{api.ISSUES_URL}?page={page + 1}>; rel="next"'})

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        result = api.IssuesClient(Tokens(), http).list_issues(page=page)
    assert result["issues"] == [] and result["pagination"]["has_next_page"]
    assert result["pagination"]["next_page"] == (2 if page == 1 else None)
    assert result["pagination"]["page_limit_reached"] == (page == 100)


@pytest.mark.parametrize("status,headers,code,retryable", [
    (401, {}, "auth_required", False),
    (403, {}, "forbidden", False),
    (403, {"X-RateLimit-Remaining": "0"}, "rate_limited", True),
    (429, {}, "rate_limited", True),
    (404, {}, "not_found_or_forbidden", False),
    (500, {}, "github_http_error", True),
    (301, {"Location": "https://example.com/other"}, "github_http_error", False),
])
def test_http_errors_are_not_empty_lists_and_never_follow_redirects(status, headers, code, retryable):
    calls = []

    def endpoint(request):
        calls.append(request)
        return httpx.Response(status, text="private-response-body", headers=headers)

    with httpx.Client(transport=httpx.MockTransport(endpoint), follow_redirects=True) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).list_issues()
    assert error.value.code == code and error.value.retryable == retryable
    assert len(calls) == 1 and "private-response-body" not in str(error.value)


@pytest.mark.parametrize("payload", [{}, [None], [issue(number=True)], [issue(title=None)],
                                    [issue(html_url="https://github.com/other/repo/issues/4")],
                                    [issue(state="closed")], [issue(), issue(5)]])
def test_malformed_or_wrong_scope_records_are_rejected(payload):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).list_issues(page_size=1)
    assert error.value.code == "upstream_invalid"


def test_invalid_json_and_network_failure_are_safe_errors():
    for network in (False, True):
        def endpoint(request):
            if network:
                raise httpx.ReadTimeout("private-response-body", request=request)
            return httpx.Response(200, text="private-response-body")

        with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
            with pytest.raises(api.IssueError) as error:
                api.IssuesClient(Tokens(), http).list_issues()
        assert error.value.code == ("github_unavailable" if network else "upstream_invalid")
        assert "private-response-body" not in str(error.value)


def test_auth_failure_stops_before_issue_request():
    class FailedTokens:
        def access_token(self):
            raise OAuthError("auth_required", "需要独立登录")

    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as http:
        with pytest.raises(OAuthError) as error:
            api.IssuesClient(FailedTokens(), http).list_issues()
    assert error.value.code == "auth_required"


def test_configured_client_uses_real_token_store_cache_without_forcing_refresh(tmp_path, monkeypatch):
    directory = tmp_path / "private"
    settings = oauth.Settings("example-client", "fictional-secret")
    oauth.save_tokens(directory / "tokens.json", {
        "client_id": settings.client_id, "repository": settings.repository,
        "token_type": "bearer", "access_token": "cached-fictional-access", "refresh_token": "cached-fictional-refresh",
        "expires_at": int(time.time()) + 3600, "refresh_expires_at": int(time.time()) + 7200,
    })
    calls = []
    real_client = httpx.Client

    def load(path):
        assert path == directory / ".env"
        return settings

    def endpoint(request):
        calls.append(request.method)
        assert request.method == "GET" and request.headers["Authorization"] == "Bearer cached-fictional-access"
        return httpx.Response(200, json=[])

    monkeypatch.setattr(api, "local_directory", lambda: directory)
    monkeypatch.setattr(api, "load_settings", load)
    monkeypatch.setattr(api.httpx, "Client", lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(endpoint)))
    client = api.configured_client()
    try:
        assert client.list_issues()["issues"] == []
    finally:
        client.close()
    assert calls == ["GET"]


def test_detail_uses_requested_number_and_bounds_body_without_extra_fields():
    calls = []
    body = "正文\n" * 1500

    def endpoint(request):
        calls.append(request)
        assert request.method == "GET" and str(request.url) == api.ISSUES_URL + "/4"
        assert request.headers["Authorization"] == "Bearer fictional-access"
        return httpx.Response(200, json=issue(body=body))

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        result = api.IssuesClient(Tokens(), http).get_issue(4)
    detail = result["issue"]
    assert result["repository"] == "beginner2077/agent"
    assert detail["issue_number"] == 4 and detail["body"] == body[:4000]
    assert detail["body_length"] == len(body) and detail["body_truncated"]
    assert len(calls) == 1
    public = json.dumps(result)
    for excluded in ("fictional-access", "omitted-profile", "999999"):
        assert excluded not in public


@pytest.mark.parametrize("body", [None, "", "短正文\n保留换行", "x" * 4000])
def test_empty_and_untruncated_bodies_are_preserved(body):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=issue(body=body)))) as http:
        detail = api.IssuesClient(Tokens(), http).get_issue(4)["issue"]
    assert detail["body"] == (body or "")
    assert detail["body_length"] == len(body or "") and not detail["body_truncated"]


@pytest.mark.parametrize("number", [0, -1, True, "4", None])
def test_detail_rejects_invalid_number_before_credentials_or_network(number):
    tokens = Tokens()
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(tokens, http).get_issue(number)
    assert error.value.code == "invalid_arguments" and tokens.calls == 0


@pytest.mark.parametrize("payload,code", [
    ([issue()], "upstream_invalid"),
    ({"pull_request": {}, "body": "private-pr-body"}, "not_an_issue"),
    (issue(5), "upstream_invalid"),
    (issue(body=[]), "upstream_invalid"),
    ({key: value for key, value in issue().items() if key != "body"}, "upstream_invalid"),
])
def test_detail_rejects_pr_wrong_number_or_invalid_body(payload, code):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).get_issue(4)
    assert error.value.code == code and "private-pr-body" not in str(error.value)


def test_missing_detail_returns_safe_not_found_error():
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(404, text="private-response-body"))) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).get_issue(4)
    assert error.value.code == "not_found_or_forbidden"
    assert "private-response-body" not in str(error.value)


@pytest.mark.parametrize("current_state", ["open", "closed"])
def test_default_state_preview_only_reads_and_builds_plan_if_needed(current_state):
    calls = []

    def endpoint(request):
        calls.append(request.method)
        assert request.method == "GET" and str(request.url) == api.ISSUES_URL + "/5"
        return httpx.Response(200, json=issue(5, state=current_state, body="preview-private-body"))

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        result = api.IssuesClient(Tokens(), http).set_issue_state(5, "closed")
    assert calls == ["GET"]
    assert result["dry_run"] is True and result["applied"] is False
    assert result["current_state"] == current_state and result["target_state"] == "closed"
    assert result["would_change"] == (current_state != "closed")
    assert result["planned_request"] == ({"method": "PATCH", "url": api.ISSUES_URL + "/5",
                                          "json": {"state": "closed"}} if current_state != "closed" else None)
    assert "fictional-access" not in json.dumps(result) and "preview-private-body" not in json.dumps(result)


@pytest.mark.parametrize("arguments,code", [
    ({"issue_number": 4, "state": "closed"}, "target_not_allowed"),
    ({"issue_number": "5", "state": "closed"}, "invalid_arguments"),
    ({"issue_number": 5.0, "state": "closed"}, "invalid_arguments"),
    ({"issue_number": True, "state": "closed"}, "invalid_arguments"),
    ({"issue_number": 0, "state": "closed"}, "invalid_arguments"),
    ({"issue_number": 5, "state": "all"}, "invalid_arguments"),
    ({"issue_number": 5, "state": "closed", "dry_run": "true"}, "invalid_arguments"),
    ({"issue_number": 5, "state": "closed", "dry_run": 1}, "invalid_arguments"),
])
def test_state_operation_blocks_other_targets_and_invalid_values(arguments, code):
    tokens = Tokens()
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(tokens, http).set_issue_state(**arguments)
    assert error.value.code == code and tokens.calls == 0


def test_state_preview_rejects_pr_without_a_write_request():
    calls = []

    def endpoint(request):
        calls.append(request.method)
        assert request.method == "GET"
        return httpx.Response(200, json={"pull_request": {}, "body": "private-pr-body"})

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).set_issue_state(5, "closed")
    assert error.value.code == "not_an_issue" and calls == ["GET"]


@pytest.mark.parametrize("target", ["closed", "open"])
def test_explicit_write_only_changes_state_then_reads_back(target):
    current = "open" if target == "closed" else "closed"
    calls = []

    def endpoint(request):
        nonlocal current
        assert str(request.url) == api.ISSUES_URL + "/5"
        assert request.headers["Authorization"] == "Bearer fictional-access"
        calls.append(request.method)
        if request.method == "PATCH":
            assert json.loads(request.content) == {"state": target}
            current = target
        else:
            assert request.method == "GET"
        return httpx.Response(200, json=issue(5, state=current))

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        client = api.IssuesClient(Tokens(), http)
        result = client.set_issue_state(5, target, dry_run=False)
        repeated = client.set_issue_state(5, target, dry_run=False)
    assert calls == ["GET", "PATCH", "GET", "GET"]
    assert result["applied"] is True and result["verified"] is True and result["dry_run"] is False
    assert result["verified_state"] == target
    assert repeated["applied"] is False and repeated["would_change"] is False
    assert repeated["verified"] is True and repeated["planned_request"] is None


@pytest.mark.parametrize("arguments", [
    {"issue_number": 4, "state": "closed", "dry_run": False},
    {"issue_number": 5, "state": "closed", "dry_run": 0},
])
def test_invalid_write_does_not_load_tokens_or_send_http(arguments):
    tokens = Tokens()
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as http:
        with pytest.raises(api.IssueError):
            api.IssuesClient(tokens, http).set_issue_state(**arguments)
    assert tokens.calls == 0


@pytest.mark.parametrize("failure,code", [
    ("timeout", "write_outcome_unknown"), (503, "write_outcome_unknown"),
    (302, "write_outcome_unknown"), (401, "auth_required"), (403, "forbidden"),
    (404, "not_found_or_forbidden"), (422, "write_rejected"), (429, "rate_limited"),
    ("invalid_json", "write_outcome_unknown"), ("wrong_state", "write_outcome_unknown"),
    ("wrong_number", "write_outcome_unknown"), ("pr", "write_outcome_unknown"),
])
def test_write_failures_do_not_retry_or_claim_no_write(failure, code):
    calls = []

    def endpoint(request):
        calls.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json=issue(5))
        assert request.method == "PATCH"
        if failure == "timeout":
            raise httpx.ReadTimeout("private-response-body", request=request)
        if type(failure) is int:
            return httpx.Response(failure, text="private-response-body", headers={"Location": "https://example.com"})
        if failure == "invalid_json":
            return httpx.Response(200, text="private-response-body")
        row = issue(4 if failure == "wrong_number" else 5,
                    state="open" if failure == "wrong_state" else "closed")
        if failure == "pr":
            row["pull_request"] = {}
        return httpx.Response(200, json=row)

    with httpx.Client(transport=httpx.MockTransport(endpoint), follow_redirects=True) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).set_issue_state(5, "closed", False)
    assert error.value.code == code and error.value.retryable is False
    assert calls == ["GET", "PATCH"]
    assert "private-response-body" not in str(error.value) and "fictional-access" not in str(error.value)


@pytest.mark.parametrize("after", ["mismatch", "timeout", "auth"])
def test_confirmed_patch_but_failed_readback_preserves_applied_without_claiming_verified(after):
    calls = []

    def endpoint(request):
        calls.append(request.method)
        if len(calls) == 1:
            return httpx.Response(200, json=issue(5))
        if request.method == "PATCH":
            return httpx.Response(200, json=issue(5, state="closed"))
        if after == "timeout":
            raise httpx.ReadTimeout("private-response-body", request=request)
        return httpx.Response(401, text="private-response-body") if after == "auth" else httpx.Response(200, json=issue(5))

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        result = api.IssuesClient(Tokens(), http).set_issue_state(5, "closed", False)
    assert calls == ["GET", "PATCH", "GET"]
    assert result["applied"] is True and result["verified"] is False
    assert result["verification_error"]["error"] == {"mismatch": "state_mismatch", "timeout": "github_unavailable", "auth": "auth_required"}[after]
    assert "private-response-body" not in json.dumps(result)


def test_failed_pre_read_does_not_send_patch():
    calls = []
    def endpoint(request):
        calls.append(request.method)
        return httpx.Response(403, text="private-response-body")
    with httpx.Client(transport=httpx.MockTransport(endpoint)) as http:
        with pytest.raises(api.IssueError) as error:
            api.IssuesClient(Tokens(), http).set_issue_state(5, "closed", False)
    assert error.value.code == "forbidden" and calls == ["GET"]
