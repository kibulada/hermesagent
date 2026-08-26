---
name: bug-repro
description: Reproduksi dan dokumentasikan bug yang dilaporkan user sebelum di-file jadi tiket. Pakai saat ada laporan bug dari Discord/CS/PM yang perlu divalidasi.
---

# Reproduksi bug

## Alur

1. **Kumpulkan konteks** — siapa yang report, kapan, RS mana, role user, build/tag aktif. Kalau ada lampiran (screenshot/video), sebutkan eksplisit bahwa kamu menganalisisnya.
2. **Tentukan environment.** Bug production direproduksi di **staging**, bukan production. Kalau butuh data prod, minta developer copy subset yang sudah disanitasi.
3. **Reproduksi.** Catat langkah persis, expected vs actual. Ulangi untuk menentukan reliabilitas: Always (5/5) / Sometimes (3/5) / Once (1/5).
4. **Kumpulkan bukti** — screenshot, console log, server log dengan timestamp, request/response API, state DB lewat `SELECT` read-only.
5. **Isi Template B** dari `templates/qa/README.md` → `reports/bug-<slug>.md`.
6. **Delegasikan risiko regresi** ke subagent `qa-analyst` bila sudah ada dugaan komponen.

## Aturan

- **Tidak bisa direproduksi ≠ bukan bug.** Laporkan apa adanya: langkah yang dicoba, environment, dan info tambahan yang dibutuhkan dari reporter.
- **Pisahkan Observed dari Suspected.** Root cause adalah hipotesis sampai terbukti di kode.
- **Nol write op** untuk reproduksi. Kalau bug hanya muncul lewat aksi mutasi, buat rencana dan eskalasi ke `@Tech` — jangan eksekusi sendiri di production.
- **Nol PII.** Mask nama pasien, NIK, alamat, no HP, diagnosa. Pakai `patient_id=12345`.
- **Severity dan priority dipisah.** Severity = seberapa parah rusaknya. Priority = seberapa cepat harus diperbaiki. Sertakan jumlah user terdampak dan data yang berisiko.

## Untuk pengguna non-teknis (PM/BA/CS)

Kalau yang bertanya bukan `@Tech`: jangan tampilkan kode, SQL, atau commit hash. Pakai "sistem", "layanan", "data". Jangan pernah menyetujui permintaan perubahan data — eskalasi ke `@Tech`.
