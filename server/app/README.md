# Arpeely Block Summarizer — Server

A FastAPI backend that receives web page content and returns a summarized version using a LangGraph-powered LLM agent.

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
- **Dependency Injection** — FastAPI's `Depends` is used to inject the service. The concrete implementation is wired once in `infrastructure/dependencies.py` via `lru_cache`, so the agent and its compiled graph are built exactly once at startup.
- **Swappable providers** — adding a new LLM provider (e.g. Anthropic) only requires a new `SummarizerAgent` subclass and a one-line change in `_MODEL_REGISTRY`.
- **LangGraph pipeline** — the agent runs a two-step graph: an optional sanitization node (strips HTML/markup) followed by a summarization node. Routing is decided at runtime based on whether the input text contains non-standard characters.

### Project Structure

```
server/app/
├── main.py                          # FastAPI app entry point
├── pyproject.toml                   # Dependencies and project config
├── api/
│   └── summarize_controller.py      # POST /api/summarize/ endpoint
├── infrastructure/
│   ├── config.py                    # Settings (reads from .env)
│   └── dependencies.py              # DI wiring — builds and caches the service
├── services/
│   └── summarizer/
│       ├── summarizer_service.py    # SummarizerService ABC + SummarizeWithAgent
│       └── agent/
│           └── summarizer_agent.py  # LangGraph agent, factory, OpenAI implementation
└── tests/
    ├── conftest.py                  # MockSummarizerAgent, fixtures, dependency overrides
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

Create a `.env` file in `server/app/`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # optional, defaults to gpt-4o-mini
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
| `502` | LLM call failed |

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
- ✅ Long text (500 words) returns 200
- ✅ Clean text does not trigger sanitization
- ✅ HTML tags, entities, URLs trigger sanitization
- ✅ Non-ASCII characters trigger sanitization

