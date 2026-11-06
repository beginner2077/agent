"""固定测试仓库的Issue操作；写入仅限#5的state，不暴露凭据。"""

import httpx

from .oauth_login import OAuthError, REPOSITORY, load_settings, local_directory
from .token_store import LOGIN_COMMAND, TokenStore


MAX_PAGE = 100
MAX_PAGE_SIZE = 10
TITLE_LIMIT = 200
BODY_LIMIT = 4000
STATE_CHANGE_ISSUE = 5
ISSUES_URL = f"https://api.github.com/repos/{REPOSITORY}/issues"


class IssueError(OAuthError):
    """业务错误沿用安全的 code/message/retryable 结构。"""


def read_json(response: httpx.Response):
    try:
        return response.json()
    except ValueError:
        raise IssueError("upstream_invalid", "GitHub 返回了无效 JSON。") from None


def summarize_issue(row: dict) -> dict:
    number = row.get("number")
    if (type(number) is not int or number <= 0 or not isinstance(row.get("title"), str)
            or row.get("state") not in ("open", "closed")
            or row.get("html_url") != f"https://github.com/{REPOSITORY}/issues/{number}"):
        raise IssueError("upstream_invalid", "GitHub Issue 字段或仓库来源不符合预期。")
    return {"issue_number": number, "title": row["title"][:TITLE_LIMIT],
            "title_truncated": len(row["title"]) > TITLE_LIMIT,
            "state": row["state"], "url": row["html_url"]}


