"""比较完整/缺认证两案的实际生成；默认仅预览，--run 才请求模型。"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from openai import OpenAI

from labs.prompt_context.run_experiment import (
    EXPECTED, REPEATS, load_config, request_model, score_output,
)
from labs.retrieval.retrieval import CASES, build_request, retrieve


CASE_NAMES = ("split_auth", "missing_auth")


def evaluate(text: str, case_name: str) -> dict:
    if case_name not in CASE_NAMES:
        raise ValueError("本轮只评价完整资料与缺认证两案")
    # 复用 JSON/schema 校验，事实支持必须按本案例的可用资料重新评价。
    parsed = score_output(text, has_document=True)
    score = {"json_valid": parsed["json_valid"], "schema_valid": parsed["schema_valid"],
             "supported": None, "matches_expected": False, "complete_plan": False}
    if not score["schema_valid"]:
        return score
    expected = dict(EXPECTED)
    if case_name == "missing_auth":
        expected["auth_header"] = None
    actual = json.loads(text)
    score["supported"] = all(actual[key] is None or actual[key] == value for key, value in expected.items())
    score["matches_expected"] = actual == expected
    # 缺认证时，正确承认未知可以符合本案预期，但不能称为完整方案。
    score["complete_plan"] = score["matches_expected"] and all(value is not None for value in expected.values())
    return score


def summarize(records: list[dict]) -> dict:
    summary = {}
    for name in CASE_NAMES:
        attempted = [row for row in records if row["case"] == name]
        completed = [row for row in attempted if row["error"] is None]
        judged = [row for row in completed if row["score"]["schema_valid"]]
        summary[name] = {
            "planned": REPEATS, "attempted": len(attempted), "api_completed": len(completed),
            "json_valid": sum(row["score"]["json_valid"] for row in completed),
            "schema_valid": len(judged),
            "supported": sum(row["score"]["supported"] for row in judged),
            "support_evaluable": len(judged),
            "matches_expected": sum(row["score"]["matches_expected"] for row in completed),
            "complete_plan": sum(row["score"]["complete_plan"] for row in completed),
        }
    return summary


def run_trials(client: OpenAI, directory: Path) -> tuple[dict, bool]:
    directory.mkdir(parents=True, exist_ok=False)
    records = []
    stopped = False
    with (directory / "results.jsonl").open("x", encoding="utf-8") as stream:
        for trial in range(1, REPEATS + 1):
            for name in CASE_NAMES:
                case = CASES[name]
                trace = retrieve(**case)
                request = build_request(case, trace)
                row = {"case": name, "trial": trial,
                       "retrieval": {key: value for key, value in trace.items() if key != "context"},
                       **request_model(client, request), "score": None}
                if row["error"] is None:
                    row["score"] = evaluate(row["output_text"], name)
                records.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                state = "API完成" if row["error"] is None else "接口异常，已停止"
                print(f"{name} 第 {trial}/{REPEATS} 次：{state}", flush=True)
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
    parser.add_argument("--run", action="store_true", help="执行两案各三次，最多六次真实模型请求")
    args = parser.parse_args()
    if not args.run:
        for name in CASE_NAMES:
            case = CASES[name]
            trace = retrieve(**case)
            print(json.dumps({"case": name, "prepared_request": build_request(case, trace)}, ensure_ascii=False, indent=2))
        print("仅预览：没有读取密钥或调用模型。--run 将交错运行两案各三次。")
        return 0
    try:
        config = load_config(Path.home() / ".claude" / "settings-deepseek.json")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        directory = Path(__file__).resolve().parents[2] / "traces" / "retrieval-generation" / f"{stamp}-{uuid.uuid4().hex[:8]}"
        print(f"结果目录：{directory}", flush=True)
        with OpenAI(**config, timeout=30, max_retries=0) as client:
            summary, finished = run_trials(client, directory)
        print("\n案例  API完成  结构合规  有依据/可判定  符合本案预期  完整方案")
        for name, counts in summary.items():
            print(f"{name}  {counts['api_completed']}/{counts['planned']}  {counts['schema_valid']}  "
                  f"{counts['supported']}/{counts['support_evaluable']}  "
                  f"{counts['matches_expected']}  {counts['complete_plan']}")
        print("缺认证时 auth_header=null 可符合预期，但不构成完整方案；未执行示例接口。")
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
