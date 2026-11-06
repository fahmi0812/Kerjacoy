import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import cp from "node:child_process";
import * as U from "../core/lib/update.mjs";
import * as UI from "../core/lib/update-ui.mjs";

const sink = (tty = false) => { const o = { buf: "", isTTY: tty, write(s) { o.buf += s; return true; } }; return o; };

test("updater: repo sendiri fahmi0812/Kerjacoy", () => {
  assert.equal(U.DEFAULT_URL, "https://github.com/fahmi0812/Kerjacoy.git");
  assert.equal(U.TARBALL("v0.1.0"), "https://github.com/fahmi0812/Kerjacoy/tarball/v0.1.0");
});

test("updater: cmpVer + remoteTags (vX.Y.Z saja, urut, tag anotasi di-peel)", () => {
  assert.ok(U.cmpVer("v0.3.10", "0.3.2") > 0 && U.cmpVer("0.3.2", "v0.3.2") === 0 && U.cmpVer("0.2.9", "0.3.0") < 0);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "kctag-")), g = (...a) => cp.execFileSync("git", a, { cwd: tmp, stdio: "pipe" }).toString().trim();
  g("init", "-q"); fs.writeFileSync(path.join(tmp, "a"), "1"); g("add", "a"); g("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "a");
  const c1 = g("rev-parse", "HEAD"); g("tag", "v0.1.1"); g("-c", "user.name=t", "-c", "user.email=t@t", "tag", "-a", "v0.1.10", "-m", "x"); g("tag", "latest");
  const tags = U.remoteTags(tmp);
  assert.equal(tags.map((t) => t.tag).join(), "v0.1.1,v0.1.10"); assert.ok(tags.every((t) => t.sha === c1));
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("updater UI: non-TTY polos; TTY wordmark + spinner satu baris + ✓; ASCII; CI tanpa animasi", async () => {
  const o1 = sink(); const u1 = UI.createUI({ out: o1, mode: { tty: false, color: false, ascii: false } });
  u1.logo(); u1.step("Memeriksa"); u1.step("Mengunduh"); u1.done("Selesai — v1.2.3");
  assert.equal(o1.buf, "Memeriksa…\nMengunduh…\nSelesai — v1.2.3\n");
  const o2 = sink(true); const u2 = UI.createUI({ out: o2, mode: { tty: true, color: true, ascii: false }, interval: 10 });
  u2.logo(); u2.step("Memasang"); await new Promise((r) => setTimeout(r, 60)); u2.done("Selesai — v1.2.3");
  const frames = o2.buf.split("\r\x1b[2K").filter((x) => /Memasang/.test(x));
  assert.ok(o2.buf.includes("\x1b[38;2;212;175;55m"), "wordmark emas");
  assert.ok(frames.length >= 3 && new Set(frames.map((f) => f.replace(/\x1b\[[0-9;?]*m/g, "")[0])).size >= 3, "spinner beranimasi");
  assert.match(o2.buf, /✓\x1b\[0m Selesai — v1\.2\.3\n/); assert.ok(o2.buf.endsWith("\x1b[?25h"));
  assert.ok(!/\x1b\[38;2;[0-9;]+mMemasang/.test(o2.buf), "teks status warna default");
  const o3 = sink(true); const u3 = UI.createUI({ out: o3, mode: { tty: true, color: false, ascii: true }, interval: 10 }); u3.logo(); u3.step("Mengunduh"); await new Promise((r) => setTimeout(r, 30)); u3.done("Selesai");
  assert.ok(/KERJACOY/.test(o3.buf) && /[|/\\-] Mengunduh\.\.\./.test(o3.buf) && /OK Selesai/.test(o3.buf) && !/[^\x00-\x7f]/.test(o3.buf));
  assert.ok(!UI.uiMode({ env: { CI: "1" }, isTTY: true }).tty && !UI.uiMode({ env: { TERM: "dumb" }, isTTY: true }).tty);
  assert.ok(UI.uiMode({ env: { KC_ASCII: "1" }, isTTY: true, platform: "linux" }).ascii);
});

test("updater: error singkat (detail di log), npm-mode tarball, sudah terbaru, butuh --yes", async () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "kcupd-")); const repo = path.join(home, "src"); fs.mkdirSync(repo);
  const e4 = Object.assign(new Error("x"), { detail: "fatal: Could not resolve host" });
  const o4 = sink();
  assert.equal(await U.update({ argv: ["--check"], version: "0.1.0", repo, home, env: { KC_INSTALL: "npm" }, out: o4, tagsImpl: async () => { throw e4; } }), 1);
  assert.equal(o4.buf, "Memeriksa…\nTidak bisa memeriksa versi terbaru.\nCek koneksi internet, lalu coba lagi.\n");
  assert.ok(fs.readFileSync(path.join(home, "logs", "update.log"), "utf8").includes("Could not resolve host"));
  assert.ok(U.isNpmInstall(repo, { KC_INSTALL: "npm" }) && U.isNpmInstall(path.join("C:", "x", "node_modules", "kerjacoy"), {}, () => false) && !U.isNpmInstall(repo, {}));
  const calls = []; const o6 = sink();
  const r6 = await U.update({ argv: ["--yes"], version: "0.1.0", repo, home, env: { KC_INSTALL: "npm" }, out: o6, tagsImpl: async () => [{ tag: "v0.1.1", sha: "a" }], runImpl: async (cmd, args, o) => { calls.push([cmd, ...args]); o.log("npm WARN noise"); return ""; } });
  assert.equal(r6, 0); assert.equal(calls[0][0], "npm"); assert.ok(calls[0].includes(U.TARBALL("v0.1.1")));
  assert.equal(o6.buf.trim().split("\n").pop(), "Selesai — v0.1.1"); assert.ok(!o6.buf.includes("npm WARN"));
  const o7 = sink(); await U.update({ argv: [], version: "0.1.1", repo, home, env: { KC_INSTALL: "npm" }, out: o7, tagsImpl: async () => [{ tag: "v0.1.1", sha: "a" }] });
  assert.equal(o7.buf.trim().split("\n").pop(), "Sudah versi terbaru — v0.1.1");
  const o8 = sink(); assert.equal(await U.update({ argv: [], version: "0.1.0", repo, home, env: { KC_INSTALL: "npm" }, out: o8, tagsImpl: async () => [{ tag: "v0.1.1", sha: "a" }] }), 1);
  assert.ok(o8.buf.includes("kerjacoy update --yes"));
  fs.rmSync(home, { recursive: true, force: true });
});

test("updater git-mode e2e: clone tag lokal, verifikasi, swap, backup, cek pasca-pasang", async () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "kcgit-")); fs.writeFileSync(path.join(home, ".kerjacoy-home"), "");
  const origin = path.join(home, "origin"); const repoRoot = path.resolve(new URL("..", import.meta.url).pathname);
  fs.cpSync(repoRoot, origin, { recursive: true, filter: (s) => !s.includes(`${path.sep}.git`) && !s.includes("node_modules") });
  const g = (cwd, ...a) => cp.execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@t", ...a], { cwd, stdio: "pipe" }).toString().trim();
  const setVer = (d, v) => { fs.writeFileSync(path.join(d, "VERSION"), v + "\n"); const f = path.join(d, "core/bin/kerjacoy.mjs"); fs.writeFileSync(f, fs.readFileSync(f, "utf8").replace(/VERSION = "[\d.]+"/, `VERSION = "${v}"`)); };
  g(origin, "init", "-q", "-b", "main"); setVer(origin, "0.1.0"); g(origin, "add", "-A"); g(origin, "commit", "-qm", "a"); g(origin, "tag", "v0.1.0");
  const repo = path.join(home, "src"); g(home, "clone", "-q", origin, repo);
  setVer(origin, "0.1.1"); g(origin, "commit", "-qam", "b"); g(origin, "tag", "v0.1.1");
  const o = sink();
  const r = await U.update({ argv: ["--yes"], version: "0.1.0", repo, home, env: { ...process.env, KERJACOY_HOME: home, KC_OPENCODE: "/bin/false" }, out: o });
  assert.equal(r, 0, o.buf + fs.readFileSync(path.join(home, "logs", "update.log"), "utf8"));
  assert.equal(fs.readFileSync(path.join(repo, "VERSION"), "utf8").trim(), "0.1.1");
  assert.ok(fs.readdirSync(path.join(home, "backups")).some((d) => d.startsWith("src-v0.1.0")));
  fs.rmSync(home, { recursive: true, force: true });
});
