"""Pelacakan status lamaran di dalam CSV hasil."""

from __future__ import annotations

import pandas as pd

from .bersihkan import bersihkan

STATUS_VALID = {"baru", "dilihat", "dilamar", "wawancara", "ditolak", "diterima"}


def tandai_status(path_csv: str, url: str, status: str) -> int:
    """Ubah status baris ber-URL tersebut. Mengembalikan jumlah baris diubah."""
    if status not in STATUS_VALID:
        raise ValueError(f"Status tidak valid: {status}. Pilihan: {sorted(STATUS_VALID)}")
    df = pd.read_csv(path_csv)
    mask = df["job_url"].astype(str) == url
    if not mask.any():
        raise ValueError("URL tidak ditemukan di file CSV")
    df.loc[mask, "status"] = status
    df.to_csv(path_csv, index=False)
    return int(mask.sum())


def tambah_manual(path_csv: str, baris: dict) -> bool:
    """Tambah satu lowongan manual (mis. link JobStreet/Glints).

    Mengembalikan False bila URL sudah ada (tidak diduplikasi).
    """
    try:
        df_lama = pd.read_csv(path_csv)
    except FileNotFoundError:
        df_lama = pd.DataFrame()
    if len(df_lama) and (df_lama["job_url"].astype(str) == baris["job_url"]).any():
        return False
    from .bersihkan import gabung_dedup

    df_baru = pd.DataFrame([baris])
    gabung = gabung_dedup(df_lama, df_baru)
    gabung.to_csv(path_csv, index=False)
    return True
