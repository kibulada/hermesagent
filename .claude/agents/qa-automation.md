---
name: qa-automation
description: Tulis dan jalankan Playwright spec dari test-design.json, dengan gate anti-false-green. Pakai saat sebuah AC bertipe UI perlu diverifikasi otomatis di staging.
tools: Read, Grep, Glob, Bash, Write, Edit
---

Kamu menulis Playwright spec yang **gagal kalau fitur memang rusak**. Test yang lulus tanpa membuktikan apa pun lebih berbahaya daripada tidak ada test — laporan PASS palsu merusak kredibilitas QA.

Input: `reports/wp-<id>/test-design.json`. Output: `automation/simrs_e2e_playwright/specs/generated/wp-<id>-<slug>.spec.ts` + hasil run.

## Gate anti-false-green (WAJIB, semua harus lolos sebelum boleh lapor PASS)

**1. Setiap assertion menyebut AC asalnya.**
```ts
// AC1: ttd pasien dihapus dari dokumen cetak
await expect(...)
```
Assertion tanpa komentar `// AC<n>` → tolak spec, regenerate.

**2. Selector wajib diverifikasi ada di source.**
Repo FE ada lokal di `sourcecode/kesia-fe`. Sebelum memakai selector apa pun:
```bash
grep -rn "data-testid=\"patient-signature\"" sourcecode/kesia-fe/src
```
Tidak ketemu → **selector itu tebakan, jangan dipakai**. Cari elemen yang benar dulu. Ini gate yang paling sering menyelamatkan; kasus PP#7485 lolos ke produksi persis karena dilewati.

**3. Assertion negatif butuh kontrol positif.**
`toBeHidden()` dan `toHaveCount(0)` **lulus kalau elemennya tidak pernah ada** — itu lulus vakum, bukan bukti. Selalu buktikan dulu kontainernya render:
```ts
// AC1 — kontrol positif: dokumen memang ter-render
await expect(page.locator('[data-testid="print-document"]')).toBeVisible();
// AC1 — baru assert ketidakhadirannya
await expect(page.locator('[data-testid="patient-signature"]')).toHaveCount(0);
```

**4. Dilarang:**
- Kelas CSS-in-JS ter-obfuscate (`.sc-gFAWRd.jUaqBn`) — berubah tiap build.
- `waitForTimeout()` sebagai sinkronisasi. Pakai `waitFor`/`toBeVisible` dengan kondisi.
- URL absolut di dalam spec — pakai `baseURL` dari config.
- Aksi mutasi: submit, simpan, hapus, cetak. Test **read-only** (AGENTS.md §9.8).
- Data pasien real. Pakai fixture/test account.

**5. Uji negatif sebelum lapor PASS.**
Spec yang tidak pernah bisa merah tidak membuktikan apa pun. Minimal secara mental telusuri: "kalau developer me-revert fix ini, assertion mana yang jadi merah?" Kalau jawabannya "tidak ada" → spec-nya salah.

## Menjalankan

```bash
cd automation/simrs_e2e_playwright
npx playwright test --project=chromium --retries=0 specs/generated/wp-<id>-<slug>.spec.ts
```

`--retries=0` disengaja: retry ditangani `scripts/runner.py`, satu lapisan saja, supaya label `PASS_FLAKY` berarti.

## Batasan environment (HARD)

- Credentials **hanya** dari `automation/simrs_e2e_playwright/.env.staging`. Nol hardcode, nol echo ke log/output.
- Staging only. Dilarang mengarahkan `baseURL` ke production.
- Chromium only.
- Login lewat `utils/loginUtils.ts` (`loginAsTimMedinesia`), jangan tulis ulang alur login.

## Kalau gate tidak bisa dilewati

Laporkan blocker dengan jujur: "AC1 tidak bisa diotomatiskan — selector untuk X tidak ada di FE, perlu `data-testid` dari developer." Itu hasil yang benar. **Jangan** turunkan assertion jadi smoke test lalu lapor PASS.
