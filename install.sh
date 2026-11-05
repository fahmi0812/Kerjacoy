#!/usr/bin/env bash
# Kerjacoy installer (Linux / macOS / WSL2). Idempoten. Tidak menyentuh OpenCode atau Lumitome yang sudah ada:
#   engine OpenCode v2.2.4 terpin (SHA256, upstream) di $KERJACOY_HOME/bin (default ~/.kerjacoy),
#   launcher kerjacoy + kc di ~/.local/bin, mesin pencari kerja Python (loker) di $KERJACOY_HOME/venv.
# Pakai:  curl -fsSL https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.sh | bash
#   atau: bash install.sh [--dry-run] [--uninstall] [--no-node]
set -euo pipefail

KC_VERSION=2.0.0
OC_VERSION=2.2.4
NODE_VERSION=22.23.4
KERJACOY_HOME="${KERJACOY_HOME:-$HOME/.kerjacoy}"
KC_BIN_DIR="${KC_BIN_DIR:-$HOME/.local/bin}"
BIN="$KERJACOY_HOME/bin"
REPO_URL="${KC_REPO_URL:-https://github.com/fahmi0812/Kerjacoy.git}"
if [ -d "$KERJACOY_HOME" ] && [ -n "$(ls -A "$KERJACOY_HOME" 2>/dev/null)" ] && [ ! -f "$KERJACOY_HOME/.kerjacoy-home" ] && [ "${KC_FORCE_HOME:-0}" != 1 ]; then
  echo "[kerjacoy] $KERJACOY_HOME berisi file lain — pilih KERJACOY_HOME lain (atau KC_FORCE_HOME=1)" >&2; exit 1; fi

# ---------- mode remote: curl ... | bash ----------
_src="${BASH_SOURCE[0]:-}"
if [ -n "$_src" ] && [ -f "$_src" ]; then PROJECT="$(cd "$(dirname "$_src")" && pwd)"; else PROJECT=""; fi
case " $* " in *" --uninstall "*) _UN=1;; *) _UN=0;; esac
if [ "$_UN" = 0 ] && { [ -z "$PROJECT" ] || [ ! -f "$PROJECT/core/bin/kerjacoy.mjs" ]; }; then
  SRC="$KERJACOY_HOME/src"
  command -v git >/dev/null 2>&1 || { echo "[kerjacoy] butuh 'git' (apt/brew install git)" >&2; exit 1; }
  mkdir -p "$KERJACOY_HOME" && touch "$KERJACOY_HOME/.kerjacoy-home"
  if [ -d "$SRC/.git" ]; then git -C "$SRC" pull -q --ff-only origin main || true
  else git clone -q --depth 1 "$REPO_URL" "$SRC"; fi
  exec bash "$SRC/install.sh" "$@"
fi

UNINSTALL=0 DRY=0 DO_NODE=1
while [ $# -gt 0 ]; do case "$1" in
  --uninstall) UNINSTALL=1;; --dry-run) DRY=1;; --no-node) DO_NODE=0;;
  -h|--help) sed -n 2,5p "$0"; exit 0;; *) echo "opsi tidak dikenal: $1" >&2; exit 2;; esac; shift; done

say() { printf '\033[1m[kerjacoy]\033[0m %s\n' "$*"; }
ok()  { printf '  OK   %s\n' "$*"; }
warn(){ printf '  WARN %s\n' "$*"; }
die() { printf '  FAIL %s\n' "$*" >&2; exit 1; }

OS="$(uname -s)"; ARCH="$(uname -m)"
case "$OS" in Linux) OS=linux;; Darwin) OS=darwin;; *) die "OS tidak didukung: $OS (Windows: npm install -g, lihat README)";; esac
case "$ARCH" in x86_64|amd64) ARCH=x64;; aarch64|arm64) ARCH=arm64;; *) die "arsitektur tidak didukung: $ARCH";; esac

if [ "$UNINSTALL" = 1 ]; then
  for l in "$KC_BIN_DIR/kerjacoy" "$KC_BIN_DIR/kc" "$KC_BIN_DIR/loker"; do
    if [ -f "$l" ] && grep -q "KC-LAUNCHER" "$l"; then rm -f "$l"; ok "hapus $l"; fi
  done
  if [ -f "$KERJACOY_HOME/.kerjacoy-home" ]; then rm -rf "$KERJACOY_HOME"; ok "hapus $KERJACOY_HOME"; else warn "$KERJACOY_HOME tanpa marker — tidak dihapus"; fi
  exit 0
