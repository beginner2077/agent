"""两案独立输入及依据敏感评分；全部使用虚构凭据和本地模拟响应。"""

import json
from pathlib import Path
import sys

import httpx
from openai import OpenAI
import pytest

from labs.retrieval import run_generation as lab


def response_payload(text, status="completed", unexpected=False):
    output = [{"id": "message_fake", "type": "message", "role": "assistant", "status": "completed",
               "content": [{"type": "output_text", "text": text, "annotations": []}]}]
    if unexpected:
        output.append({"type": "function_call", "id": "tool_fake", "call_id": "call_fake", "name": "unexpected", "arguments": "{}"})
    return {"id": "response_fake", "object": "response", "created_at": 0, "model": "deepseek-flash",
            "status": status, "reasoning": {"effort": "none"}, "temperature": 0.2, "top_p": 1.0,
            "max_output_tokens": 512, "output": output}


@pytest.mark.parametrize("case,auth,supported,matches,complete", [
    ("split_auth", "X-Org-Key", True, True, True),
    ("split_auth", None, True, False, False),
    ("missing_auth", None, True, True, False),
    ("missing_auth", "X-Org-Key", False, False, False),
    ("missing_auth", "Authorization", False, False, False),
])
def test_evaluation_depends_on_available_evidence(case, auth, supported, matches, complete):
    output = dict(lab.EXPECTED, auth_header=auth)
    score = lab.evaluate(json.dumps(output), case)
    assert score == {"json_valid": True, "schema_valid": True, "supported": supported,
                     "matches_expected": matches, "complete_plan": complete}


def test_all_unknown_is_supported_but_does_not_use_available_facts():
    score = lab.evaluate(json.dumps(dict.fromkeys(lab.EXPECTED)), "missing_auth")
    assert score["supported"] and not score["matches_expected"]
    assert not score["complete_plan"]


@pytest.mark.parametrize("text", ['```json\n{}\n```', '{"method":"GET"}',
                                  '{"method":null,"method":"GET","url":null,"auth_header":null,"result_path":null}'])
def test_invalid_structure_is_not_given_factual_judgment(text):
    score = lab.evaluate(text, "split_auth")
    assert not score["schema_valid"] and score["supported"] is None
    assert not score["matches_expected"] and not score["complete_plan"]


def test_preview_does_not_load_credentials_or_create_client(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run_generation"])
    monkeypatch.setattr(lab, "load_config", lambda path: pytest.fail("preview read credentials"))
    monkeypatch.setattr(lab, "OpenAI", lambda **kwargs: pytest.fail("preview created client"))
    assert lab.main() == 0
    assert "仅预览" in capsys.readouterr().out


def test_six_requests_are_independent_and_missing_auth_has_no_answer_leak(tmp_path, capsys):
    captured = []

    def endpoint(request):
        name = lab.CASE_NAMES[len(captured) % 2]
        case = lab.CASES[name]
        trace = lab.retrieve(**case)
        payload = json.loads(request.content)
        assert request.url == "https://api.deepseek.com/responses"
        assert request.headers["Authorization"] == "Bearer fictional-selected-key"
        assert payload == lab.build_request(case, trace)
        assert len(payload["input"]) == 1
        if name == "missing_auth":
            assert "X-Org-Key" not in request.content.decode()
            assert "unresolved_refs" not in request.content.decode()
        captured.append(payload)
        output = dict(lab.EXPECTED)
        if name == "missing_auth":
            output["auth_header"] = None
        return httpx.Response(200, json=response_payload(json.dumps(output)))

    directory = tmp_path / "run"
    with OpenAI(api_key="fictional-selected-key", base_url="https://api.deepseek.com", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(endpoint))) as client:
        summary, finished = lab.run_trials(client, directory)
    assert finished and len(captured) == 6
    rows = [json.loads(line) for line in (directory / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(row["trial"], row["case"]) for row in rows] == [(trial, name) for trial in (1, 2, 3) for name in lab.CASE_NAMES]
    assert rows[0]["retrieval"]["expanded"] == ["directory-v2-auth"]
    assert rows[1]["retrieval"]["unresolved_refs"][0]["reason"] == "missing"
    assert rows[0]["response_meta"]["reasoning"]["effort"] == "none"
    assert summary["split_auth"]["complete_plan"] == 3
    assert summary["missing_auth"]["matches_expected"] == 3
    assert summary["missing_auth"]["complete_plan"] == 0
    assert json.loads((directory / "summary.json").read_text(encoding="utf-8")) == summary
    assert "fictional-selected-key" not in (directory / "results.jsonl").read_text(encoding="utf-8") + capsys.readouterr().out


def test_api_failure_stops_without_retry_or_response_body_leak(tmp_path, capsys):
    attempts = []

    def endpoint(request):
        attempts.append(request)
        return httpx.Response(401, json={"error": {"message": "fictional-private-body", "type": "authentication_error"}})

    directory = tmp_path / "failed"
    with OpenAI(api_key="fictional-selected-key", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(endpoint))) as client:
        summary, finished = lab.run_trials(client, directory)
    assert not finished and len(attempts) == 1
    assert summary["split_auth"]["api_completed"] == 0
    assert summary["missing_auth"]["attempted"] == 0
    stored = (directory / "results.jsonl").read_text(encoding="utf-8")
    assert json.loads(stored)["score"] is None
    assert json.loads(stored)["error"]["http_status"] == 401
    assert "fictional-private-body" not in stored + capsys.readouterr().out


def test_run_entry_uses_named_profile_and_saves_summary(monkeypatch, tmp_path, capsys):
    def config(path):
        assert path == Path.home() / ".claude" / "settings-deepseek.json"
        return {"api_key": "fictional-selected-key", "base_url": "https://api.deepseek.com"}

    calls = []

    def endpoint(request):
        assert request.url == "https://api.deepseek.com/responses"
        name = lab.CASE_NAMES[len(calls) % 2]
        calls.append(request)
        output = dict(lab.EXPECTED, auth_header=None) if name == "missing_auth" else lab.EXPECTED
        return httpx.Response(200, json=response_payload(json.dumps(output)))

    def client(**kwargs):
        assert kwargs["max_retries"] == 0 and kwargs["timeout"] == 30
        return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(endpoint)))

    monkeypatch.setattr(sys, "argv", ["run_generation", "--run"])
    monkeypatch.setattr(lab, "__file__", str(tmp_path / "labs" / "retrieval" / "run_generation.py"))
    monkeypatch.setattr(lab, "load_config", config)
    monkeypatch.setattr(lab, "OpenAI", client)
    assert lab.main() == 0 and len(calls) == 6
    summaries = list((tmp_path / "traces" / "retrieval-generation").glob("*/summary.json"))
    assert len(summaries) == 1
    assert json.loads(summaries[0].read_text(encoding="utf-8"))["missing_auth"]["matches_expected"] == 3
    assert "符合本案预期" in capsys.readouterr().out


@pytest.mark.parametrize("status,unexpected", [("incomplete", False), ("completed", True)])
def test_incomplete_or_tool_response_stops_without_scoring(tmp_path, status, unexpected):
    def endpoint(request):
        return httpx.Response(200, json=response_payload("{}", status, unexpected))

    directory = tmp_path / "unexpected"
    with OpenAI(api_key="fictional-selected-key", max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(endpoint))) as client:
        summary, finished = lab.run_trials(client, directory)
    assert not finished and summary["split_auth"]["api_completed"] == 0
    assert json.loads((directory / "results.jsonl").read_text(encoding="utf-8"))["score"] is None
