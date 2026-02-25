# Arpeely Block Summarizer — Chrome Extension

A Manifest V3 Chrome extension that injects a floating **∑** button into every web page. Click it to enter **pick mode** — hover over any section to highlight it, then click to summarize it. The result appears in a slide-in sidebar powered by the local FastAPI server.

---

## Project structure

```
plugin/
├── manifest.json   # Extension manifest (MV3)
├── config.js       # Server URL & tuning constants  ← edit this to change the target server
├── content.js      # Content script: FAB + pick mode + extraction + sidebar logic
├── styles.css      # FAB, pick-mode highlight & sidebar styles
└── icons/          # 16 / 48 / 128 px PNG icons
```

---

## Loading the extension in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** and select the `plugin/` folder
4. The **∑** button will appear on every page

---

## Usage

| Action | Result |
|--------|--------|
| Click **∑** | Enter pick mode — cursor becomes a crosshair |
| Hover over a section | Section is highlighted with an indigo outline |
| Click a highlighted section | Summarize that section; spinner shown while waiting |
| Click **✕** FAB or press `ESC` | Cancel pick mode |
| Click **✕** in the sidebar header | Close the sidebar |

> **Pick mode** only highlights elements with ≥ 200 characters of visible text. The selected text is automatically truncated to 6 000 chars before being sent to the server.

---

## Configuration (`config.js`)

| Constant | Default | Description |
|----------|---------|-------------|
| `SUMMARIZER_BASE_URL` | `http://localhost:8000` | Server base URL |
| `SPA_FALLBACK_MIN_CHARS` | `200` | Min chars for auto-extraction fallback |
| `MAX_CHARS` | `6000` | Hard cap on text sent to the server |
| `PICK_MIN_CHARS` | `200` | Min chars for an element to be selectable in pick mode |

To point at a deployed server, change `SUMMARIZER_BASE_URL`:

```js
const SUMMARIZER_BASE_URL = "https://your-server.example.com";
```

---

## Auto-extraction fallback

If pick mode is not used and the FAB were to trigger automatically, the following priority chain is used:

| Priority | Selector | Notes |
|----------|----------|-------|
| 1 | `<article>` | News / blog posts |
| 2 | `<main>` | Standard semantic landmark |
| 3 | All `<p>` tags joined | Generic article pages |
| 4 | Longest `<div>` > `SPA_FALLBACK_MIN_CHARS` chars | React / Vue SPA fallback |

---

## Running the server

```bash
cd server/app
uv sync --group dev
uv run uvicorn server.app.main:app --reload
```

See [`server/app/README.md`](../server/app/README.md) for full server setup.
