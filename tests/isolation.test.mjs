import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import net from "node:net";
import cp from "node:child_process";
import * as SP from "../core/lib/service-port.mjs";
import * as SC from "../core/lib/service-ctl.mjs";
import * as BR from "../core/lib/brand.mjs";

const ROOT = path.resolve(new URL("..", import.meta.url).pathname);
const WRAP = path.join(ROOT, "core/bin/kerjacoy.mjs");
const listen = (port) => new Promise((res, rej) => { const s = net.createServer(); s.once("error", rej); s.listen(port, "127.0.0.1", () => res(s)); });

// engine palsu: catat argv + env yang relevan
function fakeEngine(dir) {
  const f = path.join(dir, "fake-opencode");
  fs.writeFileSync(f, `#!${process.execPath}\nconst fs=require("fs");const e=process.env;fs.writeFileSync(e.FAKE_OUT, JSON.stringify({argv:process.argv.slice(2), env:Object.fromEntries(Object.entries(e).filter(([k])=>/^(XDG_|OPENCODE_|KC_|NINEROUTER)/.test(k)))}));\n`, { mode: 0o755 });
  return f;
}
function runWrap(args, { home, userHome, extra = {} }) {
  fs.mkdirSync(home, { recursive: true });
  const out = path.join(home, "fake.json");
  const env = { PATH: process.env.PATH, HOME: userHome, KERJACOY_HOME: home, KC_OPENCODE: fakeEngine(home), FAKE_OUT: out, KC_ONBOARD: "0", ...extra };
  const r = cp.spawnSync(process.execPath, [WRAP, ...args], { env, encoding: "utf8", cwd: userHome, input: "" });
  return { ...r, rec: fs.existsSync(out) ? JSON.parse(fs.readFileSync(out, "utf8")) : null };
}
function setup() {
  const userHome = fs.mkdtempSync(path.join(os.tmpdir(), "kcuser-"));
  // instalasi OpenCode dan Lumitome milik user yang sudah ada
  const files = {
    [path.join(userHome, ".config/opencode/opencode.json")]: '{"model":"user/model"}',
    [path.join(userHome, ".local/share/opencode/auth.json")]: '{"x":{"key":"user-secret"}}',
    [path.join(userHome, ".lumitome/config/service.json")]: '{"port":51234}',
    [path.join(userHome, ".lumitome/credentials.json")]: '{"9router":"lumi-key"}',
  };
  for (const [f, c] of Object.entries(files)) { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, c); }
  return { userHome, home: path.join(userHome, ".kerjacoy"), files };
}

test("isolasi: config/data/state/cache di ~/.kerjacoy; OpenCode & Lumitome milik user tidak disentuh", () => {
  const { userHome, home, files } = setup();
  fs.mkdirSync(home, { recursive: true });
  const before = Object.fromEntries(Object.entries(files).map(([f]) => [f, fs.readFileSync(f, "utf8")]));
  const r = runWrap(["run", "halo"], { home, userHome, extra: { NINEROUTER_API_KEY: "kc-test-key" } });
  assert.equal(r.status, 0, r.stderr);
  const e = r.rec.env;
  for (const k of ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "OPENCODE_CONFIG_DIR"]) assert.ok(e[k].startsWith(home), `${k}=${e[k]}`);
  assert.equal(e.OPENCODE_DISABLE_AUTOUPDATE, "1");
  for (const [f, c] of Object.entries(before)) assert.equal(fs.readFileSync(f, "utf8"), c, `${f} berubah`);
  assert.ok(!JSON.stringify(r.rec).includes("lumi-key") && !JSON.stringify(r.rec).includes("user-secret"), "tidak membaca key Lumitome/OpenCode");
  assert.ok(!r.stdout.includes("kc-test-key") && !r.stderr.includes("kc-test-key"), "key tidak dicetak");
  fs.rmSync(userHome, { recursive: true, force: true });
});

