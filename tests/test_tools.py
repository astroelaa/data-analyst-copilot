import pandas as pd
import pytest

from src.agent.tools import load_csv, plot_chart, profile_data, run_pandas

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


def test_profile_data_describes_uploaded_dataframe():
    profile = profile_data(DF)
    assert "Rows: 3" in profile
    assert "- region:" in profile
    assert "sample_values=a, b" in profile
    assert "min=1.0" in profile


def test_run_pandas_blocks_file_and_introspection_access():
    for code in (
        "result = open('secret.txt').read()",
        "result = df.__class__",
        "result = __import__('os')",
    ):
        with pytest.raises(ValueError):
            run_pandas(code, DF)


def test_plot_chart_supports_bar_line_and_pie():
    for chart_type in ("bar", "line", "pie"):
        figure = plot_chart(DF, chart_type, "region", "revenue")
        assert figure is not None


def test_load_csv_parses_date_columns(tmp_path):
    path = tmp_path / "custom.csv"
    path.write_text("event_date,amount\n2026-01-02,4\n2026-02-03,5\n", encoding="utf-8")
    loaded = load_csv(path)
    assert str(loaded["event_date"].dtype).startswith("datetime")
    assert loaded["amount"].sum() == 9
