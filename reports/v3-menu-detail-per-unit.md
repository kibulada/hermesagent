# Kesia v3 — Detail Sub-Menu & Form Per-Unit (Rajal, Ranap, IGD, Farmasi, Penunjang, Bedah)

> Generated 2026-08-07 oleh Salsabila QA.
> Audit mendalam per-unit pada codebase v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `869afa1`) disandingkan dengan v1 (`D:\Hermes-QA\sourcecode\kesia-fe`).

---

## 1. UNIT RAWAT JALAN (Poli)

### A. Sub-Menu & Tab yang SUDAH ADA di v3
- **Worklist & Pendaftaran**:
  - `/registrasi/pasien` (Registrasi Pasien baru/lama)
  - `/perawat/station` (Stasiun Perawat Poli — Penganggilan + TTV/EWS + Selesai Perawat)
  - `/dokter/worklist` & `/emr/worklist` (Worklist Dokter — Pilihan Rajal/Ranap Segmented)
  - `/kiosk` (Anjungan Mandiri Self Check-in)
  - `/registrasi/waitlist` & `/registrasi/dibatalkan`
- **Workstation Dokter (`DoctorWorkspacePage`)**:
  - Tab **SOAP / Integrated Note** (Form `integrated-note`, Ajv STRICT, ICD-10/9)
  - Tab **Resep / Prescription** (drugId, edit resep, review concern, FEFO batch)
  - Tab **Order Penunjang** (Lab/Radiologi multi-item, qty-aware)
  - Tab **Visite & Konsul Internal** (`/dokter/konsul`)
  - Tab **Surat Kontrol & SPRI** (CarePlanSection → Cetak SPRI / Surat Kontrol)
  - Tab **TTV & Riwayat Pasien** (CPPT Timeline, Riwayat Resep, Riwayat Penunjang)
- **Halaman Khusus Rajal**:
  - `/verifikasi/online` (Registrasi Mobile/Web)
  - `/verifikasi/telemedicine` & `/emr/telemedicine/:episodeId` (Live Video Jitsi + SOAP)
  - `/verifikasi/ttd` (Halaman Tanda Tangan Dokter, `migrasi 0075`)

### B. Sub-Menu / Form Rajal yang BELUM ADA di v3
1. **Pra Medik Rawat Jalan (`PRMRJ`) Standalone**: v1 punya form PRMRJ khusus perawat; v3 menyatukannya di `medical-assessment` tanpa tab khusus PRMRJ.
2. **Form Resep & Layanan Rehabilitasi Medik (`Medical Rehabilitation`)**: v3 punya `/penunjang/rehab-medik`, tetapi sub-form entri resep fisioterapi dari Dokter Rajal belum selengkap v1.
3. **Hard-Gate TTD Dokter di Workstation**: Menu `/verifikasi/ttd` ada, namun **tombol Selesai (`finish`) di workspace belum mengunci** jika TTD belum diisi.

---

## 2. UNIT IG D / GAWAT DARURAT

### A. Sub-Menu & Tab yang SUDAH ADA di v3
- **Triase & Pendaftaran**:
  - `/igd/board` (Papan Triase IGD real-time)
  - `/igd/registrasi` (Registrasi IGD)
  - `/igd/triase` (Form Triase IGD `triage-igd` dengan disposisi enum)
  - `/igd/verifikasi-pasien` (Verifikasi & Merge Pasien Temporary ke MR Permanen)
- **Pelayanan & Order**:
  - `/igd/order-ruang` (Order Ruang Rawat Inap / SPRI dari IGD)
  - `/igd/resep` (Verifikasi & Resep Khusus IGD)
  - `/igd/operasi` (Order & Layanan Operasi CITO IGD)
  - `/igd/data` (Data & Riwayat Pasien IGD)

### B. Sub-Menu / Form IGD yang BELUM ADA di v3
1. **Summary / Catatan Tindakan Medis IGD (`Medical Action Summary`)**: v1 punya form ringkasan tindakan cito IGD; v3 masih menggunakan order tindakan generik.
2. **Auto-Disposisi ke Discharge Method**: Form `triage-igd` v3 sudah punya disposisi enum (`rawat-inap/rawat-jalan/observasi/rujuk/pulang-paksa/meninggal`), tetapi **belum terhubung otomatis ke method discharge episode**.

