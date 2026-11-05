"""Tes `kerjacoy connect` dan preset cakupan luas."""

from __future__ import annotations

import argparse
import os

import pytest

from loker_plus import cli as cli_mod
from loker_plus.scrape import PRESET


def _args(**kwargs):
    dasar = {"type": "openai", "name": None, "base_url": None, "model": None,
             "key": None, "key_env": None, "list": False}
    dasar.update(kwargs)
    return argparse.Namespace(**dasar)


@pytest.fixture
def home_sementara(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    for var in ("KERJACOY_LLM_BASE_URL", "KERJACOY_LLM_API_KEY", "KERJACOY_LLM_MODEL",
                "CARIKERJA_LLM_BASE_URL", "CARIKERJA_LLM_API_KEY", "CARIKERJA_LLM_MODEL",
                "CARILOKER_LLM_BASE_URL", "CARILOKER_LLM_API_KEY", "CARILOKER_LLM_MODEL"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


def test_connect_key_env_menyimpan_dan_tes_koneksi(home_sementara, monkeypatch):
    monkeypatch.setenv("KUNCI_STUB", "kunci-connect")
    monkeypatch.setattr(cli_mod, "cmd_cek_llm", lambda args: 0)
    kode = cli_mod.cmd_connect(_args(
        name="stub", base_url="http://127.0.0.1:9/v1",
        model="model-stub", key_env="KUNCI_STUB"))
    assert kode == 0
    from loker_plus.setup import muat_pengaturan
    pengaturan = muat_pengaturan()
    assert pengaturan["provider"] == "stub"
    assert pengaturan["base_url"] == "http://127.0.0.1:9/v1"
    assert pengaturan["api_key"] == "kunci-connect"


def test_connect_key_env_kosong_gagal(home_sementara, monkeypatch):
    monkeypatch.delenv("KUNCI_KOSONG", raising=False)
    kode = cli_mod.cmd_connect(_args(key_env="KUNCI_KOSONG"))
    assert kode == 1


def test_connect_tipe_anthropic_ditolak(home_sementara):
    kode = cli_mod.cmd_connect(_args(type="anthropic"))
    assert kode == 1


def test_connect_list_menampilkan_provider(home_sementara, monkeypatch, capsys):
    from loker_plus.setup import simpan_pengaturan
    simpan_pengaturan("stub", "http://127.0.0.1:9/v1", "model-stub", "kunci-x")
    kode = cli_mod.cmd_connect(_args(list=True))
    assert kode == 0
    keluar = capsys.readouterr().out
    assert "kunci-x" not in keluar
    assert "•" in keluar


def test_preset_luas_memuat_semua_board_relevan():
    situs, _ = PRESET["luas"]
    assert {"indeed", "linkedin", "google", "glassdoor", "zip_recruiter",
            "bayt", "naukri"} <= set(situs)


def test_preset_indonesia_tidak_berubah():
    situs, negara = PRESET["indonesia"]
    assert situs == ["indeed", "linkedin"]
    assert negara == "Indonesia"


def test_update_tanpa_installer(tmp_path, monkeypatch):
    monkeypatch.setenv("KERJACOY_HOME", str(tmp_path))
    args = argparse.Namespace()
    kode = cli_mod.cmd_update(args)
    assert kode == 1


def test_direktori_instal_terdeteksi(tmp_path, monkeypatch):
    (tmp_path / "src" / ".git").mkdir(parents=True)
    monkeypatch.setenv("KERJACOY_HOME", str(tmp_path))
    assert cli_mod._direktori_instal() == tmp_path / "src"


def test_config_dir_windows(monkeypatch):
    from loker_plus import setup as setup_mod
    monkeypatch.setattr(setup_mod, "_is_windows", lambda: True)
    monkeypatch.setenv("APPDATA", r"C:\Users\Tes\AppData\Roaming")
    hasil = str(setup_mod.config_dir())
    assert hasil.endswith("kerjacoy")
    assert "AppData" in hasil
