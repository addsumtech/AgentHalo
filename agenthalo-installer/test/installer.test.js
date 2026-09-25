"use strict";

// Everything runs against loopback servers and temporary directories; nothing
// here touches the network, /Applications or a real AgentHalo process.

const { describe, it, before, after } = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const {
  InstallError,
  download,
  installApp,
  main,
  sha256File,
  swapIntoPlace,
} = require("../bin/agenthalo");

const VERSION = require("../package.json").version;
const BIN = path.join(__dirname, "..", "bin", "agenthalo.js");

function tempDir(t, label = "agenthalo-installer-test-") {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), label));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

// A stand-in .app bundle: only the marker file matters to these tests.
function fakeApp(dir, marker) {
  fs.mkdirSync(path.join(dir, "Contents", "MacOS"), { recursive: true });
  fs.writeFileSync(path.join(dir, "Contents", "marker"), marker);
  return dir;
}

const markerOf = (app) => fs.readFileSync(path.join(app, "Contents", "marker"), "utf8");
const siblings = (dir) => fs.readdirSync(dir).filter((name) => name.startsWith("."));
const copyTree = (from, to) => fs.cpSync(from, to, { recursive: true });

describe("download", () => {
  const payload = crypto.randomBytes(256 * 1024);
  let server;
  let base;

  before(async () => {
    server = http.createServer((req, res) => {
      if (req.url === "/ok.zip") {
        res.writeHead(200, { "content-length": payload.length });
        res.end(payload);
      } else if (req.url === "/stall.zip") {
        // Headers and a first chunk, then silence: a dead mirror or proxy.
        res.writeHead(200, { "content-length": payload.length });
        res.write(payload.subarray(0, 1024));
      } else {
        res.writeHead(404);
        res.end();
      }
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    base = `http://127.0.0.1:${server.address().port}`;
  });

  after(() => {
    server.closeAllConnections();
    server.close();
  });

  const quiet = { interactive: false, write: () => {} };

  it("streams the archive to disk and hashes it without reading it whole", async (t) => {
    const dest = path.join(tempDir(t), "ok.zip");
    await download(`${base}/ok.zip`, dest, quiet);
    assert.ok(fs.readFileSync(dest).equals(payload));
    assert.equal(await sha256File(dest), crypto.createHash("sha256").update(payload).digest("hex"));
  });

  it("reports a missing release as an install error", async (t) => {
    const dest = path.join(tempDir(t), "missing.zip");
    await assert.rejects(download(`${base}/missing.zip`, dest, quiet), (err) => {
      assert.ok(err instanceof InstallError);
      assert.match(err.message, /HTTP 404/);
      return true;
    });
  });

  it("gives up on a stalled download instead of hanging", { timeout: 10000 }, async (t) => {
    const dest = path.join(tempDir(t), "stall.zip");
    const started = Date.now();
    await assert.rejects(download(`${base}/stall.zip`, dest, { ...quiet, stallTimeoutMs: 300 }), (err) => {
      assert.ok(err instanceof InstallError);
      assert.match(err.message, /没有进展/);
      return true;
    });
    assert.ok(Date.now() - started < 5000);
  });
});

describe("app replacement", () => {
  it("swaps the new app into place and removes the old copy", (t) => {
    const dir = tempDir(t);
    const target = fakeApp(path.join(dir, "AgentHalo.app"), "old");
    const incoming = fakeApp(path.join(dir, ".incoming"), "new");
    swapIntoPlace(incoming, target);
    assert.equal(markerOf(target), "new");
    assert.deepEqual(siblings(dir), []);
  });

  it("puts the old app back when the new one cannot be moved into place", (t) => {
    const dir = tempDir(t);
    const target = fakeApp(path.join(dir, "AgentHalo.app"), "old");
    const incoming = fakeApp(path.join(dir, ".incoming"), "new");
    const flaky = {
      ...fs,
      renameSync(from, to) {
        if (from === incoming) throw Object.assign(new Error("EIO"), { code: "EIO" });
        return fs.renameSync(from, to);
      },
    };
    assert.throws(() => swapIntoPlace(incoming, target, flaky), /EIO/);
    assert.equal(markerOf(target), "old");
    assert.deepEqual(siblings(dir), [".incoming"]);
  });

  it("installs next to the target first and replaces the app only once it has quit", (t) => {
    const dir = tempDir(t);
    const staged = fakeApp(path.join(tempDir(t), "AgentHalo.app"), "new");
    const target = fakeApp(path.join(dir, "AgentHalo.app"), "old");
    const events = [];
    installApp(staged, target, {
      copy: (from, to) => {
        events.push(`copy:${path.dirname(to) === dir}`);
        copyTree(from, to);
      },
      quit: () => events.push("quit"),
      isRunning: () => false,
    });
    assert.deepEqual(events, ["copy:true", "quit"]);
    assert.equal(markerOf(target), "new");
    assert.deepEqual(siblings(dir), []);
  });

  it("leaves a still-running app installed and untouched", (t) => {
    const dir = tempDir(t);
    const staged = fakeApp(path.join(tempDir(t), "AgentHalo.app"), "new");
    const target = fakeApp(path.join(dir, "AgentHalo.app"), "old");
    assert.throws(
      () => installApp(staged, target, { copy: copyTree, quit: () => {}, isRunning: () => true }),
      (err) => err instanceof InstallError && /还在运行/.test(err.message)
    );
    assert.equal(markerOf(target), "old");
    assert.deepEqual(siblings(dir), []);
  });

  it("does not touch the installed app when copying the new one fails", (t) => {
    const dir = tempDir(t);
    const staged = fakeApp(path.join(tempDir(t), "AgentHalo.app"), "new");
    const target = fakeApp(path.join(dir, "AgentHalo.app"), "old");
    let quitCalled = false;
    assert.throws(() => installApp(staged, target, {
      copy: (from, to) => {
        fs.mkdirSync(to);
        fs.writeFileSync(path.join(to, "partial"), "x");
        throw new Error("disk full");
      },
      quit: () => { quitCalled = true; },
      isRunning: () => false,
    }), /disk full/);
    assert.equal(quitCalled, false);
    assert.equal(markerOf(target), "old");
    assert.deepEqual(siblings(dir), []);
  });
});

describe("main", () => {
  const archive = crypto.randomBytes(64 * 1024);
  const asset = `AgentHalo-${VERSION}-arm64.zip`;
  const goodSum = crypto.createHash("sha256").update(archive).digest("hex");
  let server;
  let base;

  before(async () => {
    server = http.createServer((req, res) => {
      if (req.url === `/good/${asset}`) {
        res.writeHead(200, { "content-length": archive.length });
        res.end(archive);
      } else {
        res.writeHead(404);
        res.end();
      }
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    base = `http://127.0.0.1:${server.address().port}`;
  });

  after(() => {
    server.closeAllConnections();
    server.close();
  });

  function run(t, overrides = {}) {
    const tmpDir = tempDir(t);
    const installDir = path.join(tempDir(t), "Applications");
    const promise = main({
      platform: "darwin",
      arch: "arm64",
      argv: ["node", BIN, "--dir", installDir],
      tmpDir,
      base: `${base}/good`,
      checksums: { [asset]: goodSum },
      download: { interactive: false, write: () => {} },
      extract: (_zip, into) => fakeApp(path.join(into, "AgentHalo.app"), "new"),
      install: { copy: copyTree, quit: () => {}, isRunning: () => false },
      skipLaunch: true,
      ...overrides,
    });
    return { promise, tmpDir, installDir };
  }

  it("installs and removes its temporary directory", async (t) => {
    const { promise, tmpDir, installDir } = run(t);
    const target = await promise;
    assert.equal(target, path.join(installDir, "AgentHalo.app"));
    assert.equal(markerOf(target), "new");
    assert.deepEqual(fs.readdirSync(tmpDir), []);
  });

  for (const [label, overridesFor, pattern] of [
    ["a failed download", () => ({ base: "http://127.0.0.1:1" }), /./],
    ["a missing release", () => ({ base: `${base}/missing` }), /HTTP 404/],
    ["a checksum mismatch", () => ({ checksums: { [asset]: "0".repeat(64) } }), /校验和不匹配/],
    ["an archive without the app", () => ({ extract: () => {} }), /没有找到 AgentHalo\.app/],
    ["a still-running app", (installDir) => {
      fakeApp(path.join(installDir, "AgentHalo.app"), "old");
      return { install: { copy: copyTree, quit: () => {}, isRunning: () => true } };
    }, /还在运行/],
  ]) {
    it(`removes its temporary directory after ${label}`, async (t) => {
      const installDir = path.join(tempDir(t), "Applications");
      const { promise, tmpDir } = run(t, {
        argv: ["node", BIN, "--dir", installDir],
        ...overridesFor(installDir),
      });
      await assert.rejects(promise, pattern);
      assert.deepEqual(fs.readdirSync(tmpDir), []);
      if (fs.existsSync(installDir)) assert.deepEqual(siblings(installDir), []);
    });
  }

  it("removes its temporary directory when interrupted mid-download", { skip: process.platform === "win32", timeout: 15000 }, async (t) => {
    const tmp = tempDir(t);
    // A child process installing from a server that never finishes the body.
    const script = `
      const http = require("node:http");
      const { main } = require(${JSON.stringify(BIN)});
      const server = http.createServer((req, res) => {
        res.writeHead(200, { "content-length": "1000000" });
        res.write(Buffer.alloc(16));
      });
      server.listen(0, "127.0.0.1", () => {
        main({
          platform: "darwin",
          arch: "arm64",
          tmpDir: ${JSON.stringify(tmp)},
          base: "http://127.0.0.1:" + server.address().port,
          checksums: { ${JSON.stringify(asset)}: "unused" },
          download: { interactive: false, write() {} },
        }).catch(() => {});
      });
    `;
    const child = require("node:child_process").spawn(process.execPath, ["-e", script], { stdio: "ignore" });
    const exited = new Promise((resolve) => child.on("exit", (code, signal) => resolve({ code, signal })));
    for (let i = 0; i < 100 && fs.readdirSync(tmp).length === 0; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    assert.equal(fs.readdirSync(tmp).length, 1, "the install should have created its work directory");
    child.kill("SIGINT");
    assert.deepEqual(await exited, { code: null, signal: "SIGINT" });
    assert.deepEqual(fs.readdirSync(tmp), []);
  });

  it("fails before creating anything on other platforms", { skip: process.platform === "darwin" }, (t) => {
    const tmp = tempDir(t);
    const result = spawnSync(process.execPath, [BIN], {
      encoding: "utf8",
      env: { ...process.env, TMPDIR: tmp, TMP: tmp, TEMP: tmp },
    });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /当前只提供 macOS 版本/);
    assert.deepEqual(fs.readdirSync(tmp), []);
  });
});