---

## 3. UNIT RAWAT INAP (Ranap)

### A. Sub-Menu & Tab yang SUDAH ADA di v3
- **Admisi & Manajemen Bed**:
  - `/ranap/admisi` (Admisi Pasien dari Rajal/IGD)
  - `/ranap/board` (Papan Bangsal / Status Bed per-Ruangan)
  - `/ranap/bed` (Manajemen & Status Kamar/Bed)
  - `/ranap/transfer` (Transfer Pasien & Perpindahan Bed, `migrasi 0053`)
  - `/ranap/laporan-bed` & `/ranap/bed-tv` (Monitor Bed TV Fullscreen)
- **Pelayanan & EMR Ranap**:
  - Tab **Visite Harian Dokter** (POST `/clinical/episodes/:id/visite`, `migrasi 0082`, otomatis masuk EpisodeCharges `source='visite'`)
  - Tab **Nursing Care Plan (SDKI/SLKI/SIKI)** & **Implementasi Perawat** (`migrasi 0156`)
  - Tab **Discharge Planning** (Form-engine `discharge-planning` v1, wajib `dischargeCondition`)
  - Tab **Clinical Pathway** (`/ranap/clinical-pathway`, `migrasi 0159`)
  - Halaman **Medical Resume** (`/rm/medical-resume` + Cetak WYSIWYG)

### B. Sub-Menu / Form Ranap yang BELUM ADA di v3
1. **Print Surat Keterangan Rawat Inap Otomatis**: v1 dapat mencetak Surat Keterangan Inap / Rawat otomatis dari data episode; v3 baru menyediakan Cetak SPRI & Resume.
2. **Akomodasi Kamar Multi-Kelas (Transfer Mid-Stay)**: Jika pasien pindah kelas di tengah masa inap, kalkulator akomodasi v3 perlu pengujian ketat agar delta tarif kamar kelas lama vs kelas baru terhitung presisi.

---

## 4. UNIT FARMASI (Rajal, Ranap, IGD, OK, Online)

### A. Sub-Menu & Tab yang SUDAH ADA di v3
- **Worklist Berbasis Unit**:
  - `/farmasi/rajal` (Apotek Rawat Jalan)
  - `/farmasi/ranap` (Apotek Rawat Inap)
  - `/farmasi/igd` (Apotek Gawat Darurat)
  - `/farmasi/ok` (Apotek Operasi / Kamar Bedah)
  - `/farmasi/apotek-online` (Apotek Online / Delivery)
- **Fitur Manajerial & Stok**:
  - `/farmasi/antrean` & `/farmasi/antrean/tv` (Dashboard & Display Antrean Panggilan Voice TTS)
  - `/farmasi/stok` (Stok Obat, Lot, FEFO Batching `migrasi 0081`, Penerimaan & Penyesuaian Batch)
  - `/farmasi/rekap-penyerahan` (Rekap Penyerahan Obat per Rentang/Petugas)
  - `/farmasi/penjualan-bebas` (Penjualan Obat Bebas / OTC Tanpa Episode, `migrasi 0097`)
- **Alur Telaah & Resep**:
  - Telaah Terstruktur 6-Concern (Interaksi, Alergi, Dosis, Duplikasi, Kontraindikasi, Inkompatibilitas)
  - Split Resep Apotek & Retur Obat (`POST /prescriptions/:id/return`)

### B. Sub-Menu / Form Farmasi yang BELUM ADA di v3
1. **Resep Racikan Kompresif**: Form resep v3 masih bertipe item per-baris generik, belum ada UI pembuat formula racikan (misal: puyer/salep dengan DTD & bahan pembawa) seperti v1.
2. **Verifikasi Etiket Obat Print-Barcoded**: Cetak etiket obat v3 sudah ada, tetapi belum dilengkapi barcode unik resep untuk pemindaian instan saat penyerahan di kasir apotek.

---

## 5. UNIT PENUNJANG MEDIS (Lab, Rad, Cathlab, HD, MCU, Fisio)

