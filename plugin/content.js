// ─── Text Extraction ─────────────────────────────────────────────────────────

/**
 * Priority chain for extracting meaningful text from the current page:
 *   1. <article>  — news, blog posts
 *   2. <main>     — standard semantic landmark
 *   3. All <p>    — generic article-style pages
 *   4. Longest <div> with > SPA_FALLBACK_MIN_CHARS chars — SPA fallback
 */
function extractPageText() {
  const clean = (el) =>
    el.innerText.replace(/\s+/g, " ").trim();

  // 1. <article>
  const article = document.querySelector("article");
  if (article) {
    const text = clean(article);
    if (text.length > SPA_FALLBACK_MIN_CHARS) return text;
  }

  // 2. <main>
  const main = document.querySelector("main");
  if (main) {
    const text = clean(main);
    if (text.length > SPA_FALLBACK_MIN_CHARS) return text;
  }

  // 3. All <p> tags joined
  const paragraphs = Array.from(document.querySelectorAll("p"))
    .map((p) => p.innerText.trim())
    .filter((t) => t.length > 0);
  if (paragraphs.length > 0) {
    const joined = paragraphs.join(" ");
    if (joined.length > SPA_FALLBACK_MIN_CHARS) return joined;
  }

  // 4. SPA fallback — longest <div> above threshold
  const divs = Array.from(document.querySelectorAll("div"));
  let best = "";
  for (const div of divs) {
    // Skip divs that contain other divs (we want leaf-ish nodes)
    if (div.querySelector("div")) continue;
    const text = clean(div);
    if (text.length > best.length) best = text;
  }
  if (best.length > SPA_FALLBACK_MIN_CHARS) return best;

  return null;
}

// ─── Truncation ───────────────────────────────────────────────────────────────

function truncate(text) {
  if (text.length <= MAX_CHARS) return text;
  // Trim at the last space within the limit to avoid cutting mid-word
  const cut = text.slice(0, MAX_CHARS);
  const lastSpace = cut.lastIndexOf(" ");
  return (lastSpace > MAX_CHARS * 0.9 ? cut.slice(0, lastSpace) : cut) + " …";
}

// ─── Pick Mode ────────────────────────────────────────────────────────────────

let _pickMode = false;
let _lastHighlighted = null;

function enterPickMode() {
  _pickMode = true;
  document.body.classList.add("arpeely-pick-mode");

  // Change FAB to cancel affordance
  const fab = document.getElementById("arpeely-fab");
  if (fab) {
    fab.textContent = "✕";
    fab.title = "Cancel selection (ESC)";
    fab.classList.add("arpeely-fab--picking");
  }

  document.addEventListener("mouseover", _onPickHover, true);
  document.addEventListener("mouseout", _onPickOut, true);
  document.addEventListener("click", _onPickClick, true);
  document.addEventListener("keydown", _onPickKeydown, true);
}

function exitPickMode() {
  _pickMode = false;
  document.body.classList.remove("arpeely-pick-mode");

  // Restore FAB
  const fab = document.getElementById("arpeely-fab");
  if (fab) {
    fab.textContent = "∑";
    fab.title = "Summarize this page";
    fab.classList.remove("arpeely-fab--picking");
  }

  _clearHighlight();
  document.removeEventListener("mouseover", _onPickHover, true);
  document.removeEventListener("mouseout", _onPickOut, true);
  document.removeEventListener("click", _onPickClick, true);
  document.removeEventListener("keydown", _onPickKeydown, true);
}

function _isPickable(el) {
  // Ignore our own UI elements
  if (el.closest("#arpeely-sidebar") || el.id === "arpeely-fab") return false;
  const text = (el.innerText || "").replace(/\s+/g, " ").trim();
  return text.length >= PICK_MIN_CHARS;
}

function _clearHighlight() {
  if (_lastHighlighted) {
    _lastHighlighted.classList.remove("arpeely-highlight");
    _lastHighlighted = null;
  }
}

