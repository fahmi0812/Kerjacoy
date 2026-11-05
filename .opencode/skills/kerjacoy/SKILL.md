---
name: kerjacoy
description: Cari kerja lintas bidang, nilai kecocokan lowongan, lacak status lamaran, dan siapkan bahan lamaran (sorotan keahlian + draf cover letter) dengan CLI `loker`. Use when the user wants to find jobs, score job matches, track applications, or prepare application materials — any field, including Indonesian job boards (Indeed Indonesia, LinkedIn Indonesia). Bukan untuk melamar otomatis: pengiriman lamaran selalu butuh persetujuan eksplisit pengguna per lowongan.
license: MIT
compatibility: opencode
---

# Kerjacoy: cari kerja + administrasi lamaran

Kamu mengoperasikan CLI `loker` dari repo ini. Semua data kerja (hasil
pencarian, skor, status lamaran) tinggal di file CSV + laporan Markdown,
jadi seluruh riwayat bisa dilacak dan diaudit.

## Cara menjalankan CLI

Cek dulu apakah `loker` terpasang:

```bash
which loker || ls loker_plus/
```

- Bila `loker` ada di PATH, pakai `loker ...`.
- Bila tidak, jalankan dari root repo dengan
  `./venv/bin/python -m loker_plus ...` (atau `python -m loker_plus ...`
  bila venv aktif).

Jangan menginstal ulang dependensi tanpa diminta.

## Perintah (lihat README.md bila ragu)

| Perintah | Fungsi |
|---|---|
| `loker cari --keyword "..." --lokasi Indonesia --preset indonesia --profil profil/<nama>.yaml --keluaran hasil/<nama>.csv` | Cari lowongan, skor, simpan CSV + laporan MD |
| `loker nilai --masukan hasil/<nama>.csv --profil profil/<nama>.yaml` | Skor ulang CSV dengan profil lain |
| `loker tambah --masukan hasil/<nama>.csv --url <URL> --judul <judul> [--perusahaan ...] [--deskripsi ...]` | Tambah lowongan manual (mis. JobStreet/Glints) |
| `loker tandai --masukan hasil/<nama>.csv --url <URL> --status <status>` | Ubah status: baru / dilihat / dilamar / wawancara / ditolak / diterima |
| `loker tailor --masukan hasil/<nama>.csv --url <URL> --profil profil/<nama>.yaml` | Bahan lamaran untuk satu lowongan |
| `loker laporan --masukan hasil/<nama>.csv` | Buat ulang laporan MD dari CSV |
| `loker cek-llm` | Tes koneksi ke endpoint LLM yang dikonfigurasi |

Preset: `indonesia` (Indeed Indonesia + LinkedIn Indonesia),
`global` (Indeed + LinkedIn + ZipRecruiter + Glassdoor).
Profil contoh ada di `profil/`: `contoh-umum.yaml`, `contoh-admin.yaml`,
`contoh-sales.yaml`, `contoh-customer-service.yaml`, `contoh-logistik.yaml`.

## Alur kerja standar

1. **Profil dulu.** Bila belum ada profil yang cocok, buatkan file
   `profil/<nama>.yaml` dari data yang pengguna berikan (nama, keahlian,
   jabatan diinginkan, lokasi diinginkan, pengalaman, ringkasan). Bila data
   kurang, tanyakan dulu — jangan mengarang isi profil.
2. **Cari** dengan `loker cari` (pakai `--preset indonesia` bila lokasinya
   Indonesia). Simpan ke `hasil/<kata-kunci>.csv`.
3. **Lapor** 5–10 teratas dari laporan MD yang otomatis dibuat, dengan skor
   dan alasan skornya. Bila skor terlihat aneh, cek `alasan_skor` di CSV.
4. **Siapkan bahan lamaran** dengan `loker tailor` hanya untuk lowongan yang
   pengguna pilih.
5. **Lacak** dengan `loker tandai` setiap kali status berubah.

## Melengkapi data lowongan (fokus utama)

Tugas terpentingmu adalah membuat data loker lengkap dan akurat. Setiap
baris CSV harus bisa dipertanggungjawabkan.

Field yang harus lengkap bila tersedia di sumbernya: `title`, `company`,
`location`, `job_url`, `description`, `date_posted`, `status`. Bila sumber
menyebut gaji, deadline, atau tipe kerja (remote/hybrid/onsite), simpan
informasinya di `description` atau sampaikan ke pengguna.

Cara melengkapi:

1. Baca baris CSV-nya dulu — jangan menilai dari ingatan.
2. Bila ada field kosong, periksa `job_url`-nya dan lengkapi dari sumber
   asli. Bila sumbernya tidak bisa dibuka (mis. proteksi bot), catat
   `[PERLU DATA: <field>]` dan lanjutkan — jangan mengarang.
3. Untuk lowongan manual (JobStreet/Glints/dll.), minta datanya ke pengguna
   lalu masukkan dengan `loker tambah`.
4. Sebelum melaporkan hasil, baca ulang baris yang relevan di CSV dan
   pastikan yang kamu laporkan sama dengan isi file.

Akurasi di atas kecepatan: lebih baik menulis `[PERLU DATA: gaji]` daripada
menebak angka gaji.

## LLM (opsional)

LLM hanya menambah penilaian kedua (`skor_llm`) dan draf cover letter yang
lebih luwes. Tanpa LLM pun semua perintah jalan penuh.

- Konfigurasi hanya lewat environment variable, tidak pernah ditulis di file:
  `KERJACOY_LLM_API_KEY` (wajib), `KERJACOY_LLM_BASE_URL` (bila bukan
  OpenAI, harus berakhiran `/v1`), `KERJACOY_LLM_MODEL`.
- Bila pengguna minta penilaian/draf LLM, jalankan dulu `loker cek-llm`.
  Bila gagal, sampaikan pesan errornya apa adanya dan lanjutkan dengan mode
  tanpa LLM — jangan mengarang hasil LLM.
- Tambahkan flag `--llm` pada `cari`, `nilai`, dan `tailor` bila LLM sudah
  terkonfigurasi.

## Aturan yang tidak bisa ditawar

1. **Jangan pernah melamar atau mengirim apa pun atas nama pengguna.**
   Menyiapkan bahan lamaran boleh; mengklik kirim / submit tidak boleh,
   kecuali pengguna menyetujui lowongan spesifik itu secara eksplisit.
2. **Jangan mengarang data.** Keahlian, pengalaman, dan skor hanya dari
   profil dan hasil perintah `loker`. Bila data kurang, tulis
   `[PERLU DATA: …]`.
3. **Jangan menulis API key, token, atau URL endpoint berisi kredensial ke
   file apa pun.** Key dan URL hanya lewat environment variable.
4. **Jangan mengubah file di luar `hasil/` dan `profil/`** tanpa diminta.
5. **Klaim selesai harus dibuktikan** dengan output perintah (exit code,
   file CSV/MD yang terbentuk) sebelum dilaporkan ke pengguna.
