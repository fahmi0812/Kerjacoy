<p align="center"><img src="assets/brand/banner.svg" alt="Kerjacoy" width="640"></p>

# Kerjacoy

Kerjacoy membantu kamu cari kerja: mencari lowongan lintas bidang, menilai kecocokan dengan profilmu, melacak status lamaran, dan menyiapkan bahan lamaran. Termasuk lowongan Indonesia.

Ada dua cara pakai: **agen** (`kerjacoy`) — kamu ketik maumu, dia yang bekerja; dan **perintah langsung** (`loker`) — untuk yang mau cepat lewat terminal.

## Instalasi

Linux, macOS, atau WSL2 — satu baris:

```bash
curl -fsSL https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.sh | bash
```

Semua tersimpan di `~/.kerjacoy`. Perintah `kerjacoy` (alias `kc`) dan `loker` dipasang di `~/.local/bin`. Jalankan lagi kapan saja untuk memperbarui; hapus dengan `bash ~/.kerjacoy/src/install.sh --uninstall`.

Windows — lewat npm (butuh Node.js 22.6+ dan Python 3.10+):

```powershell
npm install -g https://github.com/fahmi0812/Kerjacoy/tarball/v2.0.0
```

Hapus dengan `npm uninstall -g kerjacoy`, lalu hapus `%USERPROFILE%\.kerjacoy`. Kalau hanya butuh mesin `loker` saja di Windows: `irm https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.ps1 | iex`.

Butuh: Python 3.10+, git, dan Node.js 22.6+ (untuk agen; tidak perlu kalau hanya memakai `loker`).

## Pakai agennya

Jalankan `kerjacoy`. Kalau belum ada provider, layar tambah provider terbuka — isi nama, alamat server, dan API key, lalu koneksi dites dan daftar model diambil.

![Layar provider](docs/provider-screen.svg)

Setelah itu ketik saja, misalnya:

```
cari kerja staff admin di Indonesia
nilai ulang hasil/staff-admin.csv dengan profil contoh-admin
siapkan bahan lamaran untuk lowongan Staff Admin di SEVIMA
tandai lowongan yang sudah saya lamar
```

Perbarui ke versi terbaru: `kerjacoy update`. Tambah atau ubah provider: `kerjacoy provider`, atau `kerjacoy connect --list` untuk melihat yang tersimpan.

## Pakai perintah langsung

Jalankan `loker` tanpa argumen untuk membuka menu interaktif.

![Terminal loker](docs/front-page.svg)

Atau pakai perintah langsung:

```bash
# Cari "staff admin" di Indonesia (Indeed Indonesia + LinkedIn Indonesia)
loker cari --keyword "staff admin" --lokasi Indonesia --preset indonesia \
  --jumlah 50 --jam 168 --profil ~/.kerjacoy/config/profil/contoh-admin.yaml \
  --keluaran hasil/staff-admin.csv

# Tandai yang sudah dilamar
loker tandai --masukan hasil/staff-admin.csv --url "https://..." --status dilamar

# Siapkan bahan lamaran untuk satu lowongan
loker tailor --masukan hasil/staff-admin.csv --url "https://..." \
  --profil ~/.kerjacoy/config/profil/contoh-admin.yaml
```

## Perintah

| Perintah | Fungsi |
|---|---|
| `kerjacoy` | Buka agen; kalau belum ada provider, layar provider terbuka dulu |
| `kerjacoy provider` | Tambah, lihat, atau hapus provider (key selalu disamarkan) |
| `kerjacoy connect` | Tambah provider dari baris perintah |
| `kerjacoy update` | Perbarui Kerjacoy ke rilis terbaru |
| `loker` | Buka menu interaktif mesin pencari kerja |
| `loker cari` | Cari lowongan, beri skor, simpan CSV + laporan |
| `loker nilai` | Skor ulang CSV yang sudah ada dengan profil lain |
| `loker tambah` | Tambah lowongan manual (mis. tautan JobStreet/Glints) |
| `loker tandai` | Ubah status: baru / dilihat / dilamar / wawancara / ditolak / diterima |
| `loker tailor` | Sorotan keahlian + draf cover letter dari data profilmu |
| `loker laporan` | Buat ulang laporan dari CSV |
| `loker cek-llm` | Tes koneksi ke server LLM yang dikonfigurasi |

