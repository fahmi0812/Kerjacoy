"""Setup pertama kali ala 0DayExploit: jalankan `kerjacoy`, masukkan URL + key.

Pola yang dipakai (meniru repo 0DayExploit):
- Perintah pertama kali membuka wizard: pilih nama provider, isi base URL,
  API key (diketik tersembunyi, tampil sebagai •••), dan model.
- Data non-rahasia (nama provider, base URL, model) disimpan di
  `config.json`; API key disimpan TERPISAH di `credentials.json` dengan
  izin baca hanya pemilik (0600). Key tidak pernah ditulis ke file lain.
- Saat program jalan, key diteruskan lewat environment variable internal,
  sama seperti cara 0DayExploit meneruskannya ke engine.
- Environment variable KERJACOY_LLM_* tetap menang atas file, supaya
  integrasi OpenCode dan skrip lama tidak berubah.
"""

from __future__ import annotations

import getpass
import json
import os
from pathlib import Path

from .llm import DEFAULT_BASE_URL, DEFAULT_MODEL, ENV_API_KEY, ENV_BASE_URL, ENV_MODEL, ambil_env

CONFIG_DIRNAME = "kerjacoy"
CONFIG_FILE = "config.json"
CREDENTIALS_FILE = "credentials.json"


def _is_windows() -> bool:
    return os.name == "nt"


def config_dir() -> Path:
    """Direktori config, lintas platform.

    Windows: %APPDATA%/kerjacoy. Linux/macOS: $XDG_CONFIG_HOME/kerjacoy
    atau ~/.config/kerjacoy.
    """
    if _is_windows():
        dasar = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        dasar = Path(xdg) if xdg else Path.home() / ".config"
    return dasar / CONFIG_DIRNAME


def _baca_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _tulis_json(path: Path, data: dict, rahasia: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if rahasia:
        try:
            # Unix: hanya pemilik yang bisa baca. Windows: chmod tidak
            # mengatur ACL, jadi abaikan kegagalan dengan tenang.
            os.chmod(path, 0o600)
        except (OSError, NotImplementedError):
            pass


def muat_pengaturan() -> dict:
    """Gabungkan config file + credentials file. Kembalikan dict kosong bila belum ada."""
    cfg = _baca_json(config_dir() / CONFIG_FILE)
    kred = _baca_json(config_dir() / CREDENTIALS_FILE)
    gabung = dict(cfg)
    if kred.get("api_key"):
        gabung["api_key"] = kred["api_key"]
    return gabung


def simpan_pengaturan(nama: str, base_url: str, model: str, api_key: str) -> Path:
    """Simpan provider. Kembalikan path direktori config."""
    direktori = config_dir()
    _tulis_json(direktori / CONFIG_FILE, {
        "provider": nama,
        "base_url": base_url,
        "model": model,
    })
    _tulis_json(direktori / CREDENTIALS_FILE, {"api_key": api_key}, rahasia=True)
    return direktori


def provider_dikonfigurasi() -> bool:
    """True bila ada API key (dari env atau file) — cukup untuk memakai LLM."""
    if ambil_env(ENV_API_KEY):
        return True
    return bool(muat_pengaturan().get("api_key"))


def _tanya(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    jawab = input(f"{prompt}{suffix}: ").strip()
    return jawab or default


def jalankan_wizard() -> dict:
    """Wizard interaktif pertama kali. Kembalikan pengaturan yang disimpan."""
    print("Belum ada provider LLM yang dikonfigurasi.")
    print("Isi sekali saja — disimpan lokal di komputer kamu, tidak dikirim ke mana pun.")
    print()
    nama = _tanya("Nama provider", "kerjacoy-llm")
    base_url = _tanya("Base URL endpoint (harus berakhiran /v1)", DEFAULT_BASE_URL)
    model = _tanya("Model", DEFAULT_MODEL)
    while True:
        api_key = getpass.getpass("API key (diketik tersembunyi): ").strip()
        if api_key:
            break
        print("API key tidak boleh kosong.")
    direktori = simpan_pengaturan(nama, base_url.rstrip("/"), model, api_key)
    print()
    print(f"Tersimpan di {direktori} (key hanya bisa dibaca kamu).")
    print(f"Provider '{nama}' siap — model {model}.")
    return muat_pengaturan()


def tampilkan_provider() -> None:
    """Tampilkan provider yang aktif, dengan key disamarkan."""
    pengaturan = muat_pengaturan()
    env_key = ambil_env(ENV_API_KEY)
    if env_key:
        print("Provider aktif dari environment variable:")
        print(f"  base URL : {ambil_env(ENV_BASE_URL) or DEFAULT_BASE_URL}")
        print(f"  model    : {ambil_env(ENV_MODEL) or DEFAULT_MODEL}")
        print(f"  API key  : {'•' * 8} (dari env)")
        return
    if not pengaturan:
        print("Belum ada provider yang dikonfigurasi.")
        print("Jalankan: kerjacoy setup")
        return
    print("Provider aktif dari file konfigurasi:")
    print(f"  nama     : {pengaturan.get('provider', '-')}")
    print(f"  base URL : {pengaturan.get('base_url', '-')}")
    print(f"  model    : {pengaturan.get('model', '-')}")
    print(f"  API key  : {'•' * 8} (tersimpan di {config_dir() / CREDENTIALS_FILE})")
