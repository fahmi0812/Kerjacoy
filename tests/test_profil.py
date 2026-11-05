"""Tes unit muat profil."""

import pytest

from loker_plus.profil import muat_profil


def test_muat_yaml_contoh(tmp_path):
    p = tmp_path / "profil.yaml"
    p.write_text(
        "nama: Budi\nkeahlian:\n  - excel\njabatan_diinginkan:\n  - staff admin\n",
        encoding="utf-8",
    )
    profil = muat_profil(str(p))
    assert profil["nama"] == "Budi"
    assert profil["keahlian"] == ["excel"]
    assert profil["lokasi_diinginkan"] == []  # default terisi
    assert profil["pengalaman"] == []


def test_file_tidak_ada_error():
    with pytest.raises(FileNotFoundError):
        muat_profil("/tmp/tidak-ada-profil.yaml")


def test_list_bukan_list_error(tmp_path):
    p = tmp_path / "profil.yaml"
    p.write_text("keahlian: excel\n", encoding="utf-8")
    with pytest.raises(ValueError):
        muat_profil(str(p))
