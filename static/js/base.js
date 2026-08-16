/* ============================================================
   MoodFlix AI — base.js
   Shared behaviour loaded on every page: icons, theme, sidebar.
============================================================ */

// Render lucide icons (script tag for the lucide CDN is included in base.html)
document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("page-transition-ready");
  if (window.lucide) lucide.createIcons();
  initTheme();
  initAccentColor();
  initMobileSidebar();
  highlightActiveNavLink();
  initLogout();
  initFavoriteButtons();
  initFeedbackButtons();
  initWhyThisToggle();
  initChatSearch();
  ensureToastContainer();
  applyTimeBasedGreeting();
});

/* ---------- personalized greeting based on local time (dashboard only) ---------- */
function applyTimeBasedGreeting() {
  const el = document.getElementById("dash-greeting");
  if (!el) return;
  const hour = new Date().getHours();
  const timeGreeting = hour < 5 ? "Still up" : hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : hour < 21 ? "Good evening" : "Good night";
  // Keep the name the server already rendered; just swap the leading phrase.
  el.textContent = el.textContent.replace(/^(Welcome back|Good morning|Good afternoon|Good evening|Good night|Still up),/, `${timeGreeting},`);
}

/* ---------- feedback (Loved it / Not for me) on recommendation cards ---------- */
function initFeedbackButtons() {
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".feedback-btn");
    if (!btn) return;

    const card = btn.closest(".rec-card, .song-card");
    const otherBtn = card ? card.querySelector(`.feedback-btn[data-reaction="${btn.dataset.reaction === "loved" ? "disliked" : "loved"}"]`) : null;

    btn.disabled = true;
    try {
      const res = await apiFetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: btn.dataset.fbTitle,
          content_type: btn.dataset.fbType,
          genre: btn.dataset.fbGenre || "",
          reaction: btn.dataset.reaction,
        }),
      });

      if (res.status === 401) { window.location.href = "/login"; return; }

      const data = await res.json().catch(() => ({}));
      if (res.ok && data.success) {
        btn.classList.add("active");
        if (otherBtn) otherBtn.classList.remove("active");
        toast(btn.dataset.reaction === "loved" ? "Thanks — noted!" : "Got it, we'll show less of this.", "success");
      } else {
        toast(data.message || "Couldn't save your feedback.", "error");
      }
    } catch (err) {
      toast("Couldn't reach the server.", "error");
    } finally {
      btn.disabled = false;
    }
  });
}

/* ---------- accent color (persisted in localStorage, applied on every page) ---------- */
function initAccentColor() {
  const saved = localStorage.getItem("moodflix_accent");
  if (saved) document.documentElement.style.setProperty("--primary", saved);
}
function setAccentColor(color) {
  document.documentElement.style.setProperty("--primary", color);
  localStorage.setItem("moodflix_accent", color);
}
window.setAccentColor = setAccentColor;

/* ---------- apiFetch: adds CSRF header to state-changing requests ---------- */
async function apiFetch(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { ...(options.headers || {}) };
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && window.CSRF_TOKEN) {
    headers["X-CSRF-Token"] = window.CSRF_TOKEN;
  }
  return fetch(url, { ...options, headers });
}

/* ---------- toast notifications ---------- */
function ensureToastContainer() {
  if (document.getElementById("toast-container")) return;
  const el = document.createElement("div");
  el.id = "toast-container";
  el.style.cssText = "position:fixed;top:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;";
  document.body.appendChild(el);
}

function toast(message, type = "info") {
  ensureToastContainer();
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  const colors = { success: "#4ade80", error: "#f87171", info: "var(--primary, #8B5CF6)" };
  el.textContent = message;
  el.style.cssText = `
    background:var(--card,#17171f); color:var(--text,#fff); border:1px solid ${colors[type] || colors.info};
    border-left:4px solid ${colors[type] || colors.info}; padding:12px 16px; border-radius:10px;
    font-size:13.5px; max-width:320px; box-shadow:0 8px 24px rgba(0,0,0,0.35);
    animation: toast-in .2s ease-out;
  `;
  container.appendChild(el);
  setTimeout(() => {
    el.style.transition = "opacity .2s, transform .2s";
    el.style.opacity = "0";
    el.style.transform = "translateX(8px)";
    setTimeout(() => el.remove(), 200);
  }, 3500);
}
window.toast = toast;
window.apiFetch = apiFetch;

/* ---------- "Why this?" reveal on recommendation cards (delegated so it
   also works for cards injected dynamically by chatbot.js) ---------- */
function initWhyThisToggle() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".why-btn");
    if (!btn) return;
    const el = btn.nextElementSibling;
    if (el && el.classList.contains("why-text")) {
      el.classList.toggle("hidden");
    }
  });
}

