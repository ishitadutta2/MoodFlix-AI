/* analytics.js */
document.addEventListener("DOMContentLoaded", () => {
  const statsEl = qs("#analytics-stats");
  if (!statsEl) return;

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  async function load() {
    try {
      const res = await apiFetch("/api/analytics");
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      renderStats(data.analytics);
    } catch (err) {
      statsEl.innerHTML = `<p class="muted-2" style="padding:16px;">Couldn't load analytics right now.</p>`;
    }

    try {
      const res2 = await apiFetch("/api/trending");
      const data2 = await res2.json();
      renderTrending(data2.trending || []);
    } catch (err) {}
  }

  function renderStats(a) {
    statsEl.innerHTML = `
      <div class="card stat-tile"><b class="gradient-text">${a.chats_this_week}</b><span>Chats this week</span></div>
      <div class="card stat-tile"><b class="gradient-text">${escapeHtml(a.favorite_genre || "—")}</b><span>Favorite genre</span></div>
      <div class="card stat-tile"><b class="gradient-text">${escapeHtml(a.most_active_mood || "—")}</b><span>Most active mood</span></div>
      <div class="card stat-tile"><b class="gradient-text">${a.average_session_messages}</b><span>Avg. messages / chat</span></div>
    `;

    const bar = qs("#acceptance-bar");
    const label = qs("#acceptance-label");
    if (bar) bar.style.width = `${a.recommendation_acceptance_rate}%`;
    if (label) label.textContent = `${a.recommendation_acceptance_rate}% of ${a.recommendations_shown} recommendations shown were "Loved it"`;

    const moodWrap = qs("#mood-bars");
    if (moodWrap) {
      if (!a.mood_trend.length) {
        moodWrap.innerHTML = `<p class="muted-2" style="font-size:12.5px;">Chat a bit more and your mood trend will show up here.</p>`;
      } else {
        const max = Math.max(...a.mood_trend.map((m) => m.count));
        moodWrap.innerHTML = a.mood_trend.map((m) => `
          <div class="mood-bar-row">
            <span class="label">${escapeHtml(m.mood)}</span>
            <div class="mood-bar-track"><div class="mood-bar-fill" style="width:${(m.count / max) * 100}%;"></div></div>
            <span class="mood-bar-count">${m.count}</span>
          </div>
        `).join("");
      }
    }
  }

  function renderTrending(items) {
    const el = qs("#trending-list");
    if (!el) return;
    if (!items.length) {
      el.innerHTML = `<p class="muted-2" style="font-size:12.5px;">No favorites saved across MoodFlix AI yet.</p>`;
      return;
    }
    el.innerHTML = items.map((t) => `
      <div class="card history-row">
        <div class="icon-box"><i data-lucide="trending-up" class="icon-sm" style="color:var(--primary-2)"></i></div>
        <div class="titles"><p>${escapeHtml(t.title)}</p><span>${escapeHtml(t.content_type)} · favorited ${t.favorite_count}×</span></div>
      </div>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  load();
});
