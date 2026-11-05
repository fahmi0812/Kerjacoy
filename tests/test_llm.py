"""Tes modul LLM memakai server tiruan lokal (stub OpenAI-compatible).

Tidak ada panggilan ke internet di sini: stub berjalan di 127.0.0.1
dengan port acak, dan balasan bisa diatur per tes lewat StubHandler.balasan.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from loker_plus.llm import (
    LLMError,
    cek_koneksi,
    chat,
    draf_cover_letter_llm,
    llm_tersedia,
    muat_konfigurasi,
    skor_llm,
)


class StubHandler(BaseHTTPRequestHandler):
    balasan = "ok"
    status = 200

    def log_message(self, *args):
        pass

    def do_POST(self):  # noqa: N802
        panjang = int(self.headers.get("Content-Length", 0))
        self.rfile.read(panjang)
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.status == 200:
            tubuh = {
                "choices": [{"message": {"content": self.balasan}}],
            }
        else:
            tubuh = {"error": {"message": "stub error"}}
        self.wfile.write(json.dumps(tubuh).encode())


@pytest.fixture(scope="module")
def server_stub():
    server = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
    utas = threading.Thread(target=server.serve_forever, daemon=True)
    utas.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture
def cfg_stub(server_stub, monkeypatch):
    # Client menambah /chat/completions ke base URL, jadi base URL harus
    # sudah mengandung /v1 seperti endpoint OpenAI-compatible sungguhan.
    monkeypatch.setenv("KERJACOY_LLM_BASE_URL", server_stub + "/v1")
    monkeypatch.setenv("KERJACOY_LLM_API_KEY", "kunci-tes")
    monkeypatch.setenv("KERJACOY_LLM_MODEL", "model-tes")
    StubHandler.status = 200
    StubHandler.balasan = "ok"
    return muat_konfigurasi()


def test_muat_konfigurasi_dari_env(cfg_stub, server_stub):
    assert cfg_stub.base_url == server_stub + "/v1"
    assert cfg_stub.api_key == "kunci-tes"
    assert cfg_stub.model == "model-tes"
    assert llm_tersedia(cfg_stub)


def test_llm_tidak_tersedia_tanpa_key(monkeypatch):
    monkeypatch.delenv("KERJACOY_LLM_API_KEY", raising=False)
    assert not llm_tersedia()


def test_chat_mengembalikan_teks(cfg_stub):
    StubHandler.balasan = "halo dari stub"
    assert chat(cfg_stub, "sistem", "user") == "halo dari stub"


def test_chat_gagal_http_500(cfg_stub):
    StubHandler.status = 500
    with pytest.raises(LLMError, match="HTTP 500"):
        chat(cfg_stub, "sistem", "user")


def test_skor_llm_parse_json(cfg_stub):
    StubHandler.balasan = '```json\n{"skor": 82, "alasan": ["judul cocok", "skill cocok"]}\n```'
    lowongan = {"title": "Staff Admin", "company": "PT X", "location": "Jakarta",
                "description": "Butuh admin yang bisa Excel."}
    profil = {"keahlian": ["excel"], "jabatan_diinginkan": ["admin"],
              "lokasi_diinginkan": ["jakarta"]}
    skor, alasan = skor_llm(cfg_stub, lowongan, profil)
    assert skor == 82
    assert alasan == ["judul cocok", "skill cocok"]


def test_skor_llm_gagal_bila_bukan_json(cfg_stub):
    StubHandler.balasan = "maaf, tidak bisa menilai"
    with pytest.raises(LLMError):
        skor_llm(cfg_stub, {"title": "X"}, {})


def test_skor_llm_gagal_bila_skor_di_luar_range(cfg_stub):
    StubHandler.balasan = '{"skor": 150, "alasan": []}'
    with pytest.raises(LLMError):
        skor_llm(cfg_stub, {"title": "X"}, {})


def test_draf_cover_letter_llm(cfg_stub):
    StubHandler.balasan = "Yth. Tim Rekrutmen, saya tertarik melamar."
    hasil = draf_cover_letter_llm(cfg_stub, {"title": "Admin", "company": "PT X"},
                                  {"nama": "Budi"}, {"keahlian_cocok": ["excel"],
                                   "pengalaman_relevan": ["Admin di PT Y"]})
    assert "tertarik melamar" in hasil


def test_cek_koneksi_ok(cfg_stub):
    ok, pesan = cek_koneksi(cfg_stub)
    assert ok
    assert "Terhubung" in pesan


def test_cek_koneksi_gagal_tanpa_key(monkeypatch):
    monkeypatch.delenv("KERJACOY_LLM_API_KEY", raising=False)
    ok, pesan = cek_koneksi()
    assert not ok
    assert "belum dikonfigurasi" in pesan
