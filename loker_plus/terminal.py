"""Terminal interaktif Kerjacoy: jalankan `kerjacoy` tanpa argumen.

Menu bernomor sederhana (input teks biasa) supaya jalan di Linux, macOS,
dan Windows tanpa dependensi TUI. Setiap pilihan memanggil kembali CLI
`kerjacoy` dengan argumen yang sama seperti mode perintah, jadi tidak ada
logika ganda.
"""

from __future__ import annotations

import re
from pathlib import Path

from .banner import tampilkan_banner
from .setup import jalankan_wizard, provider_dikonfigurasi, tampilkan_provider


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


def jalankan_terminal(jalankan=None) -> int:
    """Loop menu interaktif. `jalankan` adalah fungsi main CLI (bisa di-mock di tes)."""
    if jalankan is None:
        from .cli import main as jalankan

    tampilkan_banner()
    if not provider_dikonfigurasi():
        jawab = input("Belum ada provider LLM. Setup sekarang? [Y/n]: ").strip().lower()
        if jawab in ("", "y", "ya"):
            try:
                jalankan_wizard()
            except (EOFError, KeyboardInterrupt):
                print("\nSetup dibatalkan.")
    while True:
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
            return 0
        if pilih == "0":
            print("Sampai jumpa!")
            return 0
        elif pilih == "1":
            keyword = _tanya("Kata kunci lowongan")
            if not keyword:
                print("Kata kunci wajib diisi.")
                continue
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
                continue
            if sub == "1":
                try:
                    jalankan_wizard()
                except (EOFError, KeyboardInterrupt):
                    print("\nSetup dibatalkan.")
            elif sub == "2":
                tampilkan_provider()
        elif pilih == "7":
            jalankan(["cek-llm"])
        else:
            print("Pilihan tidak dikenal. Pilih 0-7.")
    return 0
