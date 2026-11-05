"""Dukungan LLM opsional lewat endpoint yang kompatibel dengan OpenAI.

Prinsip:
- Repo ini TIDAK menyimpan API key atau URL siapa pun. Semua konfigurasi
  dibaca dari environment variable saat program dijalankan.
- Endpoint apa pun yang mengikuti format OpenAI (``/v1/chat/completions``)
  bisa dipakai: OpenAI resmi, maupun server/gateway lain yang kompatibel.
  Model ditulis bebas lewat env var, termasuk nama model custom.
- LLM hanya dipakai untuk penilaian tambahan dan draf surat lamaran.
  Skor template yang transparan tetap jadi skor utama, dan pencocokan
  keahlian tetap berbasis template (tidak mengarang pengalaman).
- Kalau LLM gagal (tidak terkonfigurasi, endpoint mati, balasan tidak
  valid), program jatuh kembali ke mode tanpa LLM, bukan crash.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

ENV_BASE_URL = "KERJACOY_LLM_BASE_URL"
ENV_API_KEY = "KERJACOY_LLM_API_KEY"
ENV_MODEL = "KERJACOY_LLM_MODEL"

# Nama lama tetap dibaca sebagai fallback (rantai: KERJACOY -> CARIKERJA -> CARILOKER).
_ENV_LAMA = {
    ENV_BASE_URL: ("CARIKERJA_LLM_BASE_URL", "CARILOKER_LLM_BASE_URL"),
    ENV_API_KEY: ("CARIKERJA_LLM_API_KEY", "CARILOKER_LLM_API_KEY"),
    ENV_MODEL: ("CARIKERJA_LLM_MODEL", "CARILOKER_LLM_MODEL"),
}


def ambil_env(nama: str) -> str | None:
    """Ambil env var baru; fallback ke nama-nama lama bila belum diisi."""
    if os.environ.get(nama):
        return os.environ.get(nama)
    for lama in _ENV_LAMA.get(nama, ()):
        if os.environ.get(lama):
            return os.environ.get(lama)
    return None

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


class LLMError(Exception):
    """Gagal memakai LLM (konfigurasi, jaringan, atau balasan tidak valid)."""


@dataclass
class KonfigurasiLLM:
    base_url: str
    api_key: str
    model: str


def muat_konfigurasi() -> KonfigurasiLLM:
    """Baca konfigurasi LLM: environment variable dulu, lalu file setup.

    Urutan: KERJACOY_LLM_* (env) menang atas file konfigurasi
    (~/.config/kerjacoy/config.json + credentials.json) yang diisi lewat
    wizard `kerjacoy setup`. Tanpa keduanya, kembalikan default kosong.
    """
    base_url = ambil_env(ENV_BASE_URL)
    api_key = ambil_env(ENV_API_KEY)
    model = ambil_env(ENV_MODEL)
    if not (base_url and api_key and model):
        # Lazy import: setup memakai konstanta dari modul ini.
        from .setup import muat_pengaturan

        pengaturan = muat_pengaturan()
        base_url = base_url or pengaturan.get("base_url", DEFAULT_BASE_URL)
        api_key = api_key or pengaturan.get("api_key", "")
        model = model or pengaturan.get("model", DEFAULT_MODEL)
    return KonfigurasiLLM(
        base_url=(base_url or DEFAULT_BASE_URL).rstrip("/"),
        api_key=api_key or "",
        model=model or DEFAULT_MODEL,
    )


def llm_tersedia(cfg: KonfigurasiLLM | None = None) -> bool:
    """True bila key + base URL + model sudah diisi."""
    cfg = cfg or muat_konfigurasi()
    return bool(cfg.api_key and cfg.base_url and cfg.model)


def _minta(cfg: KonfigurasiLLM, payload: dict, timeout: int = 60) -> dict:
    url = f"{cfg.base_url}/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:300]
        except Exception:
            detail = ""
        raise LLMError(f"endpoint menolak permintaan (HTTP {e.code}): {detail}") from e
    except urllib.error.URLError as e:
        raise LLMError(f"tidak bisa menghubungi endpoint {cfg.base_url}: {e.reason}") from e
    except (json.JSONDecodeError, TimeoutError) as e:
        raise LLMError(f"balasan endpoint tidak bisa dibaca: {e}") from e


def chat(cfg: KonfigurasiLLM, pesan_sistem: str, pesan_user: str,
         timeout: int = 60) -> str:
    """Satu kali panggil chat completion; kembalikan isi balasan sebagai teks."""
    if not llm_tersedia(cfg):
        raise LLMError(
            "LLM belum dikonfigurasi. Isi environment variable: "
            f"{ENV_API_KEY}, {ENV_BASE_URL} (opsional), {ENV_MODEL} (opsional)."
        )
    hasil = _minta(cfg, {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": pesan_sistem},
            {"role": "user", "content": pesan_user},
        ],
        "temperature": 0.2,
    }, timeout=timeout)
    try:
        return hasil["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError) as e:
        raise LLMError("balasan endpoint tidak berisi teks chat") from e


def cek_koneksi(cfg: KonfigurasiLLM | None = None) -> tuple[bool, str]:
    """Tes cepat: panggil endpoint dengan pesan minimal. Kembalikan (ok, pesan)."""
    cfg = cfg or muat_konfigurasi()
    if not llm_tersedia(cfg):
        return False, (
            "LLM belum dikonfigurasi. Isi dulu "
            f"{ENV_API_KEY} (wajib), {ENV_BASE_URL} dan {ENV_MODEL} (opsional)."
        )
    try:
        balasan = chat(cfg, "Jawab singkat saja.", "Balas dengan satu kata: ok", timeout=30)
    except LLMError as e:
        return False, f"Gagal: {e}"
    return True, f"Terhubung ke {cfg.base_url} (model: {cfg.model}). Balasan: {balasan[:80]}"


def daftar_model(base_url: str, api_key: str, timeout: int = 15) -> list[str]:
    """Ambil daftar model dari {base_url}/models (dipakai layar provider).

    Kembalikan daftar id model (bisa kosong bila endpoint tidak menyediakannya).
    """
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise LLMError(f"endpoint menolak permintaan (HTTP {e.code})") from e
    except urllib.error.URLError as e:
        raise LLMError(f"tidak bisa menghubungi endpoint {base_url}: {e.reason}") from e
    except (json.JSONDecodeError, TimeoutError) as e:
        raise LLMError(f"balasan endpoint tidak bisa dibaca: {e}") from e
    try:
        return [m["id"] for m in data["data"] if m.get("id")]
    except (KeyError, TypeError):
        return []


def _ambil_json(teks: str) -> dict:
    """Ambil objek JSON pertama dari teks balasan (tahan terhadap ```json fence)."""
    bersih = re.sub(r"```(?:json)?\s*", "", teks).replace("```", "")
    cocok = re.search(r"\{.*\}", bersih, re.DOTALL)
    if not cocok:
        raise LLMError("balasan LLM tidak mengandung JSON")
    try:
        return json.loads(cocok.group(0))
    except json.JSONDecodeError as e:
        raise LLMError(f"balasan LLM bukan JSON valid: {e}") from e


def skor_llm(cfg: KonfigurasiLLM, lowongan: dict, profil: dict) -> tuple[int, list[str]]:
    """Nilai kecocokan 0-100 lewat LLM. Kembalikan (skor, alasan).

    LLM hanya menilai dari teks lowongan + profil yang diberikan.
    """
    desk = str(lowongan.get("description") or "")[:1500]
    pesan_user = (
        "Nilai kecocokan lowongan ini dengan profil pelamar, skor 0-100.\n\n"
        f"Lowongan: {lowongan.get('title')} — {lowongan.get('company')} "
        f"({lowongan.get('location')})\nDeskripsi: {desk}\n\n"
        f"Profil: keahlian {profil.get('keahlian')}, "
        f"jabatan diinginkan {profil.get('jabatan_diinginkan')}, "
        f"lokasi diinginkan {profil.get('lokasi_diinginkan')}.\n\n"
        'Jawab HANYA dengan JSON: {"skor": 82, "alasan": ["alasan singkat", ...]}. '
        "Maksimal 3 alasan, bahasa Indonesia."
    )
    balasan = chat(
        cfg,
        "Kamu penilai lowongan kerja. Jawab hanya dengan JSON valid, tanpa teks lain.",
        pesan_user,
    )
    data = _ambil_json(balasan)
    try:
        skor = int(data["skor"])
        alasan = [str(a) for a in (data.get("alasan") or [])][:3]
    except (KeyError, TypeError, ValueError) as e:
        raise LLMError("JSON dari LLM tidak berisi skor yang valid") from e
    if not 0 <= skor <= 100:
        raise LLMError(f"skor dari LLM di luar 0-100: {skor}")
    return skor, alasan


def draf_cover_letter_llm(cfg: KonfigurasiLLM, lowongan: dict, profil: dict,
                          hasil_template: dict) -> str:
    """Tulis draf pembuka cover letter lewat LLM.

    Hanya memakai data profil yang diberikan — prompt melarang mengarang
    pengalaman atau keahlian yang tidak ada di profil.
    """
    pesan_user = (
        "Tulis draf pembuka surat lamaran (3-4 kalimat, bahasa Indonesia, sopan) "
        "untuk lowongan ini.\n\n"
        f"Lowongan: {lowongan.get('title')} — {lowongan.get('company')}\n"
        f"Keahlian yang cocok (dari pencocokan profil): "
        f"{', '.join(hasil_template.get('keahlian_cocok') or []) or '-'}\n"
        f"Pengalaman relevan (dari profil): "
        f"{'; '.join(hasil_template.get('pengalaman_relevan') or []) or '-'}\n"
        f"Nama pelamar: {profil.get('nama') or '[Nama Kamu]'}\n"
        f"Ringkasan profil: {profil.get('ringkasan') or '-'}\n\n"
        "ATURAN: dilarang mengarang pengalaman, keahlian, gelar, atau prestasi "
        "yang tidak tertulis di atas. Bila data kurang, tulis kalimat umum saja."
    )
    return chat(
        cfg,
        "Kamu menulis draf surat lamaran. Jangan pernah mengarang data pelamar.",
        pesan_user,
    )
