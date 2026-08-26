# FIX FINAL — Billing Baru → Legacy Parity (5 P0)

**Source code state**: develop HEAD @ 2026-08-05 = local snapshot. Semua line number valid.
**Repos**: kesiaid/sirs-emr-microservice, kesiaid/sirs-masterdata-microservice, kesiaid/kesia-fe.

---

## Catatan dari validasi develop

1. `sirs-emr-microservice/dao/BillingDAO.js` develop HEAD = local. Byte-identical (size 38611).
2. `sirs-emr-microservice/helpers/billingCalc.js` develop = local. Size 5366.
3. `sirs-emr-microservice/models/billingDetail.js` develop = local. Size 4361.
4. `sirs-masterdata-microservice/dao/ActionPriceDAO.js` develop = local. Size 28961.
5. `sirs-masterdata-microservice/models/siteManagementCompanyPartner.js` develop = local. Punya `global`, `isCovered`, `isGlobalDiscount`, `globalDiscountValue`, `notCoveredDiscountValue` — **TIDAK ADA** `isFullCover`.
6. `kesia-fe/src/components/billing/AllComponents.js` develop = local. Size 128884.

Sheet `FINAL-bug-fix-billing-parity.xlsx` valid line numbers untuk semua referensi lokal. **TAPI** ada 3 pembetulan root cause di bawah.

---

## BUG #1 — Filter medicalSupport

**Root cause**: BENAR. `BillingDAO.js:626-634` memproses semua `ar.unit === 'MEDICAL SUPPORT'` tanpa cek status. Filter harus match FE legacy `getMedicalSupportActionBilling` di `AllComponents.js:1516-1541`.

**Sheet fix**: Struktur benar (helper `isMedSupBillable`, payer-type mapping mirror FE).

**Pembetulan Salsabila terhadap sheet**:
- **ORDER list status**: Sheet hardcoded `['waitlist','processing','sampling','verified','finished']` — ini **ENUM BE**, BUKAN FE. FE pakai `['waitlist','examined','expertise','sampling']`. Sebelum commit: `SELECT DISTINCT status FROM medical_supports WHERE deleted_at IS NULL` untuk pakai enum yang valid.
- **PREREQ `parentInfo.companyPartnerCompanyType`**: TIDAK ADA di `getParentDataByRegisterType` (cek L47-180). Tapi `parentData.patientInsurer.companyPartner` sudah di-include dengan attributes `['id', 'companyName']` saja (L62-66). **Ganti** include attributes jadi `['id', 'companyName', 'companyType']`, baca dari `parentData.patientInsurer.companyPartner.companyType`.

---

## BUG #2 — Cover cathLab + insurer full-cover

**Root cause dua-lapis**:
1. `helpers/billingCalc.js:33` hardcoded skip cathLab:
   ```js
   if (!isCathLab && ap?.isCovered) { coverAmount = ... }
   ```
   Untuk `category='cathLab'` → `coverAmount = 0`. Ini valid evidence: INP/00016 cathLab cover=0 di billing, 37jt di invoice.
2. Untuk pasien `siteManagementCompanyPartner.global = true` (umbrella insurer): `ActionPriceDAO.js:600-609` flow sudah benar set `isCovered=true` dan propagate `additionalInfo.global = true`. Tapi EMR `billingCalc.calculatePriceInfo` tidak signal ini — `ap.additionalInfo.global` tidak dipakai.

**Sheet fix**: Tambah param `companyPartnerSite`, cabang `insurerFullCover = !!companyPartnerSite && companyPartnerSite.isFullCover`.

**Pembetulan Salsabila terhadap sheet** ⚠️:
- Field `companyPartnerSite.isFullCover` **TIDAK ADA** di `siteManagementCompanyPartner.js` (cek develop HEAD). Gunakan field yang sudah ada: `companyPartnerSite.global` (sama semantik dengan FE `getPriceCoverDiscount` L93 `if (companyPartnerSite.global || initPrice)`).
- Lebih robust lagi: pakai `ap.additionalInfo.global` dari masterdata (sudah di-set di L609, L621), supaya EMR tidak duplicate logic insurer-coverage.
- **CathLab fix**: ganti `if (!isCathLab && ap?.isCovered)` ke `if (ap.additionalInfo?.companyPartnerId || ap.additionalInfo?.global)`. Untuk cathLab, kalau insurer flag global atau companyPartnerId spesifik → cover.

