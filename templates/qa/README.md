# Templates: Test Case, Bug Report, Regression Analysis

Copy template yang relevan tergantung konteks. Semua field wajib diisi kecuali ditandai `(optional)`.

---

## Template A — Test Case Verification

Dipakai saat: verifikasi tiket sesuai acceptance criteria (post-development).

```markdown
# Test verification — #<WP ID> <subject>

**Tester:** <nama>
**Tester role:** QA Engineer
**Verified at:** <YYYY-MM-DD HH:MM WIB>
**Site + env:** <site>, build `<version/tag/commit>`
**Related ticket:** #<WP ID> — <URL>

## Acceptance criteria (dari tiket)

1. <AC 1 yang ada di tiket>
2. <AC 2>
3. ...

## Preconditions

- **Data seed:** <apa yang harus ada di DB>
- **Config:** <config flag / setting yang harus aktif>
- **Role user:** <test user + role>
- **Deployment status:** <FE build, BE build, migrasi sudah run, dsb.>

## Test scenarios

### Scenario 1: <nama scenario>

**Steps:**
1. Login sebagai `<user>` di `<URL>`.
2. Klik menu `<X>` → submenu `<Y>`.
3. Isi form: field A = `<val>`, field B = `<val>`.
4. Click Submit.

**Expected:**
- UI menampilkan `<X>`.
- DB row `<table>` id=`<id>` field `<col>` = `<val>`.
- API response HTTP 200 dengan body `{...}`.

**Actual:**
- <yang benar-benar terjadi>

**Evidence:**
- Screenshot: `<attach>`
- Log: `<log excerpt>`
- Query verification: `<SELECT ... hasil>`

**Verdict:** PASS / FAIL / BLOCKED / NEED_MORE_INFO

### Scenario 2: <nama>
(sama format)

## Regression retest

Dari §9 KNOWLEDGE.md, module yang berubah = `<X>`. Related module yang di-retest:

- `<module A>` — scenario: <apa yang di-retest> — verdict: PASS/FAIL
- `<module B>` — scenario: — verdict:

## Summary

- Total scenarios: <N>
- PASS: <n>
- FAIL: <n>
- BLOCKED: <n>

**Overall verdict:** PASS / FAIL / PARTIAL

**Next action:**
- [ ] Kalau PASS → transition status ke `Tested Dev (16)` + comment
- [ ] Kalau FAIL → transition status ke `Test failed (11)` + comment + attach evidence
- [ ] Kalau BLOCKED → status `On hold (13)` + escalate
```

---

## Template B — Bug Reproduction Report

Dipakai saat: reproduce + document bug yang di-report user, sebelum ticket QA-nya di-file ke dev.

```markdown
# Bug reproduction — <ringkasan bug>

**Reporter (asal):** <nama user yang report — dari Discord/email/dsb>
**Reported at:** <timestamp original report>
**Reproduced by:** <nama QA>
**Reproduced at:** <YYYY-MM-DD HH:MM WIB>

## Environment

- **Site:** <RS>
- **Build:** <version + branch/tag + commit hash>
- **User role:** <role yang trigger bug>
- **Browser/device:** <bila UI bug — Chrome 120 macOS, Firefox 121 Windows, dsb.>
- **Reproducibility:** Always (5/5) / Sometimes (3/5) / Once (1/5)

## Steps to reproduce

1. Login sebagai `<user>` di `<URL>`.
2. ...
3. ...
4. Trigger error.

## Expected

<sesuai spec / user expectation>

## Actual

<yang terjadi — sertakan URL error, error code, message>

## Evidence

- **Screenshot / video:** <path/URL>
- **Browser console log (bila UI):**
  ```
  <log excerpt>
  ```
- **Server log (bila BE):**
  ```
  <log excerpt dengan timestamp>
  ```
- **Network trace (bila API):**
  ```
  Request: POST /api/v1/xxx
  Body: {...}
  Response: HTTP 500 {...}
  ```
- **DB state (bila data corruption):**
  ```sql
  SELECT ... FROM ... WHERE ...
  -- hasil:
  ```

## Analysis (Suspected)

- **Root cause hypothesis:** <apa yang mungkin bug>
- **Suspected component:** <repo/file/module>
- **Related tickets / historical occurrences:** #X, #Y (dari FAQ KNOWLEDGE.md)

## Impact assessment

- **Severity:** Critical (data loss / prod down) / High (major feature broken) / Medium (workaround exists) / Low (cosmetic)
- **Priority:** P0 (fix now) / P1 (next release) / P2 (backlog) / P3 (nice to have)
- **Users affected:** <RS/role/estimated count>
- **Data at risk:** <table/entity yang terpengaruh>

## Recommendation

- **Immediate action:** <workaround untuk user sementara fix belum ada>
- **Fix suggestion:** <apa yang perlu dev cek/ubah>
- **Regression risk:** <module lain yang bisa terkena bila fix salah>

## Next step

- [ ] File ticket baru di OpenProject → project `kesia`, type `Bug`
- [ ] Assign ke dev yang relevant (berdasarkan `@Tech` yang handle module)
- [ ] Attach reproduction evidence
- [ ] Set severity & priority di ticket
```

---

## Template C — Regression Risk Analysis

Dipakai saat: review perubahan (biasanya code review atau pre-merge) untuk identify area yang perlu regression retest.

```markdown
# Regression risk — #<WP ID> <subject>

**Analyzed by:** <nama>
**Analyzed at:** <timestamp>
**Change scope:** <ringkasan perubahan 1-2 kalimat>

## Files touched

- `<repo>/<file A>` — <apa yang berubah>
- `<repo>/<file B>` — <apa yang berubah>

## Direct affected area (primary)

- **Feature:** <apa fitur utamanya>
- **Modules:** <daftar module inti>

## Indirect affected area (secondary)

Berdasarkan §9 regression checklist:

- **`<module A>`** — alasan: `<shared table X / shared config Y / API dependency Z>` — retest scenario: `<apa>`
- **`<module B>`** — alasan: — retest scenario:
- **`<module C>`** — alasan: — retest scenario:

## Data at risk

- Table `<X>`: <impact>
- Table `<Y>`: <impact>

## Configuration change

- [ ] Ada config baru? → sebutkan
- [ ] Ada migration? → sebutkan versi migration + rollback plan

## Environment matrix (di mana WAJIB retest)

- [ ] Dev EKS `kesia-staging`
- [ ] Staging per RS: `<RS 1>`, `<RS 2>` (kalau site-specific)
- [ ] Multi-tenant test: minimal 2 RS berbeda untuk pastikan tidak break per-tenant config

## Recommended regression test scenarios

Priority tinggi (WAJIB di-test):
1. <scenario A> — related module `<X>`
2. <scenario B> — related module `<Y>`

Priority sedang (bila waktu memungkinkan):
3. <scenario C>

## Sign-off

- [ ] QA sudah lengkapi regression retest sesuai list di atas
- [ ] Regression retest hasil dicomment di tiket via API dengan format Rule 4 (`[QA-PASS]`)
```

---

## Cara Hermes menggunakan template ini

1. Saat user minta "verify tiket X" atau "reproduce bug Y" → cari template yang cocok, isi field sesuai konteks.
2. Kalau field tidak bisa diisi (info missing) → tanya user, jangan asumsi.
3. Output final selalu ikuti struktur template — user (QA lead / dev) sudah familiar sama format ini.
4. Attach file evidence via OUTPUT_DIR kalau ada log/screenshot/CSV yang perlu di-share.
5. Setelah user approve hasil → jalankan next action (mis. transition status tiket via API sesuai Rule 4 di qa_workflow.md).
