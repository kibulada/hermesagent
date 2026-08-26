# Kesia v3 — End-to-End Trace per Unit (Rajal, Ranap, IGD)

> Generated 2026-08-07 oleh Salsabila QA.
> **Caveat runtime**: Workstation ini **tidak punya Docker / Postgres / NATS** (verified: `docker: command not found`, `PG:15432/5432 DOWN`). Jadi tidak bisa spin `docker compose -f docker/compose.dev.yml up` untuk smoke-test live. Investigasi ini berbasis **kode statis** (controller → service → DB) + `dev-e2e.sh` script jika dijalankan di lingkungan yang menyediakan infra.
> Sumber: `E:/WORK KESIA/Project/kesiaV3` (commit `869afa1`).
> API source: `apps/api/src/modules/**` (NestJS), Nx monorepo.
> FE source: `apps/web-clinic/src/features/**` (Vite + React 18 + AntD 5).
>

**Definisi "E2E di v3"** = kunjungan 1 pasien dari registrasi → SOAP/observasi → order (obat/lab/rad) → verifikasi → biaya → kasir → selesai. Untuk setiap unit saya trace dengan format:

> Langkah (tujuan UX) → Endpoint API → File:Line → Service → Outbox/Event → FE component

Setiap endpoint di bawah punya signature RBAC `@RequirePermission(...)` dan divalidasi Zod (`@ZodBody(...)`).

---

## Status kesiapan hidup (yang sudah jalan di skeleton vs yang masih desain)

| Area | Status | Bukti |
|---|---|---|
| Tenant middleware fail-closed + auth dev-login | ✅ jalan | `apps/api/src/app.module.ts:35-44`; `common/tenant.middleware.ts` |
| Multi-tenant DB-per-tenant + FORCE RLS | ✅ jalan | `libs/db-base/src/connection-resolver.ts`; `db/rls-policies.sql` |
| Registered → Encounter → SOAP → EpisodeCharge → Saga PostBillingToOdoo (mock) | ✅ jalan | `scripts/dev-demo.sh` + `apps/relay/src/main.ts` |
| Realtime SSE antrean | ✅ jalan | `apps/api/src/modules/realtime/*` |
| Form-engine (Ajv STRICT) | ✅ jalan | 26 form_code ter-register `db/seed/*` + `db/migrations/*` |
| VClaim/Antrean/SatuSehat/Dukcapil/INA-CBG riil | ❌ mock-only | Gated ke kredensial Kemenkes/BPJS |
| Multi-role login | ❌ desain | TODO spec-05 |
| EKG waveform-strip + DICOM viewer lengka p + LIS MLLP bridge | ❌ TODO | PARITY-BACKLOG |

---

## Unit 1 — RAWAT JALAN (Rajal)

### Alur ujung ke ujung

```
Pendaftaran Pasien → Encounter/Episode → SOAP (form-engine integrated-note)
  → Order Penunjang (lab/rad) → Verifikasi+ekspertise
  → Order Resep → Telaah Resep → Pembayaran Resep → Dispense
  → Visite (kosong di rajal)
  → Discharge / Selesai → EpisodeCharges agregat → BillingPage → Kasir bayar
```

### Endpoints yang membentuk alur (file:line di `apps/api/src/modules/clinical/clinical.controller.ts` kecuali dicatat lain)