class IssuesClient:
    def __init__(self, tokens: TokenStore, client: httpx.Client):
        self.tokens = tokens
        self.client = client

    def close(self):
        self.client.close()

    def _request(self, method: str, url: str, *, params=None, json=None) -> httpx.Response:
        access_token = self.tokens.access_token()
        writing = method == "PATCH"
        try:
            response = self.client.request(method, url, params=params, json=json, headers={
                "Authorization": "Bearer " + access_token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            }, follow_redirects=False)
        except httpx.RequestError:
            if writing:
                raise IssueError("write_outcome_unknown", "修改请求的网络结果未知；请先读取#5状态，不要盲目重试。") from None
            raise IssueError("github_unavailable", "GitHub 查询网络失败，本次没有取得结果，可稍后重试。", True) from None
        status = response.status_code
        if status == 401:
            raise IssueError("auth_required", "GitHub 拒绝当前凭据，请独立重新登录：" + LOGIN_COMMAND)
        if status == 429 or (status == 403 and (
                response.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in response.headers)):
            raise IssueError("rate_limited", "GitHub 暂时限流；写操作先核对状态，不自动重试。", not writing)
        if status == 403:
            raise IssueError("forbidden", "GitHub 拒绝操作，请检查权限、组织策略或限流信息。")
        if status == 404:
            raise IssueError("not_found_or_forbidden", "资源不存在或对当前授权不可见，请核对仓库、编号及安装范围。")
        if status != 200:
            if writing:
                if status in (410, 422):
                    raise IssueError("write_rejected", f"GitHub 拒绝修改（HTTP {status}），请核对目标和参数。")
                raise IssueError("write_outcome_unknown", f"修改返回HTTP {status}，未确认结果；请先读取#5状态，不要盲目重试。")
            raise IssueError("github_http_error", f"GitHub 查询返回 HTTP {status}，未取得结果。", status >= 500)
        return response

    def list_issues(self, state="open", page=1, page_size=10) -> dict:
        if (state not in ("open", "closed", "all")
                or type(page) is not int or not 1 <= page <= MAX_PAGE
                or type(page_size) is not int or not 1 <= page_size <= MAX_PAGE_SIZE):
            raise IssueError("invalid_arguments", "请使用有效状态、1至100的页码和1至10的每页条数。")
        response = self._request("GET", ISSUES_URL, params={
            "state": state, "page": page, "per_page": page_size,
            "sort": "created", "direction": "desc",
        })
        rows = read_json(response)
        if not isinstance(rows, list) or len(rows) > page_size:
            raise IssueError("upstream_invalid", "GitHub 列表结构或条数不符合本次请求。")
        issues = []
        for row in rows:
            if not isinstance(row, dict):
                raise IssueError("upstream_invalid", "GitHub 列表包含无效记录。")
            if "pull_request" in row:
                continue
            item = summarize_issue(row)
            if state != "all" and item["state"] != state:
                raise IssueError("upstream_invalid", "GitHub Issue 状态不符合本次筛选。")
            issues.append(item)
        # 不直接跟随上游提供的 URL；下一次仍请求代码中固定的端点。
        has_next = "next" in response.links
        return {"repository": REPOSITORY, "issues": issues, "pagination": {
            "page": page, "page_size": page_size, "upstream_count": len(rows),
            "returned_count": len(issues), "has_next_page": has_next,
            "next_page": page + 1 if has_next and page < MAX_PAGE else None,
            "page_limit_reached": has_next and page == MAX_PAGE,
        }}

    def get_issue(self, issue_number: int) -> dict:
        if type(issue_number) is not int or issue_number <= 0:
            raise IssueError("invalid_arguments", "issue_number 必须是正整数。")
        row = read_json(self._request("GET", f"{ISSUES_URL}/{issue_number}"))
        if not isinstance(row, dict):
            raise IssueError("upstream_invalid", "GitHub 详情不是有效对象。")
        if "pull_request" in row:
            raise IssueError("not_an_issue", "该编号属于PR，本工具只读取Issue。")
        item = summarize_issue(row)
        if item["issue_number"] != issue_number:
            raise IssueError("upstream_invalid", "GitHub 返回的编号与请求不符。")
        if "body" not in row or (row["body"] is not None and not isinstance(row["body"], str)):
            raise IssueError("upstream_invalid", "GitHub 正文结构不符合预期。")
        body = row["body"] or ""
        item.update({"body": body[:BODY_LIMIT], "body_length": len(body),
                     "body_truncated": len(body) > BODY_LIMIT})
        return {"repository": REPOSITORY, "issue": item}

    def set_issue_state(self, issue_number: int, state: str, dry_run: bool = True) -> dict:
        if (type(issue_number) is not int or issue_number <= 0
                or state not in ("open", "closed") or type(dry_run) is not bool):
            raise IssueError("invalid_arguments", "请使用正整数编号、open/closed状态和布尔dry_run。")
        if issue_number != STATE_CHANGE_ISSUE:
            raise IssueError("target_not_allowed", "状态操作仅限专用测试Issue #5。")
        current = self.get_issue(issue_number)["issue"]
        would_change = current["state"] != state
        result = {
            "repository": REPOSITORY, "issue_number": issue_number,
            "title": current["title"], "title_truncated": current["title_truncated"], "url": current["url"],
            "current_state": current["state"], "target_state": state,
            "dry_run": dry_run, "would_change": would_change, "applied": False,
            # 返回计划不会执行；只有显式dry_run=false才会进入下方写分支。
            "planned_request": {"method": "PATCH", "url": f"{ISSUES_URL}/{issue_number}",
                                "json": {"state": state}} if would_change else None,
        }
        if dry_run:
            return result
        if not would_change:
            return {**result, "verified": True, "verified_state": current["state"]}
        response = self._request("PATCH", f"{ISSUES_URL}/{issue_number}", json={"state": state})
        try:
            row = read_json(response)
            if not isinstance(row, dict) or "pull_request" in row:
                raise IssueError("upstream_invalid", "修改响应不是Issue。")
            updated = summarize_issue(row)
            if updated["issue_number"] != issue_number or updated["state"] != state:
                raise IssueError("upstream_invalid", "修改响应与目标不符。")
        except IssueError:
            raise IssueError("write_outcome_unknown", "已收到修改响应，但无法确认目标和状态；请先读取#5，不要盲目重试。") from None
        result.update({"applied": True, "verified": False, "verified_state": None})
        try:
            observed = self.get_issue(issue_number)["issue"]["state"]
        except OAuthError as error:
            result["verification_error"] = {"error": error.code, "message": str(error)}
            return result
        result.update({"verified": observed == state, "verified_state": observed})
        if not result["verified"]:
            result["verification_error"] = {"error": "state_mismatch", "message": "修改已确认，但回读状态与目标不符；停止，不自动重试。"}
        return result


def configured_client() -> IssuesClient:
    """仅在业务工具首次调用时加载本机配置，进程内复用同一 TokenStore。"""
    directory = local_directory()
    settings = load_settings(directory / ".env")
    client = httpx.Client(timeout=20, follow_redirects=False)
    return IssuesClient(TokenStore(settings, directory / "tokens.json", client), client)
