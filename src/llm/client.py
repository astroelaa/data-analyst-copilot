import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from google import genai
from google.genai import errors, types

from src.config import GEMINI_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)
RETRYABLE = (429, 503)


def generate(model_name: str, prompt: str, response_schema=None, retries: int = 3) -> dict:
    config = None
    if response_schema is not None:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
        )
    for attempt in range(retries):
        start = time.time()
        try:
            response = client.models.generate_content(
                model=model_name, contents=prompt, config=config
            )
        except errors.APIError as error:
            if error.code in RETRYABLE and attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
        usage = response.usage_metadata
        return {
            "text": response.text,
            "input_tokens": usage.prompt_token_count or 0,
            "output_tokens": usage.candidates_token_count or 0,
            "latency": round(time.time() - start, 2),
        }


def generate_ollama(prompt: str, response_schema=None) -> dict:
    if response_schema is not None:
        prompt += "\nReturn JSON matching this schema:\n" + json.dumps(response_schema.model_json_schema())
    payload_data = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if response_schema is not None:
        payload_data["format"] = "json"
    payload = json.dumps(payload_data).encode()
    request = Request(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    try:
        with urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode())
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Ollama is unavailable at {OLLAMA_BASE_URL}. Start Ollama and pull {OLLAMA_MODEL}."
        ) from error
    return {
        "text": body["message"]["content"],
        "input_tokens": body.get("prompt_eval_count", 0) or 0,
        "output_tokens": body.get("eval_count", 0) or 0,
        "latency": round(time.time() - start, 2),
    }
