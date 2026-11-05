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
