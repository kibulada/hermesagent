---
name: qa-report
description: Rekap kualitas QA — pass rate, flake rate, defect per modul, reopen rate, dan desync board vs kode. Pakai saat butuh laporan sprint atau evaluasi berkala.
---

# Laporan & evaluasi QA

Argumen opsional: rentang tanggal atau nama sprint. Default: 14 hari terakhir.

Delegasikan perhitungan ke subagent `qa-analyst`.

## Isi laporan

1. **Ringkasan eksekusi** — jumlah tiket diverifikasi, PASS / PASS_FLAKY / FAIL / BLOCKED.
2. **Flake rate per spec** dari `reports/history.jsonl`. Tandai spec dengan flake rate > 20% dalam 10 run terakhir.
3. **Defect per modul** — jumlah + severity, dari laporan di `reports/`.
4. **Reopen rate** — tiket yang balik dari `Tested Dev` ke `Test failed`. Ini indikator kualitas review, bukan kualitas developer.
5. **Desync board vs kode** — jalankan `parse_sync.py`: tiket yang kodenya sudah merged tapi statusnya basi.
6. **Cakupan** — AC yang berstatus `NOT_VERIFIED` karena gate anti-false-green tidak lolos. Ini utang QA yang harus terlihat, jangan disembunyikan.

## Aturan

- **Jangan pernah menghitung persentase dari sampel kurang dari 5.** Tulis "data belum cukup".
- **Sebutkan apa yang tidak tercakup.** Laporan yang diam soal celah terbaca seolah semua tercakup.
- **Setiap angka diikuti aksi.** Metrik tanpa rekomendasi tidak berguna.
- Nol PII di seluruh agregat dan contoh.
