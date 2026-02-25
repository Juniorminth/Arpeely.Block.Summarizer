# Arpeely Block Summarizer — Server

A FastAPI backend that receives web page content and returns a summarized version using a LangGraph-powered LLM agent.

> **Input:** the Chrome extension automatically truncates text to **6 000 chars** before sending. Raw `POST` callers should do the same to keep latency and token costs predictable.

---

## Architecture

```
POST /api/summarize/
        │
        ▼
summarize_controller.py       # HTTP layer — validates input, returns response
        │
        ▼
SummarizerService (ABC)       # Service layer — decouples HTTP from summarization logic
        │
        ▼
SummarizeWithAgent            # Concrete service — delegates to the agent
        │
        ▼
SummarizerAgent (ABC)         # Agent abstraction — swappable LLM providers
        │
        ▼
SummarizerAgentOpenAI         # OpenAI implementation — runs a LangGraph pipeline
        │
        ▼
LangGraph StateGraph          # sanitize (optional) → summarize
```

### Key Design Decisions

- **Separation of concerns** — the controller only knows about `SummarizerService`. It has no knowledge of LangGraph, OpenAI, or how summarization works internally.
- **Singleton service** — a `lifespan` context manager in `main.py` builds the agent and service exactly once at startup and stores them on `app.state`. The dependency in `infrastructure/dependencies.py` reads from `request.app.state`, ensuring every request reuses the same compiled LangGraph and LLM client.
- **Swappable providers** — adding a new LLM provider (e.g. Anthropic) only requires a new `SummarizerAgent` subclass and a one-line change in `_MODEL_REGISTRY`.
- **LangGraph pipeline** — the agent runs a two-step graph: an optional sanitization node (strips HTML/markup) followed by a summarization node. Routing is decided at runtime based on whether the input text contains non-standard characters, avoiding a redundant LLM call for clean text.
- **Output cap** — `ChatOpenAI` is initialised with `max_tokens=400` to prevent over-generation and reduce tail latency.
- **Request timeout** — `SummarizeWithAgent` wraps the agent call with `asyncio.wait_for` using a configurable timeout (default 30 s, set via `LLM_TIMEOUT_SECONDS`). If the LLM hangs, the request fails gracefully with a 502 instead of spinning indefinitely.
- **Unicode-aware sanitization** — the dirty-text regex uses `\w` (Python 3 Unicode-aware), so accented characters from any script (French, German, Spanish, etc.) are treated as clean text and skip the sanitization LLM call.
- **Structured logging** — uses Python's stdlib `logging` with a consistent `timestamp | level | module | message` format. Logs are emitted at key boundaries: startup config, request received/completed, sanitization routing decisions, timeouts, and errors. Configured once at startup via `infrastructure/logging_config.py` under the `arpeely.*` namespace to avoid polluting third-party loggers.

### Project Structure

```
server/app/
├── main.py                          # FastAPI app entry point
├── pyproject.toml                   # Dependencies and project config
├── .env.example                     # Environment variable template
├── api/
│   └── summarize_controller.py      # POST /api/summarize/ endpoint
├── infrastructure/
│   ├── config.py                    # Settings (reads from .env)
│   ├── dependencies.py              # DI wiring — reads service from app.state
│   └── logging_config.py            # Structured logging setup
├── services/
│   └── summarizer/
│       ├── summarizer_service.py    # SummarizerService ABC + SummarizeWithAgent
│       └── agent/
│           └── summarizer_agent.py  # LangGraph agent, factory, OpenAI implementation
└── tests/
    ├── conftest.py                  # Mock agents, fixtures, app.state injection
    ├── test_summarize_endpoint.py   # Integration tests for the HTTP layer
    └── test_sanitization.py         # Unit tests for the sanitization heuristic
```

---

## Setup

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- An OpenAI API key

### Install dependencies

```bash
cd server/app
uv sync --group dev
```

### Configure environment

Copy the example and add your key:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini          # optional, defaults to gpt-4o-mini
LLM_TIMEOUT_SECONDS=30            # optional, defaults to 30
```

---

## Running the Server

```bash
cd server/app
uv run python -m server.app.main
```

Or with uvicorn directly:

```bash
uv run uvicorn server.app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Docs

Once running, open:

| UI | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

### API Usage

```bash
curl -X POST http://localhost:8000/api/summarize/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Your web page content here..."}'
```

**Response:**
```json
{
  "summary": "A concise summary of the provided content."
}
```

**Error responses:**
| Status | Reason |
|---|---|
| `422` | Empty or whitespace-only text |
| `502` | LLM call failed or timed out |

---

## Running Tests

Tests use a `MockSummarizerAgent` that bypasses the LLM entirely — no OpenAI API key required.

```bash
cd server/app
uv run pytest tests/ -v
```

### Test Coverage

| File | What it tests |
|---|---|
| `test_summarize_endpoint.py` | Full HTTP stack via FastAPI `AsyncClient` with mocked service |
| `test_sanitization.py` | `_needs_sanitization` regex logic in isolation |

### Test cases

- ✅ Valid text returns 200 with `summary` field
- ✅ Response shape contains exactly `{"summary": "..."}`
- ✅ Empty text returns 422
- ✅ Whitespace-only text returns 422
- ✅ Missing `text` field returns 422
- ✅ LLM failure returns 502 with error detail
- ✅ LLM timeout returns 502 with "timed out" detail
- ✅ Long text (500 words) returns 200
- ✅ Clean text does not trigger sanitization
- ✅ HTML tags, entities, URLs trigger sanitization
- ✅ Unicode letters (accented characters) do not trigger sanitization

