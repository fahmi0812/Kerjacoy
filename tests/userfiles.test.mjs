import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import http from "node:http";
import cp from "node:child_process";
import * as UF from "../core/lib/userfiles.mjs";
import * as SC from "../core/lib/service-ctl.mjs";

const ROOT = path.resolve(new URL("..", import.meta.url).pathname);
const WRAP = path.join(ROOT, "core/bin/kerjacoy.mjs");
const tmp = (p) => fs.mkdtempSync(path.join(os.tmpdir(), p));
const TPL = fs.readFileSync(path.join(ROOT, "core/template/AGENTS.md"), "utf8");

test("template: AGENTS.md netral + bisa diedit; skills/README.md + skill kerjacoy", () => {
  assert.match(TPL, /MILIKMU/); assert.match(TPL, /rahasia/);
  const files = fs.readdirSync(path.join(ROOT, "core/template/skills"));
  assert.deepEqual(files.sort(), ["README.md", "kerjacoy"]);
  assert.match(fs.readFileSync(path.join(ROOT, "core/template/skills/README.md"), "utf8"), /SKILL\.md[\s\S]*name:[\s\S]*description:/);
  const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"));
  assert.ok(pkg.files.includes("core/"));
});

test("seed: buat bila belum ada; kedua kali menjaga edit user + skill user", () => {
  const cfg = path.join(tmp("kcuf-"), "config");
  assert.deepEqual(UF.seedUserFiles(cfg), { agents: "created", skills: "created", agent: "created", profil: "created" });
  assert.equal(fs.readFileSync(path.join(cfg, "AGENTS.md"), "utf8"), TPL);
  assert.ok(fs.existsSync(path.join(cfg, "skills", "README.md")));
  assert.ok(fs.existsSync(path.join(cfg, "skills", "kerjacoy", "SKILL.md")));
  assert.ok(fs.existsSync(path.join(cfg, "agent", "pemburu-kerja.md")));
  assert.ok(fs.existsSync(path.join(cfg, "profil", "contoh-umum.yaml")));
  // user mengedit + menambah skill + menghapus README
  fs.writeFileSync(path.join(cfg, "AGENTS.md"), "punyaku\n");
  fs.mkdirSync(path.join(cfg, "skills", "s1")); fs.writeFileSync(path.join(cfg, "skills", "s1", "SKILL.md"), "---\nname: s1\ndescription: d\n---\n");
  assert.equal(UF.seedUserFiles(cfg).agents, "kept");
  assert.equal(fs.readFileSync(path.join(cfg, "AGENTS.md"), "utf8"), "punyaku\n");
  assert.ok(fs.existsSync(path.join(cfg, "skills", "s1", "SKILL.md")));
  // template baru + AGENTS.md user diubah → .new, file user tetap
  const tpl2 = tmp("kctpl-"); fs.mkdirSync(path.join(tpl2, "skills"));
  fs.writeFileSync(path.join(tpl2, "AGENTS.md"), "v2\n"); fs.writeFileSync(path.join(tpl2, "skills", "README.md"), "x");
  assert.equal(UF.seedUserFiles(cfg, tpl2).agents, "kept+new");
  assert.equal(fs.readFileSync(path.join(cfg, "AGENTS.md"), "utf8"), "punyaku\n");
  assert.equal(fs.readFileSync(path.join(cfg, "AGENTS.md.new"), "utf8"), "v2\n");
  assert.ok(fs.existsSync(path.join(cfg, "skills", "s1", "SKILL.md")));
  // AGENTS.md tidak diubah user → boleh ikut template baru
  const cfg2 = path.join(tmp("kcuf-"), "config"); UF.seedUserFiles(cfg2);
  assert.equal(UF.seedUserFiles(cfg2, tpl2).agents, "updated");
  assert.equal(fs.readFileSync(path.join(cfg2, "AGENTS.md"), "utf8"), "v2\n");
});

