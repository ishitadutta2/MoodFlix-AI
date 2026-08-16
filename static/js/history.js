/* history.js */
document.addEventListener("DOMContentLoaded", () => {
  const list = qs("#history-list");
  const empty = qs("#history-empty");
  const clearBtn = qs("#clear-history-btn");
  if (!list) return;

  let chats = [];

  function fmtDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  }

  function render() {
    if (chats.length === 0) {
      list.innerHTML = "";
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";
    list.innerHTML = chats.map((c) => `
      <div class="card history-row fade-in" data-chat-id="${c.id}">
        <div class="icon-box"><i data-lucide="message-square" class="icon-sm" style="color:var(--primary-2)"></i></div>
        <a class="titles" href="/chatbot?chat_id=${c.id}" style="text-decoration:none;color:inherit;">
          <p>${c.pinned ? '📌 ' : ''}${escapeHtml(c.title || "Untitled chat")}</p>
          <span>${escapeHtml(c.last_message || "No messages yet")} · ${fmtDate(c.updated_at)}</span>
        </a>
        <div class="row-actions">
          <button class="btn btn-ghost btn-icon pin-btn" title="${c.pinned ? 'Unpin' : 'Pin'}"><i data-lucide="pin" class="icon-sm"${c.pinned ? ' fill="var(--primary)" style="color:var(--primary)"' : ''}></i></button>
          <button class="btn btn-ghost btn-icon rename-btn" title="Rename"><i data-lucide="pencil" class="icon-sm"></i></button>
          <button class="btn btn-ghost btn-icon delete-btn" title="Delete"><i data-lucide="trash-2" class="icon-sm"></i></button>
        </div>
      </div>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  async function loadHistory() {
    list.innerHTML = `<div class="card skeleton skeleton-row"></div><div class="card skeleton skeleton-row"></div><div class="card skeleton skeleton-row"></div>`;
    try {
      const res = await apiFetch("/api/history");
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      chats = data.history || [];
      chats.sort((a, b) => (b.pinned - a.pinned));
      render();
    } catch (err) {
      list.innerHTML = `<p class="muted-2" style="padding:16px;">Couldn't load your chat history right now.</p>`;
    }
  }

  list.addEventListener("click", async (e) => {
    const row = e.target.closest(".history-row");
    if (!row) return;
    const chatId = row.dataset.chatId;

    if (e.target.closest(".pin-btn")) {
      const chat = chats.find((c) => c.id === chatId);
      if (!chat) return;
      const newPinned = !chat.pinned;
      const res = await apiFetch(`/api/history/${chatId}/pin`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pinned: newPinned }),
      });
      if (res.ok) {
        chat.pinned = newPinned;
        chats.sort((a, b) => (b.pinned - a.pinned));
        render();
      }
      return;
    }

    if (e.target.closest(".delete-btn")) {
      if (!confirm("Delete this chat? This can't be undone.")) return;
      const res = await apiFetch(`/api/history/${chatId}`, { method: "DELETE" });
      if (res.ok) {
        chats = chats.filter((c) => c.id !== chatId);
        render();
      }
      return;
    }

    if (e.target.closest(".rename-btn")) {
      const chat = chats.find((c) => c.id === chatId);
      const titlesEl = row.querySelector(".titles");
      const currentTitle = chat ? chat.title : "";
      titlesEl.outerHTML = `<div class="titles"><input class="input rename-input" value="${escapeAttr(currentTitle)}" maxlength="120"></div>`;
      const input = row.querySelector(".rename-input");
      input.focus();
      input.select();

      const commit = async () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== currentTitle) {
          const res = await apiFetch(`/api/history/${chatId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: newTitle }),
          });
          if (res.ok && chat) chat.title = newTitle;
        }
        render();
      };
      input.addEventListener("blur", commit);
      input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") input.blur(); });
    }
  });

  clearBtn.addEventListener("click", async () => {
    if (chats.length === 0) return;
    if (!confirm("Delete ALL chat history? This can't be undone.")) return;
    const res = await apiFetch("/api/history", { method: "DELETE" });
    if (res.ok) {
      chats = [];
      render();
    }
  });

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }
  function escapeAttr(str) { return escapeHtml(str).replace(/"/g, "&quot;"); }

  loadHistory();
});
