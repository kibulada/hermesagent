# Audit Defect & Blocker — Kesia V3 (main `0ffd892`, 18-08-2026)

Repo: `E:\WORK KESIA\Project\kesiaV3` — HEAD `0ffd892` (Odoo 18: Odoo18Adapter + honest-mock gate)
Audit: 4 worker paralel (Clinical Core / Billing-Keuangan / Farmasi-Penunjang / RBAC-Auth-Masterdata)

## Total: 96 defect (4 CRITICAL, 26 HIGH, 42 MEDIUM, 14 LOW + 10 verifikasi)

---

## A. CLINICAL CORE (Pendaftaran → EMR → Discharge) — 40 temuan

### Status defect lama (11)
| # | Defect | Status |
|---|--------|--------|
| 1 | SEP issue() tanpa guard duplikat/closed | **OPEN** (sep.service.ts:91) |
| 2 | respondConsult overwrite non-idempotent | **OPEN** (care-plan.service.ts:177) |
| 3 | recordVisite tanpa guard closed + duplikat | **OPEN** (order.service.ts:231) |
| 4 | deleteVisite hard delete tanpa cek invoice | **OPEN** (order.service.ts:262) |
| 5 | cancelEpisode cascade foodOrders+surgeries | **FIXED** (registration.service.ts:913-938) |
| 6 | RAJAL_ALREADY_OPEN_SAME_UNIT | ADA (registration.service.ts:1042) |
| 7 | NIK bypass TempPatientVerify | **FIXED** server (registration.service.ts:441); sisa gap LOW: FE nik `required:false` |
| 8 | Jadwal dokter hapus tanpa modal | TIDAK RELEVAN — JadwalDokterPage read-only |
| 9 | PatientListPage filter terbatas | **FIXED** (filter nama/RM/NIK/HP/tgl-lahir/alamat/penjamin/perusahaan) |
| 10 | MCU walk-in hasPaidDeposit=true tanpa deposit riil | **OPEN** (registration.service.ts:588) |
| 11 | saveCathlabReport tanpa guard cancelled | **OPEN** (order.service.ts:728) |

