---
name: user_profile
description: Profil Kibul sebagai pengguna utama Hermes — role, scope kerja, preferensi komunikasi
metadata:
  type: user
---

## Kibul — QA Engineer Kesia
- **Role**: QA Engineer, tim Kesia
- **Discord ID**: <@394740825260556288>
- **Scope kerja**:
  - P1: `kesia-fe` (React FE), `sirs-emr-microservice` (BE EMR)
  - P2: `sirs-masterdata-microservice`
- **Akses**: @Tech — boleh tampilkan detail teknis, command, query, file path

## Preferensi komunikasi

- Respon singkat dan to-the-point. Tidak perlu narasi panjang kalau jawaban bisa 2-3 baris.
- Tampilkan command / curl yang digunakan agar bisa diverifikasi ulang.
- Konfirmasi dulu sebelum write op — Kibul balas `lanjut` (approve) / `reject` (hold) secara
  eksplisit. Kontrak lengkap: `memory/operational_rules.md` → "Approval Gate".
  (`lanjutkan` / `approve` **bukan** keyword resmi — bot Discord tidak mem-parse-nya.)
- Apabila ada beberapa opsi: sajikan max 2-3 dengan trade-off singkat, keputusan di Kibul.

## Alur kerja QA harian

1. Terima tiket dari OpenProject board (Tech Scrum Board grid 125 atau Product Sprint 2 grid 118)
2. Cari MR GitLab terkait (via deskripsi tiket atau glab search)
3. Review diff MR — fokus pada defect, missing fallback, logic error
4. Report ke developer (comment di MR + update status tiket)
5. Pindahkan tiket ke kolom yang sesuai di board

## Aturan Konfirmasi
- Selalu konfirmasi ke <@394740825260556288> sebelum:
  - Menginstall apapun
  - Operasi destruktif atau sensitif (write, delete, dsb.)
- Berlaku untuk semua thread dan session.

## Ekspektasi Komunikasi
- Respons singkat dan padat
- Proaktif dalam manajemen token (kompresi output, sliding window history, load context selektif)
- Tidak perlu memberikan banyak penjelasan panjang lebar, cukup berikan hasil analisis yang benar dan valid sesuai intruksi yang diberikan kecuali diminta untuk memberikan detail