---

## BUG #3 — computeServiceFee formula

**Root cause**: BENAR. `billingCalc.js:13-20` selisih dari legacy `InvoiceDAO.js:1923-1931`. Lihat perbedaan konkret:
- Baru: `serviceFee = subTotal * admFee / 100`, `Math.round`, hardcoded `isSelfPaid` filter.
- Legacy: `serviceFee = (subTotal - discountAmount) * admFee / 100`, `Math.floor`, capped `admFeeLimit`, no selfPaid filter.

**Sheet fix**: BENAR byte-perfect mirror legacy. `Math.max(0, total)` di `assembleBillingTotals` bantu closing Bug #4 (total negatif).

**Catatan**:
- BREAKING: `isSelfPaid` filter hilang → insurer juga kena serviceFee. Konfirmasi finance sebelum merge.
- PREREQ: `billingCalc.js:106-119` destructuring harus ubah `{ depositAmount, admFee, isSelfPaid }` → `{ depositAmount, admFee, admFeeLimit }`.

---

## BUG #4 — billingDetails paranoid

**Root cause**: BENAR. `models/billingDetail.js:128` `paranoid: false`. `models/invoiceDetail.js:134` `paranoid: true` (inkonsisten).

**Sheet fix**: BENAR. Migration + `paranoid: true` + `force: true` di 3 destroy sites.

**Pembetulan minor**:
- L910, L1180, L1192 — `force: true` WAJIB atau duplicate row + FK violation di re-generate room/action/prescription (setelahnya insert dengan id berbeda, baris lama masih hidup).
- Cek juga: ada `await billing.destroy({ transaction })` di `processMergeToInpatientBilling` L458 — `billing` model juga perlu paranoid check sebelum PR ini merge (di luar scope 5 bug, tapi tandai untuk follow-up).

---

## BUG #5 — getActionPrice companyPartner-specific

**Root cause**: SEBAGIAN BENAR. Tapi sheet lokasi fix SALAH.

**Source code aktual** (`sirs-masterdata-microservice/dao/ActionPriceDAO.js:447-619`):
```js
// Query (L447-485): order by companyPartnerId ASC (Postgres NULLS FIRST by default)
// ActionPriceDAO models has 'companyPartnerId', 'isDiscount', 'discount', 'priceType'
// NO 'isCovered' field — isCovered di-resolve dari companyPartnerId non-null

// Result handler (L592-619):
return this.model.findAll(options).then(async (actionPrice) => {
  if (actionPrice.length > 0) {
    // ... ambil actionPrice[0] unconditionally
    let isCovered = (!!actionPrice[0].companyPartnerId)  // L614
    // kalau [0] = NULL row, isCovered = false
    ...
    return { actionPriceId, margin, cost, price, isCovered, additionalInfo: {...} }
  }
})
```

**Query return**: WHERE `companyPartnerId: [null, <X>]`. Kalau ada baris default (`companyPartnerId=null`) DAN baris `<X>`, query return keduanya. ORDER BY ASC + Postgres `NULLS FIRST` → array `[null_row, X_row]`. Code ambil `[0]` = `null_row` selalu.

**Fix ada 2 pilihan (sheet hanya list option 1):**

**Option A (PILIH INI) — Fix di masterdata ActionPriceDAO** (`sirs-masterdata-microservice/dao/ActionPriceDAO.js`):
```diff
@@ L469 order @@
     order: [
-      ['companyPartnerId'],
+      [sequelize.fn('CASE WHEN ?? IS NULL THEN 1 ELSE 0 END', sequelize.col('companyPartnerId')), 'ASC'],
+      ['companyPartnerId'],
       ['unitId'],
       ['doctorId']
     ],
```

