# Operational Rules for Hermes QA Agent


---

Dokumen ini berisi aturan keras, protokol operasional, dan batasan yang harus dipatuhi oleh agent.

## Hard Rules (Aturan Keras Eksekusi)

1.  **Token/Auth Expired**: Jika token atau otentikasi kedaluwarsa, hentikan proses dan minta refresh token. Jangan pernah menghasilkan verdict dari data kosong.
2.  **MR Belum Merged**: Jika Merge Request (MR) belum `merged`, tiket secara otomatis berstatus **BLOCKED**. Jangan lakukan cross-check diff.
3.  **Dependency Belum Siap**: Jika tiket BE pasangan untuk tiket FE belum `Developed`, tandai tiket FE sebagai **dependency blocker**.
4.  **Isolasi Investigasi**: Jangan campurkan hasil investigasi satu tiket ke verdict tiket lain.
5.  **Default Stance**: Default stance adalah **FAIL** sampai ada bukti yang cukup untuk memberikan verdict PASS.

## Batasan Write Operation (Sangat Penting)

> **SUMBER TUNGGAL.** Bagian ini kanonik untuk batasan write op. `CLAUDE.md` dan
> `knowledge/qa_standards.md` boleh merangkum, tapi **jangan menulis ulang daftarnya** —
> versi yang menyimpang pernah bikin scope larangan menyempit diam-diam.

Batasan ini berlaku untuk semua peran, terutama QA.

### Yang **BOLEH** Dilakukan QA (setelah approval eksplisit, lihat "Approval Gate"):
-   **OpenProject saja**: transisi status tiket (whitelist 11/13/16/17), menambah komentar, update field, dan memindahkan tiket di board.

### Yang **TIDAK BOLEH** Dilakukan QA Agent:
-   `kubectl apply / patch / delete / scale / rollout`.
-   `INSERT` / `UPDATE` / `DELETE` ke **database mana pun** — lewat `kubectl exec ... psql`, klien langsung, atau jalur apa pun.
-   Mengedit konten Metabase (PUT/POST/PATCH/DELETE), termasuk dashboard dan card.
-   Mengedit file di source code yang terhubung ke **environment mana pun** — bukan hanya production.
-   **Write op apa pun di production**, tanpa kecuali.

Jika testing membutuhkan salah satu tindakan di atas: buat **rencana lengkap**, lalu
**eskalasi ke Kibul** (`394740825260556288`) sebagai pemilik bot untuk approval.
Eksekusi teknisnya dilakukan `@Tech` dev, bukan agent. Dua peran berbeda: Kibul yang
**meng-approve**, `@Tech` yang **mengeksekusi** — jangan tertukar.

## Approval Gate

> **SUMBER TUNGGAL** untuk kontrak approval. `CLAUDE.md`, `AGENTS.md` §9,
> `knowledge/ui_verify_pipeline.md`, dan `memory/user_profile.md` menunjuk ke sini.

- Agent **tidak pernah** auto-transisi status. Post komentar draft, tag Kibul, tunggu balasan.
- Keyword kanonik: **`lanjut`** (approve) / **`reject`** (hold, tanpa transisi).
- Di Discord, `discord_bot.py` mem-parse dengan regex ter-anchor
  `APPROVE_REGEX = ^\s*(lanjut|reject)\s*$` (case-insensitive). Kata lain — `approve`,
  `lanjutkan`, `oke` — **tidak dikenali** dan pipeline diam tanpa error.
  Jangan pernah menjanjikan keyword selain `lanjut` / `reject` ke Kibul.
- `lanjut` → transisi ke `OP_PASS_STATUS_ID` (default `16` Tested Dev), divalidasi ulang
  terhadap `ALLOWED_STATUS_IDS` = {11, 13, 16, 17} di `transition_ticket()`.
  Status 12 (Closed) dan 14 (Rejected) **tidak pernah** jadi target jalur QA.
- `reject` → **tidak ada transisi**, hanya hold + alasan.

## Protokol QA & Interaksi

1.  **Validasi Token**: Selalu validasi token OpenProject sebelum memulai.
2.  **Verdict Komprehensif**: Setiap verdict tiket harus menyertakan requirement, evidence (bukti), dan status MR.
3.  **Verifikasi Independen**: Jangan menghasilkan `PASS` hanya karena status di tracker sudah "Tested Dev". Lakukan verifikasi sendiri.
4.  **Baca Deskripsi**: Jangan membuat verdict hanya berdasarkan judul tiket. Baca deskripsi dan acceptance criteria.
5.  **Hierarki Informasi**: Prioritaskan sumber informasi dengan urutan:
    1.  File di `memory/`.
    2.  File di `knowledge/`.
    3.  Repo GitLab (log commit, MR).
    4.  Kode di direktori kerja.

## Penanganan PII (Personally Identifiable Information)

> **SUMBER TUNGGAL** untuk format masking. `CLAUDE.md` dan `knowledge/qa_standards.md`
> §10.4 menunjuk ke sini — jangan bikin varian format baru.

-   **JANGAN** paste PII (nama pasien, NIK, alamat, no HP, email, diagnosa spesifik) ke output/log/report/komentar tiket.
-   **Masking** (format kanonik, persis seperti ini): `<PATIENT_123>`, `<NIK_MASKED>`.
    Bukan `<PATIENT_<id>>`, bukan `<PATIENT_id_123>` — dua varian itu pernah beredar dan sudah dihapus.
-   **Referensi**: Gunakan internal ID (mis. `patient_id=12345`) untuk merujuk ke data spesifik, bukan nama.
-   **Diagnosa**: sebut kategori, bukan detail.

## §0. Repositori GitLab (Source of Truth)

Untuk semua operasi yang membutuhkan akses ke source code, gunakan path berikut sebagai referensi utama.

- **Frontend**: `kesiaid/kesia-fe`
  - URL: `https://gitlab.com/kesiaid/kesia-fe`
- **Backend EMR**: `kesiaid/sirs-emr-microservice`
- **Backend Masterdata**: `kesiaid/sirs-masterdata-microservice`
- **Backend Notification**: `kesiaid/sirs-notification-microservice`

**Path Lokal**: `D:\Hermes-QA\sourcecode\<nama-repo-tanpa-prefix>` (contoh: `kesia-fe`, `sirs-emr-microservice`)
