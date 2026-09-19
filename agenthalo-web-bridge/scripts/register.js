#!/usr/bin/env node
// Registers the three web launcher stubs as AgentHalo custom HTTP agents by editing
// agenthalo-prefs.json directly (AgentHalo must NOT be running while this runs, or it
// will overwrite the change). Also rewrites extension/config.js with the ids.
//
// Usage: node scripts/register.js
const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const { execFileSync } = require("child_process");

const BIN = path.join(os.homedir(), ".clawd-web-bridge", "bin");
const PREFS = path.join(os.homedir(), "Library", "Application Support", "AgentHalo", "agenthalo-prefs.json");
const CONFIG = path.join(__dirname, "..", "extension", "config.js");
const INSTALL_DIR = path.join(os.homedir(), "Library", "Application Support", "AgentHalo", "WebBridge", "extension");
const INSTALLED_CONFIG = path.join(INSTALL_DIR, "config.js");

const DEFS = [
  ["claude-web", "Claude Web", "https://claude.ai/new"],
  ["chatgpt-web", "ChatGPT Web", "https://chatgpt.com/"],
  ["gemini-web", "Gemini Web", "https://gemini.google.com/app"],
];

if (process.platform !== "darwin") throw new Error("This setup script currently supports macOS only.");
// Abort before creating files if preferences do not exist or AgentHalo is running.
const prefs = JSON.parse(fs.readFileSync(PREFS, "utf8"));
const processes = execFileSync("/bin/ps", ["-axo", "comm="], { encoding: "utf8" });
if (processes.split("\n").some((command) => /\/AgentHalo\.app\/Contents\/MacOS\/AgentHalo$/.test(command.trim()))) {
  throw new Error("Quit AgentHalo from its menu, then run this script again.");
}
fs.mkdirSync(BIN, { recursive: true });
const apps = DEFS.map(([file, name, url]) => {
  const exe = path.join(BIN, file);
  fs.writeFileSync(exe, `#!/bin/sh\n# AgentHalo Web Bridge launcher stub: opens ${name}\nopen "${url}"\n`, { mode: 0o755 });
  // Same derivation as agenthalo/src/custom-applications.js applicationId()
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 32);
  const id = `custom-${slug}-${crypto.createHash("sha256").update(exe).digest("hex").slice(0, 12)}`;
  return { id, name, sourcePath: exe, executablePath: exe, processName: file, category: "work", key: file };
});

const ids = new Set(apps.map((a) => a.id));
prefs.customApplications = (prefs.customApplications || []).filter((a) => !ids.has(a.id))
  .concat(apps.map(({ key, ...rest }) => rest));
prefs.agents = prefs.agents || {};
for (const a of apps) {
  prefs.agents[a.id] = { enabled: true, notificationHookEnabled: true, ...prefs.agents[a.id], integrationInstalled: false, permissionsEnabled: false };
}
fs.copyFileSync(PREFS, `${PREFS}.bak-${Date.now()}`);
const temporaryPrefs = `${PREFS}.tmp-${process.pid}`;
fs.writeFileSync(temporaryPrefs, JSON.stringify(prefs, null, 2), { mode: 0o600 });
fs.renameSync(temporaryPrefs, PREFS);

let cfg = fs.readFileSync(fs.existsSync(INSTALLED_CONFIG) ? INSTALLED_CONFIG : fs.existsSync(CONFIG) ? CONFIG : path.join(path.dirname(CONFIG), "config.example.js"), "utf8");
for (const a of apps) {
  cfg = cfg.replace(new RegExp(`"${a.key}": "(?:custom-[a-z0-9-]+)?"`), `"${a.key}": "${a.id}"`);
}
fs.writeFileSync(CONFIG, cfg);
fs.mkdirSync(path.dirname(INSTALL_DIR), { recursive: true });
fs.cpSync(path.dirname(CONFIG), INSTALL_DIR, { recursive: true });
console.log("Load unpacked extension from:", INSTALL_DIR);
console.log("registered:", apps.map((a) => `${a.key} → ${a.id}`).join("\n            "));
