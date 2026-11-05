# Folder skill Kerjacoy

Folder ini sengaja masih kosong. Isi sendiri kapan saja; update Kerjacoy tidak pernah menghapus isinya.
(This folder is intentionally empty. Add your own skills; updates never delete them.)

## Cara menambah skill

1. Buat folder baru di sini, namanya = nama skill (huruf kecil, pakai tanda `-`), misalnya `catatan-rilis/`.
2. Di dalamnya buat file `SKILL.md` seperti ini:

```markdown
---
name: catatan-rilis
description: Menulis catatan rilis dari daftar commit. Pakai saat user minta changelog atau catatan rilis.
---

Langkah:
1. Baca `git log` sejak tag terakhir.
2. Kelompokkan: Fitur, Perbaikan, Lainnya.
3. Tulis singkat dalam bahasa user.
```

- `name` harus sama dengan nama folder.
- `description` menjelaskan kapan skill dipakai — engine membaca ini untuk memutuskan.
3. Buka ulang `kerjacoy`. Skill langsung terdeteksi.

Hasil akhirnya: `skills/catatan-rilis/SKILL.md`.
