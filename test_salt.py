"""Retest S-02: hash tanpa salt dapat ditebak, hash bersalt tidak.

Jalankan dari folder utama proyek (utsproject):
    python test_salt.py
"""
import itertools
import secrets

from app import hash_credential, get_credential_data

TARGET_NAMES = ["Budi Santoso", "Siti Aminah", "Aida Nurfadilah", "Rizky Pratama"]
NPM_PREFIX = "2370060"          # penyerang tahu format NPM kampus
GRAD_YEAR = "2026"
INSTITUTION = "Universitas Siliwangi"
CRED_TYPE = "Ijazah"


def make_record(name, npm, with_salt):
    credential = {
        "credential_id": "CRD-" + secrets.token_hex(4).upper(),
        "student_name": name,
        "student_id": npm,
        "credential_type": CRED_TYPE,
        "institution": INSTITUTION,
        "graduation_year": GRAD_YEAR,
    }
    if with_salt:
        credential["salt"] = secrets.token_hex(32)
    return credential


def brute_force(credential_id, target_hash, salt=None):
    """Penyerang tahu credential_id (publik di event) dan target_hash (publik
    di chain). Ia menebak nama + NPM. Salt tidak diketahui penyerang."""
    attempts = 0
    for name, suffix in itertools.product(TARGET_NAMES, range(0, 100)):
        attempts += 1
        guess = {
            "credential_id": credential_id,
            "student_name": name,
            "student_id": f"{NPM_PREFIX}{suffix:02d}",
            "credential_type": CRED_TYPE,
            "institution": INSTITUTION,
            "graduation_year": GRAD_YEAR,
        }
        if hash_credential(guess) == target_hash:
            return guess, attempts
    return None, attempts


def main():
    # Kasus 1: tanpa salt (perilaku lama) -> harus ditemukan
    old = make_record("Aida Nurfadilah", "237006076", with_salt=False)
    old_hash = hash_credential(get_credential_data(old))
    found, n = brute_force(old["credential_id"], old_hash)
    print(f"[tanpa salt] ditemukan={found is not None} dalam {n} percobaan")
    assert found is not None

    # Kasus 2: bersalt (perilaku baru) -> tidak boleh ditemukan
    new = make_record("Aida Nurfadilah", "237006076", with_salt=True)
    new_hash = hash_credential(get_credential_data(new))
    found, n = brute_force(new["credential_id"], new_hash)
    print(f"[bersalt]    ditemukan={found is not None} dalam {n} percobaan")
    assert found is None

    # Kasus 3: dua penerbitan data identik menghasilkan hash berbeda
    a = make_record("Aida Nurfadilah", "237006076", with_salt=True)
    b = dict(a, salt=secrets.token_hex(32))
    assert hash_credential(get_credential_data(a)) != hash_credential(get_credential_data(b))
    print("[bersalt]    salt berbeda -> hash berbeda: OK")

    # Kasus 4: verifikasi ulang memakai salt tersimpan -> hash sama
    assert hash_credential(get_credential_data(new)) == new_hash
    print("[bersalt]    verifikasi ulang dengan salt tersimpan: OK")

    # Kasus 5: kredensial lama tanpa salt tetap dapat diverifikasi
    assert "salt" not in get_credential_data(old)
    assert hash_credential(get_credential_data(old)) == old_hash
    print("[kompatibel] kredensial lama tanpa salt tetap valid: OK")

    print("SEMUA UJI SALT LULUS (5/5)")


if __name__ == "__main__":
    main()
