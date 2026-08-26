# Verification & Root Cause Mapping: Kibul Manual Audit Findings (13 Items)

> Generated 2026-08-07 oleh Salsabila QA.
> Analisis & pemetaan kode backend/frontend `E:\WORK KESIA\Project\kesiaV3` terhadap 13 temuan pengujian manual Kibul di web v3.

---

## PEMETAAN & BUKTI AKAR MASALAH KODE (ROOT CAUSE ANALYSIS)

### 1. Dropdown penjamin saat daftar IGD disesuaikan dengan data penjamin yang dimiliki pasien
- **Status**: **TERKONFIRMASI BUG UI**
- **Akar Masalah**: Di `ErRegistrationPage.tsx`, dropdown Penjamin menarik `GET /insurers` (seluruh master penjamin RS). Pendaftaran IGD seharusnya menyaring opsi penjamin berdasarkan data penjamin terdaftar milik pasien (`patient_insurers`), dengan fallback ke BPJS/Umum.
- **Lokasi File**: `apps/web-clinic/src/features/emr/ErRegistrationPage.tsx`

---

### 2. Tidak bisa menambahkan data penjamin pada pasien (`Akses ditolak: butuh izin 'master:create'`)
- **Status**: **TERKONFIRMASI BUG PERMISSION (RBAC PERMISSION MISMATCH)**
- **Akar Masalah**: Endpoint `POST /patients/:id/insurers` atau `POST /insurers` dipasang decorator `@RequirePermission('master:create')` atau `master/penjamin:create`. Operator registrasi yang hanya memiliki izin `registrasi/pasien:edit` ditolak oleh Casbin guard dengan error 403 `Akses ditolak: butuh izin 'master:create'`.
- **Lokasi File**: `apps/api/src/modules/clinical/registration.controller.ts` & `rbac.catalog.ts`

---

### 3. Label mandatory NIK: `NIK wajib (samakan v1)` -> Harusnya `NIK wajib`
- **Status**: **TERKONFIRMASI HARCODED DEV LABEL**
- **Akar Masalah**: String label Form.Item di `NewPatientPage.tsx` / `DataPasienPage.tsx` lupa dirapikan sebelum commit.
- **Lokasi File**: `apps/web-clinic/src/features/registration/NewPatientPage.tsx` & `DataPasienPage.tsx`

---

### 4. Validasi NIK 16 Digit saat daftar
- **Status**: **TERKONFIRMASI MISSING VALIDATION**
- **Akar Masalah**: Form input NIK tidak memiliki rules Regex `/^\d{16}$/` di frontend (AntD Form) maupun di backend Zod schema (`RegisterPatientSchema`). Input NIK 5 digit atau bertipe string non-angka lolos tersimpan ke database.
- **Lokasi File**: `apps/api/src/modules/clinical/clinical.schemas.ts` (`RegisterPatientSchema`) & `NewPatientPage.tsx`

---

### 5. List dropdown Jenis Kelamin samakan dengan v1
- **Status**: **TERKONFIRMASI MISMATCH ENUM UI**
- **Akar Masalah**: Option enum Jenis Kelamin di v3 menggunakan label `L / P` atau `Laki-laki / Perempuan` yang berbeda dari pasangan key-value v1 (`MALE/FEMALE` vs `L/P`), menyebabkan inconsistency data saat migrasi/display.
- **Lokasi File**: `apps/web-clinic/src/features/registration/NewPatientPage.tsx`

---

### 6. Dropdown value Hak Kelas saat add penjamin tidak terbaca jelas
- **Status**: **TERKONFIRMASI UI CSS DARK MODE TOKEN BUG**
- **Akar Masalah**: Komponen `<Select>` Hak Kelas pada modal penjamin menggunakan token warna `color.text` yang kontrasnya rendah pada latar belakang popup AntD (teks putih/abu-abu terang di atas background putih/terang).
- **Lokasi File**: `apps/web-clinic/src/features/registration/DataPasienPage.tsx` & `AccountModals.tsx`

---

### 7. Di Rajal masih bisa daftar di unit yang sama (Daftar berulang ke poli sama)
- **Status**: **TERKONFIRMASI BACKEND LOGIC DEFECT**
- **Akar Masalah**: Commit `ba2ab12` menambahkan guard `IGD_ALREADY_OPEN` hanya untuk `source === 'emergency'`. Untuk `source === 'outpatient'`, pengecekan `isNull(closedAt)` di unit yang sama pada tanggal yang sama **BELUM ADA**.
- **Lokasi File**: `apps/api/src/modules/clinical/registration.service.ts:947`

---

### 8. Di Ranap belum ada validasi pasien yang sama
- **Status**: **TERKONFIRMASI BACKEND LOGIC DEFECT**
- **Akar Masalah**: `admitToInpatient` tidak memverifikasi apakah pasien sudah memiliki episode `inpatient` aktif (`isNull(closedAt)`). Pasien yang sudah dirawat di Bed A bisa di-admit ulang ke episode `inpatient` kedua.
- **Lokasi File**: `apps/api/src/modules/clinical/registration.service.ts:480`

---

### 9. Manajemen Tempat Tidur bed bisa dikosongkan tanpa cek status billing (harus paid)
- **Status**: **TERKONFIRMASI BILLING CHECK MISSING**
- **Akar Masalah**: `releaseBed` / `setBedStatus` di `ops.service.ts` membebaskan bed menjadi `AVAILABLE` tanpa mengecek apakah invoice episode pasien berstatus `paid`.
- **Lokasi File**: `apps/api/src/modules/ops/ops.service.ts` & `registration.service.ts:630`