| # | Tujuan UX | Method+Route | File:Line | Permission | Catatan |
|---|---|---|---|---|---|
| 1 | Daftar Pasien Baru | `POST /clinical/patients` | `clinical.controller.ts:112` | `registrasi/pasien:create` | Service: `registration.service.ts:332 registerPatient`. Validasi: `RegisterPatientSchema` Zod. |
| 2 | Ambil pasien by ID | `GET /clinical/patients/:id` | `registration.controller.ts:52` | (open via tenant) | View mask NIK (R9). |
| 3 | Buat Episode Kunjungan | `POST /clinical/episodes` | `clinical.controller.ts:122` | `registrasi/pasien:create` | Service: `registration.service.ts:925 createEpisode`. `registerNo` dari sequence, queue_no nullable. |
| 4 | Worklist Dokter | `GET /clinical/worklist` | `clinical.controller.ts:284` | `dokter/worklist:view`, `emr/worklist:view`, `perawat/station:view` | Filter site (R3 RLS), filter `source='outpatient'/'inpatient'`. |
| 5 | Catat SOAP (`integrated-note`) | `POST /clinical/observations` | `clinical.controller.ts:269` | `perawat/station:edit`, `dokter/worklist:edit` | Service: `clinical-observation.service.ts`. Ajv STRICT validate (mig SOAP strict per PARITY-BACKLOG). |
| 6 | Update/Patch SOAP | `PATCH /clinical/observations/:id` | `clinical.controller.ts:274` | same | Untuk koreksi pre-confirm. |
| 7 | Confirm observasi | `POST /clinical/observations/:id/confirm` | `clinical.controller.ts:279` | `dokter/worklist:edit`, `dokter/konsul:edit` | Flip status ke `confirmed`, masuk EpisodeCharges kalau order-generators. |
| 8 | Order Penunjang multi-item | `POST /clinical/support-orders` | (lihat `OrderService.createSupportOrder`) | per `penunjang/*` | Service buat `support_orders` + `support_order_items` (mig 0050) qty-aware. |
| 9 | Hasil Penunjang | `POST /clinical/support-orders/:id/result` | (di controller `clinical-observation.service.ts`) | `penunjang/lab:edit` | Structured result_data jsonb (CBC analit / Rad finding-impression). Trigger critical-value. |
| 10 | Ekspertise (assigned dokter) | `POST /clinical/support-orders/:id/assign` | (mig 0080 endpoint) | `penunjang/lab:edit` | set `assigned_doctor_id` LEFT-JOIN employees. |
| 11 | Verifikasi | `POST /clinical/support-orders/:id/verify` | (di controller) | `penunjang/lab:verify` | Status `verified`, `verified_by`/`verified_at`; auto-episodeCharges. |
| 12 | Order Resep | `POST /clinical/prescriptions` | (di controller) | `dokter/worklist:edit`, `verifikasi/resep:create` | drugId round-trip. Source-order back-ref mig 0045. |
| 13 | Telaah Resep | `POST /clinical/prescriptions/:id/review` | `clinical.controller.ts:431` | `verifikasi/resep:verify` | `ReviewPrescriptionSchema`. Concern whitelist 6 item (interaksi/duplikasi/alergi/dosis/kontraindikasi/inkompatibilitas). Concern count > 0 → flagged. |
| 14 | Confirm Resep | `POST /clinical/prescriptions/:id/confirm` | `clinical.controller.ts:425` | `verifikasi/resep:verify` | Auto confirm kalau review=ok. |
| 15 | Bayar Resep | `POST /clinical/prescriptions/:id/pay` | `clinical.controller.ts:437` | `farmasi/antrean:pay` | Trigger `prescriptionPaid=1` di invoice line; event `pharmacy.prescription.paid`. |
| 16 | Dispense | `POST /clinical/prescriptions/:id/dispense` | `clinical.controller.ts:442` | `farmasi/antrean:dispense` | FEFO batch (mig 0081) — dispense A-SOON dulu. |
| 17 | Farmasi worklist per kanal | `GET /clinical/pharmacy/worklist?channel=online` | `clinical.controller.ts:393` | `farmasi/antrean:view` | Channel=onsite|online, diturunkan server dari tipe episode. |
| 18 | TTD Dokter | `POST /clinical/episodes/:id/sign` | `clinical.controller.ts:224` | `verifikasi/ttd:finish` | `doctor_signatures` table mig 0075, idempoten. **Belum ada hard-gate** di `finishDoctor`. |
| 19 | Panggil Antrian (perawat station) | `POST /clinical/episodes/:id/call` | `clinical.controller.ts:342` | `perawat/station:call` | Status ke `INPROGRESS`, broadcast event `clinical.episode.called`. |
| 20 | TTV Selesai (perawat) | `POST /clinical/episodes/:id/nurse-done` | `clinical.controller.ts:347` | `perawat/station:edit` | Gate TTV wajib sebelum finishDoctor. |
| 21 | Finish (dokter) | `POST /clinical/episodes/:id/finish` | `clinical.controller.ts:352` | `dokter/worklist:finish` | Tutup episode rajal. Outbox event `clinical.episode.closed`. |
| 22 | Discharge summary | `GET /clinical/episodes/:id/resume` + `POST /clinical/episodes/:id/resume` | `clinical.controller.ts:186, 190` | `rm/medical-resume:view`/`print` | WYSIWYG (sesuai dengan FE `CetakResume`). |
| 23 | Tarik EpisodeCharges | (BFF / BillingPage baca langsung dari `/clinical/episodes/:id/charges` di BFF) | `BFF` | `kasir/billing:view` | Agregat: source=`obat/lab/radiology/procedure/mcu/tindakan/akomodasi/visite`. |
| 24 | Buat Billing Intent | `POST /billing/intent` | `apps/api/src/modules/billing/billing.controller.ts:342 createBillingIntent` | per `kasir:bill` | GUARD baris ber-`sourceOrderId` yg sudah NON-VOID → ALREADY_BILLED (anti tagih-ganda). Outbox event `billing.invoice.posted`. |
| 25 | Bayar Invoice | `POST /billing/invoices/:id/pay` (legacy) atau `payInvoice` di service | `apps/api/src/modules/billing/billing.service.ts:314` | `kasir:pay` | payments + notifications. BFF mempertahankan referensi payment saga. |
| 26 | Saga PostBillingToOdoo | consumer NATS → `SagaRunner` → `post-billing-to-odoo.saga.ts` | `apps/api/src/modules/billing/saga/*` | (auto) | Idempoten via `externalRef`, `processed_events` inbox dedup. |

