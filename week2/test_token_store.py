"""静默刷新只使用模拟端点和临时令牌，不访问真实 GitHub。"""

from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event
from urllib.parse import parse_qs

import httpx
import pytest

from week2 import oauth_login as oauth
from week2 import token_store as storage


@pytest.fixture
def settings():
    return oauth.Settings("example-client", "fictional-client-secret")


@pytest.fixture
def cache(tmp_path, settings, monkeypatch):
    monkeypatch.setattr(storage.time, "time", lambda: 1000)
    path = tmp_path / "private" / "tokens.json"
    oauth.save_tokens(path, {
        "client_id": settings.client_id,
        "repository": settings.repository,
        "token_type": "bearer",
        "access_token": "old-fictional-access",
        "refresh_token": "old-fictional-refresh",
        "expires_at": 1000,
        "refresh_expires_at": 5000,
    })
    return path


def fresh_response():
    return httpx.Response(200, json={
        "access_token": "new-fictional-access",
        "refresh_token": "new-fictional-refresh",
        "token_type": "bearer",
        "expires_in": 28800,
        "refresh_token_expires_in": 15897600,
    })


def replace_cache(cache, **changes):
    contents = json.loads(cache.read_text())
    contents.update(changes)
    oauth.save_tokens(cache, contents)


def test_valid_cache_never_requests_or_rewrites_tokens(cache, settings):
    replace_cache(cache, expires_at=2000)
    before = cache.read_bytes()

    def unexpected_request(request):
        pytest.fail("valid cache must not request a refresh")

    with httpx.Client(transport=httpx.MockTransport(unexpected_request)) as client:
        store = storage.TokenStore(settings, cache, client)
        assert store.access_token() == "old-fictional-access"
        assert store.access_token() == "old-fictional-access"
    assert cache.read_bytes() == before


def test_explicit_refresh_does_not_need_cache_expiry_to_be_changed(cache, settings):
    replace_cache(cache, expires_at=2000)
    calls = []

    def endpoint(request):
        assert json.loads(cache.read_text())["expires_at"] == 2000
        calls.append(request)
        return fresh_response()

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        store = storage.TokenStore(settings, cache, client)
        assert store.access_token(force_refresh=True) == "new-fictional-access"
        assert store.access_token() == "new-fictional-access"
    assert len(calls) == 1


@pytest.mark.parametrize("expires_at", [900, 1000, 1059, 1060])
def test_refresh_rotates_both_tokens_once(cache, settings, expires_at):
    replace_cache(cache, expires_at=expires_at)
    calls = []

    def endpoint(request):
        calls.append(request)
        assert str(request.url) == oauth.TOKEN_URL
        assert request.method == "POST"
        assert parse_qs(request.content.decode()) == {
            "grant_type": ["refresh_token"],
            "client_id": [settings.client_id],
            "client_secret": [settings.client_secret],
            "refresh_token": ["old-fictional-refresh"],
        }
        return fresh_response()

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        store = storage.TokenStore(settings, cache, client)
        assert store.access_token() == "new-fictional-access"
        assert store.access_token() == "new-fictional-access"
    assert len(calls) == 1
    saved = json.loads(cache.read_text())
    assert saved["refresh_token"] == "new-fictional-refresh"
    assert saved["expires_at"] == 29800
    assert saved["refresh_expires_at"] == 15898600


@pytest.mark.parametrize("changes", [
    {"refresh_expires_at": 999},
    {"client_id": "other-client"},
    {"repository": "other/repo"},
    {"expires_at": True},
    {"refresh_token": ""},
])
def test_invalid_or_expired_cache_requires_login_without_network(cache, settings, changes):
    replace_cache(cache, **changes)
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as client:
        with pytest.raises(oauth.OAuthError) as error:
            storage.TokenStore(settings, cache, client).access_token()
    assert error.value.code == "auth_required"
    assert not error.value.retryable


