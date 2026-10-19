from pydantic import ValidationError

from src.llm.router import ask
from src.prompts import build_plan_prompt
from src.schemas import AnalysisPlan

MAX_ATTEMPTS = 2


def make_plan(question: str, dictionary: str) -> tuple[AnalysisPlan, dict]:
    prompt = build_plan_prompt(question, dictionary)
    feedback = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        text, record = ask(question, prompt + feedback, AnalysisPlan)
        try:
            plan = AnalysisPlan.model_validate_json(text)
        except ValidationError as error:
            feedback = f"\n\nYour previous output was invalid: {error}\nReturn valid JSON only."
            continue
        record["attempts"] = attempt
        return plan, record
    raise ValueError("plan failed validation after retries")
