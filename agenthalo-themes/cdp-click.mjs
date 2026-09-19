// Click a visible button by label (trusted mouse event) and sample the page for a while.
// Usage: cdp-click.mjs <port> <match> <buttonLabel> <sampleMs>
const [port, match, label, sampleMs = "10000"] = process.argv.slice(2);
const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
const target = list.find((t) => (t.url || "").includes(match) || (t.title || "").includes(match));
if (!target) { console.error("NO_TARGET", match); process.exit(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const call = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (e) => { const r = await call("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true }); return r.result && r.result.result ? r.result.result.value : JSON.stringify(r).slice(0, 200); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const L = JSON.stringify(label);
const rect = await ev(`(() => { const b = Array.from(document.querySelectorAll("button,[role=button]")).find(b => ((b.getAttribute("aria-label")||"") + " " + (b.innerText||"")).includes(${L}) && b.getBoundingClientRect().width > 0); if (!b) return null; const r = b.getBoundingClientRect(); return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, disabled: b.disabled}); })()`);
if (!rect) { console.log("NO_BUTTON", label); process.exit(3); }
const { x, y, disabled } = JSON.parse(rect);
await call("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
await call("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
await call("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
const t0 = Date.now(); const samples = [];
while (Date.now() - t0 < Number(sampleMs)) {
  const s = await ev(`JSON.stringify({url: location.href.slice(0, 90), btns: Array.from(document.querySelectorAll("button,[role=button]")).filter(b => b.getBoundingClientRect().width > 0).map(b => (b.getAttribute("aria-label") || b.getAttribute("title") || (b.innerText || "").trim()).slice(0, 10)).filter(Boolean).slice(-6), editor: ((document.querySelector("div[contenteditable=true]") || {}).innerText || "").trim().slice(0, 16), bodyLen: document.body.innerText.length})`);
  samples.push({ t: Date.now() - t0, ...JSON.parse(s) }); await sleep(600);
}
const after = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
console.log(JSON.stringify({ clicked: { x, y, disabled }, samples, targets: after.filter(t => t.type === "page" || t.type === "other").map(t => (t.url || "").slice(0, 90)) }));
ws.close();
