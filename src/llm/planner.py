from pydantic import ValidationError

from src.llm.router import ask
from src.prompts import build_fix_prompt, build_plan_prompt
from src.rag.store import citation, known_columns, load_entries, retrieve
from src.schemas import AnalysisPlan, CodeFix

MAX_ATTEMPTS = 2


def make_plan(question: str) -> tuple[AnalysisPlan, dict]:
    try:
        chunks = retrieve(question)
    except Exception:
        chunks = load_entries()
    context = "\n".join(chunk["text"] for chunk in chunks)
    prompt = build_plan_prompt(question, context)
    valid = known_columns()
    feedback = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        text, record = ask(question, prompt + feedback, AnalysisPlan)
        try:
            plan = AnalysisPlan.model_validate_json(text)
        except ValidationError as error:
            feedback = f"\n\nYour previous output was invalid: {error}\nReturn valid JSON only."
            continue
        unknown = [column for column in plan.columns if column not in valid]
        if unknown:
            feedback = f"\n\nYou used columns that do not exist: {unknown}. Use only the listed columns."
            continue
        record["attempts"] = attempt
        record["citations"] = [citation(chunk) for chunk in chunks]
        return plan, record
    raise ValueError("plan failed validation after retries")


def fix_code(question: str, code: str, error: str, columns: list[str]) -> tuple[str, dict]:
    text, record = ask(question, build_fix_prompt(question, code, error, columns), CodeFix)
    return CodeFix.model_validate_json(text).pandas_code, record
