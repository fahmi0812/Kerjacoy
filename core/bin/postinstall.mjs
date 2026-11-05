#!/usr/bin/env node
/**
 * postinstall npm: pasang engine OpenCode terpin (SHA256) ke KERJACOY_HOME.
 * Tidak pernah menggagalkan `npm install`: bila gagal (offline, dsb.), engine dipasang saat `kerjacoy` pertama kali dijalankan.
 * Lewati dengan KC_SKIP_ENGINE_DOWNLOAD=1.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { kcHome, engineBin, engineVersion, installEngine, ensureEngine, OC_VERSION } from "../lib/engine.mjs";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const say = (m) => process.stderr.write(`kerjacoy postinstall: ${m}\n`);
const inRepoCheckout = fs.existsSync(path.join(REPO, ".git"));
try {
  if (process.env.KC_SKIP_ENGINE_DOWNLOAD === "1" || (inRepoCheckout && process.env.KC_POSTINSTALL_FORCE !== "1")) process.exit(0);
  const home = kcHome();
  fs.mkdirSync(path.join(home, "bin"), { recursive: true });
  if (!fs.existsSync(path.join(home, ".kerjacoy-home"))) fs.writeFileSync(path.join(home, ".kerjacoy-home"), "");
  try { (await import("../lib/userfiles.mjs")).seedUserFiles(path.join(home, "config")); } catch {}
  const bin = engineBin(home);
  const r = await ensureEngine({ home, bin, log: say, env: { ...process.env, XDG_STATE_HOME: path.join(home, "state"), XDG_DATA_HOME: path.join(home, "data"), XDG_CONFIG_HOME: path.join(home, "xdg-config"), XDG_CACHE_HOME: path.join(home, "cache"), OPENCODE_DISABLE_AUTOUPDATE: "1" } });
  if (!r.installed) say(`engine v${OC_VERSION} sudah ada (${bin}, ${r.flavor || "upstream"})`);
} catch (e) { say(`dilewati (${e.message}); engine akan dipasang saat 'kerjacoy' pertama kali dijalankan`); }
