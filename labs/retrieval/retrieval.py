"""本地关键词检索与关联补全；仅预览模型输入，不读取密钥或请求模型。"""

import argparse
from dataclasses import dataclass
import json
import re

from labs.prompt_context.run_experiment import make_request


@dataclass(frozen=True)
class Chunk:
    id: str
    service: str
    version: str
    title: str
    text: str
    related: tuple[str, ...] = ()


MEMBER_V2 = Chunk(
    "directory-v2-member", "Directory", "v2", "获取用户资料",
    '按用户 ID 获取用户资料。\n'
    '接口：GET https://directory.example.test/v2/members/{id}\n'
    '认证：参见本版本全局认证章节。\n'
    '响应示例：{"data":{"profile":{"display_name":"李明"}}}',
    ("directory-v2-auth",),
)
AUTH_V2 = Chunk(
    "directory-v2-auth", "Directory", "v2", "全局认证",
    "所有接口都需要在请求头 X-Org-Key 中传入 API key。",
)
MEMBER_V1 = Chunk(
    "directory-v1-member", "Directory", "v1", "获取用户资料和姓名",
    '按用户 ID 获取用户资料，查询用户姓名。\n'
    '接口：GET https://directory.example.test/v1/users/{id}\n'
    '认证：请求头 Authorization。\n'
    '响应示例：{"name":"李明"}',
)

# 同一检索流程运行五种输入条件；这里不包含评价答案。
CASES = {
    "split_auth": {
        "query": "获取用户资料", "service": "Directory", "version": "v2",
        "chunks": (MEMBER_V2, AUTH_V2),
    },
    "paraphrase": {
        "query": "这个人怎么称呼", "service": "Directory", "version": "v2",
        "chunks": (MEMBER_V2, AUTH_V2),
    },
    "version_noise": {
        "query": "获取用户资料和姓名", "service": "Directory", "version": "v2",
        "chunks": (MEMBER_V1, MEMBER_V2, AUTH_V2),
    },
    "missing_auth": {
        "query": "获取用户资料", "service": "Directory", "version": "v2",
        "chunks": (MEMBER_V2, MEMBER_V1),
    },
    "unknown_service": {
        "query": "获取用户资料", "service": "Roster", "version": "v2",
        "chunks": (MEMBER_V2, AUTH_V2, MEMBER_V1),
    },
}


def terms(text: str) -> set[str]:
    """英文保留标识符，中文取相邻双字；这是简化关键词方法，不是 BM25。"""
    result = set()
    for word in re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", text.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", word) and len(word) > 1:
            result.update(word[i:i + 2] for i in range(len(word) - 1))
        else:
            result.add(word)
    return result


def retrieve(chunks: tuple[Chunk, ...], query: str, service: str, version: str,
             top_k: int = 1) -> dict:
    if top_k < 1:
        raise ValueError("top_k 必须大于零")
    by_id = {chunk.id: chunk for chunk in chunks}
    if len(by_id) != len(chunks):
        raise ValueError("片段 ID 不能重复")
    query_terms = terms(query)
    ranked = []
    for chunk in chunks:
        if (chunk.service, chunk.version) != (service, version):
            continue
        score = len(query_terms & terms(chunk.title + "\n" + chunk.text))
        if score:
            ranked.append({"id": chunk.id, "score": score})
    ranked.sort(key=lambda item: (-item["score"], item["id"]))
    selected = [item["id"] for item in ranked[:top_k]]
    context_ids = list(selected)
    visited = set(selected)
    unresolved = []
    # 沿片段明确引用补全；每个 ID 最多访问一次，循环引用不会无限展开。
    for chunk_id in context_ids:
        for related_id in by_id[chunk_id].related:
            if related_id in visited:
                continue
            visited.add(related_id)
            related = by_id.get(related_id)
            if related is None:
                reason = "missing"
            elif (related.service, related.version) != (service, version):
                reason = "scope_mismatch"
            else:
                context_ids.append(related_id)
                continue
            unresolved.append({"from": chunk_id, "ref": related_id, "reason": reason})
    context = "\n\n".join(
        f"[片段 {chunk.id}] 来源：{chunk.service} API {chunk.version} / {chunk.title}\n{chunk.text}"
        for chunk in (by_id[chunk_id] for chunk_id in context_ids)
    )
    return {
        "query": query, "filters": {"service": service, "version": version},
        "candidates": ranked, "selected": selected,
        "expanded": [chunk_id for chunk_id in context_ids if chunk_id not in selected],
        "unresolved_refs": unresolved, "context_ids": context_ids, "context": context,
    }


def build_request(case: dict, trace: dict) -> dict:
    # 复用上一实验的固定模型、指令和参数；只替换本题输入，不执行该请求。
    request = make_request("A")
    context = trace["context"] or "未检索到可用资料。"
    request["input"] = [{"role": "user", "content": (
        f"[目标文档]\n{context}\n\n"
        f"目标服务：{case['service']}，版本：{case['version']}，用户 ID：u42。\n"
        f"用户问题：{case['query']}"
    )}]
    return request


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, default="split_auth")
    args = parser.parse_args()
    case = CASES[args.case]
    trace = retrieve(**case)
    # 正文只在请求体中展示一次，便于对照检索证据和实际组装的输入。
    print(json.dumps({
        "case": args.case,
        "retrieval": {key: value for key, value in trace.items() if key != "context"},
        "prepared_request": build_request(case, trace),
    }, ensure_ascii=False, indent=2))
    print("仅本地检索与输入预览：未请求模型，未执行示例接口。score 是词项重合数，不是正确概率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
