# OpenProject API Reference for QA

Dokumen ini menjelaskan cara interaksi dengan OpenProject API di **https://tracker.kesia.id**.

**Autentikasi ditangani secara berbeda untuk operasi BACA dan TULIS.**

## Operasi BACA (READ) - Gunakan Tool Bawaan

Gunakan tool `openproject` yang tersedia untuk semua operasi baca. Ini lebih aman dan mudah.
Contoh: `openproject.get_work_package(id=7449)`

Daftar endpoint di bawah ini hanya sebagai referensi teknis.

-   `GET /api/v3/users/me`
-   `GET /api/v3/statuses`
-   `GET /api/v3/work_packages/{id}`
-   `GET /api/v3/work_packages/{id}/activities`
-   `GET /api/v3/grids/{id}`
-   `GET /api/v3/queries/{id}/order`

## Operasi TULIS (WRITE) - Gunakan `curl` Manual

Tool `openproject` bersifat read-only. Untuk mengubah data, gunakan `curl` manual dengan token dari file.

-   **Lokasi Token**: `D:\Hermes-QA\secrets\openproject.token`
-   **Keamanan**: **JANGAN** pernah menampilkan token mentah di output.

### 1. Transisi Status Tiket
Gunakan `PATCH /api/v3/work_packages/{id}`.

```bash
# Step 1: Dapatkan lockVersion (gunakan tool read)
# lock_version = openproject.get_work_package(id=7449).lockVersion

# Step 2: PATCH status dengan curl
TOKEN=$(cat D:\Hermes-QA\secrets\openproject.token)
curl -X PATCH -H "Content-Type: application/json" -u "apikey:$TOKEN" \
  -d "{\"lockVersion\": <lock_version>, \"_links\": {\"status\": {\"href\": \"/api/v3/statuses/16\"}}}" \
  "https://tracker.kesia.id/api/v3/work_packages/7449"
```

### 2. Tambah Komentar
Gunakan `POST /api/v3/work_packages/{id}/activities`.

```bash
TOKEN=$(cat D:\Hermes-QA\secrets\openproject.token)
curl -X POST -H "Content-Type: application/json" -u "apikey:$TOKEN" \
  -d '{"comment": {"raw": "Verified pass di dev. Test steps: ..."}}' \
  "https://tracker.kesia.id/api/v3/work_packages/7449/activities"
```

### 3. Pindah Tiket Antar Kolom
Operasi dua langkah: hapus dari kolom asal, lalu tambahkan ke kolom tujuan.

```bash
TOKEN=$(cat D:\Hermes-QA\secrets\openproject.token)

# 1. Hapus dari kolom asal (query_id_A)
curl -X PATCH -H "Content-Type: application/json" -u "apikey:$TOKEN" \
  -d '{"delta": {"7449": -1}}' \
  "https://tracker.kesia.id/api/v3/queries/{query_id_A}/order"

# 2. Tambah ke kolom tujuan (query_id_B)
curl -X PATCH -H "Content-Type: application/json" -u "apikey:$TOKEN" \
  -d '{"delta": {"7449": -819632}}' \
  "https://tracker.kesia.id/api/v3/queries/{query_id_B}/order"
```
- **Internal Reference**: Logika server untuk operasi ini ada di `/app/lib/api/v3/queries/order/query_order_api.rb` di codebase OpenProject.

## Status ID Mapping (Penting untuk QA)
| ID | Nama | Keterangan |
|----|------|------------|
| 8 | Developed | Dev selesai, siap diuji QA |
| 11 | Test failed | QA menolak, kembali ke Dev |
| **16** | **Tested Dev** | **Lulus uji di environment Dev** |
| **17** | **Tested Staging**| **Lulus uji di environment Staging** |
| **18** | **Intesting Dev**| **Sedang diuji di Dev** |
| **19** | **Intesting Staging**| **Sedang diuji di Staging** |
| 20 | Released | Sudah dirilis ke produksi |
| ~~12~~ | Closed | **BUKAN wewenang QA** — jangan dipakai sebagai target transisi |
| ~~14~~ | Rejected | **BUKAN wewenang QA** — jangan dipakai sebagai target transisi |

> Whitelist status yang boleh dipakai jalur QA otomatis: **11, 13, 16, 17**.
> Ditegakkan di kode oleh `ALLOWED_STATUS_IDS` di `automation/simrs_e2e_playwright/scripts/discord_bot.py`.

## Board 125 — Tech Scrum Board New
| Kolom | Query ID |
|---|---|
| To Do | 516 |
| Inprogress | 517 |
| Done Dev | 518 |
| **In QA Dev** | 519 |
| **Tested Dev** | 520 |
| Staging | 521 |
| **In QA Staging**| 522 |
| **Done Staging** | 523 |
| Release FE | 526 |
| Release BE | 527 |
| Closed | 528 |

**Alur Kerja QA di Board:**
1.  Dev memindahkan tiket ke `Done Dev` (status `Developed`).
2.  QA memindahkan tiket ke `In QA Dev` (status `Intesting Dev`).
3.  Jika lulus, QA pindah ke `Tested Dev` (status `Tested Dev`).
4.  Jika gagal, status diubah ke `Test failed (11)` dan diberi komentar.
5.  Siklus yang sama berulang untuk Staging.
