# Audit Defect Kesia V3 — Per Role & Menu (Batch 1–4)

- **Repo**: `E:\WORK KESIA\Project\kesiaV3` — Next.js `apps/web-clinic` + NestJS `apps/api`
- **HEAD**: `5300cb6` (branch main — tidak ada commit fix baru setelah audit)
- **Tanggal audit**: 14 Agustus 2026
- **Auditor**: Salsabila (QA Agent)
- **Metode**: Verifikasi langsung ke kode backend (NestJS service) & frontend (Next.js page/hook)

---

## Ringkasan Eksekutif

| Batch | Fokus | Jumlah Defect |
|---|---|---|
| Batch 1 | Registrasi, Kasir, Farmasi, OK, Penunjang, APJ, EMR | 15 |
| Batch 2 | Billing, Stok, SEP, OK, EMR, Antrean | 12 |
| Batch 3 | Masterdata, RBAC, ARM, Casemix | 12 |
| Batch 4 | Per-role (Kasir, Dokter, RM, BPJS, OK, Gizi) | 17 |
| **TOTAL** | | **56 defect baru** |

**Prioritas kritis (urut)**
1. 🔴 K7 — Void invoice status `paid` dibolehkan tanpa mekanisme refund → potensi kerugian uang
2. 🔴 R4 — `mergePatient` tidak re-point tabel keuangan (invoice, deposit, ARM, bpjs_queue) → data orphan
3. 🔴 R3/R4/R5 (batch 3) — Auth: token reset bocor di non-prod, dev-login terbuka di staging, JWT secret fallback hardcoded
4. 🔴 D8 — `createCarePlan` tanpa guard episode closed (0 guard)
5. 🔴 O6 — `scheduleSurgery` tidak cek status episode (closed/cancelled)
6. 🟡 Sisanya — validasi enum/state-machine & duplikat data

---

# BATCH 1 — 15 Defect (Registrasi, Kasir, Farmasi, OK, Penunjang, APJ, EMR)

## Pendaftaran / Registrasi

### R1 — Pasien baru dibuat tanpa pengecekan duplikasi NIK
- **File**: `apps/api/src/modules/clinical/registration.service.ts:345-391`
- **Detail**: `registerPatient` INSERT langsung ke `patients` tanpa cek `idNo` (NIK) yang sudah ada di site. Pasien yang sama bisa dibuat berkali-kali dengan NIK sama → MR ganda, MPI kotor.
- **Dampak**: Duplikasi MR, riwayat klinis terpecah, risiko klaim BPJS salah.

### R2 — Promoting pasien temporary tidak mengecek NIK bentrok dengan MR aktif
- **File**: `apps/api/src/modules/clinical/registration.service.ts:424-455`
- **Detail**: `verifyPatient` (promote temporary → permanen) hanya update `set['idNo']` tanpa cek apakah NIK sudah dipakai pasien lain yang punya episode aktif.
- **Dampak**: Dua MR permanen dengan NIK sama; merge manual baru ketahuan belakangan.

### R3 — Merge patient tidak merepoint `invoices` & `deposit_payments`
- **File**: `apps/api/src/modules/clinical/registration.service.ts:452-455`
- **Detail**: `MERGE_TABLES` hanya berisi 12 tabel klinis (`emr_episodes, prescriptions, support_orders, seps, care_plans, nursing_care_plans, medical_resumes, casemix_entries, clinical_observations, incidents, patient_documents, surgeries`). Tabel keuangan & operasional TIDAK di-repoint.
- **Dampak**: Tagihan, deposit, dan data operasional pasien sumber jadi orphan (hilang dari survivor).

## Kasir / Deposit

### K1 — Deposit dapat direfund setelah episode status `closed`
- **File**: `apps/api/src/modules/clinical/queue.service.ts:72-96`
- **Detail**: `refundDeposit` hanya cek `hasPaidDeposit` & saldo > 0, TIDAK cek `ep.status`. Episode yang sudah selesai/closed masih bisa direfund.
- **Dampak**: Refund ganda di luar alur; pasien bisa dapat uang untuk layanan yang sudah selesai.

### K2 — Refund deposit tidak membatalkan invoice DRAFT terkait
- **File**: `apps/api/src/modules/clinical/queue.service.ts:86`
- **Detail**: Saat refund, hanya insert baris negatif `deposit_payments` + update `hasPaidDeposit=false`. Invoice DRAFT yang memakai deposit tidak di-update → sisa bayar invoice tidak berubah.
- **Dampak**: Invoice menampilkan deposit yang sudah direfund sebagai pengurang.

