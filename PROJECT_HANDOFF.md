# Project handoff

## Status

- v1 LLM layer done
- v2 Pydantic-validated planning done
- v3 Chroma RAG with citations done
- v4 agent tools, trace, session state, and Streamlit UI done
- English-only question handling is now used throughout the project
- Targeted evaluation rerun is in progress for `q01,q10,q11,q12,q13,q14,q15`
- README and push remain

## Pricing

`prices.json` uses the current standard Gemini Flash pricing:

- Input: $0.75 per 1M tokens
- Output: $3.75 per 1M tokens

## Evaluation

The evaluation runner includes 5-second pauses between questions and exponential backoff for 429 and 504 errors.
