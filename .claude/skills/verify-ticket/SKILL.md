---
name: verify-ticket
description: Verifikasi satu tiket OpenProject end-to-end — baca AC, susun test design, jalankan automation bila relevan, hasilkan laporan dan draft komentar. Pakai saat diminta "verify tiket X", "cek PP#X", atau "tiket X sudah bisa di-test belum".
---

# Verifikasi tiket

Argumen: nomor work package (mis. `7485`).

## Alur

**1. Ambil tiket.** MCP `openproject` → subject, deskripsi, status, AC, MR terkait.

**2. Gerbang blocker — cek sebelum kerja apa pun:**
- MR belum merged → **BLOCKED**, berhenti, laporkan.
- Tiket BE pasangan belum `Developed` → **dependency blocker**, berhenti.
- 401 dari OpenProject → STOP, minta token baru.

**3. Test design.** Delegasikan ke subagent `qa-requirement` → `reports/wp-<id>/test-design.json`.
Kalau ada AC masuk `untestable`, tanyakan ke Kibul sekarang — jangan ditebak.

**4. Code review MR** (kalau ada MR). Fokus: defect, missing fallback (`?.` + `?? '-'` di kolom tabel FE), logic error, edge case yang tidak tertutup AC.

**5. Automation** — hanya untuk AC bertipe `UI`. Delegasikan ke subagent `qa-automation`.
Gate anti-false-green wajib lolos. Kalau tidak bisa, AC itu berstatus `NOT_VERIFIED`, bukan `PASS`.

**6. Laporan.** Delegasikan ke subagent `qa-reporter` → `reports/wp-<id>/report.md` + draft komentar.

**7. Berhenti dan tunggu approval.** Post draft, tag Kibul. Jangan transisi status sendiri.
- `lanjut` → status 16 (Tested Dev) / 17 (Tested Staging)
- `reject` → tidak ada transisi, hold + alasan

**8. Catat run** ke `reports/history.jsonl` untuk analisa flake rate nanti.

## Aturan

- Default stance **FAIL** sampai bukti cukup.
- 1 tiket = 1 tiket. Jangan campur temuan lintas tiket.
- Nol PII di seluruh output.
- Verdict wajib menyertakan: requirement, evidence, status MR, build yang diuji.