fi
say "Kerjacoy $KC_VERSION · $OS-$ARCH · KERJACOY_HOME=$KERJACOY_HOME"
command -v curl >/dev/null || die "butuh curl"; command -v tar >/dev/null || die "butuh tar"
sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fetch() { # url sha
  local f="$TMP/$(basename "$1")"
  [ "$DRY" = 1 ] && { echo "  (dry-run) unduh $1"; return 0; }
  curl -fsSL --retry 3 -o "$f" "$1" || die "unduh gagal: $1"
  [ "$(sha256 "$f")" = "$2" ] || die "SHA256 tidak cocok: $(basename "$1")"
  ok "SHA256 cocok $(basename "$1")"
}
mkdir -p "$BIN"; [ "$DRY" = 1 ] || touch "$KERJACOY_HOME/.kerjacoy-home"

# ---------- engine OpenCode v2.2.4 (upstream; build Kerjacoy engine-2.2.4-kc.1 belum dirilis) ----------
up_asset() { case "$OS-$ARCH" in
  linux-x64) echo "opencode-linux-x64.tar.gz 1b70ce4a88e27c3643c2bb61c757dfe173b4e3629926ce808d45f3774d87826e";;
  linux-arm64) echo "opencode-linux-arm64.tar.gz 81edcae078f36356cde3cf57d0cc6627896b18d1bddf47317cb025c56fcffd93";;
  darwin-x64) echo "opencode-darwin-x64.zip 2be9b7671f94a9636b85ff31fcfce613f197c5204ec90291982d692010d072fd";;
  darwin-arm64) echo "opencode-darwin-arm64.zip 4e093cae2931773c354896d98e7da0cfa3607c110aeaf255ba07f9c2d2238219";; esac; }
FLAVOR=upstream; BASE="https://github.com/anomalyco/opencode/releases/download/v$OC_VERSION"; PICK="$(up_asset)"
say "1/4 engine OpenCode v$OC_VERSION ($FLAVOR)"
oc() { XDG_DATA_HOME="$KERJACOY_HOME/data" XDG_CONFIG_HOME="$KERJACOY_HOME/xdg-config" XDG_STATE_HOME="$KERJACOY_HOME/state" XDG_CACHE_HOME="$KERJACOY_HOME/cache" \
  OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_MODELS_FETCH=1 "$BIN/opencode" "$@"; }
if [ -x "$BIN/opencode" ] && oc --version 2>/dev/null | grep -q "$OC_VERSION" && [ "$(cat "$BIN/opencode.flavor" 2>/dev/null || echo upstream)" = "$FLAVOR" ]; then ok "sudah terpasang"
else
  set -- $PICK
  fetch "$BASE/$1" "$2"
  if [ "$DRY" = 0 ]; then
    mkdir -p "$TMP/oc"
    case "$1" in *.zip) unzip -qo "$TMP/$1" -d "$TMP/oc";; *) tar -xzf "$TMP/$1" -C "$TMP/oc";; esac
    rm -f "$BIN/opencode"; install -m 0755 "$(find "$TMP/oc" -type f -name opencode | head -1)" "$BIN/opencode"
    echo "$FLAVOR" > "$BIN/opencode.flavor"
    oc --version | grep -q "$OC_VERSION" || die "versi engine tidak sesuai"; ok "engine $(oc --version)"
  fi
fi

# ---------- Node >= 22.6 ----------
say "2/4 Node.js (>= 22.6)"
NODE_DIR="$KERJACOY_HOME/node-v$NODE_VERSION-$OS-$ARCH"; NODE_PATH_LINE=""
node_ok() { "$1" -e 'const [a,b]=process.versions.node.split(".").map(Number);process.exit(a>22||(a===22&&b>=6)?0:1)' 2>/dev/null; }
if [ -x "$NODE_DIR/bin/node" ]; then ok "node lokal $("$NODE_DIR/bin/node" -v)"; NODE_PATH_LINE="export PATH=\"$NODE_DIR/bin:\$PATH\""
elif command -v node >/dev/null && node_ok node; then ok "node sistem $(node -v)"
elif [ "$DO_NODE" = 1 ]; then
  case "$OS-$ARCH" in
    linux-x64) nf=node-v$NODE_VERSION-linux-x64.tar.xz;; linux-arm64) nf=node-v$NODE_VERSION-linux-arm64.tar.xz;;
    darwin-x64) nf=node-v$NODE_VERSION-darwin-x64.tar.gz;; darwin-arm64) nf=node-v$NODE_VERSION-darwin-arm64.tar.gz;; esac
  nb="https://nodejs.org/dist/v$NODE_VERSION"
  if [ "$DRY" = 0 ]; then
    curl -fsSL --retry 3 -o "$TMP/$nf" "$nb/$nf" && curl -fsSL -o "$TMP/SHASUMS256.txt" "$nb/SHASUMS256.txt" || die "unduh node gagal"
    grep -q "^$(sha256 "$TMP/$nf")  $nf\$" "$TMP/SHASUMS256.txt" || die "SHA256 node tidak cocok"
    tar -xf "$TMP/$nf" -C "$KERJACOY_HOME"; ok "node $("$NODE_DIR/bin/node" -v)"
  fi
  NODE_PATH_LINE="export PATH=\"$NODE_DIR/bin:\$PATH\""
