from types import SimpleNamespace

from src.llm import client


def test_generate_groq_sends_json_mode_for_structured_requests(monkeypatch):
    captured = {}

    class Completions:
        def create(self, **request):
            captured.update(request)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))],
                usage=SimpleNamespace(prompt_tokens=4, completion_tokens=3),
            )

    monkeypatch.setattr(
        client,
        "groq_client",
        SimpleNamespace(chat=SimpleNamespace(completions=Completions())),
    )
    result = client.generate_groq("test-model", "return JSON", dict)

    assert captured["model"] == "test-model"
    assert captured["response_format"] == {"type": "json_object"}
    assert result["input_tokens"] == 4
    assert result["output_tokens"] == 3


def test_generate_groq_requires_configuration(monkeypatch):
    monkeypatch.setattr(client, "groq_client", None)
    try:
        client.generate_groq("test-model", "hello")
    except RuntimeError as error:
        assert "GROQ_API_KEY" in str(error)
    else:
        raise AssertionError("missing Groq configuration was not rejected")