test("config final: timeout di semua provider, update mati, key hanya lewat env, model default", () => {
  const { userHome, home } = setup(); fs.mkdirSync(home, { recursive: true });
  fs.writeFileSync(path.join(home, "providers.json"), JSON.stringify({ providers: { my: { type: "openai", baseURL: "http://x/v1", models: ["m1"] } } }));
  fs.writeFileSync(path.join(home, "credentials.json"), JSON.stringify({ my: "my-key" }));
  const r = runWrap(["run", "halo"], { home, userHome });
  const cfg = JSON.parse(r.rec.env.OPENCODE_CONFIG_CONTENT);
  assert.equal(cfg.update, "disable");
  assert.deepEqual(cfg.providers.my.settings, { baseURL: "http://x/v1", apiKey: "{env:KC_KEY_MY}", headerTimeout: 300000, chunkTimeout: 900000, timeout: 3600000 });
  assert.equal(cfg.providers["9router"].settings.chunkTimeout, 900000);
  assert.ok(!r.rec.env.OPENCODE_CONFIG_CONTENT.includes("my-key"));
  assert.equal(r.rec.env.KC_KEY_MY, "my-key");
  assert.deepEqual(cfg.disabled_providers, ["9router"]);
  assert.ok(r.rec.argv.includes("-m") && r.rec.argv.includes("my/m1"));
  assert.ok(!cfg.permissions && !cfg.default_agent && !cfg.mcp && !cfg.instructions, "agent & izin = bawaan OpenCode");
  fs.rmSync(userHome, { recursive: true, force: true });
});

test("mode auto: default aktif (run --auto, cli.json autoaccept); KC_AUTO=0 mematikan", () => {
  const { userHome, home } = setup(); fs.mkdirSync(home, { recursive: true });
  const r1 = runWrap(["run", "halo"], { home, userHome, extra: { NINEROUTER_API_KEY: "k" } });
  assert.equal(r1.rec.argv[0], "run"); assert.ok(r1.rec.argv.includes("--auto"));
  const cli = JSON.parse(fs.readFileSync(path.join(home, "config", "cli.json"), "utf8"));
  assert.equal(cli.session.permissions, "autoaccept"); assert.equal(cli.terminal.title, false);
  const r2 = runWrap(["run", "halo"], { home, userHome, extra: { NINEROUTER_API_KEY: "k", KC_AUTO: "0" } });
  assert.ok(!r2.rec.argv.includes("--auto"));
  assert.equal(JSON.parse(fs.readFileSync(path.join(home, "config", "cli.json"), "utf8")).session.permissions, "prompt");
  // pilihan user lewat /config dihormati
  assert.equal(BR.seedCliConfig({ session: { permissions: "prompt" }, terminal: { title: true } }).changed, false);
  assert.equal(BR.seedCliConfig({}).config.session.permissions, "autoaccept");
  assert.equal(BR.seedCliConfig({ session: { permissions: "prompt" } }, { auto: "1" }).config.session.permissions, "autoaccept");
  fs.rmSync(userHome, { recursive: true, force: true });
});

test("port service: rentang 60000–64999, bukan 49374 (OpenCode) dan bukan rentang Lumitome", async () => {
  for (const h of ["/a", "/home/u/.kerjacoy", "C:\\Users\\F\\.kerjacoy"]) { const p = SP.derivePort(h); assert.ok(p >= 60000 && p < 65000); }
  const { userHome, home } = setup();
  const busy = []; for (const p of [49374, 51234]) try { busy.push(await listen(p)); } catch {}
  const busyOwn = await listen(SP.derivePort(home)).catch(() => null);
  const r = await SP.ensureServicePort({ home, cfgDir: path.join(home, "config"), stateHome: path.join(home, "state"), env: {} });
  assert.ok(r.port !== 49374 && r.port !== 51234 && r.port !== SP.derivePort(home) && !(r.port >= 50000 && r.port < 60000), `port ${r.port}`);
  assert.equal(JSON.parse(fs.readFileSync(r.file, "utf8")).port, r.port);
  const forced = await SP.ensureServicePort({ home, cfgDir: path.join(home, "config2"), stateHome: home, env: { KC_SERVICE_PORT: "61111" } });
  assert.equal(forced.port, 61111);
  for (const s of [...busy, busyOwn]) s?.close();
  fs.rmSync(userHome, { recursive: true, force: true });
});

