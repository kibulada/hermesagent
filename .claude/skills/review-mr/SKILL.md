---
name: review-mr
description: Code review satu merge request GitLab dari sudut pandang QA — defect, missing fallback, logic error, dan risiko regresi. Pakai saat diminta "review MR X" atau "cek diff tiket Y".
---

# Code review MR

Argumen: nomor MR, atau nomor tiket (cari MR-nya dari deskripsi tiket / `glab mr list`).

## Alur

1. Ambil diff — MCP `gitlab` (`get_merge_request_changes`) atau `glab mr diff <id>`.
2. Pastikan branch target benar sesuai alur `develop` → `staging` → `master` → `production`.
3. Review tiap file yang berubah.
4. Delegasikan analisa dampak ke subagent `qa-analyst` → daftar modul yang wajib di-retest.

## Yang dicari (urutan prioritas)

1. **Logic error** — kondisi terbalik, off-by-one, early return yang salah.
2. **Missing fallback** — kolom tabel FE wajib `?.` diikuti `?? '-'`. Ini konvensi tim, bukan preferensi.
3. **Edge case tak tertutup** — data kosong, list kosong, role tanpa akses, nilai null dari BE.
4. **Race condition** — terutama sequence/nomor register (ada riwayat duplikat `register_no` di `emr_episodes`).
5. **Kebocoran PII** ke log atau response.
6. **Migrasi tanpa rencana rollback.**
7. **Perubahan yang tidak diminta AC** — scope creep juga temuan.

## Format keluaran

```
**Tiket**: #XXXX — [judul]
**MR**: !YYYY (branch → target)
**Reviewer**: Salsabila QA
---
**Temuan:**
1. [✅/⚠️/❌] — [deskripsi singkat]
   File: `path/to/file.js:baris`
---
**Verdict**: LULUS / PERLU PERBAIKAN / BLOCKER
**Regression retest**: [modul dari qa-analyst]
**Catatan**: [ringkasan untuk developer]
```

Sebut `file:baris` untuk tiap temuan. Temuan tanpa lokasi tidak bisa ditindaklanjuti.