### Defect baru Clinical (ringkas)
- **[NEW-01] HIGH** orderInpatient double-click → SPRI ganda — registration.service.ts:665-677 (carePlan insert + admit di tx terpisah)
- **[NEW-02] HIGH** create carePlan consult ganda tanpa cek existing — care-plan.service.ts:60-113
- **[NEW-03] HIGH** cancelEpisode **tidak cascade bpjsQueues + invoices** — registration.service.ts:923-936 → antrean BPJS bocor di Mobile JKN, kasir bisa tagih episode batal
- **[NEW-04] HIGH** dischargeEpisode tidak batalkan child (foodOrders/surgeries/supportOrders/prescriptions) — registration.service.ts:684-729
- **[NEW-05] HIGH** SEP issue() tak cek closed/cancelled + tak cek bpjsSepNo → SEP ganda — sep.service.ts:91-165
- **[NEW-06] HIGH** recordVisite tanpa guard closed + duplikat (episode,doctor,date) — order.service.ts:231-246
- **[NEW-07] MED** deleteVisite hard delete hapus jejak tagihan — order.service.ts:262-269
- **[NEW-08] MED** respondConsult overwrite tanpa status check — care-plan.service.ts:177-190
- **[NEW-09] MED** returnOnDischarge non-idempotent utk 'failed' retry — sep.service.ts:249-262
- **[NEW-10] MED** editEpisode tanpa guard closed/cancelled — registration.service.ts:973-989
- **[NEW-11] MED** setEpisodeCoding tanpa guard episode — registration.service.ts:893-911
- **[NEW-12] MED** payDeposit tanpa guard episode closed/cancelled — queue.service.ts:38-75
- **[NEW-13] MED** refundDeposit tolak refund walau episode closed — queue.service.ts:127-150
- **[NEW-14] MED** MCU walk-in hasPaidDeposit=true tanpa transaksi deposit riil — registration.service.ts:558-595
- **[NEW-15] MED** saveCathlabReport tanpa guard status order — order.service.ts:728-782
- **[NEW-16] MED** createPrescription guard hanya closed, bisa di episode cancelled — order.service.ts:367-379
- **[NEW-17] MED** createFoodOrder guard hanya closed, bukan cancelled — order.service.ts:816-833
- **[NEW-18] MED** createSupportOrder guard hanya closed — order.service.ts:474-519
- **[NEW-19] MED** SEP issue() noKartu bisa '' → BPJS insert gagal — sep.service.ts:119,144
- **[NEW-20] MED** clinicalObservations tanpa unique formCode — schema/clinical.ts:195-224
- **[NEW-21] MED** confirmObservation tak cek episode closed utk data sudah-confirm — clinical-observation.service.ts:345-350
- **[NEW-22] MED** RBAC: dischargeEpisode butuh `ranap/board:view` (view-only bisa pulangkan) — clinical.controller.ts:183
- **[NEW-23] LOW** RBAC: signEncounter `verifikasi/ttd:finish` tak cukup utk DPJP — clinical.controller.ts:227
- **[NEW-24] LOW** RBAC: record observasi tak include `igd/*` → perawat IGD tak bisa input TTV — clinical.controller.ts:272
- **[NEW-25] LOW** finishDoctor butuh `dokter/worklist:finish` — OK by design
- **[NEW-26] MED** finishNurse set nurseChecked tanpa cek episode cancelled — queue.service.ts:164-192
- **[NEW-27] LOW** callQueue guard deposit hanya outpatient — by design
- **[NEW-28] MED** episodeCharges hitung akomodasi full-day saat discharge (tagih 1 hari lebih) — order.service.ts:218-226
- **[NEW-29] LOW** SoapForm onSubmit tak disable saat saving (double submit) — SoapForm.tsx:105
- **[NEW-30] LOW** CpptTimeline render r.value bisa undefined/objek → crash — CpptTimeline.tsx:155-156
- **[NEW-31] LOW** CpptTimeline key r.label duplikat — CpptTimeline.tsx:155
- **[NEW-32] LOW** ttvLine p['systolic'] 0 → render TD 0/0 — CpptTimeline.tsx:35-39
- **[NEW-33] LOW** PatientListPage filter tgl-lahir format tak konsisten — PatientListPage.tsx:97
- **[NEW-34] MED** DoctorWorkspacePage patient bisa undefined saat merge — DoctorWorkspacePage.tsx:52
- **[NEW-35] LOW** TempPatientVerifyPage merge survivor sudah difilter mergedIntoId — OK
- **[NEW-36] MED** schema inpatientVisites tanpa unique (episode,doctor,date) — schema/clinical.ts:658-674
- **[NEW-37] MED** schema seps tanpa unique (episodeId, issued) — schema/clinical.ts:327
- **[NEW-38] LOW** SEP tglSep pakai UTC → beda hari WIB — sep.service.ts:126
- **[NEW-39] LOW** discharge notif push di tx terpisah — OK by design
- **[NEW-40]** RBAC REG/NURSE/DOCTOR lengkap; risiko utama NEW-22

---

## B. BILLING / KEUANGAN — 21 temuan

### Status defect lama
| # | Defect | Status |
|---|--------|--------|
| 1 | cancelInvoice tolak paid | **FIXED** (billing.service.ts:149) |
| 2 | payInvoice tanpa guard | **OPEN** (billing.service.ts:393-396) |
| 3 | voidSale farmasi | **OPEN parsial** (pharmacy.service.ts:262-281 — FEFO/item_stocks tak dipulihkan) |
| 4 | refundDeposit tanpa cek closed | **OPEN** (queue.service.ts:127-150) |
| 5 | DepositInvoicePage tanpa Refund | **OPEN** (endpoint ada clinical.controller.ts:343, FE tak pakai) |
| 6 | ALREADY_BILLED kolisi | **FIXED** (billing.service.ts:496-500) |

