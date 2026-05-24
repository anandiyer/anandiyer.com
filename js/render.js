// Tweet rail renderer. The investments / writing / talks rails are inlined
// directly in index.html (better for SEO and LLM crawlers that don't run JS).
// Tweets stay JS-rendered because data/tweets.json is auto-refreshed hourly
// by .github/workflows/refresh-tweets.yml.

const escape = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);

async function loadTweets() {
  try {
    const r = await fetch("/data/tweets.json", { cache: "no-cache" });
    if (!r.ok) throw new Error(`tweets.json: ${r.status}`);
    return await r.json();
  } catch (e) {
    console.warn("tweets load failed", e);
    return [];
  }
}

function renderTweets(items, root) {
  if (!items.length) {
    root.innerHTML = `<div style="color:var(--muted);font-size:.9rem">Tweets unavailable right now — see <a href="https://x.com/ai">@ai on X</a>.</div>`;
    return;
  }
  root.innerHTML = items.map((t) => `
    <a class="tweet" href="${escape(t.url)}" target="_blank" rel="noopener">
      <div class="text">${escape(t.text)}</div>
      <div class="foot">
        <span>@${escape(t.handle || "ai")}</span>
        <span>${escape(t.date || "")}</span>
      </div>
    </a>
  `).join("");
}

(async () => {
  const el = document.getElementById("tweets");
  if (!el) return;
  renderTweets(await loadTweets(), el);
})();
