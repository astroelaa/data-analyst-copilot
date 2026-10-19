import pandas as pd

from src.agent.tools import run_pandas
from src.llm.local_fallback import make_local_plan


def test_local_fallback_handles_greeting():
    df = pd.DataFrame({"revenue": [10.0]})
    plan, record = make_local_plan("hello", list(df.columns))
    result = run_pandas(plan.pandas_code, df)
    assert record["model"] == "local-fallback"
    assert "Data Analyst Copilot" in result.iloc[0]["message"]
    assert "draw charts" in result.iloc[0]["message"]


def test_local_fallback_builds_executable_revenue_plan():
    df = pd.DataFrame(
        {
            "product": ["A", "B", "A"],
            "revenue": [10.0, 20.0, 5.0],
        }
    )
    plan, record = make_local_plan("What are the top 2 products by revenue?", list(df.columns))
    result = run_pandas(plan.pandas_code, df)
    assert record["model"] == "local-fallback"
    assert result.iloc[0]["product"] == "B"
    assert result.iloc[0]["revenue"] == 20.0


def test_local_fallback_builds_revenue_by_region_plan():
    df = pd.DataFrame(
        {
            "region": ["Cairo", "Cairo", "Giza"],
            "revenue": [10.0, 5.0, 20.0],
        }
    )
    plan, _ = make_local_plan("Show revenue by region", list(df.columns))
    result = run_pandas(plan.pandas_code, df)
    assert result.iloc[0]["region"] == "Giza"
    assert result.iloc[0]["revenue"] == 20.0


def test_local_fallback_builds_monthly_revenue_plan():
    df = pd.DataFrame(
        {
            "order_date": pd.to_datetime(["2025-01-01", "2025-01-15", "2025-02-01"]),
            "revenue": [10.0, 5.0, 20.0],
        }
    )
    plan, _ = make_local_plan("Show monthly revenue", list(df.columns))
    result = run_pandas(plan.pandas_code, df)
    assert len(result) == 2
    assert result.iloc[0]["revenue"] == 15.0


def test_local_fallback_builds_orders_by_category_plan():
    df = pd.DataFrame(
        {
            "category": ["A", "A", "B"],
            "order_id": [1, 1, 2],
        }
    )
    plan, _ = make_local_plan("How many orders per category?", list(df.columns))
    result = run_pandas(plan.pandas_code, df)
    assert result.loc[result["category"] == "A", "order_count"].iloc[0] == 1