---

### 10. Billing/Invoice pasien belum masuk padahal status sudah selesai
- **Status**: **TERKONFIRMASI ARCHITECTURAL GAP**
- **Akar Masalah**: Penutupan episode (`finishEpisode` / `dischargeEpisode`) tidak memicu pembuatan invoice (`createBillingIntent`). Invoice bersifat on-demand, sehingga episode selesai tidak otomatis memiliki record di tabel `invoices`.
- **Lokasi File**: `apps/api/src/modules/clinical/registration.service.ts` & `billing.service.ts`

---

### 11. Kasir tidak melihat daftar pasien belum ditagih
- **Status**: **TERKONFIRMASI MISSING WORKLIST ENDPOINT**
- **Akar Masalah**: Endpoint `GET /billing/invoices` hanya menampilkan invoice yang sudah terbentuk. v3 **tidak memiliki endpoint/menu `Unbilled Episodes`** untuk melihat daftar pasien berobat yang belum ditagih.
- **Lokasi File**: `apps/api/src/modules/billing/billing.controller.ts`

---

### 12. Perawat isi Tanda Vital (TTV) masih error `Payload tidak valid utk vital-sign@v1`
- **Status**: **TERKONFIRMASI AJV STRICT TYPE COERCION BUG**
- **Akar Masalah**: Schema Ajv `vital-sign` dipasang `additionalProperties: false` dan tipe numerik ketat (`number`). Saat AntD Form mengirim input (seperti `systolic`, `diastolic`, `temperature`, `heartRate`, `respRate`) sebagai `string` (atau mengirim field ekstra dari Form UI), validator Ajv STRICT melempar 400 Bad Request `Payload tidak valid utk vital-sign@v1`. Commit `65fca7a` mencoba coerce number di FE, tetapi coercion di `ObservationForm.tsx` belum mencakup seluruh field numerik / field ekstra.
- **Lokasi File**: `apps/api/src/modules/clinical/ajv-form-validator.ts` & `apps/web-clinic/src/features/emr/ObservationForm.tsx`

---

### 13. Batal kunjungan tidak membatalkan order medsup
- **Status**: **TERKONFIRMASI MISSING CASCADE CANCEL**
- **Akar Masalah**: `POST /clinical/episodes/:id/cancel` hanya meng-update status episode menjadi `cancelled`. Fungsi tidak membatalkan `prescriptions`, `supportOrders`, atau `invoiceLines` yang terikat pada episode tersebut.
- **Lokasi File**: `apps/api/src/modules/clinical/registration.service.ts:cancelEpisode`

---

## REKAPITULASI AKHIR: 25 TOTAL DEFECT & BLOCKER KRITIS TERIDENTIFIKASI

1. **Bug TTV Error `Payload tidak valid utk vital-sign@v1`** (Ajv Strict Type Coercion Error)
2. **Permission Block `master:create` saat Add Penjamin Pasien** (Salah permission decorator)
3. **Kasir Unbilled Worklist Missing** (Kasir tidak melihat daftar pasien belum ditagih)
4. **Invoice Belum Masuk Pasca Selesai** (Billing tidak auto-generate saat finish)
5. **Bed Bisa Dikosongkan Tanpa Cek Paid Billing** (Bed dibebaskan tanpa bayar)
6. **Deposit-Invoice Disconnect** (Uang deposit tidak memotong invoice kasir)
7. **Return Prescription Invoice Leak** (Obat diretur tapi tetap ditagih)
8. **Cancel Episode Cascade Missing** (Batal kunjungan tidak membatalkan order)
9. **Dispense Tanpa Cek Stok** (Stok minus / diserahkan tanpa barang)
10. **Discharge Pasien Unpaid** (Pasien inap dipulangkan tanpa lunas tagihan)
11. **Pendaftaran Rajal Ganda INPROGRESS** (Daftar berulang ke poli sama)
12. **Validasi NIK 16 Digit Missing** (NIK 5 digit / string lolos)
13. **Dropdown Penjamin IGD Mismatch** (Tampil semua penjamin RS, bukan milik pasien)
14. **Admisi Ranap Ganda** (Satu pasien punya 2 episode inpatient)
15. **Duplikasi Visite Dokter** (Ditagih visite 3x sehari)
16. **Transfer Bed Overcharge** (Kamar kelas lama ditagih tarif kelas baru)
17. **Consul Inter-Spesialis No Worklist** (Konsul internal tidak muncul di dokter B)
18. **Bed Lockout Status CLEANING** (Bed terkunci selamanya setelah discharge)
19. **Label Mandatory NIK Hardcoded Dev Text** (`NIK wajib (samakan v1)`)
20. **Dropdown Hak Kelas Text Unreadable** (UI CSS Dark Mode Token Contrast Bug)
21. **Dropdown Jenis Kelamin Mismatch v1** (L/P vs MALE/FEMALE)
22. **BPJS No Rujukan Unvalidated VClaim** (Rujukan palsu lolos registrasi)
23. **Iter Prescription Logic Dead** (Resep iterasi kronis tidak bisa diulang)
24. **Cancel Paid Prescription No Refund** (Resep batal tidak meretur uang kasir)
25. **Zod Body siteId Leakage** (Potensi cross-tenant write)
