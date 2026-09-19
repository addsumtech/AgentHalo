#!/usr/bin/env node
// Type a message into a chat composer inside an Electron/Chromium app and press Enter
// using trusted CDP input events (synthetic DOM events are often ignored by editors).
// Usage: cdp-send.mjs <port> <urlOrTitleSubstring> <editorSelector> <text> [waitMs]
const [port, match, selector, text, waitMs = "1500"] = process.argv.slice(2);
const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const target = list.find((t) => (t.url || "").includes(match) || (t.title || "").includes(match));
if (!target) { console.error("NO_TARGET", match); process.exit(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const call = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evalJs = async (expression) => { const r = await call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }); return r.result && r.result.result ? r.result.result.value : r; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const sel = JSON.stringify(selector);
const focused = await evalJs(`(() => { const ed = document.querySelector(${sel}); if (!ed) return "NO_EDITOR"; ed.focus(); const r = document.createRange(); r.selectNodeContents(ed); const s = getSelection(); s.removeAllRanges(); s.addRange(r); return "focused"; })()`);
if (focused !== "focused") { console.log(focused); process.exit(3); }
// select-all + delete via trusted keys, then type text as trusted input
await call("Input.dispatchKeyEvent", { type: "keyDown", key: "a", code: "KeyA", modifiers: 4, windowsVirtualKeyCode: 65, commands: ["selectAll"] });
await call("Input.dispatchKeyEvent", { type: "keyUp", key: "a", code: "KeyA", modifiers: 4, windowsVirtualKeyCode: 65 });
await call("Input.dispatchKeyEvent", { type: "keyDown", key: "Backspace", code: "Backspace", windowsVirtualKeyCode: 8 });
await call("Input.dispatchKeyEvent", { type: "keyUp", key: "Backspace", code: "Backspace", windowsVirtualKeyCode: 8 });
await call("Input.insertText", { text });
await sleep(400);
const before = await evalJs(`(document.querySelector(${sel}) || {}).innerText || ""`);
await call("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
await call("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
await sleep(Number(waitMs));
const after = await evalJs(`(document.querySelector(${sel}) || {}).innerText || ""`);
const buttons = await evalJs(`JSON.stringify(Array.from(document.querySelectorAll("button")).filter(b => b.getBoundingClientRect().width > 0).map(b => (b.getAttribute("aria-label") || (b.innerText || "").trim()).slice(0, 12)).filter(Boolean).slice(-12))`);
console.log(JSON.stringify({ typed: before.trim().slice(0, 40), afterEnter: after.trim().slice(0, 40), sent: !after.includes(text), buttons: JSON.parse(buttons), url: target.url.slice(0, 100) }));
ws.close();
