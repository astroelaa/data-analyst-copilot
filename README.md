# Data Analyst Copilot

Data Analyst Copilot is a Streamlit application that turns English questions about any uploaded CSV into validated pandas analysis plans, executes the plans safely, and displays tables, charts, citations, and tool traces. It profiles each uploaded dataframe so the hosted agent can work with new schemas and general analysis questions. It uses local deterministic handling for basic questions, Groq as the hosted planning provider, Gemini as a provider fallback, and restricted pandas tools for execution.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Create `.env` in the repository root:

```env
GEMINI_API_KEY=your_api_key
CHEAP_MODEL=gemini-3.7-flash
STRONG_MODEL=gemini-3.8-flash
GROQ_API_KEY=your_groq_api_key
GROQ_CHEAP_MODEL=openai/gpt-oss-20b
GROQ_STRONG_MODEL=openai/gpt-oss-120b
```

## Run

```powershell
.\.venv\Scripts\streamlit run app.py
```

Open `http://localhost:8501`, upload a CSV, and ask an English question about its contents.

## How to use

1. Start the Streamlit app with the command above.
2. Keep the included `data/sales.csv`, or upload another CSV from the sidebar.
3. Type a normal English question in the chat box.
4. Watch the status message while the agent profiles the uploaded data, creates a plan, and runs the pandas code.
5. Review the goal, steps, generated code, result table, and chart.
6. Expand **What the agent did** to inspect the tool trace and **Analysis details** to see token usage, cost estimate, and citations.

Example questions:

```text
What are the top 5 products by revenue?
What is the total revenue?
How many orders were placed in Cairo?
What is the average discount across all orders?
Show revenue by region
Show monthly revenue
What is the average revenue by region?
How many orders per category?
Which product sold the most units?
```

The agent profiles every uploaded CSV and sends its actual columns, types, sample values, cardinalities, and numeric ranges to the planner. New or complex questions are sent to Groq first, then Gemini if Groq fails. The local fallback handles basic schema questions and common sales examples without using a hosted API. If both providers are unavailable and the fallback cannot recognize the question, the app displays a clear limitation instead of inventing an answer.

For Streamlit Community Cloud, add these values under App settings > Secrets:

```toml
GEMINI_API_KEY = "your_api_key"
CHEAP_MODEL = "gemini-3.7-flash"
STRONG_MODEL = "gemini-3.8-flash"
GROQ_API_KEY = "your_groq_api_key"
GROQ_CHEAP_MODEL = "openai/gpt-oss-20b"
GROQ_STRONG_MODEL = "openai/gpt-oss-120b"
EMBED_MODEL = "gemini-embedding-001"
```

## Architecture

```mermaid
flowchart LR
    U[User question and any CSV] --> UI[Streamlit UI]
    UI --> A[Agent]
    A --> D[Profile uploaded dataframe]
    A --> P[Planner]
    P --> L[Local generic basics]
    P --> R[Rule-based router]
    R --> C[Cheap Groq model]
    R --> S[Strong Groq model]
    C --> V[Pydantic validation]
    S --> V
    C -. provider failure .-> G[Gemini fallback models]
    S -. provider failure .-> G
    P --> D1[Uploaded schema context]
    D1 --> E[Columns, types, samples, stats]
    A --> T[Agent tools]
    T --> DP[describe_data]
    T --> RP[run_pandas]
    T --> PC[plot_chart]
    T --> Q[Result verification]
    Q -->|invalid| X[One repair attempt]
    L --> T
    T --> O[Result, trace, citations, session history]
```

### Request flow

1. Streamlit creates a session for the uploaded dataset.
2. The agent profiles the data with `describe_data` and builds uploaded-schema context.
3. The planner checks local generic handlers first for basic schema questions.
4. Unsupported questions go to the router, which selects the cheap or strong Groq model.
5. If Groq fails, the router retries with the corresponding Gemini model.
6. The planner returns a structured `AnalysisPlan` with explicit intent fields, validated by Pydantic.
7. `run_pandas` executes only validated code against a copy of the dataframe.
8. The verifier checks the result shape and requested comparisons, allowing one bounded repair attempt.
9. `plot_chart` creates a chart when the plan requests one.
10. The UI displays the answer, code, result, chart, citations, and tool trace without provider internals.

The hosted planner is data-agnostic within the uploaded CSV: it can use new column names and new analysis questions because the current dataframe profile is included in the planning context. Its role, goal, tools, and plan→execute→verify workflow are defined in the system instructions. The optional RAG dictionary is not required for uploaded-data planning.

The local layer is intentionally conservative. It handles basic schema questions and selected examples without an API, while hosted models provide general open-ended analysis. Unsupported questions produce an explicit limitation instead of a fabricated answer.

## Branch architecture

- `v1-llm`: two-model Gemini client, routing, retries, and cost records.
- `v2-prompting`: Pydantic analysis plans, structured prompts, and validation retries.
- `v3-rag`: Chroma retrieval over the data dictionary with citations.
- `v4-agent`: pandas execution tools, charts, traces, session state, and Streamlit UI.

## Technical decisions

- Use two Groq models with rule-based routing so simple questions use the cheaper tier and complex questions use the stronger tier, with Gemini as a provider fallback.
- Use Pydantic validation for structured analysis plans before executing generated pandas code.
- Verify result shape and requested comparisons after execution, with one bounded repair attempt.
- Preserve recent questions and result columns as context for follow-up questions.
- Define the analyst role, goal, tools, workflow, and failure behavior explicitly instead of relying on a framework-specific persona.
- Profile every uploaded dataframe and provide its live schema, samples, and numeric statistics to the planner.
- Keep Chroma and embeddings optional; uploaded-data profiling is the primary planning context and does not require a startup embedding call.
- Execute generated code only through restricted pandas tools that block imports, file access, and other unsafe operations.
- Keep the evaluation honest by recording quota and timeout failures instead of treating them as correct answers.
- Use a small deterministic local layer for basic schema questions and selected examples; unsupported open-ended questions remain explicit failures without hosted providers.

## Validation

The historical 35-test suite is not included in the deployed repository. Current validation uses Python compilation, direct agent smoke tests, custom uploaded-data checks, Streamlit startup checks, and the evaluation below.

## Evaluation

The evaluation contains 11 English reference-answer questions. The latest clean run completed all 11 questions using the configured provider chain and deterministic fallback support.

| Metric | Latest recorded result |
| --- | ---: |
| Questions | 11 |
| Correct answers | 11/11 |
| Overall correctness | 100.0% |
| First-try code success | 100.0% |
| Code success after auto-fix | 100.0% |
| Average time per question | 0.05 seconds |

Run it from the repository root with:

```powershell
.\.venv\Scripts\python -m evaluation.run_eval
```

The recorded rows identify the provider used for each question. The benchmark measures the included dataset and does not prove unlimited open-ended model capability.

## Limitations

- Gemini free-tier quota is limited to 20 requests per day per model and can prevent a full evaluation or live demo.
- Groq is the primary hosted provider for deployment availability, while Gemini remains configured as a second provider and fallback. The local fallback does not replace the hosted LLM layer.
- The local layer is not an unlimited language model. Open-ended questions on arbitrary datasets need a configured hosted provider. Production deployments should add rate limiting, caching, and a higher-quota or secondary model provider for many users.
- The sales data is synthetic.
- `prices.json` contains configured standard Flash price estimates, but actual billing and account-specific pricing are not validated.
