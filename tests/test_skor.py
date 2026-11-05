"""Tes unit skor kecocokan (tanpa internet)."""

from loker_plus.skor import skor_lowongan

PROFIL = {
    "keahlian": ["excel", "administrasi"],
    "jabatan_diinginkan": ["staff admin", "admin"],
    "lokasi_diinginkan": ["Jakarta"],
    "kata_hindari": ["magang tanpa gaji"],
}


def test_judul_dan_skill_cocok_skor_tinggi():
    low = {"title": "Staff Admin", "description": "Menguasai excel dan administrasi perkantoran",
           "location": "Jakarta", "date_posted": None}
    skor, alasan = skor_lowongan(low, PROFIL)
    assert skor >= 70
    assert any("judul cocok" in a for a in alasan)
    assert any("keahlian cocok" in a for a in alasan)


def test_tidak_cocok_skor_rendah():
    low = {"title": "Teknisi Las", "description": "Mengelas baja dan membaca gambar teknik",
           "location": "Surabaya", "date_posted": None}
    skor, _ = skor_lowongan(low, PROFIL)
    assert skor < 30


def test_kata_hindari_mengurangi_skor():
    dasar = {"title": "Staff Admin", "description": "Kerja kantoran", "location": "Jakarta",
             "date_posted": None}
    jelek = {"title": "Staff Admin", "description": "Magang tanpa gaji selama 6 bulan",
             "location": "Jakarta", "date_posted": None}
    s1, _ = skor_lowongan(dasar, PROFIL)
    s2, alasan = skor_lowongan(jelek, PROFIL)
    assert s2 < s1
    assert any("kata hindari" in a for a in alasan)


def test_skor_dibatasi_0_sampai_100():
    low = {"title": "Staff Admin", "description": "excel administrasi " * 20,
           "location": "Jakarta", "date_posted": None}
    skor, _ = skor_lowongan(low, PROFIL)
    assert 0 <= skor <= 100


def test_deskripsi_kosong_tidak_error():
    low = {"title": "Admin", "description": None, "location": None, "date_posted": None}
    skor, alasan = skor_lowongan(low, PROFIL)
    assert 0 <= skor <= 100
    assert alasan
