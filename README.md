# Arpeely Block Summarizer

A tool that summarizes web page content blocks using an LLM agent.

The project consists of two parts:
- **Server** — a FastAPI backend that receives content and returns a summary via a LangGraph-powered OpenAI agent.
- **Extension** *(coming soon)* — a browser extension that captures page content and sends it to the server.

---

## Quick Start

```bash
cd server/app
uv sync --group dev
uv run uvicorn server.app.main:app --reload
```

Then open **http://localhost:8000/docs** for the interactive API.

---

## Documentation

For full setup, architecture, API usage, and test instructions see the server README:

👉 [`server/app/README.md`](server/app/README.md)

