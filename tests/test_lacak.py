"""Tes unit pelacakan status & entri manual (tanpa internet)."""

import pandas as pd
import pytest

from loker_plus.lacak import tambah_manual, tandai_status


def _csv_awal(tmp_path):
    p = tmp_path / "hasil.csv"
    pd.DataFrame([
        {"site": "indeed", "title": "Staff Admin", "company": "PT A", "location": "Jakarta",
         "job_url": "https://x/1", "description": "", "date_posted": "", "status": "baru"},
    ]).to_csv(p, index=False)
    return str(p)


def test_tandai_status_berhasil(tmp_path):
    path = _csv_awal(tmp_path)
    assert tandai_status(path, "https://x/1", "dilamar") == 1
    df = pd.read_csv(path)
    assert df.iloc[0]["status"] == "dilamar"


def test_tandai_url_tidak_ada_error(tmp_path):
    path = _csv_awal(tmp_path)
    with pytest.raises(ValueError):
        tandai_status(path, "https://x/tidak-ada", "dilamar")


def test_tandai_status_tidak_valid_error(tmp_path):
    path = _csv_awal(tmp_path)
    with pytest.raises(ValueError):
        tandai_status(path, "https://x/1", "sudah-kirim")


def test_tambah_manual_dan_tolak_duplikat(tmp_path):
    path = _csv_awal(tmp_path)
    baris = {"site": "manual", "title": "Kasir", "company": "PT D", "location": "Jakarta",
             "job_url": "https://glints/contoh", "description": "", "date_posted": ""}
    assert tambah_manual(path, baris) is True
    assert tambah_manual(path, baris) is False  # duplikat ditolak
    df = pd.read_csv(path)
    assert len(df) == 2
    assert df.iloc[1]["status"] == "baru"
