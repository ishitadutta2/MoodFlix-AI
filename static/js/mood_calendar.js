/* mood_calendar.js */
document.addEventListener("DOMContentLoaded", () => {
  const grid = qs("#cal-grid");
  const weekdaysEl = qs("#cal-weekdays");
  const label = qs("#cal-month-label");
  const prevBtn = qs("#cal-prev");
  const nextBtn = qs("#cal-next");
  const dayPanel = qs("#cal-day-panel");
  const dayTitle = qs("#cal-day-title");
  const dayChats = qs("#cal-day-chats");
  if (!grid) return;

  const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const WEEKDAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

  const now = new Date();
  let year = now.getFullYear();
  let month = now.getMonth() + 1; // 1-12

  weekdaysEl.innerHTML = WEEKDAYS.map((d) => `<span>${d}</span>`).join("");

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  async function loadMonth() {
    label.textContent = `${MONTH_NAMES[month - 1]} ${year}`;
    grid.innerHTML = `<div class="skeleton" style="grid-column:1/-1;height:220px;"></div>`;
    dayPanel.style.display = "none";

    try {
      const res = await apiFetch(`/api/mood-calendar?year=${year}&month=${month}`);
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      render(data.days);
    } catch (err) {
      grid.innerHTML = `<p class="muted-2" style="grid-column:1/-1;padding:16px;">Couldn't load the calendar right now.</p>`;
    }
  }

  function render(days) {
    const firstWeekday = new Date(year, month - 1, 1).getDay();
    const blanks = Array.from({ length: firstWeekday }, () => `<div class="cal-day empty"></div>`);

    const dayCells = days.map((d) => {
      const hasChats = d.chat_count > 0;
      return `
        <div class="cal-day ${hasChats ? 'has-chats' : ''}" data-date="${d.date}" title="${hasChats ? d.chat_count + ' chat(s)' : ''}">
          <span class="day-num">${d.day}</span>
          <span class="day-emoji">${d.emoji}</span>
        </div>`;
    });

    grid.innerHTML = blanks.join("") + dayCells.join("");
    if (window.lucide) lucide.createIcons();
  }

  grid.addEventListener("click", async (e) => {
    const cell = e.target.closest(".cal-day.has-chats");
    if (!cell) return;
    const date = cell.dataset.date;

    dayPanel.style.display = "block";
    dayTitle.textContent = `Chats on ${date}`;
    dayChats.innerHTML = `<div class="skeleton skeleton-row"></div>`;

    try {
      const res = await apiFetch(`/api/mood-calendar/day/${date}`);
      const data = await res.json();
      dayChats.innerHTML = (data.chats || []).map((c) => `
        <a class="card history-row" href="/chatbot?chat_id=${c.id}" style="text-decoration:none;color:inherit;display:flex;">
          <div class="icon-box"><span style="font-size:18px;">${c.emoji}</span></div>
          <div class="titles"><p>${escapeHtml(c.title)}</p><span>${escapeHtml(c.last_message || "")}</span></div>
        </a>
      `).join("") || `<p class="muted-2">No chats found for this day.</p>`;
      dayPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      dayChats.innerHTML = `<p class="muted-2">Couldn't load that day.</p>`;
    }
  });

  prevBtn.addEventListener("click", () => {
    month -= 1;
    if (month < 1) { month = 12; year -= 1; }
    loadMonth();
  });
  nextBtn.addEventListener("click", () => {
    month += 1;
    if (month > 12) { month = 1; year += 1; }
    loadMonth();
  });

  loadMonth();
});
