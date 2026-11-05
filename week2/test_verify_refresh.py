"""刷新验证入口只使用临时凭据与 MockTransport，不访问真实 GitHub。"""

import json
import sys
from urllib.parse import parse_qs

import httpx
import pytest

from week2 import oauth_login as oauth
from week2 import token_store as storage
from week2 import verify_refresh as lab


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.time, "time", lambda: 1000)
    settings = oauth.Settings("example-client", "fictional-client-secret")
    path = tmp_path / "private" / "tokens.json"
    oauth.save_tokens(path, {
        "client_id": settings.client_id, "repository": settings.repository, "token_type": "bearer",
        "access_token": "old-fictional-access", "refresh_token": "old-fictional-refresh",
        "expires_at": 2000, "refresh_expires_at": 5000,
    })
    return settings, path


def fresh_response(**changes):
    payload = {"access_token": "new-fictional-access", "refresh_token": "new-fictional-refresh",
               "token_type": "bearer", "expires_in": 28800, "refresh_token_expires_in": 15897600}
    payload.update(changes)
    return httpx.Response(200, json=payload)


def test_rotation_is_read_back_and_verified_without_printing_credentials(prepared, capsys):
    settings, path = prepared
    calls = []

    def endpoint(request):
        calls.append((request.method, str(request.url)))
        if request.method == "POST":
            assert str(request.url) == oauth.TOKEN_URL
            assert parse_qs(request.content.decode())["refresh_token"] == ["old-fictional-refresh"]
            return fresh_response()
        assert str(request.url) == "https://api.github.com/user"
        assert request.headers["Authorization"] == "Bearer new-fictional-access"
        assert json.loads(path.read_text())["refresh_token"] == "new-fictional-refresh"
        return httpx.Response(200, json={"login": "beginner2077"})

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        result = lab.verify_refresh(settings, path, client)
    assert calls == [("POST", oauth.TOKEN_URL), ("GET", "https://api.github.com/user")]
    assert result == {"account": "beginner2077", "access_token_rotated": True,
                      "refresh_token_rotated": True, "cached_access_token_matches": True, "user_verified": True}
    printed = capsys.readouterr()
    public = printed.out + printed.err + json.dumps(result)
    for secret in (settings.client_secret, "old-fictional-access", "old-fictional-refresh",
                   "new-fictional-access", "new-fictional-refresh"):
        assert secret not in public


@pytest.mark.parametrize("status,login,code", [(401, None, "identity_check_failed"),
                                             (200, "other-user", "account_mismatch")])
def test_failed_identity_check_preserves_saved_pair_and_reports_stage(prepared, capsys, status, login, code):
    settings, path = prepared
    calls = []

    def endpoint(request):
        calls.append(request.method)
        if request.method == "POST":
            return fresh_response()
        return httpx.Response(status, json={"login": login, "private": "private-response-body"})

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        with pytest.raises(oauth.OAuthError) as error:
            lab.verify_refresh(settings, path, client)
    assert error.value.code == code
    assert "已保存" in str(error.value) and "未保存" not in str(error.value)
    assert json.loads(path.read_text())["access_token"] == "new-fictional-access"
    assert calls == ["POST", "GET"]
    printed = capsys.readouterr()
    assert "private-response-body" not in str(error.value) + printed.out + printed.err


def test_rejected_refresh_never_calls_user_or_retries(prepared, capsys):
    settings, path = prepared
    before = path.read_bytes()
    calls = []

    def endpoint(request):
        calls.append(request.method)
        return httpx.Response(401, text="private-response-body")

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        with pytest.raises(oauth.OAuthError) as error:
            lab.verify_refresh(settings, path, client)
    assert error.value.code == "auth_required"
    assert calls == ["POST"] and path.read_bytes() == before
    assert "2/3" not in capsys.readouterr().out


@pytest.mark.parametrize("field", ["access_token", "refresh_token"])
def test_both_tokens_must_change_for_verification_success(prepared, field):
    settings, path = prepared
    before = json.loads(path.read_text())
    calls = []

    def endpoint(request):
        calls.append(request.method)
        return fresh_response(**{field: before[field]})

    with httpx.Client(transport=httpx.MockTransport(endpoint)) as client:
        with pytest.raises(oauth.OAuthError) as error:
            lab.verify_refresh(settings, path, client)
    assert error.value.code == "refresh_verification_failed"
    assert calls == ["POST"]


def test_default_entry_does_not_read_credentials_or_create_client(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["verify_refresh"])
    monkeypatch.setattr(lab, "local_directory", lambda: pytest.fail("default entry read credentials"))
    monkeypatch.setattr(lab.httpx, "Client", lambda **kwargs: pytest.fail("default entry created client"))
    assert lab.main() == 0
    assert "未读取凭据" in capsys.readouterr().out


def test_explicit_entry_uses_local_config_and_only_two_requests(prepared, monkeypatch, capsys):
    settings, path = prepared
    real_client = httpx.Client
    calls = []

    def load(path_arg):
        assert path_arg == path.parent / ".env"
        return settings

    def endpoint(request):
        calls.append(request.method)
        return fresh_response() if request.method == "POST" else httpx.Response(200, json={"login": "beginner2077"})

    def client(**kwargs):
        assert kwargs == {"timeout": 20, "follow_redirects": False}
        return real_client(**kwargs, transport=httpx.MockTransport(endpoint))

    monkeypatch.setattr(sys, "argv", ["verify_refresh", "--refresh"])
    monkeypatch.setattr(lab, "local_directory", lambda: path.parent)
    monkeypatch.setattr(lab, "load_settings", load)
    monkeypatch.setattr(lab.httpx, "Client", client)
    assert lab.main() == 0
    assert calls == ["POST", "GET"]
    printed = capsys.readouterr()
    assert "3/3 刷新验证通过" in printed.out
    assert "fictional" not in printed.out + printed.err
