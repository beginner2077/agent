"""离线回归：只使用虚构配置和内存 HTTP 响应，不请求真实模型。"""

import importlib.util
import json
from pathlib import Path

import httpx
from openai import OpenAI
import pytest


def write_profile(path, **changes):
    env = {
        "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
        "ANTHROPIC_AUTH_TOKEN": "test-deepseek-key",
        "ANTHROPIC_MODEL": "deepseek-v4-pro",
    }
    env.update(changes)
    path.write_text(json.dumps({"env": env}), encoding="utf-8")
    return path


@pytest.fixture
def lecture(tmp_path, monkeypatch):
    profile = write_profile(tmp_path / "settings-deepseek.json")
    monkeypatch.setenv("CS146S_DEEPSEEK_SETTINGS", str(profile))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    source = Path(__file__).with_name("lecture-9-22-official.py")
    spec = importlib.util.spec_from_file_location("lecture_deepseek_under_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    module.deepseek_client.close()


@pytest.mark.parametrize("auth_field", ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"])
def test_reads_named_profile_without_openai_key(lecture, tmp_path, auth_field):
    path = write_profile(tmp_path / "selected.json", ANTHROPIC_AUTH_TOKEN="")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["env"][auth_field] = "fake-selected-key"
    path.write_text(json.dumps(data), encoding="utf-8")
    config = lecture.load_deepseek_settings(path)
    assert config == {"api_key": "fake-selected-key", "base_url": "https://api.deepseek.com"}
    assert lecture.DEEPSEEK_MODEL == "deepseek-flash"


@pytest.mark.parametrize("base_url", ["https://api.openai.com", "http://127.0.0.1:58888/anthropic"])
def test_rejects_other_upstreams(lecture, tmp_path, base_url):
    path = write_profile(tmp_path / "wrong-upstream.json", ANTHROPIC_BASE_URL=base_url)
    with pytest.raises(RuntimeError, match="DeepSeek HTTPS"):
        lecture.load_deepseek_settings(path)


def test_missing_key_does_not_fall_back_to_openai_key(lecture, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "unrelated-fake-openai-key")
    path = write_profile(tmp_path / "no-key.json", ANTHROPIC_AUTH_TOKEN="")
    with pytest.raises(RuntimeError, match="缺少 ANTHROPIC_AUTH_TOKEN"):
        lecture.load_deepseek_settings(path)


def test_invalid_json_does_not_echo_sensitive_content(lecture, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"secret": "fake-private-value",', encoding="utf-8")
    with pytest.raises(RuntimeError) as failure:
        lecture.load_deepseek_settings(path)
    assert "fake-private-value" not in str(failure.value)


def test_loop_sends_flash_to_deepseek_and_returns_tool_result(lecture, tmp_path, monkeypatch, capsys):
    requests = []
    replies = ['tool: read_file({"filename":"sample.py"})', "DONE"]

    def respond(request):
        assert request.url.host == "api.deepseek.com"
        assert request.url.path == "/responses"
        assert request.method == "POST"
        assert request.headers["Authorization"] == "Bearer test-deepseek-key"
        payload = json.loads(request.content)
        assert payload["model"] == "deepseek-flash"
        assert payload["input"][0]["role"] == "system"
        requests.append(payload)
        text = replies[len(requests) - 1]
        return httpx.Response(200, json={
            "id": f"resp_{len(requests)}", "object": "response", "created_at": 0,
            "status": "completed", "model": "deepseek-flash",
            "output": [{"id": f"msg_{len(requests)}", "type": "message",
                        "role": "assistant", "status": "completed",
                        "content": [{"type": "output_text", "text": text, "annotations": []}]}],
        })

    lecture.deepseek_client.close()
    lecture.deepseek_client = OpenAI(
        api_key="test-deepseek-key", base_url="https://api.deepseek.com",
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    )
    (tmp_path / "sample.py").write_text("print('fixture')\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    inputs = iter(["Read sample.py"])

    def next_input(prompt):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", next_input)
    lecture.run_coding_agent_loop()
    assert len(requests) == 2
    history = requests[1]["input"]
    assert history[-2]["role"] == "assistant"
    assert history[-2]["content"] == replies[0]
    assert history[-1]["role"] == "user"
    result_text = history[-1]["content"]
    result = json.loads(result_text[len("tool_result("):-1])
    assert result["content"] == "print('fixture')\n"
    output = capsys.readouterr().out
    assert "DONE" in output
    assert "test-deepseek-key" not in output
