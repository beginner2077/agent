"""四组独立上下文实验；默认只预览，--run 才请求 DeepSeek。"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from openai import APIError, OpenAI


MODEL = "deepseek-flash"
GROUPS = {"A": (False, False), "B": (True, False), "C": (False, True), "D": (True, True)}
REPEATS = 3
INSTRUCTIONS = """请根据提供的目标接口资料，给出查询用户姓名的调用方案。
只返回一个 JSON 对象，恰好包含 method、url、auth_header、result_path 四个字段。
字段值只能是字符串或 null。
只能依据与当前目标服务有关的资料填写事实；缺少依据的字段返回 null，不猜测。
result_path 用点分路径表示，url 应替换成指定用户的实际路径。
示例用于展示格式，不是当前目标服务的接口资料。
不要调用工具或访问网络。"""
TASK = "目标服务：Directory，用户 ID：u42，目标：取得该用户的姓名。"
EXAMPLES = """示例目标：取得 Status 服务的健康状态。
示例资料：GET https://status.example.test/ping，无需认证，响应为 {"healthy": true}。
示例输出：
{"method":"GET","url":"https://status.example.test/ping","auth_header":null,"result_path":"healthy"}

示例目标：查询 Weather 服务的城市天气。
示例资料：未提供。
示例输出：
{"method":null,"url":null,"auth_header":null,"result_path":null}"""
DOCUMENT = """Directory API v2：
按用户 ID 获取用户资料：GET https://directory.example.test/v2/members/{id}
认证要求：在请求头 X-Org-Key 中传入 API key。
响应示例：{"data":{"profile":{"display_name":"李明"}}}"""
# 仅用于收到回复后的评价，不参与请求组装。
EXPECTED = {
    "method": "GET", "url": "https://directory.example.test/v2/members/u42",
    "auth_header": "X-Org-Key", "result_path": "data.profile.display_name",
}


def make_request(group: str) -> dict:
    examples, document = GROUPS[group]
    parts = []
    if examples:
        parts.append("[示例]\n" + EXAMPLES)
    if document:
        parts.append("[目标文档]\n" + DOCUMENT)
    parts.append(TASK)
    # 每次新建一条 user 消息，不携带其他试验的回答，也不读取整份 README。
    return {
        "model": MODEL, "instructions": INSTRUCTIONS,
        "input": [{"role": "user", "content": "\n\n".join(parts)}],
        "reasoning": {"effort": "none"}, "temperature": 0.2, "top_p": 1.0,
        "max_output_tokens": 512, "tools": [], "tool_choice": "none",
        "text": {"format": {"type": "text"}},
    }


def score_output(text: str, has_document: bool) -> dict:
    score = {"json_valid": False, "schema_valid": False, "supported": None,
             "complete": False, "correct_fields": None}
    duplicate_keys = False

    def collect_pairs(pairs):
        nonlocal duplicate_keys
        if len({key for key, _ in pairs}) != len(pairs):
            duplicate_keys = True
        return dict(pairs)

    def reject_constant(value):
        raise ValueError("Non-JSON numeric constant")

    try:
        value = json.loads(text, object_pairs_hook=collect_pairs, parse_constant=reject_constant)
    except (ValueError, TypeError):
        return score
    score["json_valid"] = True
    if (duplicate_keys or not isinstance(value, dict) or set(value) != set(EXPECTED)
            or any(item is not None and not isinstance(item, str) for item in value.values())):
        return score
    score["schema_valid"] = True
    if has_document:
        score["supported"] = all(value[key] is None or value[key] == expected for key, expected in EXPECTED.items())
        score["correct_fields"] = sum(value[key] == expected for key, expected in EXPECTED.items())
        score["complete"] = value == EXPECTED
    else:
        # 无资料时允许合规地回答未知；不能把猜中地址等同于有事实依据。
        score["supported"] = all(item is None for item in value.values())
    return score


def load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise ValueError("无法读取指定的 DeepSeek 配置，请检查路径、编码及 JSON 格式。") from None
    env = data.get("env") if isinstance(data, dict) else None
    if not isinstance(env, dict):
        raise ValueError("配置需要包含 env 对象。")
    key = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY")
    base = env.get("ANTHROPIC_BASE_URL")
    if (not isinstance(key, str) or not key.strip() or not isinstance(base, str)
            or base.rstrip("/") not in ("https://api.deepseek.com/anthropic", "https://api.deepseek.com")):
        raise ValueError("请检查命名配置中的密钥和官方 DeepSeek HTTPS 地址。")
    return {"api_key": key.strip(), "base_url": "https://api.deepseek.com"}


def summarize(records: list[dict]) -> dict:
    summary = {}
    for group in GROUPS:
        attempted = [row for row in records if row["group"] == group]
        completed = [row for row in attempted if row["error"] is None]
        judged = [row for row in completed if row["score"]["schema_valid"]]
        summary[group] = {
            "planned": REPEATS, "attempted": len(attempted), "api_completed": len(completed),
            "json_valid": sum(row["score"]["json_valid"] for row in completed),
            "schema_valid": len(judged),
            "supported": sum(row["score"]["supported"] for row in judged),
            "support_evaluable": len(judged),
            "complete": sum(row["score"]["complete"] for row in completed),
        }
    return summary


def request_model(client: OpenAI, request: dict) -> dict:
    """执行一次请求，保留可核对结果；异常只记录类型及状态码。"""
    result = {"request": request, "error": None, "output_text": None, "response_meta": None}
    try:
        response = client.responses.create(**request)
        reported = response.model_dump(mode="json")
        result["response_meta"] = {key: reported.get(key) for key in (
            "id", "model", "status", "reasoning", "temperature", "top_p",
            "max_output_tokens", "usage", "incomplete_details",
        )}
        result["output_text"] = response.output_text
        unexpected = any(item.get("type") not in ("message", "reasoning")
                         for item in reported.get("output", []))
        if response.status != "completed" or unexpected:
            result["error"] = {"type": "response_not_completed_or_unexpected_tool_call"}
    except APIError as error:
        # SDK 异常正文可能含服务响应，不能直接输出其 str。
        result["error"] = {"type": type(error).__name__, "http_status": getattr(error, "status_code", None)}
    return result


def run_trials(client: OpenAI, directory: Path) -> tuple[dict, bool]:
    directory.mkdir(parents=True, exist_ok=False)
    records = []
    stopped = False
    with (directory / "results.jsonl").open("x", encoding="utf-8") as stream:
        # 交错运行 A/B/C/D，每个请求独立；不把单组全部放在最前面。
        for trial in range(1, REPEATS + 1):
            for group, (_, has_document) in GROUPS.items():
                request = make_request(group)
                row = {"group": group, "trial": trial, **request_model(client, request), "score": None}
                if row["error"] is None:
                    row["score"] = score_output(row["output_text"], has_document)
                records.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                state = "API完成" if row["error"] is None else "接口异常，已停止"
                print(f"{group} 第 {trial}/{REPEATS} 次：{state}", flush=True)
                if row["error"] is not None:
                    print(json.dumps(row["error"], ensure_ascii=False), flush=True)
                    stopped = True
                    break
            if stopped:
                break
    summary = summarize(records)
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary, not stopped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="执行最多12次模型请求；默认只预览输入")
    args = parser.parse_args()
    if not args.run:
        for group in GROUPS:
            print(f"\n=== {group} 组 ===")
            print(json.dumps(make_request(group), ensure_ascii=False, indent=2))
        print("\n仅预览：没有读取密钥或调用模型。--run 将运行四组各三次。")
        return 0
    try:
        config = load_config(Path.home() / ".claude" / "settings-deepseek.json")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        directory = Path(__file__).resolve().parents[2] / "traces" / "prompt-context" / f"{stamp}-{uuid.uuid4().hex[:8]}"
        print(f"结果目录：{directory}", flush=True)
        with OpenAI(**config, timeout=30, max_retries=0) as client:
            summary, finished = run_trials(client, directory)
        print("\n组  API完成  JSON可解析  结构合规  有依据/可判定  任务完成")
        for group, counts in summary.items():
            print(f"{group}   {counts['api_completed']}/{counts['planned']}       "
                  f"{counts['json_valid']}          {counts['schema_valid']}          "
                  f"{counts['supported']}/{counts['support_evaluable']}          {counts['complete']}")
        print("结果已保存；任务完成以本地四字段规则评价，不代表真实接口调用或自动检索成功。")
        return 0 if finished else 1
    except ValueError as error:
        print(str(error))
    except OSError:
        print("无法创建或写入实验结果目录，请检查路径与权限。")
    except KeyboardInterrupt:
        print("实验已中断，已写入的结果保留。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
