"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const pkg = require("../package.json");
const lock = require("../package-lock.json");

const EXPECTED_VERSION = "2.16.3";
const EXPECTED_INTEGRITY = "sha512-E9y1AsgYGlaxMhcZzHr8y96QF2U5XzA12GGVAfbWqIubTwPNMXQarfBzePNXHe0xtIEtNd6ifAv3GAKYGUeBAQ==";

test("Koffi native code is pinned exactly in package and lock metadata", () => {
  assert.equal(pkg.dependencies.koffi, EXPECTED_VERSION);
  assert.equal(lock.packages[""].dependencies.koffi, EXPECTED_VERSION);
  const entry = lock.packages["node_modules/koffi"];
  assert.equal(entry.version, EXPECTED_VERSION);
  assert.equal(entry.integrity, EXPECTED_INTEGRITY);
  assert.equal(entry.hasInstallScript, true);
  assert.match(entry.resolved, /^https:\/\/registry\.npmjs\.org\/koffi\//);
});

test("every locked package resolves from the public npm registry", () => {
  // A regional mirror in `resolved` makes `npm ci` fail wherever that mirror
  // is unreachable (CI runners, most networks outside China). Tarballs are
  // byte-identical across registries, so integrity is unaffected, and npm's
  // default replace-registry-host=npmjs still sends these URLs to a mirror
  // configured with `registry=` in .npmrc. Configure the mirror; do not
  // commit it.
  const offRegistry = Object.entries(lock.packages)
    .filter(([, entry]) => entry.resolved && !entry.resolved.startsWith("https://registry.npmjs.org/"))
    .map(([name, entry]) => `${name}: ${entry.resolved}`);
  assert.deepEqual(offRegistry, []);
});

test("electron-builder runs the reviewed safe afterPack hook", () => {
  assert.equal(pkg.build.afterPack, "scripts/after-pack-koffi.js");
  assert.equal(pkg.scripts["audit:native-package"], "node scripts/audit-packaged-native.js");
  assert.equal(pkg.scripts["verify:updater-metadata"], "node scripts/verify-updater-metadata.js");
});
