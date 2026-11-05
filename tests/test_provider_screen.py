"""Tes layar provider interaktif (parser tombol, reducer, render, alur penuh)."""

from __future__ import annotations

import io

import pytest

from loker_plus import provider_screen as layar
from loker_plus import setup as setup_mod


def test_parse_keys_escape_sequence():
    assert layar.parse_keys("\x1b[A") == [{"t": "up"}]
    assert layar.parse_keys("\x1b[B") == [{"t": "down"}]
    assert layar.parse_keys("\t") == [{"t": "tab"}]
    assert layar.parse_keys("\x1b[Z") == [{"t": "shift-tab"}]
    assert layar.parse_keys("\x1b[3~") == [{"t": "delete"}]
    assert layar.parse_keys("\x1b") == [{"t": "esc"}]
    assert layar.parse_keys("\r") == [{"t": "enter"}]
    assert layar.parse_keys("\r\n") == [{"t": "enter"}]
    assert layar.parse_keys("\x7f") == [{"t": "backspace"}]
    assert layar.parse_keys("\x03") == [{"t": "ctrl-c"}]


def test_parse_keys_paste():
    assert layar.parse_keys("\x1b[200~http://x/v1\x1b[201~") == [
        {"t": "paste", "v": "http://x/v1"}]
    assert layar.parse_keys("abc") == [{"t": "paste", "v": "abc"}]
    assert layar.parse_keys("a") == [{"t": "char", "v": "a"}]
    assert layar.parse_keys("a\x1b[200~b\x1b[201~c") == [
        {"t": "char", "v": "a"}, {"t": "paste", "v": "b"}, {"t": "char", "v": "c"}]


def test_mask():
    assert layar.mask("kunci-rahasia") == "•" * 13
    assert layar.mask("") == ""


def test_reduce_pindah_dan_ketik():
    st = layar.init_state(None)
    assert st["focus"] == "form:nama"
    layar.reduce(st, {"t": "char", "v": "D"})
    layar.reduce(st, {"t": "char", "v": "emo"})
    assert st["nama"] == "demo"  # nama selalu huruf kecil
    layar.reduce(st, {"t": "tab"})
    assert st["focus"] == "form:base_url"
    layar.reduce(st, {"t": "char", "v": "http://127.0.0.1:9/v1"})
    assert st["base_url"] == "http://127.0.0.1:9/v1"
    layar.reduce(st, {"t": "backspace"})
    assert st["base_url"] == "http://127.0.0.1:9/v"
    layar.reduce(st, {"t": "clear"})
    assert st["base_url"] == ""
    layar.reduce(st, {"t": "shift-tab"})
    assert st["focus"] == "form:nama"


def test_reduce_enter_simpan_dan_esc_keluar():
    st = layar.init_state(None)
    assert layar.reduce(st, {"t": "enter"}) == {"simpan": True}
    assert layar.reduce(st, {"t": "esc"}) == {"keluar": True}
    assert st["selesai"] is True


def test_reduce_hapus_dengan_konfirmasi():
    st = layar.init_state({"provider": "demo", "model": "m", "api_key": "k"})
    assert st["focus"] == "form:nama"
    layar.reduce(st, {"t": "shift-tab"})
    assert st["focus"] == "tersimpan"
    assert layar.reduce(st, {"t": "delete"}) is None
    assert st["confirm"] == "demo"
    assert layar.reduce(st, {"t": "char", "v": "y"}) == {"hapus": "demo"}


def test_reduce_hapus_batal():
    st = layar.init_state({"provider": "demo", "model": "m", "api_key": "k"})
    st["focus"] = "tersimpan"
    layar.reduce(st, {"t": "delete"})
    assert layar.reduce(st, {"t": "char", "v": "n"}) is None
    assert st["confirm"] is None


def test_render_memuat_form_dan_key_tersamar():
    st = layar.init_state({"provider": "demo", "model": "model-x", "api_key": "k"})
    st["nama"] = "baru"
    st["key"] = "kunci-x"
    keluar = layar.render(st, 80, 24)
    assert "Tambah provider" in keluar
    assert "Nama" in keluar and "Base URL" in keluar and "API Key" in keluar
    assert "kunci-x" not in keluar
    assert "•" * 7 in keluar
    assert "Tab pindah" in keluar and "Esc lewati" in keluar
    assert "demo" in keluar


class _InputPalsu:
    """Input non-TTY yang mengembalikan potongan skrip."""

    def __init__(self, teks):
        self._buf = io.StringIO(teks)

    def read(self, n=-1):
        return self._buf.read(n)

    def isatty(self):
        return False


@pytest.fixture
def home_sementara(tmp_path, monkeypatch):
    monkeypatch.setenv("KERJACOY_HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    for var in ("KERJACOY_LLM_BASE_URL", "KERJACOY_LLM_API_KEY", "KERJACOY_LLM_MODEL"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


def test_layar_penuh_simpan_lalu_keluar(home_sementara):
    def verifikasi_palsu(base_url, key):
        assert base_url == "http://127.0.0.1:9/v1"
        assert key == "kunci-x"
        return ["model-a", "model-b"]

    skrip = "demo\t http://127.0.0.1:9/v1\tkunci-x\r\x1b"
    keluar = io.StringIO()
    hasil = layar.jalankan_layar(verifikasi=verifikasi_palsu,
                                 input=_InputPalsu(skrip), output=keluar)
    assert hasil == 1
    pengaturan = setup_mod.muat_pengaturan()
    assert pengaturan["provider"] == "demo"
    assert pengaturan["model"] == "model-a"
    assert pengaturan["api_key"] == "kunci-x"
    teks = keluar.getvalue()
    assert "Terhubung" in teks
    assert "2 model" in teks
    assert "kunci-x" not in teks


def test_layar_gagal_koneksi_tidak_menyimpan(home_sementara):
    def verifikasi_gagal(base_url, key):
        from loker_plus.llm import LLMError
        raise LLMError("endpoint menolak permintaan (HTTP 401)")

    skrip = "demo\t http://127.0.0.1:9/v1\tkunci-x\r\x1b"
    keluar = io.StringIO()
    hasil = layar.jalankan_layar(verifikasi=verifikasi_gagal,
                                 input=_InputPalsu(skrip), output=keluar)
    assert hasil == 0
    assert setup_mod.muat_pengaturan() == {}
    assert "401" in keluar.getvalue()


def test_layar_hapus_provider_tersimpan(home_sementara):
    setup_mod.simpan_pengaturan("demo", "http://127.0.0.1:9/v1", "model-a", "kunci-x")
    skrip = "\x1b[Z\x7fy\x1b"  # shift-tab ke baris tersimpan, Del, y, Esc
    keluar = io.StringIO()
    hasil = layar.jalankan_layar(verifikasi=lambda b, k: [],
                                 input=_InputPalsu(skrip), output=keluar)
    assert hasil == 0
    assert setup_mod.muat_pengaturan() == {}
    assert "dihapus" in keluar.getvalue()
