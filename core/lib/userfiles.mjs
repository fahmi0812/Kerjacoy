/**
 * File milik user di config Kerjacoy (OPENCODE_CONFIG_DIR = $KERJACOY_HOME/config):
 *  - AGENTS.md  → instruksi global (engine 2.2.4 membaca <config>/AGENTS.md)
 *  - skills/    → skill user (engine memindai <config>/skills/<nama>/SKILL.md); dikirim kosong + README.md
 * Aturan: hanya DIBUAT bila belum ada. Tidak pernah menimpa/menghapus milik user.
 * AGENTS.md yang belum diubah user (hash = yang kita pasang) boleh diperbarui ke template baru;
 * yang sudah diubah user → template baru ditaruh sebagai AGENTS.md.new.
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

export const TEMPLATE_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "template");
const sha = (s) => crypto.createHash("sha256").update(s).digest("hex");

export function seedUserFiles(cfgDir, tplDir = TEMPLATE_DIR) {
  const res = { agents: "kept", skills: "kept", agent: "kept", profil: "kept" };
  fs.mkdirSync(cfgDir, { recursive: true, mode: 0o700 });
  const tpl = fs.readFileSync(path.join(tplDir, "AGENTS.md"), "utf8");
  const f = path.join(cfgDir, "AGENTS.md"), mark = path.join(cfgDir, ".AGENTS.md.sha256");
  if (!fs.existsSync(f)) { fs.writeFileSync(f, tpl); fs.writeFileSync(mark, sha(tpl)); res.agents = "created"; }
  else {
    const cur = fs.readFileSync(f, "utf8");
    let installed = ""; try { installed = fs.readFileSync(mark, "utf8").trim(); } catch {}
    if (cur !== tpl) {
      if (installed && sha(cur) === installed) { fs.writeFileSync(f, tpl); fs.writeFileSync(mark, sha(tpl)); res.agents = "updated"; }
      else if (installed !== sha(tpl)) { fs.writeFileSync(f + ".new", tpl); fs.writeFileSync(mark, sha(tpl)); res.agents = "kept+new"; } // template berubah
    }
  }
  const sd = path.join(cfgDir, "skills");
  if (!fs.existsSync(sd)) { fs.mkdirSync(sd, { recursive: true }); res.skills = "created"; }
  const rd = path.join(sd, "README.md");
  if (!fs.existsSync(rd)) fs.copyFileSync(path.join(tplDir, "skills", "README.md"), rd);
  // Skill + agent + profil Kerjacoy: salin bila belum ada, tidak pernah menimpa milik user.
  const salinBilaBaru = (asal, tujuan) => {
    if (!fs.existsSync(tujuan)) { fs.mkdirSync(path.dirname(tujuan), { recursive: true }); fs.copyFileSync(asal, tujuan); return true; }
    return false;
  };
  const skillSrc = path.join(tplDir, "skills", "kerjacoy", "SKILL.md");
  if (fs.existsSync(skillSrc) && salinBilaBaru(skillSrc, path.join(sd, "kerjacoy", "SKILL.md"))) res.skills = "created";
  const agentSrc = path.join(tplDir, "agent", "pemburu-kerja.md");
  if (fs.existsSync(agentSrc) && salinBilaBaru(agentSrc, path.join(cfgDir, "agent", "pemburu-kerja.md"))) res.agent = "created";
  const profilDir = path.join(tplDir, "profil");
  if (fs.existsSync(profilDir)) {
    for (const nama of fs.readdirSync(profilDir)) {
      if (salinBilaBaru(path.join(profilDir, nama), path.join(cfgDir, "profil", nama))) res.profil = "created";
    }
  }
  return res;
}
