/* favorites.js */
document.addEventListener("DOMContentLoaded", () => {
  const grid = qs("#favorites-grid");
  const empty = qs("#favorites-empty");
  const typeTabs = qsa(".fav-tabs")[1] ? qsa(".fav-tabs")[1].querySelectorAll(".tab-btn") : [];
  const listTabs = qs("#list-tabs") ? qs("#list-tabs").querySelectorAll(".tab-btn") : [];
  if (!grid) return;

  let favorites = [];
  let activeType = "all";
  let activeList = "favorites";

  const TYPE_ICON = { movie: "film", song: "music-2", anime: "sparkles", tv_show: "tv", book: "book-open" };
  const TYPE_LABEL = { movie: "Movie", song: "Song", anime: "Anime", tv_show: "TV Show", book: "Book" };

  function hueFor(text) {
    let h = 0;
    for (let i = 0; i < (text || "").length; i++) h = (h * 31 + text.charCodeAt(i)) % 360;
    return h;
  }

  function render() {
    const items = activeType === "all" ? favorites : favorites.filter((f) => f.content_type === activeType);

    if (items.length === 0) {
      grid.innerHTML = "";
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";

    grid.innerHTML = items.map((f) => {
      const hue = hueFor(f.title);
      const icon = TYPE_ICON[f.content_type] || "star";
      const metaBits = [f.genre, f.year].filter(Boolean).join(" · ");
      return `
        <div class="card favorite-card fade-in" data-fav-id="${f.id}">
          <div class="tile" style="background:linear-gradient(150deg,hsl(${hue} 70% 22%),hsl(${(hue + 40) % 360} 65% 12%));">
            <i data-lucide="${icon}" class="icon"></i>
          </div>
          <span class="chip" style="font-size:10.5px;margin-bottom:6px;display:inline-block;">${TYPE_LABEL[f.content_type] || f.content_type}</span>
          <h4>${escapeHtml(f.title)}</h4>
          ${metaBits ? `<p class="meta">${escapeHtml(metaBits)}</p>` : ""}
          <div class="row-actions">
            <button class="btn btn-ghost btn-icon move-fav-btn" title="${activeList === 'favorites' ? 'Move to Watch Later' : 'Move to Favorites'}"><i data-lucide="${activeList === 'favorites' ? 'clock' : 'heart'}" class="icon-sm"></i></button>
            <button class="btn btn-ghost btn-icon remove-fav-btn" title="Remove"><i data-lucide="trash-2" class="icon-sm"></i></button>
          </div>
        </div>`;
    }).join("");
    if (window.lucide) lucide.createIcons();
  }

  async function loadFavorites() {
    grid.innerHTML = `<div class="card skeleton skeleton-card"></div><div class="card skeleton skeleton-card"></div><div class="card skeleton skeleton-card"></div>`;
    empty.style.display = "none";
    try {
      const res = await apiFetch(`/api/favorites?list=${activeList}`);
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      favorites = data.favorites || [];
      render();
    } catch (err) {
      grid.innerHTML = `<p class="muted-2" style="padding:16px;">Couldn't load your favorites right now.</p>`;
    }
  }

  typeTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      typeTabs.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeType = btn.dataset.tab;
      render();
    });
  });

  listTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      listTabs.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeList = btn.dataset.list;
      loadFavorites();
    });
  });

  grid.addEventListener("click", async (e) => {
    const card = e.target.closest(".favorite-card");
    if (!card) return;
    const favId = card.dataset.favId;

    if (e.target.closest(".remove-fav-btn")) {
      const res = await apiFetch(`/api/favorites/${favId}`, { method: "DELETE" });
      if (res.ok) {
        favorites = favorites.filter((f) => f.id !== favId);
        render();
        toast("Removed", "success");
      }
      return;
    }

    if (e.target.closest(".move-fav-btn")) {
      const item = favorites.find((f) => f.id === favId);
      if (!item) return;
      const newList = activeList === "favorites" ? "watch_later" : "favorites";
      // Move = remove from current list + re-add under the new list (no dedicated move endpoint).
      await apiFetch(`/api/favorites/${favId}`, { method: "DELETE" });
      await apiFetch("/api/favorites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: item.content_type, title: item.title, artist: item.artist || "",
          genre: item.genre || "", year: item.year || "", description: item.description || "",
          list: newList,
        }),
      });
      favorites = favorites.filter((f) => f.id !== favId);
      render();
      toast(newList === "watch_later" ? "Moved to Watch Later" : "Moved to Favorites", "success");
    }
  });

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  loadFavorites();
});
