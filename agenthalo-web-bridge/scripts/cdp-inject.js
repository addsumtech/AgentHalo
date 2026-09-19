(() => {
  globalThis.__clawdEvents = [];
  globalThis.__clawdSendResults = [];
  globalThis.__clawdWebBridgeSend = (body) => {
    globalThis.__clawdEvents.push({ t: Date.now(), state: body.state, event: body.event, title: body.session_title, cwd: body.cwd, sid: body.session_id });
    try {
      return fetch("http://127.0.0.1:23333/state", { method: "POST", mode: "no-cors", headers: { "content-type": "text/plain" }, body: JSON.stringify(body) })
        .then((r) => { const o = { ok: true, type: r.type, status: r.status }; globalThis.__clawdSendResults.push(o); return o; })
        .catch((e) => { const o = { ok: false, err: String(e) }; globalThis.__clawdSendResults.push(o); return o; });
    } catch (e) { const o = { ok: false, err: String(e) }; globalThis.__clawdSendResults.push(o); return o; }
  };
// AgentHalo custom agent IDs registered in AgentHalo (Settings → Agents).
// These must match the `customApplications[].id` entries in
// ~/Library/Application Support/AgentHalo/agenthalo-prefs.json.
// AgentHalo custom agent IDs registered in AgentHalo (Settings → Agents).
// These must match the `customApplications[].id` entries in
// ~/Library/Application Support/AgentHalo/agenthalo-prefs.json.
// Regenerate with: node agenthalo-web-bridge/scripts/register.js (from the repo root)
const CLAWD_WEB_BRIDGE_CONFIG = {
  agents: {
    "claude-web": "custom-claude-web-b9c9490d2d4d",
    "chatgpt-web": "custom-chatgpt-web-0b029b5066a4",
    "gemini-web": "custom-gemini-web-9aaefb55d605"
  },
  // AgentHalo binds 127.0.0.1 and picks the first free port in this range.
  ports: [23333, 23334, 23335, 23336, 23337],
  // How long a generation must run before "thinking" becomes "working".
  workingAfterMs: 2500,
  // Heartbeat while generating (AgentHalo idles a "working" session after 5 min of silence).
  heartbeatMs: 45000,
  // DOM poll interval (a MutationObserver also triggers checks).
  pollMs: 500
};
if (typeof globalThis !== "undefined") globalThis.CLAWD_WEB_BRIDGE_CONFIG = CLAWD_WEB_BRIDGE_CONFIG;
// AgentHalo Web Bridge — content script.
// Watches a web chat page (claude.ai / ChatGPT / Gemini) and reports lifecycle
// states to AgentHalo through the background service worker.
//
// One browser tab == one AgentHalo session (like one terminal). The session id is a
// random token kept in sessionStorage so it survives in-tab navigation
// (e.g. claude.ai/new → /chat/<id>) but not tab duplication.
(() => {
  const CFG = globalThis.CLAWD_WEB_BRIDGE_CONFIG;
  if (!CFG) return;
  if (globalThis.__clawdWebBridgeLoaded) return;
  globalThis.__clawdWebBridgeLoaded = true;

  const STOP_LABELS = [
    "Stop response", "Stop generating", "Stop streaming", "Stop",
    "停止回复", "停止响应", "停止回答", "停止生成", "停止"
  ];

  function buttonWithLabel(labels, exact = true) {
    const buttons = document.querySelectorAll("button[aria-label]");
    for (const b of buttons) {
      const al = (b.getAttribute("aria-label") || "").trim();
      if (!al) continue;
      if (exact ? labels.includes(al) : labels.some((l) => al.includes(l))) {
        const r = b.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) return b;
      }
    }
    return null;
  }

  const SITES = [
    {
      key: "claude-web",
      match: (h) => /(^|\.)claude\.ai$/.test(h),
      // claude.ai/code is Claude Code on the web (different UI) — not handled here.
      skip: () => location.pathname.startsWith("/code"),
      isGenerating: () =>
        !!document.querySelector('[data-is-streaming="true"]')
        || !!buttonWithLabel(["Stop response", "停止回复", "停止响应"])
        || (!document.querySelector('[data-testid="chat-input-send"]') && !!buttonWithLabel(STOP_LABELS, false)),
      title: () => document.title.replace(/\s*[-|–—]\s*Claude\s*$/i, "").trim(),
    },
    {
      key: "chatgpt-web",
      match: (h) => /(^|\.)(chatgpt\.com|chat\.openai\.com)$/.test(h),
      skip: () => /^\/(codex|codex\/)/.test(location.pathname),
      isGenerating: () =>
        !!document.querySelector('button[data-testid="stop-button"]')
        || !!document.querySelector('#composer-submit-button[aria-label*="停止"], #composer-submit-button[aria-label*="Stop"]'),
      title: () => document.title.replace(/\s*[-|–—]\s*ChatGPT\s*$/i, "").trim(),
    },
    {
      key: "gemini-web",
      match: (h) => /(^|\.)gemini\.google\.com$/.test(h),
      skip: () => false,
      isGenerating: () => {
        const icons = document.querySelectorAll(".send-button mat-icon, button.send-button mat-icon, .send-button-container mat-icon");
        for (const i of icons) {
          const name = (i.getAttribute("data-mat-icon-name") || i.getAttribute("fonticon") || i.textContent || "").trim().toLowerCase();
          if (name === "stop") return true;
        }
        return !!buttonWithLabel(["停止回答", "Stop response", "Stop generating"]);
      },
      title: () => document.title.replace(/\s*[-|–—]\s*(Google\s+)?Gemini\s*$/i, "").trim(),
    },
  ];

  const site = SITES.find((s) => s.match(location.hostname));
  if (!site) return;
  const agentId = CFG.agents[site.key];
  if (!agentId) return;

  function sessionToken() {
    const k = "__clawd_web_bridge_session";
    let t = null;
    try { t = sessionStorage.getItem(k); } catch {}
    if (!t) {
      t = Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
      try { sessionStorage.setItem(k, t); } catch {}
    }
    return t;
  }
  const sessionId = `tab-${sessionToken()}`;

  function conversationUrl() {
    return location.origin + location.pathname;
  }

  function payload(state, event, extra = {}) {
    const t = (site.title() || "").slice(0, 120);
    return Object.assign({
      agent_id: agentId,
      session_id: sessionId,
      state,
      event,
      platform: "webui",
      cwd: conversationUrl(),
      ...(t ? { session_title: t } : {}),
    }, extra);
  }

  // Transport: background service worker (has host permission for 127.0.0.1).
  // A test shim may replace this via globalThis.__clawdWebBridgeSend.
  function send(body) {
    if (typeof globalThis.__clawdWebBridgeSend === "function") {
      return Promise.resolve(globalThis.__clawdWebBridgeSend(body));
    }
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage({ type: "clawd-state", body }, (res) => {
          void chrome.runtime.lastError; // extension reloaded etc. — fail open
          resolve(res || { ok: false });
        });
      } catch {
        resolve({ ok: false });
      }
    });
  }

  // State machine per tab.
  let phase = "idle";            // idle | generating | done
  let generatingSince = 0;
  let workingSent = false;
  let lastHeartbeat = 0;
  let lastTitle = null;
  let checkScheduled = false;

  function onGenerationStart() {
    phase = "generating";
    generatingSince = Date.now();
    workingSent = false;
    lastHeartbeat = Date.now();
    send(payload("thinking", "UserPromptSubmit"));
  }

  function onGenerationTick() {
    const now = Date.now();
    if (!workingSent && now - generatingSince >= CFG.workingAfterMs) {
      workingSent = true;
      lastHeartbeat = now;
      send(payload("working", "PreToolUse", { tool_name: "generate" }));
      return;
    }
    if (workingSent && now - lastHeartbeat >= CFG.heartbeatMs) {
      lastHeartbeat = now;
      send(payload("working", "PostToolUse", { tool_name: "generate" }));
    }
  }

  function onGenerationEnd() {
    phase = "done";
    // Turn completed → "attention" (your turn). AgentHalo plays the happy animation.
    send(payload("attention", "Stop"));
  }

  function check() {
    checkScheduled = false;
    if (site.skip()) return;
    let generating = false;
    try { generating = !!site.isGenerating(); } catch { generating = false; }
    if (generating && phase !== "generating") onGenerationStart();
    else if (generating && phase === "generating") onGenerationTick();
    else if (!generating && phase === "generating") onGenerationEnd();
    // Title changes after the first reply (auto-naming): refresh the card label.
    if (phase === "done") {
      const t = site.title();
      if (t && t !== lastTitle) {
        lastTitle = t;
        // preserve_state keeps the card in "attention"; PostToolUse never opens a bubble.
        send(payload("attention", "PostToolUse", { preserve_state: true }));
      }
    } else if (phase === "generating") {
      lastTitle = site.title();
    }
  }

  function scheduleCheck() {
    if (checkScheduled) return;
    checkScheduled = true;
    setTimeout(check, 120);
  }

  const observer = new MutationObserver(scheduleCheck);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["aria-label", "data-testid", "data-is-streaming", "data-mat-icon-name", "fonticon"] });
  setInterval(check, CFG.pollMs);

  // Tab is going away (close / navigate to another origin) → end session.
  // Background also ends it on tabs.onRemoved; this covers same-tab navigation away.
  window.addEventListener("pagehide", (ev) => {
    if (ev.persisted) return; // bfcache — tab still alive
    if (phase === "idle") return;
    send(payload("idle", "SessionEnd"));
  });

  // Expose for the CDP test harness.
  globalThis.__clawdWebBridge = { get phase() { return phase; }, sessionId, agentId, siteKey: site.key, check };
})();
  return "injected:" + (globalThis.__clawdWebBridge ? globalThis.__clawdWebBridge.siteKey + "/" + globalThis.__clawdWebBridge.sessionId : "no-site"); })()
