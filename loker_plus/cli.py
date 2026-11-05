"""CLI Kerjacoy: cari, nilai, tambah, tandai, tailor, laporan."""

from __future__ import annotations

import argparse
import getpass
import os
import sys

import pandas as pd

from .banner import tampilkan_banner
from .bersihkan import bersihkan
from .cv import tailor
from .lacak import tambah_manual, tandai_status
from .laporan import buat_laporan
from .llm import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    LLMError,
    cek_koneksi,
    draf_cover_letter_llm,
    llm_tersedia,
    muat_konfigurasi,
    skor_llm,
)
from .profil import muat_profil
from .scrape import PRESET, cari_lowongan
from .setup import (
    jalankan_wizard,
    provider_dikonfigurasi,
    simpan_pengaturan,
    tampilkan_provider,
)
from .skor import skor_lowongan
from .terminal import jalankan_terminal


def _nilai_df(df: pd.DataFrame, profil: dict, jam: int, pakai_llm: bool = False) -> pd.DataFrame:
    skor_list, alasan_list = [], []
    for _, row in df.iterrows():
        s, a = skor_lowongan(row.to_dict(), profil, jam_maks=jam)
        skor_list.append(s)
        alasan_list.append("; ".join(a))
    df = df.copy()
    df["skor"] = skor_list
    df["alasan_skor"] = alasan_list
    if pakai_llm:
        cfg = muat_konfigurasi()
        if not llm_tersedia(cfg):
            print("LLM tidak dikonfigurasi (isi KERJACOY_LLM_API_KEY dulu); "
                  "lanjut dengan skor template saja.")
        else:
            skor_llm_list, alasan_llm_list = [], []
            for _, row in df.iterrows():
                try:
                    s, a = skor_llm(cfg, row.to_dict(), profil)
                    skor_llm_list.append(s)
                    alasan_llm_list.append("; ".join(a))
                except LLMError as e:
                    print(f"  LLM gagal untuk '{row.get('title')}': {e}")
                    skor_llm_list.append(None)
                    alasan_llm_list.append("")
            df["skor_llm"] = skor_llm_list
            df["alasan_llm"] = alasan_llm_list
    return df


def _simpan(df: pd.DataFrame, keluaran: str, top: int = 20) -> None:
    os.makedirs(os.path.dirname(keluaran) or ".", exist_ok=True)
    df.to_csv(keluaran, index=False)
    md_path = os.path.splitext(keluaran)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(buat_laporan(df, top=top))
    print(f"Tersimpan: {keluaran} ({len(df)} lowongan) dan {md_path}")


def cmd_cari(args) -> int:
    if args.preset:
        situs, negara = PRESET[args.preset]
        negara_indeed = negara if args.negara_indeed is None else args.negara_indeed
    else:
        situs = [s.strip() for s in args.situs.split(",") if s.strip()]
        negara_indeed = args.negara_indeed
    profil = muat_profil(args.profil) if args.profil else {}
    print(f"Mencari '{args.keyword}' di {situs} (lokasi: {args.lokasi}) ...")
    try:
        df = cari_lowongan(args.keyword, args.lokasi, situs, args.jumlah,
                           args.jam, negara_indeed)
    except Exception as e:  # noqa: BLE001 - tampilkan pesan jelas ke pengguna
        print(f"Gagal scraping: {e}", file=sys.stderr)
        return 1
    df = bersihkan(df)
    if len(df) == 0:
        print("Tidak ada lowongan ditemukan. Coba: ubah kata kunci, perbesar "
              "--jam, kurangi --jumlah, atau ganti situs.")
        return 0
    df = _nilai_df(df, profil, args.jam, pakai_llm=args.llm)
    df = df.sort_values("skor", ascending=False).reset_index(drop=True)
    _simpan(df, args.keluaran)
    print("\n5 teratas:")
    for _, r in df.head(5).iterrows():
        print(f"  [{r['skor']}] {r['title']} — {r['company']} ({r['location']})")
        print(f"       {r['job_url']}")
    return 0


def cmd_nilai(args) -> int:
    profil = muat_profil(args.profil)
    df = pd.read_csv(args.masukan)
    df = _nilai_df(df, profil, args.jam, pakai_llm=args.llm)
    df = df.sort_values("skor", ascending=False).reset_index(drop=True)
    _simpan(df, args.masukan)
    print(f"Dinilai ulang: {len(df)} lowongan.")
    return 0


def cmd_tambah(args) -> int:
    baris = {"site": args.situs or "manual", "title": args.judul,
             "company": args.perusahaan or "", "location": args.lokasi or "",
             "job_url": args.url, "description": args.deskripsi or "",
             "date_posted": ""}
    ok = tambah_manual(args.masukan, baris)
    print("Ditambahkan." if ok else "Sudah ada (URL duplikat, tidak ditambah).")
    return 0


