from src.llm.router import route


def test_arabic_revenue_question_uses_strong_model():
    decision = route("ما هي المنطقة الأعلى في الإيرادات؟")
    assert decision.tier == "strong"
    assert "إيرادات" in decision.reason