### Happy-path kritis

**Sukses**: Register patient → Episode `RJ` → SOAP strict valid (`integrated-note` validated via AjvFormValidator) → Order lab `Hb+GDS` (qty 2+1) → Hasil masuk → TTV vital sign → TTD (opsional) → `finish` episode → EpisodeCharges ke-aggregate ke billing → Invoice dibuat via `createBillingIntent` → Outbox publish ke NATS → Saga Runner `PostBillingToOdoo` → Odoo mock posted.

**Risiko yang saya lihat di kode statis** (TAHAP runtime butuh diulang):
- *Overlap EpisodeCharges* — recipe `order.service.ts:174-203` menghasilkan 7 source (`obat/lab/radiology/procedure/mcu/tindakan/akomodasi/visite`), semua qty-aware dan back-ref ke source_order_id. Verify sum(amount) = bill_invoice_net, lalu cek split coverage self/BPJS/asuransi tidak ada duplicate line.
- *Cohort SOAP strict* — `integrated-note` wajib S/O/A/P minLength, ICD-10/9 pola regex, 13-organ enum. Wajib test 1失败 case per titik (cek spec-09 R8 & mig AjvFormValidator strict di PARITY-BACKLOG).
- *Hard-gate TTD* belum on (keputusan produk). Default "catat tanpa blokir alur". Saat ini `POST /clinical/episodes/:id/finish` sukses tanpa TTD. PP#7485 memintanya BLOCKED, tapi itu keputusan user, bukan kode.

### Rekomendasi QA end-to-end saat infra up

