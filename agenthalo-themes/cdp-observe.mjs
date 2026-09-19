// Send text via trusted input to an editor and sample visible button labels + URL every 500ms.
// Usage: cdp-observe.mjs <port> <match> <editorSelector> <text> <sampleMs>
const [port, match, selector, text, sampleMs = "9000"] = process.argv.slice(2);
const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const target = list.find((t) => (t.url || "").includes(match) || (t.title || "").includes(match));
if (!target) { console.error("NO_TARGET", match); process.exit(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const call = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (e) => { const r = await call("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true }); return r.result && r.result.result ? r.result.result.value : JSON.stringify(r).slice(0, 200); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const sel = JSON.stringify(selector);
const f = await ev(`(() => { const ed = document.querySelector(${sel}); if (!ed) return "NO_EDITOR"; ed.focus(); return "ok"; })()`);
if (f !== "ok") { console.log(f); process.exit(3); }
await call("Input.dispatchKeyEvent", { type: "keyDown", key: "a", code: "KeyA", modifiers: 4, windowsVirtualKeyCode: 65, commands: ["selectAll"] });
await call("Input.dispatchKeyEvent", { type: "keyUp", key: "a", code: "KeyA", modifiers: 4, windowsVirtualKeyCode: 65 });
await call("Input.dispatchKeyEvent", { type: "keyDown", key: "Backspace", code: "Backspace", windowsVirtualKeyCode: 8 });
await call("Input.dispatchKeyEvent", { type: "keyUp", key: "Backspace", code: "Backspace", windowsVirtualKeyCode: 8 });
await call("Input.insertText", { text }); await sleep(400);
await call("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: "\r", unmodifiedText: "\r" });
await call("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
const t0 = Date.now(); const samples = [];
while (Date.now() - t0 < Number(sampleMs)) {
  const s = await ev(`JSON.stringify({url: location.href.slice(0, 90), btns: Array.from(document.querySelectorAll("button,[role=button]")).filter(b => b.getBoundingClientRect().width > 0).map(b => (b.getAttribute("aria-label") || b.getAttribute("title") || (b.innerText || "").trim()).slice(0, 10)).filter(Boolean).slice(-8), stream: document.querySelectorAll("[class*=stream], [class*=loading], [class*=typing], [class*=generating]").length, editor: ((document.querySelector(${sel}) || {}).innerText || "").trim().slice(0, 20)})`);
  samples.push({ t: Date.now() - t0, ...JSON.parse(s) }); await sleep(500);
}
console.log(JSON.stringify(samples, null, 0));
ws.close();
