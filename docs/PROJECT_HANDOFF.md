# Project handoff

## Current status

- The English-only Streamlit agent is implemented and deployed from `master`.
- The planner uses a layered flow: local generic handlers first, Groq as the primary hosted planner, Gemini as the provider fallback, and restricted pandas tools for execution.
- Uploaded CSVs are profiled dynamically with columns, types, null counts, cardinalities, sample values, and numeric statistics.
- The planner receives the current uploaded dataframe profile, so hosted analysis can work with new CSV schemas and new column names.
- Pydantic validates every analysis plan before restricted pandas execution.
- The agent tools are `describe_data`, `profile_data`, `run_pandas`, and `plot_chart`.
- The hosted agent receives an explicit analyst role, goal, tool contract, plan→execute→verify workflow, and no-fabrication rules.
- Plans include structured intent fields, results receive a conservative verification pass, and recent session context supports follow-up questions.
- Chat sessions, result tables, charts, generated code, citations, and tool traces are supported in the Streamlit UI.
- Chat records are persisted in SQLite at the configurable `DATABASE_PATH` and reloaded by dataset source.
- Unsupported analysis requests and unexpected failures use separate neutral user-facing messages without provider internals.
- The latest source and documentation changes are pushed to the `master` branch.

## Repository layout

```text
app.py                 Streamlit entrypoint
main.py                CLI entrypoint
src/                   Agent, LLM, RAG, schemas, and prompts
data/                  Default sales CSV and data dictionary
evaluation/            Questions, results, and evaluation runner
tests/                 Not tracked; historical validation tests remain outside the deployed repository
scripts/               Dataset generation and model-list utilities
README.md              Setup, architecture, deployment, persistence, and evaluation docs
docs/PROJECT_HANDOFF.md Current implementation handoff
```

Root entrypoints and configuration files intentionally remain at the repository root because Streamlit Cloud expects `app.py` there and the Python commands reference the root package layout.

## Deployment

For Streamlit Community Cloud:

1. Use branch `master`.
2. Use `app.py` as the main file.
3. Add Groq and Gemini keys and model names under App settings > Secrets.
4. Save the secrets and reboot the app.

Never commit `.env` or API keys. `.env` is ignored by Git; `.env.example` contains placeholders only.

The default SQLite database is `data/analyst.db`, which is ignored by Git. It provides persistence for a single-user or demonstration deployment. Streamlit Cloud filesystem persistence is not guaranteed across container replacement, and there is no authentication yet. Use authenticated Supabase/PostgreSQL storage before treating this as multi-user production software.

## Pricing

`prices.json` contains the configured Gemini Flash estimates:

- Input: $0.75 per 1M tokens
- Output: $3.75 per 1M tokens

Unknown Groq models currently use zero configured cost until their prices are added to `prices.json`.

## Validation

The current repository does not include the historical 35-test suite. The active validation uses compilation, direct smoke tests, Streamlit startup checks, and the 11-question evaluation. The latest evaluation reached 11/11 correct with 100% first-try and final code success, averaging 0.06 seconds per question.

Run the evaluation from the repository root:

```powershell
.\.venv\Scripts\python -m evaluation.run_eval
```

The benchmark contains 11 English questions. The latest recorded run reached 11/11 correct, but the questions are a small benchmark and do not prove universal accuracy. The results identify which provider handled each question.

## Known limitations

- Arbitrary questions on new datasets require a working Groq or Gemini API key.
- The offline deterministic layer is intentionally limited; general open-ended analysis requires a hosted provider.
- The sales data is synthetic.
- Evaluation results should be regenerated after provider, prompt, planner, or fallback changes.
