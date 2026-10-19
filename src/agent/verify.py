import re

import pandas as pd

from src.schemas import AnalysisPlan


def verify_result(question: str, plan: AnalysisPlan, result: pd.DataFrame) -> tuple[bool, str]:
    text = question.casefold()
    for column in plan.intent.group_by:
        if column not in result.columns:
            return False, f"The requested grouping column '{column}' is missing from the result."
    if plan.x and plan.x not in result.columns:
        return False, f"The chart x column '{plan.x}' is missing from the result."
    if plan.y and plan.y not in result.columns:
        return False, f"The chart y column '{plan.y}' is missing from the result."
    match = re.search(r"\btop\s+(\d+)\b", text)
    if match and len(result) > int(match.group(1)):
        return False, "The result contains more rows than the requested top-N limit."
    if any(token in text for token in ("compare", " versus ", " vs ")) and len(result) < 2:
        return False, "The comparison result must contain at least two groups."
    return True, ""