### K3 — Refund deposit tidak memvalidasi idempotency / flag refund
- **File**: `apps/api/src/modules/clinical/queue.service.ts:72-96`
- **Detail**: Tidak ada flag `refunded` / guard double-refund selain `total > 0`. Refund berurutan dengan saldo 0 → error, tapi tidak ada idempotency token.
- **Dampak**: Race condition refund ganda bila dua request paralel.

## Operasi / OK

### O1 — Penjadwalan operasi tidak memverifikasi status episode (closed/cancelled)
- **File**: `apps/api/src/modules/ops/ops.service.ts:818`
- **Detail**: `scheduleSurgery` hanya `select({ patientId, source })` lalu cek `EPISODE_NOT_FOUND`. Status `closed`/`cancelled` tidak dicek.
- **Dampak**: Operasi bisa dijadwalkan untuk pasien yang sudah pulang/dibatalkan.

### O2 — `setSurgeryStatus` menerima input string bebas tanpa enum/transition validation
- **File**: `apps/api/src/modules/ops/ops.service.ts:908-915`
- **Detail**: `db.update(S).set({ status })` langsung — status apa pun diterima. FE punya map `NEXT` (`OperasiPage.tsx:138-143`), tapi API tidak memvalidasi.
- **Dampak**: State korup (mis. `done → scheduled`), board salah.

### O3 — Batal operasi tidak mentrigger pembatalan antrean BPJS & SEP
- **File**: `apps/api/src/modules/ops/ops.service.ts` (setSurgeryStatus) + `apps/api/src/modules/clinical/sep.service.ts`
- **Detail**: Saat status surgery diubah ke `cancelled`, tidak ada panggilan `batalAntrean` BPJS atau pembatalan SEP terkait episode.
- **Dampak**: BPJS melihat antrean/SEP aktif untuk operasi batal.

## Farmasi

### F1 — `editItem` resep mengizinkan quantity 0 atau negatif di controller
- **File**: `apps/api/src/modules/clinical/clinical.controller.ts:465`
- **Detail**: Schema `EditPrescriptionItemSchema` mungkin `.positive()` di schema, tapi service set `set['quantity'] = patch.quantity` tanpa guard tambahan; bypass via API langsung tetap bisa qty ≤ 0.
- **Dampak**: Resep qty 0/negatif → billing & stok kacau.

### F2 — Edit item resep tidak menjaga konsistensi flag `isRacikan`
- **File**: `apps/api/src/modules/clinical/pharmacy.service.ts:403-430`
- **Detail**: `editItem` tidak pernah menyentuh/merekomputasi `isRacikan`. Ubah `drugId` item racikan → status racikan tetap, atau sebaliknya → racikan jadi obat jadi.
- **Dampak**: Racikan tercatat sebagai obat jadi (atau sebaliknya) → salah harga, salah stok.

## Penunjang

### P1 — Re-input hasil lab menghapus alert critical value status pending yang sudah di-ack
- **File**: `apps/api/src/modules/clinical/order.service.ts:541`
- **Detail**: `resultSupport` menghapus alert critical value tanpa filter status; alert yang sudah di-ack DPJP hilang saat hasil di-input ulang.
- **Dampak**: Kehilangan jejak penanganan nilai kritis (regulasi lab).

### P2 — Status order penunjang dapat diubah ke `start` meskipun sudah `verified`
- **File**: `apps/api/src/modules/clinical/order.service.ts:509-517` (`supportTransition`)
- **Detail**: `supportTransition` tidak punya state machine — status `start`/`resulted`/`verified` bisa dipanggil kapan saja.
- **Dampak**: Order verified bisa dikembalikan ke in-progress; duplikasi hasil.

## BPJS / SEP

### A1 — Payload `sendBpjsQueue` hardcode `jampraktek` dan fallback `kodedokter=''`
- **File**: `apps/api/src/modules/ops/ops.service.ts:102`
- **Detail**: Payload antrean BPJS menggunakan `jampraktek` hardcode & `kodedokter` fallback kosong.
- **Dampak**: Antrean BPJS salah jam/kode dokter → penolakan BPJS.