Tambah: kalau `companyPartnerId` ada di param query, cari baris specific dulu; kalau tidak ketemu, fallback NULL row. Atau tambah `LIMIT 1` setelah order dengan `NULLS LAST`.

**Option B — Sheet fix di EMR BillingDAO** (partial, tidak solve masalah sistemik, hanya workaround lokal):
```js
const resolveAp = async (base) => {
  if (base.companyPartnerId) {
    // Coba specific — kalau null, fallback default
    const rows = await Promise.all([
      this.getActionPrice(base),
      this.getActionPrice({ ...base, companyPartnerId: null })
    ])
    const specific = rows[0]
    const fallback = rows[1]
    if (specific) return specific  // tapi TETAP default row kalau [0]=NULL!
    return fallback
  }
  return this.getActionPrice(base)
}
```
⚠️ Bug: `getActionPrice` panggil masterdata yang return ALL rows via `findAll`, tapi `.data.data` cuma ambil element/array — belum jelas return shape. Cek `ActionPriceDAO.findAll` return type — di Result adalah array, `ap?.data?.data` di BillingDAO.js:44 BUKAN single obj kalau ada >1 row.

**Rekomendasi**: Fix di masterdata (Option A). Sheet PR `!XXXX` (MR EMR) tidak cukup — perlu MR terpisah di `sirs-masterdata-microservice`. Sebelum merge, **WAJIB run query**:
```sql
SELECT company_partner_id, price
FROM action_prices
WHERE action_id = '<action_id MCS>'
  AND site_id = '<Tasik site_id>'
  AND is_active = true
  AND deleted_at IS NULL;
```
Kalau row untuk RS PERMATA BUNDA exist → root cause di masterdata query logic. Kalau tidak ada → data masterdata perlu di-input manual.

---

## PR Sequence (update dari sheet)

Sheet `Rollout Plan` urut: paranoid → serviceFee → filter medicalSupport → cover cathLab → getActionPrice.

**Salsabila re-order berdasarkan root cause priority**:
1. **MR_PARITY_MASTERDATA** (NEW, antesed #1-5): Fix ActionPriceDAO order + add LIMIT/case. **BLOCKER** untuk Bug #5. Tanpa ini, fix #5 tidak efektif.
2. **MR_PARITY_4** (paranoid): migration + model + 3 destroy force.
3. **MR_PARITY_3** (computeServiceFee): billingCalc + BillingDAO signatures. Tambah `Math.max(0, total)`.
4. **MR_PARITY_1** (filter medicalSupport): tambah `companyType` di include parentData + helper class.
5. **MR_PARITY_2** (cover cathLab): update `calculatePriceInfo` accept `companyPartnerSite`, ganti `isFullCover` → `global`, fix cathLab skip logic. (Sekarang bisa akurat pakai `ap.additionalInfo.global`).
6. **MR_PARITY_5** (actionPrice resolve): setelah masterdata MR, EMR caller fix handling array.

**Catatan**: urutan di atas PENTING. MR #2, #5 memerlukan output `ap.additionalInfo` dari masterdata — tapi field itu sudah ada (L609, L621). Jadi #2 bisa merge independent dari MR masterdata. #5 TIDAK BISA merge efektif tanpa MR masterdata.

---

## Verdict per-bug (update)

| Bug | Verdict | Reason |
|---|---|---|
| #1 | ✅ SCHET OK dgn catatan | Tambah `companyType` di include attributes, validate status enum via SELECT |
| #2 | ⚠️ PERLU REVISI | Ganti `isFullCover` → `global` di companyPartnerSite (field exist); cathLab fix harus lewat `ap.additionalInfo` signal, bukan recreate logic |
| #3 | ✅ SCHET OK | Mirror legacy byte-perfect. Konfirmasi finance utk BREAKING isSelfPaid |
| #4 | ✅ SCHET OK | Paranoid migration + 3 force destroy |
| #5 | ⚠️ LOKASI FIX SALAH | Root cause di `sirs-masterdata-microservice/dao/ActionPriceDAO.js:469-619`, bukan di EMR. Butuh MR masterdata terpisah |
