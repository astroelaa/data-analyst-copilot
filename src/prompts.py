def build_plan_prompt(question: str, context: str) -> str:
    return f"""You are a data analyst planning a pandas analysis.
The dataframe is named df and was loaded from sales.csv.
Use only columns that appear in the data dictionary entries below. Never invent columns.
pandas_code must use only pandas and df, must not import anything or read files, and must assign the final table to a variable named result.
The question may be in Arabic or English. Write goal and steps in the language of the question. Keep code and column names in English.
Set chart_type to none if a chart does not help. x and y must be columns of result.

Data dictionary entries:
{context}

Question: {question}"""
