"""Layar provider interaktif ala 0DayExploit (Python murni, tanpa dependensi).

Satu layar penuh: provider tersimpan + form tambah. Tab pindah, Enter simpan
(lalu tes koneksi + hitung model dari /models), Del hapus, Esc lewati.
API key tampil sebagai • per karakter (paste didukung). Jalan di Linux,
macOS, dan Windows (Terminal/PowerShell/cmd).
"""

from __future__ import annotations

import os
import re
import shutil
import sys

from .banner import BANNER
from .llm import DEFAULT_MODEL, LLMError

UNI = {"bullet": "•", "x": "×", "arrow": "›", "rule": "─", "ok": "✓",
       "bad": "✗", "dot": "·", "cur": "█", "ell": "…"}
ASCII = {"bullet": "*", "x": "x", "arrow": ">", "rule": "-", "ok": "OK",
         "bad": "X", "dot": "|", "cur": "_", "ell": "..."}


def pick_glyphs(env=None) -> dict:
    """Unicode bila konsol mendukung; ASCII bila tidak (konsol Windows lama)."""
    env = env if env is not None else os.environ
    if env.get("KERJACOY_ASCII") == "1":
        return ASCII
    if os.name == "nt":
        if env.get("WT_SESSION") or env.get("TERM_PROGRAM"):
            return UNI
        enc = sys.stdout.encoding or ""
        if "utf" not in enc.lower():
            return ASCII
    return UNI


def _bersihkan_paste(v: str) -> str:
    return re.sub(r"[\x00-\x1f\x7f]", "", str(v).replace("\r\n", "").replace("\r", "").replace("\n", "")).strip()


def mask(v: str, g: dict | None = None) -> str:
    g = g or UNI
    return g["bullet"] * len(str(v or ""))


def parse_keys(chunk, st: dict | None = None) -> list[dict]:
    """Urai potongan input terminal jadi token.

    Mengenali escape sequence VT (Linux/macOS/Windows Terminal/conhost),
    bracketed paste, CRLF, dan tombol kontrol.
    """
    st = st if st is not None else {"paste": None}
    s = chunk if isinstance(chunk, str) else chunk.decode("utf-8", "replace")
    out: list[dict] = []
    i = 0
    while i < len(s):
        if st["paste"] is not None:
            end = s.find("\x1b[201~", i)
            if end < 0:
                st["paste"] += s[i:]
                break
            st["paste"] += s[i:end]
            out.append({"t": "paste", "v": _bersihkan_paste(st["paste"])})
            st["paste"] = None
            i = end + 6
            continue
        if s.startswith("\x1b[200~", i):
            st["paste"] = ""
            i += 6
            continue
        c = s[i]
        if c == "\x1b":
            m = re.match(r"\x1b(?:\[([0-9;]*)([A-Za-z~])|O([A-Za-z]))", s[i:])
            if m:
                k = m.group(3) or m.group(2)
                n = m.group(1) or ""
                nama = {"A": "up", "B": "down", "C": "right", "D": "left",
                        "Z": "shift-tab", "H": "home", "F": "end"}.get(k)
                if nama is None and k == "~":
                    nama = {"3": "delete", "1": "home", "7": "home",
                            "4": "end", "8": "end"}.get(n.split(";")[0], "unknown")
                out.append({"t": nama or "unknown"})
                i += len(m.group(0))
                continue
            out.append({"t": "esc"})
            i += 1
            continue
        if c == "\r":
            out.append({"t": "enter"})
            i += 2 if i + 1 < len(s) and s[i + 1] == "\n" else 1
            continue
        if c == "\n":
            out.append({"t": "enter"})
            i += 1
            continue
        if c == "\t":
            out.append({"t": "tab"})
            i += 1
            continue
        if c in ("\x7f", "\b"):
            out.append({"t": "backspace"})
            i += 1
            continue
        if c == "\x03":
            out.append({"t": "ctrl-c"})
            i += 1
            continue
        if c == "\x15":
            out.append({"t": "clear"})
            i += 1
            continue
        if c == "\x16":
            i += 1
            continue
        if c < " ":
            i += 1
            continue
        j = i
        while j < len(s) and s[j] >= " " and s[j] != "\x7f" and s[j] != "\x1b":
            j += 1
        teks = s[i:j]
        out.append({"t": "paste", "v": teks} if len(teks) > 1 else {"t": "char", "v": teks})
        i = j
    return out


