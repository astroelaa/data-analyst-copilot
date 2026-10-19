from typing import Literal

from pydantic import BaseModel


class AnalysisPlan(BaseModel):
    goal: str
    columns: list[str]
    steps: list[str]
    pandas_code: str
    chart_type: Literal["bar", "line", "pie", "none"]
    x: str | None = None
    y: str | None = None


class CodeFix(BaseModel):
    pandas_code: str