else die "Node >= 22.6 tidak ada (hapus --no-node)"; fi

# ---------- launcher: kerjacoy + alias kc (bila nama itu belum dipakai) ----------
say "3/4 launcher $KC_BIN_DIR"
if [ "$DRY" = 0 ]; then
  printf '%s\n' "$NODE_PATH_LINE" > "$KERJACOY_HOME/env.sh"
  mkdir -p "$KC_BIN_DIR"
  for name in kerjacoy kc; do
    L="$KC_BIN_DIR/$name"
    if [ -e "$L" ] && ! grep -q "KC-LAUNCHER" "$L" 2>/dev/null; then warn "$L sudah ada dan bukan milik Kerjacoy — dilewati"; continue; fi
    if [ "$name" = kc ] && [ ! -e "$L" ] && command -v kc >/dev/null 2>&1; then warn "perintah 'kc' sudah ada di PATH — alias dilewati"; continue; fi
    printf '#!/usr/bin/env bash\n# KC-LAUNCHER (hapus: bash %s/install.sh --uninstall)\nexport KERJACOY_HOME="%s"\nexec "%s/core/bin/kerjacoy" "$@"\n' "$PROJECT" "$KERJACOY_HOME" "$PROJECT" > "$L"
    chmod 0755 "$L"; ok "$L"
  done
  case ":$PATH:" in *":$KC_BIN_DIR:"*) ;; *) warn "$KC_BIN_DIR belum di PATH: export PATH=\"$KC_BIN_DIR:\$PATH\"";; esac
fi
# AGENTS.md + skills + agent + profil (hanya dibuat bila belum ada; milik user tidak pernah ditimpa/dihapus)
if [ "$DRY" = 0 ]; then
  NODE_BIN=node; [ -x "$NODE_DIR/bin/node" ] && NODE_BIN="$NODE_DIR/bin/node"
  "$NODE_BIN" -e 'import(require("url").pathToFileURL(process.argv[1]).href).then(m=>m.seedUserFiles(process.argv[2]))' "$PROJECT/core/lib/userfiles.mjs" "$KERJACOY_HOME/config" \
    && ok "AGENTS.md: $KERJACOY_HOME/config/AGENTS.md · skill: $KERJACOY_HOME/config/skills/kerjacoy/" || warn "AGENTS.md/skills dilewati"
fi

# ---------- mesin pencari kerja Python (loker) ----------
say "4/4 mesin loker (Python)"
VENV="$KERJACOY_HOME/venv"
if [ "$DRY" = 1 ]; then
  echo "  (dry-run) buat venv $VENV + pip install loker"
elif ! command -v python3 >/dev/null; then
  warn "python3 tidak ada — mesin loker dilewati (pasang python3 lalu jalankan install.sh lagi)"
else
  python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null || die "butuh Python >= 3.10"
  if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV" || die "gagal membuat venv"; ok "venv $VENV"; fi
  "$VENV/bin/pip" install -q --upgrade pip 2>/dev/null || true
  if "$VENV/bin/pip" install -q -e "$PROJECT" 2>/dev/null; then ok "loker terpasang ($("$VENV/bin/loker" --help >/dev/null 2>&1 && echo ok))"
  else
    warn "pip install biasa gagal — coba workaround jobspy"
    "$VENV/bin/pip" install -q --no-deps python-jobspy==1.4.1
    "$VENV/bin/pip" install -q pydantic tls-client requests markdownify regex curl_cffi
    "$VENV/bin/pip" install -q --no-deps -e "$PROJECT"
    ok "loker terpasang (workaround jobspy)"
  fi
  L="$KC_BIN_DIR/loker"
  if [ -e "$L" ] && ! grep -q "KC-LAUNCHER" "$L" 2>/dev/null; then warn "$L sudah ada dan bukan milik Kerjacoy — dilewati"
  else
    printf '#!/usr/bin/env bash\n# KC-LAUNCHER (hapus: bash %s/install.sh --uninstall)\nexec "%s/bin/loker" "$@"\n' "$PROJECT" "$VENV" > "$L"
    chmod 0755 "$L"; ok "$L"
  fi
fi
say "Selesai. Jalankan: kerjacoy"
