# Kesia v3 vs v1 — Comprehensive Flow-by-Flow Gap Audit & Priority Matrix

> Generated 2026-08-07 oleh Salsabila QA.
> Analisis mendalam perbandingan alur end-to-end v1 (`D:\Hermes-QA\sourcecode\kesia-fe`) vs v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `426bf91`).

---

## I. PRIORITY 1: CRITICAL BLOCKERS (Melumpuhkan Operasional RS / Transaksi Keuangan)

### 1. ALUR MASTER TARIF, DISKON, & MARGIN ASURANSI (`cost-and-pricing` & `margin-price`)
- **Alur Ideal v1**:
  RS memiliki master tarif tindakan/obat berbasis kelas & penjamin. Penjamin Asuransi A punya margin diskon/markup khusus (`margin-price`), tarif ICD (`icd-tarif`), dan plafon harga obat (`item-hna`). Saat dokter mengorder tindakan/resep di EMR, sistem otomatis menarik harga sesuai kontrak penjamin pasien tersebut.
- **Kondisi v3 Saat Ini**:
  v3 hanya memiliki `classTypes.daily_rate` sederhana dan tarif tindakan generik di `items`. **TIDAK ADA ENGINE MARGIN HARGA PENJAMIN** (`margin-price`) dan **TIDAK ADA KONTRAK PERUSAHAAN MITRA** (`company-partner-item`).
- **Dampak Kritis**: Pasien Asuransi Swasta ditagih dengan tarif umum/flat! RS rugi akibat tidak bisa menerapkan markup asuransi atau diskon kontrak.
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Master Penjamin → Set Margin/Plafon (% markup/diskon per kategori) → Order EMR → Engine Resolve Price (Base × Margin) → EpisodeCharges → Invoice
  ```

---

### 2. ALUR DEPOSIT PASIEN VS INVOICE KASIR (`Deposit Disconnect`)
- **Alur Ideal v1**:
  1. Pasien bayar deposit di Kasir/Registrasi (`POST /deposit`) → Saldo Deposit tercatat.
  2. Saat pelayanan selesai, Kasir buka Billing.
  3. Total Invoice otomatis terpotong saldo deposit (`Total Tagihan - Saldo Deposit = Sisa Bayar`).
  4. Pasien hanya membayar sisa tagihan, atau menerima refund jika deposit berlebih.
- **Kondisi v3 Saat Ini**:
  `billing.service.ts` **SAMA SEKALI TIDAK MEMBACA ATAU MEMOTONG SALDO DEPOSIT** (`depositPayments`). Saldo deposit menggantung terpisah di database.
- **Dampak Kritis**: Pasien ditagih 100% total invoice tanpa memperhitungkan deposit yang sudah dibayar! Kasir harus menghitung manual di kalkulator.
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Deposit Payment → Balance Ledger → Billing Intent → Auto-Deduct Deposit Line → Net Invoice Total → Kasir Pay Sisa
  ```

---

### 3. ALUR RETUR OBAT FARMASI VS INVOICE KASIR (`Return Prescription Invoice Leak`)
- **Alur Ideal v1**:
  1. Pasien meretur obat yang belum diminum ke Apotek (`returnPrescription`).
  2. Apotek mengonfirmasi retur → Stok obat bertambah kembali di inventaris.
  3. Sistem otomatis meng-update/menghapus baris obat tersebut dari Invoice DRAFT Kasir.
- **Kondisi v3 Saat Ini**:
  `returnPrescription` hanya mengembalikan stok ke batch (`applyStockMovement`), tetapi **TIDAK MEMPERBARUI ATAU MENGHAPUS BARIS OBAT DI TABEL `invoiceLines`**.
