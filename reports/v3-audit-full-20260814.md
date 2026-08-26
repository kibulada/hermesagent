# LAPORAN EVALUASI & AUDIT KRITIS KESIA V3 (SIMRS RE-ARCHITECTED)

**Tanggal Audit**: 14 Agustus 2026  
**Target Repository**: `E:\WORK KESIA\Project\kesiaV3` (HEAD `1ea94cd` / `origin/main`)  
**Pembanding v1**: `D:\Hermes-QA\sourcecode`  
**Auditor**: Salsabila (QA Engineer Agent)

---

## 1. PENILAIAN ALUR UX KESIA V3

Kesia v3 mengadopsi pendekatan **Workspace & Station-centric** dengan **TopBar Peran Aktif**, menggantikan model pencarian berbasis menu statis di v1.

### Kelebihan Flow UX v3:
1. **Workspace-Centric / Context Switch Minimal**: Dokter dan Perawat bekerja dalam 1 layar terpadu (`DoctorWorkspacePage`, `NurseWorkspacePage`). Semua tab EMR (CPPT, SOAP, Vital Sign, Order Penunjang, Resep, Care Plan) dibuka dalam konteks pasien aktif tanpa pindah halaman.
2. **TopBar Switcher & Multi-Station**: Pengguna dengan role jamak (misal Dokter Jaga merangkap Perawat/Igd) dapat berpindah konteks station secara instan via TopBar tanpa re-login.
3. **Form Engine Generik & Dynamic Forms**: 26+ form klinis (Triage, Morse, Braden, MCU, Bedah, Spesialis) di-render dinamis dari registry DB, mempercepat pengisian data tanpa reload halaman.
4. **Realtime Queue & Patient Rail**: Drawer riwayat dan antrean pasien terintegrasi langsung di sisi kanan layar (RiwayatRailPanel).

### Kekurangan & Flaw Flow UX v3:
1. **Inkonsistensi State Machine Pasien Pulang**: Setelah invoice disetatuskan `paid` di Kasir, episode EMR **tidak otomatis closed** dan status kamar/bed tidak otomatis ter-checkout. Kasir dan Perawat harus melakukan aksi terpisah secara manual.
2. **Ketiadaan Notifikasi Visual/Popup Realtime**: Pengiriman order penunjang (Lab/Rad/Cathlab) atau resep statis di workspace tanpa indikator visual panggil antrean di unit penerima (kecuali SSE queue aktif).
3. **Flow Batal Kunjungan / Refund Berbelit**: Batal kunjungan membutuhkan pembatalan manual di Pendaftaran, void invoice di Billing, dan refund deposit di Kasir secara terpisah.

---

## 2. KEKURANGAN V3: MENU, ROLE, MAPPING & MASTERDATA

### A. Menu & Navigation
- **Inkonsistensi Tree Menu vs Route Real**: Terdapat 140 label menu di `nav.tsx`, namun leaf aktif nyata adalah 126. Sebagian route seperti `/ranap/clinical-pathway` dan `/rt/*` menggunakan fallback generic stub.
- **Menu Deny-By-Default Belum Rapi**: Beberapa role khusus (seperti `onkrad`, `ok`) jatuh ke fallback default yang berpotensi memunculkan menu tanpa izin akses jika RBAC DB tidak terkonfigurasi tepat.

### B. Role & Permission (RBAC)
- **Cross-Site Privilege Escalation di `setUserRoles` / `setRoleGrants`**: `apps/api/src/modules/master/rbac.service.ts:102-140` menerima `roleId` tanpa validasi bahwa role tersebut milik `siteId` tenant aktif.
- **Empty-Role Lockout**: Mengosongkan role pengguna via API `setUserRoles` dengan array kosong `[]` akan mengatur `roleId = null` tanpa fallback, menyebabkan pengguna terkunci total dari sistem.

### C. Mapping & Integration
- **R4 - Merge Pasien Mengabaikan Tabel Keuangan (CRITICAL DATA LOSS)**:
  - File: `apps/api/src/modules/clinical/registration.service.ts:452-455`
  - Deskripsi: `MERGE_TABLES` hanya me-repoint 12 tabel klinis (`episodes`, `observations`, `prescriptions`, dll).
  - Dampak: Tabel `invoices`, `deposit_payments`, `arm_tracers`, `food_orders`, `inpatient_visites`, dan `bpjs_queues` TIDAK ikut di-repoint ke `targetPatientId`. Data keuangan pasien lama menjadi **orphan/hilang** dari billing pasien gabungan.

### D. Masterdata & CRUD
- **M1 - Ketiadaan Unique Constraint Code pada Create Master Resource**:
  - File: `apps/api/src/modules/masterdata/masterdata.service.ts:45-88`
  - Deskripsi: Generic resource handler (`res/:resource`) memasukkan kode unit/item/insurer tanpa mengecek keunikan `code`.
  - Dampak: Duplikasi kode masterdata yang merusak pencarian dan reporting.
- **M2 - Reference Guard Absen pada Delete Master Data**:
  - File: `apps/api/src/modules/masterdata/masterdata.service.ts:112`
  - Deskripsi: Menghapus master item/unit yang sudah dipakai dalam transaksi EMR/Billing tidak memicu `FOREIGN_KEY_CONFLICT` guard secara eksplisit, berpotensi memicu error cascade SQL mentah.
- **M3 - Silent Truncation `.limit(500)` pada Master Tables Besar**:
  - File: `apps/api/src/modules/masterdata/masterdata.service.ts:150`
  - Deskripsi: Dropdown master ICD-10, Wilayah (Kelurahan/Kecamatan), dan Item Obat di-clamp max 500 row tanpa warning pagination.

