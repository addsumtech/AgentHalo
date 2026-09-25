const vscode = require("vscode");
const http = require("http");

// Port range for AgentHalo terminal-focus extension instances.
// Each editor window gets its own extension host → each needs a unique port.
// main.js broadcasts to all ports; only the one with the matching PID responds 200.
const PORT_BASE = 23456;
const PORT_RANGE = 5; // support up to 5 concurrent editor windows
// A focus request is `{"pids":[...]}` — a few hundred bytes. Anything larger is
// not from AgentHalo; stop reading it instead of buffering it in the editor.
const MAX_BODY_BYTES = 16 * 1024;

let server = null;
let boundPort = null;

async function focusTerminalByPids(pids) {
  for (const terminal of vscode.window.terminals) {
    const termPid = await terminal.processId;
    if (termPid && pids.includes(termPid)) {
      terminal.show(false);
      return true;
    }
  }
  return false;
}

function rejectTooLarge(req, res) {
  res.writeHead(413, { Connection: "close" });
  // Drop the connection once the answer is out so the rest of an oversized
  // body is never read.
  res.end("too large", () => req.destroy());
}

function handleRequest(req, res, focus = focusTerminalByPids) {
  if (req.method !== "POST" || req.url !== "/focus-tab") {
    res.writeHead(404);
    res.end();
    return;
  }
  const declared = Number(req.headers["content-length"]);
  if (Number.isFinite(declared) && declared > MAX_BODY_BYTES) {
    rejectTooLarge(req, res);
    return;
  }
  let body = "";
  let size = 0;
  let rejected = false;
  req.on("data", (chunk) => {
    if (rejected) return;
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      rejected = true;
      body = "";
      rejectTooLarge(req, res);
      return;
    }
    body += chunk;
  });
  req.on("end", () => {
    if (rejected) return;
    try {
      const data = JSON.parse(body);
      const pids = Array.isArray(data.pids) ? data.pids.filter(Number.isFinite) : [];
      if (pids.length) {
        Promise.resolve()
          .then(() => focus(pids))
          .then((found) => {
            res.writeHead(found ? 200 : 404);
            res.end(found ? "ok" : "not found");
          }, () => {
            res.writeHead(500);
            res.end("focus failed");
          });
      } else {
        res.writeHead(400);
        res.end("no pids");
      }
    } catch {
      res.writeHead(400);
      res.end("bad json");
    }
  });
}

function tryListen(port, maxPort) {
  if (port > maxPort) {
    console.log("AgentHalo terminal-focus: all ports in use, HTTP server disabled");
    return;
  }

  server = http.createServer((req, res) => handleRequest(req, res));

  server.on("error", (err) => {
    if (err.code === "EADDRINUSE") {
      server = null;
      tryListen(port + 1, maxPort);
    }
  });

  server.listen(port, "127.0.0.1", () => {
    boundPort = port;
    console.log(`AgentHalo terminal-focus: listening on 127.0.0.1:${port}`);
  });
}

function activate(context) {
  tryListen(PORT_BASE, PORT_BASE + PORT_RANGE - 1);

  // URI handler kept as fallback for manual testing:
  // vscode://clawd.clawd-terminal-focus?pids=1234,5678
  context.subscriptions.push(
    vscode.window.registerUriHandler({
      async handleUri(uri) {
        const params = new URLSearchParams(uri.query);
        const raw = params.get("pids") || params.get("pid") || "";
        const pids = raw.split(",").map(Number).filter(Boolean);
        if (pids.length) focusTerminalByPids(pids);
      },
    })
  );
}

function deactivate() {
  if (server) {
    server.close();
    server = null;
  }
}

module.exports = { activate, deactivate, handleRequest, MAX_BODY_BYTES };
