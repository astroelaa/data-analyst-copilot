import pandas as pd

from src.agent import agent
from src.schemas import AnalysisPlan


def _plan(code):
    return AnalysisPlan(
        goal="Calculate a result",
        columns=["amount"],
        steps=["Calculate the amount"],
        pandas_code=code,
        chart_type="none",
    )


def test_answer_executes_plan_and_records_tools(monkeypatch):
    monkeypatch.setattr(
        agent,
        "make_plan",
        lambda question, columns, context: (
            _plan("result = pd.DataFrame({'total': [df['amount'].sum()]})"),
            {
                "model": "test",
                "tier": "cheap",
                "attempts": 1,
                "cost": 0.0,
                "input_tokens": 1,
                "output_tokens": 1,
                "citations": [],
            },
        ),
    )
    session = agent.Session(pd.DataFrame({"amount": [2, 3]}))
    output = agent.answer(session, "What is the total amount?")

    assert output["result"].iloc[0]["total"] == 5
    assert [step["tool"] for step in output["trace"]] == [
        "describe_data",
        "make_plan",
        "run_pandas",
        "plot_chart",
    ]
    assert session.history[-1]["ok"] is True


def test_answer_retries_failed_code_with_fix(monkeypatch):
    monkeypatch.setattr(
        agent,
        "make_plan",
        lambda question, columns, context: (
            _plan("result = df['missing'].sum()"),
            {
                "model": "test",
                "tier": "cheap",
                "attempts": 1,
                "cost": 0.0,
                "input_tokens": 1,
                "output_tokens": 1,
                "citations": [],
            },
        ),
    )
    monkeypatch.setattr(
        agent,
        "fix_code",
        lambda question, code, error, columns: (
            "result = pd.DataFrame({'total': [df['amount'].sum()]})",
            {"cost": 0.0},
        ),
    )
    session = agent.Session(pd.DataFrame({"amount": [2, 3]}))
    output = agent.answer(session, "What is the total amount?")

    assert output["fixed"] is True
    assert output["result"].iloc[0]["total"] == 5
    assert any(step.get("attempt") == 2 for step in output["trace"])
