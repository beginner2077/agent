"""独立 OAuth 登录入口：浏览器授权 → 本机回调 → 换取并保存令牌。"""

import base64
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time
from urllib.parse import parse_qs, urlencode, urlsplit

from dotenv import dotenv_values
import httpx


REDIRECT_URI = "http://127.0.0.1:8765/callback"
REPOSITORY = "beginner2077/agent"
EXPECTED_LOGIN = "beginner2077"
TOKEN_URL = "https://github.com/login/oauth/access_token"


class OAuthError(Exception):
    """只携带我们定义的提示，不拼接远端响应或含凭据的异常。"""

    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str = field(repr=False)
    redirect_uri: str = REDIRECT_URI
    repository: str = REPOSITORY


def local_directory() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "CS146S" / "github-mcp"


def load_settings(path: Path) -> Settings:
    if not path.is_file():
        raise OAuthError("config_missing", "本机 .env 不存在，请先按 README 准备配置。")
    try:
        values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
    except (OSError, UnicodeError):
        raise OAuthError("config_invalid", "无法读取本机配置，请检查文件和编码。") from None
    # 显式环境变量优先；不会修改全局环境，也不会自动搜索其他项目的 .env。
    keys = ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_REDIRECT_URI", "GITHUB_REPOSITORY")
    selected = {key: os.environ.get(key, values.get(key)) for key in keys}
    if any(not isinstance(value, str) or not value.strip() for value in selected.values()):
        raise OAuthError("config_invalid", "本机配置有缺失字段，请检查四个 GITHUB_ 配置项。")
    if selected["GITHUB_REDIRECT_URI"] != REDIRECT_URI or selected["GITHUB_REPOSITORY"] != REPOSITORY:
        raise OAuthError("config_invalid", "回调地址或练习仓库与 README 不一致。")
    return Settings(selected["GITHUB_CLIENT_ID"].strip(), selected["GITHUB_CLIENT_SECRET"].strip())


def pkce_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def authorization_url(settings: Settings, state: str, verifier: str) -> str:
    # verifier 留在进程内；浏览器只携带它的 SHA-256 挑战值。
    return "https://github.com/login/oauth/authorize?" + urlencode({
        "client_id": settings.client_id,
        "redirect_uri": settings.redirect_uri,
        "state": state,
        "code_challenge": pkce_challenge(verifier),
        "code_challenge_method": "S256",
        "scope": "offline_access",
        "login": EXPECTED_LOGIN,
    })


def validate_callback(target: str, expected_state: str) -> str:
    try:
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or parsed.path != "/callback":
            raise ValueError
        query = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=12)
        states = query.get("state", [])
        if len(states) != 1 or not secrets.compare_digest(states[0].encode(), expected_state.encode()):
            raise OAuthError("state_mismatch", "回调 state 不匹配，未接受该回调。")
        if "error" in query:
            raise OAuthError("authorization_denied", "授权未完成，请重新运行登录入口后在 GitHub 确认。")
        codes = query.get("code", [])
        if len(codes) != 1 or not codes[0].strip():
            raise ValueError
        return codes[0]
    except ValueError:
        raise OAuthError("callback_invalid", "回调参数不完整或重复，未接受该回调。") from None


class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 默认 HTTP 日志会记录带 code 的 URL，必须关闭。
        pass

    def do_GET(self):
        if self.path.split("?", 1)[0] != "/callback":
            self.reply(404, "Not found")
            return
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.reply(400, "Invalid host")
            return
        try:
            self.server.code = validate_callback(self.path, self.server.state)
        except OAuthError as error:
            self.reply(400, "回调未接受，请回到终端检查。")
            if error.code == "authorization_denied":
                self.server.auth_error = error
            else:
                print(f"回调未接受（{error.code}），继续等待本次授权。", file=sys.stderr)
            return
        # 此时仅收到回调，令牌交换尚未完成，不能在网页报告登录成功。
        self.reply(200, "授权回调已收到，请回到终端确认令牌交换结果。")

    def reply(self, status: int, text: str):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)


class CallbackServer(HTTPServer):
    def __init__(self, state: str, port: int = 8765):
        super().__init__(("127.0.0.1", port), CallbackHandler)
        self.state = state
        self.code = None
        self.auth_error = None
        self.timeout = 1

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


def exchange_code(client: httpx.Client, settings: Settings, code: str, verifier: str) -> dict:
    try:
        response = client.post(TOKEN_URL, headers={"Accept": "application/json"}, data={
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "redirect_uri": settings.redirect_uri,
            "code": code,
            "code_verifier": verifier,
        })
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as error:
        raise OAuthError("token_http_error", f"令牌端点返回 HTTP {error.response.status_code}，请检查网络及 App 配置。") from None
    except httpx.RequestError:
        raise OAuthError("network_error", "令牌交换网络失败；结果可能不确定，请重新运行登录入口。") from None
    except ValueError:
        raise OAuthError("token_invalid", "令牌端点返回的内容不是有效 JSON。") from None
    return tokens_from_payload(payload, settings)


