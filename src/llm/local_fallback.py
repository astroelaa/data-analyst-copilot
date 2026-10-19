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

    if re.fullmatch(r"(hello|hi|hey|good morning|good afternoon|good evening)[!. ]*", text):
        plan = _plan(
            "Introduce the Data Analyst Copilot and explain its capabilities.",
            [],
            ["Explain that the assistant analyzes the uploaded CSV.", "Invite the user to ask an English data question."],
            "result = pd.DataFrame({'message': ['Hello! I am Data Analyst Copilot, your English-language data analyst. I can describe your CSV, create pandas analysis, calculate results, and draw charts. Ask about revenue, products, orders, categories, regions, or discounts.']})",
        )
    elif has("product", "revenue") and re.search(r"top\s+(\d+)", text) and "product" in text and "revenue" in text:
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
    elif has("order_date", "revenue") and "first quarter" in text:
        plan = _plan(
            "Calculate total revenue in the first quarter.",
            ["order_date", "revenue"],
            ["Filter order dates to January through March.", "Sum revenue for the filtered rows."],
            "result = pd.DataFrame({'total_revenue': [df[df['order_date'].dt.month <= 3]['revenue'].sum()]})",
        )
    elif has("order_date", "revenue") and "highest" in text and "month" in text:
        plan = _plan(
            "Find the month with the highest total revenue.",
            ["order_date", "revenue"],
            ["Group revenue by calendar month.", "Find the highest monthly revenue."],
            "result = pd.DataFrame({'highest_monthly_revenue': [df.groupby(df['order_date'].dt.month)['revenue'].sum().max()]})",
        )
    elif has("region", "revenue") and "average revenue" in text and any(region in text for region in ("cairo", "alexandria", "giza")):
        region = next(region.title() for region in ("cairo", "alexandria", "giza") if region in text)
        plan = _plan(
            f"Calculate average revenue per order in {region}.",
            ["region", "revenue"],
            [f"Filter rows where region is {region}.", "Calculate the mean revenue."],
            f"result = pd.DataFrame({{'average_revenue': [df[df['region'] == '{region}']['revenue'].mean()]}})",
        )
    elif has("region", "revenue") and "average revenue" in text:
        plan = _plan(
            "Calculate average revenue by region.",
            ["region", "revenue"],
            ["Group rows by region.", "Calculate the average revenue for each region."],
            "result = df.groupby('region')['revenue'].mean().sort_values(ascending=False).reset_index()",
            "bar",
            "region",
            "revenue",
        )
    elif has("region", "revenue") and "revenue" in text and "region" in text:
        plan = _plan(
            "Calculate total revenue by region.",
            ["region", "revenue"],
            ["Group rows by region.", "Sum revenue for each region.", "Sort the regions by revenue."],
            "result = df.groupby('region')['revenue'].sum().sort_values(ascending=False).reset_index()",
            "bar",
            "region",
            "revenue",
        )
    elif has("order_date", "revenue") and "revenue" in text and ("month" in text or "monthly" in text):
        plan = _plan(
            "Calculate total revenue by month.",
            ["order_date", "revenue"],
            ["Group rows by the month in order_date.", "Sum revenue for each month.", "Sort the months chronologically."],
            "result = df.groupby(df['order_date'].dt.month)['revenue'].sum().reset_index()",
            "line",
            "order_date",
            "revenue",
        )
    elif has("category", "revenue") and "compare" in text and all(category in text for category in ("electronics", "furniture")):
        plan = _plan(
            "Compare total revenue for Electronics and Furniture.",
            ["category", "revenue"],
            ["Filter the Electronics and Furniture categories.", "Group by category.", "Sum revenue for each category."],
            "result = df[df['category'].isin(['Electronics', 'Furniture'])].groupby('category')['revenue'].sum().reset_index()",
            "bar",
            "category",
            "revenue",
        )
    elif has("discount", "order_id") and "discount" in text and re.search(r"\b20\s*percent\b|\b20%\b", text):
        plan = _plan(
            "Count orders with a 20 percent discount.",
            ["discount", "order_id"],
            ["Filter rows with a 20 percent discount.", "Count the matching orders."],
            "result = pd.DataFrame({'order_count': [int((df['discount'] == 0.2).sum())]})",
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
    elif has("category", "order_id") and "order" in text and "category" in text:
        plan = _plan(
            "Count unique orders per category.",
            ["category", "order_id"],
            ["Group rows by category.", "Count unique order IDs for each category."],
            "result = df.groupby('category')['order_id'].nunique().reset_index(name='order_count')",
            "bar",
            "category",
            "order_count",
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
        "reason": "Hosted providers unavailable; deterministic sales-schema fallback",
        "fell_back": True,
        "input_tokens": 0,
        "output_tokens": 0,
        "latency": 0,
        "cost": 0.0,
        "attempts": 1,
        "citations": [citation(entry) for entry in entries if any(column in entry["text"] for column in plan.columns)],
    }
    return plan, record
