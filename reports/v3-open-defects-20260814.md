# Laporan Defect & Blocker Terverifikasi — Kesia V3

- **Repo**: `E:\WORK KESIA\Project\kesiaV3`
- **HEAD**: `1ea94cd` (branch `main` — latest per 14 Agt 2026)
- **Status 10 Item Verifikasi Manual Kibul**: SUDAH DIFIX di commit `a373de9` (NIK duplikat, deposit list+guard, resep qty/racikan, guard status support order, lab kritis, delete confirm, care plan closed guard, surgery closed guard). **Item yang sudah fixed TIDAK dimasukkan ke laporan ini**.
- **Metode**: Re-audit seluruh codebase NestJS API (`apps/api`) & Next.js FE (`apps/web-clinic`) pada HEAD `1ea94cd`.
- **Total Defect Open**: **24 defect/blocker riil** (terverifikasi di kode).

---

## 1. Menu Kasir & Billing (`/kasir`, `/billing`)

### K-01 — Void Invoice Status `PAID` Dibolehkan Tanpa Mekanisme Refund
- **Menu UI**: `Menu TopBar > Peran Aktif: Kasir > Tagihan / Billing (/billing)`
- **File Backend**: `apps/api/src/modules/billing/billing.service.ts:144`
- **File Frontend**: `apps/web-clinic/src/features/billing/BillingPage.tsx:182`
- **Detail**:
  - FE: Tombol Batal ditampilkan untuk semua invoice yang `r.status !== 'void'` (termasuk status `Lunas / paid`).
  - BE: `cancelInvoice` guard hanya `if (inv.status === 'void') throw`. Invoice `paid` di-void, status resep di-flip balik ke `confirmed`, tetapi **uang tunai/transfer yang sudah diterima tidak tercatat direfund**.
- **Dampak**: 🔴 **Kerugian Keuangan / Fraud Risk**. Tagihan pasien lunas bisa dibatalkan kasir, status resep kembali belum-bayar, sementara uang pasien hilang dari pencatatan tanpa jurnal refund.

### K-02 — `payInvoice` Tidak Memvalidasi Status Invoice Sebelum Pembayaran
- **Menu UI**: `Menu TopBar > Peran Aktif: Kasir > Billing (/billing)`
- **File Backend**: `apps/api/src/modules/billing/billing.service.ts:385-390`
- **Detail**: `payInvoice` langsung melakukan `db.update(schema.invoices).set({ status: 'paid' })` tanpa membaca/memvalidasi status invoice saat ini (`draft`, `posted`, `void`).
- **Dampak**: Invoice berstatus `draft` (belum difinalisasi) atau invoice yang sudah `void` bisa dipaksa jadi `paid` via API/action.

### K-03 — Refund Deposit Bebas Dilakukan Setelah Episode Kunjungan Berstatus `CLOSED`
- **Menu UI**: `Menu TopBar > Peran Aktif: Kasir > Deposit / Kasir`
- **File Backend**: `apps/api/src/modules/clinical/queue.service.ts:72-96`
- **Detail**: `refundDeposit` memverifikasi `hasPaidDeposit` dan saldo, tetapi **tidak mengecek `ep.status`**.
- **Dampak**: Deposit dapat direfund untuk pasien yang sudah selesai berobat/pulang minggu lalu, merusak rekap kasir harian.

---

## 2. Menu Pendaftaran & Rekam Medis (`/pendaftaran`, `/rm`)

### R-01 — `mergePatient` TIDAK Re-Point 8 Tabel Finansial & Operasional (Data Orphan)
- **Menu UI**: `Menu TopBar > Peran Aktif: Petugas RM > Merge Pasien Temporary (/rm/merge)`
- **File Backend**: `apps/api/src/modules/clinical/registration.service.ts:466-469`
- **Detail**: `MERGE_TABLES` hanya menyertakan 12 tabel klinis. **8 tabel berikut TIDAK di-repoint**:
  1. `invoices`
  2. `deposit_payments`
  3. `pharmacy_sales`
  4. `arm_records`
  5. `arm_loans`
  6. `food_orders`
  7. `inpatient_visites`
  8. `bpjs_queues`
- **Dampak**: 🔴 **Integritas Data Finansial & Operasional**. Saat pasien duplikat di-merge ke MR survivor, semua tagihan, deposit, resep bebas, peminjaman berkas RM, order gizi, dan antrean BPJS milik pasien sumber **menjadi ORPHAN** (hilang dari profil survivor). Kasir tidak bisa menagih invoice lama pasien.

