"""供后续 GitHub 工具取得令牌：复用缓存，临近过期时静默刷新。"""

import json
from pathlib import Path
from threading import Lock
import time

import httpx

from .oauth_login import (
    OAuthError, Settings, TOKEN_URL, cache_lock, save_tokens, tokens_from_payload,
)


LOGIN_COMMAND = r".\week2\.venv\Scripts\python.exe week2/oauth_login.py"


def auth_required(message: str) -> OAuthError:
    return OAuthError("auth_required", message + " 请在独立终端运行：" + LOGIN_COMMAND)


class TokenStore:
    def __init__(self, settings: Settings, path: Path, client: httpx.Client):
        self.settings = settings
        self.path = path
        self.client = client
        self._lock = Lock()
        self._blocked_refresh = None

    def _read(self) -> dict:
        try:
            cached = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise auth_required("令牌缓存不存在、不可读或已损坏。") from None
        if (not isinstance(cached, dict)
                or cached.get("client_id") != self.settings.client_id
                or cached.get("repository") != self.settings.repository
                or cached.get("token_type") != "bearer"
                or any(not isinstance(cached.get(key), str) or not cached[key].strip()
                       for key in ("access_token", "refresh_token"))
                or any(type(cached.get(key)) is not int or cached[key] <= 0
                       for key in ("expires_at", "refresh_expires_at"))):
            raise auth_required("令牌缓存不完整或不属于当前应用/仓库。")
        if cached["refresh_token"] == self._blocked_refresh:
            raise auth_required("上次刷新结果无法安全使用，不能继续使用该旧令牌对。")
        return cached

    def access_token(self, *, force_refresh: bool = False) -> str:
        """默认按需刷新；force_refresh 供显式验证，返回的凭据不得打印。"""
        with self._lock:
            try:
                # 文件锁也覆盖网络刷新，避免多个 Server 同时消费同一 refresh token。
                with cache_lock(self.path):
                    cached = self._read()
                    now = time.time()
                    if not force_refresh and cached["expires_at"] > now + 60:
                        return cached["access_token"]
                    if cached["refresh_expires_at"] <= now:
                        raise auth_required("刷新令牌已过期。")
                    try:
                        updated = self._refresh(cached["refresh_token"])
                    except OAuthError as error:
                        if error.code == "auth_required":
                            self._blocked_refresh = cached["refresh_token"]
                        raise
                    try:
                        save_tokens(self.path, updated)
                    except (OSError, OAuthError):
                        self._blocked_refresh = cached["refresh_token"]
                        raise OAuthError("token_cache_write_failed",
                                         "远端已刷新，但本机保存失败；不能回退旧凭据。检查目录权限后重新登录：" + LOGIN_COMMAND) from None
                    return updated["access_token"]
            except OSError:
                raise auth_required("无法访问令牌缓存目录，请检查本机文件权限。") from None

    def _refresh(self, refresh_token: str) -> dict:
        try:
            response = self.client.post(TOKEN_URL, headers={"Accept": "application/json"}, data={
                "grant_type": "refresh_token",
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
                "refresh_token": refresh_token,
            }, follow_redirects=False)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
            raise OAuthError("refresh_unavailable", "未能连接令牌端点，请稍后重试。", retryable=True) from None
        except httpx.RequestError:
            # 请求可能已经被服务端处理，不能盲目重发可能已消费的刷新令牌。
            raise auth_required("刷新响应未完整收到，远端结果不确定。") from None
        if response.status_code == 429:
            raise OAuthError("rate_limited", "令牌端点限流，请稍后重试。", retryable=True)
        if response.status_code != 200:
            raise auth_required("令牌刷新被拒绝或远端结果不确定。")
        try:
            payload = response.json()
        except ValueError:
            raise auth_required("刷新响应不是有效 JSON，无法安全保存新凭据。") from None
        if isinstance(payload, dict) and "error" in payload:
            if payload["error"] == "incorrect_client_credentials":
                raise OAuthError("client_config_invalid", "Client ID 或 Client Secret 错误，请检查本机配置后重启服务。")
            raise auth_required("GitHub 拒绝刷新，授权可能已失效。")
        try:
            return tokens_from_payload(payload, self.settings)
        except OAuthError:
            raise auth_required("刷新响应缺少有效的新令牌对。") from None
