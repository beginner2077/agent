"""检索与组装的离线验收；不把通过测试等同模型生成正确。"""

from dataclasses import replace
import json
import sys

import pytest

from labs.retrieval import retrieval as lab


def test_split_auth_expands_rule_into_actual_model_input():
    case = lab.CASES["split_auth"]
    trace = lab.retrieve(**case)
    assert trace["selected"] == [lab.MEMBER_V2.id]
    assert trace["expanded"] == [lab.AUTH_V2.id]
    assert not trace["unresolved_refs"]
    request = lab.build_request(case, trace)
    text = request["input"][0]["content"]
    assert lab.MEMBER_V2.text in text and lab.AUTH_V2.text in text
    assert "Directory API v2" in text
    assert len(request["input"]) == 1
    assert request["model"] == "deepseek-flash" and request["tools"] == []


def test_paraphrase_exposes_lexical_limit_even_when_relevant_docs_exist():
    case = lab.CASES["paraphrase"]
    assert lab.MEMBER_V2 in case["chunks"]
    trace = lab.retrieve(**case)
    assert not trace["candidates"] and not trace["context_ids"]
    assert "未检索到可用资料" in lab.build_request(case, trace)["input"][0]["content"]


def test_version_filter_excludes_old_doc_despite_higher_keyword_score():
    case = lab.CASES["version_noise"]
    query_terms = lab.terms(case["query"])
    assert len(query_terms & lab.terms(lab.MEMBER_V1.title + lab.MEMBER_V1.text)) > len(
        query_terms & lab.terms(lab.MEMBER_V2.title + lab.MEMBER_V2.text))
    trace = lab.retrieve(**case)
    assert trace["context_ids"] == [lab.MEMBER_V2.id, lab.AUTH_V2.id]
    assert all(item["id"] != lab.MEMBER_V1.id for item in trace["candidates"])
    assert "/v1/" not in trace["context"] and "Authorization" not in trace["context"]


def test_missing_auth_is_reported_without_fabrication_or_v1_fallback():
    case = lab.CASES["missing_auth"]
    trace = lab.retrieve(**case)
    assert trace["context_ids"] == [lab.MEMBER_V2.id]
    assert trace["unresolved_refs"] == [{"from": lab.MEMBER_V2.id, "ref": lab.AUTH_V2.id, "reason": "missing"}]
    request = lab.build_request(case, trace)
    assert "X-Org-Key" not in json.dumps(request)
    assert "Authorization" not in json.dumps(request)
    assert "null" in request["instructions"]


def test_unknown_service_does_not_borrow_directory_docs():
    case = lab.CASES["unknown_service"]
    trace = lab.retrieve(**case)
    assert not trace["context_ids"]
    request = lab.build_request(case, trace)
    assert "directory.example.test" not in json.dumps(request)
    assert case["service"] in request["input"][0]["content"]


@pytest.mark.parametrize("service,version", [("Other", "v2"), ("Directory", "v1")])
def test_relation_cannot_bypass_service_or_version_filter(service, version):
    wrong_auth = replace(lab.AUTH_V2, service=service, version=version)
    trace = lab.retrieve((lab.MEMBER_V2, wrong_auth), "获取用户资料", "Directory", "v2")
    assert trace["context_ids"] == [lab.MEMBER_V2.id]
    assert trace["unresolved_refs"][0]["reason"] == "scope_mismatch"


def test_cycle_and_shared_reference_are_only_expanded_once():
    member = replace(lab.MEMBER_V2, related=(lab.AUTH_V2.id, lab.AUTH_V2.id))
    auth = replace(lab.AUTH_V2, related=(lab.MEMBER_V2.id,))
    trace = lab.retrieve((member, auth), "获取用户资料", "Directory", "v2")
    assert trace["context_ids"] == [member.id, auth.id]
    assert not trace["unresolved_refs"]


def test_invalid_index_and_top_k_fail_explicitly():
    with pytest.raises(ValueError, match="ID"):
        lab.retrieve((lab.MEMBER_V2, lab.MEMBER_V2), "用户", "Directory", "v2")
    with pytest.raises(ValueError, match="top_k"):
        lab.retrieve((lab.MEMBER_V2,), "用户", "Directory", "v2", top_k=0)


def test_cli_prints_evidence_and_prepared_request_only(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["retrieval", "--case", "split_auth"])
    assert lab.main() == 0
    output = capsys.readouterr().out
    payload = json.JSONDecoder().raw_decode(output)[0]
    assert payload["retrieval"]["expanded"] == [lab.AUTH_V2.id]
    assert "X-Org-Key" in payload["prepared_request"]["input"][0]["content"]
    assert "未请求模型" in output