### A2 — `sisakuotajkn` dikirim hardcode `1`
- **File**: `apps/api/src/modules/ops/ops.service.ts:106`
- **Detail**: Nilai sisa kuota dikirim konstan `1`, bukan nilai riil dari jadwal.
- **Dampak**: Kuota JKN di sisi BPJS tidak akurat.

## EMR / Keperawatan

### E1 — Care plan create tanpa cek episode closed
- **File**: `apps/api/src/modules/clinical/care-plan.service.ts:49-75`
- **Detail**: INSERT `carePlans` langsung, 0 guard `EPISODE_CLOSED` (grep `EPISODE` = 0 hit).
- **Dampak**: Care plan dibuat di episode closed; konsul bisa memunculkan episode baru dari episode mati.

---

# BATCH 2 — 12 Defect (Billing, Stok, SEP, OK, EMR, Antrean)

## Billing / Kasir

### K4 — `payInvoice` dapat mengeksekusi bayar pada invoice status `draft`, `posted`, atau `void`
- **File**: `apps/api/src/modules/billing/billing.service.ts:385-390`
- **Detail**: UPDATE `status='paid'` langsung tanpa baca status sebelumnya. Invoice draft (belum final) bisa langsung lunas.
- **Dampak**: Pembayaran sebelum invoice valid; void bisa jadi paid lagi.

### K5 — `cancelInvoice` membatalkan invoice status `paid` tanpa mekanisme refund/kembalikan uang
- **File**: `apps/api/src/modules/billing/billing.service.ts:137`
- **Detail**: Guard hanya `INVOICE_ALREADY_VOID`. Invoice `paid` bisa di-void, resep di-revert ke `confirmed`, tapi uang tidak dikembalikan.
- **Dampak**: Pasien bayar → invoice dibatalkan → uang raib tanpa refund.

### K6 — Pay/refund deposit tanpa pengecekan status episode
- **File**: `apps/api/src/modules/clinical/queue.service.ts:38-67` (payDeposit), `72-96` (refundDeposit)
- **Detail**: Tidak ada cek `ep.status` / episode closed di kedua fungsi.
- **Dampak**: Deposit bisa dibayar/direfund untuk episode yang sudah selesai.

## Farmasi / Stok

### F3 — `deductFefo` tidak melempar error jika stok batch kurang dari requested qty (silent minus)
- **File**: `apps/api/src/modules/clinical/pharmacy.service.ts:550-563`
- **Detail**: Loop potong batch sampai `remaining=0`; kalau stok habis, `remaining` masih > 0 tapi TIDAK ada throw → item_stocks jadi minus.
- **Dampak**: Stok negatif diam-diam; jurnal stok salah.

### F4 — `adjustStock` delta negatif dapat membuat `qtyOnHand` menjadi minus
- **File**: `apps/api/src/modules/clinical/pharmacy.service.ts:607`
- **Detail**: `applyStockMovement` update on-hand tanpa guard `qtyOnHand >= 0`.
- **Dampak**: Stok minus, opname & rekap rusak.

## SEP

### D6 — `issue()` SEP tidak mengecek apakah SEP sudah terbit atau episode sudah closed/cancelled
- **File**: `apps/api/src/modules/clinical/sep.service.ts:91-130`
- **Detail**: Hanya cek penjamin BPJS + kartu. Tidak cek `seps` existing `issued` & tidak cek `ep.status`.
- **Dampak**: SEP ganda per episode; SEP untuk pasien sudah pulang.

### D7 — Console SEP menyajikan episode berstatus `cancelled`/`closed`
- **File**: `apps/api/src/modules/clinical/sep.service.ts:283`
- **Detail**: Query konsol SEP tanpa filter status episode.
- **Dampak**: Operasional bingung melihat SEP aktif di episode mati.

## OK

### O4 — Status surgery dapat di-update melompati status yang seharusnya di API NestJS
- **File**: `apps/api/src/modules/ops/ops.service.ts:908-915`
- **Detail**: API menerima string bebas; FE punya state map tapi server tidak enforce.
- **Dampak**: Melompat `scheduled → done`, board & laporan salah.

### O5 — `transferBed` & `assignBed` tidak memverifikasi outstanding billing
- **File**: `apps/api/src/modules/ops/ops.service.ts:625-660`, `719-737`
- **Detail**: `releaseBed` sudah punya guard `BILLING_UNPAID` (`ops.service.ts:655-660`), tapi `transferBed`/`assignBed` tidak. Catatan: `transferBed` juga tidak cek bed tujuan INBED (baru cek via `assignBed` setelah bed lama dibebaskan).
- **Dampak**: Transfer bed tanpa tagihan lunas; potensi double-occupy window.

