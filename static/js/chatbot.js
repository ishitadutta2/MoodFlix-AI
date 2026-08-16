/* chatbot.js */
document.addEventListener("DOMContentLoaded", () => {
  const scroll = qs("#chat-scroll");
  const input = qs("#chat-input");
  const sendBtn = qs("#chat-send");
  const stopBtn = qs("#stop-btn");
  const micBtn = qs("#mic-btn");
  if (!scroll || !input || !sendBtn) return;

  // If a chat was already loaded server-side (via ?chat_id=...), keep
  // sending follow-up messages to that same conversation.
  let currentChatId = new URLSearchParams(window.location.search).get("chat_id") || null;
  let lastUserMessage = null;
  let activeAbortController = null;

  function scrollToBottom() { scroll.scrollTop = scroll.scrollHeight; }

  function addUserBubble(text) {
    const row = document.createElement("div");
    row.className = "msg-row user fade-in";
    row.innerHTML = `
      <div class="msg-line">
        <div class="bubble user">${escapeHtml(text)}</div>
      </div>`;
    scroll.appendChild(row);
    scrollToBottom();
  }

  function addTyping() {
    const row = document.createElement("div");
    row.className = "typing-row";
    row.id = "typing-indicator";
    row.innerHTML = `
      <div class="msg-avatar"><i data-lucide="sparkles" class="icon-sm" style="color:#fff"></i></div>
      <div class="typing-bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
      <div class="recs-wrap" style="padding-left:40px;width:100%;margin-top:8px;">
        <div class="recs-grid">
          <div class="card skeleton skeleton-card"></div>
          <div class="card skeleton skeleton-card"></div>
          <div class="card skeleton skeleton-card"></div>
        </div>
      </div>`;
    scroll.appendChild(row);
    if (window.lucide) lucide.createIcons();
    scrollToBottom();
  }

  function removeTyping() {
    const el = qs("#typing-indicator");
    if (el) el.remove();
  }

  function addErrorBubble(text) {
    const row = document.createElement("div");
    row.className = "msg-row fade-in";
    row.innerHTML = `
      <div class="msg-line">
        <div class="msg-avatar"><i data-lucide="alert-triangle" class="icon-sm" style="color:#fff"></i></div>
        <div class="bubble ai">${escapeHtml(text)}</div>
      </div>`;
    scroll.appendChild(row);
    if (window.lucide) lucide.createIcons();
    scrollToBottom();
  }

  // Creates an (initially empty) AI message row and returns handles to
  // update it as streamed text arrives.
  function addStreamingAiRow() {
    const row = document.createElement("div");
    row.className = "msg-row fade-in";
    row.innerHTML = `
      <div class="msg-line">
        <div class="msg-avatar"><i data-lucide="sparkles" class="icon-sm" style="color:#fff"></i></div>
        <div class="bubble ai" data-role="reply-text"></div>
      </div>
      <div class="recs-wrap" data-role="recs" style="display:none;">
        <div>
          <p class="recs-label">Movie recommendations</p>
          <div class="recs-grid" data-role="movies"></div>
        </div>
        <div>
          <p class="recs-label">Song recommendations</p>
          <div class="recs-grid" data-role="songs"></div>
        </div>
      </div>
      <div class="msg-actions" data-role="actions" style="display:none;">
        <button class="btn btn-ghost btn-icon copy-btn" title="Copy"><i data-lucide="copy" class="icon-sm"></i></button>
        <button class="btn btn-ghost btn-icon regenerate-btn" title="Regenerate"><i data-lucide="refresh-cw" class="icon-sm"></i></button>
        <button class="btn btn-ghost btn-icon continue-btn" title="Continue"><i data-lucide="chevrons-right" class="icon-sm"></i></button>
        <button class="btn btn-ghost btn-icon share-btn" title="Share"><i data-lucide="share-2" class="icon-sm"></i></button>
        <span class="msg-timestamp" data-role="timestamp"></span>
      </div>`;
    scroll.appendChild(row);
    scrollToBottom();
    return row;
  }

  function renderMarkdown(text) {
    if (window.marked && window.DOMPurify) {
      try {
        return DOMPurify.sanitize(marked.parse(text));
      } catch (err) {
        // fall through to plain text
      }
    }
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function fmtTime(date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function finishAiRow(row, reply, movies, songs, chatId) {
    const textEl = row.querySelector('[data-role="reply-text"]');
    textEl.innerHTML = renderMarkdown(reply);
    textEl.dataset.fullText = reply;

    const recsWrap = row.querySelector('[data-role="recs"]');
    const moviesEl = row.querySelector('[data-role="movies"]');
    const songsEl = row.querySelector('[data-role="songs"]');
    moviesEl.innerHTML = (movies || []).map(movieCardHtml).join("");
    songsEl.innerHTML = (songs || []).map(songCardHtml).join("");
    if (movies && movies.length || songs && songs.length) recsWrap.style.display = "";

    const timeEl = row.querySelector('[data-role="timestamp"]');
    if (timeEl) timeEl.textContent = fmtTime(new Date());

    const actions = row.querySelector('[data-role="actions"]');
    actions.style.display = "flex";
    if (chatId) actions.dataset.chatId = chatId;

    if (window.lucide) lucide.createIcons();
    scrollToBottom();
  }

  function movieCardHtml(m) {
    return `
      <div class="card rec-card holographic-border">
        <div class="top">
          <div class="tile poster" style="background:linear-gradient(150deg,hsl(${m.hue} 70% 22%),hsl(${m.hue + 40} 65% 12%));"><i data-lucide="film" class="icon"></i></div>
          <div style="flex:1;min-width:0;">
            <div class="flex justify-between items-center">
              <h4>${escapeHtml(m.title)}</h4>
              <button class="fav-btn" data-fav-type="movie" data-fav-title="${escapeAttr(m.title)}" data-fav-genre="${escapeAttr(m.genre)}" data-fav-year="${escapeAttr(m.year)}" data-fav-desc="${escapeAttr(m.desc)}"><i data-lucide="heart" class="icon-sm" fill="none" style="color:var(--muted)"></i></button>
            </div>
            <p class="meta">${m.year} · ${escapeHtml(m.genre)}</p>
          </div>
        </div>
        <p class="desc">${escapeHtml(m.desc)}</p>
        <div class="rating"><i data-lucide="star" class="icon-sm" fill="var(--accent)" style="color:var(--accent)"></i> ${m.rating}/10</div>
        <button class="btn btn-ghost why-btn"><i data-lucide="info" class="icon-sm"></i> Why this?</button>
        <p class="why-text hidden">${escapeHtml(m.why || "")}</p>
        <div class="card-actions-row">
          <button class="btn btn-ghost btn-icon feedback-btn" data-reaction="loved" data-fb-title="${escapeAttr(m.title)}" data-fb-type="movie" data-fb-genre="${escapeAttr(m.genre)}" title="Loved it"><i data-lucide="thumbs-up" class="icon-sm"></i></button>
          <button class="btn btn-ghost btn-icon feedback-btn" data-reaction="disliked" data-fb-title="${escapeAttr(m.title)}" data-fb-type="movie" data-fb-genre="${escapeAttr(m.genre)}" title="Not for me"><i data-lucide="thumbs-down" class="icon-sm"></i></button>
          <a class="btn btn-ghost btn-icon" href="https://www.youtube.com/results?search_query=${encodeURIComponent(m.title + " trailer")}" target="_blank" rel="noopener" title="Search trailer on YouTube"><i data-lucide="play-circle" class="icon-sm"></i></a>
        </div>
      </div>`;
  }

  function songCardHtml(s) {
    return `
      <div class="card song-card holographic-border">
        <div class="top">
          <div class="tile cover" style="background:linear-gradient(150deg,hsl(${s.hue} 70% 22%),hsl(${s.hue + 40} 65% 12%));"><i data-lucide="music-2" class="icon"></i></div>
          <div style="flex:1;min-width:0;">
            <div class="flex justify-between items-center">
              <h4>${escapeHtml(s.title)}</h4>
              <button class="fav-btn" data-fav-type="song" data-fav-title="${escapeAttr(s.title)}" data-fav-artist="${escapeAttr(s.artist)}" data-fav-genre="${escapeAttr(s.genre)}" data-fav-desc="${escapeAttr(s.desc)}"><i data-lucide="heart" class="icon-sm" fill="none" style="color:var(--muted)"></i></button>
            </div>
            <p class="artist">${escapeHtml(s.artist)}</p>
            <p class="meta">${escapeHtml(s.genre)} · ${s.duration}</p>
          </div>
        </div>
        <p class="desc">${escapeHtml(s.desc)}</p>
        <div class="card-actions-row">
          <button class="btn btn-ghost btn-icon feedback-btn" data-reaction="loved" data-fb-title="${escapeAttr(s.title)}" data-fb-type="song" data-fb-genre="${escapeAttr(s.genre)}" title="Loved it"><i data-lucide="thumbs-up" class="icon-sm"></i></button>
          <button class="btn btn-ghost btn-icon feedback-btn" data-reaction="disliked" data-fb-title="${escapeAttr(s.title)}" data-fb-type="song" data-fb-genre="${escapeAttr(s.genre)}" title="Not for me"><i data-lucide="thumbs-down" class="icon-sm"></i></button>
          <a class="btn btn-ghost btn-icon" href="https://www.youtube.com/results?search_query=${encodeURIComponent(s.title + " " + s.artist)}" target="_blank" rel="noopener" title="Listen on YouTube"><i data-lucide="play-circle" class="icon-sm"></i></a>
        </div>
      </div>`;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return escapeHtml(str).replace(/"/g, "&quot;");
  }

  function setGenerating(isGenerating) {
    sendBtn.style.display = isGenerating ? "none" : "";
    if (stopBtn) stopBtn.style.display = isGenerating ? "" : "none";
    input.disabled = isGenerating;
  }

  async function sendMessage(overrideText, skipUserBubble) {
    const text = (overrideText != null ? overrideText : input.value).trim();
    if (!text) return;

    if (!skipUserBubble) {
      addUserBubble(text);
    }
    if (overrideText == null) {
      input.value = "";
    }
    lastUserMessage = text;

    activeAbortController = new AbortController();
    setGenerating(true);
    addTyping();

    let aiRow = null;

    try {
      const res = await apiFetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, chat_id: currentChatId }),
        signal: activeAbortController.signal,
      });

      if (res.status === 401) {
        removeTyping();
        addErrorBubble("You'll need to log in to chat with MoodFlix AI.");
        setTimeout(() => { window.location.href = "/login"; }, 1200);
        return;
      }

      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}));
        removeTyping();
        addErrorBubble(data.message || "Something went wrong. Please try again.");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let boundary;
        while ((boundary = buffer.indexOf("\n\n")) !== -1) {
          const chunk = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);

          const eventMatch = chunk.match(/^event: (\w+)/m);
          const dataMatch = chunk.match(/^data: (.+)$/m);
          if (!eventMatch || !dataMatch) continue;

          const eventType = eventMatch[1];
          const payload = JSON.parse(dataMatch[1]);

          if (eventType === "token") {
            if (!aiRow) {
              removeTyping();
              aiRow = addStreamingAiRow();
            }
            aiRow.querySelector('[data-role="reply-text"]').textContent = payload.text;
            scrollToBottom();
          } else if (eventType === "done") {
            if (!aiRow) aiRow = addStreamingAiRow();
            finishAiRow(aiRow, payload.reply, payload.movies, payload.songs, payload.chat_id);
            if (payload.chat_id && payload.chat_id !== currentChatId) {
              currentChatId = payload.chat_id;
              const url = new URL(window.location);
              url.searchParams.set("chat_id", currentChatId);
              window.history.replaceState({}, "", url);
            }
          }
        }
      }
    } catch (err) {
      removeTyping();
      if (err.name === "AbortError") {
        if (aiRow) {
          const textEl = aiRow.querySelector('[data-role="reply-text"]');
          textEl.textContent += " [stopped]";
          aiRow.querySelector('[data-role="actions"]').style.display = "flex";
          if (window.lucide) lucide.createIcons();
        }
      } else {
        addErrorBubble("I couldn't reach the server. Please check your connection and try again.");
      }
    } finally {
      setGenerating(false);
      activeAbortController = null;
    }
  }

  sendBtn.addEventListener("click", () => sendMessage());
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendMessage(); });

  const moodChipRow = qs("#mood-chip-row");
  if (moodChipRow) {
    moodChipRow.addEventListener("click", (e) => {
      const chip = e.target.closest(".mood-chip");
      if (!chip) return;
      sendMessage(chip.dataset.moodText);
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      if (activeAbortController) activeAbortController.abort();
    });
  }

  // Copy / regenerate / continue / share on AI messages (event delegation)
  scroll.addEventListener("click", async (e) => {
    const copyBtn = e.target.closest(".copy-btn");
    if (copyBtn) {
      const row = copyBtn.closest(".msg-row");
      const text = row.querySelector('[data-role="reply-text"]').dataset.fullText || "";
      navigator.clipboard.writeText(text).then(() => toast("Copied to clipboard", "success")).catch(() => {});
      return;
    }

    const regenBtn = e.target.closest(".regenerate-btn");
    if (regenBtn && lastUserMessage) {
      sendMessage(lastUserMessage, true);
      return;
    }

    const shareBtn = e.target.closest(".share-btn");
    if (shareBtn) {
      const row = shareBtn.closest(".msg-row");
      const text = row.querySelector('[data-role="reply-text"]').dataset.fullText || "";
      if (navigator.share) {
        navigator.share({ title: "MoodFlix AI recommendation", text }).catch(() => {});
      } else {
        navigator.clipboard.writeText(text).then(() => toast("Copied — paste it anywhere to share", "success")).catch(() => {});
      }
      return;
    }

    const continueBtn = e.target.closest(".continue-btn");
    if (continueBtn && currentChatId) {
      continueBtn.disabled = true;
      setGenerating(true);
      addTyping();
      try {
        const res = await apiFetch(`/api/continue-chat/${currentChatId}`, { method: "POST" });
        const data = await res.json().catch(() => ({}));
        removeTyping();
        if (res.ok && data.success) {
          const row = addStreamingAiRow();
          finishAiRow(row, data.reply, data.movies, data.songs, data.chat_id);
        } else {
          addErrorBubble(data.message || "Couldn't continue that reply.");
        }
      } catch (err) {
        removeTyping();
        addErrorBubble("Couldn't reach the server.");
      } finally {
        continueBtn.disabled = false;
        setGenerating(false);
      }
    }
  });

  // Voice input (Web Speech API — Chrome/Edge only; button stays hidden elsewhere)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition && micBtn) {
    micBtn.style.display = "";
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    let listening = false;
    micBtn.addEventListener("click", () => {
      if (listening) { recognition.stop(); return; }
      recognition.start();
    });
    recognition.addEventListener("start", () => {
      listening = true;
      micBtn.classList.add("active");
    });
    recognition.addEventListener("end", () => {
      listening = false;
      micBtn.classList.remove("active");
    });
    recognition.addEventListener("result", (e) => {
      const transcript = e.results[0][0].transcript;
      input.value = transcript;
      input.focus();
    });
    recognition.addEventListener("error", () => {
      listening = false;
      micBtn.classList.remove("active");
    });
  }

  scrollToBottom();

  // Server-rendered messages (resumed chat) start as plain escaped text;
  // upgrade them to rendered markdown once marked.js/DOMPurify are ready.
  function upgradeInitialMarkdown() {
    if (!window.marked || !window.DOMPurify) { setTimeout(upgradeInitialMarkdown, 50); return; }
    qsa('.bubble.ai[data-role="reply-text"]').forEach((el) => {
      const raw = el.dataset.fullText || el.textContent;
      el.innerHTML = renderMarkdown(raw);
    });
  }
  upgradeInitialMarkdown();
});
