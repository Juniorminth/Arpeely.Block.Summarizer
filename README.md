# Arpeely Block Summarizer

A tool that summarizes web page content blocks using an LLM agent.

The project consists of two parts:
- **Server** — a FastAPI backend that receives content and returns a summary via a LangGraph-powered OpenAI agent.
- **Extension** — a Chrome (Manifest V3) extension that lets you pick any section of a page and summarize it instantly via a slide-in sidebar.

---

## Quick Start

### 1. Server

```bash
# Install uv if you don't have it (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

cd server/app
cp .env.example .env          # then add your OPENAI_API_KEY
uv sync --group dev
uv run uvicorn server.app.main:app --reload
```

Then open **http://localhost:8000/docs** for the interactive API.

### 2. Extension

1. Open `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `plugin/` folder
4. The **∑** button will appear on every page

---

## How it works

1. Click the **∑** FAB — the cursor changes to a crosshair and hover-highlights any selectable section
2. Click the section you want summarized (or press `ESC` to cancel)
3. The text is truncated to 6 000 chars, sent to the server, and the summary appears in the sidebar

---

## Documentation

| Component | README |
|-----------|--------|
| Server (FastAPI + LangGraph) | [`server/app/README.md`](server/app/README.md) |
| Chrome Extension | [`plugin/README.md`](plugin/README.md) |
