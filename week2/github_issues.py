"""固定测试仓库的只读业务逻辑，不直接暴露凭据或上游原始响应。"""

import httpx

from .oauth_login import OAuthError, REPOSITORY, load_settings, local_directory
from .token_store import LOGIN_COMMAND, TokenStore


MAX_PAGE = 100
MAX_PAGE_SIZE = 10
TITLE_LIMIT = 200
ISSUES_URL = f"https://api.github.com/repos/{REPOSITORY}/issues"


class IssueError(OAuthError):
    """业务错误沿用安全的 code/message/retryable 结构。"""


class IssuesClient:
    def __init__(self, tokens: TokenStore, client: httpx.Client):
        self.tokens = tokens
        self.client = client

    def close(self):
        self.client.close()

    def list_issues(self, state="open", page=1, page_size=10) -> dict:
        if (state not in ("open", "closed", "all")
                or type(page) is not int or not 1 <= page <= MAX_PAGE
                or type(page_size) is not int or not 1 <= page_size <= MAX_PAGE_SIZE):
            raise IssueError("invalid_arguments", "请使用有效状态、1至100的页码和1至10的每页条数。")
        access_token = self.tokens.access_token()
        try:
            response = self.client.get(ISSUES_URL, params={
                "state": state, "page": page, "per_page": page_size,
                "sort": "created", "direction": "desc",
            }, headers={
                "Authorization": "Bearer " + access_token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            }, follow_redirects=False)
        except httpx.RequestError:
            raise IssueError("github_unavailable", "GitHub 查询网络失败，本次没有取得列表，可稍后重试。", True) from None
        status = response.status_code
        if status == 401:
            raise IssueError("auth_required", "GitHub 拒绝当前凭据，请独立重新登录：" + LOGIN_COMMAND)
        if status == 429 or (status == 403 and (
                response.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in response.headers)):
            raise IssueError("rate_limited", "GitHub 暂时限流，请稍后重试。", True)
        if status == 403:
            raise IssueError("forbidden", "GitHub 拒绝读取，请检查权限、组织策略或限流信息。")
        if status == 404:
            raise IssueError("not_found_or_forbidden", "测试仓库不存在或对当前授权不可见，请核对安装范围。")
        if status != 200:
            raise IssueError("github_http_error", f"GitHub 查询返回 HTTP {status}，未取得列表。", status >= 500)
        try:
            rows = response.json()
        except ValueError:
            raise IssueError("upstream_invalid", "GitHub 返回了无效 JSON。") from None
        if not isinstance(rows, list) or len(rows) > page_size:
            raise IssueError("upstream_invalid", "GitHub 列表结构或条数不符合本次请求。")
        issues = []
        for row in rows:
            if not isinstance(row, dict):
                raise IssueError("upstream_invalid", "GitHub 列表包含无效记录。")
            if "pull_request" in row:
                continue
            number = row.get("number")
            if (type(number) is not int or number <= 0 or not isinstance(row.get("title"), str)
                    or row.get("state") not in ("open", "closed")
                    or (state != "all" and row["state"] != state)
                    or row.get("html_url") != f"https://github.com/{REPOSITORY}/issues/{number}"):
                raise IssueError("upstream_invalid", "GitHub Issue 字段或仓库来源不符合预期。")
            issues.append({
                "issue_number": number, "title": row["title"][:TITLE_LIMIT],
                "title_truncated": len(row["title"]) > TITLE_LIMIT,
                "state": row["state"], "url": row["html_url"],
            })
        # 不直接跟随上游提供的 URL；下一次仍请求代码中固定的端点。
        has_next = "next" in response.links
        return {"repository": REPOSITORY, "issues": issues, "pagination": {
            "page": page, "page_size": page_size, "upstream_count": len(rows),
            "returned_count": len(issues), "has_next_page": has_next,
            "next_page": page + 1 if has_next and page < MAX_PAGE else None,
            "page_limit_reached": has_next and page == MAX_PAGE,
        }}


def configured_client() -> IssuesClient:
    """仅在业务工具首次调用时加载本机配置，进程内复用同一 TokenStore。"""
    directory = local_directory()
    settings = load_settings(directory / ".env")
    client = httpx.Client(timeout=20, follow_redirects=False)
    return IssuesClient(TokenStore(settings, directory / "tokens.json", client), client)
