/**
 * Port & state "managed service" OpenCode milik Kerjacoy — terpisah dari OpenCode milik user.
 * OpenCode v2 TUI memakai background server (service.ensure) di port default 49374. Konfigurasi port dibaca dari
 * $OPENCODE_CONFIG_DIR/service.json, registrasi service dari $XDG_STATE_HOME/opencode/service.json.
 * Wrapper memberi keduanya direktori di KERJACOY_HOME, dan file ini memastikan port-nya BUKAN 49374 serta tidak
 * dipakai proses lain. Proses lain (mis. `opencode serve --service` milik user) tidak pernah disentuh/dimatikan.
 */
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import crypto from "node:crypto";

export const OPENCODE_DEFAULT_SERVICE_PORT = 49374;
export const PORT_BASE = 60000, PORT_SPAN = 5000;
const readJson = (f) => { try { return JSON.parse(fs.readFileSync(f, "utf8")); } catch { return null; } };
const alive = (pid) => { try { process.kill(pid, 0); return true; } catch (e) { return e.code === "EPERM"; } };

/** Port deterministik per KERJACOY_HOME di rentang 60000–64999 (Lumitome memakai 50000–59999) (stabil antar-jalan, beda antar-instalasi). */
export function derivePort(home) {
  const h = crypto.createHash("sha256").update(path.resolve(home)).digest();
  return PORT_BASE + (h.readUInt32BE(0) % PORT_SPAN);
}

/** true bila port bisa di-bind di host (tidak dipakai siapa pun). */
export function isFree(port, host = "127.0.0.1") {
  return new Promise((resolve) => {
    const s = net.createServer(); s.unref();
    s.once("error", () => resolve(false));
    s.listen({ port, host, exclusive: true }, () => s.close(() => resolve(true)));
  });
}
const freePort = (host) => new Promise((resolve, reject) => { const s = net.createServer(); s.unref(); s.once("error", reject); s.listen(0, host, () => { const p = s.address().port; s.close(() => resolve(p)); }); });

/** Service Kerjacoy sendiri sedang hidup di port ini (registrasi di state Kerjacoy, pid hidup)? */
export function ownServiceOn(stateHome, port) {
  const reg = readJson(path.join(stateHome, "opencode", "service.json"));
  if (!reg || !reg.url || !reg.pid) return false;
  try { return Number(new URL(reg.url).port) === port && alive(reg.pid); } catch { return false; }
}

/**
 * Pastikan $cfgDir/service.json punya port milik Kerjacoy. Mengembalikan {port, changed, reason}.
 * Urutan: KC_SERVICE_PORT → port tersimpan (bila ≠49374 & bebas / dipakai service Kerjacoy sendiri)
 * → port deterministik (+19 percobaan) → port acak dari OS. Field lain (password, env) dipertahankan.
 */
export async function ensureServicePort({ home, cfgDir, stateHome, host = "127.0.0.1", env = process.env }) {
  const file = path.join(cfgDir, "service.json");
  const cfg = readJson(file) || {};
  const usable = async (p) => Number.isInteger(p) && p > 0 && p < 65536 && p !== OPENCODE_DEFAULT_SERVICE_PORT && !(p >= 50000 && p < 60000) && (ownServiceOn(stateHome, p) || await isFree(p, host));
  let port, reason;
  const forced = Number(env.KC_SERVICE_PORT || 0);
  if (forced) { port = forced; reason = "KC_SERVICE_PORT"; }
  else if (await usable(cfg.port)) { port = cfg.port; reason = "tersimpan"; }
  else {
    const base = derivePort(home);
    for (let i = 0; i < 20 && !port; i++) { const p = PORT_BASE + ((base - PORT_BASE + i * 7) % PORT_SPAN); if (await usable(p)) { port = p; reason = "deterministik"; } }
    if (!port) { port = await freePort(host); reason = "acak"; }
  }
  const changed = cfg.port !== port || (cfg.hostname && cfg.hostname !== host);
  if (changed) {
    fs.mkdirSync(cfgDir, { recursive: true, mode: 0o700 });
    const tmp = `${file}.${process.pid}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify({ ...cfg, port, hostname: host }, null, 2) + "\n", { mode: 0o600 });
    fs.renameSync(tmp, file);
  }
  return { port, changed, reason, file };
}
