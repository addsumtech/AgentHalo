#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

// Two shapes, because the two destinations disagree about layout.
//
//   default  a folder the user loads unpacked, so it carries the register
//            script, both READMEs and the licence next to the extension.
//   --store  a Chrome Web Store upload, which requires manifest.json at the
//            zip root and rejects anything outside the extension itself.
const storeMode = process.argv.includes("--store");
const positional = process.argv.slice(2).filter((arg) => !arg.startsWith("--"));

const root = path.resolve(__dirname, "..");
const defaultOutput = storeMode
  ? path.join(root, "../.local/releases/AgentHalo-Web-Bridge-store.zip")
  : path.join(root, "../.local/releases/AgentHalo-Web-Bridge.zip");
const output = path.resolve(positional[0] || defaultOutput);
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "agenthalo-extension-"));

// Explicit allowlist: never copy local config, credentials, logs or development
// tools. config.js is written from the example so per-machine agent ids from a
// developer checkout can never ship; the extension asks the running app for
// them through GET /web-bridge instead.
const EXTENSION_FILES = [
  "manifest.json",
  "background.js",
  "content.js",
  "conversation-url.js",
  ...[16, 32, 48, 128].map((size) => `icons/icon${size}.png`),
];

function copyExtensionInto(dir) {
  for (const file of EXTENSION_FILES) {
    const target = path.join(dir, file);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(root, "extension", file), target);
  }
  fs.copyFileSync(path.join(root, "extension/config.example.js"), path.join(dir, "config.js"));
}

try {
  const archive = path.join(temporary, "extension.zip");
  let zipRoot;
  if (storeMode) {
    const packageRoot = path.join(temporary, "store");
    fs.mkdirSync(packageRoot, { recursive: true });
    copyExtensionInto(packageRoot);
    execFileSync("zip", ["-q", "-r", archive, "."], { cwd: packageRoot });
    zipRoot = packageRoot;
  } else {
    const packageRoot = path.join(temporary, "AgentHalo-Web-Bridge");
    copyExtensionInto(path.join(packageRoot, "extension"));
    fs.copyFileSync(
      path.join(root, "extension/config.example.js"),
      path.join(packageRoot, "extension/config.example.js")
    );
    for (const file of ["scripts/register.js", "README.md", "README.en.md"]) {
      const target = path.join(packageRoot, file);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(path.join(root, file), target);
    }
    for (const file of ["LICENSE", "NOTICE.md"]) {
      fs.copyFileSync(path.join(root, "../agenthalo", file), path.join(packageRoot, file));
    }
    execFileSync("zip", ["-q", "-r", archive, "AgentHalo-Web-Bridge"], { cwd: temporary });
    zipRoot = packageRoot;
  }
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.copyFileSync(archive, output);
  console.log(output);
  if (storeMode) {
    const manifest = JSON.parse(fs.readFileSync(path.join(zipRoot, "manifest.json"), "utf8"));
    console.log(`version ${manifest.version}, ${EXTENSION_FILES.length + 1} files, manifest at zip root`);
  }
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