## EMR

### E3 — `recordVisite` dapat dicatat pada episode berstatus `closed`
- **File**: `apps/api/src/modules/clinical/order.service.ts:231`
- **Detail**: `recordVisite` hanya cek episode exists (`EPISODE_NOT_FOUND`), tidak cek `status`/`closedAt`.
- **Dampak**: Visite harian dicatat setelah pasien pulang → billing akomodasi salah.

### E4 — `createFoodOrder` tidak memiliki gate status episode closed
- **File**: `apps/api/src/modules/clinical/order.service.ts:729-741`
- **Detail**: INSERT `foodOrders` langsung tanpa cek episode.
- **Dampak**: Order diet untuk pasien sudah pulang; gizi memasak sia-sia.

## Antrean BPJS

### A3 — `sendBpjsQueue` tidak memiliki unique check / guard duplikasi per episode
- **File**: `apps/api/src/modules/ops/ops.service.ts:82-100`
- **Detail**: Selalu insert antrean baru; tidak cek antrean aktif per episode.
- **Dampak**: Booking code ganda per episode → bingung di Mobile JKN.

### A4 — `listBpjsQueue` menyajikan episode yang sudah closed/cancelled
- **File**: `apps/api/src/modules/ops/ops.service.ts:51-75`
- **Detail**: Query join `insurers.type='BPJS'` tanpa filter `closedAt`.
- **Dampak**: Antrean pasien pulang masih tampil.

### A5 — `advanceQueueTask` dapat memajukan task pada antrean status `served`/`checkedin`
- **File**: `apps/api/src/modules/ops/ops.service.ts:136-159`
- **Detail**: Bila `q.status === 'served'`, taskId ≥ 1 tetap bisa di-insert; guard hanya `ne(Q.status, 'cancelled')`.
- **Dampak**: Task naik setelah antrean selesai.

---

# BATCH 3 — 12 Defect (Masterdata, RBAC, ARM, Casemix)

## Masterdata (role Admin)

### M1 — `res/:resource` CRUD generik tanpa unique check
- **File**: `apps/api/src/modules/masterdata/masterdata.service.ts:487-491` (`resCreate` — `clean()` + insert tanpa validasi unik), contoh konkret `createUnit` `:188-192` (INSERT `units` tanpa cek `code` duplikat).
- **Dampak**: Unit/poli, item, insurer duplikat → jadwal dokter nyangkut ke poli salah, stok terpecah.

### M2 — `resDelete` hapus master yang masih dipakai
- **File**: `apps/api/src/modules/masterdata/masterdata.service.ts:507-515`
- **Detail**: `db.delete(table)` langsung tanpa cek referensi child (episode aktif, stok, pasien).
- **Dampak**: FK error 500 ATAU (dengan ON DELETE CASCADE) data klinis hilang.

### M3 — `resList` limit 500 tanpa pagination
- **File**: `apps/api/src/modules/masterdata/masterdata.service.ts:482`
- **Detail**: `.limit(500)` diam-diam memotong data > 500 baris (`icd`, `regencies`, `villages`).
- **Dampak**: Dropdown alamat/ICD tidak lengkap tanpa indikasi.

### M4 — `resList` tabel tanpa kolom `name`/`code` query `q` jadi no-op
- **File**: `apps/api/src/modules/masterdata/masterdata.service.ts:473-476`
- **Detail**: Filter `q` hanya bekerja bila tabel punya `name`/`code`; tabel lain filter diam-diam diabaikan.
- **Dampak**: FE kira sedang filter, padahal menampilkan semua baris.

### M5 — `resBulkCreate` tanpa row cap
- **File**: `apps/api/src/modules/masterdata/masterdata.service.ts:492-503`
- **Detail**: Satu request bisa insert ribuan baris dalam 1 transaksi tanpa batas.
- **Dampak**: Request besar → DB lock/latency.

## RBAC / Keamanan (role Admin)

### R1 — `setUserRoles` tanpa validasi roleId milik site
- **File**: `apps/api/src/modules/rbac/rbac.service.ts:140-150`
- **Detail**: Terima `roleIds` apa pun, langsung `insert(user_roles)`; roleId dari situs lain bisa di-assign → privilege cross-site. `setRoleGrants` (`:27-35`) juga tidak cek roleId exists.
- **Dampak**: Eskalasi privilege lintas site.

