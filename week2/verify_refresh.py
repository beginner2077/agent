"""独立验证刷新、落盘及账号；只有 --refresh 才读取凭据并访问 GitHub。"""

import argparse
import json
from pathlib import Path
import sys

import httpx

from .oauth_login import (
    EXPECTED_LOGIN, OAuthError, Settings, cache_lock, load_settings,
    local_directory, verify_user,
)
from .token_store import LOGIN_COMMAND, TokenStore


def verify_refresh(settings: Settings, path: Path, client: httpx.Client) -> dict:
    store = TokenStore(settings, path, client)
    # 复用缓存校验和文件锁；完整凭据仅在进程内比较，不进入返回结果。
    with cache_lock(path):
        before = store._read()
    print("1/3 正在请求刷新并原子保存新令牌对。", flush=True)
    access_token = store.access_token(force_refresh=True)
    try:
        with cache_lock(path):
            after = store._read()
        rotated = (after["access_token"] != before["access_token"]
                   and after["refresh_token"] != before["refresh_token"])
        if after["access_token"] != access_token or not rotated:
            raise OAuthError("refresh_verification_failed", "无法确认两枚令牌轮换及本机回读一致。")
    except (OAuthError, OSError):
        raise OAuthError("refresh_verification_failed",
                         "刷新调用已返回，但缓存核对未通过；不要自动重复刷新。检查是否存在并发更新，必要时重新登录："
                         + LOGIN_COMMAND) from None
    print("2/3 两枚令牌均已变化，访问令牌回读一致；正在只读核对账号。", flush=True)
    try:
        verify_user(client, access_token)
    except OAuthError as error:
        # 首次登录的错误说明可能提到“未保存”；刷新阶段已经落盘，必须区分。
        raise OAuthError(error.code,
                         "刷新结果已保存，但账号核对未通过。请检查网络或重新登录：" + LOGIN_COMMAND) from None
    return {
        "account": EXPECTED_LOGIN, "access_token_rotated": True,
        "refresh_token_rotated": True, "cached_access_token_matches": True,
        "user_verified": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="真实轮换令牌、保存并只读核对 GitHub 账号")
    args = parser.parse_args()
    if not args.refresh:
        print("仅说明：未读取凭据或访问 GitHub。加 --refresh 会轮换并保存令牌，然后 GET /user 核对账号。")
        return 0
    try:
        directory = local_directory()
        settings = load_settings(directory / ".env")
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            result = verify_refresh(settings, directory / "tokens.json", client)
        print("3/3 刷新验证通过；未执行 Issue 写操作。")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except OAuthError as error:
        print(json.dumps({"error": error.code, "message": str(error), "retryable": error.retryable}, ensure_ascii=False), file=sys.stderr)
    except OSError:
        print("本机 I/O 失败，请检查配置和缓存目录权限；不自动重试。", file=sys.stderr)
    except KeyboardInterrupt:
        print("验证已中断；若已经发送刷新，请保留现有缓存，不自动重发。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
