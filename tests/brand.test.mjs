import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import cp from "node:child_process";
import * as L from "../core/lib/logo.mjs";
import * as EN from "../core/lib/engine.mjs";

const ROOT = path.resolve(new URL("..", import.meta.url).pathname);
const read = (f) => fs.readFileSync(path.join(ROOT, f), "utf8");

test("logo: kaca pembesar hijau limau, wordmark Kerjacoy di kanan", () => {
  const lines = L.splashLines("truecolor"), plain = L.splashLines("none");
  assert.ok(lines.join("").includes("38;2;238;232;220") && lines.join("").includes("38;2;124;255;63"));
  assert.ok(L.MAG.some((r) => r.includes("g")) && !L.MAG.some((r) => r.includes("r")));
  const wordRows = plain.filter((l) => l.length > 40);
  assert.equal(wordRows.length, 3, "wordmark 3 baris di samping kaca pembesar");
  assert.ok(L.wordPixels().every((r) => r.length === L.wordPixels()[0].length));
  assert.equal(L.wordLines("none").length, 3);
  assert.equal(L.WORD, "Kerjacoy");
});

test("patch engine: hanya logo diganti (logo.ts + component/logo.tsx), data kaca pembesar sama dengan core/lib/logo.mjs", () => {
  const p = read("engine/patches/logo.patch");
  const files = [...p.matchAll(/^diff --git a\/(\S+)/gm)].map((m) => m[1]).sort();
  assert.deepEqual(files, ["packages/tui/src/component/logo.tsx", "packages/tui/src/logo.ts"]);
  assert.ok(p.includes(JSON.stringify(L.MAG)) && p.includes(L.COLORS.w) && p.includes(L.COLORS.g));
  assert.ok(!/hat|fedora|B2181E/.test(p));
});

test("aset brand: banner + logo SVG (teks, dari data piksel yang sama)", () => {
  for (const f of ["assets/brand/banner.svg", "assets/brand/logo.svg"]) {
    const s = read(f);
    assert.ok(s.startsWith("<svg") && s.includes("</svg>"), f);
    assert.ok(s.includes(L.COLORS.g) && s.includes('fill="#000000"'), f);
    assert.ok((s.match(/<rect/g) || []).length > 40, f);
  }
  const banner = read("assets/brand/banner.svg");
  assert.ok(banner.includes(L.COLORS.w), "banner ada wordmark bone-white");
  // jumlah piksel wordmark di SVG sama dengan data wordPixels()
  const wordPx = L.wordPixels().join("").replace(/\./g, "").length;
  const wordRects = (banner.match(new RegExp(`fill="${L.COLORS.w}"`, "g")) || []).length;
  assert.equal(wordRects, wordPx, "tiap piksel wordmark jadi satu <rect>");
});

test("engine terpin 2.2.4: upstream default, build Kerjacoy belum dirilis", async () => {
  assert.equal(EN.OC_VERSION, "2.2.4");
  assert.deepEqual(EN.KC_PINS, {}, "build engine-2.2.4-kc.1 belum dirilis — pin kosong");
  assert.equal(EN.engineFlavor({}), "upstream", "default upstream");
  assert.equal(EN.engineFlavor({ KC_ENGINE: "upstream" }), "upstream");
  assert.equal(EN.engineFlavor({ KC_ENGINE: "kc" }), "kc");
  // tanpa pin, flavor kc jatuh ke upstream
  assert.match(EN.assetFor("2.2.4", "linux", "x64", "kc").url, /anomalyco\/opencode\/releases\/download\/v2\.2\.4/);
  assert.match(EN.assetFor("2.2.4", "linux", "x64", "upstream").url, /anomalyco\/opencode\/releases\/download\/v2\.2\.4/);
  assert.match(EN.assetFor("2.2.4", "linux", "x64", "upstream").sha256, /^[0-9a-f]{64}$/);
  await assert.rejects(EN.installEngine({ home: "/tmp/kc-x", dst: "/tmp/kc-x/oc", log: () => {}, fetchImpl: async () => ({ ok: true, arrayBuffer: async () => new TextEncoder().encode("x").buffer }) }), /SHA256 tidak cocok/);
});

test("installer: sintaks bash, engine upstream, launcher kerjacoy + alias kc + loker, uninstall hanya bermarker", () => {
  const sh = read("install.sh");
  assert.equal(cp.spawnSync("bash", ["-n", path.join(ROOT, "install.sh")]).status, 0);
  assert.ok(sh.includes("OC_VERSION=2.2.4") && sh.includes("anomalyco/opencode/releases/download/v$OC_VERSION"));
  assert.ok(/for name in kerjacoy kc/.test(sh) && sh.includes("KC-LAUNCHER") && sh.includes("command -v kc"));
  assert.ok(sh.includes("mesin loker") && sh.includes("venv") && sh.includes("python-jobspy==1.4.1"));
  assert.ok(!/codebase-memory|skill-index|uvx|bwrap/.test(sh));
  const pkg = JSON.parse(read("package.json"));
  assert.equal(pkg.bin["kerjacoy"], "core/bin/cli.mjs"); assert.equal(pkg.bin["kc"], "core/bin/cli.mjs");
  assert.equal(pkg.version, read("VERSION").trim());
  assert.ok(read("core/bin/kerjacoy.mjs").includes(`VERSION = "${pkg.version}"`) && sh.includes(`KC_VERSION=${pkg.version}`));
});

test("distribusi: hanya skill kerjacoy + agent pemburu-kerja; tanpa MCP/rules/sandbox/plugin; tanpa nama Lumitome di teks pengguna", () => {
  for (const d of ["core/config/skills", "core/config/agents", "core/config/rules", "core/config/plugins", "harness", "router"]) assert.ok(!fs.existsSync(path.join(ROOT, d)), d);
  const W = read("core/bin/kerjacoy.mjs");
  assert.ok(!/mcp|bwrap|sandbox|orchestrator/i.test(W));
  assert.deepEqual(fs.readdirSync(path.join(ROOT, "core/template/skills")).sort(), ["README.md", "kerjacoy"]);
  assert.deepEqual(fs.readdirSync(path.join(ROOT, "core/template/agent")), ["pemburu-kerja.md"]);
  assert.ok(fs.readdirSync(path.join(ROOT, "core/template/profil")).length >= 1);
  const files = cp.execFileSync("git", ["ls-files", "core", "install.sh", "README.md", "package.json"], { cwd: ROOT, encoding: "utf8" }).split("\n").filter(Boolean);
  const code = (f) => read(f).split("\n").filter((l) => !/^\s*(\/\/|#|\*|\/\*)/.test(l)).join("\n");
  const bad = files.filter((f) => /lumitome/i.test(code(f).replace(/Lumitome memakai 50000–59999|~\/\.lumitome|Lumitome[^\n]*berdampingan|berdampingan[^\n]*Lumitome/gi, "")));
  // README boleh menyebut Lumitome hanya di bagian "berdampingan"
  assert.deepEqual(bad.filter((f) => f !== "README.md"), []);
});
