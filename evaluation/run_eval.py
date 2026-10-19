import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.agent.agent import Session, answer
from src.agent.tools import load_csv

QUESTIONS = Path("evaluation/questions.json")
RESULTS = Path("evaluation/results.json")
CSV = Path("data/sales.csv")
PAUSE_SECONDS = 3
MAX_LLM_ATTEMPTS = 1


def flatten(value) -> tuple[list[float], list[str]]:
    if isinstance(value, pd.Series):
        value = value.reset_index()
    if not isinstance(value, pd.DataFrame):
        value = pd.DataFrame({"value": [value]})
    numbers, labels = [], []
    for cell in value.to_numpy().ravel():
        if isinstance(cell, (int, float, np.integer, np.floating)) and not isinstance(cell, bool):
            numbers.append(float(cell))
        else:
            labels.append(str(cell).strip().lower())
    return numbers, labels


def matches(expected, actual) -> bool:
    expected_numbers, expected_labels = flatten(expected)
    actual_numbers, actual_labels = flatten(actual)
    numbers_ok = all(
        any(math.isclose(e, a, rel_tol=1e-3, abs_tol=0.005) for a in actual_numbers)
        for e in expected_numbers
    )
    labels_ok = all(e in actual_labels for e in expected_labels)
    return numbers_ok and labels_ok


def reference_answer(code: str, df: pd.DataFrame):
    scope = {"df": df.copy(), "pd": pd}
    exec(code, scope)
    return scope["result"]


def first_try_ok(trace: list[dict]) -> bool:
    return any(
        step.get("tool") == "run_pandas" and step.get("attempt") == 1 and step.get("status") == "ok"
        for step in trace
    )


def retryable(error: Exception) -> bool:
    message = str(error)
    return "429" in message or "504" in message


def evaluate_one(item: dict, df: pd.DataFrame) -> dict:
    expected = reference_answer(item["reference_code"], df)
    start = time.time()
    row = {
        "id": item["id"],
        "lang": item["lang"],
        "question": item["question"],
        "correct": False,
        "first_try_ok": False,
        "final_ok": False,
        "fixed": False,
        "tier": None,
        "model": None,
        "code": None,
        "error": None,
    }
    for attempt in range(MAX_LLM_ATTEMPTS):
        try:
            output = answer(Session(df=df), item["question"])
            break
        except Exception as exc:
            if not retryable(exc) or attempt == MAX_LLM_ATTEMPTS - 1:
                row["error"] = str(exc)[:300]
                row["seconds"] = round(time.time() - start, 2)
                return row
            time.sleep(20 * 2**attempt)
    row["first_try_ok"] = first_try_ok(output["trace"])
    row["final_ok"] = output["result"] is not None
    row["fixed"] = output["fixed"]
    row["tier"] = output["record"]["tier"]
    row["model"] = output["record"]["model"]
    row["code"] = output["code"]
    row["error"] = output["error"]
    row["correct"] = row["final_ok"] and matches(expected, output["result"])
    row["seconds"] = round(time.time() - start, 2)
    return row


def summarize(rows: list[dict]) -> dict:
    total = len(rows)

    def pct(key: str, subset: list[dict]) -> float:
        return round(100 * sum(r[key] for r in subset) / len(subset), 1) if subset else 0.0

    return {
        "questions": total,
        "correct_pct": pct("correct", rows),
        "code_success_first_try_pct": pct("first_try_ok", rows),
        "code_success_after_autofix_pct": pct("final_ok", rows),
        "avg_seconds": round(sum(r["seconds"] for r in rows) / total, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    args = parser.parse_args()
    df = load_csv(CSV)
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    selected = args.only.split(",") if args.only else [item["id"] for item in items]
    selected_items = [item for item in items if item["id"] in selected]
    existing = json.loads(RESULTS.read_text(encoding="utf-8")) if args.only and RESULTS.exists() else {"rows": []}
    rows = {row["id"]: row for row in existing["rows"]}
    for index, item in enumerate(selected_items):
        row = evaluate_one(item, df)
        rows[item["id"]] = row
        print(row["id"], "correct" if row["correct"] else "WRONG", row["seconds"], row["error"] or "")
        if index < len(selected_items) - 1:
            time.sleep(PAUSE_SECONDS)
    ordered = [rows[item["id"]] for item in items if item["id"] in rows]
    summary = summarize(ordered)
    RESULTS.write_text(json.dumps({"summary": summary, "rows": ordered}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
