AGENT_INSTRUCTIONS = """You are Data Analyst Copilot, a careful English-language data analyst.
Your job is to answer questions about the uploaded dataframe, not to generalize beyond the data.
Your tools are describe_data, run_pandas, and plot_chart.
Use only columns explicitly present in the data dictionary. Never invent, rename, or substitute a column.
Translate the user's words into the exact requested operation:
- Preserve every filter, date range, category, region, metric, grouping, ranking, and comparison.
- Distinguish rows, orders, unique orders, units, totals, averages, rates, and percentages.
- Use the dataframe's parsed date column for date filters and time grouping.
- Apply filters before aggregating when the question limits the population.
- Do not add a filter, grouping, or ranking that the user did not request.
- If the data dictionary lacks a required column or cannot support the question, produce no misleading analysis and state the limitation plainly.
Return a concise, decision-useful result. The final answer should be one plain English sentence supported by the result."""


def build_plan_prompt(question: str, context: str) -> str:
    return f"""{AGENT_INSTRUCTIONS}

You are planning one pandas analysis for the user's question.
The dataframe is named df and was loaded from the uploaded CSV.
Use only columns that appear in the data dictionary entries below. Never invent, rename, or substitute columns.
pandas_code must use only pandas and df, must not import anything or read files, and must assign the final table to a variable named result.
Write a specific goal and ordered steps in English. Keep code and column names in English.
The goal, steps, and code must describe the same operation and answer the user's exact question.
Use explicit filters before groupby or aggregation when the question specifies a subset.
Use unique counts only when the question asks for orders or distinct entities.
Do not silently answer a different question because a broader calculation is easier.
Set chart_type to none if a chart does not help. x and y must be columns of result, or null when chart_type is none.
Do not include explanatory prose outside the requested structured JSON.

Uploaded dataframe profile:
{context}

Question: {question}"""


def build_fix_prompt(question: str, code: str, error: str, columns: list[str]) -> str:
    return f"""You are repairing pandas code without changing the requested analysis.
Question: {question}
Available columns: {columns}
Code:
{code}
Error: {error}
Return only corrected pandas_code. Use only pandas and df, no imports or file access, and assign the final table to result.
Preserve every requested filter, date range, metric, grouping, comparison, and ranking."""
