import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHEAP_MODEL = os.getenv("CHEAP_MODEL")
STRONG_MODEL = os.getenv("STRONG_MODEL")
PRICES = json.loads((Path(__file__).resolve().parent.parent / "prices.json").read_text())