---

## 3. POTENSI FITUR YANG HARUS ADA DI V3 (PARITY & ENHANCEMENT)

1. **Auto-Discharge & Bed Checkout Sync**:
   - Integrasi otomatis: saat Invoice Lunas (`paid`) → set Episode status `closed` → release Bed `available`.
2. **Guard Stok FEFO & Minus Block**:
   - Peringatan dan penghentian otomatis saat dispensing obat di Farmasi jika stok `qtyOnHand` kurang.
3. **Pemberitahuan/Notifikasi Kritis Hasil Lab (Critical Value Push)**:
   - Alert modal otomatis muncul di layar Dokter/Perawat aktif saat Laboratorium memverifikasi nilai kritis.
4. **Integritas Deposit Auto-Apply**:
   - Kemudahan pemotongan saldo deposit langsung pada layar pelunasan kasir tanpa perlu input manual amount.
5. **Auto-Reversal saat Void/Cancel**:
   - Pembatalan transaksi kasir/invoice otomatis membalikkan saldo deposit dan pergerakan stok obat.

---

## 4. AUDIT DEFECT & BLOCKER KRITIS SYSTEM-WIDE (E2E FLOW)

Berikut adalah daftar **defect baru & blocker aktif** yang terverifikasi secara langsung di kode sumber `E:\WORK KESIA\Project\kesiaV3` pada commit `1ea94cd`:

### A. Alur Finansial & Billing (Kasir & Billing)
- **K7 - Void Invoice Status 'PAID' Tanpa Refund / Reversal**:
  - File: `apps/web-clinic/src/features/billing/BillingPage.tsx:182` & `apps/api/src/modules/billing/billing.service.ts:137-195`
  - Problem: Tombol Batal/Void di FE hanya memeriksa `status !== 'void'`. Backend `cancelInvoice` membatalkan invoice tanpa memeriksa apakah invoice sudah disetatuskan `paid`.
  - Dampak: Invoice lunas dapat dibatalkan tanpa mengeluarkan voucher refund, menyebabkan ketidaksesuaian laporan kas/pembukuan.
- **K8 - Pelunasan Invoice (`payInvoice`) Tanpa Guard Status Awal**:
  - File: `apps/api/src/modules/billing/billing.service.ts:85-120`
  - Problem: Method `payInvoice` langsung mengubah `status = 'paid'` tanpa memvalidasi apakah status invoice saat ini `draft` atau `void`. Invoice yang sudah dibatalkan bisa disetatuskan lunas.

### B. Alur Farmasi & Stok (Apotek)
- **F3 - FEFO Deduct Boleh Minus (`INSUFFICIENT_STOCK` Absen)**:
  - File: `apps/api/src/modules/clinical/pharmacy.service.ts:550-562` & `applyStockMovement`
  - Problem: `deductFefo` mengurangi stok batch sampai `qty` terpenuhi walau sisa stok kurang. `applyStockMovement` memotong `qtyOnHand` tanpa mengecek `qtyOnHand - qty >= 0`.
  - Dampak: Stok obat di master/batch bisa bernilai negatif (`-5`), merusak Laporan Farmasi & Opname.

### C. Alur BPJS & VClaim
- **B1 - Issue SEP Tanpa Guard Duplikasi / Closed Episode**:
  - File: `apps/api/src/modules/clinical/sep.service.ts:91-164`
  - Problem: Method `issue()` tidak memeriksa apakah `ep.bpjsSepNo` sudah terisi atau episode sudah `closed`.
  - Dampak: Pemanggilan ulang memicu penerbitan SEP ganda di VClaim BPJS.

### D. Keamanan & Environment Defaults
- **S1 - Dev Reset Token Bocor di Environment Non-Production**:
  - File: `apps/api/src/modules/auth/auth.service.ts:101`
  - Problem: API forgot-password mengembalikan `devResetToken` langsung dalam respons JSON jika `NODE_ENV !== 'production'`.
  - Dampak: Pada environment Staging, akun pengguna dapat di-takeover tanpa akses email/SMTP.
- **S2 - Hardcoded JWT & MPI Secret Fallback**:
  - File: `apps/api/src/modules/auth/auth.module.ts` & `bpjs.config.ts`
  - Problem: Penggunaan string fallback `?? 'dev-jwt-secret-change-me'`.
  - Dampak: Potensi pemalsuan token JWT jika variabel environment lupa diset di server.

---

## 5. KESIMPULAN & REKOMENDASI PRIORITY FIX

1. **Prioritas 1 (Kritis/Keuangan & Data)**:
   - Perbaiki `registration.service.ts:mergePatient` agar menyertakan `invoices`, `deposit_payments`, `arm_tracers`, dan `food_orders` dalam `MERGE_TABLES`.
   - Tambahkan guard status pada `billing.service.ts` (`cancelInvoice` & `payInvoice`).
   - Tambahkan guard stok `INSUFFICIENT_STOCK` pada `pharmacy.service.ts:deductFefo`.
2. **Prioritas 2 (Alur Integrated Flow)**:
   - Tambahkan guard duplikat SEP pada `sep.service.ts`.
   - Tutup kebocoran `devResetToken` dan fallback JWT secret di environment staging.
3. **Prioritas 3 (Enhancement UX)**:
   - Otomatisasi pemicu pelunasan invoice terhadap penutupan episode dan ketersediaan bed.
