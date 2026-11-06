#!/usr/bin/env node
/**
 * Regenerasi aset brand Kerjacoy dari data piksel `core/lib/logo.mjs`
 * (satu sumber kebenaran — logo terminal, SVG, dan patch engine).
 *
 *   node scripts/brand.mjs
 *
 * Menulis ulang `assets/brand/logo.svg` (kaca pembesar saja) dan
 * `assets/brand/banner.svg` (kaca pembesar + wordmark KERJACOY + strip
 * fade piksel emas redup di bawah), lalu mencetak fragmen untuk
 * `engine/patches/logo.patch` (objek `brand` + `logo.left` half-block).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { COLORS, FADE, MAG, wordPixels } from "../core/lib/logo.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PX = 12;
const GOLD = COLORS.g;

const count = (rows) => rows.join("").replace(/\./g, "").length;

function svgOpen(w, h) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="${w}" height="${h}" fill="#000000"/>`;
}

/** <rect> untuk tiap piksel "g" dalam rows, di offset (ox, oy). */
function rects(rows, ox, oy, fill = GOLD) {
  const out = [];
  rows.forEach((row, y) => {
    [...row].forEach((ch, x) => {
      if (ch !== ".") out.push(`<rect x="${ox + x * PX}" y="${oy + y * PX}" width="${PX}" height="${PX}" fill="${fill}"/>`);
    });
  });
  return out.join("");
}

// --- logo.svg: kaca pembesar saja ---
const magW = Math.max(...MAG.map((r) => r.length)) * PX;
const magH = MAG.length * PX;
fs.writeFileSync(path.join(ROOT, "assets/brand/logo.svg"),
  svgOpen(magW, magH) + rects(MAG, 0, 0) + "</svg>\n");

// --- banner.svg: kaca pembesar + KERJACOY + strip fade ---
const word = wordPixels();
const wordW = Math.max(...word.map((r) => r.length)) * PX;
const wordH = word.length * PX;
const gap = 3 * PX;
const width = PX + magW + gap + wordW + PX;
const height = magH;
const wordX = PX + magW + gap;
const wordY = Math.floor((height - wordH) / 2);
// Strip fade: 4 baris piksel emas redup di bawah (kepadatan mengecil).
const fade = [];
const fadeRows = [[3, 228], [6, 240], [12, 252], [24, 264]];
for (const [step, y] of fadeRows) {
  for (let x = PX; x < width - PX; x += step * PX) fade.push(`<rect x="${x}" y="${y}" width="${PX}" height="${PX}" fill="${FADE}"/>`);
}
fs.writeFileSync(path.join(ROOT, "assets/brand/banner.svg"),
  svgOpen(width, height) + rects(MAG, PX, 0) + rects(word, wordX, wordY) + fade.join("") + "</svg>\n");

// --- fragmen patch: brand + logo.left (half-block dari wordmark) ---
const half = [];
for (let y = 0; y < word.length; y += 2) {
  let s = "";
  for (let x = 0; x < word[0].length; x++) {
    const t = word[y][x] !== ".", b = (word[y + 1] ?? "")[x] !== ".";
    s += t && b ? "█" : t ? "▀" : b ? "▄" : " ";
  }
  half.push(s.replace(/\s+$/, ""));
}
console.log(`logo.svg: ${count(MAG)} piksel emas, ${magW}x${magH}`);
console.log(`banner.svg: ${count(MAG) + count(word)} piksel emas + ${fade.length} fade, ${width}x${height}`);
console.log("--- brand (untuk logo.ts di patch) ---");
console.log(JSON.stringify({ colors: { g: GOLD }, mag: MAG, word }, null, 0));
console.log("--- logo.left (untuk logo.ts di patch) ---");
console.log(JSON.stringify(half));