test("launcher: setiap start membuat AGENTS.md + skills/ di OPENCODE_CONFIG_DIR, tanpa menimpa", () => {
  const home = tmp("kch-"), userHome = tmp("kcuser-");
  const fake = path.join(home, "fake"); fs.writeFileSync(fake, `#!${process.execPath}\nrequire("fs").writeFileSync(process.env.FAKE_OUT, process.env.OPENCODE_CONFIG_DIR)\n`, { mode: 0o755 });
  const env = { PATH: process.env.PATH, HOME: userHome, KERJACOY_HOME: home, KC_OPENCODE: fake, FAKE_OUT: path.join(home, "o"), KC_ONBOARD: "0" };
  const run = () => cp.spawnSync(process.execPath, [WRAP, "run", "x"], { env, encoding: "utf8", input: "" });
  run();
  const cfg = fs.readFileSync(path.join(home, "o"), "utf8");
  assert.equal(cfg, path.join(home, "config"));
  assert.equal(fs.readFileSync(path.join(cfg, "AGENTS.md"), "utf8"), TPL);
  fs.writeFileSync(path.join(cfg, "AGENTS.md"), "edit\n"); fs.mkdirSync(path.join(cfg, "skills", "mine"));
  fs.writeFileSync(path.join(cfg, "skills", "mine", "SKILL.md"), "s");
  run();
  assert.equal(fs.readFileSync(path.join(cfg, "AGENTS.md"), "utf8"), "edit\n");
  assert.equal(fs.readFileSync(path.join(cfg, "skills", "mine", "SKILL.md"), "utf8"), "s");
});

// engine asli (opsional): KC_TEST_ENGINE=/path/opencode. Model palsu lokal (tanpa panggilan model sungguhan):
// periksa prompt sistem memuat <config>/AGENTS.md dan skill di <config>/skills/<nama>/SKILL.md.
const ENG = process.env.KC_TEST_ENGINE;
test("engine 2.2.4 membaca config/AGENTS.md dan config/skills/*/SKILL.md", { skip: !ENG && "set KC_TEST_ENGINE", timeout: 120000 }, async () => {
  const home = tmp("kceng-"), cfg = path.join(home, "config"); UF.seedUserFiles(cfg);
  fs.appendFileSync(path.join(cfg, "AGENTS.md"), "\nKC_AGENTS_PROBE\n");
  fs.mkdirSync(path.join(cfg, "skills", "probe"));
  fs.writeFileSync(path.join(cfg, "skills", "probe", "SKILL.md"), "---\nname: probe\ndescription: KC_SKILL_PROBE\n---\nx\n");
  let body = "";
  const srv = http.createServer((q, r) => { let b = ""; q.on("data", (d) => (b += d)); q.on("end", () => { body += b;
    r.setHeader("content-type", "text/event-stream");
    const ch = (delta, fin = null) => r.write(`data: ${JSON.stringify({ id: "x", object: "chat.completion.chunk", created: 1, model: "m", choices: [{ index: 0, delta, finish_reason: fin }] })}\n\n`);
    ch({ role: "assistant", content: "ok" }); ch({}, "stop"); r.end("data: [DONE]\n\n"); }); });
  await new Promise((res) => srv.listen(0, "127.0.0.1", res));
  const env = { ...process.env, KERJACOY_HOME: home, KC_OPENCODE: ENG, KC_ONBOARD: "0", KC_KEY_9ROUTER: "dummy", KC_9ROUTER_URL: `http://127.0.0.1:${srv.address().port}/v1` };
  try {
    const paths = cp.spawnSync(process.execPath, [WRAP, "debug", "paths"], { env, encoding: "utf8", cwd: home });
    assert.match(paths.stdout, new RegExp(`config\\s+${cfg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    await new Promise((res) => { const c = cp.spawn(process.execPath, [WRAP, "run", "hi"], { env, cwd: home, stdio: "ignore" }); const t = setTimeout(() => c.kill(), 90000); c.on("exit", () => { clearTimeout(t); res(); }); });
    assert.ok(body.includes(`Instructions from: ${path.join(cfg, "AGENTS.md")}`), "AGENTS.md dimuat");
    assert.ok(body.includes("KC_AGENTS_PROBE") && body.includes("KC_SKILL_PROBE"));
  } finally { try { SC.stop(home); } catch {} srv.close(); }
});
