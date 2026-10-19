# Data Analyst Copilot

Data Analyst Copilot is a Streamlit application that turns English questions about a sales CSV into validated pandas analysis plans, executes the plans safely, and displays tables, charts, citations, and tool traces. It uses Gemini for flexible planning and a deterministic local fallback for common sales questions when the API quota is unavailable.

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
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

## Run

```powershell
.\.venv\Scripts\streamlit run app.py
```

Open `http://localhost:8501`, upload a compatible CSV if needed, and ask an English question.

## How to use

1. Start the Streamlit app with the command above.
2. Keep the included `data/sales.csv`, or upload another CSV from the sidebar.
3. Type a normal English question in the chat box.
4. Watch the status message while the agent describes the data, creates a plan, and runs the pandas code.
5. Review the goal, steps, generated code, result table, and chart.
6. Expand **What the agent did** to inspect the tool trace and **Analysis details** to see the model, tier, token usage, cost estimate, and citations.

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

The local fallback handles the common sales patterns listed above without using the Gemini API. New or more complex questions are sent to Gemini when quota is available. If Gemini is unavailable and the fallback cannot recognize the question, the app displays a clear limitation instead of inventing an answer.

### Optional Ollama fallback

To answer open-ended questions locally when Gemini quota is exhausted, install [Ollama](https://ollama.com), start it, and pull a model:

```powershell
ollama pull llama3.2:3b
```

Keep Ollama running at `http://localhost:11434`. The planner tries Gemini first, then Ollama, then the deterministic fallback. Ollama is local to the machine running the app; it is not available inside Streamlit Community Cloud unless you provide a separately hosted Ollama endpoint and set `OLLAMA_BASE_URL` to that endpoint.

For Streamlit Community Cloud, add these values under App settings > Secrets:

```toml
GEMINI_API_KEY = "your_api_key"
CHEAP_MODEL = "gemini-3.7-flash"
STRONG_MODEL = "gemini-3.8-flash"
EMBED_MODEL = "gemini-embedding-001"
```

## Architecture

```mermaid
flowchart LR
    U[User question and CSV] --> UI[Streamlit UI]
    UI --> A[Agent]
    A --> D[Describe data]
    A --> P[Planner]
    P --> R[Rule-based router]
    R --> C[Cheap Gemini Flash]
    R --> S[Strong Gemini Flash]
    C --> V[Pydantic validation]
    S --> V
    P --> D1[RAG data dictionary]
    D1 --> E[Gemini embeddings]
    D1 --> Ch[Chroma vector store]
    P --> F{Gemini available?}
    F -->|No or quota exhausted| L[Local deterministic fallback]
    F -->|Yes| V
    A --> T[Agent tools]
    T --> DP[describe_data]
    T --> RP[run_pandas]
    T --> PC[plot_chart]
    V --> T
    L --> T
    T --> O[Result, trace, citations, session history]
```

### Request flow

1. Streamlit creates a session for the uploaded dataset.
2. The agent profiles the data with `describe_data`.
3. RAG retrieves relevant data-dictionary entries and citations when semantic search is available.
4. The router sends the question to the cheap or strong Gemini model based on complexity.
5. The planner returns a structured `AnalysisPlan`, validated by Pydantic.
6. If Gemini is unavailable, the local fallback creates a plan for supported sales patterns.
7. `run_pandas` executes only validated code against a copy of the dataframe.
8. `plot_chart` creates a chart when the plan requests one.
9. The UI displays the answer, code, result, chart, citations, and tool trace.

The fallback is intentionally conservative. It computes only recognized operations and does not pretend to answer unsupported questions.

## Branch architecture

- `v1-llm`: two-model Gemini client, routing, retries, and cost records.
- `v2-prompting`: Pydantic analysis plans, structured prompts, and validation retries.
- `v3-rag`: Chroma retrieval over the data dictionary with citations.
- `v4-agent`: pandas execution tools, charts, traces, session state, and Streamlit UI.

## Technical decisions

- Use two Gemini Flash models with rule-based routing so simple questions use the cheaper tier and complex questions use the stronger tier.
- Use Pydantic validation for structured analysis plans before executing generated pandas code.
- Use Chroma and Gemini embeddings for data-dictionary retrieval, with citations and a local dictionary fallback when embeddings are unavailable.
- Execute generated code only through restricted pandas tools that block imports, file access, and other unsafe operations.
- Keep the evaluation honest by recording quota and timeout failures instead of treating them as correct answers.
- Use a deterministic local fallback for common sales questions when Gemini quota is exhausted; unsupported questions remain explicit failures.

## Tests

```powershell
.\.venv\Scripts\python -m pytest tests -v
```

The test suite has 19 passing unit tests.

## Evaluation

The evaluation contains 11 English reference-answer questions. The recorded run reached 8 questions before Gemini free-tier quota exhaustion and all 8 reached questions were correct. One earlier request also failed with a 504 timeout.

| Metric | Recorded result |
| --- | ---: |
| Questions | 11 |
| Questions reaching the model | 8 |
| Correct answers among questions reaching the model | 8/8 |
| Overall recorded correctness | 72.7% |
| First-try code success | 53.3% |
| Code success after auto-fix | 53.3% |

## Limitations

- Gemini free-tier quota is limited to 20 requests per day per model and can prevent a full evaluation or live demo.
- Gemini remains the primary LLM because the project brief requires an LLM layer with two models. The local fallback does not replace that requirement.
- The fallback is designed for common sales analysis, not unlimited natural-language understanding. Production deployments should add rate limiting, caching, and a higher-quota or secondary model provider for many users.
- Ollama is optional and intended for local open-ended questions. Streamlit Community Cloud cannot access an Ollama server running on your personal computer.
- The sales data is synthetic.
- `prices.json` contains configured standard Flash price estimates, but actual billing and account-specific pricing are not validated.