function _onPickHover(e) {
  const el = e.target;
  if (!_isPickable(el)) return;
  _clearHighlight();
  el.classList.add("arpeely-highlight");
  _lastHighlighted = el;
}

function _onPickOut(e) {
  const el = e.target;
  el.classList.remove("arpeely-highlight");
  if (_lastHighlighted === el) _lastHighlighted = null;
}

function _onPickClick(e) {
  const el = e.target;
  if (el.id === "arpeely-fab") {
    // FAB click while in pick mode → cancel
    e.stopPropagation();
    e.preventDefault();
    exitPickMode();
    return;
  }
  if (!_isPickable(el)) return;
  e.stopPropagation();
  e.preventDefault();
  const text = (el.innerText || "").replace(/\s+/g, " ").trim();
  exitPickMode();
  handleSummarize(text);
}

function _onPickKeydown(e) {
  if (e.key === "Escape") {
    exitPickMode();
  }
}

// ─── Sidebar Overlay ─────────────────────────────────────────────────────────

function createSidebar() {
  const existing = document.getElementById("arpeely-sidebar");
  if (existing) return existing;

  const sidebar = document.createElement("div");
  sidebar.id = "arpeely-sidebar";
  sidebar.innerHTML = `
    <div id="arpeely-sidebar-header">
      <span id="arpeely-sidebar-title">📝 Arpeely Summary</span>
      <button id="arpeely-sidebar-close" title="Close">✕</button>
    </div>
    <div id="arpeely-sidebar-body">
      <p id="arpeely-sidebar-content"></p>
    </div>
  `;

  document.body.appendChild(sidebar);

  document.getElementById("arpeely-sidebar-close").addEventListener("click", () => {
    sidebar.classList.remove("arpeely-sidebar--open");
  });

  return sidebar;
}

function showSidebar(message, isError = false) {
  const sidebar = createSidebar();
  const content = document.getElementById("arpeely-sidebar-content");
  content.innerHTML = "";
  content.textContent = message;
  content.style.color = isError ? "#e05252" : "inherit";
  sidebar.classList.add("arpeely-sidebar--open");
}

function showLoading() {
  const sidebar = createSidebar();
  const content = document.getElementById("arpeely-sidebar-content");
  content.style.color = "inherit";
  content.innerHTML = `<span class="arpeely-spinner"></span><span class="arpeely-spinner-label">Summarizing…</span>`;
  sidebar.classList.add("arpeely-sidebar--open");
}

// ─── Floating Action Button ───────────────────────────────────────────────────

function createFAB() {
  if (document.getElementById("arpeely-fab")) return;

  const fab = document.createElement("button");
  fab.id = "arpeely-fab";
  fab.title = "Summarize this page";
  fab.textContent = "∑";

  fab.addEventListener("click", () => {
    if (_pickMode) {
      exitPickMode();
    } else {
      enterPickMode();
    }
  });

  document.body.appendChild(fab);
}

// ─── Main Handler ─────────────────────────────────────────────────────────────

/**
 * @param {string|null} [preselectedText] - Text from pick mode. Falls back to
 *   auto-extraction when omitted.
 */
async function handleSummarize(preselectedText) {
  const raw = preselectedText != null ? preselectedText : extractPageText();

  if (!raw) {
    showSidebar("⚠️ Could not find any readable text on this page.", true);
    return;
  }

  const text = truncate(raw);

  showLoading();

  try {
    const response = await fetch(SUMMARIZER_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      showSidebar(`❌ Server error ${response.status}: ${err.detail || response.statusText}`, true);
      return;
    }

    const data = await response.json();
    showSidebar(data.summary);
  } catch (err) {
    showSidebar(`❌ Network error: ${err.message}`, true);
  }
}

// ─── Bootstrap ───────────────────────────────────────────────────────────────

createFAB();
createSidebar(); // pre-create so it's ready instantly

