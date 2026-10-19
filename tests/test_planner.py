from src.llm.planner import PLAN_CACHE, make_plan
from src.schemas import AnalysisPlan


def test_make_plan_uses_uploaded_dataframe_context(monkeypatch):
    PLAN_CACHE.clear()
    captured = {}

    def fake_remote(question, prompt, valid, chunks):
        captured["prompt"] = prompt
        captured["chunks"] = chunks
        return (
            AnalysisPlan(
                goal="Sum revenue",
                columns=["amount"],
                steps=["Sum amount"],
                pandas_code="result = pd.DataFrame({'total': [df['amount'].sum()]})",
                chart_type="none",
            ),
            {"model": "test", "attempts": 1},
        )

    monkeypatch.setattr("src.llm.planner._make_remote_plan", fake_remote)
    plan, _ = make_plan(
        "What is the total amount?",
        ["amount"],
        "Rows: 2\nColumns:\n- amount: dtype=float64, min=1.0, max=2.0",
    )

    assert plan.columns == ["amount"]
    assert "dtype=float64" in captured["prompt"]
    assert captured["chunks"][0]["source"] == "uploaded dataframe"
