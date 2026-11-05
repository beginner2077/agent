"""离线检查输入隔离、评分及真实 SDK 的请求格式；不读取真实密钥。"""

import json
import sys

import httpx
from openai import OpenAI
import pytest

from labs.prompt_context import run_experiment as lab


def response_payload(text, index, status="completed"):
    return {
        "id": f"response_{index}", "object": "response", "created_at": 0,
        "status": status, "model": "deepseek-flash",
        "reasoning": {"effort": "none"}, "temperature": 0.2, "top_p": 1.0,
        "max_output_tokens": 512,
        "output": [{"id": f"message_{index}", "type": "message", "role": "assistant",
                    "status": "completed", "content": [{"type": "output_text", "text": text, "annotations": []}]}],
    }


def test_groups_have_isolated_inputs_without_evaluation_answers():
    canonical_answer = json.dumps(lab.EXPECTED, separators=(",", ":"))
    for group, (examples, document) in lab.GROUPS.items():
        request = lab.make_request(group)
        text = request["input"][0]["content"]
        assert request["instructions"] == lab.INSTRUCTIONS
        assert len(request["input"]) == 1
        assert text.endswith(lab.TASK)
        assert (lab.EXAMPLES in text) == examples
        assert (lab.DOCUMENT in text) == document
        assert canonical_answer not in text
        assert "评价标准" not in text
        if not document:
            assert "X-Org-Key" not in text
            assert "data.profile.display_name" not in text
            assert "/v2/members/" not in text
        request["input"].append({"role": "assistant", "content": "previous-trial"})
        assert len(lab.make_request(group)["input"]) == 1


def test_unknown_is_supported_but_not_complete():
    text = json.dumps(dict.fromkeys(lab.EXPECTED))
    score = lab.score_output(text, has_document=False)
    assert score == {"json_valid": True, "schema_valid": True, "supported": True,
                     "complete": False, "correct_fields": None}
    assert lab.score_output(text, has_document=True)["correct_fields"] == 0


def test_correct_plan_needs_evidence_and_exact_contract():
    text = json.dumps(lab.EXPECTED)
    assert lab.score_output(text, True)["complete"]
    guessed = lab.score_output(text, False)
    assert not guessed["supported"]
    assert not guessed["complete"]
    wrong = dict(lab.EXPECTED, auth_header="Authorization")
    score = lab.score_output(json.dumps(wrong), True)
    assert score["json_valid"] and score["schema_valid"]
    assert not score["supported"] and not score["complete"]
    assert score["correct_fields"] == 3


@pytest.mark.parametrize("text, json_valid", [
    ('```json\n{}\n```', False),
    ('{"method":NaN}', False),
    ('[]', True),
    ('{"method":"GET"}', True),
    ('{"method":null,"url":null,"auth_header":null,"result_path":false}', True),
    ('{"method":null,"method":"GET","url":null,"auth_header":null,"result_path":null}', True),
])
def test_format_failure_is_not_misreported_as_factual_judgment(text, json_valid):
    score = lab.score_output(text, True)
    assert score["json_valid"] == json_valid
    assert not score["schema_valid"]
    assert score["supported"] is None
    assert not score["complete"]


@pytest.mark.parametrize("base", ["https://api.openai.com", "http://127.0.0.1:58888/anthropic"])
def test_config_does_not_route_key_to_other_upstreams(tmp_path, base):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"env": {"ANTHROPIC_BASE_URL": base, "ANTHROPIC_AUTH_TOKEN": "fictional-secret"}}))
    with pytest.raises(ValueError) as error:
        lab.load_config(path)
    assert "fictional-secret" not in str(error.value)


def test_preview_does_not_read_credentials_or_create_client(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run_experiment.py"])
    monkeypatch.setattr(lab, "load_config", lambda path: pytest.fail("preview read credentials"))
    monkeypatch.setattr(lab, "OpenAI", lambda **kwargs: pytest.fail("preview created client"))
    assert lab.main() == 0
    assert "仅预览" in capsys.readouterr().out


def test_sdk_sends_twelve_independent_requests_and_keeps_credentials_out_of_records(tmp_path, capsys):
    captured = []

    def endpoint(request):
        assert request.url.host == "api.deepseek.com" and request.url.path == "/responses"
        assert request.headers["Authorization"] == "Bearer fictional-selected-key"
        payload = json.loads(request.content)
        expected_group = list(lab.GROUPS)[len(captured) % 4]
        assert payload == lab.make_request(expected_group)
        assert "fictional-selected-key" not in request.content.decode()
        captured.append(payload)
        output = lab.EXPECTED if lab.GROUPS[expected_group][1] else dict.fromkeys(lab.EXPECTED)
        return httpx.Response(200, json=response_payload(json.dumps(output), len(captured)))

    directory = tmp_path / "run"
    with OpenAI(api_key="fictional-selected-key", base_url="https://api.deepseek.com", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(endpoint))) as client:
        summary, finished = lab.run_trials(client, directory)
    assert finished and len(captured) == 12
    records = [json.loads(line) for line in (directory / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(row["trial"], row["group"]) for row in records] == [(trial, group) for trial in (1, 2, 3) for group in lab.GROUPS]
    assert summary["A"]["supported"] == 3 and summary["A"]["complete"] == 0
    assert summary["D"]["complete"] == 3
    assert records[0]["response_meta"]["reasoning"]["effort"] == "none"
    assert "fictional-selected-key" not in (directory / "results.jsonl").read_text(encoding="utf-8")
    assert "fictional-selected-key" not in capsys.readouterr().out


def test_authentication_failure_stops_without_hidden_retries_or_error_body_leak(tmp_path, capsys):
    attempts = []

    def endpoint(request):
        attempts.append(request)
        return httpx.Response(401, json={"error": {"message": "fictional-private-body", "type": "authentication_error"}})

    directory = tmp_path / "failed-run"
    with OpenAI(api_key="fictional-selected-key", base_url="https://api.deepseek.com", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(endpoint))) as client:
        summary, finished = lab.run_trials(client, directory)
    assert not finished and len(attempts) == 1
    assert summary["A"]["attempted"] == 1 and summary["A"]["api_completed"] == 0
    assert summary["B"]["attempted"] == 0
    text = (directory / "results.jsonl").read_text(encoding="utf-8")
    assert "fictional-private-body" not in text + capsys.readouterr().out
    assert json.loads(text)["error"]["http_status"] == 401


def test_truncated_response_is_not_scored_as_a_completed_answer(tmp_path):
    def endpoint(request):
        return httpx.Response(200, json=response_payload('{"method":', 1, status="incomplete"))

    directory = tmp_path / "truncated-run"
    with OpenAI(api_key="fictional-selected-key", base_url="https://api.deepseek.com", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(endpoint))) as client:
        summary, finished = lab.run_trials(client, directory)
    assert not finished
    assert summary["A"]["api_completed"] == 0
    assert json.loads((directory / "results.jsonl").read_text(encoding="utf-8"))["score"] is None
