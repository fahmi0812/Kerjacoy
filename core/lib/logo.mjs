/**
 * Logo Kerjacoy — konsep #1 "Gold Hunter" (dipilih Fahmi 2026-11-06):
 * kaca pembesar piksel EMAS + wordmark piksel "KERJACOY" emas di atas hitam,
 * digambar dengan half-block (▀ ▄ █) — 2 piksel per sel. Dipakai menu provider,
 * updater, dan patch engine. Kaca pembesar dipertahankan — metafora "berburu" loker.
 */
export const COLORS = { g: "#D4AF37" };
/** Emas redup untuk strip fade di banner (bukan wordmark). */
export const FADE = "#8C6D1F";
export const MAG = [".....gggggg.....", "...gg......gg...", "..g..........g..", "..g..........g..",
  ".g............g.", ".g............g.", ".g............g.", ".g............g.",
  "..g..........g..", "..g..........g..", "...gg......gg...", ".....gggggg.....",
  ".......gg.......", "........gg......", ".........gg.....", "..........gg....",
  "...........gg...", "............gg..", ".............g..", "................",
  "................", "................", "................", "................"];
// font piksel 6 baris (baris 5 = descender)
const F = {
  "0": [".##.", "#.##", "##.#", "#..#", ".##.", "...."],
  D: ["###.", "#..#", "#..#", "#..#", "###.", "...."],
  a: ["....", ".###", "#..#", "#..#", ".###", "...."],
  y: ["....", "#..#", "#..#", ".###", "...#", "###."],
  E: ["####", "#...", "###.", "#...", "####", "...."],
  x: ["....", "#..#", ".##.", ".##.", "#..#", "...."],
  p: ["....", "###.", "#..#", "###.", "#...", "#..."],
  l: ["#.", "#.", "#.", "#.", ".#", ".."],
  o: ["....", ".##.", "#..#", "#..#", ".##.", "...."],
  i: ["#", ".", "#", "#", "#", "."],
  t: [".#.", "###", ".#.", ".#.", "..#", "..."],
  K: ["#..#", "#.#.", "##..", "#.#.", "#..#", "...."],
  e: ["....", ".##.", "#..#", "####", "#...", ".##."],
  r: ["....", "###.", "#..#", "#...", "#...", "...."],
  j: ["..##", "...#", "...#", "...#", "#..#", ".##."],
  c: ["....", ".##.", "#...", "#...", "#...", ".##."],
  E: ["####", "#...", "###.", "#...", "####", "...."],
  R: ["###.", "#..#", "###.", "#.#.", "#..#", "...."],
  J: ["..##", "...#", "...#", "...#", "#..#", ".##."],
  A: [".##.", "#..#", "####", "#..#", "#..#", "...."],
  C: [".###", "#...", "#...", "#...", ".###", "...."],
  O: [".##.", "#..#", "#..#", "#..#", ".##.", "...."],
  Y: ["#...#", "#...#", ".#.#.", "..#..", "..#..", "....."],
};
export const WORD = "KERJACOY";
/** Bitmap wordmark (baris string, "g" = piksel emas, "." = kosong). */
export function wordPixels(text = WORD, c = "g") {
  const rows = ["", "", "", "", "", ""];
  [...text].forEach((ch, k) => { const g = F[ch]; for (let y = 0; y < 6; y++) rows[y] += (k ? "." : "") + g[y].replace(/#/g, c); });
  return rows;
}
/** Pixel rows → sel half-block: [[{ch, fg, bg}]] (fg/bg = kode warna atau null). */
export function cells(px) {
  const out = [];
  for (let y = 0; y < px.length; y += 2) {
    const a = px[y], b = px[y + 1] || "", row = [];
    for (let x = 0; x < Math.max(a.length, b.length); x++) {
      const t = a[x] && a[x] !== "." ? a[x] : null, u = b[x] && b[x] !== "." ? b[x] : null;
      if (!t && !u) row.push({ ch: " ", fg: null, bg: null });
      else if (t && !u) row.push({ ch: "▀", fg: t, bg: null });
      else if (!t && u) row.push({ ch: "▄", fg: u, bg: null });
      else if (t === u) row.push({ ch: "█", fg: t, bg: null });
      else row.push({ ch: "▀", fg: t, bg: u });
    }
    out.push(row);
  }
  return out;
}
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const to256 = ([r, g, b]) => 16 + 36 * Math.round(r / 51) + 6 * Math.round(g / 51) + Math.round(b / 51);
const sgr = (code, hex, mode) => { const c = rgb(hex); return mode === "256" ? `\x1b[${code === 38 ? 38 : 48};5;${to256(c)}m` : `\x1b[${code};2;${c[0]};${c[1]};${c[2]}m`; };
/** Satu baris sel → string ANSI (mode "truecolor" | "256" | "none"). */
export function ansiRow(row, mode = "truecolor") {
  if (mode === "none") return row.map((c) => c.ch).join("").replace(/\s+$/, "");
  return row.map((c) => (c.fg ? sgr(38, COLORS[c.fg], mode) + (c.bg ? sgr(48, COLORS[c.bg], mode) : "") + c.ch + "\x1b[0m" : c.ch)).join("").replace(/\s+$/, "");
}
/** Splash: kaca pembesar di kiri, wordmark di kanan (sejajar baris tengah). Mengembalikan array baris. */
export function splashLines(mode = "truecolor", { gap = 3 } = {}) {
  const mag = cells(MAG), word = cells(wordPixels()), top = Math.max(0, Math.floor((mag.length - word.length) / 2));
  const w0 = Math.max(...mag.map((r) => r.length));
  return mag.map((row, i) => { const w = word[i - top]; const l = ansiRow(row, mode); if (!w) return l;
    return l + " ".repeat(w0 - [...ansiRow(row, "none")].length + gap) + ansiRow(w, mode); });
}
/** Wordmark saja (untuk layar sempit / menu). */
export const wordLines = (mode = "truecolor") => cells(wordPixels()).map((r) => ansiRow(r, mode));
