from dataclasses import dataclass, field

import pandas as pd

from src.agent.tools import describe_data, plot_chart, profile_data, run_pandas
from src.agent.verify import verify_result
from src.llm.planner import fix_code, make_plan

MAX_RUN_ATTEMPTS = 2


@dataclass
class Session:
    df: pd.DataFrame
    history: list[dict] = field(default_factory=list)


def _conversation_context(session: Session) -> str:
    return "\n".join(
        f"Question: {item['question']}\nResult columns: {item.get('result_columns', [])}"
        for item in session.history[-3:]
    )


def _repair(
    question: str,
    code: str,
    error: str,
    columns: list[str],
    cost: float,
) -> tuple[str, float, bool]:
    repaired_code, repair_record = fix_code(question, code, error, columns)
    return repaired_code, cost + repair_record["cost"], True


def answer(session: Session, question: str) -> dict:
    trace = [
        {"tool": "describe_data", "output": describe_data(session.df)},
        {"tool": "profile_data", "output": profile_data(session.df)},
    ]
    plan, record = make_plan(
        question,
        list(session.df.columns),
        profile_data(session.df),
        _conversation_context(session),
    )
    trace.append({"tool": "make_plan", "attempts": record["attempts"]})
    code = plan.pandas_code
    cost = record["cost"]
    fixed = False
    result = None
    error = None
    for attempt in range(1, MAX_RUN_ATTEMPTS + 1):
        try:
            result = run_pandas(code, session.df)
            trace.append({"tool": "run_pandas", "attempt": attempt, "status": "ok"})
            valid, verification_error = verify_result(question, plan, result)
            if valid:
                error = None
                break
            error = verification_error
            trace.append({"tool": "verify_result", "status": "error", "error": verification_error})
            if attempt == MAX_RUN_ATTEMPTS:
                result = None
            else:
                code, cost, fixed = _repair(
                    question,
                    code,
                    verification_error,
                    list(session.df.columns),
                    cost,
                )
        except Exception as exc:
            error = str(exc)
            trace.append({"tool": "run_pandas", "attempt": attempt, "status": "error", "error": error})
            if attempt == MAX_RUN_ATTEMPTS:
                break
            code, cost, fixed = _repair(
                question,
                code,
                error,
                list(session.df.columns),
                cost,
            )
    figure = None
    if result is not None:
        figure = plot_chart(result, plan.chart_type, plan.x, plan.y)
        trace.append({"tool": "plot_chart", "status": "drawn" if figure else "skipped"})
    session.history.append(
        {
            "question": question,
            "ok": result is not None and error is None,
            "fixed": fixed,
            "result_columns": list(result.columns) if result is not None else [],
        }
    )
    return {
        "plan": plan,
        "code": code,
        "result": result,
        "figure": figure,
        "trace": trace,
        "record": record,
        "cost": cost,
        "fixed": fixed,
        "error": error,
    }