### Defect baru Billing
- **[VERIF-2] HIGH** payInvoice tanpa guard status: invoice VOID bisa dibayar ulang, paid bisa di-pay lagi — billing.service.ts:390-396
- **[NEW-01] HIGH** cancelInvoice void invoice POSTED tanpa reversal Odoo → AR ghost — billing.service.ts:147-149,183-184 + saga:75-88
- **[NEW-02] HIGH** postPayment (F4/F6) tak pernah dipanggil → pembayaran tak pernah didaftarkan ke Odoo — odoo18.adapter.ts:136-175 + saga (hanya postSaleOrder)
- **[NEW-03] MED-HIGH** depositApplied dihitung per-invoice tapi Σ deposit episode → deposit terpotong GANDA di multi-invoice — billing.service.ts:287-290 + InvoiceDetailPage:409-410
- **[NEW-04] MED-HIGH** mergeInvoices menghilangkan globalDiscount sumber — billing.service.ts:362-367
- **[NEW-05] MED-HIGH** dedup collapse baris manual refId='' dalam 1 resep → qty/item hilang, tagihan kurang — billing.service.ts:473-484 + BillingFarmasiPage.tsx:39
- **[NEW-06] MED-HIGH** payInvoice tidak settle deposit & tanpa catat payment (metode/nominal/paidAt) — billing.service.ts:390-415, tabel invoices tanpa paidAt/method
- **[NEW-07] MED** refundDeposit tanpa guard invoice-paid & bisa refund penuh walau invoice belum lunas — queue.service.ts:127-150
- **[VERIF-3b] MED** voidSale kembalikan ledger tapi tidak restore FEFO/item_stocks — pharmacy.service.ts:262-281
- **[NEW-08] MED** Odoo postSaleOrder abaikan coverages (penjamin split) — odoo18.adapter.ts:75-121
- **[NEW-09] MED** Diskon nominal → persen Odoo rounded 2 desimal → selisih rupiah — odoo18.adapter.ts:92
- **[NEW-10] MED** invoiceSummary count include VOID; outstanding include DRAFT — billing.service.ts:256-263,103
- **[NEW-11] MED** DUPLICATE_INVOICE_SAME_DAY blokir penagihan tambahan hari sama — billing.service.ts:512-524
- **[NEW-12] MED** Tidak ada jalur un-pay/koreksi invoice salah lunas — billing.service.ts:147-149
- **[NEW-13] MED** Saga failed → invoice tetap bisa dibayar → Odoo tak pernah terima — billing.service.ts:393 + saga:75-88
- **[NEW-14] MED** FE popup Bayar tampilkan total penuh tanpa potongan cover/deposit — BillingPage.tsx:198
- **[NEW-15] LOW-MED** Odoo postPayment idempotensi race (memo cek sebelum tulis) — odoo18.adapter.ts:136-175
- **[NEW-16] LOW-MED** InvoiceDetailPage tak ada aksi Batalkan & pay tanpa konfirmasi — InvoiceDetailPage.tsx:262-270
- **[NEW-17] LOW** Preview tarif tindakan tanpa insurerId → beda dgn harga server — BillingPage.tsx:328
- **[NEW-18] LOW** adjustDraftForPrescriptionReturn clamp 0 tanpa bersihkan coverage — billing.service.ts:341

---

## C. FARMASI & PENUNJANG — 32 temuan

### Status defect lama (9) — SEMUA OPEN
| # | Defect | Status |
|---|--------|--------|
| 1 | deductFefo stok minus tanpa throw | **OPEN** (pharmacy.service.ts:550-563) |
| 2 | adjustStock bisa minus | **OPEN** (pharmacy.service.ts:606-616) |
| 3 | createSale OTC tanpa cek stok | **OPEN** (pharmacy.service.ts:204-243) |
| 4 | setSurgeryStatus tanpa enum | **OPEN** (ops.service.ts:912-919) |
| 5 | saveCathlabReport guard cancelled | **OPEN** (order.service.ts:728) |
| 6 | bloodbank.createRequest guard | **OPEN** (bloodbank.service.ts:106-123) |
| 7 | imaging.remove hard delete | **OPEN** (imaging.service.ts:87-95) |
| 8 | specimen.addEvent state lompat | **OPEN parsial** (specimen.service.ts:52-67) |
| 9 | LIS re-write verified | **OPEN** (order.service.ts:606-643 + lis.service.ts:45-65) |

