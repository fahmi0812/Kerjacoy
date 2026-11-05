"""Pembersihan & dedup hasil scrape."""

from __future__ import annotations

import re

import pandas as pd

KOLOM = ["site", "title", "company", "location", "job_url", "description", "date_posted"]


def _norm(teks) -> str:
    if teks is None:
        return ""
    return re.sub(r"\s+", " ", str(teks)).strip().lower()


def bersihkan(df: pd.DataFrame) -> pd.DataFrame:
    """Pilih kolom yang ada, buang baris tanpa URL/judul, dedup.

    Dedup dua tahap: (1) job_url sama, (2) pasangan (judul, perusahaan) sama.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=KOLOM + ["status"])
    for kolom in KOLOM:
        if kolom not in df.columns:
            df[kolom] = ""
    df = df[KOLOM].copy()
    df["job_url"] = df["job_url"].astype(str).str.strip()
    df["title"] = df["title"].astype(str).str.strip()
    df = df[(df["job_url"] != "") & (df["job_url"] != "nan") & (df["title"] != "")]
    df = df.drop_duplicates(subset=["job_url"], keep="first")
    kunci = (df["title"].map(_norm) + " @ " + df["company"].astype(str).map(_norm))
    df = df[~kunci.duplicated(keep="first")]
    df["status"] = "baru"
    return df.reset_index(drop=True)


def gabung_dedup(df_lama: pd.DataFrame, df_baru: pd.DataFrame) -> pd.DataFrame:
    """Gabung dua DataFrame lalu dedup, status lama dipertahankan."""
    if df_lama is None or len(df_lama) == 0:
        return bersihkan(df_baru)
    gabung = pd.concat([df_lama, bersihkan(df_baru)], ignore_index=True)
    gabung = gabung.drop_duplicates(subset=["job_url"], keep="first")
    return gabung.reset_index(drop=True)