### R-02 — `setArm` Menerima Status String Bebas Tanpa Validasi Enum
- **Menu UI**: `Menu TopBar > Peran Aktif: Petugas RM > Arsip RM / Tracer (/rm/tracer)`
- **File Backend**: `apps/api/src/modules/ops/ops.service.ts:462-468`
- **Detail**: `setArm` menyimpan `status: input.status` secara mentah. Nilai seperti `borrowed`, `lost`, `sampah`, atau typo tersimpan tanpa error.
- **Dampak**: Status tracer berkas RM menjadi kotor dan laporan ketersediaan berkas salah.

### R-03 — `markArmInactive` Tidak Memvalidasi Status Episode
- **Menu UI**: `Menu TopBar > Peran Aktif: Petugas RM > Retensi Berkas RM`
- **File Backend**: `apps/api/src/modules/ops/ops.service.ts:432-442`
- **Detail**: Berkas RM untuk episode yang **masih aktif (rawat inap)** dapat ditandai sebagai non-aktif/retensi.
- **Dampak**: Berkas pasien yang sedang dirawat ditandai siap dimusnahkan/diarsip retensi.

---

## 3. Menu Farmasi & Stok (`/farmasi`, `/stok`)

### F-01 — `deductFefo` Tidak Melempar Error Saat Stok Batch Kurang (Silent Negative Stock)
- **Menu UI**: `Menu TopBar > Peran Aktif: Farmasi > Penjualan / Dispense Resep (/farmasi)`
- **File Backend**: `apps/api/src/modules/clinical/pharmacy.service.ts:556-564`
- **Detail**: Saat pengurangan stok batch (FEFO), jika akumulasi qty batch kurang dari `requested qty`, loop berhenti tanpa melempar exception `INSUFFICIENT_STOCK`.
- **Dampak**: Pengeluaran obat sukses di API, tetapi akumulasi stok per batch tidak sinkron dengan `item_stocks`.

### F-02 — `applyStockMovement` / `adjustStock` Tanpa Guard Stok Negatif
- **Menu UI**: `Menu TopBar > Peran Aktif: Farmasi / Logistik > Penyesuaian Stok (/stok/adjust)`
- **File Backend**: `apps/api/src/modules/clinical/pharmacy.service.ts:544-546`, `:607-618`
- **Detail**: Update `qtyOnHand` menggunakan SQL atomic `qtyOnHand + delta` tanpa assertion `qtyOnHand >= 0`.
- **Dampak**: Adjustment penyesuaian stok dapat menghasilkan stok fisik minus tanpa peringatan.

### F-03 — `voidSale` Farmasi Restore Stok Tanpa Mencatat Refund & Tanpa Guard Status
- **Menu UI**: `Menu TopBar > Peran Aktif: Farmasi > Penjualan Bebas (/farmasi/penjualan-bebas)`
- **File Backend**: `apps/api/src/modules/clinical/pharmacy.service.ts:262-272`
- **Detail**: `voidSale` mengembalikan stok obat via `sale-void` tetapi tidak mengecek apakah transaksi sudah lunas/dibayar dan tidak mencatat pengembalian uang.
- **Dampak**: Penjualan obat bebas tunai dapat dibatalkan kasir/farmasi untuk mengambil kembali stok tanpa laporan refund kas.

---

## 4. Menu BPJS, SEP & Antrean (`/bpjs`)

### B-01 — Penerbitan SEP (`issue`) Tidak Cek Episode Closed & Tidak Cek SEP Existing
- **Menu UI**: `Menu TopBar > Peran Aktif: BPJS / VClaim > Penerbitan SEP (/bpjs/sep)`
- **File Backend**: `apps/api/src/modules/clinical/sep.service.ts:91-118`
- **Detail**: `issue()` hanya mengecek `insurerType === 'BPJS'` dan kepemilikan kartu. **TIDAK mengecek apakah `ep.status === 'closed'`** dan **TIDAK mengecek apakah sudah ada SEP berstatus `issued`** untuk episode tersebut.
- **Dampak**: SEP ganda dapat diterbitkan untuk 1 kunjungan, atau SEP diterbitkan untuk pasien yang sudah pulang.