### Defect baru Farmasi & Penunjang
- **[NEW-01] CRITICAL** deductFefo izinkan stok minus tanpa throw — pharmacy.service.ts:550-563
- **[NEW-02] HIGH** adjustStock delta negatif besar tanpa guard on-hand — pharmacy.service.ts:606-616
- **[NEW-03] CRITICAL** createSale OTC tidak pre-check on-hand — pharmacy.service.ts:204-243
- **[NEW-04] HIGH** item qty=0 (free-text) bisa dispense tanpa batas — pharmacy.service.ts:362
- **[NEW-05] HIGH** racikan tanpa model komponen → stok komponen TIDAK dipotong saat dispense — pharmacy.service.ts:341-369 + OrderSection.tsx:218-258
- **[NEW-06] CRITICAL** setSurgeryStatus tanpa enum/whitelist — ops.service.ts:912-919
- **[NEW-07] HIGH** scheduleSurgery tak tolak episode cancelled — ops.service.ts:813-836
- **[NEW-08] HIGH** saveCathlabReport tak guard cancelled/verified — order.service.ts:728-782
- **[NEW-09] CRITICAL** bloodbank.createRequest tak validasi episode closed + tak cross-check episode↔patientId — bloodbank.service.ts:106-123
- **[NEW-10] HIGH** issueUnit tanpa audit crossmatch — bloodbank.service.ts:126-148
- **[NEW-11] CRITICAL** imaging.upload tak validasi orderId.patientId === input.patientId (cross-patient) — imaging.service.ts:27-48
- **[NEW-12] CRITICAL** imaging.remove hard DELETE tanpa soft-delete/audit — imaging.service.ts:87-95
- **[NEW-13] HIGH** imaging.upload tak cek order resulted/verified — imaging.service.ts:33-37
- **[NEW-14] HIGH** resultSupport allowedFrom include 'resulted' → overwrite hasil verified — order.service.ts:606-643
- **[NEW-15] HIGH** LIS ingest tak validasi order.category==='lab' — lis.service.ts:45-65
- **[NEW-16] HIGH** FE PenunjangPage tak disable tombol Edit Hasil saat verified — PenunjangPage.tsx:181
- **[NEW-17] HIGH** specimen.addEvent state machine parsial (bisa received→received, collected→discarded skip received) — specimen.service.ts:52-67
- **[NEW-18] MED** FE SpecimenModal tombol Tolak/Musnahkan tanpa konfirmasi — SpecimenModal.tsx:63-72
- **[NEW-19] MED** redeemIter iterUsedCount++ tanpa FOR UPDATE → race over-claim — order.service.ts:273-296
- **[NEW-20] MED** confirm/pay/dispense transisi tanpa FOR UPDATE → race double-dispense — pharmacy.service.ts:284-298,336-338,677-687
- **[NEW-21] MED** cancelPrescription tak tolak bila dispensedAmount>0 (partial) — pharmacy.service.ts:385-399
- **[NEW-22] MED** submitApotekResep tak cek status resep cancelled/returned — pharmacy.service.ts:472-503
- **[NEW-23] MED** FE ImagingPanel Popconfirm hapus tanpa nama file — ImagingPanel.tsx:92
- **[NEW-24] MED** FE StokObatPage tak warning delta > qtyOnHand — StokObatPage.tsx:62-73
- **[NEW-25] MED** FE PenjualanBebasPage cart qty naik tanpa cek stok — PenjualanBebasPage.tsx:49-51
- **[NEW-26] MED** FE BloodBankPage tak filter ABO/Rh compat — BloodBankPage.tsx:72-75
- **[NEW-27] MED** FE doReturn tanpa Popconfirm — PharmacyPage.tsx:255-276
- **[NEW-28] MED** FE OrderSection submit tak disable saat episode closed — OrderSection.tsx:345-363
- **[NEW-29] MED** FE CathlabReportForm re-edit setelah status final — CathlabReportForm.tsx:107-140
- **[NEW-30] LOW** specimenNo randomBytes(3) collision tanpa retry — specimen.service.ts:20-25
- **[NEW-31] LOW** PenunjangPage STATUS_TABS inkonsisten per kategori — PenunjangPage.tsx:174-188
- **[NEW-32] LOW** reviewPrescription tak emit event 'flagged' ke dokter — pharmacy.service.ts:306-333

---

## D. RBAC / AUTH / MASTERDATA — 12 temuan

