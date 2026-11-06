import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import http from "node:http";
import * as PV from "../core/lib/providers.mjs";
import * as UI from "../core/lib/provider-ui.mjs";

test("provider: model terdeteksi dari /models (OpenAI Bearer, Anthropic x-api-key + paginasi), key salah → 401", async () => {
  const srv = http.createServer((q, r) => {
    const oa = q.headers.authorization === "Bearer k1", an = q.headers["x-api-key"] === "k1" && q.headers["anthropic-version"];
    r.setHeader("content-type", "application/json");
    if (q.url === "/v1/models" && oa) return r.end(JSON.stringify({ data: [{ id: "m-b" }, { id: "m-a" }] }));
    if (q.url.startsWith("/an/v1/models") && an) return r.end(JSON.stringify(q.url.includes("after_id") ? { data: [{ id: "c-2" }], has_more: false } : { data: [{ id: "c-1" }], has_more: true, last_id: "c-1" }));
    r.statusCode = 401; r.end("{}");
  });
  await new Promise((r) => srv.listen(0, "127.0.0.1", r));
  const base = `http://127.0.0.1:${srv.address().port}`, home = fs.mkdtempSync(path.join(os.tmpdir(), "kcprov-"));
  try {
    assert.equal((await PV.add(home, { name: "oa", type: "openai", baseURL: `${base}/v1`, key: "k1" })).join(), "m-a,m-b");
    assert.equal((await PV.add(home, { name: "an", type: "anthropic", baseURL: `${base}/an`, key: "k1" })).join(), "c-1,c-2");
    await assert.rejects(PV.add(home, { name: "x", type: "openai", baseURL: `${base}/v1`, key: "salah" }), /401/);
    const F = PV.files(home), mode = (f) => fs.statSync(f).mode & 0o777;
    assert.equal(mode(F.prov), 0o600); assert.equal(mode(F.cred), 0o600);
    assert.ok(!fs.readFileSync(F.prov, "utf8").includes("k1"), "key tidak di providers.json");
    const frag = PV.opencodeFragment(home, {});
    assert.ok(!JSON.stringify(frag.providers).includes("k1"), "key tidak di config");
    assert.equal(frag.providers.oa.settings.apiKey, "{env:KC_KEY_OA}");
    assert.equal(frag.env.KC_KEY_OA, "k1");
    assert.match(frag.providers.oa.package, /openai-compatible/); assert.match(frag.providers.an.package, /anthropic/);
    assert.ok(frag.providers.an.settings.baseURL.endsWith("/an/v1") && frag.providers.an.models["c-2"]);
    assert.equal(PV.opencodeFragment(home, { KC_KEY_OA: "envk" }).env.KC_KEY_OA, "envk");
    assert.ok(PV.remove(home, "an")); assert.ok(!PV.opencodeFragment(home, {}).providers.an);
    assert.ok(!JSON.parse(fs.readFileSync(F.cred, "utf8")).an, "hapus provider juga menghapus key");
  } finally { srv.close(); fs.rmSync(home, { recursive: true, force: true }); }
});

test("provider: 9router key dari credentials.json / env → KC_KEY_9ROUTER dan NINEROUTER_API_KEY (perbaikan 401)", () => {
  const h = fs.mkdtempSync(path.join(os.tmpdir(), "kc9r-"));
  fs.writeFileSync(path.join(h, "credentials.json"), JSON.stringify({ "9router": "k-file" }));
  const f1 = PV.opencodeFragment(h, {});
  assert.equal(f1.env.KC_KEY_9ROUTER, "k-file"); assert.equal(f1.env.NINEROUTER_API_KEY, "k-file");
  const h2 = fs.mkdtempSync(path.join(os.tmpdir(), "kc9r-"));
  const f2 = PV.opencodeFragment(h2, { NINEROUTER_API_KEY: "k-env" });
  assert.equal(f2.env.KC_KEY_9ROUTER, "k-env");
  assert.ok(!("KC_KEY_9ROUTER" in PV.opencodeFragment(h2, {}).env));
  const base = fs.readFileSync(new URL("../core/config/opencode.jsonc", import.meta.url), "utf8");
  assert.ok(base.includes('"apiKey": "{env:KC_KEY_9ROUTER}"') && !base.includes("NINEROUTER_API_KEY"), "config memakai {env:...} saja");
  for (const d of [h, h2]) fs.rmSync(d, { recursive: true, force: true });
});

test("provider: lokerEnv — mesin loker memakai provider aktif yang sama", () => {
  const h = fs.mkdtempSync(path.join(os.tmpdir(), "kcloker-"));
  fs.writeFileSync(path.join(h, "providers.json"), JSON.stringify({ providers: {
    stub: { type: "openai", baseURL: "http://127.0.0.1:20299/v1", models: ["model-kamu", "model-lain"] },
    lain: { type: "openai", baseURL: "http://x/v1", models: ["m2"] },
  } }));
  fs.writeFileSync(path.join(h, "credentials.json"), JSON.stringify({ stub: "k-stub", lain: "k-lain" }));
  assert.deepEqual(PV.lokerEnv(h, {}, "stub/model-lain"), {
    KERJACOY_LLM_BASE_URL: "http://127.0.0.1:20299/v1",
    KERJACOY_LLM_API_KEY: "k-stub",
    KERJACOY_LLM_MODEL: "model-lain",
  });
  // tanpa model → provider pertama + model pertamanya
  const d = PV.lokerEnv(h, {});
  assert.equal(d.KERJACOY_LLM_MODEL, "model-kamu");
  // env pengguna menang
  assert.deepEqual(PV.lokerEnv(h, { KERJACOY_LLM_API_KEY: "k-user", KERJACOY_LLM_BASE_URL: "http://u/v1", KERJACOY_LLM_MODEL: "mu" }), {});
  assert.deepEqual(PV.lokerEnv(h, { KERJACOY_LLM_MODEL: "mu" }), {
    KERJACOY_LLM_BASE_URL: "http://127.0.0.1:20299/v1",
    KERJACOY_LLM_API_KEY: "k-stub",
  });
  // tanpa provider → kosong
  assert.deepEqual(PV.lokerEnv(fs.mkdtempSync(path.join(os.tmpdir(), "kcloker-")), {}), {});
  fs.rmSync(h, { recursive: true, force: true });
});

