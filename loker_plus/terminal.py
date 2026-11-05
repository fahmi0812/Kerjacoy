"""Terminal Kerjacoy: halaman depan + menu interaktif.

Halaman depan (ala layar awal 0DayExploit): logo besar di tengah, baris
status provider, lalu kotak cari — ketik kata kunci langsung cari, ketik
angka buka menu. Semua input teks biasa supaya jalan di Linux, macOS, dan
Windows tanpa dependensi TUI.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from .banner import BANNER
from .llm import DEFAULT_BASE_URL, DEFAULT_MODEL, ENV_API_KEY, ENV_BASE_URL, ENV_MODEL, ambil_env
from .provider_screen import jalankan_layar
from .setup import muat_pengaturan, provider_dikonfigurasi, tampilkan_provider

VERSI = "2.0.0"

HINTS = "1 cari · 2 laporan · 3 nilai · 4 tailor · 5 lacak · 6 provider · 7 cek LLM · 0 keluar"


def _slug(teks: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", teks.lower()).strip("-") or "hasil"


def _tanya(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    jawab = input(f"{prompt}{suffix}: ").strip()
    return jawab or default


def _csv_terbaru() -> str:
    try:
        files = sorted(Path("hasil").glob("*.csv"), key=lambda p: p.stat().st_mtime)
        return str(files[-1]) if files else ""
    except OSError:
        return ""


def _tampilkan_laporan(masukan: str) -> None:
    md_path = masukan.rsplit(".", 1)[0] + ".md"
    try:
        teks = Path(md_path).read_text(encoding="utf-8")
    except OSError:
        return
    print()
    print("\n".join(teks.splitlines()[:40]))


def _bersihkan_layar() -> None:
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except OSError:
        pass


def _status_provider() -> str:
    """Satu baris status provider untuk halaman depan."""
    if ambil_env(ENV_API_KEY):
        model = ambil_env(ENV_MODEL) or DEFAULT_MODEL
        base = ambil_env(ENV_BASE_URL) or DEFAULT_BASE_URL
        return f"Provider: env · {model} · {base}"
    pengaturan = muat_pengaturan()
    if pengaturan.get("api_key"):
        return (f"Provider: {pengaturan.get('provider', '-')} · "
                f"{pengaturan.get('model', '-')} · {pengaturan.get('base_url', '-')}")
    return "Provider: (belum ada) — pilih 6 untuk setup"


def tampilkan_halaman_depan() -> None:
    """Logo besar di tengah + status provider + petunjuk. Tanpa kotak/border."""
    _bersihkan_layar()
    lebar = shutil.get_terminal_size(fallback=(80, 24)).columns
    for baris in BANNER.strip("\n").splitlines():
        print(baris.center(lebar))
    print(_status_provider().center(lebar))
    print()
    print(f"Kerjacoy v{VERSI}".center(lebar))
    print()
    print(HINTS.center(lebar))
    print()


def jalankan_terminal(jalankan=None) -> int:
    """Loop halaman depan + menu. `jalankan` adalah fungsi main CLI (bisa di-mock di tes)."""
    if jalankan is None:
        from .cli import main as jalankan

    tampilkan_halaman_depan()
    if not provider_dikonfigurasi():
        jawab = input("Belum ada provider LLM. Buka layar provider sekarang? [Y/n]: ").strip().lower()
        if jawab in ("", "y", "ya"):
            try:
                jalankan_layar()
            except (EOFError, KeyboardInterrupt):
                print("\nSetup dibatalkan.")
            tampilkan_halaman_depan()
    while True:
        try:
            awal = input("Cari lowongan (kata kunci, angka = menu, Enter = menu): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa!")
            return 0
        if awal == "":
            pilih = _tanya_menu()
            if pilih is None:
                return 0
        elif awal in "01234567" and len(awal) == 1:
            pilih = awal
        else:
            # Kata kunci langsung dicari dengan default yang masuk akal.
            jalankan(["cari", "--keyword", awal, "--lokasi", "Indonesia",
                      "--preset", "indonesia", "--profil", "profil/contoh-umum.yaml",
                      "--keluaran", f"hasil/{_slug(awal)}.csv"])
            continue
        if pilih == "0":
            print("Sampai jumpa!")
            return 0
        _jalankan_menu(pilih, jalankan)
    return 0


def _tanya_menu() -> str | None:
    print("\n== Terminal Kerjacoy ==")
    print("  1. Cari lowongan")
    print("  2. Lihat laporan hasil pencarian")
    print("  3. Nilai ulang CSV")
    print("  4. Siapkan bahan lamaran (tailor)")
    print("  5. Lacak status lamaran")
    print("  6. Setup / lihat provider LLM")
    print("  7. Cek koneksi LLM")
    print("  0. Keluar")
    try:
        pilih = input("Pilih [0-7]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSampai jumpa!")
        return None
    if pilih not in "01234567" or len(pilih) != 1:
        print("Pilihan tidak dikenal. Pilih 0-7.")
        return _tanya_menu()
    return pilih


def _jalankan_menu(pilih: str, jalankan) -> None:
    if pilih == "1":
        keyword = _tanya("Kata kunci lowongan")
        if not keyword:
            print("Kata kunci wajib diisi.")
            return
        lokasi = _tanya("Lokasi", "Indonesia")
        preset = _tanya("Preset (indonesia/global/luas)", "indonesia")
        profil = _tanya("Profil", "profil/contoh-umum.yaml")
        keluaran = _tanya("Simpan ke", f"hasil/{_slug(keyword)}.csv")
        jalankan(["cari", "--keyword", keyword, "--lokasi", lokasi,
                  "--preset", preset, "--profil", profil,
                  "--keluaran", keluaran])
    elif pilih == "2":
        masukan = _tanya("File CSV hasil", _csv_terbaru())
        if masukan:
            jalankan(["laporan", "--masukan", masukan])
            _tampilkan_laporan(masukan)
    elif pilih == "3":
        masukan = _tanya("File CSV hasil")
        if masukan:
            jalankan(["nilai", "--masukan", masukan,
                      "--profil", _tanya("Profil", "profil/contoh-umum.yaml")])
    elif pilih == "4":
        masukan = _tanya("File CSV hasil")
        url = _tanya("URL lowongan")
        if masukan and url:
            jalankan(["tailor", "--masukan", masukan, "--url", url,
                      "--profil", _tanya("Profil", "profil/contoh-umum.yaml")])
    elif pilih == "5":
        masukan = _tanya("File CSV hasil")
        url = _tanya("URL lowongan")
        status = _tanya("Status (baru/dilihat/dilamar/wawancara/ditolak/diterima)", "dilamar")
        if masukan and url:
            jalankan(["tandai", "--masukan", masukan, "--url", url, "--status", status])
    elif pilih == "6":
        print("  1. Setup provider (wizard)")
        print("  2. Lihat provider aktif")
        print("  0. Kembali")
        try:
            sub = input("Pilih [0-2]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if sub == "1":
            try:
                jalankan_layar()
            except (EOFError, KeyboardInterrupt):
                print("\nSetup dibatalkan.")
        elif sub == "2":
            tampilkan_provider()
    elif pilih == "7":
        jalankan(["cek-llm"])
