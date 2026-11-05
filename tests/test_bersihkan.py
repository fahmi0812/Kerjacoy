"""Tes unit pembersihan & dedup (tanpa internet)."""

import pandas as pd

from loker_plus.bersihkan import bersihkan, gabung_dedup


def _df():
    return pd.DataFrame([
        {"site": "indeed", "title": "Staff Admin", "company": "PT A",
         "location": "Jakarta", "job_url": "https://x/1", "description": "", "date_posted": ""},
        {"site": "linkedin", "title": "Staff Admin", "company": "PT A",
         "location": "Jakarta", "job_url": "https://x/1", "description": "", "date_posted": ""},
        {"site": "linkedin", "title": "staff admin", "company": "pt a",
         "location": "Jakarta", "job_url": "https://x/2", "description": "", "date_posted": ""},
        {"site": "indeed", "title": "", "company": "PT B",
         "location": "Jakarta", "job_url": "https://x/3", "description": "", "date_posted": ""},
        {"site": "indeed", "title": "Sales", "company": "PT C",
         "location": "Jakarta", "job_url": "", "description": "", "date_posted": ""},
    ])


def test_dedup_url_dan_judul_perusahaan():
    bersih = bersihkan(_df())
    # URL sama (baris 1-2) jadi 1; judul+perusahaan sama (baris 3) ikut terbuang
    assert len(bersih) == 1
    assert bersih.iloc[0]["job_url"] == "https://x/1"


def test_baris_tanpa_judul_atau_url_dibuang():
    df = pd.DataFrame([
        {"site": "indeed", "title": "", "company": "PT B", "location": "Jakarta",
         "job_url": "https://x/3", "description": "", "date_posted": ""},
        {"site": "indeed", "title": "Sales", "company": "PT C", "location": "Jakarta",
         "job_url": "", "description": "", "date_posted": ""},
    ])
    assert len(bersihkan(df)) == 0


def test_status_default_baru():
    bersih = bersihkan(_df())
    assert (bersih["status"] == "baru").all()


def test_gabung_mempertahankan_status_lama():
    lama = bersihkan(_df())
    lama.loc[0, "status"] = "dilamar"
    baru = pd.DataFrame([
        {"site": "indeed", "title": "Staff Admin", "company": "PT A",
         "location": "Jakarta", "job_url": "https://x/1", "description": "", "date_posted": ""},
        {"site": "indeed", "title": "Kasir", "company": "PT D",
         "location": "Jakarta", "job_url": "https://x/9", "description": "", "date_posted": ""},
    ])
    gabung = gabung_dedup(lama, baru)
    assert len(gabung) == 2
    assert gabung[gabung["job_url"] == "https://x/1"].iloc[0]["status"] == "dilamar"
