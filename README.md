# Kerjacoy — Cari Kerja Lintas Bidang, Termasuk Lowongan Indonesia

Satu alat baris perintah (CLI) untuk **mencari lowongan kerja apa saja** — tidak
terkunci satu bidang — dari banyak job board sekaligus, lalu **menilai
kecocokannya** dengan profil kamu, **melacak status lamaran**, dan menyiapkan
bahan lamaran (sorotan keahlian + draf cover letter) tanpa perlu kunci API.

Dibangun dari pelajaran repo-repo terbaik yang sudah dianalisis:

- **JobSpy** (speedyapply/JobSpy) → mesin scraping multi-board.
- **career-ops** (career-ops-hq/career-ops) → ide penilaian transparan, pelacakan,
  dan penyesuaian CV tanpa mengarang pengalaman.
- Kekurangan yang dilengkapi di sini: **preset Indonesia terverifikasi**
  (Indeed Indonesia + LinkedIn lokasi Indonesia), **skor tanpa LLM**
  (jalan tanpa kunci API apa pun), **profil contoh lintas bidang**
  (admin, sales, customer service, logistik, umum), dan **entri manual**
  untuk portal yang tidak bisa di-scrape (JobStreet, Glints, Kalibrr).

## Instalasi

**Linux / macOS / WSL2** — satu baris (ala `0dayexploit`):

```bash
curl -fsSL https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.sh | bash
```

Semua tersimpan di `~/.kerjacoy` (repo di `src/`, venv di `venv/`), perintah
`kerjacoy` (dan alias pendek `kc`) dipasang di `~/.local/bin`. Jalankan lagi
kapan saja untuk memperbarui; hapus dengan `bash ~/.kerjacoy/src/install.sh --uninstall`.

**Windows (PowerShell)** — satu baris:

```powershell
irm https://raw.githubusercontent.com/fahmi0812/Kerjacoy/main/install.ps1 | iex
```

Semua tersimpan di `%USERPROFILE%\.kerjacoy`, `kerjacoy.cmd` dipasang di
`bin\` dan ditambahkan ke PATH user. Hapus dengan `install.ps1 -Uninstall`.

**Manual** (bila tidak mau pakai installer):

Linux / macOS:

```bash
git clone https://github.com/fahmi0812/Kerjacoy.git
cd Kerjacoy
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Windows (PowerShell):

```powershell
git clone https://github.com/fahmi0812/Kerjacoy.git
cd Kerjacoy
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

Setelah instalasi manual, perintah `kerjacoy` tersedia di mana saja (selama
venv aktif). Di Windows, konfigurasi tersimpan di `%APPDATA%\kerjacoy`; di
Linux/macOS di `~/.config/kerjacoy`.

> Catatan instalasi: `python-jobspy` punya konflik metadata numpy dengan pip
> resolver. Jika instalasi gagal, jalankan workaround ini (sudah teruji):
>
> ```bash
> pip install --no-deps python-jobspy
> pip install pydantic tls-client requests markdownify regex curl_cffi
> ```

Kebutuhan: Python 3.10+, git.

## Halaman depan

Jalankan `kerjacoy` tanpa argumen untuk membuka halaman depan: logo besar,
baris status provider, lalu kotak cari. Ketik kata kunci lowongan langsung
cari (preset Indonesia, lokasi Indonesia); ketik angka untuk membuka menu
(1 cari · 2 laporan · 3 nilai · 4 tailor · 5 lacak · 6 provider · 7 cek LLM ·
0 keluar). Bila belum ada provider, layar tambah provider langsung terbuka:
isi nama, base URL, API key (diketik tersembunyi), dan model.

Perbarui ke versi terbaru kapan saja (bila terpasang lewat installer):

```bash
kerjacoy update
```

## Cara pakai cepat

Jalankan `kerjacoy` tanpa argumen untuk membuka Terminal Kerjacoy
(menu interaktif — cari, lihat hasil, tailor, lacak, setup provider).

```bash
# 1. Cari lowongan "staff admin" di Indonesia (Indeed ID + LinkedIn ID)
kerjacoy cari --keyword "staff admin" --lokasi Indonesia --preset indonesia \
  --jumlah 50 --jam 168 --profil profil/contoh-admin.yaml \
  --keluaran hasil/staff-admin.csv

# 2. Lihat laporan 20 teratas (otomatis dibuat di hasil/staff-admin.md)
# 3. Tandai yang sudah dilamar
kerjacoy tandai --masukan hasil/staff-admin.csv --url "https://..." --status dilamar

# 4. Siapkan bahan lamaran untuk satu lowongan
kerjacoy tailor --masukan hasil/staff-admin.csv --url "https://..." \
  --profil profil/contoh-admin.yaml
