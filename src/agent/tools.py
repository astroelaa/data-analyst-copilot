import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BLOCKED = ("import", "open(", "__", "exec", "eval", "os.", "sys.", "subprocess", "to_csv", "read_")
SAFE_BUILTINS = {
    "len": len, "sum": sum, "min": min, "max": max, "round": round, "sorted": sorted,
    "abs": abs, "range": range, "list": list, "dict": dict, "str": str, "int": int,
    "float": float, "set": set, "zip": zip, "enumerate": enumerate,
}


def describe_data(df: pd.DataFrame) -> str:
    summary = pd.DataFrame(
        {"dtype": df.dtypes.astype(str), "non_null": df.notna().sum(), "unique": df.nunique()}
    )
    return f"{len(df)} rows\n{summary.to_string()}"


def run_pandas(code: str, df: pd.DataFrame) -> pd.DataFrame:
    lowered = code.lower()
    for token in BLOCKED:
        if token in lowered:
            raise ValueError(f"blocked token in code: {token}")
    scope = {"__builtins__": SAFE_BUILTINS, "df": df.copy(), "pd": pd}
    exec(code, scope)
    result = scope.get("result")
    if result is None:
        raise ValueError("code did not assign result")
    if isinstance(result, pd.Series):
        result = result.reset_index()
    if not isinstance(result, pd.DataFrame):
        result = pd.DataFrame({"result": [result]})
    return result


def plot_chart(result: pd.DataFrame, chart_type: str, x: str | None, y: str | None):
    if chart_type == "none" or x not in result.columns or y not in result.columns:
        return None
    figure, axis = plt.subplots(figsize=(7, 4))
    if chart_type == "bar":
        axis.bar(result[x].astype(str), result[y])
        axis.tick_params(axis="x", rotation=45)
    elif chart_type == "line":
        axis.plot(result[x], result[y])
    else:
        axis.pie(result[y], labels=result[x].astype(str), autopct="%1.0f%%")
    axis.set_title(f"{y} by {x}")
    figure.tight_layout()
    return figure
