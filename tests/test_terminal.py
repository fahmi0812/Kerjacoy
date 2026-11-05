"""Tes Terminal interaktif Kerjacoy (menu bernomor)."""

from __future__ import annotations

import pytest

from loker_plus import terminal as terminal_mod


@pytest.fixture
def tanpa_provider(monkeypatch, tmp_path):
    monkeypatch.setenv("KERJACOY_HOME", str(tmp_path))
    monkeypatch.setattr(terminal_mod, "provider_dikonfigurasi", lambda: True)
    monkeypatch.setattr(terminal_mod, "jalankan_layar", lambda: None)


def _jalankan_palsu(panggilan):
    def jalankan(argv):
        panggilan.append(argv)
        return 0
    return jalankan


def _input_antrean(jawaban, monkeypatch):
    antrean = iter(jawaban)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(antrean))


def test_menu_keluar_langsung(tanpa_provider, monkeypatch):
    _input_antrean(["0"], monkeypatch)
    assert terminal_mod.jalankan_terminal(_jalankan_palsu([])) == 0


def test_menu_pilihan_tidak_dikenal_lalu_keluar(tanpa_provider, monkeypatch, capsys):
    _input_antrean(["", "9", "0"], monkeypatch)
    assert terminal_mod.jalankan_terminal(_jalankan_palsu([])) == 0
    assert "tidak dikenal" in capsys.readouterr().out


def test_halaman_depan_cari_langsung(tanpa_provider, monkeypatch):
    panggilan = []
    _input_antrean(["staff admin", "0"], monkeypatch)
    terminal_mod.jalankan_terminal(_jalankan_palsu(panggilan))
    assert panggilan == [[
        "cari", "--keyword", "staff admin", "--lokasi", "Indonesia",
        "--preset", "indonesia", "--profil", "profil/contoh-umum.yaml",
        "--keluaran", "hasil/staff-admin.csv",
    ]]


def test_halaman_depan_tampilkan_status_provider(tanpa_provider, monkeypatch, capsys):
    monkeypatch.setenv("KERJACOY_LLM_API_KEY", "kunci-x")
    monkeypatch.setenv("KERJACOY_LLM_MODEL", "model-x")
    _input_antrean(["0"], monkeypatch)
    terminal_mod.jalankan_terminal(_jalankan_palsu([]))
    assert "model-x" in capsys.readouterr().out


def test_halaman_depan_tanpa_provider(tanpa_provider, monkeypatch, capsys):
    for var in ("KERJACOY_LLM_API_KEY", "CARIKERJA_LLM_API_KEY", "CARILOKER_LLM_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    _input_antrean(["0"], monkeypatch)
    terminal_mod.jalankan_terminal(_jalankan_palsu([]))
    assert "belum ada" in capsys.readouterr().out


def test_menu_cari_membangun_argumen(tanpa_provider, monkeypatch):
    panggilan = []
    _input_antrean([
        "1", "staff admin", "Indonesia", "indonesia",
        "profil/contoh-admin.yaml", "hasil/staff-admin.csv", "0",
    ], monkeypatch)
    terminal_mod.jalankan_terminal(_jalankan_palsu(panggilan))
    assert panggilan == [[
        "cari", "--keyword", "staff admin", "--lokasi", "Indonesia",
        "--preset", "indonesia", "--profil", "profil/contoh-admin.yaml",
        "--keluaran", "hasil/staff-admin.csv",
    ]]


def test_menu_cek_llm(tanpa_provider, monkeypatch):
    panggilan = []
    _input_antrean(["7", "0"], monkeypatch)
    terminal_mod.jalankan_terminal(_jalankan_palsu(panggilan))
    assert panggilan == [["cek-llm"]]


def test_menu_laporan(tanpa_provider, monkeypatch):
    panggilan = []
    _input_antrean(["2", "/tmp/x.csv", "0"], monkeypatch)
    terminal_mod.jalankan_terminal(_jalankan_palsu(panggilan))
    assert panggilan == [["laporan", "--masukan", "/tmp/x.csv"]]


def test_menu_tanpa_provider_tolak_setup(monkeypatch):
    monkeypatch.setattr(terminal_mod, "provider_dikonfigurasi", lambda: False)
    _input_antrean(["n", "0"], monkeypatch)
    assert terminal_mod.jalankan_terminal(_jalankan_palsu([])) == 0


def test_menu_eof_keluar(tanpa_provider, monkeypatch):
    def habis(prompt=""):
        raise EOFError
    monkeypatch.setattr("builtins.input", habis)
    assert terminal_mod.jalankan_terminal(_jalankan_palsu([])) == 0


def test_slug():
    assert terminal_mod._slug("Staff Admin (Jakarta)") == "staff-admin-jakarta"
    assert terminal_mod._slug("!!!") == "hasil"
