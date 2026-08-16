/* forgot_password.js */
document.addEventListener("DOMContentLoaded", () => {
  const form = qs("#forgot-password-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = qs("#email").value.trim();
    if (!email) return;

    const msgEl = qs("#forgot-password-msg");
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;

    try {
      const res = await apiFetch("/api/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json().catch(() => ({}));
      msgEl.textContent = data.message || "If an account exists for that email, we've sent a reset link.";
      msgEl.className = "form-msg success";
    } catch (err) {
      msgEl.textContent = "Couldn't reach the server. Please try again.";
      msgEl.className = "form-msg error";
    } finally {
      submitBtn.disabled = false;
    }
  });
});