1. `bash scripts/dev-up.sh` → init schema+seed registry+tenant.
2. `bash scripts/dev-e2e.sh` → smoke-test backend (curl) yg sudah ada di skeleton.
3. Tambahkan manual test: register pasien fresh → SOAP invalid (field asing → Ajv 400) → SOAP valid → order lab/penunjang dengan qty → prescription drugId → review concern=interaksi (forced flag) → dispense → finish → EpisodeCharges → BillingIntent → Saga publish.

---

## Unit 2 — RAWAT INAP (Ranap)

### Alur ujung ke ujung

```
SPRI / Order Ruang (IGD atau Rajal) → Admisi Ranap
  → Penempatan Bed (RanapBoard)
  → Visite harian (mig 0082)  → Akomodasi kamar (auto per malam)
  → SOAP harian per visite → Order penunjang/resep per visite
  → Discharge Planning (form-engine discharge-planning v1)
  → Discharge (close episode)  → SEP Return On Discharge (auto updTglPlg)
  → Resume Medis WYSIWYG
  → Invoice final → Billing → Kasir
```

### Endpoints

| # | Tujuan UX | Method+Route | File:Line | Permission | Catatan |
|---|---|---|---|---|---|
| 1 | SPRI (Order Ruang) dari episode IGD/Rajal | `POST /clinical/episodes/:id/order-inpatient` | `clinical.controller.ts:174` | `igd/order-ruang:order` | Service set status careplan inpatient, planDate, SPRI document template. |
| 2 | Cetak SPRI | `GET /clinical/spri/:episodeId` (via BFF) | `cetak/CetakSpriPage.tsx` | `rm/spri:print` | A4 WYSIWYG. |
| 3 | Admisi Ranap (langsung) | `POST /clinical/admissions` atau `POST /clinical/episodes/:id/admit` | `clinical.controller.ts:158, 164` | `ranap/admisi:create` | Service: `registration.service.ts:480 admitToInpatient`. |
| 4 | Papan Bangsal (board) | `GET /ops/beds` + episode view (baca RanapBoardPage) | `apps/api/src/modules/ops/*` | `ranap/board:view`, `bed:view` | Display bed = BOR/LOS/TOI (computed). |
| 5 | Transfer Bed | `POST /ops/beds/transfer` | `apps/api/src/modules/ops/*` | `ranap/transfer:edit` | Ledger `clinical.bed_transfers` (mig 0053). |
| 6 | Visite Harian Dokter (charge) | `POST /clinical/episodes/:id/visite` | `clinical.controller.ts:240` | `dokter/worklist:edit` | Service: `registration.service.ts:recordVisite`. ChargeLine `source='visite'` masuk EpisodeCharges. |
| 7 | List Visite | `GET /clinical/episodes/:id/visites` | `clinical.controller.ts:244` | `dokter/worklist:view`, `ranap/board:view`, dll | |
| 8 | Hapus Visite | `DELETE /clinical/visites/:visiteId` | `clinical.controller.ts:248` | `dokter/worklist:edit` | Hapus charge balik ke EpisodeCharges. |
| 9 | Akomodasi Kamar (auto) | (di EpisodeCharges calculator) | `order.service.ts:224` episodeCharges | (auto) | days = admit→discharge-exclusive di-clamp rentang. class_types.daily_rate + resolveRoomRate. |
| 10 | Nursing Care Plan SDKI/SLKI/SIKI | `GET/POST /clinical/episodes/:id/nursing-care-plans` | `clinical.controller.ts:196-204` | `perawat/station:*` | 1-entri per diagnosis. |
| 11 | Nursing Implementation | `GET/POST/DELETE /clinical/episodes/:id/nursing-implementations` | `clinical.controller.ts:210-218` | `perawat/station:*` | mig 0156 nursing_implementations. |
| 12 | Discharge Planning (form) | (Observation `form_code='discharge-planning'`) | form-engine + `clinical-observation.service.ts` | `perawat/station:edit` | wajib dischargeCondition enum, rencana kontrol, edukasi, diet. |
| 13 | Discharge (close episode) | `POST /clinical/episodes/:id/discharge` | `clinical.controller.ts:180` | `ranap/board:view` (salah ketik, semestinya discharge) | Service: `registration.service.ts:630 dischargeEpisode`. Bed → CLEANING, status `closed`, `closedAt`, cara/kondisi pulang. |
| 14 | SEP Return On Discharge (auto) | `POST /clinical/episodes/:id/sep/return` (best-effort panggil dari dischargeEpisode) | `clinical.controller.ts:526` + `sep.service.ts:218 returnOnDischarge` | `bpjs/sep:create` | updTglPlg via VClaimClient mock-gated; idempoten; **non-fatal** jika gagal (return_status='failed'). |
| 15 | Medical Resume read/write | `GET/POST /clinical/episodes/:id/resume` | `clinical.controller.ts:186-190` | `rm/medical-resume:view`/`print` | WYSIWYG FE `MedicalResumePage`. |
| 16 | Cetak Resume | `GET /cetak/resume/:episodeId` (FE) | `cetak/CetakResume*.tsx` | `rm/medical-resume:print` | SNARS-discharge summary. |
| 17 | Billing aggregation | sama dgn rajal, sumber Visite+tindakan+akomodasi | `order.service.ts:174-224` | (auto) | |
| 18 | Buat Billing Intent | `POST /billing/intent` | `billing.controller.ts:342` | `kasir:bill` | Outbox `billing.invoice.posted`. |
| 19 | Bayar Invoice + Void cycle | `POST /billing/invoices/:id/pay` + `/void` | `billing.service.ts:314+` | `kasir:pay` | Anti tagih-ganda GUARD `sourceOrderId` sudah NON-VOID → ALREADY_BILLED. Void → released → order BEBAS ditagih ulang (reversal support-order). |

