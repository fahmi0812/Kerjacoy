#!/usr/bin/env node
/**
 * Entry `kerjacoy` untuk instalasi npm (Windows / macOS / Linux) — tanpa bash.
 * Menyiapkan KERJACOY_HOME (~/.kerjacoy, Windows: %USERPROFILE%\.kerjacoy), memasang engine OpenCode terpin
 * (SHA256) bila belum ada, lalu menjalankan wrapper kerjacoy.mjs dengan Node yang sama.
 */
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { kcHome, engineBin, engineVersion, installEngine, ensureEngine, OC_VERSION } from "../lib/engine.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const [maj, min] = process.versions.node.split(".").map(Number);
if (maj < 22 || (maj === 22 && min < 6)) { process.stderr.write(`kerjacoy: butuh Node.js >= 22.6 (sekarang ${process.versions.node}). Unduh di https://nodejs.org\n`); process.exit(1); }

const env = { ...process.env };
const home = kcHome(env);
env.KERJACOY_HOME = home; env.KC_INSTALL ||= "npm";
fs.mkdirSync(path.join(home, "bin"), { recursive: true });
if (!fs.existsSync(path.join(home, ".kerjacoy-home"))) fs.writeFileSync(path.join(home, ".kerjacoy-home"), "");
const bin = env.KC_OPENCODE || engineBin(home);
const isoEnv = { ...env, XDG_CONFIG_HOME: path.join(home, "xdg-config"), XDG_DATA_HOME: path.join(home, "data"), XDG_STATE_HOME: path.join(home, "state"), XDG_CACHE_HOME: path.join(home, "cache"), OPENCODE_DISABLE_AUTOUPDATE: "1" };
if (!env.KC_OPENCODE) {
  try { await ensureEngine({ home, bin, env: isoEnv }); }
  catch (e) { process.stderr.write(`kerjacoy: gagal memasang engine OpenCode v${OC_VERSION}: ${e.message}\n`); process.exit(1); }
}
env.KC_OPENCODE = bin;
// bin milik KERJACOY_HOME di depan PATH
const key = Object.keys(env).find((k) => k.toUpperCase() === "PATH") || "PATH";
env[key] = [path.join(home, "bin"), env[key]].filter(Boolean).join(path.delimiter);

const child = spawn(process.execPath, ["--experimental-strip-types", "--no-warnings", path.join(HERE, "kerjacoy.mjs"), ...process.argv.slice(2)], { stdio: "inherit", env });
for (const s of ["SIGINT", "SIGTERM", "SIGHUP"]) process.on(s, () => { try { child.kill(s); } catch {} });
child.on("exit", (code, sig) => process.exit(code ?? (sig ? 1 : 0)));
