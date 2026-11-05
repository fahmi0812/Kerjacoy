#!/usr/bin/env bash
# Kerjacoy installer (Linux / macOS / WSL2). Idempoten:
#   repo di $KERJACOY_HOME/src (default ~/.kerjacoy), venv di $KERJACOY_HOME/venv,
#   launcher di ~/.local/bin: kerjacoy (+ alias kc bila nama itu belum dipakai).
# Pakai:  curl -fsSL https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.sh | bash
#   atau: bash install.sh [--dry-run] [--uninstall]
set -euo pipefail

KERJACOY_VERSION=1.2.0
KERJACOY_HOME="${KERJACOY_HOME:-$HOME/.kerjacoy}"
BIN_DIR="${KERJACOY_BIN_DIR:-$HOME/.local/bin}"
REPO_URL="${KERJACOY_REPO_URL:-https://github.com/fahmi0812/Kerjacoy.git}"
if [ -d "$KERJACOY_HOME" ] && [ -n "$(ls -A "$KERJACOY_HOME" 2>/dev/null)" ] && [ ! -f "$KERJACOY_HOME/.kerjacoy-home" ] && [ "${KERJACOY_FORCE_HOME:-0}" != 1 ]; then
  echo "[kerjacoy] $KERJACOY_HOME berisi file lain — pilih KERJACOY_HOME lain (atau KERJACOY_FORCE_HOME=1)" >&2; exit 1; fi

# ---------- mode remote: curl ... | bash ----------
_src="${BASH_SOURCE[0]:-}"
if [ -n "$_src" ] && [ -f "$_src" ]; then PROJECT="$(cd "$(dirname "$_src")" && pwd)"; else PROJECT=""; fi
case " $* " in *" --uninstall "*) _UN=1;; *) _UN=0;; esac
if [ "$_UN" = 0 ] && { [ -z "$PROJECT" ] || [ ! -f "$PROJECT/loker_plus/cli.py" ]; }; then
  SRC="$KERJACOY_HOME/src"
  command -v git >/dev/null 2>&1 || { echo "[kerjacoy] butuh 'git' (apt/brew install git)" >&2; exit 1; }
  mkdir -p "$KERJACOY_HOME" && touch "$KERJACOY_HOME/.kerjacoy-home"
  if [ -d "$SRC/.git" ]; then git -C "$SRC" pull -q --ff-only origin main || true
  else git clone -q --depth 1 "$REPO_URL" "$SRC"; fi
  exec bash "$SRC/install.sh" "$@"
fi

UNINSTALL=0 DRY=0
while [ $# -gt 0 ]; do case "$1" in
  --uninstall) UNINSTALL=1;; --dry-run) DRY=1;;
  -h|--help) sed -n 2,7p "$0"; exit 0;; *) echo "opsi tidak dikenal: $1" >&2; exit 2;; esac; shift; done

say() { printf '\033[1m[kerjacoy]\033[0m %s\n' "$*"; }
ok()  { printf '  OK   %s\n' "$*"; }
warn(){ printf '  WARN %s\n' "$*"; }
die() { printf '  FAIL %s\n' "$*" >&2; exit 1; }

OS="$(uname -s)"
case "$OS" in Linux) OS=linux;; Darwin) OS=darwin;; *) die "OS tidak didukung: $OS (Windows: install.ps1, lihat README)";; esac

if [ "$UNINSTALL" = 1 ]; then
  for l in "$BIN_DIR/kerjacoy" "$BIN_DIR/kc"; do
    if [ -f "$l" ] && grep -q "KC-LAUNCHER" "$l"; then rm -f "$l"; ok "hapus $l"; fi
  done
  if [ -f "$KERJACOY_HOME/.kerjacoy-home" ]; then rm -rf "$KERJACOY_HOME"; ok "hapus $KERJACOY_HOME"; else warn "$KERJACOY_HOME tanpa marker — tidak dihapus"; fi
  exit 0
fi

say "Kerjacoy $KERJACOY_VERSION · $OS · KERJACOY_HOME=$KERJACOY_HOME"
command -v git >/dev/null || die "butuh git"
command -v python3 >/dev/null || die "butuh python3 (>= 3.10)"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || die "butuh Python >= 3.10 (terpasang: $(python3 --version 2>&1))"

SRC="${PROJECT:-$KERJACOY_HOME/src}"
VENV="$KERJACOY_HOME/venv"

# ---------- 1/3 repo ----------
say "1/3 repo"
if [ "$DRY" = 1 ]; then echo "  (dry-run) clone/pull $REPO_URL -> $SRC"
elif [ -d "$SRC/.git" ]; then
  if git -C "$SRC" pull -q --ff-only origin main 2>/dev/null; then ok "repo diperbarui"
  else warn "repo tidak bisa ditarik (pakai versi lokal)"; fi
else git clone -q --depth 1 "$REPO_URL" "$SRC" && ok "repo di-clone"; fi

# ---------- 2/3 venv + pip ----------
say "2/3 venv + dependensi"
if [ "$DRY" = 1 ]; then echo "  (dry-run) buat venv $VENV, pip install -e $SRC"
else
  [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
  if ! "$VENV/bin/pip" install -q -e "$SRC" 2>/dev/null; then
    # Workaround konflik metadata numpy di python-jobspy (sudah teruji).
    warn "pip install biasa gagal — coba workaround jobspy"
    "$VENV/bin/pip" install -q --no-deps python-jobspy
    "$VENV/bin/pip" install -q pydantic tls-client requests markdownify regex curl_cffi
    "$VENV/bin/pip" install -q --no-deps -e "$SRC"
  fi
  "$VENV/bin/kerjacoy" --help >/dev/null && ok "kerjacoy terpasang di venv"
fi

# ---------- 3/3 launcher ----------
say "3/3 launcher $BIN_DIR"
if [ "$DRY" = 1 ]; then echo "  (dry-run) buat launcher kerjacoy (+ kc) di $BIN_DIR"
else
  mkdir -p "$BIN_DIR"
  for name in kerjacoy kc; do
    L="$BIN_DIR/$name"
    if [ -e "$L" ] && ! grep -q "KC-LAUNCHER" "$L" 2>/dev/null; then warn "$L sudah ada dan bukan milik Kerjacoy — dilewati"; continue; fi
    if [ "$name" = kc ] && [ ! -e "$L" ] && command -v kc >/dev/null 2>&1; then warn "perintah 'kc' sudah ada di PATH — alias dilewati"; continue; fi
    printf '#!/usr/bin/env bash\n# KC-LAUNCHER (hapus: bash %s/install.sh --uninstall)\nexec "%s/bin/kerjacoy" "$@"\n' "$SRC" "$VENV" > "$L"
    chmod 0755 "$L"; ok "$L"
  done
  case ":$PATH:" in *":$BIN_DIR:"*) ;; *) warn "$BIN_DIR belum di PATH: export PATH=\"$BIN_DIR:\$PATH\"";; esac
fi
say "Selesai. Jalankan: kerjacoy"
