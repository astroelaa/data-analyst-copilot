# Project handoff

## Current status

- The English-only Streamlit agent is implemented and deployed from `master`.
- Groq is the primary hosted planner, Gemini is the provider fallback, and the deterministic fallback handles recognized sales questions when both hosted providers are unavailable.
- Uploaded CSVs are profiled dynamically with columns, types, null counts, cardinalities, sample values, and numeric statistics.
- The planner receives the current uploaded dataframe profile, so hosted analysis can work with new CSV schemas and new column names.
- Pydantic validates every analysis plan before restricted pandas execution.
- The agent tools are `describe_data`, `run_pandas`, and `plot_chart`.
- Chat sessions, result tables, charts, generated code, citations, and tool traces are supported in the Streamlit UI.
- The latest source and documentation changes are pushed to the `master` branch.

## Repository layout

```text
app.py                 Streamlit entrypoint
main.py                CLI entrypoint
src/                   Agent, LLM, RAG, schemas, and prompts
data/                  Default sales CSV and data dictionary
evaluation/            Questions, results, and evaluation runner
tests/                 Automated tests
scripts/               Dataset generation and model-list utilities
README.md              Setup, architecture, deployment, and evaluation docs
PROJECT_HANDOFF.md     Current implementation handoff
```

Root entrypoints and configuration files intentionally remain at the repository root because Streamlit Cloud expects `app.py` there and the Python commands reference the root package layout.

## Deployment

For Streamlit Community Cloud:

1. Use branch `master`.
2. Use `app.py` as the main file.
3. Add Groq and Gemini keys and model names under App settings > Secrets.
4. Save the secrets and reboot the app.

Never commit `.env` or API keys. `.env` is ignored by Git; `.env.example` contains placeholders only.

## Pricing

`prices.json` contains the configured Gemini Flash estimates:

- Input: $0.75 per 1M tokens
- Output: $3.75 per 1M tokens

Unknown Groq models currently use zero configured cost until their prices are added to `prices.json`.

## Validation

Run the full test suite:

```powershell
.\.venv\Scripts\python -m pytest tests -q
```

The latest validation passed 35 tests, including provider fallback, agent retries, uploaded-data profiling, chart modes, and execution safety.

Run the evaluation from the repository root:

```powershell
.\.venv\Scripts\python -m evaluation.run_eval
```

The benchmark contains 11 English questions. The latest recorded run reached 11/11 correct, but the questions are a small benchmark and do not prove universal accuracy. The results identify which provider handled each question.

## Known limitations

- Arbitrary questions on new datasets require a working Groq or Gemini API key.
- The offline deterministic fallback is intentionally limited to recognized sales patterns.
- The sales data is synthetic.
- Evaluation results should be regenerated after provider, prompt, planner, or fallback changes.
