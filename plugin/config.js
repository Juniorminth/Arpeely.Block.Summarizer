// ─── Server Configuration ────────────────────────────────────────────────────
// Change this to point at your deployed server when moving beyond localhost.
const SUMMARIZER_BASE_URL = "http://localhost:8000";
const SUMMARIZER_ENDPOINT = `${SUMMARIZER_BASE_URL}/api/summarize/`;

// Minimum character count for the "longest <div>" SPA fallback heuristic.
const SPA_FALLBACK_MIN_CHARS = 200;

// Maximum characters sent to the server (keeps token cost predictable).
const MAX_CHARS = 6000;

// Minimum characters an element must have to be selectable in pick mode.
const PICK_MIN_CHARS = 200;

