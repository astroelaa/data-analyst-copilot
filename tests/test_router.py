from src.llm.router import route


def test_complex_english_question_uses_strong_model():
    decision = route("Compare total revenue by region")
    assert decision.tier == "strong"
    assert "compare" in decision.reason
