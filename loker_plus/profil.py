"""Muat profil pelamar dari YAML/JSON."""

from __future__ import annotations

import json
import os

DEFAULT = {
    "nama": "",
    "ringkasan": "",
    "keahlian": [],
    "jabatan_diinginkan": [],
    "lokasi_diinginkan": [],
    "kata_hindari": [],
    "pengalaman": [],
}


def muat_profil(path: str) -> dict:
    """Baca profil YAML/JSON, gabung dengan default, validasi tipe list."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Profil tidak ditemukan: {path}")
    with open(path, encoding="utf-8") as f:
        if path.endswith(".json"):
            data = json.load(f)
        else:
            import yaml

            data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Profil harus berupa mapping (dict) di tingkat atas")
    profil = dict(DEFAULT)
    profil.update(data)
    for kunci in ("keahlian", "jabatan_diinginkan", "lokasi_diinginkan",
                  "kata_hindari", "pengalaman"):
        if not isinstance(profil[kunci], list):
            raise ValueError(f"Profil: '{kunci}' harus berupa list")
    return profil
