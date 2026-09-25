"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const {
  EXT_ID,
  installTerminalFocusExtension,
  isTerminalFocusExtensionInstalled,
  listInstalledCopies,
  readSourceVersion,
  resolveExtensionSourceDir,
  uninstallTerminalFocusExtension,
} = require("../src/terminal-focus-extension");

const repoRoot = path.resolve(__dirname, "..");
const bundledSource = path.join(repoRoot, "extensions", "vscode");
const bundledVersion = JSON.parse(fs.readFileSync(path.join(bundledSource, "package.json"), "utf8")).version;

function makeHome(t, editors = [".vscode", ".cursor"]) {
  const homeDir = fs.mkdtempSync(path.join(os.tmpdir(), "agenthalo-terminal-focus-"));
  t.after(() => fs.rmSync(homeDir, { recursive: true, force: true }));
  for (const editor of editors) fs.mkdirSync(path.join(homeDir, editor, "extensions"), { recursive: true });
  return homeDir;
}

function writeCopy(homeDir, editor, version, manifest = { publisher: "clawd", name: "clawd-terminal-focus", version }) {
  const dir = path.join(homeDir, editor, "extensions", `${EXT_ID}-${version}`);
  fs.mkdirSync(dir, { recursive: true });
  if (manifest) fs.writeFileSync(path.join(dir, "package.json"), JSON.stringify(manifest));
  fs.writeFileSync(path.join(dir, "extension.js"), "// old copy\n");
  return dir;
}

test("the bundled source resolves next to src and carries the extension identity", () => {
  assert.equal(resolveExtensionSourceDir(path.join(repoRoot, "src")), bundledSource);
  assert.equal(readSourceVersion(bundledSource), bundledVersion);
  const packaged = path.join("/Applications/AgentHalo.app/Contents/Resources/app.asar", "src");
  assert.equal(
    resolveExtensionSourceDir(packaged),
    path.join("/Applications/AgentHalo.app/Contents/Resources/app.asar.unpacked", "extensions", "vscode")
  );
});

test("installing copies the bundled extension into each editor that exists", (t) => {
  const homeDir = makeHome(t, [".vscode"]);
  const result = installTerminalFocusExtension({ homeDir, sourceDir: bundledSource });
  const dest = path.join(homeDir, ".vscode", "extensions", `${EXT_ID}-${bundledVersion}`);

  assert.equal(result.status, "ok");
  assert.equal(result.editors, 1);
  assert.deepEqual(result.installed, [dest]);
  assert.equal(fs.existsSync(path.join(homeDir, ".cursor")), false, "a missing editor is not created");
  for (const file of ["package.json", "extension.js"]) {
    assert.deepEqual(fs.readFileSync(path.join(dest, file)), fs.readFileSync(path.join(bundledSource, file)));
  }
  assert.equal(isTerminalFocusExtensionInstalled({ homeDir }), true);

  const again = installTerminalFocusExtension({ homeDir, sourceDir: bundledSource });
  assert.deepEqual(again.installed, []);
  assert.deepEqual(again.current, [dest]);
});

test("installing replaces an older copy so an updated extension is recognised", (t) => {
  const homeDir = makeHome(t);
  const old = writeCopy(homeDir, ".vscode", "0.1.2");
  const partial = writeCopy(homeDir, ".cursor", bundledVersion, null);

  const result = installTerminalFocusExtension({ homeDir, sourceDir: bundledSource });

  assert.equal(result.status, "ok");
  assert.deepEqual(result.removed, [old]);
  assert.equal(fs.existsSync(old), false);
  assert.equal(result.installed.length, 2, "the half-written copy is rewritten");
  assert.equal(
    fs.readFileSync(path.join(partial, "extension.js"), "utf8"),
    fs.readFileSync(path.join(bundledSource, "extension.js"), "utf8")
  );
});

test("a failed install rolls back the copies it made and reports an error", (t) => {
  const homeDir = makeHome(t);
  let copies = 0;
  const failingFs = {
    ...fs,
    copyFileSync(from, to) {
      copies += 1;
      // First editor succeeds, second fails mid-way.
      if (copies > 2) throw new Error("disk full");
      return fs.copyFileSync(from, to);
    },
  };
  const result = installTerminalFocusExtension({ homeDir, sourceDir: bundledSource, fs: failingFs });

  assert.equal(result.status, "error");
  assert.match(result.message, /disk full/);
  assert.deepEqual(listInstalledCopies({ homeDir }), []);
});

test("installing without the bundled source is an error, not a silent no-op", (t) => {
  const homeDir = makeHome(t);
  const result = installTerminalFocusExtension({ homeDir, sourceDir: path.join(homeDir, "missing") });
  assert.equal(result.status, "error");
  assert.deepEqual(listInstalledCopies({ homeDir }), []);
});

test("uninstalling removes every AgentHalo copy but never another extension", (t) => {
  const homeDir = makeHome(t);
  const vscodeCopy = writeCopy(homeDir, ".vscode", "0.1.2");
  const cursorCopy = writeCopy(homeDir, ".cursor", bundledVersion);
  const foreign = writeCopy(homeDir, ".cursor", "9.9.9", { publisher: "someone", name: "else", version: "9.9.9" });
  const unrelated = path.join(homeDir, ".vscode", "extensions", "ms-python.python-2026.1.0");
  fs.mkdirSync(unrelated);

  const result = uninstallTerminalFocusExtension({ homeDir });

  assert.equal(result.status, "ok");
  assert.deepEqual(result.removed.sort(), [cursorCopy, vscodeCopy].sort());
  assert.equal(fs.existsSync(vscodeCopy), false);
  assert.equal(fs.existsSync(cursorCopy), false);
  assert.equal(fs.existsSync(foreign), true);
  assert.equal(fs.existsSync(unrelated), true);
  assert.equal(isTerminalFocusExtensionInstalled({ homeDir }), false);
});

test("uninstall reports a copy it could not delete", (t) => {
  const homeDir = makeHome(t);
  writeCopy(homeDir, ".vscode", "0.1.2");
  const result = uninstallTerminalFocusExtension({
    homeDir,
    fs: { ...fs, rmSync() { throw new Error("EPERM"); } },
  });
  assert.equal(result.status, "error");
  assert.match(result.message, /EPERM/);
});

test("only a complete copy counts as an existing install for upgrade hydration", (t) => {
  const homeDir = makeHome(t);
  assert.equal(isTerminalFocusExtensionInstalled({ homeDir }), false);
  writeCopy(homeDir, ".cursor", "0.1.2", null);
  assert.equal(isTerminalFocusExtensionInstalled({ homeDir }), false);
  writeCopy(homeDir, ".vscode", "0.1.2");
  assert.equal(isTerminalFocusExtensionInstalled({ homeDir }), true);
});
