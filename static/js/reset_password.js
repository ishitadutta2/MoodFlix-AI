/* reset_password.js */
document.addEventListener("DOMContentLoaded", () => {
  const form = qs("#reset-password-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = qs("#token").value;
    const new_password = qs("#new-password").value;
    if (!new_password) return;

    const msgEl = qs("#reset-password-msg");
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;

    try {
      const res = await apiFetch("/api/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok && data.success) {
        msgEl.textContent = "Password reset. Redirecting to login…";
        msgEl.className = "form-msg success";
        setTimeout(() => { window.location.href = "/login"; }, 1200);
      } else {
        msgEl.textContent = data.message || "Couldn't reset your password.";
        msgEl.className = "form-msg error";
      }
    } catch (err) {
      msgEl.textContent = "Couldn't reach the server. Please try again.";
      msgEl.className = "form-msg error";
    } finally {
      submitBtn.disabled = false;
    }
  });
});
