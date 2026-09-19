#!/usr/bin/env node
// Evaluate JS inside a Chromium/Electron target reachable on a remote-debugging port.
// Usage: cdp-eval.mjs <port> <urlOrTitleSubstring> <js-expression> [--list]
// Prints the JSON value of the (awaited) expression. Node >= 22 (native WebSocket).
const [port, match, expr, flag] = process.argv.slice(2);
const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
if (flag === "--list" || expr === "--list" || match === "--list" || !expr) {
  for (const t of list) console.log(t.type, "|", (t.title || "").slice(0, 60), "|", (t.url || "").slice(0, 110));
  process.exit(0);
}
const target = list.find((t) => (t.url || "").includes(match) || (t.title || "").includes(match));
if (!target) { console.error("NO_TARGET for", match); process.exit(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
const result = await new Promise((resolve) => {
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id === 1) resolve(d); };
  ws.send(JSON.stringify({ id: 1, method: "Runtime.evaluate", params: { expression: expr, awaitPromise: true, returnByValue: true } }));
});
ws.close();
if (result.result && result.result.exceptionDetails) {
  console.error("EXCEPTION", JSON.stringify(result.result.exceptionDetails).slice(0, 600));
  process.exit(3);
}
const v = result.result && result.result.result ? result.result.result.value : result;
console.log(typeof v === "string" ? v : JSON.stringify(v));
