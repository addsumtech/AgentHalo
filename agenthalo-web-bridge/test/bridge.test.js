"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop";

// What Chrome reports for a content script in a chat tab: our own extension
// ID and the page origin (from the conversation URL when the test has one).
function contentSender(tabId, documentId, body) {
  let origin = "https://chatgpt.com";
  try { if (body && body.cwd) origin = new URL(body.cwd).origin; } catch {}
  return { id: EXTENSION_ID, tab: { id: tabId }, documentId, origin, url: `${origin}/` };
}

function worker(saved = {}) {
  const callbacks = {};
  const posts = [];
  const requests = [];
  const tabs = new Map();
  let offline = false;
  let queryFails = false;
  const context = {
    CLAWD_WEB_BRIDGE_CONFIG: { ports: [23333], agents: { "chatgpt-web": "custom-chat", "claude-web": "custom-claude" } },
    importScripts() {}, AbortController, setTimeout, clearTimeout, URL, console,
    fetch: async (_url, options) => {
      if (offline) throw new Error("offline");
      if (options.method === "POST") { requests.push(options); posts.push(JSON.parse(options.body)); }
      return { ok: true, status: 200, headers: { get: () => "clawd-on-desk" }, json: async () => ({ app: "clawd-on-desk" }) };
    },
    chrome: {
      storage: { session: { get: async () => saved, set: async (data) => Object.assign(saved, data) }, local: { get: async () => saved, set: async (data) => Object.assign(saved, data) } },
      runtime: { id: EXTENSION_ID, onMessage: { addListener: (cb) => callbacks.message = cb }, onInstalled: { addListener: (cb) => callbacks.install = cb }, onStartup: { addListener: (cb) => callbacks.startup = cb } },
      tabs: { get: async (id) => tabs.get(id) || {id}, query: async () => { if (queryFails) throw new Error("query failed"); return [...tabs.values()]; }, onRemoved: { addListener: (cb) => callbacks.remove = cb }, onUpdated: { addListener: (cb) => callbacks.update = cb } },
      alarms: { create() {}, onAlarm: { addListener: (cb) => callbacks.alarm = cb } },
    },
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../extension/conversation-url.js"), "utf8"), context);
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../extension/background.js"), "utf8"), context);
  return {
    context, posts, requests, saved, tabs,
    setOffline(value) { offline = value; },
    setQueryFails(value) { queryFails = value; },
    alarm: async () => { callbacks.alarm({ name: "clawd-probe" }); await vm.runInContext("eventQueue", vm.createContext(context)); },
    startup: async () => { callbacks.startup(); await vm.runInContext("eventQueue", vm.createContext(context)); },
    update: async (id, url) => { callbacks.update(id, {url}); await vm.runInContext("eventQueue", vm.createContext(context)); },
    message: (tabId, documentId, body) => new Promise((resolve) => callbacks.message({ type: "clawd-state", body }, contentSender(tabId, documentId, body), resolve)),
    // Delivers a message from an arbitrary sender. Returns the listener's
    // return value and every response it sent, once queued work has drained.
    rawMessage: async (msg, sender) => {
      const responses = [];
      const kept = callbacks.message(msg, sender, (value) => responses.push(value));
      await vm.runInContext("eventQueue", vm.createContext(context));
      return { kept, responses };
    },
    remove: async (tabId) => { callbacks.remove(tabId); await vm.runInContext("eventQueue", vm.createContext(context)); },
  };
}

test("duplicated browser tabs have distinct task IDs", async () => {
  const w = worker();
  const body = { agent_id: "custom-chat", session_id: "same-token", state: "thinking", event: "UserPromptSubmit" };
  await w.message(1, "d1", body);
  await w.message(2, "d2", body);
  assert.notEqual(w.posts[0].session_id, w.posts[1].session_id);
});

test("worker suspension does not lose tab-close cleanup", async () => {
  const saved = {};
  const original = worker(saved);
  await original.message(1, "doc", { agent_id: "custom-chat", session_id: "conversation", state: "thinking", event: "UserPromptSubmit" });
  const restarted = worker(saved);
  await restarted.remove(1);
  assert.equal(restarted.posts[0].event, "SessionEnd");
  assert.equal(restarted.posts[0].session_id, original.posts[0].session_id);
});

test("switching conversations ends the old one, and late unload cannot close a new document", async () => {
  const w = worker();
  const body = { agent_id: "custom-chat", session_id: "one", state: "thinking", event: "UserPromptSubmit" };
  await w.message(1, "old", body);
  await w.message(1, "new", { ...body, session_id: "two" });
  assert.equal(w.posts[1].event, "SessionEnd");
  assert.equal(w.posts[2].session_id, "web-1-two");
  await w.message(1, "old", { ...body, event: "SessionEnd" });
  assert.equal(w.posts.length, 3);
});

test("SPA navigation gives each conversation its own session", async () => {
  const posts = [];
  let generating = true;
  const loc = { origin: "https://chatgpt.com", hostname: "chatgpt.com", pathname: "/c/one" };
  const storage = new Map();
  const context = {
    CLAWD_WEB_BRIDGE_CONFIG: { agents: { "chatgpt-web": "custom-chat" }, workingAfterMs: 2500, heartbeatMs: 45000, pollMs: 1500 },
    location: loc, URL,
    document: { title: "Example", documentElement: {}, querySelector: () => generating ? {} : null, querySelectorAll: () => [] },
    sessionStorage: { getItem: (k) => storage.get(k), setItem: (k,v) => storage.set(k,v) },
    MutationObserver: class { observe() {} }, setInterval() {}, setTimeout() {},
    window: { addEventListener() {} }, __clawdWebBridgeSend: (body) => posts.push(body),
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../extension/conversation-url.js"), "utf8"), context);
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../extension/content.js"), "utf8"), context);
  context.__clawdWebBridge.check();
  const first = posts[0].session_id;
  loc.pathname = "/c/two";
  context.__clawdWebBridge.check();
  assert.equal(posts[1].event, "SessionEnd");
  assert.equal(posts[1].cwd, "https://chatgpt.com/c/one");
  assert.equal(posts[2].cwd, "https://chatgpt.com/c/two");
  assert.notEqual(posts[2].session_id, first);
  generating = false;
  context.__clawdWebBridge.check();
  assert.equal(posts.at(-1).state, "attention");
});

const liveBody = { agent_id: "custom-chat", session_id: "one", state: "thinking", event: "UserPromptSubmit", cwd: "https://chatgpt.com/c/one" };

test("offline closure survives restart and is retried until accepted", async () => {
  const saved = {};
  const w = worker(saved);
  await w.message(9, "doc", liveBody);
  w.setOffline(true);
  await w.remove(9);
  assert.equal(saved.pendingEnds.length, 1);
  assert.equal(Object.keys(saved.tabSessions).length, 0);
  const restarted = worker(saved);
  await restarted.alarm();
  assert.equal(restarted.posts.length, 1);
  assert.equal(restarted.posts[0].event, "SessionEnd");
  assert.equal(saved.pendingEnds.length, 0);
});

test("startup reconciles missing tabs but retains open conversations", async () => {
  const w = worker();
  await w.message(1, "one", liveBody);
  await w.message(2, "two", { ...liveBody, session_id: "two", cwd: "https://chatgpt.com/c/two" });
  w.tabs.set(2, { id: 2, url: "https://chatgpt.com/c/two" });
  await w.startup();
  assert.equal(w.posts.at(-1).session_id, "web-1-one");
  assert.equal(w.posts.at(-1).event, "SessionEnd");
  assert.equal(Object.keys(w.saved.tabSessions).length, 1);
});

test("navigation away ends only that tab, and URL fragments do not end a conversation", async () => {
  const w = worker();
  await w.message(1, "one", liveBody);
  await w.update(1, liveBody.cwd + "#bottom");
  assert.equal(w.posts.length, 1);
  await w.update(1, "https://example.com/");
  assert.equal(w.posts.at(-1).event, "SessionEnd");
});

test("browser inventory failure does not delete a live task", async () => {
  const w = worker();
  await w.message(1, "one", liveBody);
  w.setQueryFails(true);
  await w.alarm();
  assert.equal(w.posts.length, 1);
  assert.equal(Object.keys(w.saved.tabSessions).length, 1);
});

test("returning to the same conversation cancels its undelivered end", async () => {
  const w = worker();
  await w.message(1, "one", liveBody);
  w.setOffline(true);
  await w.remove(1);
  await w.message(1, "two", liveBody);
  assert.equal(w.saved.pendingEnds.length, 0);
  w.tabs.set(1, {id:1, url:liveBody.cwd});
  w.setOffline(false);
  await w.alarm();
  assert.equal(w.posts.filter((p) => p.event === "SessionEnd").length, 0);
});


test("late activity from an old conversation cannot recreate a closed task", async () => {
  const w = worker();
  w.tabs.set(1, { id: 1, url: liveBody.cwd });
  await w.message(1, "old", liveBody);
  w.tabs.set(1, { id: 1, url: "https://chatgpt.com/c/two" });
  await w.update(1, "https://chatgpt.com/c/two");
  const count = w.posts.length;
  await w.message(1, "old", { ...liveBody, event: "PreToolUse" });
  assert.equal(w.posts.length, count);
  assert.equal(Object.keys(w.saved.tabSessions).length, 0);
});

for (const [url, mode] of [["https://claude.ai/new", "incognito="], ["https://chatgpt.com/", "temporary-chat=true"]]) {
  test(`leaving temporary mode closes the task and ignores late events: ${url}`, async () => {
    const w = worker();
    const body = { ...liveBody, cwd: `${url}?${mode}` };
    w.tabs.set(1, {id: 1, url: body.cwd});
    await w.message(1, "doc", body);
    await w.update(1, `${body.cwd}&model=auto#bottom`);
    assert.equal(w.posts.length, 1);
    w.tabs.set(1, {id: 1, url});
    await w.update(1, url);
    assert.equal(w.posts.at(-1).event, "SessionEnd");
    await w.message(1, "doc", { ...body, event: "Stop" });
    assert.equal(w.posts.length, 2);
    assert.equal(Object.keys(w.saved.tabSessions).length, 0);
  });
}

test("only the fields content.js reports reach AgentHalo, with the site's own agent ID", async () => {
  const w = worker();
  await w.message(1, "doc", {
    ...liveBody,
    agent_id: "claude-code",
    platform: "cli",
    site_key: "claude-web",
    session_title: "T".repeat(300),
    tool_name: "generate",
    preserve_state: true,
    source_pid: 1,
    pid_chain: [1, 2],
    agent_pid: 3,
    editor: "code",
    tmux_socket: "/tmp/tmux-0/default",
    headless: true,
  });
  assert.equal(w.posts.length, 1);
  assert.deepEqual(w.posts[0], {
    session_id: "web-1-one",
    state: "thinking",
    event: "UserPromptSubmit",
    platform: "webui",
    cwd: liveBody.cwd,
    session_title: "T".repeat(120),
    tool_name: "generate",
    preserve_state: true,
    agent_id: "custom-chat",
  });
  // The local server only accepts JSON from the extension.
  assert.equal(w.requests[0].headers["content-type"], "application/json");
});

test("messages from anything but a content script in a supported chat tab are ignored", async () => {
  const w = worker();
  const msg = { type: "clawd-state", body: liveBody };
  for (const sender of [
    { ...contentSender(1, "doc", liveBody), origin: "https://evil.example", url: "https://evil.example/" },
    { ...contentSender(1, "doc", liveBody), origin: "https://claude.ai.evil.example", url: "https://claude.ai.evil.example/" },
    { ...contentSender(1, "doc", liveBody), origin: "http://chatgpt.com", url: "http://chatgpt.com/" },
    { ...contentSender(1, "doc", liveBody), id: "another-extension" },
    { ...contentSender(1, "doc", liveBody), tab: undefined },
  ]) {
    const { kept, responses } = await w.rawMessage(msg, sender);
    assert.equal(kept, false, JSON.stringify(sender));
    assert.deepEqual(responses, []);
  }
  // Chrome versions without sender.origin still carry the frame URL.
  const { responses } = await w.rawMessage(msg, { ...contentSender(2, "doc", liveBody), origin: undefined, url: liveBody.cwd });
  assert.equal(responses.length, 1);
  assert.equal(w.posts.length, 1);
  assert.equal(w.posts[0].session_id, "web-2-one");
});

test("a message outside the content script's states and events is refused", async () => {
  const w = worker();
  for (const body of [
    { ...liveBody, state: "notification" },
    { ...liveBody, event: "PermissionRequest" },
    { ...liveBody, session_id: "" },
    { ...liveBody, session_id: 7 },
  ]) {
    const { responses } = await w.rawMessage({ type: "clawd-state", body }, contentSender(1, "doc", body));
    // The worker's objects come from the vm realm; compare their JSON shape.
    assert.deepEqual(JSON.parse(JSON.stringify(responses)), [{ ok: false, reason: "invalid-message" }], JSON.stringify(body));
  }
  assert.equal(w.posts.length, 0);
});

test("accepted sender origins are exactly the manifest's content-script origins", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, "../extension/manifest.json"), "utf8"));
  const manifestOrigins = manifest.content_scripts.flatMap((script) => script.matches)
    .map((pattern) => new URL(pattern.replace(/\*$/, "")).origin);
  const accepted = Object.keys(vm.runInContext("SITE_KEYS_BY_ORIGIN", vm.createContext(worker().context)));
  assert.deepEqual([...accepted].sort(), [...new Set(manifestOrigins)].sort());
});
