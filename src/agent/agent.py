from dataclasses import dataclass, field

import pandas as pd

from src.agent.tools import describe_data, plot_chart, run_pandas
from src.llm.planner import fix_code, make_plan

MAX_RUN_ATTEMPTS = 2


@dataclass
class Session:
    df: pd.DataFrame
    history: list[dict] = field(default_factory=list)


def answer(session: Session, question: str) -> dict:
    trace = [{"tool": "describe_data", "output": describe_data(session.df)}]
    plan, record = make_plan(question)
    trace.append({"tool": "make_plan", "model": record["model"], "attempts": record["attempts"]})
    code = plan.pandas_code
    cost = record["cost"]
    fixed = False
    result = None
    error = None
    for attempt in range(1, MAX_RUN_ATTEMPTS + 1):
        try:
            result = run_pandas(code, session.df)
            trace.append({"tool": "run_pandas", "attempt": attempt, "status": "ok"})
            error = None
            break
        except Exception as exc:
            error = str(exc)
            trace.append({"tool": "run_pandas", "attempt": attempt, "status": "error", "error": error})
            if attempt == MAX_RUN_ATTEMPTS:
                break
            code, fix_record = fix_code(question, code, error, list(session.df.columns))
            cost += fix_record["cost"]
            fixed = True
    figure = None
    if result is not None:
        figure = plot_chart(result, plan.chart_type, plan.x, plan.y)
        trace.append({"tool": "plot_chart", "status": "drawn" if figure else "skipped"})
    session.history.append({"question": question, "ok": result is not None, "fixed": fixed})
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
