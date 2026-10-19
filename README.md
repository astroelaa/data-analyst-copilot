# Data Analyst Copilot

Data Analyst Copilot is a Streamlit application that turns questions about a sales CSV into validated pandas analysis plans, executes the plans safely, and displays tabular results, charts, citations, and tool traces.

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
```

## Run

```powershell
.\.venv\Scripts\streamlit run app.py
```

Open `http://localhost:8501`, upload a compatible CSV if needed, and ask a question in English or Arabic.

## Tests

```powershell
.\.venv\Scripts\python -m pytest tests -v
```

The test suite has 15 passing unit tests.

## Architecture

- `v1-llm`: two-model Gemini client, routing, retries, and cost records.
- `v2-prompting`: Pydantic analysis plans, structured prompts, and validation retries.
- `v3-rag`: Chroma retrieval over the data dictionary with citations.
- `v4-agent`: pandas execution tools, charts, traces, session state, and Streamlit UI.

## Evaluation

The evaluation contains 15 reference-answer questions. In the completed run, all 8 questions that reached the model returned correct results, including 8/8 English questions. The remaining questions were blocked by Gemini free-tier quota exhaustion, with one earlier request also failing with a 504 timeout. Arabic questions could not be evaluated in that run. An Arabic routing fix was added afterward in commit `5102926`.

## Limitations

- Gemini free-tier quota is limited to 20 requests per day per model and can prevent a full evaluation.
- The sales data is synthetic.
- `prices.json` contains configured standard Flash price estimates, but actual billing and account-specific pricing are not validated.
