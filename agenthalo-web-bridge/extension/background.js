// AgentHalo Web Bridge — background service worker.
// Receives state events from content scripts and POSTs them to the local
// AgentHalo HTTP server (custom HTTP agent contract, docs/guides/custom-agent-http.md).
importScripts("config.js", "conversation-url.js");

const CFG = globalThis.CLAWD_WEB_BRIDGE_CONFIG || { agents: {}, ports: [23333, 23334, 23335, 23336, 23337] };
if (!CFG.agents) CFG.agents = {};
const SERVER_HEADER = "x-clawd-server";
const SERVER_ID = "clawd-on-desk";

let cachedPort = null;
let lastProbeAt = 0;
const PROBE_BACKOFF_MS = 5000;

// The manifest's content-script origins, each with the site key content.js
// uses for it. A message from any other sender is ignored.
const SITE_KEYS_BY_ORIGIN = {
  "https://claude.ai": "claude-web",
  "https://chatgpt.com": "chatgpt-web",
  "https://chat.openai.com": "chatgpt-web",
  "https://gemini.google.com": "gemini-web",
};
// Exactly what content.js reports. The forwarded body is rebuilt from these
// fields, so a compromised page renderer cannot smuggle process metadata
// (source_pid, pid_chain, editor, ...) or another agent's ID into AgentHalo.
const WEB_STATES = new Set(["thinking", "working", "attention", "idle"]);
const WEB_EVENTS = new Set(["UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"]);

// A tab owns only its currently displayed conversation. Persist pending ends
// across service-worker and browser restarts so a missed close is recoverable.
const tabSessions = new Map();
const pendingEnds = new Map();
const restored = Promise.all([
  chrome.storage.local.get(["tabSessions", "pendingEnds"]),
  chrome.storage.session.get("tabSessions"),
]).then(([saved, legacy]) => {
  for (const [id, session] of Object.entries(saved.tabSessions || legacy.tabSessions || {})) {
    tabSessions.set(Number(id), session);
  }
  for (const body of saved.pendingEnds || []) pendingEnds.set(endKey(body), body);
});
let eventQueue = Promise.resolve();

function queueEvent(run) {
  const pending = eventQueue.then(() => restored).then(run);
  eventQueue = pending.catch((err) => console.warn("AgentHalo bridge:", err));
  return pending;
}

function persistSessions() {
  const data = { tabSessions: Object.fromEntries(tabSessions) };
  return Promise.all([
    chrome.storage.session.set(data),
    chrome.storage.local.set({ ...data, pendingEnds: [...pendingEnds.values()] }),
  ]);
}

function endKey(s) { return `${s.agent_id}:${s.session_id}`; }

function rememberEnd(s) {
  const body = { agent_id: s.agent_id, session_id: s.session_id, state: "idle", event: "SessionEnd", platform: "webui" };
  pendingEnds.set(endKey(body), body);
}

async function flushPendingEnds() {
  for (const [key, body] of pendingEnds) {
    const result = await postState(body);
    if (!result.ok && result.status !== 204) break;
    pendingEnds.delete(key);
    await persistSessions();
  }
}

function conversationUrl(value) {
  return clawdConversationUrl(value);
}

async function reconcileTabs() {
  // A successful tab inventory is positive evidence of closure or navigation.
  // A browser API failure is not, so never clear live state on query failure.
  let tabs;
  try { tabs = await chrome.tabs.query({}); }
  catch { return; }
  const live = new Map(tabs.map((tab) => [tab.id, tab]));
  for (const [id, session] of tabSessions) {
    const tab = live.get(id);
    if (!tab || (tab.url && session.cwd && conversationUrl(tab.url) !== conversationUrl(session.cwd))) {
      rememberEnd(session);
      tabSessions.delete(id);
    }
  }
  await persistSessions();
  await flushPendingEnds();
}

async function probePort(port) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 800);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/state`, { method: "GET", signal: ctl.signal, cache: "no-store" });
    if (!res.ok) return false;
    if (res.headers.get(SERVER_HEADER) !== SERVER_ID) return false;
    const body = await res.json().catch(() => null);
    return !!body && body.app === SERVER_ID;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

async function refreshAgentIds(port) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 800);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/web-bridge`, { method: "GET", signal: ctl.signal, cache: "no-store" });
    if (!res.ok || res.headers.get(SERVER_HEADER) !== SERVER_ID) return;
    const body = await res.json().catch(() => null);
    if (!body || !body.agents || typeof body.agents !== "object") return;
    CFG.agents = { ...(CFG.agents || {}), ...body.agents };
  } catch {
    // Discovery is optional; config.js IDs remain as fallback.
  } finally {
    clearTimeout(timer);
  }
}

async function resolveAgentId(siteKey) {
  if (siteKey && CFG.agents && CFG.agents[siteKey]) return CFG.agents[siteKey];
  const port = await discoverPort();
  if (!port) return "";
  await refreshAgentIds(port);
  return (siteKey && CFG.agents && CFG.agents[siteKey]) || "";
}

async function discoverPort(force = false) {
  if (cachedPort && !force) return cachedPort;
  const now = Date.now();
  if (!force && now - lastProbeAt < PROBE_BACKOFF_MS) return null;
  lastProbeAt = now;
  for (const port of CFG.ports) {
    if (await probePort(port)) {
      cachedPort = port;
      await refreshAgentIds(port);
      return port;
    }
  }
  cachedPort = null;
  return null;
}

