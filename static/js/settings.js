/* settings.js */
document.addEventListener("DOMContentLoaded", () => {
  const platformsList = qs("#platforms-list");
  const platformInput = qs("#platform-add-input");
  const resendBtn = qs("#resend-verification-btn");

  let platforms = [];

  function renderPlatforms() {
    if (!platformsList) return;
    platformsList.innerHTML = platforms.map((p, i) => `
      <span class="tag-chip">${escapeHtml(p)}<button type="button" data-index="${i}"><i data-lucide="x" style="width:12px;height:12px;"></i></button></span>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  async function savePlatforms() {
    try {
      const res = await apiFetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ favorite_platforms: platforms }),
      });
      const data = await res.json();
      const msgEl = qs("#platforms-msg");
      if (res.ok && data.success) {
        msgEl.textContent = "Saved.";
        msgEl.className = "form-msg success";
      } else {
        msgEl.textContent = data.message || "Couldn't save.";
        msgEl.className = "form-msg error";
      }
    } catch (err) {}
  }

  async function loadProfile() {
    try {
      const res = await apiFetch("/api/profile");
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      const profile = data.profile || {};
      platforms = profile.favorite_platforms || [];
      renderPlatforms();

      // Highlight active theme/accent selections.
      qsa("[data-theme-option]").forEach((btn) => {
        btn.style.outline = btn.dataset.themeOption === (profile.theme_preference || "dark") ? "2px solid var(--primary)" : "none";
      });
      qsa(".accent-swatch").forEach((btn) => {
        const isActive = btn.dataset.accent.toLowerCase() === (profile.accent_color || "#8B5CF6").toLowerCase();
        btn.style.borderColor = isActive ? "#fff" : "transparent";
      });

      // Notification / privacy toggles
      qsa("[data-notif-key]").forEach((row) => {
        const key = row.dataset.notifKey;
        const btn = row.querySelector(".toggle-switch");
        btn.classList.toggle("on", !!(profile.notification_settings || {})[key]);
      });
      qsa("[data-privacy-key]").forEach((row) => {
        const key = row.dataset.privacyKey;
        const btn = row.querySelector(".toggle-switch");
        btn.classList.toggle("on", !!(profile.privacy_settings || {})[key]);
      });
    } catch (err) {}
  }

  if (platformInput) {
    platformInput.addEventListener("keydown", async (e) => {
      if (e.key !== "Enter") return;
      e.preventDefault();
      const value = platformInput.value.trim();
      if (!value || platforms.includes(value)) { platformInput.value = ""; return; }
      platforms.push(value);
      renderPlatforms();
      platformInput.value = "";
      await savePlatforms();
    });
  }

  document.addEventListener("click", async (e) => {
    const removeBtn = e.target.closest("#platforms-list .tag-chip button");
    if (removeBtn) {
      platforms.splice(parseInt(removeBtn.dataset.index, 10), 1);
      renderPlatforms();
      await savePlatforms();
      return;
    }

    const themeBtn = e.target.closest("[data-theme-option]");
    if (themeBtn) {
      qsa("[data-theme-option]").forEach((b) => b.style.outline = "none");
      themeBtn.style.outline = "2px solid var(--primary)";
      await apiFetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme_preference: themeBtn.dataset.themeOption }),
      });
      const msgEl = qs("#appearance-msg");
      if (msgEl) { msgEl.textContent = "Saved."; msgEl.className = "form-msg success"; }
      return;
    }

    const swatch = e.target.closest(".accent-swatch");
    if (swatch) {
      qsa(".accent-swatch").forEach((b) => b.style.borderColor = "transparent");
      swatch.style.borderColor = "#fff";
      const color = swatch.dataset.accent;
      setAccentColor(color);
      await apiFetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accent_color: color }),
      });
      const msgEl = qs("#appearance-msg");
      if (msgEl) { msgEl.textContent = "Saved."; msgEl.className = "form-msg success"; }
      return;
    }

    const notifToggle = e.target.closest("[data-notif-key] .toggle-switch");
    if (notifToggle) {
      const key = notifToggle.closest("[data-notif-key]").dataset.notifKey;
      const newVal = !notifToggle.classList.contains("on");
      notifToggle.classList.toggle("on", newVal);
      await apiFetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notification_settings: { [key]: newVal } }),
      });
      toast("Saved", "success");
      return;
    }

    const privacyToggle = e.target.closest("[data-privacy-key] .toggle-switch");
    if (privacyToggle) {
      const key = privacyToggle.closest("[data-privacy-key]").dataset.privacyKey;
      const newVal = !privacyToggle.classList.contains("on");
      privacyToggle.classList.toggle("on", newVal);
      await apiFetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ privacy_settings: { [key]: newVal } }),
      });
      toast("Saved", "success");
      return;
    }
  });

  if (resendBtn) {
    resendBtn.addEventListener("click", async () => {
      resendBtn.disabled = true;
      try {
        const res = await apiFetch("/api/resend-verification", { method: "POST" });
        const data = await res.json();
        toast(data.message || (res.ok ? "Verification email sent." : "Couldn't send it right now."), res.ok ? "success" : "error");
      } catch (err) {
        toast("Couldn't reach the server.", "error");
      } finally {
        resendBtn.disabled = false;
      }
    });
  }

  loadProfile();
});
