from typing import Literal

from pydantic import BaseModel, Field


class AnalysisIntent(BaseModel):
    metric: str | None = None
    aggregation: Literal["sum", "mean", "count", "nunique", "min", "max", "none"] = "none"
    filters: list[str] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    order_by: str | None = None
    limit: int | None = None
    comparison: list[str] = Field(default_factory=list)
    date_range: str | None = None


class AnalysisPlan(BaseModel):
    intent: AnalysisIntent = Field(default_factory=AnalysisIntent)
    goal: str
    columns: list[str]
    steps: list[str]
    pandas_code: str
    chart_type: Literal["bar", "line", "pie", "none"]
    x: str | None = None
    y: str | None = None


class CodeFix(BaseModel):
    pandas_code: str