test("timeout provider: default 300 s / 900 s / 3600 s, env override, nilai tidak valid → default", () => {
  assert.deepEqual(PV.providerTimeouts({}), { headerTimeout: 300000, chunkTimeout: 900000, timeout: 3600000 });
  assert.deepEqual(PV.providerTimeouts({ KC_HEADER_TIMEOUT_MS: "120000", KC_IDLE_TIMEOUT_MS: "600000", KC_TOTAL_TIMEOUT_MS: "7200000" }), { headerTimeout: 120000, chunkTimeout: 600000, timeout: 7200000 });
  assert.deepEqual(PV.providerTimeouts({ KC_HEADER_TIMEOUT_MS: "-1", KC_IDLE_TIMEOUT_MS: "abc", KC_TOTAL_TIMEOUT_MS: "1.5" }), PV.TIMEOUT_DEFAULTS);
});

test("menu provider: tombol (CRLF, backspace Windows, panah, Del, Esc, Ctrl+C) dan paste", () => {
  const P = (s, st) => UI.parseKeys(s, st).map((k) => k.t + (k.v !== undefined ? ":" + k.v : ""));
  assert.equal(P("\r\n").join(), "enter"); assert.equal(P("\b\x7f").join(), "backspace,backspace");
  assert.equal(P("\x1b[A\x1bOB\t\x1b[Z\x1b[3~\x1b\x03").join(), "up,down,tab,shift-tab,delete,esc,ctrl-c");
  const st0 = { paste: null };
  const pa = [...UI.parseKeys("\x1b[200~sk-ab", st0), ...UI.parseKeys("cd\r\n\x1b[201~", st0)];
  assert.equal(pa.length, 1); assert.equal(pa[0].v, "sk-abcd");
  let b = ""; for (const k of UI.parseKeys("ab\x1b[200~cd\r\n\x1b[201~\b")) b = UI.maskedStep(b, k).buf;
  assert.equal(b, "abc"); assert.equal(UI.mask(b), "•••");
});

test("menu provider: key tampil sebagai •, Enter simpan, Esc lewati, × hapus dengan konfirmasi", () => {
  const st = UI.initState({});
  const type = (s) => { for (const k of UI.parseKeys(s)) UI.reduce(st, k); };
  st.focus = "form:name"; type("My9R"); type("\t"); type("http://x/v1"); type("\t"); type("\x1b[200~SECRETKEY\x1b[201~"); type("\b");
  const fr = UI.render(st, 100, 30);
  assert.equal(st.name, "my9r"); assert.equal(st.key, "SECRETKE");
  assert.ok(fr.includes("••••••••") && !fr.includes("SECRETKE"));
  assert.equal(UI.reduce(st, { t: "enter" })?.save, true);
  assert.equal(UI.reduce(UI.initState({}), { t: "esc" })?.exit, true);
  const s2 = UI.initState({ a: { models: ["m"] }, b: { models: [] } }); s2.focus = "list:1";
  UI.reduce(s2, { t: "delete" }); assert.equal(s2.confirm, "b"); assert.equal(UI.reduce(s2, { t: "char", v: "y" })?.remove, "b");
  const s3 = UI.initState({ a: { models: ["m"] } }); s3.focus = "list:0"; UI.reduce(s3, { t: "char", v: "×" }); UI.reduce(s3, { t: "char", v: "n" });
  assert.equal(s3.confirm, null);
});

test("menu provider: tampilan minimal — wordmark KERJACOY (emas), latar hitam, 'N model ×', tanpa kotak", () => {
  const f0 = UI.render(UI.initState({ a: { models: ["m1", "m2"] } }), 100, 30);
  assert.ok(f0.includes("38;2;212;175;55"), "warna emas");
  assert.ok(f0.includes("48;2;0;0;0"));
  assert.match(f0, /a\s+2 model\s+×/);
  assert.ok(f0.includes("Tab pindah · Enter simpan · Del hapus · Esc lewati"));
  assert.ok(!/[┌┐└┘│]/.test(f0));
  const fa = UI.render(UI.initState({ a: { models: ["m"] } }), 100, 30, UI.ASCII);
  assert.ok(fa.includes("KERJACOY") && /1 model\s+x/.test(fa) && !/[^\x00-\x7f]/.test(fa));
  assert.equal(UI.pickGlyphs({}, "win32", 437), UI.ASCII); assert.equal(UI.pickGlyphs({ WT_SESSION: "1" }, "win32", 437), UI.UNI);
  assert.equal(UI.pickGlyphs({ KC_ASCII: "1" }, "linux"), UI.ASCII);
});
