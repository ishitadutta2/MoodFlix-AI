/* landing.js — FAQ accordion + hero parallax */
document.addEventListener("DOMContentLoaded", () => {
  qsa(".faq-item").forEach((item) => {
    item.addEventListener("click", () => {
      const wasOpen = item.classList.contains("open");
      qsa(".faq-item").forEach((i) => i.classList.remove("open"));
      if (!wasOpen) item.classList.add("open");
    });
  });

  initHeroParallax();
});

function initHeroParallax() {
  const el = qs("[data-parallax]");
  if (!el) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (window.matchMedia("(hover: none)").matches) return; // skip on touch devices

  const maxTilt = 4; // degrees

  document.addEventListener("mousemove", (e) => {
    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const dx = (e.clientX - centerX) / (window.innerWidth / 2);
    const dy = (e.clientY - centerY) / (window.innerHeight / 2);
    el.style.transform = `perspective(800px) rotateY(${dx * maxTilt}deg) rotateX(${-dy * maxTilt}deg)`;
  });

  document.addEventListener("mouseleave", () => {
    el.style.transform = "";
  });
}
