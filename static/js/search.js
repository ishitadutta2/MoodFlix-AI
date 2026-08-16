/* search.js */
document.addEventListener("DOMContentLoaded", () => {
  const input = qs("#global-search-input");
  const results = qs("#search-results");
  if (!input) return;

  let debounceTimer = null;

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  function section(title, items) {
    if (!items) return "";
    return `<p class="recs-label" style="margin:20px 0 10px;">${title}</p>${items}`;
  }

  function render(data) {
    const chatItems = data.chats.map((c) => `
      <a class="card history-row" href="/chatbot?chat_id=${c.id}" style="text-decoration:none;color:inherit;display:flex;">
        <div class="icon-box"><i data-lucide="message-square" class="icon-sm" style="color:var(--primary-2)"></i></div>
        <div class="titles"><p>${escapeHtml(c.title)}</p><span>${escapeHtml(c.last_message || "")}</span></div>
      </a>`).join("");

    const messageItems = data.messages.map((m) => `
      <a class="card history-row" href="/chatbot?chat_id=${m.chat_id}" style="text-decoration:none;color:inherit;display:flex;">
        <div class="icon-box"><i data-lucide="${m.sender === 'user' ? 'user' : 'sparkles'}" class="icon-sm" style="color:var(--primary-2)"></i></div>
        <div class="titles"><p>${escapeHtml(m.snippet)}</p><span>${m.sender === 'user' ? 'You said this' : 'MoodFlix AI said this'}</span></div>
      </a>`).join("");

    const favItems = data.favorites.map((f) => `
      <div class="card history-row">
        <div class="icon-box"><i data-lucide="heart" class="icon-sm" style="color:var(--primary-2)"></i></div>
        <div class="titles"><p>${escapeHtml(f.title)}</p><span>${escapeHtml(f.content_type)}${f.genre ? " · " + escapeHtml(f.genre) : ""}</span></div>
      </div>`).join("");

    const html = [
      section("Chats", chatItems ? `<div class="history-list">${chatItems}</div>` : ""),
      section("Messages", messageItems ? `<div class="history-list">${messageItems}</div>` : ""),
      section("Favorites", favItems ? `<div class="history-list">${favItems}</div>` : ""),
    ].join("");

    if (!chatItems && !messageItems && !favItems) {
      results.innerHTML = `<div class="page-empty"><i data-lucide="search-x" style="width:32px;height:32px;"></i><p>No results for "${escapeHtml(data.query)}".</p></div>`;
    } else {
      results.innerHTML = html;
    }
    if (window.lucide) lucide.createIcons();
  }

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (!q) {
      results.innerHTML = `<div class="page-empty"><i data-lucide="search" style="width:32px;height:32px;"></i><p>Start typing to search.</p></div>`;
      if (window.lucide) lucide.createIcons();
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const res = await apiFetch(`/api/search?q=${encodeURIComponent(q)}`);
        if (res.status === 401) { window.location.href = "/login"; return; }
        const data = await res.json();
        render(data);
      } catch (err) {
        results.innerHTML = `<p class="muted-2" style="padding:16px;">Couldn't search right now.</p>`;
      }
    }, 300);
  });
});