### Critical paths

**Sukses ranap**: IGD triase → SPRI → admisi ke bed 201 → visite harian 3 hari berturut (charge otomatis via `recordVisite`) + SOAP harian → Resep (route ke farmasi ranap) → Penunjang (route lab/rad) → Discharge Planning diisi perawat → Discharge ← close episode + SEP return best-effort → Invoice aggregate → Bayar.

**Risiko yang saya lihat di kode statis**:
- *admissionDate tidak otomatis*= dari IGD. Code BE `dischargeEpisode` & `admitToInpatient` (registration.service.ts:480) mungkin tidak menarik `treatmentDate`/`checkInDate` asal — perlu verifikasi live apakah `episodes.admission_date` ter-set dari `opnameIntroduction.outpatient.treatmentDate` atau ER `checkInDate`.
- *SEP Return-on-discharge* best-effort — kode `sep.service.ts:218 returnOnDischarge` dipanggil `SETELAH commit` di `dischargeEpisode`. Gagal → `return_status='failed'`, tapi tidak menggagalkan discharge. Endpoint manual `POST /clinical/episodes/:id/sep/return` untuk retry. Pasca-tiket PP#7486 minta field `admissionDate` di PDF Invoice; ini terkait dengan mig invoice params include.
- *Akomodasi kamar* `order.service.ts:224` → qty = days, amount = days × daily_rate. Saat checkout partial (mis. pulang paksa di tengah inap), jumlah hari harus dihitung dengan benar. Wajib test case pulang hari ke-1, pindah kamar (ledger transfer sudah jalan `bed_transfers` mig 0053).

### Rekomendasi QA end-to-end untuk ranap