@pytest.mark.parametrize("body", ["not-json", "[]", '{"private-token":true}'])
def test_corrupt_cache_does_not_echo_content(cache, settings, body):
    cache.write_text(body)
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not request"))) as client:
        with pytest.raises(oauth.OAuthError) as error:
            storage.TokenStore(settings, cache, client).access_token()
    assert error.value.code == "auth_required"
    assert "private-token" not in str(error.value)


@pytest.mark.parametrize("response", [
    httpx.Response(200, json={"error": "bad_refresh_token", "error_description": "private-token"}),
    httpx.Response(200, json={"access_token": "private-token"}),
    httpx.Response(200, text="private-token"),
    httpx.Response(401, text="private-token"),
    httpx.Response(500, text="private-token"),
    httpx.Response(307, headers={"Location": "https://example.com/steal"}),
])
def test_rejection_or_uncertain_response_blocks_old_pair(cache, settings, response):
    calls = []

    def endpoint(request):
        calls.append(request)
        return response

    with httpx.Client(transport=httpx.MockTransport(endpoint), follow_redirects=True) as client:
        store = storage.TokenStore(settings, cache, client)
        for _ in range(2):
            with pytest.raises(oauth.OAuthError) as error:
                store.access_token()
            assert error.value.code == "auth_required"
            assert "private-token" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize("failure", ["connect", "read", "rate_limit"])
def test_network_outcome_controls_retryability(cache, settings, failure):
    calls = []

    def endpoint(request):
        calls.append(request)
        if len(calls) > 1:
            return fresh_response()
        if failure == "connect":
            raise httpx.ConnectTimeout("private-token", request=request)
        if failure == "read":
            raise httpx.ReadTimeout("private-token", request=request)
        return httpx.Response(429)

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        store = storage.TokenStore(settings, cache, client)
        with pytest.raises(oauth.OAuthError) as error:
            store.access_token()
        assert len(calls) == 1
        assert "private-token" not in str(error.value)
        if failure == "read":
            assert not error.value.retryable
            with pytest.raises(oauth.OAuthError) as repeated:
                store.access_token()
            assert repeated.value.code == "auth_required"
            assert len(calls) == 1
        else:
            assert error.value.retryable
            assert store.access_token() == "new-fictional-access"
            assert len(calls) == 2


def test_remote_rotation_then_disk_failure_never_returns_old_token(cache, settings, monkeypatch):
    calls = []

    def endpoint(request):
        calls.append(request)
        return fresh_response()

    def fail_save(path, data):
        raise OSError("private-token")

    monkeypatch.setattr(storage, "save_tokens", fail_save)
    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        store = storage.TokenStore(settings, cache, client)
        with pytest.raises(oauth.OAuthError) as error:
            store.access_token()
        assert error.value.code == "token_cache_write_failed"
        assert "private-token" not in str(error.value)
        assert json.loads(cache.read_text())["access_token"] == "old-fictional-access"
        with pytest.raises(oauth.OAuthError) as repeated:
            store.access_token()
        assert repeated.value.code == "auth_required"
        assert len(calls) == 1
        # 用户独立重新登录写入不同令牌后，可读取新缓存恢复。
        replace_cache(cache, access_token="relogin-access", refresh_token="relogin-refresh", expires_at=5000)
        assert store.access_token() == "relogin-access"


def test_two_stores_cannot_refresh_same_cache_simultaneously(cache, settings):
    entered, finish = Event(), Event()
    calls = []

    def endpoint(request):
        calls.append(request)
        entered.set()
        assert finish.wait(timeout=5)
        return fresh_response()

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        first = storage.TokenStore(settings, cache, client)
        second = storage.TokenStore(settings, cache, client)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(first.access_token)
            try:
                assert entered.wait(timeout=5)
                with pytest.raises(oauth.OAuthError) as error:
                    second.access_token()
                assert error.value.code == "token_busy"
                assert error.value.retryable
            finally:
                finish.set()
            assert pending.result(timeout=5) == "new-fictional-access"
        assert second.access_token() == "new-fictional-access"
    assert len(calls) == 1