async function postState(body, { retry = true } = {}) {
  const port = await discoverPort();
  if (!port) return { ok: false, reason: "clawd-offline" };
  try {
    const res = await fetch(`http://127.0.0.1:${port}/state`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store"
    });
    if (res.headers.get(SERVER_HEADER) !== SERVER_ID) {
      cachedPort = null;
      if (retry) { await discoverPort(true); return postState(body, { retry: false }); }
      return { ok: false, reason: "not-clawd" };
    }
    // 200 = accepted, 204 = agent disabled/unregistered (still a valid AgentHalo reply)
    return { ok: res.status === 200, status: res.status };
  } catch (err) {
    cachedPort = null;
    if (retry) { await discoverPort(true); return postState(body, { retry: false }); }
    return { ok: false, reason: String(err && err.message || err) };
  }
}

function senderSiteKey(sender) {
  if (!sender || !sender.tab || sender.id !== chrome.runtime.id) return null;
  let origin = sender.origin;
  if (!origin && sender.url) {
    try { origin = new URL(sender.url).origin; } catch { origin = null; }
  }
  return Object.prototype.hasOwnProperty.call(SITE_KEYS_BY_ORIGIN, origin) ? SITE_KEYS_BY_ORIGIN[origin] : null;
}

function pickStateFields(raw) {
  if (!raw || typeof raw !== "object") return null;
  if (typeof raw.session_id !== "string" || !raw.session_id || raw.session_id.length > 512) return null;
  if (!WEB_STATES.has(raw.state) || !WEB_EVENTS.has(raw.event)) return null;
  const body = { session_id: raw.session_id, state: raw.state, event: raw.event, platform: "webui" };
  if (typeof raw.cwd === "string" && raw.cwd && raw.cwd.length <= 2048) body.cwd = raw.cwd;
  if (typeof raw.session_title === "string" && raw.session_title) body.session_title = raw.session_title.slice(0, 120);
  if (typeof raw.tool_name === "string" && raw.tool_name && raw.tool_name.length <= 64) body.tool_name = raw.tool_name;
  if (raw.preserve_state === true) body.preserve_state = true;
  return body;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.type !== "clawd-state" || !msg.body) return false;
  const tabId = sender && sender.tab ? sender.tab.id : null;
  if (tabId == null) return false;
  // The site comes from the browser-reported sender, never from the message.
  const siteKey = senderSiteKey(sender);
  if (!siteKey) return false;
  const fields = pickStateFields(msg.body);
  if (!fields) {
    sendResponse({ ok: false, reason: "invalid-message" });
    return false;
  }
  // Browser-owned tab IDs keep duplicated sessionStorage tokens independent.
  const body = { ...fields, session_id: `web-${tabId}-${fields.session_id}` };
  queueEvent(async () => {
    body.agent_id = await resolveAgentId(siteKey);
    const previous = tabSessions.get(tabId);
    if (body.event === "SessionEnd") {
      if (!previous || previous.session_id !== body.session_id
        || (previous.documentId && sender.documentId && previous.documentId !== sender.documentId)) return { ok: true };
      rememberEnd(previous);
      tabSessions.delete(tabId);
      await persistSessions();
      await flushPendingEnds();
      return { ok: true, queued: pendingEnds.has(endKey(body)) };
    }
    // A message queued by the previous document must not recreate its task
    // after this tab has already navigated elsewhere.
    if (body.cwd) {
      let current;
      try { current = await chrome.tabs.get(tabId); }
      catch { return { ok: false, reason: "tab-unavailable" }; }
      if (current.url && conversationUrl(current.url) !== conversationUrl(body.cwd)) {
        return { ok: true, ignored: true };
      }
    }
    // If the same page reopens before the end was delivered, it is live again.
    pendingEnds.delete(endKey(body));
    if (previous && previous.session_id !== body.session_id) rememberEnd(previous);
    tabSessions.set(tabId, {
      agent_id: body.agent_id,
      session_id: body.session_id,
      cwd: body.cwd,
      session_title: body.session_title,
      lastState: body.state,
      documentId: sender.documentId || null,
    });
    await persistSessions();
    await flushPendingEnds();
    return postState(body);
  }).then(sendResponse).catch((err) => sendResponse({ ok: false, reason: String(err) }));
  return true;
});

chrome.tabs.onRemoved.addListener((tabId) => {
  queueEvent(async () => {
    const session = tabSessions.get(tabId);
    if (!session) return;
    rememberEnd(session);
    tabSessions.delete(tabId);
    await persistSessions();
    await flushPendingEnds();
  });
});

chrome.tabs.onUpdated.addListener((tabId, change) => {
  if (!change.url) return;
  queueEvent(async () => {
    const session = tabSessions.get(tabId);
    if (!session || !session.cwd || conversationUrl(change.url) === conversationUrl(session.cwd)) return;
    rememberEnd(session);
    tabSessions.delete(tabId);
    await persistSessions();
    await flushPendingEnds();
  });
});

chrome.alarms.create("clawd-probe", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "clawd-probe") queueEvent(async () => {
    await discoverPort(true);
    await reconcileTabs();
  });
});
chrome.runtime.onInstalled.addListener(() => queueEvent(reconcileTabs));
chrome.runtime.onStartup.addListener(() => queueEvent(reconcileTabs));
