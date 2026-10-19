from dataclasses import dataclass

from src.config import CHEAP_MODEL, PRICES, STRONG_MODEL
from src.llm.client import generate

COMPLEX_WORDS = (
    "group", "compare", "trend", "correlation", "percentage", "growth",
    "monthly", "per month", "ratio",
    "قارن", "مقارنة", "اتجاه", "ارتباط", "نسبة", "نمو", "شهري",
)
LONG_QUESTION_WORDS = 15


@dataclass
class RouteDecision:
    model_name: str
    tier: str
    reason: str


def route(question: str) -> RouteDecision:
    text = question.lower()
    hits = [word for word in COMPLEX_WORDS if word in text]
    is_long = len(text.split()) > LONG_QUESTION_WORDS
    if hits or is_long:
        return RouteDecision(STRONG_MODEL, "strong", f"words={hits} long={is_long}")
    return RouteDecision(CHEAP_MODEL, "cheap", "no complexity signals")


def estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    price = PRICES[model_name]
    return (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000


def ask(question: str, prompt: str | None = None, schema=None) -> tuple[str, dict]:
    decision = route(question)
    model = decision.model_name
    body = prompt or question
    fell_back = False
    try:
        result = generate(model, body, schema)
    except Exception:
        model = STRONG_MODEL if model == CHEAP_MODEL else CHEAP_MODEL
        fell_back = True
        result = generate(model, body, schema)
    record = {
        "model": model,
        "tier": decision.tier,
        "reason": decision.reason,
        "fell_back": fell_back,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "latency": result["latency"],
        "cost": estimate_cost(model, result["input_tokens"], result["output_tokens"]),
    }
    return result["text"], record