### B-02 — `sendBpjsQueue` & `listBpjsQueue` Menyajikan/Mengirim Episode `CLOSED`
- **Menu UI**: `Menu TopBar > Peran Aktif: BPJS > Antrean Mobile JKN (/bpjs/antrean)`
- **File Backend**: `apps/api/src/modules/ops/ops.service.ts:51-58`, `:82-100`
- **Detail**:
  - `listBpjsQueue`: Query tidak memfilter `closedAt` / `status !== 'closed'`. Episode yang sudah selesai berobat tetap tampil di monitoring antrean.
  - `sendBpjsQueue`: Tidak mengecek status episode dan tidak ada guard duplikasi kode booking per episode.
- **Dampak**: Antrean Mobile JKN terkirim ganda atau terkirim untuk pasien yang sudah selesai berobat.

### B-03 — `advanceQueueTask` Dapat Dipanggil Pada Antrean Status `SERVED`
- **Menu UI**: `Menu TopBar > Peran Aktif: BPJS > Update Task Antrean`
- **File Backend**: `apps/api/src/modules/ops/ops.service.ts:136-155`
- **Detail**: Guard hanya `ne(Q.status, 'cancelled')`. Antrean yang sudah `served` (selesai dilayani) masih dapat di-insert task baru (misal task 1–6 dipanggil ulang).
- **Dampak**: Riwayat task antrean Mobile JKN di server BPJS menjadi tidak valid.

---

## 5. Menu Dokter & Perawat (`/emr`, `/ranap`, `/ok`)

### D-01 — `confirmObservation` CPPT/SOAP Dapat Dilakukan Pada Episode `CLOSED`
- **Menu UI**: `Menu TopBar > Peran Aktif: Dokter > Workspace EMR / CPPT (/emr)`
- **File Backend**: `apps/api/src/modules/clinical/clinical-observation.service.ts:330-342`
- **Detail**: Tanda tangan / konfirmasi DPJP atas instruksi perawat (`confirmObservation`) tidak mengecek status episode.
- **Dampak**: Dokumentasi medis legal di-approve setelah episode kunjungan ditutup/pasien pulang.

### D-02 — `recordVisite` Dokter Ranap Tanpa Guard Episode Closed & Tanpa Deduplikasi
- **Menu UI**: `Menu TopBar > Peran Aktif: Dokter Rawat Inap > Visite Dokter (/ranap)`
- **File Backend**: `apps/api/src/modules/clinical/order.service.ts:231-242`
- **Detail**: `recordVisite` hanya cek `EPISODE_NOT_FOUND`. Tidak ada pengecekan `ep.status === 'closed'` dan tidak ada batas 1 visite per dokter per hari.
- **Dampak**: Visite dapat dicatat berulang kali pada hari yang sama atau dicatat setelah pasien pulang → tagihan visite membengkak.

### D-03 — `respondConsult` Dapat Menjawab Konsul Berulang Kali (Overwrite Without Audit)
- **Menu UI**: `Menu TopBar > Peran Aktif: Dokter Spesialis > Lembar Konsul (/emr/konsul)`
- **File Backend**: `apps/api/src/modules/clinical/care-plan.service.ts:177-185`
- **Detail**: `respondConsult` melakukan update `status='responded'` tanpa memverifikasi status awal. Konsul yang sudah dijawab dapat ditimpa jawaban baru.
- **Dampak**: Jawaban konsul pertama hilang ditimpa tanpa riwayat perubahan.

### D-04 — `createRequest` Bank Darah / UTD Tidak Memvalidasi Status Episode
- **Menu UI**: `Menu TopBar > Peran Aktif: Dokter / Perawat > Permintaan Darah (/emr/utd)`
- **File Backend**: `apps/api/src/modules/clinical/bloodbank.service.ts:106-120`
- **Detail**: `createRequest` memvalidasi komponen, ABO, dan Rh, tetapi **tidak mengecek apakah `episodeId` berstatus `closed` / `cancelled`**.
- **Dampak**: Order kantong darah dapat dibuat untuk episode yang sudah ditutup.

---

## 6. Menu OK / Kamar Operasi (`/ok`)

### O-01 — `setSurgeryStatus` & `rescheduleSurgery` Mengabaikan State Machine & Status Episode
- **Menu UI**: `Menu TopBar > Peran Aktif: Petugas OK > Jadwal Operasi (/ok)`
- **File Backend**: `apps/api/src/modules/ops/ops.service.ts:877-915`
- **Detail**:
  - `rescheduleSurgery`: Tidak mengecek apakah episode sudah `closed`/`cancelled` dan tidak mengecek apakah status operasi sudah `done`/`cancelled`.
  - `setSurgeryStatus`: Menerima string status bebas dari API tanpa memvalidasi urutan transisi (`scheduled → in_progress → done`).