```

## Perintah

Perintah utama adalah **`kerjacoy`** (perintah lama `loker` dan `carikerja`
tetap jalan). Jalankan tanpa argumen untuk membuka **Terminal Kerjacoy**
(menu interaktif); bila belum ada provider LLM, wizard setup langsung
terbuka (ala `0dayexploit`): isi nama provider, base URL endpoint, API key
(diketik tersembunyi), dan model. Data non-rahasia disimpan di
`~/.config/kerjacoy/config.json` (Linux/macOS) atau `%APPDATA%\kerjacoy`
(Windows), API key disimpan terpisah di `credentials.json` (hanya bisa
dibaca kamu) dan tidak pernah ditulis ke file lain. Ulangi setup kapan saja
dengan `kerjacoy setup`; lihat provider aktif dengan `kerjacoy provider`
(key selalu disamarkan). Tambah provider tanpa wizard dengan
`kerjacoy connect` (lihat `kerjacoy connect --help`).

| Perintah | Fungsi |
|---|---|
| `loker cari` | Scrape → bersihkan → dedup → skor → simpan CSV + laporan MD |
| `loker nilai` | Skor ulang CSV yang sudah ada dengan profil lain |
| `loker tambah` | Tambah lowongan manual (mis. link JobStreet/Glints) agar tetap bisa dinilai & dilacak |
| `loker tandai` | Ubah status lowongan: baru / dilihat / dilamar / wawancara / ditolak / diterima |
| `loker tailor` | Sorotan keahlian + pengalaman relevan + draf cover letter (template, tanpa LLM) |
| `loker laporan` | Buat ulang laporan MD dari CSV |
| `loker cek-llm` | Tes koneksi ke endpoint LLM yang dikonfigurasi |
| `kerjacoy` | Buka Terminal Kerjacoy (menu interaktif) |
| `kerjacoy setup` | Setup pertama kali: isi URL + API key + model LLM (wizard) |
| `kerjacoy provider` | Lihat provider LLM yang aktif (key disamarkan) |
| `kerjacoy connect` | Tambah provider LLM (URL + API key, ala `0dayexploit connect`) |

## LLM (opsional)

Tanpa LLM pun semua perintah di atas jalan penuh. LLM hanya menambah
penilaian kedua dan draf cover letter yang lebih luwes.

Atur lewat environment variable (tidak pernah disimpan di repo):

| Variable | Wajib | Keterangan |
|---|---|---|
| `KERJACOY_LLM_API_KEY` | ya | API key endpoint LLM kamu |
| `KERJACOY_LLM_BASE_URL` | tidak | Default `https://api.openai.com/v1`. Isi URL lain bila memakai endpoint yang kompatibel dengan OpenAI (mis. server/gateway sendiri) |
| `KERJACOY_LLM_MODEL` | tidak | Default `gpt-4o-mini`. Nama model apa pun yang disediakan endpoint kamu |

Pemakaian:

```bash
export KERJACOY_LLM_API_KEY="kunci-kamu"
export KERJACOY_LLM_BASE_URL="https://endpoint-kamu/v1"   # bila bukan OpenAI
export KERJACOY_LLM_MODEL="nama-model-kamu"

loker cek-llm                                  # tes koneksi dulu
loker cari --keyword "staff admin" --preset indonesia \
  --profil profil/contoh-admin.yaml --keluaran hasil/staff-admin.csv --llm
loker tailor --masukan hasil/staff-admin.csv --url "<URL lowongan>" \
  --profil profil/contoh-admin.yaml --llm
```

Dengan `--llm`, `cari`/`nilai` menambah kolom `skor_llm` dan `alasan_llm`
di CSV; skor template tetap jadi skor utama dan penentu urutan. `tailor --llm`
memakai LLM hanya untuk menulis draf cover letter — pencocokan keahlian
tetap dari template, dan prompt melarang LLM mengarang pengalaman.
Bila LLM gagal, program lanjut dengan mode tanpa LLM.

## Pakai lewat OpenCode

Repo ini sudah berisi integrasi OpenCode, supaya asisten AI bisa
mengoperasikan Kerjacoy untuk kamu — cari kerja, menilai, melacak lamaran,
dan menyiapkan bahan lamaran — tanpa kamu menghafal perintah CLI.

Yang sudah tersedia di repo:

- **Skill** `.opencode/skills/kerjacoy/SKILL.md` — cara memakai CLI `loker`,
  alur kerja standar, dan aturan keselamatan (tidak pernah melamar tanpa
  persetujuan eksplisit, tidak mengarang data, tidak menulis key ke file).
- **Agent** `.opencode/agents/pemburu-kerja.md` — subagent khusus cari kerja,
  bisa dipanggil dengan `@pemburu-kerja`.
