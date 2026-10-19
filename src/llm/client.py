import time

from google import genai
from google.genai import errors

from src.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
RETRYABLE = (429, 503)


def generate(model_name: str, prompt: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        start = time.time()
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
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