- **Dampak Kritis**: Obat sudah dikembalikan ke apotek, tetapi harganya **TETAP TERTAGIH di Invoice Kasir pasien**!
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Apotek Retur Obat → Stock Reverted → Trigger Update Invoice Lines (Recalculate Net Qty & Amount) → Invoice Draft Updated
  ```

---

### 4. ALUR PEMBEBASAN BED RANAP VS STATUS BILLING (`Bed Lockout & Unpaid Release`)
- **Alur Ideal v1**:
  1. Dokter memulangkan pasien (`dischargeEpisode`) → Status bed otomatis `CLEANING`.
  2. Pasien menuju Kasir & Melunasi Tagihan → Invoice status `paid`.
  3. Staf Housekeeping membersihkan kamar → Mengubah status bed dari `CLEANING` menjadi `AVAILABLE` di menu Housekeeping.
  4. Bed siap di-assign ke pasien baru.
- **Kondisi v3 Saat Ini**:
  1. `releaseBed` / `setBedStatus` membebaskan bed **TANPA MEMVERIFIKASI STATUS INVOICE** (pasien unpaid bisa dibebaskan bed-nya).
  2. **TIDAK ADA MENU/HALAMAN HOUSEKEEPING** di frontend v3 untuk mengubah bed dari `CLEANING` ke `AVAILABLE`!
- **Dampak Kritis**: Pasien unpaid bisa bebas bed-nya, DAN semua bed bekas discharge **terkunci permanen di status `CLEANING` di Papan Bangsal**.
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Discharge → Bed status CLEANING → Kasir Pay Invoice (Check Paid) → Menu Housekeeping "Set Ready" → Bed status AVAILABLE
  ```

---

## II. PRIORITY 2: HIGH DEFECTS (Menghambat Alur Pelayanan Medis / Klaim BPJS)

### 5. ALUR KONSUL INTER-SPESIALIS / RUJUKAN POLI INTERNAL
- **Alur Ideal v1**:
  1. Dokter Poli A membuat Konsul Internal ke Poli B (`POST /care-plans` type=`consult`).
  2. Sistem otomatis membuat **Episode Konsul / Entry Worklist baru** di Poli B dengan flag `Rujukan Internal`.
  3. Dokter Poli B melihat pasien di Worklist-nya, membuka EMR, dan menginput Balasan Konsul.
- **Kondisi v3 Saat Ini**:
  `respondConsult` hanya meng-update status record `carePlans` menjadi `responded`. **SAMA SEKALI TIDAK MEMBENTUK EPISODE BARU ATAU WORKLIST ENTRY** di Poli B.
- **Dampak**: Dokter Poli B tidak pernah melihat pasien rujukan konsul tersebut di menu Worklist-nya!
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Dokter A Submit Konsul → Auto-Create Episode Consult (Source: Outpatient, Unit: Poli B) → Appear in Worklist Dokter B → Dokter B Input Balasan
  ```

---

### 6. ALUR VALIDASI RUJUKAN ONLINE BPJS VCLAIM
- **Alur Ideal v1**:
  1. Operator masukkan No. Rujukan BPJS saat pendaftaran.
  2. Server memanggil API VClaim `checkRujukan`.
  3. VClaim mengembalikan data: Nama Pasien, Poli Tujuan, PPK Asal, Tanggal Kadaluarsa.
  4. Jika valid & sesuai, pendaftaran diteruskan.
- **Kondisi v3 Saat Ini**:
  `createEpisode` hanya mengecek apakah string `bpjsNoRujukan` **tidak kosong** (`non-empty`). Server **SAMA SEKALI TIDAK MEMANGGIL API VCLAIM**.
- **Dampak**: Nomor rujukan palsu, kadaluarsa, atau salah poli lolos begitu saja. Klaim BPJS ditolak saat pengajuan.
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Input No Rujukan → Panggil VClaim Client checkRujukan → Validate (Poli Match & Expiry OK) → Save Episode + Auto Fill BPJS Fields
  ```

---

### 7. ALUR RESEP ITERASI (ITER / PENGULANGAN RESEP KRONIS)
- **Alur Ideal v1**:
  1. Dokter buat resep ber-flag `Iter = 2` (Maksimal 3x pengambilan).
  2. Apotek serahkan resep ke-1 → System mencatat `Iter Counter = 1`.
  3. Pasien datang bulan depan → Apotek panggil menu "Resep Iterasi" → System menarik resep master & membuat Salinan Resep Iter ke-2.