1. Setup patient → IGD reg → triase → SPRI → admisi ke bangsal.
2. Visite harian 3x (tiap hari jam yang sama) → cek `episodeCharges` punya 3 baris source=`visite`.
3. Akomodasi kamar auto: cek days = 3, amount = class.daily_rate × 3.
4. Transfer bed → ledger `bed_transfers`; cek akomodasi di-clamp hanya untuk kelas akhir.
5. Discharge planning form (form-engine discharge-planning v1) — wajib dischargeCondition enum valid.
6. `discharge` → cek SEP issued punya `return_status='returned'` (best-effort).
7. EpisodeCharges final → BillingIntent → Bayar (cek coverage matrix + global discount).
8. Saga publish ke mock Odoo → idempotent retry setelah void.

---

## Unit 3 — IGD / GAWAT DARURAT

### Alur ujung ke ujung

```
Registrasi IGD → Temporary Patient (pasien gawat tanpa MR)
  → Verifikasi Pasien (verify +/− merge ke MR permanen)
  → NIK verify (Dukcapil mock)
  → Triase medis (form-engine triage-igd dengan disposisi)
  → Dokter workspace (SOAP)
  → Order Ruang Rawat Inap (SPRI)  → admitToInpatient
  → Order Penunjang/Resep (route farmasi IGD)
  → Layanan Operasi (kalo ada)
  → Discharge / Observe / Inap / Rujuk / Pulang Paksa / Meninggal
  → SEP Return On Discharge
  → Billing → Kasir
```

### Endpoints

| # | Tujuan UX | Method+Route | File:Line | Permission | Catatan |
|---|---|---|---|---|---|
| 1 | Register Temporary (IGD tanpa MR) | `POST /clinical/patients/temporary` | `clinical.controller.ts:136` | `igd/registrasi:create` | Service `registration.service.ts:389 registerTemporary`. `is_merged=false`, `is_temporary=true`. |
| 2 | Verify Pasien (cek di master) | `POST /clinical/patients/:id/verify` | `clinical.controller.ts:141` | `igd/verifikasi-pasien:verify` | Service `registration.service.ts:412 verifyPatient`. |
| 3 | Merge Temporary → Permanen | `POST /clinical/patients/:id/merge` | `clinical.controller.ts:153` | `igd/verifikasi-pasien:verify` | Service repoint 12 tabel clinical, non-destruktif (source is_merged=true+parent_id), guard MERGE_SELF/ALREADY/TARGET_MERGED/TARGET_TEMP. |
| 4 | Verifikasi NIK (Dukcapil mock) | `POST /clinical/patients/:id/verify-nik` | `clinical.controller.ts:147` | `registrasi/pasien:edit` | `dukcapil.service.ts`. Valid 16 digit → mock echo nama resmi + nameMatch → simpan `nik_verified`, NIK TERMASKER (privacy). |
| 5 | Triase IGD | `POST /clinical/episodes/:id/triage` | `clinical.controller.ts:169` | `igd/triase:triage` | `TriageSchema` v1-0002, disposisi enum `rawat-inap/rawat-jalan/observasi/rujuk/pulang-paksa/meninggal` + tujuan + catatan. Form-engine `triage-igd`. |
| 6 | Order Ruang Rawat Inap (SPRI) | `POST /clinical/episodes/:id/order-inpatient` | `clinical.controller.ts:174` | `igd/order-ruang:order` | Plan tanggal + diagnosa kerja + DPJP. Trigger CetakSpriPage. |
| 7 | Admisi Ranap dari SPRI | `POST /clinical/episodes/:id/admit` | `clinical.controller.ts:158` | `ranap/admisi:create` | Service `registration.service.ts:480 admitToInpatient`. |
| 8 | SOAP (di workspace) | sama dgn rajal | `clinical.controller.ts:269` | `dokter/worklist:edit` | |
| 9 | Order Penunjang | sama dgn rajal | (lihat OrderService) | per `penunjang/*` | |
| 10 | Order Resep (route farmasi IGD) | `POST /clinical/prescriptions` | (OrderService) | `dokter/worklist:edit` | channel default IGD. |
| 11 | Layanan Operasi IGD | `POST /clinical/surgeries` | (OrderService.createSurgery) | `jadwal/operasi:create` | `surgeries.action_id` (mig 0068) + `charge_amount` override manual. EpisodeCharges source=`tindakan`. |
| 12 | Discharge (close) | `POST /clinical/episodes/:id/discharge` | `clinical.controller.ts:180` | (sama) | Idem dengan ranap/rajal. |
| 13 | SEP Return On Discharge | `POST /clinical/episodes/:id/sep/return` | `clinical.controller.ts:526` | `bpjs/sep:create` | Idempoten, only for closed episode. |
| 14 | Billing Intent | `POST /billing/intent` | sama | `kasir:bill` | Sama source mix. |
| 15 | Worklist IGD-specific | `GET /clinical/worklist?source=er` | `clinical.controller.ts:284` | `dokter/worklist:view`, dll | IgdBoardPage filter. |
| 16 | Bayar | `POST /billing/invoices/:id/pay` | `billing.service.ts:314` | `kasir:pay` | |