### A. Sub-Menu & Tab yang SUDAH ADA di v3
- **Laboratorium & Radiologi**:
  - `/penunjang/registrasi` & `/penunjang/riwayat` (Registrasi & Riwayat Penunjang Pasien)
  - `/penunjang/lab` & `/penunjang/radiologi` (Worklist & Input Hasil Terstruktur)
  - `/penunjang/lis` (Konsol Ingest HL7 ORU^R01 Analyzer)
  - `/penunjang/dicom` (Viewer DICOM MONOCHROME 8/16 bit)
  - Specimen Barcode & Chain-of-Custody Timeline (`migrasi 0079`)
  - Critical Value Alert Auto-Detection (`migrasi 0056`)
- **Unit Spesialis**:
  - `/penunjang/bank-darah` (Stok 5 Komponen Darah WB/PRC/FFP/TC/CRYO & Crossmatch)
  - `/penunjang/cathlab` (Layanan Cathlab & Laporan Tindakan Invasif)
  - `/penunjang/hemodialisa` & `/penunjang/hemodialisa-catatan` (Catatan Sesi HD)
  - `/penunjang/fisioterapi` & `/penunjang/rehab-medik` (Catatan Terapi Fisioterapi)
  - `/penunjang/mcu` & `/penunjang/mcu-pemeriksaan` (Pemeriksaan 12 Exam MCU + Cetak Sertifikat Kebugaran)
  - `/penunjang/gizi` (Asuhan Gizi & Skrining MST)

### B. Sub-Menu / Form Penunjang yang BELUM ADA di v3
1. **LIS Socket MLLP TCP Bridge**: `/penunjang/lis` v3 baru menerima HL7 via HTTP POST; adapter socket MLLP TCP (Port 2575) langsung dari mesin analyzer belum ada.
2. **EKG Waveform Drawing Canvas**: Form `ecg-interpretation` v3 baru berupa input angka/skalar; kanvas penempelan/penggambaran grafik EKG belum ada.

---

## 6. UNIT BEDAH & KAMAR OPERASI (OK)

### A. Sub-Menu & Tab yang SUDAH ADA di v3
- **Jadwal & Operasi**:
  - `/jadwal/operasi` (Jadwal Operasi OK Rajal/Ranap/IGD)
  - `OperativeReportForm` (Laporan Operasi SOAP + ICD-9-CM Prosedur + Tim Bedah)
- **Set Bedah Form-Engine (5 Tab Drawer di OperasiPage)**:
  1. Asesmen Pra-Anestesi (`migrasi 0084`)
  2. Pasca-Anestesi Aldrete Scored (`migrasi 0085`)
  3. WHO Perioperatif Checklist (`migrasi 0086`)
  4. Monitoring Anestesi Intra-Op (`migrasi 0087`)
  5. Asesmen Sedasi (`migrasi 0088`)

### B. Sub-Menu / Form Bedah yang BELUM ADA di v3
1. **Cardiac Conference Form**: Form khusus Rapat Multidisiplin Bedah Jantung v1 belum dipindahkan ke v3.
2. **Template Resep Paket Operasi**: Paket obat/alkes khusus kamar bedah yang otomatis terpotong dari depo OK saat operasi dimulai.

---

## Matriks Ringkasan Kesiapan Detail Menu Per-Unit

| Unit | Menu Tercover v3 | Gap / Belum Ada di v3 | Kesiapan v3 |
|---|---|---|---|
| **Rawat Jalan** | Registrasi, Worklist Perawat/Dokter, Telemedicine, TTD, Surat Kontrol | PRMRJ Standalone, Hard-Gate TTD Finish | **90%** |
| **IGD** | Triase Disposisi, Reg Temp, Merge MR, SPRI, Operasi CITO | Action Summary khusus IGD | **90%** |
| **Rawat Inap** | Admisi, Ranap Board, Visite Harian, Transfer Bed, Discharge Plan | Cetak Surat Inap Otomatis | **90%** |
| **Farmasi** | Rajal, Ranap, IGD, OK, Online, Stok FEFO, Rekap, OTC Sale | Form Formula Resep Racikan | **85%** |
| **Penunjang** | Lab, Rad, LIS, DICOM, Bank Darah, Cathlab, HD, MCU, Fisio, Gizi | MLLP TCP Bridge, EKG Canvas | **85%** |
| **Bedah (OK)** | Jadwal, Laporan Operasi, 5 Set Form Anestesi/WHO | Form Cardiac Conference | **85%** |
