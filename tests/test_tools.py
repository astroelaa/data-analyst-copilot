import pandas as pd
import pytest

from src.agent.tools import plot_chart, run_pandas

DF = pd.DataFrame({"region": ["a", "b", "a"], "revenue": [1.0, 2.0, 3.0]})


def test_run_pandas_returns_result():
    result = run_pandas("result = df.groupby('region', as_index=False)['revenue'].sum()", DF)
    assert result.loc[result["region"] == "a", "revenue"].iloc[0] == 4.0


def test_run_pandas_does_not_modify_original():
    run_pandas("df['revenue'] = 0\nresult = df", DF)
    assert DF["revenue"].sum() == 6.0


def test_blocked_code_rejected():
    with pytest.raises(ValueError):
        run_pandas("import os\nresult = df", DF)


def test_missing_result_rejected():
    with pytest.raises(ValueError):
        run_pandas("x = 1", DF)


def test_plot_skipped_for_none():
    assert plot_chart(DF, "none", "region", "revenue") is None
