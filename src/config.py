import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
except ImportError:
    st = None


def setting(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if st is not None:
        try:
            return st.secrets.get(name, default)
        except st.errors.StreamlitSecretNotFoundError:
            return default
    return default


GEMINI_API_KEY = setting("GEMINI_API_KEY")
CHEAP_MODEL = setting("CHEAP_MODEL")
STRONG_MODEL = setting("STRONG_MODEL")
EMBED_MODEL = setting("EMBED_MODEL", "gemini-embedding-001")
OLLAMA_BASE_URL = setting("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = setting("OLLAMA_MODEL", "llama3.2:3b")
PRICES = json.loads((Path(__file__).resolve().parent.parent / "prices.json").read_text())
