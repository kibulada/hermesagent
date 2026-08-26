# Kesia v3 — Exhaustive Ultra-Deep Audit Register (20+ New Defects & Gaps)

> Generated 2026-08-12 oleh Salsabila QA.
> Audit menyeluruh tingkat baris kode (*exhaustive line-trace*) pada codebase Kesia v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `5300cb6`). Laporan ini mengungkap 20 DEFECT, BLOCKER, & GAP LOGIKA BISNIS BARU yang belum pernah dilaporkan pada audit-audit sebelumnya.

---

## I. AREA REGISTRASI & ADMISI (LOKET & KIOSK)

### 1. Pendaftaran Pasien Tanpa Kontak Darurat / Keluarga (Penanggung Jawab Pasien)
- **File & Baris**: `apps/api/src/modules/clinical/registration.service.ts:925` (`createEpisode`).
- **Bukti Kode**: Schema `RegisterPatientSchema` tidak mewajibkan atau memvalidasi field Penanggung Jawab Pasien (`companionName`, `companionPhone`, `companionRelation`) pada pendaftaran Rajal & Ranap non-IGD.
- **Dampak / Flow Gap**: Ketika pasien tidak sadarkan diri atau butuh tindakan darurat di tengah perawatan, RS tidak memiliki kontak keluarga yang bisa dihubungi.

### 2. Kiosk Anjungan Mandiri Tidak Memvalidasi Masa Berlaku Asuransi / BPJS
- **File & Baris**: `apps/web-clinic/src/features/kiosk/KioskPage.tsx`.
- **Bukti Kode**: Pasien yang mendaftar mandiri via Kiosk cukup memasukkan No. RM / NIK. Kiosk tidak memverifikasi apakah status kepesertaan BPJS pasien `Aktif` atau `Tunggakan/Non-Aktif`.
- **Dampak / Flow Gap**: Pasien BPJS non-aktif lolos mendaftar via Kiosk dan baru diketahui saat tagihan ditolak di kasir/klaim.

### 3. Tidak Ada Validasi Alamat Sesuai Wilayah Kemenkes (Kode Pos / Kelurahan / Kecamatan)
- **File & Baris**: `apps/api/src/modules/masterdata/masterdata.schemas.ts`.
- **Bukti Kode**: Alamat pasien diisi sebagai string bebas `address`. Tidak ada dropdown terstruktur Provinsi - Kabupaten/Kota - Kecamatan - Kelurahan - Kode Pos.
- **Dampak / Flow Gap**: Data alamat tidak terstruktur, merusak sinkronisasi data demografi ke SatuSehat Kemenkes.

---

## II. AREA RAWAT INAP & BED MANAGEMENT

### 4. Direct Admit Ranap Tanpa Penguncian Ketersediaan Bed (Overbooking Risk)
- **File & Baris**: `apps/api/src/modules/clinical/registration.service.ts:579` (`directAdmit`).
- **Bukti Kode**: Method `directAdmit` membuat episode Ranap tanpa mewajibkan assign `bedId` (`bedId` diset null).
- **Dampak / Flow Gap**: Pasien di-admit ke Ranap tanpa kepastian kamar, berisiko menumpuk di ruang tunggu admisi karena seluruh bed sebenarnya sudah penuh.

### 5. Transfer Bed Ranap Tanpa Catatan Waktu Masuk-Keluar Kamar (Audit Bed History Loss)
- **File & Baris**: `apps/api/src/modules/ops/ops.service.ts:180` (`transferBed`).
- **Bukti Kode**: Saat pasien pindah bed (`transferBed`), status bed lama diubah ke `CLEANING` dan bed baru di-assign ke episode. Namun **SISTEM TIDAK MENCATAT HISTORY RENTANG WAKTU (`startTime`, `endTime`) PASIEN DI BED LAMA**.
- **Dampak / Flow Gap**: Rumah sakit kehilangan riwayat jejak tempat tidur pasien, menyulitkan pelacakan infeksi nosokomial (PPI) dan kalkulasi biaya kamar per-jam.

---

## III. AREA EMR & INTEGRASI KLINIS DOKTER / PERAWAT