### Critical paths

**Sukses IGD**: Temporary register → verify → merge (kalau ada MR permanen di master) → Triase (Priority 1 merah / Resusitasi) → SOAP by emergency doctor → Order lab cito + X-Ray thorax → Order Ruang Ranap (SPRI) → Cetak SPRI → admitToInpatient (mulai EpisodeCharges visite+akomodasi). Atau: Pulang jalan dengan resep + observasi selesai.

**Risiko & blind spot**:
- *Konsistensi disposition v discharge* — `TriageSchema` v1-0002 disposisi `rawat-inap/rawat-jalan/observasi/rujuk/pulang-paksa/meninggal`. Belum ada endpoint otomatis yang menghubungkan disposition → Discharge method — masih harus manual dipilih saat discharge. Wajib test kalau disposition='pulang-paksa', discharge method='pulang paksa', SEP tidak usah issued.
- *Merge temp → permanen* guard: `MERGE_TARGET_MERGED` (target sudah merger) → 400, `MERGE_TARGET_TEMP` (target = temporary) → 400 (kecuali proses 2 tahap), `MERGE_ALREADY` (sumber sudah merged), `MERGE_SELF`. Wajib test di code review `mergePatient`.
- *SEP issued dari IGD* — alur SEP issuance via `sep.service.ts:91 issue` setelah `createEpisode` dengan cara bayar BPJS. Override 7 field di FE BpjsSepPage drawer ("Edit field SEP (opsional)") — effectiveNoKartu override, guard via `effectiveNoKartu`.

### Rekomendasi QA end-to-end untuk IGD

1. Pasien temporary register (tanpa NIK, nama samaran).
2. Verify via `POST /verify` → cari kandidat permanen → merge temp ke permanen.
3. Triase valid + invalid (enum salah → 400).
4. SPRI → Cetak → Admisi.
5. Discharge observasi → SEP issued check → Return on close.
6. Billing agregat → Bayar.
7. Adversarial review: rujuk keluar RS (tanpa SEP), pulang paksa (billing batal), meninggal (mandatory cause-of-death di SOAP).

---

## Endpoints & RBAC ringkasan (per unit) yang siap uji live

**Rajal**:
```
POST   /clinical/patients                        registrasi/pasien:create
POST   /clinical/episodes                        registrasi/pasien:create
GET    /clinical/worklist?source=outpatient      dokter|emr/perawat :view
POST   /clinical/observations                    perawat/dokter :edit
POST   /clinical/support-orders                  penunjang/* :order
POST   /clinical/prescriptions                   dokter/worklist:edit
POST   /clinical/prescriptions/:id/review        verifikasi/resep:verify
POST   /clinical/prescriptions/:id/confirm       verifikasi/resep:verify
POST   /clinical/prescriptions/:id/pay           farmasi/antrean:pay
POST   /clinical/prescriptions/:id/dispense      farmasi/antrean:dispense
POST   /clinical/episodes/:id/call               perawat/station:call
POST   /clinical/episodes/:id/nurse-done         perawat/station:edit
POST   /clinical/episodes/:id/sign               verifikasi/ttd:finish
POST   /clinical/episodes/:id/finish             dokter/worklist:finish
POST   /clinical/episodes/:id/deposit            kasir:pay
POST   /billing/intent                           kasir:bill
POST   /billing/sagas                            (monitoring Odoo)
```