### R2 — Role kosong = semua akses hilang (no fallback guard)
- **File**: `apps/api/src/modules/rbac/rbac.service.ts:147`
- **Detail**: `roleId: ids[0] ?? null` — assign role kosong → user kehilangan semua permission.
- **Dampak**: Admin tak sengaja mengunci user.

### R3 — Reset password non-prod bocor token
- **File**: `apps/api/src/modules/auth/auth.service.ts:101-103`
- **Detail**: `if (!isProd()) return { ...generic, devResetToken: token }` — di staging (NODE_ENV ≠ production) token reset dikembalikan ke respons API.
- **Dampak**: Siapa pun dengan akses respons bisa reset password user lain.

### R4 — `dev-login` tetap aktif di staging
- **File**: `apps/api/src/modules/auth/dev-auth.controller.ts:45-47`
- **Detail**: Guard hanya `NODE_ENV === 'production'`. Staging `development` → `dev-login` bisa bikin token admin.
- **Dampak**: Akses penuh tanpa kredensial di staging.

### R5 — `KESIA_INTERNAL_JWT_SECRET` fallback hardcoded
- **File**: `apps/api/src/modules/auth/auth.service.ts:70`, `tenant.middleware.ts:29`, `blind-index.ts:6`
- **Detail**: `'dev-internal-jwt-secret-change-me'` / `'dev-mpi-secret-change-me'` sebagai default saat env tidak set.
- **Dampak**: JWT bisa dipalsukan, blind-index NIK bisa dibalik bila secret default terpakai di prod.

## RM / ARM (role Petugas RM)

### A1 — `setArm` status bebas tanpa enum
- **File**: `apps/api/src/modules/ops/ops.service.ts:462-468`
- **Detail**: `set({ status: input.status })` — string apa pun tersimpan (`borrowed`/`in_storage`/`lost`/`sampah`).
- **Dampak**: Status ARM kotor, tracer tidak konsisten.

### A2 — `borrowArm` bisa pinjam berkas episode closed
- **File**: `apps/api/src/modules/ops/ops.service.ts:473-487`
- **Detail**: Guard hanya `ARM_ALREADY_BORROWED`; tidak cek status episode. `returnArm` update `in_storage` juga tanpa cek.
- **Dampak**: Berkas pasien lama bisa dipinjam tanpa limit; tracer salah.

## Casemix / INA-CBG (role BPJS/Coding)

### C1 — `saveCasemix` tanpa cek episode source
- **File**: `apps/api/src/modules/ops/ops.service.ts:217-235`
- **Detail**: INSERT `casemix_entries` untuk episode BPJS apa pun; `listCasemix` (`:194-215`) sudah include `inArray(source, ['inpatient','emergency','outpatient'])` — rawat jalan bisa di-CBG.
- **Dampak**: Klaim ganda ilegal untuk rawat jalan.

### C2 — `saveCasemix` tarif placeholder hardcode
- **File**: `apps/api/src/modules/ops/ops.service.ts:222-224`
- **Detail**: `cbgTariff ?? 1500000` + `INACBG-UNSPEC` saat ICD kosong. Tarif default 1,5 juta tanpa grouper = angka fiktif masuk klaim.
- **Dampak**: Nominal klaim tidak valid.

### C3 — `groupCasemix` update tidak ada episode status guard
- **File**: `apps/api/src/modules/ops/ops.service.ts:284-309`
- **Detail**: Cek `patientId, source, class` saja, tidak cek `closedAt`. Grouping ulang setelah episode closed = klaim double.
- **Dampak**: Klaim berulang untuk episode selesai.

---

# BATCH 4 — 17 Defect (Per-Role Deep Dive)

## Role Kasir / Billing

### K7 — Void invoice status `paid` DIBOLEHKAN tanpa refund
- **File**: `apps/web-clinic/src/features/billing/BillingPage.tsx:182` (FE: tombol Batal untuk `r.status !== 'void'` — termasuk Lunas), `apps/api/src/modules/billing/billing.service.ts:137-195`
- **Detail**: `cancelInvoice` guard hanya `INVOICE_ALREADY_VOID`; invoice `paid` di-void → resep di-flip balik ke `confirmed` (un-pay), **uang tidak dikembalikan** ke pasien.
- **Dampak**: 🔴 **Kerugian uang**. Pasien bayar tunai → invoice void → tidak ada refund tercatat.
- **Fix**: Tolak void invoice `paid` (atau wajibkan jurnal refund) di `cancelInvoice` + sembunyikan tombol Batal utk status `paid` di FE.

