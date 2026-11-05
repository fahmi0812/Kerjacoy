#!/usr/bin/env node
/**
 * kerjacoy — OpenCode v2.2.4 (engine terpin) dengan tambahan kecil:
 *  - provider custom (menu "tambah provider", credentials.json, key lewat env {env:KC_KEY_*})
 *  - timeout provider (header 300 s, idle 900 s, total 3600 s)
 *  - isolasi: config/data/state/cache di ~/.kerjacoy, port service sendiri, tanpa auto-update
 *  - mode auto (izin disetujui otomatis) sebagai default; KC_AUTO=0 untuk mematikan
 * Semua argumen lain diteruskan ke engine apa adanya.
 */
import { spawn, spawnSync, execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");                 // .../core
const REPO = path.resolve(ROOT, "..");
export const VERSION = "2.0.0";
const DEFAULT_MODEL = "9router/ag/gemini-3.8-flash-high";
const env = { ...process.env };
const die = (code, msg) => { process.stderr.write(`kerjacoy: ${msg}\n`); process.exit(code); };
const lib = (n) => import(pathToFileURL(path.join(ROOT, "lib", n)).href);

const argv = process.argv.slice(2);
const sub = argv[0] && !argv[0].startsWith("-") ? argv[0] : "";
const HOME = env.KERJACOY_HOME || path.join(os.homedir(), ".kerjacoy");
const CFG_DIR = path.join(HOME, "config");
// isolasi dari OpenCode milik user (~/.config/opencode, ~/.local/share/opencode) dan dari harness lain
const isoEnv = () => ({ XDG_CONFIG_HOME: path.join(HOME, "xdg-config"), XDG_DATA_HOME: path.join(HOME, "data"),
  XDG_STATE_HOME: path.join(HOME, "state"), XDG_CACHE_HOME: path.join(HOME, "cache"), OPENCODE_DISABLE_AUTOUPDATE: "1" });
function ocBin() {
  if (env.KC_OPENCODE) return env.KC_OPENCODE;
  const exe = process.platform === "win32" ? "opencode.exe" : "opencode";
  const own = path.join(HOME, "bin", exe);
  return fs.existsSync(own) ? own : exe;
}

if (argv[0] === "--version" || argv[0] === "-v") {
  let oc = "?"; try { oc = execFileSync(ocBin(), ["--version"], { encoding: "utf8", env: { ...env, ...isoEnv() } }).trim(); } catch {}
  console.log(`kerjacoy ${VERSION} (${oc})`); process.exit(0);
}
// engine terpin: self-upgrade/uninstall engine diblok
if (sub === "upgrade" || sub === "uninstall") die(2, `'${sub}' diblok (engine terpin v2.2.4). Perbarui Kerjacoy: kerjacoy update; hapus: install.sh --uninstall`);
if (sub === "update") {
  const { update } = await lib("update.mjs");
  process.exit(await update({ argv: argv.slice(1), version: VERSION, repo: REPO, home: HOME }));
}

// ---------- provider ----------
const PV = await lib("providers.mjs");
async function providerMenu() {
  if (!process.stdin.isTTY || !process.stdout.isTTY) die(2, "menu provider butuh terminal interaktif; pakai: kerjacoy connect --type openai|anthropic --name <n> --base-url <url> --key-env VAR");
  const UI = await lib("provider-ui.mjs");
  return UI.run({ home: HOME, PV });
}
if (sub === "provider") { await providerMenu(); process.exit(0); }
if (sub === "connect" && process.stdin.isTTY && process.stdout.isTTY && !argv.includes("--text")
  && !["--list", "--remove", "--type", "--name", "--base-url", "--key-env", "--key-stdin"].some((f) => argv.includes(f))) { await providerMenu(); process.exit(0); }
if (sub === "connect" || (sub === "models" && argv.includes("--refresh"))) process.exit(await PV.cli({ argv: argv.slice(1), home: HOME, sub }));

const FRAG = PV.opencodeFragment(HOME, env);
const HAS_9R = !!FRAG.env.KC_KEY_9ROUTER;
const HAS_PROVIDER = HAS_9R || Object.keys(FRAG.providers).length > 0;
function chooseModel() {
  if (env.KC_MODEL) return env.KC_MODEL;
  if (HAS_9R || FRAG.providers["9router"]?.models["ag/gemini-3.8-flash-high"]) return DEFAULT_MODEL;
  const [n, p] = Object.entries(FRAG.providers)[0] || []; return n ? `${n}/${Object.keys(p.models)[0]}` : null;
}
const MODEL = chooseModel();
if (!HAS_PROVIDER && sub === "") {
  if (process.stdin.isTTY && process.stdout.isTTY && env.KC_ONBOARD !== "0") {
    const n = await providerMenu();
    if (n > 0) process.exit(spawnSync(process.execPath, [fileURLToPath(import.meta.url), ...argv], { stdio: "inherit", env: process.env }).status ?? 1);
  } else process.stderr.write("kerjacoy: belum ada provider. Tambah: `kerjacoy provider` atau `kerjacoy connect`; di TUI: /connect\n");
}

// ---------- config final (OPENCODE_CONFIG_CONTENT): provider + timeout + tanpa auto-update ----------
const TIMEOUTS = PV.providerTimeouts(env);
const finalCfg = { update: "disable", providers: { "9router": { settings: { ...TIMEOUTS } } } };
for (const [n, p] of Object.entries(FRAG.providers)) finalCfg.providers[n] = { ...p, settings: { ...p.settings, ...TIMEOUTS } };
if (MODEL) finalCfg.model = MODEL;
if (!HAS_9R && !FRAG.providers["9router"]) finalCfg.disabled_providers = ["9router"];

// config dir milik Kerjacoy (engine juga menulis service.json & cli.json ke sini)
fs.mkdirSync(CFG_DIR, { recursive: true, mode: 0o700 });
fs.copyFileSync(path.join(ROOT, "config", "opencode.jsonc"), path.join(CFG_DIR, "opencode.jsonc"));
// AGENTS.md + folder kosong milik user (lihat userfiles.mjs): hanya dibuat bila belum ada
try { (await lib("userfiles.mjs")).seedUserFiles(CFG_DIR); } catch (e) { if (env.KC_DEBUG) process.stderr.write(`kerjacoy: AGENTS.md: ${e.message}\n`); }
// cli.json: judul jendela, mode auto (izin disetujui otomatis) default
{
  const BR = await lib("brand.mjs");
  const cliFile = path.join(CFG_DIR, "cli.json");
  let cur = {}; try { cur = JSON.parse(fs.readFileSync(cliFile, "utf8")); } catch {}
  const r = BR.seedCliConfig(cur, { auto: env.KC_AUTO });
  if (r.changed) fs.writeFileSync(cliFile, JSON.stringify(r.config, null, 2) + "\n", { mode: 0o600 });
  if (sub === "" && process.stderr.isTTY) process.stderr.write(BR.titleSeq());
}
// port service sendiri (bukan 49374 milik OpenCode, beda rentang dari Lumitome)
if (sub !== "run") {
  const SP = await lib("service-port.mjs");
  const sp = await SP.ensureServicePort({ home: HOME, cfgDir: CFG_DIR, stateHome: path.join(HOME, "state"), env });
  if (env.KC_DEBUG) process.stderr.write(`kerjacoy: service port ${sp.port} (${sp.reason})\n`);
}
try { fs.chmodSync(path.join(CFG_DIR, "service.json"), 0o600); } catch {}

Object.assign(env, isoEnv(), {
  OPENCODE_CONFIG_DIR: CFG_DIR,
  OPENCODE_CONFIG_CONTENT: JSON.stringify(finalCfg),
  OPENCODE_DISABLE_MODELS_FETCH: env.KC_MODELS_FETCH === "1" ? "" : "1",
  OPENCODE_DISABLE_CLAUDE_CODE: "1",
  KC_9ROUTER_URL: env.KC_9ROUTER_URL || "http://127.0.0.1:20128/v1",
  ...FRAG.env, // key provider untuk SEMUA sub-perintah (termasuk service latar) — perbaikan 401
  ...PV.lokerEnv(HOME, env, MODEL), // mesin loker (`loker --llm`) memakai provider aktif yang sama
});
delete env.OPENCODE_CONFIG;
// service latar milik KERJACOY_HOME: key/config berubah → service lama dihentikan agar tidak memakai env basi (401)
if (sub === "" || sub === "serve") {
  const SC = await lib("service-ctl.mjs");
  try { SC.ensureFresh(HOME, SC.fingerprint([VERSION, env.OPENCODE_CONFIG_CONTENT, FRAG.env, env.KC_9ROUTER_URL])); } catch {}
}

let args = argv.slice();
if (sub === "run" && env.KC_AUTO !== "0" && !args.includes("--auto")) args = ["run", "--auto", ...args.slice(1)];
if (sub === "run" && MODEL && !args.some((a) => a === "-m" || a === "--model" || a.startsWith("--model="))) args.splice(1, 0, "-m", MODEL);

// mesin loker (Python) di depan PATH, supaya agen bisa memanggil `loker`
{
  const venvBin = path.join(HOME, "venv", "bin");
  const key = Object.keys(env).find((k) => k.toUpperCase() === "PATH") || "PATH";
  if (fs.existsSync(path.join(venvBin, "loker")) && !(env[key] || "").split(path.delimiter).includes(venvBin)) {
    env[key] = [venvBin, env[key]].filter(Boolean).join(path.delimiter);
  }
}

const child = spawn(ocBin(), args, { stdio: "inherit", env });
for (const s of ["SIGINT", "SIGTERM", "SIGHUP"]) process.on(s, () => { try { child.kill(s); } catch {} });
child.on("error", (e) => die(1, `engine tidak bisa dijalankan (${e.message}). Pasang ulang: install.sh atau npm install -g`));
child.on("exit", (code, sig) => process.exit(code ?? (sig ? 1 : 0)));
