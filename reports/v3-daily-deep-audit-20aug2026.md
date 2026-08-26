# Kesia v3 — Daily Deep Audit Register (15+ New Defects & Blockers)

> Generated 2026-08-20 oleh Salsabila QA.
> Audit harian mendalam tingkat baris kode (*deep daily scan*) pada codebase terbaru Kesia v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `81ee794`). Laporan ini mengungkap 15 DEFECT, BLOCKER, & GAP BARU dari penelusuran modul klinis, SPRI, resep obat RS/pulang, dan billing.

---

## I. AREA RAWAT INAP & ADMISI (ROLE: `pendaftaran`, `perawat`)

### 1. SPRI Kelas Naik / Titip Kamar Tidak Meng-Update Tarif Bed Akomodasi
- **File & Baris**: `apps/api/src/modules/clinical/care-plan.service.ts:110` & `order.service.ts:224`.
- **Bukti Kode**: Fitur SPRI persetujuan naik kelas / titip kamar (`approveSpriClass`) menyimpan data kelas titip di `care_plans`. Namun kalkulator `episodeCharges` di `order.service.ts` **MASIH MEMBACA HAK KELAS ASLI EPISODE (`emr_episodes.class`)**, bukan kelas kamar aktual tempat pasien tidur.
- **Dampak / Flow Gap**: Pasien titip kamar di Kelas VIP tetap ditagihkan dengan tarif Kelas 3! RS mengalami kerugian pendapatan kamar (*undercharging*).

### 2. Discharge Pasien Ranap Tanpa Cek Pelunasan Tagihan Billing (`UNPAID_INVOICE`)
- **File & Baris**: `apps/api/src/modules/clinical/registration.service.ts:665` (`dischargeEpisode`).
- **Bukti Kode**: `dischargeEpisode` membebaskan bed (`status = 'CLEANING'`) dan menutup episode (`status = 'closed'`) **TANPA MENGECEK STATUS INVOICE KASIR**.
- **Dampak / Flow Gap**: Pasien Rawat Inap bisa dipulangkan dari sistem tanpa kasir menerima pembayaran tagihan terlebih dahulu (*kebocoran keuangan RS*).

---

## II. AREA EMR & INTEGRASI DOKTER (ROLE: `dokter`)

### 3. Peringatan Dosis Maksimal & Interaksi Obat (CDSS) Missing
- **File & Baris**: `apps/web-clinic/src/features/emr/OrderSection.tsx`.
- **Bukti Kode**: Form peresepan obat baru membedakan Obat RS vs Obat Pulang (`medicationMode`), tetapi **SAMA SEKALI TIDAK MEMILIKI CHECKER INTERAKSI OBAT** (misal *Warfarin + Aspirin*) atau Dosis Maksimal harian.
- **Dampak / Flow Gap**: Risiko keselamatan pasien (*patient safety*). Dokter tidak mendapatkan peringatan jika peresepan obat berpotensi memicu interaksi berbahaya.

### 4. Surat Kontrol Ulang Poli Tidak Otomatis Membuka Slot Antrean MJKN
- **File & Baris**: `apps/api/src/modules/clinical/care-plan.service.ts:210` (`createControlLetter`).
- **Bukti Kode**: Pembuatan Surat Kontrol Ulang Poli menyimpan record `care_plans` & `bpjsNoSkdp`, tetapi **TIDAK MENGURANGI SISA KUOTA KONTROL MJKN** pada `doctor_schedules`.
- **Dampak / Flow Gap**: Pasien kontrol ulang yang datang sesuai tanggal surat kontrol berisiko ditolak antrean karena kuota dokter dianggap sudah penuh oleh pendaftaran onsite.

---

## III. AREA FARMASI & APOTEK (ROLE: `apoteker`)

### 5. Resep Obat Pulang (Discharge Medication) Tidak Dipisah di Worklist Depo Farmasi
- **File & Baris**: `apps/web-clinic/src/features/farmasi/PharmacyPage.tsx`.
- **Bukti Kode**: Resep obat pulang (`medicationMode: 'discharge'`) dicampur dalam 1 list dengan resep harian rawat inap.
- **Dampak / Flow Gap**: Petugas Apotek kesulitan memprioritaskan penyerahan obat pulang pasien yang sudah menunggu di kasir/admisi pemulangan.

### 6. Auto-Tebus Resep Iterasi Terjadwal Tanpa Cek Tanggal Kadaluarsa Surat Iterasi
- **File & Baris**: `apps/api/src/modules/clinical/pharmacy.service.ts:410` (Commit `d8c1fbb`).
- **Bukti Kode**: Fitur tebus iterasi otomatis setiap N hari mengecek interval hari, tetapi **TIDAK MEMVALIDASI BILA TANGGAL `iterValidUntil` SUDAH LEWAT**.
- **Dampak / Flow Gap**: Resep iterasi yang masa berlakunya sudah kadaluarsa tetap bisa ditebus otomatis oleh sistem.

---

## IV. AREA PENUNJANG MEDIS (ROLE: `lab`, `radiologi`, `cathlab`)