def cmd_tandai(args) -> int:
    try:
        n = tandai_status(args.masukan, args.url, args.status)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Status diubah ({n} baris) menjadi '{args.status}'.")
    return 0


def cmd_tailor(args) -> int:
    profil = muat_profil(args.profil)
    df = pd.read_csv(args.masukan)
    mask = df["job_url"].astype(str) == args.url
    if not mask.any():
        print("Error: URL tidak ditemukan di file CSV", file=sys.stderr)
        return 1
    hasil = tailor(df[mask].iloc[0].to_dict(), profil)
    if args.llm:
        cfg = muat_konfigurasi()
        if not llm_tersedia(cfg):
            print("LLM tidak dikonfigurasi (isi KERJACOY_LLM_API_KEY dulu); "
                  "pakai draf template saja.")
        else:
            try:
                hasil["draf_cover_letter"] = draf_cover_letter_llm(
                    cfg, df[mask].iloc[0].to_dict(), profil, hasil)
            except LLMError as e:
                print(f"LLM gagal menulis draf ({e}); pakai draf template saja.")
    print(f"\nLowongan: {df[mask].iloc[0]['title']} — {df[mask].iloc[0]['company']}")
    print("Keahlian yang cocok:", ", ".join(hasil["keahlian_cocok"]) or "-")
    print("\nPengalaman relevan dari profil kamu:")
    for p in hasil["pengalaman_relevan"]:
        print(f"  - {p}")
    print("\nDraf pembuka cover letter:")
    print(hasil["draf_cover_letter"])
    print("\nChecklist sebelum kirim:")
    for c in hasil["checklist"]:
        print(f"  [ ] {c}")
    return 0


def cmd_laporan(args) -> int:
    df = pd.read_csv(args.masukan)
    md_path = os.path.splitext(args.masukan)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(buat_laporan(df, top=args.top))
    print(f"Laporan ditulis: {md_path}")
    return 0


def cmd_cek_llm(args) -> int:
    ok, pesan = cek_koneksi()
    print(pesan)
    return 0 if ok else 1


def cmd_setup(args) -> int:
    try:
        tampilkan_banner()
        jalankan_wizard()
    except (EOFError, KeyboardInterrupt):
        print("\nSetup dibatalkan. Jalankan lagi: kerjacoy setup", file=sys.stderr)
        return 1
    print("\nTes koneksi:")
    return cmd_cek_llm(args)


def cmd_provider(args) -> int:
    tampilkan_provider()
    return 0


def cmd_connect(args) -> int:
    """Tambah provider LLM (ala `0dayexploit connect`).

    Key tidak pernah ditulis ke argumen riwayat bila memungkinkan: pakai
    --key-env (nama environment variable berisi key) atau biarkan prompt
    bertanya dengan input tersembunyi.
    """
    if args.list:
        tampilkan_provider()
        return 0
    if (args.type or "openai") != "openai":
        print("Error: saat ini hanya --type openai (endpoint yang kompatibel "
              "dengan OpenAI) yang didukung.", file=sys.stderr)
        return 1
    nama = args.name or "kerjacoy-llm"
    base_url = (args.base_url or DEFAULT_BASE_URL).rstrip("/")
    model = args.model or DEFAULT_MODEL
    if args.key_env:
        api_key = os.environ.get(args.key_env, "")
        if not api_key:
            print(f"Error: environment variable {args.key_env} kosong.",
                  file=sys.stderr)
            return 1
    elif args.key:
        print("Peringatan: --key menulis key ke riwayat shell. Lebih aman pakai "
              "--key-env atau biarkan prompt bertanya.")
        api_key = args.key
    else:
        try:
            api_key = getpass.getpass("API key (diketik tersembunyi): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nDibatalkan.", file=sys.stderr)
            return 1
        if not api_key:
            print("Error: API key tidak boleh kosong.", file=sys.stderr)
            return 1
    direktori = simpan_pengaturan(nama, base_url, model, api_key)
    print(f"Provider '{nama}' tersimpan di {direktori}.")
    print("\nTes koneksi:")
    return cmd_cek_llm(args)


