"""Tes setup pertama kali (wizard + file konfigurasi)."""

from __future__ import annotations

import os
import stat

import pytest

from loker_plus import setup as setup_mod
from loker_plus.llm import muat_konfigurasi


@pytest.fixture
def home_sementara(tmp_path, monkeypatch):
    """Arahkan KERJACOY_HOME ke direktori sementara + bersihkan env LLM."""
    monkeypatch.setenv("KERJACOY_HOME", str(tmp_path / ".kerjacoy"))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    for var in ("KERJACOY_LLM_BASE_URL", "KERJACOY_LLM_API_KEY", "KERJACOY_LLM_MODEL"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


def test_config_dir_di_home_sendiri(home_sementara):
    assert str(setup_mod.config_dir()).endswith(".kerjacoy/config")


def test_migrasi_dari_lokasi_lama(tmp_path, monkeypatch):
    """Config lama (XDG) ditemukan dan disalin ke home baru."""
    lama = tmp_path / "lama"
    baru = tmp_path / "baru"
    monkeypatch.setenv("KERJACOY_HOME", str(baru))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(lama))
    (lama / "kerjacoy").mkdir(parents=True)
    (lama / "kerjacoy" / "config.json").write_text(
        '{"provider": "lama", "base_url": "http://127.0.0.1:9/v1", "model": "model-lama"}')
    (lama / "kerjacoy" / "credentials.json").write_text('{"api_key": "kunci-lama"}')
    pengaturan = setup_mod.muat_pengaturan()
    assert pengaturan["provider"] == "lama"
    assert pengaturan["api_key"] == "kunci-lama"
    assert (baru / "config" / "config.json").exists()
    assert (baru / "config" / "credentials.json").exists()


def test_hapus_pengaturan(home_sementara):
    setup_mod.simpan_pengaturan("tes", "http://x/v1", "m", "kunci-tes")
    assert setup_mod.hapus_pengaturan() is True
    assert setup_mod.muat_pengaturan() == {}
    assert setup_mod.hapus_pengaturan() is False


def test_simpan_dan_muat(home_sementara):
    setup_mod.simpan_pengaturan("tes", "http://127.0.0.1:9/v1", "model-tes", "kunci-tes")
    pengaturan = setup_mod.muat_pengaturan()
    assert pengaturan["provider"] == "tes"
    assert pengaturan["base_url"] == "http://127.0.0.1:9/v1"
    assert pengaturan["model"] == "model-tes"
    assert pengaturan["api_key"] == "kunci-tes"


def test_credentials_hanya_bisa_dibaca_pemilik(home_sementara):
    setup_mod.simpan_pengaturan("tes", "http://x/v1", "m", "kunci-tes")
    mode = stat.S_IMODE(os.stat(setup_mod.config_dir() / "credentials.json").st_mode)
    assert mode == 0o600


def test_muat_konfigurasi_dari_file(home_sementara):
    setup_mod.simpan_pengaturan("tes", "http://127.0.0.1:9/v1", "model-tes", "kunci-tes")
    cfg = muat_konfigurasi()
    assert cfg.base_url == "http://127.0.0.1:9/v1"
    assert cfg.api_key == "kunci-tes"
    assert cfg.model == "model-tes"


def test_env_menang_atas_file(home_sementara, monkeypatch):
    setup_mod.simpan_pengaturan("tes", "http://127.0.0.1:9/v1", "model-tes", "kunci-file")
    monkeypatch.setenv("KERJACOY_LLM_API_KEY", "kunci-env")
    monkeypatch.setenv("KERJACOY_LLM_MODEL", "model-env")
    cfg = muat_konfigurasi()
    assert cfg.api_key == "kunci-env"
    assert cfg.model == "model-env"


def test_nama_env_lama_masih_dibaca(home_sementara, monkeypatch):
    """Kompatibilitas: nama CARILOKER_LLM_* (v0.2.0-0.4.0) tetap jalan."""
    monkeypatch.setenv("CARILOKER_LLM_API_KEY", "kunci-lama")
    monkeypatch.setenv("CARILOKER_LLM_MODEL", "model-lama")
    monkeypatch.setenv("CARILOKER_LLM_BASE_URL", "http://127.0.0.1:9/v1")
    cfg = muat_konfigurasi()
    assert cfg.api_key == "kunci-lama"
    assert cfg.model == "model-lama"
    assert setup_mod.provider_dikonfigurasi()


def test_provider_belum_dikonfigurasi(home_sementara):
    assert not setup_mod.provider_dikonfigurasi()


def test_wizard_menyimpan_jawaban(home_sementara, monkeypatch):
    jawaban = iter(["", "http://127.0.0.1:9/v1", "model-wizard"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(jawaban))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "kunci-wizard")
    hasil = setup_mod.jalankan_wizard()
    assert hasil["provider"] == "kerjacoy-llm"
    assert hasil["base_url"] == "http://127.0.0.1:9/v1"
    assert hasil["model"] == "model-wizard"
    assert hasil["api_key"] == "kunci-wizard"
    assert setup_mod.provider_dikonfigurasi()


def test_provider_tampil_key_disamarkan(home_sementara, capsys):
    setup_mod.simpan_pengaturan("tes", "http://127.0.0.1:9/v1", "model-tes", "kunci-rahasia")
    setup_mod.tampilkan_provider()
    keluar = capsys.readouterr().out
    assert "kunci-rahasia" not in keluar
    assert "•" in keluar
    assert "http://127.0.0.1:9/v1" in keluar
