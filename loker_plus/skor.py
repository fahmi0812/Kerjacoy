"""Penilaian kecocokan lowongan vs profil — transparan, tanpa LLM."""

from __future__ import annotations

import re
from datetime import datetime, timezone

_KATA_HINDARI_DEFAULT = ["bayar di muka", "deposit", "tanpa gaji", "investasi awal"]


def _norm(teks) -> str:
    """Normalisasi: huruf kecil, hanya huruf/angka/spasi."""
    if teks is None:
        return ""
    try:
        import math

        if isinstance(teks, float) and math.isnan(teks):
            return ""
    except Exception:
        pass
    return re.sub(r"[^a-z0-9 ]+", " ", str(teks).lower())


def _mengandung(teks_norm: str, frasa: str) -> bool:
    frasa_norm = _norm(frasa)
    return bool(frasa_norm) and frasa_norm in teks_norm


def _poin_kebaruan(tanggal_posting, jam_maks: int) -> tuple[int, str]:
    """Poin kebaruan: 15 (<=24 jam), 10 (<=72 jam), 5 (dalam jendela), 0 (lewat).

    Jika tanggal tidak tersedia, beri nilai netral 7 agar tidak menghukum
    lowongan yang datanya tidak lengkap.
    """
    if tanggal_posting is None or (isinstance(tanggal_posting, str) and not tanggal_posting.strip()):
        return 7, "tanggal posting tidak tersedia (netral)"
    try:
        if isinstance(tanggal_posting, str):
            dt = datetime.fromisoformat(tanggal_posting.replace("Z", "+00:00"))
        else:
            dt = tanggal_posting
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        selisih_jam = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return 7, "tanggal posting tidak bisa dibaca (netral)"
    if selisih_jam <= 24:
        return 15, "posting <= 24 jam"
    if selisih_jam <= 72:
        return 10, "posting <= 72 jam"
    if selisih_jam <= jam_maks:
        return 5, "posting dalam jendela pencarian"
    return 0, "posting sudah lama"


def skor_lowongan(lowongan: dict, profil: dict, jam_maks: int = 168) -> tuple[int, list[str]]:
    """Hitung skor 0-100 + alasan yang bisa dibaca manusia.

    lowongan: dict dengan kunci title, description, location, date_posted.
    profil: dict dengan keahlian, jabatan_diinginkan, lokasi_diinginkan,
    kata_hindari.
    """
    judul = _norm(lowongan.get("title"))
    desk = _norm(lowongan.get("description"))
    lokasi = _norm(lowongan.get("location"))
    gabung = f"{judul} {desk}"
    alasan: list[str] = []
    skor = 0

    jabatan = profil.get("jabatan_diinginkan") or []
    cocok_jabatan = [j for j in jabatan if _mengandung(judul, j)]
    if jabatan:
        skor += round(40 * len(cocok_jabatan) / len(jabatan))
        if cocok_jabatan:
            alasan.append(f"judul cocok: {', '.join(cocok_jabatan)}")

    keahlian = profil.get("keahlian") or []
    cocok_skill = [k for k in keahlian if _mengandung(gabung, k)]
    if keahlian:
        skor += round(30 * len(cocok_skill) / len(keahlian))
        if cocok_skill:
            alasan.append(f"keahlian cocok: {', '.join(cocok_skill)}")

    for lok in profil.get("lokasi_diinginkan") or []:
        if _mengandung(lokasi, lok):
            skor += 15
            alasan.append(f"lokasi cocok: {lok}")
            break

    poin_baru, alasan_baru = _poin_kebaruan(lowongan.get("date_posted"), jam_maks)
    skor += poin_baru
    alasan.append(alasan_baru)

    kata_hindari = list(profil.get("kata_hindari") or []) + _KATA_HINDARI_DEFAULT
    for kata in kata_hindari:
        if _mengandung(gabung, kata):
            skor -= 25
            alasan.append(f"mengandung kata hindari: {kata}")

    skor = max(0, min(100, skor))
    return skor, alasan
