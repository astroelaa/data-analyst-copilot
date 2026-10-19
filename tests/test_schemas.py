import pytest
from pydantic import ValidationError

from src.schemas import AnalysisPlan

VALID = {
    "goal": "top products",
    "columns": ["product", "revenue"],
    "steps": ["group by product", "sum revenue", "take top 5"],
    "pandas_code": "result = df.groupby('product')['revenue'].sum().nlargest(5).reset_index()",
    "chart_type": "bar",
    "x": "product",
    "y": "revenue",
}


def test_valid_plan_parses():
    plan = AnalysisPlan.model_validate(VALID)
    assert plan.chart_type == "bar"


def test_invalid_chart_type_rejected():
    with pytest.raises(ValidationError):
        AnalysisPlan.model_validate({**VALID, "chart_type": "scatter3d"})


def test_missing_code_rejected():
    data = {key: value for key, value in VALID.items() if key != "pandas_code"}
    with pytest.raises(ValidationError):
        AnalysisPlan.model_validate(data)