- **Kondisi v3 Saat Ini**:
  `prescriptions` menyimpan `isIter` & `iterMaxCount`, tetapi saat `dispense`, **TIDAK ADA LOGIKA COUNTER ATAU PEMBUATAN RESEP ITERASI TURUNAN**.
- **Dampak**: Pasien kronis tidak bisa mengambil resep ulangan di apotek tanpa minta resep baru dari dokter.
- **Alur Perbaikan yang Harus Dibuat**:
  ```
  Dispense Resep Iter → Increment Iter Count → Generate Copy Prescription Header for Next Iteration → Lock when Iter Count = Max Iter
  ```

---

### 8. ALUR BATAL RESEP PAID VS JURNAL KASIR (CREDIT NOTE)
- **Alur Ideal v1**:
  1. Dokter/Apoteker membatalkan resep yang sudah dibayar (`POST /prescriptions/:id/cancel`).
  2. System membatalkan resep + **otomatis menerbitkan Credit Note / Void Invoice Line** di Kasir.
  3. Kasir menyerahkan refund uang ke pasien.
- **Kondisi v3 Saat Ini**:
  `cancelPrescription` mengubah status resep jadi `cancelled`, tetapi **SAMA SEKALI TIDAK TERHUBUNG KE MODUL BILLING/KASIR**.
- **Dampak**: Pasien sudah bayar resep, resep dibatalkan, tetapi uang pasien menggantung di sistem tanpa ada jurnal pengembalian di kasir.

---

## III. PRIORITY 3: MEDIUM DEFECTS & MISSING MODULES (Fitur Pendukung & Laporan)

### 9. ALUR JASA MEDIS & REMUNERASI DOKTER (`doctor-remuneration`)
- **v1**: Memiliki modul pembagian Jasa Medis (JM) Dokter berdasarkan tindakan/visite/operasi dengan persentase bagi hasil RS vs Dokter.
- **v3**: **Sama sekali belum ada**.

### 10. ALUR STERILISASI ALAT MEDIS / CSSD (`CSSD`)
- **v1**: Memiliki modul penyerahan, proses otoklaf/sterilisasi, dan distribusi alat bedah/alkes steril ke OK/Ranap.
- **v3**: **Sama sekali belum ada**.

### 11. ALUR PENGADAAN & MANAGEMENT SUPPLIER FARMASI (`supplier` & `supplier-item`)
- **v1**: Memiliki modul Purchase Order (PO), Surat Pesanan Obat (SPO), Receiving Batch, dan Faktur Supplier.
- **v3**: v3 baru memiliki `receiveBatch` sederhana tanpa modul Supplier & PO.

### 12. ALUR JADWAL SHIFT PERAWAT & PETUGAS BANGSAL (`officer-schedule`)
- **v1**: Memiliki manajemen shift perawat (Pagi/Siang/Malam) per-ruangan inap.
- **v3**: v3 baru memiliki `doctorSchedules` (Jadwal Dokter), belum ada Jadwal Shift Perawat.

---

## REKAPITULASI DERAJAT PRIORITAS PERBAIKAN

| Priority Level | Jumlah Alur | Contoh Utama | Action Item Dev |
|---|---|---|---|
| **P1: CRITICAL BLOCKER** | 4 Alur | Master Tarif Margin, Deposit Disconnect, Retur Obat Leak, Bed Lockout | Wajib di-fix minggu ini sebelum pilot RS |
| **P2: HIGH DEFECT** | 4 Alur | Konsul Inter-Spesialis, Validasi VClaim, Resep Iterasi, Credit Note Batal Resep | Wajib di-fix sebelum Go-Live |
| **P3: MEDIUM / MISSING** | 4 Alur | Remunerasi Dokter, CSSD Sterilisasi, Supplier PO, Shift Perawat | Target Fase 2 pasca Go-Live |