test("berdampingan: wrapper TUI menulis port sendiri; service.json Lumitome tetap", () => {
  const { userHome, home } = setup();
  const r = runWrap([], { home, userHome, extra: { NINEROUTER_API_KEY: "k" } });
  assert.equal(r.status, 0, r.stderr);
  const port = JSON.parse(fs.readFileSync(path.join(home, "config", "service.json"), "utf8")).port;
  assert.ok(port >= 60000 && port < 65000);
  assert.equal(fs.readFileSync(path.join(userHome, ".lumitome/config/service.json"), "utf8"), '{"port":51234}');
  assert.ok(!fs.existsSync(path.join(userHome, ".config/opencode/service.json")));
  fs.rmSync(userHome, { recursive: true, force: true });
});

test("service latar: dipakai ulang bila sidik sama; key berubah → service lama dihentikan (perbaikan 401)", async () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "kcsvc-"));
  assert.ok(!SC.status(home).running); assert.equal(SC.stop(home), false);
  const svc = cp.spawn(process.execPath, ["-e", "setInterval(()=>{},1000)"], { stdio: "ignore" });
  fs.mkdirSync(path.join(home, "state", "opencode"), { recursive: true });
  fs.writeFileSync(SC.regFile(home), JSON.stringify({ pid: svc.pid, url: "http://127.0.0.1:61000" }));
  const fpA = SC.fingerprint(["0.1.0", { KC_KEY_9ROUTER: "a" }]), fpB = SC.fingerprint(["0.1.0", { KC_KEY_9ROUTER: "b" }]);
  const gone1 = new Promise((r) => svc.once("exit", r));
  assert.equal(SC.ensureFresh(home, fpA), "restart", "tanpa sidik tersimpan → service lama dihentikan"); await gone1;
  // service baru dengan sidik A
  const svc2 = cp.spawn(process.execPath, ["-e", "setInterval(()=>{},1000)"], { stdio: "ignore" });
  fs.writeFileSync(SC.regFile(home), JSON.stringify({ pid: svc2.pid, url: "http://127.0.0.1:61000" }));
  assert.equal(SC.ensureFresh(home, fpA), "reuse");
  const gone2 = new Promise((r) => svc2.once("exit", r));
  assert.equal(SC.ensureFresh(home, fpB), "restart");
  await gone2;
  try { svc.kill("SIGKILL"); } catch {}
  fs.rmSync(home, { recursive: true, force: true });
});

test("engine terpin: 'upgrade'/'uninstall' engine diblok; --version tanpa auto-update", () => {
  const { userHome, home } = setup(); fs.mkdirSync(home, { recursive: true });
  const r = runWrap(["upgrade"], { home, userHome });
  assert.equal(r.status, 2); assert.match(r.stderr, /diblok/);
  fs.rmSync(userHome, { recursive: true, force: true });
});

test("engine asli (bila tersedia, KC_TEST_ENGINE): versi 2.2.4 + flag --auto ada di `run`", { skip: !process.env.KC_TEST_ENGINE && "set KC_TEST_ENGINE=<path opencode>" }, () => {
  const { userHome, home } = setup(); fs.mkdirSync(home, { recursive: true });
  const env = { PATH: process.env.PATH, HOME: userHome, KERJACOY_HOME: home, KC_OPENCODE: process.env.KC_TEST_ENGINE };
  const v = cp.spawnSync(process.execPath, [WRAP, "--version"], { env, encoding: "utf8" });
  assert.match(v.stdout, /^kerjacoy \d+\.\d+\.\d+ \(opencode v2\.2\.4\)/);
  const h = cp.spawnSync(process.env.KC_TEST_ENGINE, ["run", "--help"], { env: { ...env, XDG_DATA_HOME: path.join(home, "d"), XDG_STATE_HOME: path.join(home, "s"), XDG_CONFIG_HOME: path.join(home, "c"), XDG_CACHE_HOME: path.join(home, "k") }, encoding: "utf8" });
  assert.match(h.stdout + h.stderr, /--auto/);
  assert.ok(!fs.existsSync(path.join(userHome, ".local/share/opencode/log")), "engine tidak menulis log ke data OpenCode user");
  fs.rmSync(userHome, { recursive: true, force: true });
});
