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
GROQ_API_KEY = setting("GROQ_API_KEY")
GROQ_CHEAP_MODEL = setting("GROQ_CHEAP_MODEL")
GROQ_STRONG_MODEL = setting("GROQ_STRONG_MODEL")
EMBED_MODEL = setting("EMBED_MODEL", "gemini-embedding-001")
PRICES = json.loads((Path(__file__).resolve().parent.parent / "prices.json").read_text())
