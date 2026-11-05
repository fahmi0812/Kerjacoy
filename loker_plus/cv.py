"""Penyesuaian bahan lamaran berbasis template — tanpa LLM, tanpa karangan.

Prinsip kejujuran: semua kalimat hanya memakai data dari profil pengguna
sendiri. Pengalaman yang ditampilkan dipilih berdasarkan relevansi dengan
lowongan, bukan dibuat-buat.
"""

from __future__ import annotations

from .skor import _norm, _mengandung


def tailor(lowongan: dict, profil: dict) -> dict:
    judul = _norm(lowongan.get("title"))
    desk = _norm(lowongan.get("description"))
    gabung = f"{judul} {desk}"

    keahlian = profil.get("keahlian") or []
    cocok = [k for k in keahlian if _mengandung(gabung, k)]

    # Pengalaman relevan: yang teksnya menyebut keahlian yang cocok / judul.
    pengalaman = profil.get("pengalaman") or []
    relevan = []
    for p in pengalaman:
        teks = _norm(p)
        if any(_mengandung(teks, k) for k in cocok) or any(
            _mengandung(teks, j) for j in (profil.get("jabatan_diinginkan") or [])
        ):
            relevan.append(p)
    if not relevan:
        relevan = pengalaman[:3]

    nama = profil.get("nama") or "[Nama Kamu]"
    perusahaan = lowongan.get("company") or "perusahaan tersebut"
    jabatan = lowongan.get("title") or "posisi tersebut"
    daftar_skill = ", ".join(cocok) if cocok else "keahlian yang saya miliki"

    pembuka = (
        f"Yth. Tim Rekrutmen {perusahaan},\n\n"
        f"Saya {nama} tertarik melamar posisi {jabatan}. "
        f"Berdasarkan deskripsi lowongan, posisi ini membutuhkan {daftar_skill}, "
        f"yang sejalan dengan pengalaman saya. "
    )
    if profil.get("ringkasan"):
        pembuka += profil["ringkasan"].strip() + " "

    checklist = [
        "Sesuaikan CV: tonjolkan keahlian berikut: " + (", ".join(cocok) if cocok else "-"),
        "Siapkan dokumen: CV terbaru, KTP, ijazah/transkrip bila diminta.",
        "Cek ulang link lamaran sebelum kirim; waspada bila diminta bayaran.",
    ]
    return {
        "keahlian_cocok": cocok,
        "pengalaman_relevan": relevan,
        "draf_cover_letter": pembuka,
        "checklist": checklist,
    }
