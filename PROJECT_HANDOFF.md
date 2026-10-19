# Project handoff

## Status

- v1 LLM layer done
- v2 Pydantic-validated planning done
- v3 Chroma RAG with citations done
- v4 agent tools, trace, session state, and Streamlit UI done
- English-only question handling is now used throughout the project
- The evaluation contains 11 English questions
- README updates and push remain

## Pricing

`prices.json` uses the current standard Gemini Flash pricing:

- Input: $0.75 per 1M tokens
- Output: $3.75 per 1M tokens

## Evaluation

The evaluation runner uses a three-second pause between questions and records quota or timeout failures without fabricating results.
