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

// 多久收不到任何数据就放弃下载。按停顿计时而不是按总时长：慢网络下 120MB
// 可以下很久，但一个不再来数据的连接只会让人一直干等。
const DOWNLOAD_STALL_TIMEOUT_MS = 30000;

// 安装过程中的可预期失败。抛出而不是直接 process.exit，这样 finally 里的清理
// （临时目录、目标旁边的半成品）在每条失败路径上都会执行。
class InstallError extends Error {}

function log(msg) {
  process.stdout.write(`${msg}\n`);
}

function fail(msg) {
  throw new InstallError(msg);
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

async function download(url, dest, options = {}) {
  const fetchImpl = options.fetch || fetch;
  const stallTimeoutMs = options.stallTimeoutMs || DOWNLOAD_STALL_TIMEOUT_MS;
  // \r 只在终端里能原地覆盖。被重定向或管道接走时每一行都会留下，
  // 120MB 就是几百行噪声，所以非终端环境只在结束时报一次。
  const interactive = options.interactive !== undefined ? options.interactive : process.stdout.isTTY;
  const write = options.write || ((text) => process.stdout.write(text));

  const controller = new AbortController();
  let stallTimer = null;
  const armStallTimer = () => {
    clearTimeout(stallTimer);
    stallTimer = setTimeout(() => controller.abort(), stallTimeoutMs);
  };

  armStallTimer();
  try {
    const res = await fetchImpl(url, { redirect: "follow", signal: controller.signal });
    if (!res.ok) {
      fail(`下载返回 HTTP ${res.status}。\n  ${url}\n  如果是 404，说明这个版本的 release 还没发布。`);
    }
    const total = Number(res.headers.get("content-length")) || 0;
    let seen = 0;
    let lastShown = 0;

    const source = Readable.fromWeb(res.body);
    source.on("data", (chunk) => {
      armStallTimer();
      seen += chunk.length;
      if (!interactive) return;
      const now = Date.now();
      if (now - lastShown < 200 && seen !== total) return;
      lastShown = now;
      const pct = total ? ` ${Math.floor((seen / total) * 100)}%` : "";
      write(`\r  已下载 ${formatMB(seen)}MB${total ? ` / ${formatMB(total)}MB` : ""}${pct}   `);
    });

    await pipeline(source, fs.createWriteStream(dest));
    if (interactive) write("\n");
    else write(`  完成 ${formatMB(fs.statSync(dest).size)}MB\n`);
  } catch (err) {
    if (controller.signal.aborted) {
      fail(`下载 ${Math.round(stallTimeoutMs / 1000)} 秒没有进展，已放弃。请检查网络后重试。\n  ${url}`);
    }
    throw err;
  } finally {
    clearTimeout(stallTimer);
  }
}

// 边读边算，不把 100 多 MB 的压缩包整个读进内存。
async function sha256File(file) {
  const hash = crypto.createHash("sha256");
  for await (const chunk of fs.createReadStream(file)) hash.update(chunk);
  return hash.digest("hex");
}

function isAppRunning(appPath) {
  const running = spawnSync("/usr/bin/pgrep", ["-f", `${appPath}/Contents/MacOS/`], {
    stdio: ["ignore", "pipe", "ignore"],
  });
  return running.status === 0;
}

function quitRunningApp(appPath) {
  if (!isAppRunning(appPath)) return;
  log("  检测到正在运行，先退出旧版本");
  spawnSync("/usr/bin/osascript", ["-e", 'quit app "AgentHalo"'], { stdio: "ignore" });
  for (let i = 0; i < 20; i += 1) {
    if (!isAppRunning(appPath)) return;
    spawnSync("/bin/sleep", ["0.5"], { stdio: "ignore" });
  }
}

// 目标旁边的隐藏临时名：和目标在同一个目录（同一个卷），rename 才是原子的。
function siblingPath(target, label) {
  const suffix = `${process.pid}-${crypto.randomBytes(4).toString("hex")}`;
  return path.join(path.dirname(target), `.${path.basename(target)}.${label}-${suffix}`);
}

// 用两次同目录 rename 把 incoming 换到 target：旧版先让位，新版就位后才删旧版。
// 第二次 rename 失败就把旧版挪回去，所以失败时 target 要么是完整的旧版，要么是
// 完整的新版，不会是复制到一半的目录。唯一的空窗是两次 rename 之间那一瞬间；
// 它们是紧挨着的同步调用，Ctrl-C 的处理也插不进去。
function swapIntoPlace(incoming, target, fsApi = fs) {
  const previous = fsApi.existsSync(target) ? siblingPath(target, "previous") : null;
  if (previous) fsApi.renameSync(target, previous);
  try {
    fsApi.renameSync(incoming, target);
  } catch (err) {
    if (previous) fsApi.renameSync(previous, target);
    throw err;
  }
  if (previous) {
    try {
      fsApi.rmSync(previous, { recursive: true, force: true });
    } catch {
      // 新版已经就位；留下的隐藏旧目录不影响使用，下次安装也不会碰到它。
    }
  }
}

// 先把新版完整复制到目标旁边，再退出旧版并确认它真的退出了，最后原子替换。
// 复制失败、旧版退不掉，都不会动已安装的那一份。
function installApp(staged, target, deps = {}) {
  const copy = deps.copy || ((from, to) => execFileSync("/usr/bin/ditto", [from, to], { stdio: "inherit" }));
  const quit = deps.quit || quitRunningApp;
  const isRunning = deps.isRunning || isAppRunning;
  const pending = deps.pending || new Set();

  const incoming = siblingPath(target, "incoming");
  pending.add(incoming);
  try {
    copy(staged, incoming);
    if (fs.existsSync(target)) {
      quit(target);
      if (isRunning(target)) {
        fail("AgentHalo 还在运行，没有替换已安装的版本。请从菜单栏图标退出 AgentHalo 后重新运行 npx agenthalo。");
      }
    }
    swapIntoPlace(incoming, target);
  } finally {
    fs.rmSync(incoming, { recursive: true, force: true });
    pending.delete(incoming);
  }
}

function resolveInstallDir(argv = process.argv) {
  // --dir 给受管机器和想装到别处的人留的出口，也让安装流程可以在临时目录里验证。
  const flag = argv.indexOf("--dir");
  if (flag !== -1) {
    const dir = argv[flag + 1];
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

// Ctrl-C / 终端关闭时 finally 不会执行：先删掉临时文件，再按原信号退出。
function removeOnSignal(pending) {
  const signals = ["SIGINT", "SIGTERM", "SIGHUP"];
  const handler = (signal) => {
    for (const target of pending) {
      try { fs.rmSync(target, { recursive: true, force: true }); } catch {}
    }
    for (const other of signals) process.removeListener(other, handler);
    process.kill(process.pid, signal);
  };
  for (const signal of signals) process.on(signal, handler);
  return () => {
    for (const signal of signals) process.removeListener(signal, handler);
  };
}

async function main(options = {}) {
  const platform = options.platform || process.platform;
  const argv = options.argv || process.argv;
  if (platform !== "darwin") {
    fail(
      `当前只提供 macOS 版本（检测到 ${platform}）。\n`
      + `  其它平台请到 https://github.com/${REPO}/releases 查看。`
    );
  }

  const arch = options.arch || detectArch();
  const asset = `AgentHalo-${VERSION}-${arch}.zip`;
  const checksums = options.checksums || CHECKSUMS;
  const expected = checksums[asset];
  if (!expected) fail(`这个包里没有 ${asset} 的校验和，安装脚本和版本对不上。`);

  log(`AgentHalo ${VERSION}（${arch === "arm64" ? "Apple Silicon" : "Intel"}）`);

  const work = fs.mkdtempSync(path.join(options.tmpDir || os.tmpdir(), "agenthalo-"));
  const pending = new Set([work]);
  const stopWatchingSignals = removeOnSignal(pending);
  const zipPath = path.join(work, asset);

  try {
    log("下载中");
    await download(`${options.base || BASE}/${asset}`, zipPath, options.download);

    log("校验");
    const actual = await sha256File(zipPath);
    if (actual !== expected) {
      fail(`校验和不匹配，文件可能没下完或已被改动。\n  期望 ${expected}\n  实际 ${actual}`);
    }

    log("解压");
    // 用 ditto 而不是 unzip：.app 里的 Frameworks 有符号链接和特殊权限，
    // unzip 会弄坏它们，ditto 是 macOS 原生、electron-builder 的 zip 就是按它打的。
    const extract = options.extract
      || ((zip, into) => execFileSync("/usr/bin/ditto", ["-x", "-k", zip, into], { stdio: "inherit" }));
    extract(zipPath, work);
    const staged = path.join(work, APP_NAME);
    if (!fs.existsSync(staged)) fail("压缩包里没有找到 AgentHalo.app。");

    const installDir = resolveInstallDir(argv);
    const target = path.join(installDir, APP_NAME);
    log(`安装到 ${target}`);
    installApp(staged, target, { ...options.install, pending });

    if (!options.skipLaunch) spawnSync("/usr/bin/open", ["-a", target], { stdio: "ignore" });
    log("");
    log("装好了，点击 Dock 图标可打开设置，菜单栏也保留入口。");
    log("下一步：设置 → 连接应用，给你在用的 AI 工具装上 hook。");
    return target;
  } finally {
    fs.rmSync(work, { recursive: true, force: true });
    stopWatchingSignals();
  }
}

if (require.main === module) {
  main().catch((err) => {
    process.stderr.write(`\nAgentHalo 安装失败：${err && err.message ? err.message : String(err)}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  InstallError,
  download,
  installApp,
  main,
  sha256File,
  swapIntoPlace,
};