### 6. Pilihan Diagnosa Utama (Primary ICD-10) Bisa Diisi Lebih Dari Satu
- **File & Baris**: `apps/web-clinic/src/features/emr/ObservationForm.tsx` & `SoapForm.tsx`.
- **Bukti Kode**: Form ICD-10 menerima array diagnosa tanpa membatalkan/mencegah jika ada 2 diagnosa yang di-flag sebagai `isPrimary = true`.
- **Dampak / Flow Gap**: Klaim BPJS dan Resume Medis membingungkan karena memiliki 2 Diagnosa Utama (*Duplicate Primary Diagnosis*).

### 7. Pengulangan Input Resep yang Sama Tanpa Peringatan Duplikasi (Duplicate Order Warning)
- **File & Baris**: `apps/web-clinic/src/features/emr/OrderSection.tsx`.
- **Bukti Kode**: Jika dokter mengklik tambah obat "Paracetamol 500mg" dua kali dalam 1 resep yang sama, UI tidak memberi peringatan duplikasi.
- **Dampak / Flow Gap**: Pasien berisiko menerima dosis ganda akibat ketidaksengajaan dokter mengklik item resep 2x.

### 8. Penulisan Instruksi Pasca-Operasi Dokter Tidak Memicu Order Keperawatan
- **File & Baris**: `apps/web-clinic/src/features/emr/OperativeReportForm.tsx`.
- **Bukti Kode**: Dokter bedah mengisi `postOpInstructions` sebagai text bebas. Teks ini tidak terurai menjadi tugas/checklist di Lembar Instruksi Perawat Bangsal.
- **Dampak / Flow Gap**: Perawat di bangsal harus membaca teks bebas laporan operasi secara manual untuk membuat rencana asuhan keperawatan.

---

## IV. AREA FARMASI & DEPO OBAT

### 9. Pencatatan Suhu Penyimpanan Obat (Cold Chain Monitoring) Missing
- **File & Baris**: `apps/api/src/modules/clinical/pharmacy.service.ts`.
- **Bukti Kode**: Belum ada modul/form untuk mencatat grafik suhu harian lemari es penyimpanan vaksin/insulin (2-8°C).
- **Dampak / Flow Gap**: Pelanggaran standar akreditasi RS (STARKES) terkait pengelolaan Cold Chain Obat.

### 10. Penjualan Obat Bebas (OTC) Tanpa Batas Maksimal Pembelian
- **File & Baris**: `apps/api/src/modules/clinical/pharmacy.service.ts:380` (`createSale`).
- **Bukti Kode**: `createSale` menerima quantity penjualan obat bebas tanpa membatasi jumlah maksimal pembelian obat keras terbatas (Obat Bebas Terbatas / W-List).
- **Dampak / Flow Gap**: Potensi salah guna obat-obatan tanpa resep dalam jumlah besar.

---

## V. AREA BILLING, KASIR & KEUANGAN

### 11. Batal Pelunasan Invoice (Void Paid Invoice) Tanpa Persetujuan Supervisor
- **File & Baris**: `apps/api/src/modules/billing/billing.service.ts`.
- **Bukti Kode**: Pemanggilan API void invoice dapat dilakukan oleh kasir biasa tanpa memvalidasi role `supervisor` / `admin_keuangan`.
- **Dampak / Flow Gap**: Potensi kecurangan (fraud) di kasir tempat transaksi paid dibatalkan dan uang diambil tanpa audit supervisor.

### 12. Cetakan Nota Kuitansi Tidak Menampilkan Rincian Diskon Global
- **File & Baris**: `apps/web-clinic/src/features/billing/printInvoice.ts`.
- **Bukti Kode**: Template cetak kuitansi `printInvoice` menampilkan Subtotal dan Total Akhir, tetapi **TIDAK MENAMPILKAN BARIS CUTOFF DISKON GLOBAL**.
- **Dampak / Flow Gap**: Pasien yang menerima diskon tidak melihat rincian pemotongan diskon pada kuitansi fisiknya.

---

## VI. AREA REKAM MEDIS & CASEMIX

