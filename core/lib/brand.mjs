/** Branding wrapper: judul jendela + default cli.json terisolasi (engine membaca OPENCODE_CONFIG_DIR/cli.json). */
export const TITLE = "Kerjacoy";
/** OSC 0 judul jendela/tab. */
export const titleSeq = (t = TITLE) => `\x1b]0;${String(t).replace(/[\x00-\x1f\x7f]/g, "")}\x07`;
/**
 * terminal.title:false (judul "Kerjacoy" tidak ditimpa engine) dan session.permissions:"autoaccept" (mode auto)
 * bila belum diatur. Pilihan user di /config dihormati. auto="0" → paksa "prompt"; auto="1" → paksa "autoaccept".
 */
export function seedCliConfig(cur, { auto } = {}) {
  const c = cur && typeof cur === "object" && !Array.isArray(cur) ? { ...cur } : {};
  let changed = false;
  if (!c.terminal || typeof c.terminal !== "object" || c.terminal.title === undefined) { c.terminal = { ...(c.terminal || {}), title: false }; changed = true; }
  const s = c.session && typeof c.session === "object" ? { ...c.session } : {};
  const want = auto === "0" ? "prompt" : auto === "1" ? "autoaccept" : s.permissions ?? "autoaccept";
  if (s.permissions !== want) { s.permissions = want; c.session = s; changed = true; }
  return { config: c, changed };
}
