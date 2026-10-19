def build_plan_prompt(question: str, context: str) -> str:
    return f"""You are a data analyst planning a pandas analysis.
The dataframe is named df and was loaded from sales.csv.
Use only columns that appear in the data dictionary entries below. Never invent columns.
pandas_code must use only pandas and df, must not import anything or read files, and must assign the final table to a variable named result.
Write goal and steps in English. Keep code and column names in English.
Preserve the requested metric, grouping, filter, and ranking.
Set chart_type to none if a chart does not help. x and y must be columns of result.

Data dictionary entries:
{context}

Question: {question}"""


def build_fix_prompt(question: str, code: str, error: str, columns: list[str]) -> str:
    return f"""This pandas code failed.
Question: {question}
Available columns: {columns}
Code:
{code}
Error: {error}
Return corrected pandas_code. Use only pandas and df, no imports, assign the final table to result."""
