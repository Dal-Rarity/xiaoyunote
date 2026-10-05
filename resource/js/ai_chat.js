/**
 * 小语手记 · AI 问答页
 * - fetch + ReadableStream 手动解析 SSE（EventSource 只支持 GET）
 * - 支持打字机效果、停止生成、参考文章卡片、"思考中" loading
 * - localStorage 按 user_id 隔离保存 session_id 与聊天历史
 */
(function () {
  "use strict";

  // ========== 用户隔离 ==========
  const USER_ID = String(window.__AI_USER_ID__ || "anon");
  const SID_KEY = "ai_session_id_" + USER_ID;
  const HIST_KEY = "ai_chat_history_" + USER_ID;

  const logEl = document.getElementById("ai-log");
  const qEl = document.getElementById("ai-q");
  const sendBtn = document.getElementById("ai-send");
  const stopBtn = document.getElementById("ai-stop");

  let controller = null;

  // ========== session_id 管理 ==========
  function getSessionId() {
    let sid = localStorage.getItem(SID_KEY);
    if (!sid || sid.length < 8) {
      sid =
        "sess-" +
        Math.random().toString(36).slice(2, 10) +
        Date.now().toString(36).slice(-4);
      localStorage.setItem(SID_KEY, sid);
    }
    return sid;
  }

  // ========== 聊天历史持久化 ==========
  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
    } catch (_) {
      return [];
    }
  }

  function saveHistory(msgs) {
    try {
      localStorage.setItem(HIST_KEY, JSON.stringify(msgs.slice(-30)));
    } catch (_) {}
  }

  let chatHistory = loadHistory();

  // ========== 防 XSS ==========
  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s == null ? "" : String(s);
    return div.innerHTML;
  }

  // ========== 渲染气泡 ==========
  function appendBubble(role, text, showLoading = false) {
    const wrap = document.createElement("div");
    wrap.className = "ai-bubble ai-" + role;

    const textEl = document.createElement("div");
    textEl.className = "ai-text";
    textEl.textContent = text || "";

    const srcEl = document.createElement("div");
    srcEl.className = "ai-sources";

    wrap.appendChild(textEl);
    wrap.appendChild(srcEl);
    logEl.appendChild(wrap);
    logEl.scrollTop = logEl.scrollHeight;

    let loadingEl = null;
    if (showLoading) {
      loadingEl = document.createElement("div");
      loadingEl.className = "ai-loading";
      loadingEl.innerHTML =
        '<span class="ai-loading-dot"></span>' +
        '<span class="ai-loading-dot"></span>' +
        '<span class="ai-loading-dot"></span>';
      textEl.appendChild(loadingEl);
    }

    return { wrap, textEl, srcEl, loadingEl };
  }

  function clearLoading(bubble) {
    if (bubble.loadingEl) {
      bubble.loadingEl.remove();
      bubble.loadingEl = null;
    }
  }

  function renderSources(srcEl, items) {
    if (!items || !items.length) return;
    const html =
      '<div class="ai-src-title">参考文章</div>' +
      items
        .map(
          (it, i) =>
            '<a class="ai-src-item" target="_blank" rel="noopener" ' +
            'href="/detail?article_id=' +
            encodeURIComponent(it.article_id) +
            '">[' +
            (i + 1) +
            "] " +
            escapeHtml(it.title) +
            "</a>"
        )
        .join("");
    srcEl.innerHTML = html;
  }

  // ========== SSE 帧处理 ==========
  function handleFrame(frame, bubble, turn) {
    let event = "message";
    let data = "";

    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data += line.slice(5).trim();
    }

    if (data === "[DONE]") return;

    let payload;
    try {
      payload = JSON.parse(data);
    } catch (_) {
      return;
    }

    if (event === "sources") {
      // 参考文章先出来，loading 保留（还没开始出字）
      renderSources(bubble.srcEl, payload.items);
      turn.sources = payload.items || [];
    } else if (event === "delta") {
      // 第一个 delta 到达 → 清掉 loading
      clearLoading(bubble);
      bubble.textEl.textContent += payload.text || "";
      turn.answer += payload.text || "";
      logEl.scrollTop = logEl.scrollHeight;
    } else if (event === "refused") {
      clearLoading(bubble);
      bubble.textEl.textContent = payload.text || "";
      turn.answer = payload.text || "";
    } else if (event === "error") {
      clearLoading(bubble);
      bubble.textEl.textContent = "出错了：" + (payload.message || "未知错误");
      turn.answer = bubble.textEl.textContent;
    }
  }

  // ========== 发送 ==========
  async function ask(question) {
    appendBubble("user", question);
    // AI 气泡带 loading
    const bubble = appendBubble("ai", "", true);

    sendBtn.disabled = true;
    stopBtn.disabled = false;
    controller = new AbortController();

    const turn = { sources: [], answer: "" };

    try {
      const res = await fetch("/api/ai/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          session_id: getSessionId(),
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        clearLoading(bubble);
        bubble.textEl.textContent = "服务暂时不可用（HTTP " + res.status + "）";
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        let idx;
        while ((idx = buf.indexOf("\n\n")) !== -1) {
          const frame = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          handleFrame(frame, bubble, turn);
        }
      }
      if (buf.trim()) handleFrame(buf, bubble, turn);
    } catch (err) {
      clearLoading(bubble);
      if (err.name === "AbortError") {
        bubble.textEl.textContent += "\n（已停止生成）";
        turn.answer += "\n（已停止生成）";
      } else {
        bubble.textEl.textContent = "请求失败：" + err.message;
        turn.answer = bubble.textEl.textContent;
      }
    } finally {
      clearLoading(bubble);
      sendBtn.disabled = false;
      stopBtn.disabled = true;
      controller = null;

      chatHistory.push({ role: "user", text: question });
      chatHistory.push({ role: "ai", text: turn.answer, sources: turn.sources });
      saveHistory(chatHistory);
    }
  }

  // ========== 事件绑定 ==========
  sendBtn.addEventListener("click", () => {
    const q = qEl.value.trim();
    if (!q) return;
    qEl.value = "";
    ask(q);
  });

  stopBtn.addEventListener("click", () => {
    if (controller) controller.abort();
  });

  qEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendBtn.click();
    }
  });

  // ========== 页面加载时恢复历史 ==========
  (function restore() {
    if (!chatHistory.length) return;
    for (const msg of chatHistory) {
      const { textEl, srcEl } = appendBubble(msg.role, msg.text || "");
      if (msg.sources && msg.sources.length) {
        renderSources(srcEl, msg.sources);
      }
    }
  })();
})();