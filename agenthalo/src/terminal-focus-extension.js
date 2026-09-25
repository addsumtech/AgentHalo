"use strict";

// ── VS Code / Cursor terminal-focus extension (opt-in) ──
//
// AgentHalo ships a tiny editor extension (extensions/vscode) that listens on
// 127.0.0.1:23456-23460 so a task click can bring the matching integrated
// terminal tab to the front. Copying it into another application's extension
// folder is a user-visible change, so it only happens through the General
// settings switch (`terminalFocusExtensionEnabled`): turning it on copies the
// extension into every editor that exists, turning it off removes the copies.
//
// Copies are recognised by their folder name (`<publisher>.<name>-<version>`,
// the layout VS Code itself uses) plus the identity in their package.json, so
// removal never touches an unrelated extension. The version in the folder name
// is read from the bundled manifest; bumping it there is what makes an updated
// copy replace an older one.

const fs = require("fs");
const os = require("os");
const path = require("path");

const EXT_PUBLISHER = "clawd";
const EXT_NAME = "clawd-terminal-focus";
const EXT_ID = `${EXT_PUBLISHER}.${EXT_NAME}`;
const EXT_FILES = ["package.json", "extension.js"];
const EDITOR_EXTENSION_ROOTS = [
  [".vscode", "extensions"],
  [".cursor", "extensions"],
];
const COPY_DIR_RE = new RegExp(`^${EXT_ID.replace(/\./g, "\\.")}-(\\d+\\.\\d+\\.\\d+)$`);

// Extension source — in dev: ../extensions/vscode/, in packaged builds the
// asar-unpacked copy (build.asarUnpack includes extensions/**/*), because an
// editor cannot read files from inside app.asar.
function resolveExtensionSourceDir(baseDir = __dirname) {
  const source = path.join(baseDir, "..", "extensions", "vscode");
  return source.replace("app.asar" + path.sep, "app.asar.unpacked" + path.sep);
}

function editorExtensionRoots(homeDir) {
  return EDITOR_EXTENSION_ROOTS.map((parts) => path.join(homeDir, ...parts));
}

function readJson(fsImpl, filePath) {
  try {
    return JSON.parse(fsImpl.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function isOwnManifest(manifest) {
  return !!manifest && manifest.publisher === EXT_PUBLISHER && manifest.name === EXT_NAME;
}

function readSourceVersion(sourceDir, fsImpl = fs) {
  const manifest = readJson(fsImpl, path.join(sourceDir, "package.json"));
  if (!isOwnManifest(manifest) || typeof manifest.version !== "string" || !/^\d+\.\d+\.\d+$/.test(manifest.version)) {
    return null;
  }
  return manifest.version;
}

// Every folder in one editor's extension root that this extension occupies.
// A folder without a readable manifest is a half-finished copy of ours (the
// name pattern is unique to it); a folder whose manifest names another
// extension is left alone.
function listCopiesInRoot(root, fsImpl) {
  let names;
  try {
    names = fsImpl.readdirSync(root);
  } catch {
    return [];
  }
  const copies = [];
  for (const name of names) {
    const match = COPY_DIR_RE.exec(name);
    if (!match) continue;
    const dir = path.join(root, name);
    const manifestPath = path.join(dir, "package.json");
    let complete = false;
    if (fsImpl.existsSync(manifestPath)) {
      const manifest = readJson(fsImpl, manifestPath);
      if (manifest && !isOwnManifest(manifest)) continue;
      complete = isOwnManifest(manifest) && fsImpl.existsSync(path.join(dir, "extension.js"));
    }
    copies.push({ root, dir, name, version: match[1], complete });
  }
  return copies;
}

function listInstalledCopies({ homeDir = os.homedir(), fs: fsImpl = fs } = {}) {
  return editorExtensionRoots(homeDir).flatMap((root) => listCopiesInRoot(root, fsImpl));
}

// Used once, on the first launch that knows about the switch: an existing
// complete copy means the user already had the old always-on behaviour, so the
// switch starts on and they keep it.
function isTerminalFocusExtensionInstalled(options = {}) {
  return listInstalledCopies(options).some((copy) => copy.complete);
}

function removeDir(fsImpl, dir) {
  fsImpl.rmSync(dir, { recursive: true, force: true });
}

// Copy the bundled extension into every editor whose extension root exists,
// replacing older AgentHalo copies. Returns { status, installed, current,
// removed, editors, message? }. On any failure the folders created by this
// call are rolled back, so a failed enable does not leave a partial install
// behind a switch that stays off.
function installTerminalFocusExtension(options = {}) {
  const fsImpl = options.fs || fs;
  const homeDir = options.homeDir || os.homedir();
  const sourceDir = options.sourceDir || resolveExtensionSourceDir();
  const result = { status: "ok", installed: [], current: [], removed: [], editors: 0 };

  const version = readSourceVersion(sourceDir, fsImpl);
  if (!version || !EXT_FILES.every((file) => fsImpl.existsSync(path.join(sourceDir, file)))) {
    return { ...result, status: "error", message: `terminal-focus extension source not found at ${sourceDir}` };
  }
  const targetName = `${EXT_ID}-${version}`;
  const created = [];

  try {
    for (const root of editorExtensionRoots(homeDir)) {
      if (!fsImpl.existsSync(root)) continue; // editor not installed
      result.editors += 1;
      const copies = listCopiesInRoot(root, fsImpl);
      const dest = path.join(root, targetName);
      const existing = copies.find((copy) => copy.name === targetName);
      if (existing && existing.complete) {
        result.current.push(dest);
      } else {
        if (existing) removeDir(fsImpl, dest);
        created.push(dest);
        fsImpl.mkdirSync(dest, { recursive: true });
        for (const file of EXT_FILES) {
          fsImpl.copyFileSync(path.join(sourceDir, file), path.join(dest, file));
        }
        result.installed.push(dest);
      }
      for (const copy of copies) {
        if (copy.name === targetName) continue;
        removeDir(fsImpl, copy.dir);
        result.removed.push(copy.dir);
      }
    }
  } catch (err) {
    for (const dir of created) {
      try { removeDir(fsImpl, dir); } catch {}
    }
    return {
      ...result,
      status: "error",
      installed: [],
      message: `terminal-focus extension install failed: ${err && err.message}`,
    };
  }
  return result;
}

// Remove every copy of the extension from both editors. Returns
// { status, removed, message? }; a copy that cannot be removed is an error so
// the switch does not report "off" while the extension is still installed.
function uninstallTerminalFocusExtension(options = {}) {
  const fsImpl = options.fs || fs;
  const removed = [];
  const failures = [];
  for (const copy of listInstalledCopies({ homeDir: options.homeDir, fs: fsImpl })) {
    try {
      removeDir(fsImpl, copy.dir);
      removed.push(copy.dir);
    } catch (err) {
      failures.push(`${copy.dir}: ${err && err.message}`);
    }
  }
  if (failures.length) {
    return {
      status: "error",
      removed,
      message: `terminal-focus extension removal failed: ${failures.join("; ")}`,
    };
  }
  return { status: "ok", removed };
}

module.exports = {
  EXT_ID,
  installTerminalFocusExtension,
  isTerminalFocusExtensionInstalled,
  listInstalledCopies,
  readSourceVersion,
  resolveExtensionSourceDir,
  uninstallTerminalFocusExtension,
};
