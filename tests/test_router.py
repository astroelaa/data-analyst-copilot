from src.config import GROQ_STRONG_MODEL
from src.llm.router import route


def test_complex_english_question_uses_strong_model():
    decision = route("Compare total revenue by region")
    assert decision.tier == "strong"
    assert "compare" in decision.reason
    assert decision.model_name == GROQ_STRONG_MODEL
