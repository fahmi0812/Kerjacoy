"""Wrapper scraping (JobSpy) + preset situs."""

from __future__ import annotations

import pandas as pd

PRESET = {
    # Terverifikasi langsung 5 Nov 2026: mengembalikan lowongan Indonesia asli.
    "indonesia": (["indeed", "linkedin"], "Indonesia"),
    "global": (["indeed", "linkedin", "zip_recruiter", "glassdoor"], None),
    # Cakupan terluas: semua board yang didukung JobSpy. Sebagian situs bisa
    # gagal (403/timeout), tapi hasil parsial dari situs lain tetap dipakai.
    # Google Jobs sering memunculkan agregat (termasuk JobStreet/Glints).
    "luas": (["indeed", "linkedin", "google", "glassdoor", "zip_recruiter",
              "bayt", "naukri"], None),
}


def cari_lowongan(keyword: str, lokasi: str, situs: list[str], jumlah: int,
                  jam: int, negara_indeed: str | None = None) -> pd.DataFrame:
    """Scrape lowongan. Mengembalikan DataFrame (bisa kosong bila diblokir).

    JobSpy mencatat error per-situs di log tapi tetap mengembalikan hasil
    dari situs yang berhasil — jadi hasil parsial tetap berguna.
    """
    from jobspy import scrape_jobs

    kwargs: dict = {
        "site_name": situs,
        "search_term": keyword,
        "location": lokasi,
        "results_wanted": jumlah,
        "hours_old": jam,
    }
    if "indeed" in situs and negara_indeed:
        kwargs["country_indeed"] = negara_indeed
    return scrape_jobs(**kwargs)