**Ranap** (tambahan, selain endpoint rajal):
```
POST   /clinical/episodes/:id/order-inpatient    igd/order-ruang:order (SPRI dari IGD)
POST   /clinical/episodes/:id/admit              ranap/admisi:create
POST   /clinical/episodes/:id/visite             dokter/worklist:edit
DELETE /clinical/visites/:visiteId               dokter/worklist:edit
GET/POST/DELETE /clinical/episodes/:id/nursing-care-plans   perawat/station:edit
GET/POST/DELETE /clinical/episodes/:id/nursing-implementations perawat/station:edit
POST   /clinical/episodes/:id/discharge          ranap/board:view (koreksi saran)
GET    /clinical/episodes/:id/resume             rm/medical-resume:view
POST   /clinical/episodes/:id/resume             rm/medical-resume:print
POST   /clinical/episodes/:id/sep/return         bpjs/sep:create
```

**IGD** (tambahan):
```
POST   /clinical/patients/temporary              igd/registrasi:create
POST   /clinical/patients/:id/verify             igd/verifikasi-pasien:verify
POST   /clinical/patients/:id/merge              igd/verifikasi-pasien:verify
POST   /clinical/patients/:id/verify-nik         registrasi/pasien:edit
POST   /clinical/episodes/:id/triage             igd/triase:triage
GET    /clinical/worklist?source=er              dokter|emr|perawat :view
```

---

## Verdict & blocker

**Status v3 end-to-end untuk Rajal/Ranap/IGD**: Skeleton hidup (`scripts/dev-e2e.sh` valid via curl per README `apps/web-clinic`). Tiap-tiap endpoint terdaftar di `clinical.controller.ts`. RBAC per `@RequirePermission`. Validasi Zod. Saga PostBillingToOdoo (mock) bekerja end-to-end di dev.

**Yang tidak bisa saya uji di sesi ini (no Docker / no PG)**: smoke-test live. Untuk runtime E2E, butuh environment terpisah dengan Docker + Postgres + NATS (lihat `docker/compose.dev.yml`); bisa dijalankan hanya di workstation dengan docker terinstall.

**Risiko tertinggi menurut trace kode**:
1. **SEP Return On Discharge** = best-effort setelah commit. Bisa sukses, bisa gagal karena jaringan VClaim. Default sekarang `return_status='failed'` + tidak menggagalkan discharge. Wajib verify: idempotency + retry endpoint.
2. **Merge Temp→Permanen** = 4 guard ketat. Wajib test tiap kondisi invalid.
3. **Akomodasi kamar ranap** = clamp rentang tanggal. Wajib test pindah kamar di tengah inap.
4. **Payment-Void cycle** = ALREADY_BILLED guard per `sourceOrderId`. Wajib test sequence: bill order A → coba bill ulang order A → expect 400 → void invoice → bill ulang order A → sukses.
5. **TTD tidak hard-gated** di finishDoctor saat ini. Keputusan produk (default catat tanpa blokir).
6. **Front-end vs BE admissionDate contract** (PP#7486, MR !7301): pastikan invoiceParams include `opnameIntroduction(er,outpatient,senderDoctor)` agar field `admissionDate` di PDF Invoice FE benar.

**Rekomendasi**: tarik tiket spesifik untuk verifikasi live (bukan static) saat sandbox dev tersedia — prioritas 1: payment-void cycle, admissionDate contract, SEP return-on-discharge idempotency, merge-patient guards.