FIELDS = ["nama", "base_url", "key"]


def init_state(tersimpan: dict | None) -> dict:
    return {"tersimpan": tersimpan, "focus": "form:nama", "nama": "",
            "base_url": "", "key": "", "status": None, "confirm": None,
            "busy": False, "selesai": False}


def _urutan_fokus(st: dict) -> list[str]:
    urutan = (["tersimpan"] if st["tersimpan"] else []) + [f"form:{f}" for f in FIELDS]
    return urutan


def _pindah(st: dict, d: int) -> None:
    o = _urutan_fokus(st)
    i = o.index(st["focus"]) if st["focus"] in o else 0
    st["focus"] = o[(i + d) % len(o)]


def reduce(st: dict, k: dict):
    """Reducer murni: (state, token) -> aksi {simpan} | {hapus} | {keluar} | None."""
    if k["t"] == "ctrl-c":
        st["selesai"] = True
        return {"keluar": True}
    if st["busy"]:
        return None
    if st["confirm"]:
        if (k["t"] == "char" and k.get("v", "").lower() == "y") or k["t"] == "enter":
            nama = st["confirm"]
            st["confirm"] = None
            return {"hapus": nama}
        st["confirm"] = None
        st["status"] = None
        return None
    if k["t"] == "esc":
        st["selesai"] = True
        return {"keluar": True}
    if k["t"] in ("tab", "down"):
        _pindah(st, 1)
        return None
    if k["t"] in ("shift-tab", "up"):
        _pindah(st, -1)
        return None
    if st["focus"] == "tersimpan":
        if k["t"] in ("delete", "backspace") or (k["t"] == "char" and k.get("v") in ("x", "×")):
            st["confirm"] = st["tersimpan"].get("provider", "")
        return None
    if k["t"] == "enter":
        return {"simpan": True}
    f = st["focus"].split(":")[1]
    if k["t"] == "backspace":
        st[f] = st[f][:-1]
        return None
    if k["t"] == "clear":
        st[f] = ""
        return None
    if k["t"] in ("char", "paste"):
        v = _bersihkan_paste(k["v"]) if k["t"] == "paste" else k["v"]
        if f == "nama":
            v = v.lower()
        st[f] += v
        st["status"] = None
        return None
    return None


BOLD = "\x1b[1m"
DIM = "\x1b[2m"
REV = "\x1b[7m"
RST = "\x1b[0m"


def _vlen(s: str) -> int:
    return len(re.sub(r"\x1b\[[0-9;]*m", "", s))


