"""Tes unit tailor CV: tidak boleh mengarang pengalaman."""

from loker_plus.cv import tailor

PROFIL = {
    "nama": "Budi",
    "ringkasan": "Lulusan administrasi dengan pengalaman data entry.",
    "keahlian": ["excel", "data entry", "administrasi"],
    "jabatan_diinginkan": ["staff admin"],
    "lokasi_diinginkan": ["Jakarta"],
    "kata_hindari": [],
    "pengalaman": [
        "Staff data entry di PT Maju (2023-2024): menginput 500+ dokumen per minggu dengan excel.",
        "Asisten toko di Toko Berkah (2022): melayani pelanggan dan mengelola stok.",
    ],
}


def test_hanya_pengalaman_profil_yang_ditampilkan():
    low = {"title": "Staff Admin", "company": "PT ABC",
           "description": "Dibutuhkan yang menguasai excel dan data entry."}
    hasil = tailor(low, PROFIL)
    assert "excel" in hasil["keahlian_cocok"]
    # Semua pengalaman relevan HARUS berasal dari profil, bukan karangan
    for p in hasil["pengalaman_relevan"]:
        assert p in PROFIL["pengalaman"]
    assert hasil["pengalaman_relevan"]  # ada yang relevan


def test_cover_letter_memakai_data_profil():
    low = {"title": "Staff Admin", "company": "PT ABC", "description": "excel"}
    hasil = tailor(low, PROFIL)
    assert "Budi" in hasil["draf_cover_letter"]
    assert "PT ABC" in hasil["draf_cover_letter"]
    assert "Staff Admin" in hasil["draf_cover_letter"]


def test_tanpa_kecocokan_tetap_aman():
    low = {"title": "Koki", "company": "Resto X", "description": "Memasak masakan Padang"}
    hasil = tailor(low, PROFIL)
    assert hasil["keahlian_cocok"] == []
    assert hasil["pengalaman_relevan"]  # fallback: pengalaman pertama
    for p in hasil["pengalaman_relevan"]:
        assert p in PROFIL["pengalaman"]
