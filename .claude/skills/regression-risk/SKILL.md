---
name: regression-risk
description: Tentukan area mana yang wajib di-retest akibat sebuah perubahan kode. Pakai sebelum merge, sebelum transisi ke Tested, atau saat menentukan cakupan regression suite.
---

# Analisa risiko regresi

Argumen: nomor MR, nomor tiket, atau daftar file yang berubah.

Delegasikan ke subagent `qa-analyst`, lalu keluarkan **Template C** dari `templates/qa/README.md`.

## Yang harus ada di hasil

1. **Files touched** — path + ringkasan apa yang berubah.
2. **Direct affected area** — fitur dan modul inti.
3. **Indirect affected area** — dari `knowledge/regression_map.yaml` (fallback `knowledge/qa_standards.md` §9). Tiap entri wajib menyebut **alasan** keterkaitan: shared table, shared config, atau dependency API.
4. **Data at risk** — tabel yang terpengaruh.
5. **Config / migrasi** — ada migrasi baru? ada rencana rollback?
6. **Environment matrix** — di mana wajib retest. Untuk perubahan yang site-specific, uji minimal 2 RS berbeda supaya config per-tenant tidak jebol.
7. **Skenario retest** dipisah prioritas tinggi (wajib) dan sedang (bila waktu memungkinkan).

## Aturan

- Keterkaitan tanpa alasan konkret adalah tebakan — tandai begitu.
- Jangan salin seluruh tabel §9. Ambil hanya yang benar-benar tersentuh perubahan ini.
- Kalau perubahan menyentuh modul yang belum ada di peta regresi, **tambahkan entri baru** ke `knowledge/regression_map.yaml` — peta itu memang dimaksudkan tumbuh.
