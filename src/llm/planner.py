from pydantic import ValidationError

from src.llm.router import ask
from src.llm.client import generate_ollama
from src.llm.local_fallback import make_local_plan
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
    try:
        return _make_remote_plan(question, prompt, valid, chunks)
    except Exception as error:
        try:
            return _make_ollama_plan(question, prompt, valid, chunks)
        except Exception:
            pass
        try:
            return make_local_plan(question, valid)
        except ValueError as fallback_error:
            raise ValueError(
                "Gemini is unavailable and Ollama is not running. "
                f"The local fallback could not answer this question: {fallback_error}"
            ) from error


def _make_ollama_plan(question: str, prompt: str, valid: list[str], chunks: list[dict]) -> tuple[AnalysisPlan, dict]:
    result = generate_ollama(question + "\n\n" + prompt, AnalysisPlan)
    text = result["text"]
    plan = AnalysisPlan.model_validate_json(text)
    unknown = [column for column in plan.columns if column not in valid]
    if unknown:
        raise ValueError(f"Ollama used unknown columns: {unknown}")
    record = result
    record.update(
        {
            "model": "ollama-local",
            "tier": "local-llm",
            "reason": "Gemini unavailable; Ollama local fallback",
            "fell_back": True,
            "cost": 0.0,
            "attempts": 1,
            "citations": [citation(chunk) for chunk in chunks],
        }
    )
    return plan, record


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
