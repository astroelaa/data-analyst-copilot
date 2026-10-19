import re

from src.rag.store import citation, load_entries
from src.schemas import AnalysisPlan


def _plan(goal: str, columns: list[str], steps: list[str], code: str, chart_type: str = "none", x: str | None = None, y: str | None = None) -> AnalysisPlan:
    return AnalysisPlan(
        goal=goal,
        columns=columns,
        steps=steps,
        pandas_code=code,
        chart_type=chart_type,
        x=x,
        y=y,
    )


def make_local_plan(question: str, available_columns: list[str]) -> tuple[AnalysisPlan, dict]:
    text = question.lower()
    required = set(available_columns)

    def has(*columns: str) -> bool:
        return set(columns).issubset(required)

    if has("product", "revenue") and re.search(r"top\s+(\d+)", text) and "product" in text and "revenue" in text:
        count = int(re.search(r"top\s+(\d+)", text).group(1))
        plan = _plan(
            f"Find the top {count} products by total revenue.",
            ["product", "revenue"],
            ["Group rows by product.", "Sum revenue for each product.", f"Sort by revenue and keep the top {count} products."],
            f"result = df.groupby('product')['revenue'].sum().nlargest({count}).reset_index()",
            "bar",
            "product",
            "revenue",
        )
    elif has("revenue") and ("total revenue" in text or "sum of revenue" in text):
        plan = _plan(
            "Calculate total revenue across all orders.",
            ["revenue"],
            ["Sum the revenue column.", "Store the total in result."],
            "result = pd.DataFrame({'total_revenue': [df['revenue'].sum()]})",
        )
    elif has("region", "order_id") and ("orders" in text or "order") and any(region in text for region in ("cairo", "alexandria", "giza")):
        region = next(region.title() for region in ("cairo", "alexandria", "giza") if region in text)
        plan = _plan(
            f"Count orders placed in {region}.",
            ["region", "order_id"],
            [f"Filter rows where region is {region}.", "Count unique order IDs."],
            f"result = pd.DataFrame({{'order_count': [df[df['region'] == '{region}']['order_id'].nunique()]}})",
        )
    elif has("discount") and "average" in text:
        plan = _plan(
            "Calculate the average discount across all orders.",
            ["discount"],
            ["Select the discount column.", "Calculate its mean."],
            "result = pd.DataFrame({'average_discount': [df['discount'].mean()]})",
        )
    elif has("category", "quantity") and "quantity" in text and ("category" in text or "per category" in text):
        plan = _plan(
            "Calculate total quantity sold per category.",
            ["category", "quantity"],
            ["Group rows by category.", "Sum quantity for each category."],
            "result = df.groupby('category')['quantity'].sum().reset_index()",
            "bar",
            "category",
            "quantity",
        )
    elif has("product", "quantity") and ("most" in text or "highest" in text) and ("unit" in text or "quantity" in text):
        plan = _plan(
            "Find the product with the highest total quantity sold.",
            ["product", "quantity"],
            ["Group rows by product.", "Sum quantity and keep the highest result."],
            "result = df.groupby('product')['quantity'].sum().nlargest(1).reset_index()",
            "bar",
            "product",
            "quantity",
        )
    else:
        raise ValueError(
            "The Gemini API is unavailable because its quota is exhausted, and this question is not supported by the local fallback. "
            "Try a revenue, product, category, quantity, discount, or regional order question."
        )

    entries = load_entries()
    record = {
        "model": "local-fallback",
        "tier": "local",
        "reason": "Gemini unavailable; deterministic sales-schema fallback",
        "fell_back": True,
        "input_tokens": 0,
        "output_tokens": 0,
        "latency": 0,
        "cost": 0.0,
        "attempts": 1,
        "citations": [citation(entry) for entry in entries if any(column in entry["text"] for column in plan.columns)],
    }
    return plan, record