### Status defect lama
| # | Defect | Status |
|---|--------|--------|
| 1 | devResetToken bocor non-prod (S1) | **OPEN** (auth.service.ts:103, gated !isProd()) |
| 2 | JWT/MPI secret hardcoded fallback (S2) | **FIXED** (tenant.middleware.ts:30-34 fail-closed prod) |
| 3 | master:create permission generik (A-4) | **OPEN** (masterdata.controller.ts:109-110) |
| 4 | RBAC multi-role+leak (bbaa73c) | **FIXED** (getEffective ownership-aware, guard union) |
| 5 | BPJS role tak ter-map (fb #165) | **FIXED** (rbac.service.ts:45,67) |
| 6 | MenuPrefsEditor multi-role | **FIXED** (setMenuPrefs:186-188 filter status) |

### Defect baru RBAC/Auth/Masterdata
- **[NEW-01] S1** forgot-password tanpa rate limit; token 1 jam brute-force — auth.service.ts:85-127
- **[NEW-02] S1** devResetToken bocor di staging/test (bukan cuma prod) — auth.service.ts:103
- **[NEW-03] S1** GET/DELETE `/masterdata/res/:resource/:id` tanpa RequirePermission → semua staf bisa baca/delete users/bpjs-certs — masterdata.controller.ts:106-112
- **[NEW-04] S1** resDelete/resUpdate utk tabel site:false (icd, provinces, dll) → CROSS-TENANT delete — masterdata.service.ts:377
- **[NEW-05] S1** setRoleGrants tak validasi roleId milik site → grant role site B — rbac.service.ts:32
- **[NEW-06] S1** REKAMMEDIS & UPM tak ada di DEFAULT_ROLE_PAGES → seedDefaults skip → deny semua (role login tapi menu kosong) — rbac.service.ts:51-75
- **[NEW-07] S2** CASHIER vs farmasi/billing permission mismatch (verifikasi migrasi 0186) — rbac.service.ts:57
- **[NEW-08] S2** deleteSchedule tanpa cek referensi child; resDelete units/actions → FK violation 500 — masterdata.service.ts:320-326
- **[NEW-09] S2** setMenuPrefs tak validasi hiddenKeys ⊆ menu diizinkan — rbac.service.ts:183-193
- **[NEW-10] S2** localStorage token + AuthUser roles[] (FE bisa edit, tapi getEffective cek owned — FIXED); sisa: token expiry 8 jam tanpa refresh — auth.ts:61-63
- **[NEW-11] S3** changePassword akun legacy (null passwordHash) bisa set password tanpa verify current — auth.service.ts:138
- **[NEW-12] S3** resBulkCreate tanpa validasi required columns → 500 mentah — masterdata.service.ts:492-502
- **[NEW-13] S3** resetPassword invalidasi token OK (normal)
- **[NEW-14] S3** catalog lab-online ada — bukan defect
- **[NEW-15] S2** AppShell homePath fallback `/registrasi/pasien` → redirect loop utk role tanpa menu (REKAMMEDIS/UPM) — AppShell.tsx:89
- **[NEW-16] S3** roles.ts GROUPS_FOR.ok hanya g-dashboard padahal RBAC izinkan jadwal/operasi dll → FE sidebar tak tampil — roles.ts:6-30
- **[NEW-17] S3** TTL 8 jam fixed tanpa refresh flow — auth.service.ts:76
- **Cacat lintas peta** ROLE_PRIORITY missing 'bpjs','ok','rekammedis','upm','mcu' → user multi-role landing salah — rbac.service.ts:39-47

---

## PRIORITAS FIX (Top 10 blocker)

1. **[CRITICAL] Stok farmasi**: deductFefo + createSale + adjustStock bisa stok minus (F-CRIT-1/2/3) → tambah DB CHECK (qty_on_hand >= 0) + throw STOCK_INSUFFICIENT
2. **[CRITICAL] imaging.upload cross-patient**: orderId.patientId !== input.patientId harus ditolak (keselamatan pasien)
3. **[CRITICAL] imaging.remove hard delete**: ganti soft-delete + audit
4. **[CRITICAL] setSurgeryStatus**: whitelist enum (scheduled|in_progress|done|cancelled)
5. **[HIGH] cancelEpisode**: cascade bpjsQueues + void/flag invoice terbuka
6. **[HIGH] dischargeEpisode**: cascade cancel child records (food/surgery/support/prescription)
7. **[HIGH] payInvoice**: guard status (draft|posted only; tolak void/paid)
8. **[HIGH] SEP issue()**: guard closed + cek bpjsSepNo existing (idempotent)
9. **[HIGH] recordVisite**: guard closed + uniqueIndex (episodeId, doctorId, visitDate)
10. **[HIGH] Odoo**: postPayment tak pernah dipanggil + cancel posted tanpa reversal → AR ghost

## CATATAN VERIFIKASI
- `emr_episodes.doctorScheduleId` (schema/clinical.ts:151) TANPA FK ke doctor_schedules → deleteSchedule = dangling ref (bukan FK violation)
- cancelEpisode sudah cascade foodOrders+surgeries (FIXED batch2), TAPI masih bolong bpjsQueues + invoices
- Semua audit read-only; tidak ada file dimodifikasi
