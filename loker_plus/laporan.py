"""Laporan Markdown dari CSV hasil."""

from __future__ import annotations

import pandas as pd


def buat_laporan(df: pd.DataFrame, top: int = 20) -> str:
    """Buat laporan MD: ringkasan + tabel N teratas berdasarkan skor."""
    if df is None or len(df) == 0:
        return "# Laporan Lowongan\n\nBelum ada lowongan.\n"
    df = df.copy()
    if "skor" in df.columns:
        df = df.sort_values("skor", ascending=False)
    total = len(df)
    per_situs = df["site"].value_counts().to_dict() if "site" in df.columns else {}
    per_status = df["status"].value_counts().to_dict() if "status" in df.columns else {}

    baris = ["# Laporan Lowongan\n", f"Total: **{total}** lowongan.\n"]
    if per_situs:
        baris.append("Per situs: " + ", ".join(f"{k} ({v})" for k, v in per_situs.items()) + "\n")
    if per_status:
        baris.append("Per status: " + ", ".join(f"{k} ({v})" for k, v in per_status.items()) + "\n")
    baris.append(f"\n## {min(top, total)} Teratas (berdasarkan skor)\n")
    baris.append("| # | Skor | Jabatan | Perusahaan | Lokasi | Link | Alasan |")
    baris.append("|---|------|---------|------------|--------|------|--------|")
    for i, (_, r) in enumerate(df.head(top).iterrows(), start=1):
        skor = r.get("skor", "")
        alasan = str(r.get("alasan_skor", ""))[:120]
        baris.append(
            f"| {i} | {skor} | {r.get('title', '')} | {r.get('company', '')} "
            f"| {r.get('location', '')} | [Lamar]({r.get('job_url', '')}) | {alasan} |"
        )
    return "\n".join(baris) + "\n"
