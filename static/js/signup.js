/* signup.js */
document.addEventListener("DOMContentLoaded", () => {
  const form = qs("#signup-form");
  if (!form) return;

  const pwInput = qs("#password");
  const fill = qs("#pw-strength-fill");
  const label = qs("#pw-strength-label");

  if (pwInput && fill && label) {
    pwInput.addEventListener("input", () => {
      const { score, text, color } = scorePassword(pwInput.value);
      fill.style.width = `${score}%`;
      fill.style.background = color;
      label.textContent = pwInput.value ? text : "";
    });
  }

  function scorePassword(pw) {
    if (!pw) return { score: 0, text: "", color: "transparent" };
    let score = 0;
    if (pw.length >= 8) score += 25;
    if (pw.length >= 12) score += 15;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score += 20;
    if (/\d/.test(pw)) score += 20;
    if (/[^A-Za-z0-9]/.test(pw)) score += 20;
    score = Math.min(score, 100);

    if (score < 40) return { score, text: "Weak — add length, numbers, and symbols", color: "#f87171" };
    if (score < 75) return { score, text: "Okay — a bit more variety helps", color: "#fbbf24" };
    return { score, text: "Strong password", color: "#4ade80" };
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = qs("#name").value.trim();
    const email = qs("#email").value.trim();
    const password = qs("#password").value;
    if (!name || !email || !password) return;

    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;

    try {
      const res = await apiFetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok && data.success) {
        window.location.href = "/dashboard";
        return;
      }

      toast(data.message || "Could not create your account.", "error");
    } catch (err) {
      toast("Couldn't reach the server. Please check your connection and try again.", "error");
    } finally {
      submitBtn.disabled = false;
    }
  });
});
