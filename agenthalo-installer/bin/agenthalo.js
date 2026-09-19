#!/usr/bin/env node
"use strict";

// npx agenthalo — 下载并安装 AgentHalo 桌面端。
//
// 为什么走这条路而不是让用户下 dmg：macOS 的 Gatekeeper 只拦带
// com.apple.quarantine 属性的文件，而这个属性是**下载的那个程序**打上去的。
// 浏览器会打，curl 和 Node 不打。所以从这里装的 app 不会触发「无法验证开发者」
// 的拦截，用户装完直接能开。
//
// 零依赖，只用 Node 内建模块：npx 要先把这个包拉下来才能跑，依赖越少启动越快。

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const crypto = require("node:crypto");
const { execFileSync, spawnSync } = require("node:child_process");
const { Readable } = require("node:stream");
const { pipeline } = require("node:stream/promises");

const VERSION = require("../package.json").version;
const REPO = "addsumtech/AgentHalo";
const APP_NAME = "AgentHalo.app";
// 覆盖下载来源，只为发版前拿真实产物端到端跑一遍（见 scripts/verify-install.sh）。
const BASE = process.env.AGENTHALO_DOWNLOAD_BASE
  || `https://github.com/${REPO}/releases/download/v${VERSION}`;

// 按版本固定校验和：既能挡住下到一半的坏包，也能发现 release 资产被换过。
// 每次发版由 scripts/sync-checksums.js 从 dist/ 重新写入。
const CHECKSUMS = require("./checksums.json");

function log(msg) {
  process.stdout.write(`${msg}\n`);
}

function fail(msg) {
  process.stderr.write(`\nAgentHalo 安装失败：${msg}\n`);
  process.exit(1);
}

// process.arch 在 Rosetta 下的 Node 里会报 x64，哪怕机器是 Apple Silicon。
// 直接问硬件，免得给 M 系列芯片装上 Intel 包。
function detectArch() {
  if (process.arch === "arm64") return "arm64";
  try {
    const out = execFileSync("/usr/sbin/sysctl", ["-n", "hw.optional.arm64"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    if (out === "1") return "arm64";
  } catch {}
  return "x64";
}

function formatMB(bytes) {
  return (bytes / 1024 / 1024).toFixed(1);
}

async function download(url, dest) {
  const res = await fetch(url, { redirect: "follow" });
  if (!res.ok) {
    fail(`下载返回 HTTP ${res.status}。\n  ${url}\n  如果是 404，说明这个版本的 release 还没发布。`);
  }
  const total = Number(res.headers.get("content-length")) || 0;
  let seen = 0;
  let lastShown = 0;

  const source = Readable.fromWeb(res.body);
  // \r 只在终端里能原地覆盖。被重定向或管道接走时每一行都会留下，
  // 120MB 就是几百行噪声，所以非终端环境只在结束时报一次。
  const interactive = process.stdout.isTTY;
  if (interactive) {
    source.on("data", (chunk) => {
      seen += chunk.length;
      const now = Date.now();
      if (now - lastShown < 200 && seen !== total) return;
      lastShown = now;
      const pct = total ? ` ${Math.floor((seen / total) * 100)}%` : "";
      process.stdout.write(`\r  已下载 ${formatMB(seen)}MB${total ? ` / ${formatMB(total)}MB` : ""}${pct}   `);
    });
  }

  await pipeline(source, fs.createWriteStream(dest));
  if (interactive) process.stdout.write("\n");
  else log(`  完成 ${formatMB(fs.statSync(dest).size)}MB`);
}

function sha256(file) {
  const hash = crypto.createHash("sha256");
  hash.update(fs.readFileSync(file));
  return hash.digest("hex");
}

function quitRunningApp(appPath) {
  const running = spawnSync("/usr/bin/pgrep", ["-f", `${appPath}/Contents/MacOS/`], {
    stdio: ["ignore", "pipe", "ignore"],
  });
  if (running.status !== 0) return;
  log("  检测到正在运行，先退出旧版本");
  spawnSync("/usr/bin/osascript", ["-e", 'quit app "AgentHalo"'], { stdio: "ignore" });
  for (let i = 0; i < 20; i += 1) {
    const still = spawnSync("/usr/bin/pgrep", ["-f", `${appPath}/Contents/MacOS/`], {
      stdio: ["ignore", "pipe", "ignore"],
    });
    if (still.status !== 0) return;
    spawnSync("/bin/sleep", ["0.5"], { stdio: "ignore" });
  }
}

function resolveInstallDir() {
  // --dir 给受管机器和想装到别处的人留的出口，也让安装流程可以在临时目录里验证。
  const flag = process.argv.indexOf("--dir");
  if (flag !== -1) {
    const dir = process.argv[flag + 1];
    if (!dir) fail("--dir 后面要跟一个目录路径。");
    fs.mkdirSync(dir, { recursive: true });
    return path.resolve(dir);
  }
  try {
    fs.accessSync("/Applications", fs.constants.W_OK);
    return "/Applications";
  } catch {
    // 受管机器上 /Applications 可能不可写，退到用户自己的应用目录，不提权。
    const userApps = path.join(os.homedir(), "Applications");
    fs.mkdirSync(userApps, { recursive: true });
    return userApps;
  }
}

async function main() {
  if (process.platform !== "darwin") {
    fail(
      `当前只提供 macOS 版本（检测到 ${process.platform}）。\n`
      + `  其它平台请到 https://github.com/${REPO}/releases 查看。`
    );
  }

  const arch = detectArch();
  const asset = `AgentHalo-${VERSION}-${arch}.zip`;
  const expected = CHECKSUMS[asset];
  if (!expected) fail(`这个包里没有 ${asset} 的校验和，安装脚本和版本对不上。`);

  log(`AgentHalo ${VERSION}（${arch === "arm64" ? "Apple Silicon" : "Intel"}）`);

  const work = fs.mkdtempSync(path.join(os.tmpdir(), "agenthalo-"));
  const zipPath = path.join(work, asset);

  try {
    log("下载中");
    await download(`${BASE}/${asset}`, zipPath);

    log("校验");
    const actual = sha256(zipPath);
    if (actual !== expected) {
      fail(`校验和不匹配，文件可能没下完或已被改动。\n  期望 ${expected}\n  实际 ${actual}`);
    }

    log("解压");
    // 用 ditto 而不是 unzip：.app 里的 Frameworks 有符号链接和特殊权限，
    // unzip 会弄坏它们，ditto 是 macOS 原生、electron-builder 的 zip 就是按它打的。
    execFileSync("/usr/bin/ditto", ["-x", "-k", zipPath, work], { stdio: "inherit" });
    const staged = path.join(work, APP_NAME);
    if (!fs.existsSync(staged)) fail("压缩包里没有找到 AgentHalo.app。");

    const installDir = resolveInstallDir();
    const target = path.join(installDir, APP_NAME);
    log(`安装到 ${target}`);
    if (fs.existsSync(target)) {
      quitRunningApp(target);
      fs.rmSync(target, { recursive: true, force: true });
    }
    execFileSync("/usr/bin/ditto", [staged, target], { stdio: "inherit" });

    spawnSync("/usr/bin/open", ["-a", target], { stdio: "ignore" });
    log("");
    log("装好了，点击 Dock 图标可打开设置，菜单栏也保留入口。");
    log("下一步：设置 → 连接应用，给你在用的 AI 工具装上 hook。");
  } finally {
    fs.rmSync(work, { recursive: true, force: true });
  }
}

main().catch((err) => fail(err && err.message ? err.message : String(err)));