/* ---------- sidebar chat search (present on every app page) ---------- */
function initChatSearch() {
  const search = document.getElementById("chat-search");
  if (!search) return;
  search.addEventListener("input", () => {
    const q = search.value.toLowerCase();
    qsa(".chat-row").forEach((row) => {
      row.style.display = row.dataset.title.includes(q) ? "flex" : "none";
    });
  });
}

/* ---------- logout ---------- */
function initLogout() {
  const link = document.getElementById("logout-link");
  if (!link) return;
  link.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await apiFetch("/api/logout", { method: "POST" });
    } catch (err) {
      // Even if the request fails, still send the user home —
      // there's nothing more useful to do client-side.
    }
    window.location.href = "/";
  });
}

/* ---------- favorite (heart) buttons on recommendation cards ---------- */
function initFavoriteButtons() {
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".fav-btn");
    if (!btn) return;

    const icon = btn.querySelector("i");
    const activating = !btn.classList.contains("active");

    // Cards without data-fav-type are decorative only (nothing to persist).
    if (!btn.dataset.favType || !btn.dataset.favTitle) {
      toggleHeart(btn, icon, activating);
      return;
    }

    if (!activating) {
      toggleHeart(btn, icon, false);
      const favoriteId = btn.dataset.favoriteId;
      if (favoriteId) {
        try { await apiFetch(`/api/favorites/${favoriteId}`, { method: "DELETE" }); } catch (err) {}
      }
      return;
    }

    btn.disabled = true;
    try {
      const res = await apiFetch("/api/favorites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: btn.dataset.favType,
          title: btn.dataset.favTitle,
          artist: btn.dataset.favArtist || "",
          genre: btn.dataset.favGenre || "",
          year: btn.dataset.favYear || "",
          description: btn.dataset.favDesc || "",
        }),
      });

      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }

      const data = await res.json().catch(() => ({}));

      if (res.ok && data.success) {
        btn.dataset.favoriteId = data.favorite.id;
        toggleHeart(btn, icon, true);
        toast("Added to favorites", "success");
      } else {
        toast(data.message || "Could not add to favorites.", "error");
      }
    } catch (err) {
      toast("Could not reach the server. Please try again.", "error");
    } finally {
      btn.disabled = false;
    }
  });
}

function toggleHeart(btn, icon, active) {
  btn.classList.toggle("active", active);
  if (!icon) return;
  icon.setAttribute("fill", active ? "var(--primary)" : "none");
  icon.style.color = active ? "var(--primary)" : "var(--muted)";
}

/* ---------- theme (persisted in localStorage, defaults to dark; supports "system") ---------- */
function resolveTheme(pref) {
  if (pref === "system") {
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  return pref;
}
function initTheme() {
  const saved = localStorage.getItem("moodflix_theme") || "dark";
  document.documentElement.setAttribute("data-theme", resolveTheme(saved));
  document.querySelectorAll("[data-theme-option]").forEach((btn) => {
    btn.classList.toggle("theme-active", btn.dataset.themeOption === saved);
    btn.addEventListener("click", () => setTheme(btn.dataset.themeOption));
  });

  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
      if ((localStorage.getItem("moodflix_theme") || "dark") === "system") {
        document.documentElement.setAttribute("data-theme", resolveTheme("system"));
      }
    });
  }
}
function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", resolveTheme(theme));
  localStorage.setItem("moodflix_theme", theme);
  document.querySelectorAll("[data-theme-option]").forEach((btn) => {
    btn.classList.toggle("theme-active", btn.dataset.themeOption === theme);
  });
}

/* ---------- mobile sidebar drawer ---------- */
function initMobileSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const openBtn = document.querySelector("[data-sidebar-open]");
  const closeBtn = document.querySelector("[data-sidebar-close]");
  if (!sidebar) return;
  openBtn && openBtn.addEventListener("click", () => sidebar.classList.add("open"));
  closeBtn && closeBtn.addEventListener("click", () => sidebar.classList.remove("open"));
  document.addEventListener("click", (e) => {
    if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && !(openBtn && openBtn.contains(e.target))) {
      sidebar.classList.remove("open");
    }
  });
}

/* ---------- highlight the current page's sidebar/nav link ---------- */
function highlightActiveNavLink() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  document.querySelectorAll("[data-nav-link]").forEach((link) => {
    const target = link.getAttribute("href").replace(/\/$/, "") || "/";
    link.classList.toggle("active", target === path);
  });
}

/* ---------- tiny helper other page scripts reuse ---------- */
function qs(sel, ctx = document) { return ctx.querySelector(sel); }
function qsa(sel, ctx = document) { return Array.from(ctx.querySelectorAll(sel)); }
