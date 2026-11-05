"""只使用虚构凭据、MockTransport 和临时目录；不请求 GitHub。"""

import json
from threading import Thread
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from week2 import oauth_login as oauth


@pytest.fixture
def settings():
    return oauth.Settings("example-client", "fictional-client-secret")


def token_payload():
    return {
        "access_token": "fictional-access-token",
        "refresh_token": "fictional-refresh-token",
        "token_type": "bearer",
        "expires_in": 28800,
        "refresh_token_expires_in": 15897600,
    }


def test_authorization_uses_rfc_pkce_vector_without_secret(settings):
    # RFC 7636 Appendix B 的固定向量，避免用同一实现计算测试预期。
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    url = oauth.authorization_url(settings, "random-state", verifier)
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "github.com"
    assert query["code_challenge"] == ["E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == ["random-state"]
    assert query["redirect_uri"] == [oauth.REDIRECT_URI]
    assert query["scope"] == ["offline_access"]
    assert settings.client_secret not in url and verifier not in url


@pytest.mark.parametrize("target", [
    "/callback?state=wrong&code=private-code",
    "/callback?code=private-code",
    "/callback?state=expected&state=expected&code=private-code",
    "/callback?state=expected&code=one&code=two",
    "/callback?state=expected&code=",
    "/other?state=expected&code=private-code",
    "http://example.com/callback?state=expected&code=private-code",
])
def test_rejects_invalid_callback_without_echoing_code(target):
    with pytest.raises(oauth.OAuthError) as error:
        oauth.validate_callback(target, "expected")
    assert "private-code" not in str(error.value)


def test_callback_denial_is_actionable():
    with pytest.raises(oauth.OAuthError) as error:
        oauth.validate_callback("/callback?state=expected&error=access_denied", "expected")
    assert error.value.code == "authorization_denied"


def test_real_loopback_callback_does_not_log_authorization_code(capsys):
    with oauth.CallbackServer("expected", port=0) as server:
        thread = Thread(target=server.handle_request)
        thread.start()
        with httpx.Client(trust_env=False) as client:
            response = client.get(f"http://127.0.0.1:{server.server_port}/callback?state=expected&code=private-code")
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert response.status_code == 200
        assert server.code == "private-code"
        assert "登录成功" not in response.text
        assert response.headers["cache-control"] == "no-store"
    output = capsys.readouterr()
    assert "private-code" not in output.out + output.err


def test_exchange_sends_verifier_and_records_expiration(settings, monkeypatch):
    def endpoint(request):
        assert str(request.url) == oauth.TOKEN_URL
        query = parse_qs(request.content.decode())
        assert query["code_verifier"] == ["private-verifier"]
        assert query["client_secret"] == [settings.client_secret]
        assert query["code"] == ["private-code"]
        return httpx.Response(200, json=token_payload())

    monkeypatch.setattr(oauth.time, "time", lambda: 1000)
    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        tokens = oauth.exchange_code(client, settings, "private-code", "private-verifier")
    assert tokens["expires_at"] == 29800
    assert tokens["refresh_expires_at"] == 15898600
    assert tokens["repository"] == oauth.REPOSITORY


@pytest.mark.parametrize("payload", [
    {"error": "incorrect_client_credentials", "error_description": "private-secret"},
    {"error": {"malformed": "private-secret"}},
    {"access_token": "private-secret"},
    {**token_payload(), "expires_in": True},
    {**token_payload(), "token_type": 123},
    [],
])
def test_bad_token_response_does_not_leak_payload(settings, payload):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as client:
        with pytest.raises(oauth.OAuthError) as error:
            oauth.exchange_code(client, settings, "private-code", "private-verifier")
    assert "private-secret" not in str(error.value)


def test_network_failure_is_not_retried(settings):
    attempts = []

    def endpoint(request):
        attempts.append(request)
        raise httpx.ReadTimeout("private-secret", request=request)

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        with pytest.raises(oauth.OAuthError) as error:
            oauth.exchange_code(client, settings, "private-code", "private-verifier")
    assert error.value.code == "network_error"
    assert "private-secret" not in str(error.value)
    assert len(attempts) == 1


def test_wrong_account_is_rejected():
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"login": "other-user"}))) as client:
        with pytest.raises(oauth.OAuthError) as error:
            oauth.verify_user(client, "fictional-access-token")
    assert error.value.code == "account_mismatch"


def test_atomic_cache_failure_keeps_previous_tokens(tmp_path, monkeypatch):
    cache = tmp_path / "private" / "tokens.json"
    oauth.save_tokens(cache, {"access_token": "old-fictional-token"})
    if oauth.os.name == "nt":
        import win32api
        import win32security

        acl = win32security.GetFileSecurity(str(cache), win32security.DACL_SECURITY_INFORMATION).GetSecurityDescriptorDacl()
        current_sid = win32security.LookupAccountName(None, win32api.GetUserName())[0]
        assert acl.GetAceCount() == 1
        assert acl.GetAce(0)[2] == current_sid

    def fail_replace(source, target):
        raise OSError("simulated disk error")

    monkeypatch.setattr(oauth.os, "replace", fail_replace)
    with pytest.raises(OSError):
        oauth.save_tokens(cache, {"access_token": "new-fictional-token"})
    assert json.loads(cache.read_text())["access_token"] == "old-fictional-token"
    assert list(cache.parent.iterdir()) == [cache]


@pytest.mark.parametrize("login, expected_exit", [("beginner2077", 0), ("other-user", 1)])
def test_main_uses_fake_config_and_never_saves_wrong_account(tmp_path, monkeypatch, capsys, login, expected_exit):
    directory = tmp_path / "private"
    directory.mkdir()
    directory.joinpath(".env").write_text(
        "GITHUB_CLIENT_ID=example-client\nGITHUB_CLIENT_SECRET=fictional-client-secret\n"
        f"GITHUB_REDIRECT_URI={oauth.REDIRECT_URI}\nGITHUB_REPOSITORY={oauth.REPOSITORY}\n"
    )
    if expected_exit:
        oauth.save_tokens(directory / "tokens.json", {"access_token": "old-fictional-token"})
    for key in ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_REDIRECT_URI", "GITHUB_REPOSITORY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(oauth, "local_directory", lambda: directory)

    class FakeCallback:
        code = "private-code"
        auth_error = None

        def __init__(self, state):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def endpoint(request):
        if request.url.host == "github.com":
            return httpx.Response(200, json=token_payload())
        assert request.headers["Authorization"] == "Bearer fictional-access-token"
        return httpx.Response(200, json={"login": login})

    client_class = httpx.Client
    monkeypatch.setattr(oauth, "CallbackServer", FakeCallback)
    monkeypatch.setattr(oauth.httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(endpoint), **kwargs))
    assert oauth.main() == expected_exit
    assert (directory / "tokens.json").is_file()
    output = capsys.readouterr()
    for private in ("fictional-client-secret", "fictional-access-token", "fictional-refresh-token", "private-code"):
        assert private not in output.out + output.err
    if expected_exit:
        assert json.loads((directory / "tokens.json").read_text())["access_token"] == "old-fictional-token"
        assert "3/3 登录成功" not in output.out
        assert "account_mismatch" in output.err
    else:
        assert "3/3 登录成功" in output.out