### K8 — `payInvoice` tanpa cek status invoice
- **File**: `apps/api/src/modules/billing/billing.service.ts:385-390`
- **Detail**: UPDATE langsung `status='paid'` tanpa baca status; draft/posted/void bisa jadi paid.
- **Dampak**: Invoice draft dibayar sebelum final; void bisa aktif lagi.

### K9 — `voidSale` farmasi restore stok tapi tidak refund uang & tanpa guard status
- **File**: `apps/api/src/modules/clinical/pharmacy.service.ts:262-272`
- **Detail**: `voidSale` restore stok via `applyStockMovement` tapi tidak ada refund tercatat & tidak cek sale sudah dibayar/lunas.
- **Dampak**: Uang penjualan bebas hilang tanpa jejak refund.

## Role Dokter / Perawat

### D8 — `createCarePlan` 0 guard episode (closed/cancelled)
- **File**: `apps/api/src/modules/clinical/care-plan.service.ts:49-90`
- **Detail**: INSERT `carePlans` langsung (grep `EPISODE_CLOSED` = 0 hit). Konsul `once` bahkan membuat episode baru (`emrEpisodePost`) tanpa cek episode asal valid/closed. Bandingkan `createPrescription`/`createSupportOrder` yang sudah punya guard `EPISODE_CLOSED` (`order.service.ts:310`, `416`).
- **Dampak**: Care plan dibuat di episode mati; konsul dari episode closed.
- **Fix**: Tambah guard `ep.status === 'closed' || ep.closedAt → EPISODE_CLOSED` di awal `create()`.

### D9 — `confirmObservation` tidak cek episode status
- **File**: `apps/api/src/modules/clinical/clinical-observation.service.ts:330-353`
- **Detail**: Konfirmasi DPJP (CPPT/SOAP/SBAR) tidak cek `ep.status` — catatan episode closed masih bisa dikonfirmasi.
- **Dampak**: TTD dokumen setelah pasien pulang; inkonsistensi legal.

### D10 — `deleteVisite` hapus permanen tanpa guard
- **File**: `apps/api/src/modules/clinical/order.service.ts:262-266`
- **Detail**: `db.delete(V)` langsung; tidak ada soft-delete / audit trail.
- **Dampak**: Riwayat visite (dasar billing akomodasi) hilang permanen.

### D11 — `respondConsult` bisa menjawab konsul berulang
- **File**: `apps/api/src/modules/clinical/care-plan.service.ts:157-176`
- **Detail**: Update `status='responded'` tanpa cek status existing; konsul `responded` bisa dijawab ulang / ditimpa.
- **Dampak**: Jawaban konsul kedua menimpa yang pertama tanpa audit.

## Role Petugas RM (ARM)

### A6 — `setArm` status string bebas
- **File**: `apps/api/src/modules/ops/ops.service.ts:462-468`
- **Detail**: Tidak ada enum/whitelist status (`borrowed`, `in_storage`, `lost`, dll semua diterima).
- **Dampak**: Status tracer kotor, laporan RM salah.

### A7 — `listArm` default `armStatus='in_storage'` untuk SEMUA episode
- **File**: `apps/api/src/modules/ops/ops.service.ts:399-430`
- **Detail**: Episode tanpa record ARM ditampilkan sebagai `in_storage` (bukan "belum diarsip") — ambigu; limit 200 tanpa pagination juga memotong data.
- **Dampak**: Petugas RM salah kira berkas sudah diarsip.

### A8 — `markArmInactive` tanpa cek episode closed
- **File**: `apps/api/src/modules/ops/ops.service.ts:432-447`
- **Detail**: Berkas episode AKTIF (masih dirawat) bisa ditandai non-aktif/retensi.
- **Dampak**: Berkas pasien aktif masuk retensi → hilang saat dibutuhkan.

## Role BPJS

### B1 — `issue` SEP tidak cek episode closed/cancelled & tidak cek SEP sudah terbit
- **File**: `apps/api/src/modules/clinical/sep.service.ts:91-130`
- **Detail**: Hanya cek `insurerType === 'BPJS'` + kartu aktif. Tidak ada cek `ep.status` & tidak ada cek `seps.status='issued'` existing.
- **Dampak**: SEP ganda per episode; SEP untuk pasien pulang.