def build_parser() -> argparse.ArgumentParser:
    nama = os.path.basename(sys.argv[0]) if sys.argv else "kerjacoy"
    prog = nama if nama in ("kerjacoy", "carikerja", "loker") else "kerjacoy"
    p = argparse.ArgumentParser(prog=prog, description="Kerjacoy: cari kerja lintas bidang.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cari", help="Cari + skor + simpan lowongan")
    c.add_argument("--keyword", required=True)
    c.add_argument("--lokasi", default="Indonesia")
    c.add_argument("--preset", choices=list(PRESET))
    c.add_argument("--situs", default="indeed,linkedin")
    c.add_argument("--negara-indeed", default=None)
    c.add_argument("--jumlah", type=int, default=50)
    c.add_argument("--jam", type=int, default=168)
    c.add_argument("--profil")
    c.add_argument("--keluaran", required=True)
    c.add_argument("--llm", action="store_true",
                   help="Tambah penilaian LLM (butuh KERJACOY_LLM_API_KEY)")
    c.set_defaults(func=cmd_cari)

    n = sub.add_parser("nilai", help="Skor ulang CSV dengan profil")
    n.add_argument("--masukan", required=True)
    n.add_argument("--profil", required=True)
    n.add_argument("--jam", type=int, default=168)
    n.add_argument("--llm", action="store_true",
                   help="Tambah penilaian LLM (butuh KERJACOY_LLM_API_KEY)")
    n.set_defaults(func=cmd_nilai)

    t = sub.add_parser("tambah", help="Tambah lowongan manual (mis. JobStreet/Glints)")
    t.add_argument("--masukan", required=True)
    t.add_argument("--url", required=True)
    t.add_argument("--judul", required=True)
    t.add_argument("--perusahaan")
    t.add_argument("--lokasi")
    t.add_argument("--situs")
    t.add_argument("--deskripsi")
    t.set_defaults(func=cmd_tambah)

    d = sub.add_parser("tandai", help="Ubah status lamaran")
    d.add_argument("--masukan", required=True)
    d.add_argument("--url", required=True)
    d.add_argument("--status", required=True,
                   choices=["baru", "dilihat", "dilamar", "wawancara", "ditolak", "diterima"])
    d.set_defaults(func=cmd_tandai)

    v = sub.add_parser("tailor", help="Bahan lamaran untuk satu lowongan")
    v.add_argument("--masukan", required=True)
    v.add_argument("--url", required=True)
    v.add_argument("--profil", required=True)
    v.add_argument("--llm", action="store_true",
                   help="Tulis draf cover letter dengan LLM (butuh KERJACOY_LLM_API_KEY)")
    v.set_defaults(func=cmd_tailor)

    l = sub.add_parser("laporan", help="Buat ulang laporan MD dari CSV")
    l.add_argument("--masukan", required=True)
    l.add_argument("--top", type=int, default=20)
    l.set_defaults(func=cmd_laporan)

    k = sub.add_parser("cek-llm", help="Tes koneksi ke endpoint LLM yang dikonfigurasi")
    k.set_defaults(func=cmd_cek_llm)

    s = sub.add_parser("setup", help="Setup pertama kali: isi URL + API key + model LLM")
    s.set_defaults(func=cmd_setup)

    pr = sub.add_parser("provider", help="Lihat provider LLM yang aktif (key disamarkan)")
    pr.set_defaults(func=cmd_provider)

    cn = sub.add_parser("connect", help="Tambah provider LLM (URL + API key)")
    cn.add_argument("--type", default="openai", choices=["openai", "anthropic"],
                    help="Jenis endpoint (saat ini hanya openai yang didukung)")
    cn.add_argument("--name", default=None, help="Nama provider")
    cn.add_argument("--base-url", default=None, help="Base URL endpoint (berakhiran /v1)")
    cn.add_argument("--model", default=None, help="Model")
    cn.add_argument("--key", default=None, help="API key (masuk riwayat shell; tidak disarankan)")
    cn.add_argument("--key-env", default=None,
                    help="Nama environment variable berisi API key (disarankan)")
    cn.add_argument("--list", action="store_true", help="Lihat provider yang tersimpan")
    cn.set_defaults(func=cmd_connect)
    return p


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        # Tanpa argumen: buka Terminal Kerjacoy bila interaktif (ala
        # 0dayexploit yang langsung membuka layarnya); bila tidak interaktif
        # (pipe/skrip), tampilkan banner + bantuan saja supaya tidak menggantung.
        if sys.stdin.isatty():
            return jalankan_terminal()
        tampilkan_banner()
        print("Perintah: cari | nilai | tambah | tandai | tailor | laporan | "
              "cek-llm | setup | provider | connect")
        print("Contoh: kerjacoy cari --keyword \"staff admin\" --preset indonesia "
              "--profil profil/contoh-admin.yaml --keluaran hasil/staff-admin.csv")
        print("Bantuan lengkap: kerjacoy --help")
        return 0
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
