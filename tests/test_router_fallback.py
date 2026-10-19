from src.llm import router


def test_ask_uses_groq_without_fallback(monkeypatch):
    calls = []

    def fake_groq(model, prompt, schema):
        calls.append(("groq", model, prompt, schema))
        return {"text": "groq answer", "input_tokens": 10, "output_tokens": 5, "latency": 0.1}

    monkeypatch.setattr(router, "generate_groq", fake_groq)
    text, record = router.ask("What is the total revenue?")

    assert text == "groq answer"
    assert calls[0][0] == "groq"
    assert record["fell_back"] is False
    assert record["input_tokens"] == 10


def test_ask_falls_back_to_gemini(monkeypatch):
    calls = []

    def failed_groq(model, prompt, schema):
        calls.append("groq")
        raise RuntimeError("Groq unavailable")

    def fake_gemini(model, prompt, schema):
        calls.append("gemini")
        return {"text": "gemini answer", "input_tokens": 20, "output_tokens": 8, "latency": 0.2}

    monkeypatch.setattr(router, "generate_groq", failed_groq)
    monkeypatch.setattr(router, "generate", fake_gemini)
    text, record = router.ask("What is the total revenue?")

    assert text == "gemini answer"
    assert calls == ["groq", "gemini"]
    assert record["fell_back"] is True
    assert record["model"] == router.CHEAP_MODEL


def test_estimate_cost_uses_zero_for_unknown_model():
    assert router.estimate_cost("unknown", 100, 100) == 0.0