- **Dampak**: Operasi yang sudah selesai dapat diubah kembali ke `scheduled`, atau operasi diubah statusnya tanpa aturan transisi.

---

## 7. Menu Admin, Masterdata & Auth (`/masterdata`, `/settings`)

### M-01 — `createUnit` (Master Poli/Unit) Tanpa Unique Check Kode Unit
- **Menu UI**: `Menu TopBar > Peran Aktif: Admin > Master Unit / Poli (/masterdata/unit)`
- **File Backend**: `apps/api/src/modules/masterdata/masterdata.service.ts:188-192`
- **Detail**: INSERT `units` tidak mengecek keberadaan `code` yang sama di site.
- **Dampak**: Poli/unit duplikat dengan kode sama dapat dibuat, menyebabkan duplikasi antrean dan jadwal dokter.

### M-02 — `resDelete` Masterdata Menghapus Baris Tanpa Cek Referensi Foreign Key
- **Menu UI**: `Menu TopBar > Peran Aktif: Admin > Master Data`
- **File Backend**: `apps/api/src/modules/masterdata/masterdata.service.ts:507-515`
- **Detail**: `db.delete(table)` dieksekusi langsung.
- **Dampak**: Menghapus data master (misal ICD/Dokter/Unit) yang sedang digunakan di episode aktif melempar HTTP 500 Unhandled Foreign Key Error.

### M-03 — Reset Password Mengembalikan `devResetToken` di Non-Production Environment
- **Menu UI**: `Halaman Login > Lupa Kata Sandi`
- **File Backend**: `apps/api/src/modules/auth/auth.service.ts:101-103`
- **Detail**: `if (!isProd()) return { ...generic, devResetToken: token }`. Di environment staging (`NODE_ENV=development`), token reset password dikembalikan langsung di respons HTTP API.
- **Dampak**: 🔴 **Celah Keamanan**. Siapa pun yang memanggil API lupa password di staging dapat melihat token reset user lain dan mengambil alih akun.

### M-04 — `dev-login` Aktif di Staging & JWT Secret Fallback Hardcoded
- **Menu UI**: Endpoint API `/auth/dev-login`
- **File Backend**: `apps/api/src/modules/auth/dev-auth.controller.ts:45`, `apps/api/src/modules/auth/auth.service.ts:70`
- **Detail**:
  - `dev-login` hanya di-disable jika `NODE_ENV === 'production'`. Di staging, login bypass tanpa password tetap terbuka.
  - `KESIA_INTERNAL_JWT_SECRET` memiliki fallback string `'dev-internal-jwt-secret-change-me'`.
- **Dampak**: 🔴 **Celah Keamanan**. Akses admin tanpa password terbuka di staging, dan JWT dapat dipalsukan jika env secret lupa di-set.

---

## 8. Menu UPM / Gizi (`/gizi`)

### U-01 — `setFoodOrderStatus` String Bebas & `recordFoodDelivery` Tanpa Guard Re-Delivery
- **Menu UI**: `Menu TopBar > Peran Aktif: Petugas Gizi > Monitoring Order Makanan (/gizi)`
- **File Backend**: `apps/api/src/modules/clinical/order.service.ts:830-856`
- **Detail**:
  - `setFoodOrderStatus`: Menerima string status apa pun tanpa enum.
  - `recordFoodDelivery`: Tidak mengecek apakah order sudah berstatus `delivered`. Pengantaran makanan dapat dicatat berulang kali untuk order yang sama.
- **Dampak**: Laporan pengantaran gizi menjadi ganda dan status order tidak valid.

---

## Ringkasan Distribusi Defect Per Modul/Menu

| Menu / Modul | Jumlah Defect | Kategori Risiko |
|---|---|---|
| Kasir & Billing | 3 | 🔴 Kritis (Kerugian Keuangan) |
| Pendaftaran & RM | 3 | 🔴 Kritis (Data Orphan Finansial) |
| Farmasi & Stok | 3 | 🟡 Sedang (Stok Minus / Retur) |
| BPJS & Antrean JKN | 3 | 🟡 Sedang (Integrasi BPJS) |
| Dokter & Perawat (EMR) | 4 | 🟡 Sedang (Integritas Legal / Billing) |
| OK / Kamar Operasi | 1 | 🟡 Sedang (Jadwal Operasi) |
| Admin, Master & Auth | 4 | 🔴 Kritis (Celah Keamanan Auth) |
| UPM / Gizi | 1 | 🟢 Rendah (Laporan Pengantaran) |
| **TOTAL** | **24 Defect** | |
