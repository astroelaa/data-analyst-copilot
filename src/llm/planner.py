from copy import deepcopy

from pydantic import ValidationError

from src.llm.router import ask
from src.llm.local_fallback import make_local_plan
from src.prompts import build_fix_prompt, build_plan_prompt
from src.rag.store import citation, known_columns, load_entries, retrieve
from src.schemas import AnalysisPlan, CodeFix

MAX_ATTEMPTS = 2
PLAN_CACHE: dict[tuple[str, tuple[str, ...], str], tuple[AnalysisPlan, dict]] = {}


def make_plan(
    question: str,
    available_columns: list[str] | None = None,
    data_context: str | None = None,
) -> tuple[AnalysisPlan, dict]:
    valid = available_columns if available_columns is not None else known_columns()
    key = (question.strip().lower(), tuple(valid), data_context or "")
    if key in PLAN_CACHE:
        plan, record = PLAN_CACHE[key]
        return deepcopy(plan), deepcopy(record)
    try:
        if data_context is None:
            chunks = retrieve(question)
        else:
            chunks = [
                {
                    "column": "uploaded_dataframe",
                    "text": data_context,
                    "line": 0,
                    "source": "uploaded dataframe",
                }
            ]
    except Exception:
        chunks = load_entries()
    context = "\n".join(chunk["text"] for chunk in chunks)
    prompt = build_plan_prompt(question, context)
    feedback = ""
    try:
        result = _make_remote_plan(question, prompt, valid, chunks)
        PLAN_CACHE[key] = result
        return deepcopy(result[0]), deepcopy(result[1])
    except Exception as error:
        try:
            result = make_local_plan(question, valid)
            PLAN_CACHE[key] = result
            return deepcopy(result[0]), deepcopy(result[1])
        except ValueError as fallback_error:
            raise ValueError(
                "Hosted LLM providers are temporarily unavailable. "
                f"The local fallback could not answer this question: {fallback_error}"
            ) from error


def _make_remote_plan(question: str, prompt: str, valid: list[str], chunks: list[dict]) -> tuple[AnalysisPlan, dict]:
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
