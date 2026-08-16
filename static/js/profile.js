/* profile.js */
document.addEventListener("DOMContentLoaded", () => {
  const basicForm = qs("#basic-info-form");
  const passwordForm = qs("#password-form");
  const avatarInput = qs("#avatar-input");
  const avatarImg = qs("#profile-avatar-img");
  const deleteBtn = qs("#delete-account-btn");
  if (!basicForm) return;

  const TAG_FIELDS = ["favorite_genres", "favorite_languages", "favorite_artists", "favorite_actors"];
  const listElFor = {
    favorite_genres: qs("#genres-list"),
    favorite_languages: qs("#languages-list"),
    favorite_artists: qs("#artists-list"),
    favorite_actors: qs("#actors-list"),
  };
  let profile = { favorite_genres: [], favorite_languages: [], favorite_artists: [], favorite_actors: [] };

  function showMsg(el, text, isError) {
    el.textContent = text;
    el.className = "form-msg " + (isError ? "error" : "success");
    setTimeout(() => { el.textContent = ""; el.className = "form-msg"; }, 4000);
  }

  function renderTags(field) {
    const el = listElFor[field];
    if (!el) return;
    el.innerHTML = (profile[field] || []).map((val, i) => `
      <span class="tag-chip">${escapeHtml(val)}<button type="button" data-field="${field}" data-index="${i}"><i data-lucide="x" style="width:12px;height:12px;"></i></button></span>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  async function loadProfile() {
    try {
      const res = await apiFetch("/api/profile");
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      profile = data.profile || profile;
      TAG_FIELDS.forEach(renderTags);
    } catch (err) {
      // Non-fatal — the page still works with an empty preference set.
    }
  }

  async function saveField(field, value, msgEl) {
    try {
      const res = await apiFetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [field]: value }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        if (msgEl) showMsg(msgEl, "Saved.", false);
        return true;
      }
      if (msgEl) showMsg(msgEl, data.message || "Couldn't save.", true);
      return false;
    } catch (err) {
      if (msgEl) showMsg(msgEl, "Couldn't reach the server.", true);
      return false;
    }
  }

  // -------- basic info --------
  basicForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msgEl = qs("#basic-info-msg");
    const name = qs("#name-input").value.trim();
    const bio = qs("#bio-input").value.trim();
    if (!name) { showMsg(msgEl, "Name can't be empty.", true); return; }
    const res = await apiFetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, bio }),
    });
    const data = await res.json();
    showMsg(msgEl, res.ok && data.success ? "Saved." : (data.message || "Couldn't save."), !(res.ok && data.success));
  });

  // -------- taste preferences --------
  qsa(".tag-add-input").forEach((input) => {
    input.addEventListener("keydown", async (e) => {
      if (e.key !== "Enter") return;
      e.preventDefault();
      const field = input.dataset.field;
      const value = input.value.trim();
      if (!value) return;
      if ((profile[field] || []).includes(value)) { input.value = ""; return; }
      profile[field] = [...(profile[field] || []), value];
      renderTags(field);
      input.value = "";
      await saveField(field, profile[field], qs("#prefs-msg"));
    });
  });

  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".tag-chip button");
    if (!btn) return;
    const field = btn.dataset.field;
    const index = parseInt(btn.dataset.index, 10);
    profile[field] = (profile[field] || []).filter((_, i) => i !== index);
    renderTags(field);
    await saveField(field, profile[field], qs("#prefs-msg"));
  });

  // -------- avatar upload --------
  avatarInput.addEventListener("change", async () => {
    const file = avatarInput.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("avatar", file);
    try {
      const res = await apiFetch("/api/profile/avatar", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok && data.success) {
        avatarImg.src = data.avatar + "?t=" + Date.now();
      } else {
        toast(data.message || "Couldn't upload that image.", "error");
      }
    } catch (err) {
      toast("Couldn't reach the server.", "error");
    }
  });

  // -------- password --------
  passwordForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msgEl = qs("#password-msg");
    const current_password = qs("#current-password").value;
    const new_password = qs("#new-password").value;
    if (!current_password || !new_password) {
      showMsg(msgEl, "Both fields are required.", true);
      return;
    }
    const res = await apiFetch("/api/profile/password", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password, new_password }),
    });
    const data = await res.json();
    if (res.ok && data.success) {
      qs("#current-password").value = "";
      qs("#new-password").value = "";
      showMsg(msgEl, "Password updated.", false);
    } else {
      showMsg(msgEl, data.message || "Couldn't update password.", true);
    }
  });

  // -------- delete account --------
  deleteBtn.addEventListener("click", async () => {
    if (!confirm("Delete your account? This permanently removes your chats and favorites and can't be undone.")) return;
    if (!confirm("Are you absolutely sure? This is your last chance to cancel.")) return;
    const res = await apiFetch("/api/profile", { method: "DELETE" });
    if (res.ok) {
      window.location.href = "/";
    } else {
      toast("Couldn't delete your account right now. Please try again.", "error");
    }
  });

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  loadProfile();
});