def tokens_from_payload(payload: object, settings: Settings) -> dict:
    """首次兑换和刷新共用同一份令牌结构及过期时间校验。"""
    if not isinstance(payload, dict):
        raise OAuthError("token_invalid", "令牌响应结构不符合预期。")
    if "error" in payload:
        messages = {
            "incorrect_client_credentials": "Client ID 或 Client Secret 不正确，请检查本机配置。",
            "redirect_uri_mismatch": "Redirect URI 不匹配，请核对 App 注册页与本机配置。",
            "bad_verification_code": "授权码已失效或不能使用，请重新运行登录入口。",
        }
        error_code = payload["error"] if isinstance(payload["error"], str) else "unknown"
        raise OAuthError("token_exchange_failed", messages.get(error_code, "GitHub 拒绝令牌交换，请检查 App 配置后重新登录。"))
    if (any(not isinstance(payload.get(key), str) or not payload[key].strip()
            for key in ("access_token", "refresh_token"))
            or not isinstance(payload.get("token_type"), str)
            or payload["token_type"].lower() != "bearer"
            or any(type(payload.get(key)) is not int or payload[key] <= 0
                   for key in ("expires_in", "refresh_token_expires_in"))):
        raise OAuthError("token_invalid", "缺少可过期访问令牌或刷新令牌，请核对令牌过期设置。")
    now = int(time.time())
    return {
        "client_id": settings.client_id,
        "repository": settings.repository,
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "token_type": "bearer",
        "expires_at": now + payload["expires_in"],
        "refresh_expires_at": now + payload["refresh_token_expires_in"],
    }


def verify_user(client: httpx.Client, access_token: str) -> None:
    try:
        response = client.get("https://api.github.com/user", headers={
            "Authorization": "Bearer " + access_token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        })
        response.raise_for_status()
        user = response.json()
    except (httpx.HTTPError, ValueError):
        raise OAuthError("identity_check_failed", "无法核对授权账号，未保存新令牌；请检查网络后重新登录。") from None
    if not isinstance(user, dict) or not isinstance(user.get("login"), str) or user["login"].lower() != EXPECTED_LOGIN:
        raise OAuthError("account_mismatch", "授权账号与 beginner2077 不一致，未保存新令牌。")


@contextmanager
def cache_lock(path: Path):
    """让同一缓存的读、刷新、保存串行；其他进程占用时返回可重试错误。"""
    with path.with_suffix(".lock").open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            acquire = lambda: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            release = lambda: msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            acquire = lambda: fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            release = lambda: fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        try:
            acquire()
        except OSError:
            raise OAuthError("token_busy", "其他请求正在更新令牌，请稍后重试。", retryable=True) from None
        try:
            yield
        finally:
            stream.seek(0)
            release()


def save_tokens(path: Path, tokens: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        import ntsecuritycon
        import pywintypes
        import win32api
        import win32security

        try:
            token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY)
            try:
                sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
            finally:
                token.Close()
            acl = win32security.ACL()
            acl.AddAccessAllowedAceEx(win32security.ACL_REVISION,
                                     win32security.OBJECT_INHERIT_ACE | win32security.CONTAINER_INHERIT_ACE,
                                     ntsecuritycon.FILE_ALL_ACCESS, sid)
            win32security.SetNamedSecurityInfo(str(path.parent), win32security.SE_FILE_OBJECT,
                                              win32security.DACL_SECURITY_INFORMATION | win32security.PROTECTED_DACL_SECURITY_INFORMATION,
                                              None, None, acl, None)
        except pywintypes.error:
            raise OAuthError("cache_permissions_failed", "无法限制缓存目录权限，未保存新令牌。") from None
    else:
        path.parent.chmod(0o700)
    temporary = None
    try:
        # 临时文件也在受限目录内；失败时保留原缓存，成功时一次替换。
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(tokens, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    try:
        directory = local_directory()
        settings = load_settings(directory / ".env")
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
        with CallbackServer(state) as server:
            print("1/3 请在浏览器打开下面的 GitHub 授权链接（5 分钟内完成）：", flush=True)
            print(authorization_url(settings, state, verifier), flush=True)
            deadline = time.monotonic() + 300
            while server.code is None:
                if time.monotonic() >= deadline:
                    raise OAuthError("authorization_timeout", "等待授权超时，请重新运行登录命令。")
                server.handle_request()
                if server.auth_error:
                    raise server.auth_error
            code = server.code
        print("2/3 回调校验通过，正在交换令牌并核对账号。", flush=True)
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            tokens = exchange_code(client, settings, code, verifier)
            verify_user(client, tokens["access_token"])
        with cache_lock(directory / "tokens.json"):
            save_tokens(directory / "tokens.json", tokens)
        print("3/3 登录成功，账号 beginner2077；可过期访问令牌及刷新令牌已保存到本机。")
        return 0
    except OAuthError as error:
        print(json.dumps({"error": error.code, "message": str(error), "retryable": error.retryable}, ensure_ascii=False), file=sys.stderr)
    except OSError:
        print("本机 I/O 失败，请检查 8765 端口、配置文件和缓存目录权限。", file=sys.stderr)
    except KeyboardInterrupt:
        print("登录已取消。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
