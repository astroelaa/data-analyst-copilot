import time

from google import genai
from google.genai import errors, types
from openai import OpenAI

from src.config import GEMINI_API_KEY, GROQ_API_KEY

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)
groq_client = (
    OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    if GROQ_API_KEY
    else None
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


def generate_groq(model_name: str, prompt: str, response_schema=None) -> dict:
    if groq_client is None:
        raise RuntimeError("GROQ_API_KEY is not configured")
    start = time.time()
    request = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
    }
    if response_schema is not None:
        request["response_format"] = {"type": "json_object"}
    response = groq_client.chat.completions.create(**request)
    usage = response.usage
    return {
        "text": response.choices[0].message.content,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "latency": round(time.time() - start, 2),
    }
