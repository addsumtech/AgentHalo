#!/usr/bin/env node
"use strict";

// 从 agenthalo/dist/ 里真正要发布的 zip 重新生成 bin/checksums.json。
// 每次重新构建后、发 release 之前跑一次，否则安装器会用旧哈希拒掉新包。

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const ROOT = path.resolve(__dirname, "..");
const DIST = path.resolve(ROOT, "..", "agenthalo", "dist");
const VERSION = require(path.join(ROOT, "package.json")).version;
const ARCHES = ["arm64", "x64"];

const out = {};
const missing = [];

for (const arch of ARCHES) {
  const name = `AgentHalo-${VERSION}-${arch}.zip`;
  const file = path.join(DIST, name);
  if (!fs.existsSync(file)) {
    missing.push(name);
    continue;
  }
  const hash = crypto.createHash("sha256");
  hash.update(fs.readFileSync(file));
  out[name] = hash.digest("hex");
}

if (missing.length) {
  process.stderr.write(
    `dist/ 里缺少：${missing.join("、")}\n`
    + `先在 agenthalo/ 跑 npm run build:mac 再执行本脚本。\n`
  );
  process.exit(1);
}

const target = path.join(ROOT, "bin", "checksums.json");
fs.writeFileSync(target, `${JSON.stringify(out, null, 2)}\n`);
process.stdout.write(`已写入 ${path.relative(ROOT, target)}\n`);
for (const [name, hash] of Object.entries(out)) {
  process.stdout.write(`  ${name}  ${hash}\n`);
}