Opsi `cari` yang sering dipakai: `--keyword`, `--lokasi` (mis. `Indonesia`, `Jakarta`, `Remote`), `--preset indonesia` (Indeed Indonesia + LinkedIn Indonesia), `--preset global`, `--preset luas` (semua board: Indeed, LinkedIn, Google Jobs, Glassdoor, ZipRecruiter, Bayt, Naukri), `--situs`, `--jumlah`, `--jam` (hanya lowongan N jam terakhir).

## LLM (opsional)

Semua perintah di atas jalan penuh tanpa LLM. LLM hanya menambah penilaian kedua dan draf cover letter yang lebih luwes.

Untuk agen, LLM diatur lewat layar provider (`kerjacoy provider`). Agen memakai provider aktif, dan mesin `loker` yang dipanggil agen memakai provider yang sama.

Untuk `loker` langsung, atur lewat environment variable:

| Variable | Keterangan |
|---|---|
| `KERJACOY_LLM_API_KEY` | API key server LLM kamu |
| `KERJACOY_LLM_BASE_URL` | Alamat server (default `https://api.openai.com/v1`) |
| `KERJACOY_LLM_MODEL` | Nama model (default `gpt-4o-mini`) |

```bash
export KERJACOY_LLM_API_KEY="kunci-kamu"
export KERJACOY_LLM_BASE_URL="https://endpoint-kamu/v1"
export KERJACOY_LLM_MODEL="nama-model-kamu"

loker cek-llm
loker cari --keyword "staff admin" --preset indonesia \
  --profil ~/.kerjacoy/config/profil/contoh-admin.yaml \
  --keluaran hasil/staff-admin.csv --llm
```

Dengan `--llm`, `cari`/`nilai` menambah kolom `skor_llm` dan `alasan_llm` di CSV; skor utama tetap dari aturan yang transparan (lihat Profil). `tailor --llm` memakai LLM hanya untuk menulis draf cover letter — pencocokan keahlian tetap dari data profilmu, dan LLM dilarang mengarang pengalaman. Kalau LLM gagal, program lanjut tanpa LLM.

## Profil

Profil adalah file YAML yang menjelaskan siapa pelamarnya. Setelah instalasi, profil contoh ada di `~/.kerjacoy/config/profil/` dan bisa diedit:

- `contoh-umum.yaml` — pelamar fleksibel segala bidang.
- `contoh-admin.yaml`, `contoh-sales.yaml`, `contoh-customer-service.yaml`, `contoh-logistik.yaml`.

Skor dihitung dengan aturan yang bisa dibaca di CSV (`alasan_skor`): judul cocok (maks 40), keahlian cocok (maks 30), lokasi cocok (15), lowongan baru (maks 15), kata yang dihindari (mis. "bayar di muka", "deposit") −25 per kata.

## Catatan

- ZipRecruiter memblokir IP cloud (HTTP 403) — butuh proxy untuk situs itu.
- Indeed dan Glassdoor kadang timeout dari IP datacenter; ulangi atau pakai koneksi rumahan.
- JobStreet, Glints, dan Kalibrr tidak bisa diambil langsung karena proteksi bot — pakai `loker tambah` untuk memasukkan tautannya manual, lalu tetap bisa dinilai, dilacak, dan dibuatkan bahan lamarannya.
- Sudah dites 5 Nov 2026: Indeed Indonesia dan LinkedIn lokasi Indonesia mengembalikan lowongan Indonesia asli.
- `kerjacoy run` (mode sekali jalan) belum jalan di semua mesin — pakai `kerjacoy` tanpa argumen. Logo di dalam agen masih logo OpenCode; logo Kerjacoy tampil di layar provider dan halaman depan.

## Kredit

Dibangun di atas [OpenCode](https://opencode.ai) 2.2.4 (MIT) dan pola [0DayExploit](https://github.com/fahmi0812/0DayExploit) — lihat `NOTICE.md`. Mesin pencari kerja memakai [JobSpy](https://github.com/speedyapply/JobSpy); penilaian transparan dan pelacakan terinspirasi [career-ops](https://github.com/career-ops-hq/career-ops).

## Lisensi

MIT.
