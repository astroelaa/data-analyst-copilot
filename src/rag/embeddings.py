from google.genai import types

from src.config import EMBED_MODEL
from src.llm.client import client


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [item.values for item in response.embeddings]