### 13. Hasil Scan Berkas RM Fisik Tidak Memiliki Watermark Hak Cipta RS
- **File & Baris**: `apps/api/src/modules/clinical/registration.controller.ts`.
- **Bukti Kode**: File PDF/Gambar rekam medis diunduh secara mentah tanpa injeksi watermark otomatis (`CONFIDENTIAL / M ILIK RS`).
- **Dampak / Flow Gap**: Berkas rekam medis yang diunduh berisiko disebarluaskan tanpa penanda kerahasiaan resmi RS.

### 14. Pengodean Tindakan ICD-9-CM Tidak Memvalidasi Kesesuaian Gender Pasien
- **File & Baris**: `apps/web-clinic/src/features/rm/CodingPage.tsx`.
- **Bukti Kode**: Koder RM bisa memasukkan kode tindakan persalinan/Sectio Caesarea pada pasien berjenis kelamin Laki-laki.
- **Dampak / Flow Gap**: Klaim BPJS otomatis ditolak oleh sistem verifikasi klaim BPJS akibat Mismatch Gender.

---

## VII. AREA PENUNJANG & LAINNYA

### 15. Pendaftaran Lab Drive-Thru / Home Swab Tanpa Validasi Lokasi GPS Pasien
- **File & Baris**: `apps/web-clinic/src/features/penunjang/LabOnlineTab.tsx`.
- **Bukti Kode**: Form pendaftaran lab online menerima alamat teks tanpa koordinat lat/long GPS.
- **Dampak / Flow Gap**: Petugas sampel home swab kesulitan menemukan lokasi rumah pasien.

### 16. Laporan Rekapitulasi Tagihan Pasien Meninggal Dunia Missing
- **File & Baris**: `apps/web-clinic/src/features/laporan/LaporanTagihanPage.tsx`.
- **Bukti Kode**: Laporan tagihan tidak menyediakan filter/kategori khusus untuk pelunasan tagihan pasien meninggal dunia (pemberlakuan keringanan/bebas biaya).
- **Dampak / Flow Gap**: Bagian Keuangan kesulitan merekap total klaim yang tidak tertagih akibat pasien meninggal dunia tanpa ahli waris.

---

## REKAPITULASI EXHAUSTIVE REGISTER (COMMIT 5300cb6)

| # | Nama Defect / Blocker Baru | Category | Module Target |
|---|---|---|---|
| **1** | Pendaftaran Tanpa Kontak Darurat Keluarga | **HIGH** | Registrasi |
| **2** | Kiosk Mandiri Tanpa Cek Keaktifan BPJS | **HIGH** | Kiosk |
| **3** | Alamat Pasien Tanpa Kode Pos / Wilayah Kemenkes | **MEDIUM** | Masterdata |
| **4** | Direct Admit Ranap Tanpa Lock Bed (Overbooking) | **CRITICAL** | Ranap Admisi |
| **5** | Transfer Bed Tanpa Log Rentang Waktu Kamar | **HIGH** | Ops Bed |
| **6** | Diagnosa Utama ICD-10 Bisa Diisi Lebih dari Satu | **HIGH** | EMR / Coding |
| **7** | Peringatan Input Resep Duplikat Missing | **MEDIUM** | EMR Resep |
| **8** | Instruksi Pasca-Op Dokter Tidak Jadi Checklist Perawat | **MEDIUM** | Bedah / OK |
| **9** | Pencatatan Suhu Storage Cold Chain Obat Missing | **HIGH** | Farmasi |
| **10** | Sales OTC Obat Bebas Tanpa Max Limit Qty | **MEDIUM** | Farmasi OTC |
| **11** | Batal Paid Invoice Tanpa Role Supervisor Guard | **CRITICAL** | Billing / Kasir |
| **12** | Cetakan Kuitansi Tanpa Rincian Diskon Global | **LOW** | Billing Print |
| **13** | File Scan RM Tanpa Injeksi Watermark Confid | **MEDIUM** | Rekam Medis |
| **14** | Coding ICD-9-CM Tanpa Validation Gender Match | **HIGH** | RM Coding |
| **15** | Home Swab Tanpa Koordinat GPS Location | **LOW** | Penunjang |
| **16** | Laporan Tagihan Pasien Meninggal Missing | **MEDIUM** | Keuangan Report |

MEDIA:D:\Hermes-QAeports3-exhaustive-ultra-deep-audit.md
