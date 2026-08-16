/* login.js */
document.addEventListener("DOMContentLoaded", () => {
  const form = qs("#login-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = qs("#email").value.trim();
    const password = qs("#password").value;
    const rememberMe = qs("#remember-me") ? qs("#remember-me").checked : false;
    if (!email || !password) return;

    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;

    try {
      const res = await apiFetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, remember_me: rememberMe }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok && data.success) {
        window.location.href = "/dashboard";
        return;
      }

      toast(data.message || "Could not log in. Check your credentials.", "error");
    } catch (err) {
      toast("Couldn't reach the server. Please check your connection and try again.", "error");
    } finally {
      submitBtn.disabled = false;
    }
  });
});
