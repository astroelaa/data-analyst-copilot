import pandas as pd

from src.agent.tools import run_pandas
from src.llm.local_fallback import make_local_plan


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