def render(st: dict, cols: int = 80, rows: int = 24, g: dict | None = None) -> str:
    """Bingkai layar (string ANSI). Tanpa kotak/border; terpusat; latar hitam."""
    g = g or UNI
    L: list[str] = []
    W = min(64, cols - 4)
    if cols >= 70:
        for baris in BANNER.strip("\n").splitlines():
            L.append(baris)
    else:
        L.append(f"{BOLD}KERJACOY{RST}")
    L.append("")
    L.append(f"{DIM}Provider tersimpan{RST}")
    if not st["tersimpan"]:
        L.append(f"{DIM}  (belum ada){RST}")
    else:
        p = st["tersimpan"]
        on = st["focus"] == "tersimpan"
        txt = (f"{str(p.get('provider', '-'))[:20]:<20} "
               f"{str(p.get('model', '-'))[:24]:<24} {g['x']}")
        L.append(f"{REV}{g['arrow']} {txt}{RST}" if on else f"  {txt}")
    if st["confirm"]:
        L.append(f"  Hapus '{st['confirm']}'? y = ya, tombol lain = batal")
    L.append(f"{DIM}{g['rule'] * W}{RST}")
    L.append(f"{DIM}Tambah provider{RST}")

    def field(f: str, label: str, val: str) -> str:
        on = st["focus"] == f"form:{f}"
        return (f"{g['arrow'] if on else ' '} {label:<9} {g['arrow']} {val}"
                f"{g['cur'] if on else ''}")

    L.append(f"{DIM}Tipe      {g['arrow']} OpenAI (compatible){RST}")
    L.append(field("nama", "Nama", st["nama"]))
    placeholder = "" if st["focus"] == "form:base_url" else f"{DIM}http://127.0.0.1:20128/v1{RST}"
    L.append(field("base_url", "Base URL", st["base_url"] or placeholder))
    km = mask(st["key"], g)
    tampil = km if len(km) <= W - 16 else g["ell"] + km[-(W - 17):]
    L.append(field("key", "API Key", tampil))
    L.append("")
    if st["busy"]:
        L.append(f"{DIM}{g['ell']} menghubungi server{RST}")
    elif st["status"]:
        L.append(st["status"].replace("✓", g["ok"]).replace("✗", g["bad"]))
    L.append("")
    L.append(f"{DIM}{' · '.join(['Tab pindah', 'Enter simpan', 'Del hapus', 'Esc lewati'])}{RST}")
    atas = max(0, (rows - len(L)) // 2)
    kiri = max(0, (cols - max(_vlen(x) for x in L)) // 2)
    baris_keluar = []
    for y in range(rows):
        isi = L[y - atas] if 0 <= y - atas < len(L) else ""
        tubuh = (" " * kiri + isi) if isi else ""
        baris_keluar.append(tubuh + " " * max(0, cols - _vlen(tubuh)))
    return "\x1b[H" + "\r\n".join(baris_keluar)


def _chunks_unix(inp, fd: int):
    """Yield potongan teks dari stdin (raw mode bila TTY)."""
    while True:
        try:
            data = os.read(fd, 64)
        except OSError:
            return
        if not data:
            return
        yield data.decode("utf-8", "replace")


def _chunks_windows():
    """Yield potongan teks dari msvcrt (khusus Windows)."""
    import msvcrt
    while True:
        b = msvcrt.getch()
        if b in (b"\x00", b"\xe0"):
            kode = msvcrt.getch()
            peta = {b"H": "\x1b[A", b"P": "\x1b[B", b"K": "\x1b[D",
                    b"M": "\x1b[C", b"S": "\x1b[3~"}
            yield peta.get(kode, "")
            continue
        if b == b"\x0f":
            yield "\x1b[Z"
            continue
        teks = b.decode("utf-8", "replace")
        # Burst (paste) di cmd: kumpulkan yang sudah menunggu.
        while msvcrt.kbhit():
            b2 = msvcrt.getch()
            if b2 in (b"\x00", b"\xe0"):
                msvcrt.ungetch(b2[0])
                break
            teks += b2.decode("utf-8", "replace")
        yield teks


def _chunks_biasa(inp):
    while True:
        data = inp.read(64)
        if not data:
            return
        yield data if isinstance(data, str) else data.decode("utf-8", "replace")


def _ukuran(out) -> tuple[int, int]:
    try:
        cols = getattr(out, "columns", None) or shutil.get_terminal_size().columns
        rows = getattr(out, "rows", None) or shutil.get_terminal_size().lines
        return cols, rows
    except OSError:
        return 80, 24


def jalankan_layar(verifikasi=None, input=None, output=None, glyphs=None) -> int:
    """Jalankan layar provider. Kembalikan jumlah provider saat keluar (0/1)."""
    from .llm import daftar_model
    from .setup import hapus_pengaturan, muat_pengaturan, simpan_pengaturan

    verifikasi = verifikasi or daftar_model
    inp = input if input is not None else sys.stdin
    out = output if output is not None else sys.stdout
    g = glyphs or pick_glyphs()
    tersimpan = muat_pengaturan() or None
    if tersimpan and not tersimpan.get("api_key"):
        tersimpan = None
    st = init_state(tersimpan)
    tty = hasattr(inp, "isatty") and inp.isatty()
    out.write("\x1b[?1049h\x1b[?25l\x1b[?2004h\x1b[2J")
    out.flush()
    fd = None
    raw_lama = None
    try:
        if tty and os.name != "nt":
            import termios
            import tty as ttymod
            fd = inp.fileno()
            raw_lama = termios.tcgetattr(fd)
            ttymod.setraw(fd)
        cols, rows = _ukuran(out)
        out.write(render(st, cols, rows, g))
        out.flush()
        ps = {"paste": None}
        if tty and os.name == "nt":
            chunks = _chunks_windows()
        elif tty:
            chunks = _chunks_unix(inp, fd)
        else:
            chunks = _chunks_biasa(inp)
        for chunk in chunks:
            for k in parse_keys(chunk, ps):
                aksi = reduce(st, k)
                if aksi and aksi.get("keluar"):
                    cols, rows = _ukuran(out)
                    out.write(render(st, cols, rows, g))
                    out.flush()
                    return 1 if st["tersimpan"] else 0
                if aksi and "hapus" in aksi:
                    ok = hapus_pengaturan()
                    st["tersimpan"] = None
                    st["status"] = "✓ dihapus" if ok else "✗ tidak ada"
                    st["focus"] = "form:nama"
                if aksi and aksi.get("simpan"):
                    st = _simpan(st, verifikasi, simpan_pengaturan)
            cols, rows = _ukuran(out)
            out.write(render(st, cols, rows, g))
            out.flush()
            if st["selesai"]:
                return 1 if st["tersimpan"] else 0
        return 1 if st["tersimpan"] else 0
    finally:
        if raw_lama is not None and fd is not None:
            import termios
            termios.tcsetattr(fd, termios.TCSADRAIN, raw_lama)
        out.write("\x1b[?2004l\x1b[?25h\x1b[0m\x1b[?1049l")
        out.flush()


def _simpan(st: dict, verifikasi, simpan_pengaturan) -> dict:
    """Validasi + tes koneksi + simpan. Kembalikan state baru."""
    nama = st["nama"].strip()
    base_url = st["base_url"].strip().rstrip("/")
    key = st["key"].strip()
    if not (nama and base_url and key):
        st["status"] = "✗ Nama, Base URL, dan API Key wajib diisi."
        return st
    st["busy"] = True
    try:
        model_list = verifikasi(base_url, key)
    except LLMError as e:
        pesan = str(e).replace(key, "•••")
        st["status"] = f"✗ {pesan}"
        st["busy"] = False
        return st
    except Exception as e:  # noqa: BLE001 - endpoint apa pun bisa gagal dengan cara apa pun
        st["status"] = f"✗ {e}"
        st["busy"] = False
        return st
    model = model_list[0] if model_list else DEFAULT_MODEL
    simpan_pengaturan(nama, base_url, model, key)
    jumlah = len(model_list)
    st["tersimpan"] = {"provider": nama, "model": model, "base_url": base_url}
    if jumlah:
        st["status"] = f"✓ Terhubung · {jumlah} model terdeteksi · model: {model}"
    else:
        st["status"] = f"✓ Terhubung · model: {model} (daftar model tidak tersedia)"
    st["nama"] = ""
    st["base_url"] = ""
    st["key"] = ""
    st["focus"] = "form:nama"
    st["busy"] = False
    return st