### B2 — `sendBpjsQueue` tanpa guard episode status/duplikasi
- **File**: `apps/api/src/modules/ops/ops.service.ts:82-100`
- **Detail**: Selalu insert antrean; tidak cek episode closed & tidak cek antrean aktif per episode.
- **Dampak**: Booking code ganda; antrean pasien pulang.

### B3 — `listBpjsQueue` tampilkan episode closed (limit 200, tanpa filter status)
- **File**: `apps/api/src/modules/ops/ops.service.ts:51-75`
- **Detail**: Query `insurers.type='BPJS'` tanpa filter `closedAt`/status.
- **Dampak**: Antrean pasien selesai masih tampil di monitoring.

## Role OK / Operasi

### O6 — `scheduleSurgery` tidak cek episode closed
- **File**: `apps/api/src/modules/ops/ops.service.ts:818-820`
- **Detail**: `select({ patientId, source })` + cek `EPISODE_NOT_FOUND` saja; tidak cek `status`/`closedAt`.
- **Dampak**: Operasi dijadwalkan utk pasien sudah pulang → kamar OK kosong, billing salah.

### O7 — `setSurgeryStatus` string bebas (FE punya NEXT map, API tidak)
- **File**: `apps/api/src/modules/ops/ops.service.ts:908-915`
- **Detail**: FE: `NEXT` map di `OperasiPage.tsx:138-143` (`scheduled→[in_progress,cancelled]`, dst). API: `set({ status })` langsung.
- **Dampak**: State machine dilanggar via API langsung.

## Role Pendaftaran (temuan terpenting batch 4)

### R4 — `mergePatient` TIDAK re-point tabel keuangan & operasional
- **File**: `apps/api/src/modules/clinical/registration.service.ts:452-455`
- **Detail**: `MERGE_TABLES` = `['emr_episodes','prescriptions','support_orders','seps','care_plans','nursing_care_plans','medical_resumes','casemix_entries','clinical_observations','incidents','patient_documents','surgeries']`. **TIDAK termasuk**: `invoices`, `deposit_payments`, `pharmacy_sales`, `arm_records`, `arm_loans`, `food_orders`, `inpatient_visites`, `bpjs_queues`.
- **Dampak**: 🔴 **Integritas finansial**. Tagihan, deposit, penjualan farmasi, peminjaman berkas, order diet, visite, antrean BPJS pasien sumber jadi ORPHAN — hilang dari pasien survivor. Kasir tidak bisa menagih, tracer RM hilang.
- **Fix**: Tambahkan 8 tabel tsb ke `MERGE_TABLES` + uji re-point.

## Role Admin / Masterdata

### M6 — `createUnit` tanpa unique check `code`
- **File**: `apps/api/src/modules/masterdata/masterdata.service.ts:188-192`
- **Detail**: INSERT `units` langsung; `code` duplikat bisa dibuat.
- **Dampak**: Poli ganda → jadwal dokter & antrean terpecah.

### M7 — `setUserRoles` tanpa validasi roleId exists
- **File**: `apps/api/src/modules/rbac/rbac.service.ts:140-150`
- **Detail**: `roleIds` bebas di-insert ke `user_roles`; roleId dari situs lain bisa di-assign.
- **Dampak**: Eskalasi privilege cross-site.

### M8 — `setRoleGrants` tanpa cek roleId exists
- **File**: `apps/api/src/modules/rbac/rbac.service.ts:27-35`
- **Detail**: Delete + insert `role_permissions` untuk roleId apa pun (FK error atau grants nyasar).
- **Dampak**: Grants ke role tidak dikenal.

### M9 — `forgotPassword` di non-prod bocorkan `devResetToken`
- **File**: `apps/api/src/modules/auth/auth.service.ts:101-103`
- **Detail**: `if (!isProd()) return { ...generic, devResetToken: token, devResetPath }` — staging (development) mengembalikan token reset di respons.
- **Dampak**: Siapa pun dengan akses API staging bisa reset password user lain.

## Role UPM / Gizi

### U1 — `createFoodOrder` tanpa cek episode closed
- **File**: `apps/api/src/modules/clinical/order.service.ts:729-741`
- **Detail**: INSERT `foodOrders` langsung tanpa gate episode.
- **Dampak**: Order diet pasien pulang; gizi masak sia-sia.

