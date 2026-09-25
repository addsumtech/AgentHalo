"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const Module = require("node:module");
const path = require("node:path");
const test = require("node:test");

const repoRoot = path.resolve(__dirname, "..");
const extensionPath = path.join(repoRoot, "extensions", "vscode", "extension.js");

// extension.js runs inside the editor's extension host and requires the
// `vscode` API module, which does not exist under plain Node. Resolve it to a
// stub for the duration of one require.
function loadExtension() {
  const originalResolve = Module._resolveFilename;
  const stubId = "vscode-api-stub";
  require.cache[stubId] = {
    id: stubId,
    filename: stubId,
    loaded: true,
    exports: { window: { terminals: [] } },
  };
  Module._resolveFilename = function resolve(request, ...rest) {
    if (request === "vscode") return stubId;
    return originalResolve.call(this, request, ...rest);
  };
  try {
    delete require.cache[extensionPath];
    return require(extensionPath);
  } finally {
    Module._resolveFilename = originalResolve;
    delete require.cache[stubId];
  }
}

function startServer(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

function post(port, body, headers = {}) {
  return new Promise((resolve) => {
    const req = http.request({
      hostname: "127.0.0.1",
      port,
      path: "/focus-tab",
      method: "POST",
      headers,
    }, (res) => {
      let text = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => { text += chunk; });
      res.on("end", () => resolve({ status: res.statusCode, text }));
    });
    // An early 413 may close the socket while the body is still streaming.
    req.on("error", (err) => resolve({ status: null, error: err.code }));
    req.end(body);
  });
}

test("terminal-focus extension activates on startup and focuses terminal input", () => {
  const manifest = JSON.parse(fs.readFileSync(
    path.join(repoRoot, "extensions", "vscode", "package.json"),
    "utf8"
  ));
  const source = fs.readFileSync(extensionPath, "utf8");

  // The installed folder name carries this version; bump it whenever
  // extension.js changes so an updated copy replaces the old one.
  assert.equal(manifest.version, "0.1.3");
  assert.equal(manifest.publisher, "clawd");
  assert.equal(manifest.name, "clawd-terminal-focus");
  assert.ok(manifest.activationEvents.includes("onStartupFinished"));
  assert.ok(manifest.activationEvents.includes("onUri"));
  assert.match(source, /terminal\.show\(false\)/);
  assert.doesNotMatch(source, /terminal\.show\(true\)/);
});

test("terminal-focus extension answers focus requests with the matching pids", async (t) => {
  const { handleRequest } = loadExtension();
  const seen = [];
  const server = await startServer((req, res) => handleRequest(req, res, async (pids) => {
    seen.push(pids);
    return pids.includes(42);
  }));
  t.after(() => server.close());
  const { port } = server.address();

  assert.deepEqual(await post(port, JSON.stringify({ pids: [7, 42, "x"] })), { status: 200, text: "ok" });
  assert.deepEqual(await post(port, JSON.stringify({ pids: [7] })), { status: 404, text: "not found" });
  assert.deepEqual(await post(port, JSON.stringify({ pids: [] })), { status: 400, text: "no pids" });
  assert.deepEqual(await post(port, "{"), { status: 400, text: "bad json" });
  assert.deepEqual(seen, [[7, 42], [7]]);
});

test("terminal-focus extension refuses oversized request bodies", async (t) => {
  const { handleRequest, MAX_BODY_BYTES } = loadExtension();
  let focusCalls = 0;
  const server = await startServer((req, res) => handleRequest(req, res, async () => {
    focusCalls += 1;
    return true;
  }));
  t.after(() => server.close());
  const { port } = server.address();
  const oversized = JSON.stringify({ pids: [1], pad: "x".repeat(MAX_BODY_BYTES) });

  // Declared up front: refused before any of the body is read.
  const declared = await post(port, oversized, { "Content-Length": Buffer.byteLength(oversized) });
  assert.ok(declared.status === 413 || ["ECONNRESET", "EPIPE"].includes(declared.error), JSON.stringify(declared));

  // Streamed without a length: refused once the running total passes the cap.
  const streamed = await post(port, oversized, { "Transfer-Encoding": "chunked" });
  assert.ok(streamed.status === 413 || ["ECONNRESET", "EPIPE"].includes(streamed.error), JSON.stringify(streamed));

  assert.equal(focusCalls, 0);
  assert.ok(MAX_BODY_BYTES <= 64 * 1024, "a focus request is a short pid list");
});
