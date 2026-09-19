"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const script = fs.readFileSync(path.join(__dirname, "../scripts/register.js"), "utf8");

function setup({ running = false, platform = "darwin" } = {}) {
  const files = new Map();
  const writes = [];
  const prefsPath = "/test-user/Library/Application Support/AgentHalo/agenthalo-prefs.json";
  files.set(prefsPath, JSON.stringify({ lang: "es", freeRoam: true, agents: {}, customApplications: [] }));
  const config = fs.readFileSync(path.join(__dirname, "../extension/config.example.js"), "utf8");
  const fakeFs = {
    readFileSync: (p) => files.has(p) ? files.get(p) : config,
    existsSync: (p) => files.has(p),
    mkdirSync: (p) => writes.push(p),
    writeFileSync: (p, content) => { writes.push(p); files.set(p, content); },
    cpSync: (from, to) => {
      writes.push(to);
      for (const [name, content] of [...files]) if (name.startsWith(from + "/")) files.set(to + name.slice(from.length), content);
    },
    copyFileSync: (from, to) => { writes.push(to); files.set(to, files.get(from)); },
    renameSync: (from, to) => { writes.push(to); files.set(to, files.get(from)); files.delete(from); },
  };
  const run = () => vm.runInNewContext(script, {
    require: (name) => name === "fs" ? fakeFs : name === "os" ? { homedir: () => "/test-user" }
      : name === "child_process" ? { execFileSync: () => running ? "/Applications/AgentHalo.app/Contents/MacOS/AgentHalo\n" : "" } : require(name),
    __dirname: "/extension-package/scripts", process: { platform, pid: 123 }, console: { log() {} },
  });
  return { run, writes, files, prefsPath };
}

test("registration refuses a running app before writing anything", () => {
  const env = setup({ running: true });
  assert.throws(env.run, /Quit AgentHalo/);
  assert.deepEqual(env.writes, []);
});
test("registration refuses unsupported platforms before writing anything", () => {
  const env = setup({ platform: "win32" });
  assert.throws(env.run, /macOS only/);
  assert.deepEqual(env.writes, []);
});
test("repeat registration preserves preferences and disabled web agents without duplicates", () => {
  const env = setup();
  env.run();
  const first = JSON.parse(env.files.get(env.prefsPath));
  const id = first.customApplications[0].id;
  first.agents[id].enabled = false;
  first.agents[id].notificationHookEnabled = false;
  env.files.set(env.prefsPath, JSON.stringify(first));
  env.run();
  const after = JSON.parse(env.files.get(env.prefsPath));
  assert.equal(after.customApplications.length, 3);
  assert.equal(after.agents[id].enabled, false);
  assert.equal(after.agents[id].notificationHookEnabled, false);
  assert.equal(after.lang, "es");
  assert.equal(after.freeRoam, true);
  assert.ok(env.files.get("/extension-package/extension/config.js").includes(id));
  assert.ok(env.files.get("/test-user/Library/Application Support/AgentHalo/WebBridge/extension/config.js").includes(id));
});