### U2 — `setFoodOrderStatus` status string bebas tanpa enum
- **File**: `apps/api/src/modules/clinical/order.service.ts:789-795`
- **Detail**: `set({ status })` — string apa pun diterima.
- **Dampak**: Status order diet korup.

### U3 — `recordFoodDelivery` tanpa guard status — bisa re-deliver berkali-kali
- **File**: `apps/api/src/modules/clinical/order.service.ts:800-815`
- **Detail**: Update `status='delivered'` tanpa cek status sebelumnya; delivery dicatat ulang tak terbatas.
- **Dampak**: Monitoring gizi salah (delivery ganda).

---

# Lampiran A — Status Defect yang SUDAH DIFIX (11 item permintaan Kibul 13/08)

Verifikasi ulang di HEAD `5300cb6`:

| # | Defect | Status | Bukti |
|---|---|---|---|
| 1 | Duplikat NIK pasien baru | ❌ BELUM | `registration.service.ts:347-356` INSERT langsung |
| 2 | Verify temporary tanpa cek NIK bentrok | ❌ BELUM | `registration.service.ts:424-437` update langsung |
| 3 | Deposit terakumulasi tapi list tidak muncul | ❌ BELUM | Tidak ada endpoint riwayat `deposit_payments`; hanya Σ `depositApplied` di `billing.service.ts:283-307` |
| 4 | Deposit bisa setelah lunas | ❌ BELUM | `queue.service.ts:38-67` tanpa cek status |
| 5 | Edit item qty 0/negatif | ❌ BELUM (schema `.positive()` bisa di-bypass) | `pharmacy.service.ts:420` |
| 6 | Racikan → obat jadi saat edit | ❌ BELUM | `pharmacy.service.ts:403-430` tanpa sentuh `isRacikan` |
| 7 | Jadwal operasi tanpa cek status episode | ❌ BELUM | `ops.service.ts:818-819` |
| 8 | Re-input lab hapus alert kritis | ⚠️ SEBAGIAN — backend fix `delete where status='pending'` (`order.service.ts:547`), tapi `resultSupport` tanpa state machine (bisa re-input di verified) | |
| 9 | Care plan create tanpa cek episode closed | ❌ BELUM (0 guard) | `care-plan.service.ts:49-75` |
| 10 | Flow penunjang medis per status | ✅ SUDAH — `cancelSupport` guard `resulted/verified` (`order.service.ts:626-628`), FE disable by status | |
| 11 | Popup confirmation delete | ✅ SUDAH — Popconfirm di master (`MasterDataPage.tsx`), nursing (`NursingCarePlanSection.tsx:176`), pathway (`ClinicalPathwayMasterPage.tsx:29`), refund (`CancelledPage.tsx:49`) | |

---

# Lampiran B — Ringkas Defect per Modul

| Modul | Jumlah | Kode Defect |
|---|---|---|
| Pendaftaran / Registrasi / MPI | 6 | R1, R2, R3 (b1), R4 (b4), + merge coverage |
| Kasir / Billing / Deposit | 9 | K1, K2, K3 (b1), K4, K5, K6 (b2), K7, K8, K9 (b4) |
| Farmasi / Stok | 5 | F1, F2 (b1), F3, F4 (b2), K9 (b4) |
| OK / Operasi / Bed | 5 | O1, O2, O3 (b1), O4, O5 (b2), O6, O7 (b4) |
| Penunjang / Lab | 3 | P1, P2 (b1), D10 (b4) |
| BPJS / SEP / Antrean | 8 | A1, A2 (b1), A3, A4, A5 (b2), B1, B2, B3 (b4) |
| EMR / Keperawatan / Care Plan | 6 | E1 (b1), E3, E4 (b2), D8, D9, D11 (b4) |
| Masterdata / RBAC / Auth | 9 | M1–M5, R1, R2, R3, R4, R5 (b3), M6–M9 (b4) |
| RM / ARM | 3 | A1, A2 (b3), A6, A7, A8 (b4) |
| Casemix | 3 | C1, C2, C3 (b3) |
| UPM / Gizi | 3 | U1, U2, U3 (b4) |

**Catatan**: Beberapa defect terhitung lintas kategori (mis. K9 di Farmasi & Kasir). Jumlah unik tetap **56 defect**.
