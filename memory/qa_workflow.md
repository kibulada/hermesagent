# QA Workflow & Mindset

Ini adalah panduan cara berpikir dan pola kerja standar untuk QA Engineer di Kesia.

## Rule 1 — Verification-first, never assume

**Why:** Laporan QA yang salah memicu re-work yang tidak perlu.
**How:** Sebelum menyatakan PASS/FAIL:
1.  Baca acceptance criteria/detail requirements di tiket OpenProject.
2.  Verifikasi environment (build, branch, commit hash).
3.  Reproduksi langkah sesuai spesifikasi, catat expected vs actual.
4.  Jika ada celah antara spesifikasi dan implementasi, **TANYA**, jangan berasumsi.

## Rule 2 — Pisahkan Fact vs Claim

**Why:** Membantu developer fokus pada bukti yang bisa diverifikasi.
**How:**
-   **Fact**: Hasil query DB, log, screenshot, response API.
-   **Claim**: Hipotesis root cause, dugaan modul yang bermasalah.
-   **Format**: Gunakan section "Observed" untuk fakta, "Suspected" untuk klaim.

## Rule 3 — Convention Comment Ticket

**Why:** Komentar di tiket adalah audit trail permanen yang harus konsisten.
**How:** Setiap kali transisi status via API, WAJIB tambah komentar dengan format:

### Untuk PASS (Tested Dev / Tested Staging):
```
[QA-PASS] Verified by <nama QA> pada <YYYY-MM-DD HH:MM WIB>.
Environment: <site> — build <version/tag/commit>
Test scope:
- <scenario 1>: PASS
Regression retest:
- <module A>: PASS (no regression observed)
Notes: <catatan bila ada>
```

### Untuk FAIL (Test failed):
```
[QA-FAIL] Failed by <nama QA> pada <YYYY-MM-DD HH:MM WIB>.
Environment: <site> — build <version/tag/commit>
Reproduction steps:
1. ...
Expected: <...>
Actual: <...>
Evidence:
- Log: <log excerpt>
Severity: <Critical/High/Medium/Low>
Recommendation: <apa yang perlu di-fix>
```

## Rule 4 — Idempotency Check

**Why:** Menghindari eksekusi ganda saat beberapa QA bekerja bersamaan.
**How:** Sebelum `PATCH` status tiket:
1.  `GET` status tiket saat ini.
2.  Jika status sudah sesuai target, **SKIP** dan beri notifikasi "sudah di target, no-op".
3.  Jika belum, lanjutkan dengan konfirmasi.

## Rule 5 — Eskalasi Jika Ter-block

**Why:** Blocker (environment down, data kurang) harus dieskalasi cepat.
**How:**
1.  Set status tiket ke `On hold (13)` dan beri komentar alasan.
2.  Beri tahu di channel yang sesuai (mis. `#qa-blocker`) dan tag orang yang relevan.

## Rule 6 — Jalankan Regression Checklist

**Why:** Perubahan di satu modul sering kali berdampak pada modul lain.
**How:** Sebelum transisi ke `Tested`:
1.  Baca `knowledge/qa_standards.md` bagian checklist regresi.
2.  Identifikasi modul yang berubah dan modul terkait.
3.  Uji ulang minimal 1 skenario per modul terkait.
4.  Laporkan hasilnya di komentar tiket.