- **Command** `.opencode/commands/cari-kerja.md` — pintasan `/cari-kerja
  <kata kunci>`.
- **`opencode.json`** — contoh provider LLM yang kompatibel dengan OpenAI.
  Key dan URL dibaca dari environment variable, tidak tertulis di file.

Cara pakai:

```bash
# 1. Instal Kerjacoy (lihat "Instalasi" di atas) dan OpenCode (https://opencode.ai)
# 2. Atur kredensial LLM kamu (bila mau pakai LLM):
export KERJACOY_LLM_API_KEY="kunci-kamu"
export KERJACOY_LLM_BASE_URL="https://endpoint-kamu/v1"   # bila bukan OpenAI
export KERJACOY_LLM_MODEL="nama-model-kamu"

# 3. Jalankan OpenCode dari root repo ini:
opencode

# 4. Di dalam OpenCode, mis.:
#    /cari-kerja staff admin
#    @pemburu-kerja nilai ulang hasil/staff-admin.csv dengan profil contoh-admin
```

Tanpa LLM pun skill dan agent tetap jalan penuh — LLM hanya menambah
penilaian kedua dan draf cover letter yang lebih luwes.

Opsi `cari` yang penting:

- `--keyword`: kata kunci, mis. `"staff admin"`, `"customer service"`, `"sales"`.
- `--lokasi`: mis. `Indonesia`, `Jakarta`, `Remote`, `Bandung`.
- `--preset indonesia`: Indeed Indonesia + LinkedIn Indonesia.
- `--preset global`: Indeed + LinkedIn + ZipRecruiter + Glassdoor.
- `--preset luas`: semua board JobSpy — Indeed, LinkedIn, Google Jobs, Glassdoor, ZipRecruiter, Bayt, Naukri (cakupan terluas; situs yang gagal dilewati, hasil parsial tetap dipakai).
- `--situs`: pilih manual, mis. `--situs indeed,linkedin`.
- `--negara-indeed`: mis. `Indonesia`, `USA` (khusus Indeed).
- `--jumlah`: jumlah hasil per situs. `--jam`: hanya lowongan N jam terakhir.

## Profil

Profil adalah file YAML yang menjelaskan siapa pelamarnya. Lihat `profil/`:

- `contoh-umum.yaml` — pelamar fleksibel segala bidang.
- `contoh-admin.yaml`, `contoh-sales.yaml`,
  `contoh-customer-service.yaml`, `contoh-logistik.yaml`.

Isi profil: `nama`, `ringkasan`, `keahlian`, `jabatan_diinginkan`,
`lokasi_diinginkan`, `kata_hindari`, `pengalaman`. Skor dihitung transparan:

- Judul mengandung jabatan yang diinginkan: maks 40 poin.
- Deskripsi mengandung keahlian profil: maks 30 poin.
- Lokasi cocok: 15 poin. Kebaruan lowongan: maks 15 poin.
- Mengandung kata yang dihindari (mis. "bayar di muka", "deposit"): −25 per kata.

Kolom `alasan_skor` di CSV menjelaskan kenapa sebuah lowongan dapat skor itu —
tidak ada skor misterius.

## Keterbatasan (jujur, hasil uji langsung)

- **ZipRecruiter** memblokir IP cloud (HTTP 403) — butuh proxy untuk situs itu.
- **Indeed & Glassdoor** kadang timeout dari IP datacenter; ulangi atau pakai
  koneksi rumahan.
- **JobStreet, Glints, Kalibrr** tidak bisa di-scrape langsung karena proteksi
  bot — pakai `loker tambah` untuk memasukkan linknya manual, lalu tetap bisa
  dinilai, dilacak, dan dibuatkan bahan lamarannya.
- **Terverifikasi langsung 5 Nov 2026:** Indeed Indonesia dan LinkedIn lokasi
  Indonesia mengembalikan lowongan Indonesia asli (mis. "Staff Admin" di
  Tangerang, "Secretary" di Astra International Jakarta).
- Bahan lamaran di sini berbasis template dari data profil kamu sendiri —
  tidak mengarang pengalaman. Penulisan ulang penuh oleh AI tersedia lewat
  flag `--llm` (lihat "LLM (opsional)" di atas).

## Tes

```bash
pip install pytest
pytest -q            # tes unit (tanpa internet)
```

Uji langsung (smoke test) 5 Nov 2026: `loker cari` dengan kata kunci
"staff admin", lokasi Indonesia, 10 hasil per situs — Indeed Indonesia dan
LinkedIn Indonesia masing-masing mengembalikan 10 lowongan asli; laporan dan
CSV tersimpan di `contoh/`.

## Lisensi

MIT. Dibuat untuk membantu pencari kerja; gunakan dengan bijak dan hormati
ketentuan tiap job board.
