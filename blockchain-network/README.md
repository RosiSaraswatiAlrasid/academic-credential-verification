# Academic Credential Verification — Smart Contract

Smart contract untuk penerbitan, verifikasi, dan pencabutan kredensial akademik menggunakan Solidity dan Hardhat 3.

## 1. Teknologi

- Solidity
- Hardhat 3
- TypeScript
- Ethers.js
- Mocha dan Chai untuk pengujian
- Flask dan Web3.py untuk integrasi aplikasi

## 2. Struktur Proyek

- `contracts/AcademicCredential.sol` — implementasi smart contract.
- `test/AcademicCredential.ts` — unit test smart contract.
- `deploy.ts` — skrip deployment.
- `hardhat.config.ts` — konfigurasi Hardhat.
- `deployment-record.md` — catatan deployment dan bukti transaksi.

## 3. Persyaratan

- Node.js dan npm.
- Python serta virtual environment untuk aplikasi Flask.
- Hardhat 3 dan dependensi proyek yang terpasang.

## 4. Instalasi

Jalankan perintah berikut dari folder `blockchain-network`:

```bash
npm install
```

## 5. Compile Smart Contract

```bash
npx hardhat compile
```

## 6. Menjalankan Unit Test

```bash
npx hardhat test
```

Pengujian mencakup penerbitan dan verifikasi kredensial, hash tidak valid, ID kosong, hash kosong, ID duplikat, kontrol akses penerbitan dan pencabutan, serta pencabutan kredensial yang tidak ditemukan atau sudah dicabut.

Hasil pengujian yang telah diperoleh: **10 test berhasil dan 0 test gagal**.

## 7. Menjalankan Blockchain Lokal

Buka terminal pertama di folder `blockchain-network`:

```bash
npx hardhat node
```

Biarkan terminal tersebut tetap berjalan.

## 8. Deployment ke Hardhat Localhost

Buka terminal kedua di folder `blockchain-network`:

```bash
npx hardhat run deploy.ts --network localhost
```

Catat alamat kontrak yang ditampilkan setelah deployment berhasil. Alamat kontrak dapat berubah jika jaringan lokal di-reset atau kontrak di-deploy ulang.

## 9. Integrasi dengan Aplikasi Flask

Aplikasi Flask menggunakan Web3.py untuk berinteraksi dengan smart contract pada RPC lokal `http://127.0.0.1:8545`.

Pastikan alamat kontrak pada konfigurasi klien Web3 sesuai dengan deployment aktif. Kunci privat akun pengujian lokal disimpan pada file `.env` di folder utama proyek dan tidak boleh dimasukkan ke repositori.

Jalankan aplikasi Flask dari folder utama proyek menggunakan virtual environment yang telah disiapkan.

## 10. Verifikasi Transaksi

Setelah menerbitkan kredensial dummy melalui aplikasi, gunakan transaction hash untuk mengambil receipt dan memeriksa status transaksi. Event `CredentialIssued` dapat diperiksa dari log receipt menggunakan ABI kontrak.

Detail deployment dan bukti transaksi yang telah dicatat tersedia pada dokumen `deployment-record.md`.

## 11. Batasan Penggunaan

Proyek ini menggunakan jaringan pengembangan lokal untuk keperluan pembelajaran dan pengujian. Proyek ini tidak ditujukan untuk transaksi aset kripto sungguhan atau deployment produksi.

Jangan pernah mengunggah kunci privat, seed phrase, atau rahasia lain ke repositori publik.