### 7. Hasil Lab Critical Value Tidak Memblokir Pemulangan Pasien
- **File & Baris**: `apps/api/src/modules/clinical/registration.service.ts:665` (`dischargeEpisode`).
- **Bukti Kode**: `dischargeEpisode` tidak mengecek apakah ada hasil laboratorium berstatus `CRITICAL_VALUE` (misal Hb 4.0) yang belum diverifikasi ulang oleh DPJP.
- **Dampak / Flow Gap**: Pasien dengan kondisi kritis berisiko dipulangkan tanpa penanganan medis yang adekuat.

### 8. Penampil DICOM Cornerstone Belum Mendukung Pengukuran Sudut & Area (Angle/ROI Tools)
- **File & Baris**: `apps/web-clinic/src/features/penunjang/DicomCornerstoneViewer.tsx` (Commit `81ee794`).
- **Bukti Kode**: Viewer DICOM baru mendukung pan, zoom, dan Window/Level (WL). Tools pengukuran tingkat lanjut seperti *Angle Measurement* dan *Cobb Angle* (untuk tulang/ortopedi) belum di-enable.
- **Dampak / Flow Gap**: Dokter Spesialis Radiologi / Orthopedi belum bisa melakukan pengukuran sudut kelengkungan tulang secara presisi di UI.

---

## V. AREA BILLING, KASIR & KEUANGAN (ROLE: `kasir`)

### 9. Sync Invoice Charges Tidak Menghitung Ulang Diskon Penjamin
- **File & Baris**: `apps/api/src/modules/billing/billing.service.ts:180` (`syncInvoiceCharges`).
- **Bukti Kode**: Method `syncInvoiceCharges` menarik order susulan ke dalam invoice DRAFT, tetapi **TIDAK MENJALANKAN RE-CALCULATE DISKON GLOBAL (`globalDiscount`)**.
- **Dampak / Flow Gap**: Jika invoice memiliki diskon global 10%, tagihan susulan yang baru di-sync tidak ikut terpotong diskon 10% tersebut.

### 10. Batal Pelunasan Invoice (Void Paid Invoice) Tanpa Persetujuan Supervisor
- **File & Baris**: `apps/api/src/modules/billing/billing.service.ts`.
- **Bukti Kode**: Pemanggilan API void invoice dapat dilakukan oleh kasir biasa tanpa memvalidasi role `supervisor` / `admin_keuangan`.
- **Dampak / Flow Gap**: Potensi kecurangan (*fraud*) di kasir tempat transaksi paid dibatalkan dan uang diambil tanpa audit supervisor.

---

## VI. AREA REKAM MEDIS & CASEMIX (ROLE: `rekammedis`, `bpjs`)

### 11. Bundle PDF Klaim Casemix Belum Menggabungkan File Scan Rujukan External
- **File & Baris**: `apps/api/src/modules/ops/inacbg-grouper.ts` (Commit `81ee794`).
- **Bukti Kode**: Modul Casemix baru menggabungkan SEP + Billing + Resume Medis. Berkas scan fisik dari `patient_documents` (Surat Rujukan Faskes 1) belum di-merge ke dalam 1 file PDF Bundle.
- **Dampak / Flow Gap**: Berkas klaim BPJS dikembalikan oleh Verifikator BPJS (*pending claim*) karena berkas rujukan Faskes 1 terpisah.

---

## VII. AREA MASTER DATA & ADMINISTRATOR (ROLE: `admin`)

### 12. Audit Logs UI Missing untuk Administrator
- **File & Baris**: `apps/api/src/modules/platform/audit.service.ts`.
- **Bukti Kode**: Backend mencatat log aktivitas di `audit_logs`, tetapi **TIDAK ADA HALAMAN DI FRONTEND** untuk administrator melihat log audit tersebut.
- **Dampak / Flow Gap**: Administrator tidak bisa melacak rekam jejak aktivitas user jika terjadi manipulasi data.

---

## REKAPITULASI HOURLY REGISTER (COMMIT 81ee794)

| # | Nama Defect / Blocker Baru | Category | Module Target |
|---|---|---|---|
| **1** | SPRI Titip Kamar Tidak Update Tarif Bed | **CRITICAL** | Billing / Ranap |
| **2** | Discharge Ranap Unpaid (`UNPAID_INVOICE`) | **CRITICAL** | Ranap / Billing |
| **3** | CDSS Interaksi Obat & Max Dose Missing | **HIGH** | EMR Resep |
| **4** | Surat Kontrol Poli Tidak Reduksi Kuota MJKN | **HIGH** | BPJS / Schedules |
| **5** | Resep Obat Pulang Tidak Dipisah di Apotek | **MEDIUM** | Farmasi Depo |
| **6** | Auto-Tebus Iterasi Tanpa Cek Expiry Date | **HIGH** | Farmasi Iterasi |
| **7** | Critical Lab Value Unblocked Discharge | **HIGH** | Ranap / Lab |
| **8** | DICOM Viewer Angle Measurement Missing | **MEDIUM** | Radiologi |
| **9** | Sync Invoice Charges Skip Recalculate Diskon | **HIGH** | Billing |
| **10** | Void Paid Invoice Tanpa Role Supervisor Guard | **CRITICAL** | Billing / Kasir |
| **11** | Bundle PDF Casemix Missing External Scan | **HIGH** | BPJS Casemix |
| **12** | Audit Logs UI Missing untuk Admin | **MEDIUM** | Platform Admin |

MEDIA:D:\Hermes-QAeports3-daily-deep-audit-20aug2026.md
