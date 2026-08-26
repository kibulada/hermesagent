# Kesia v3 — Additional End-to-End Parity Gaps & Strategic Improvement Opportunities

> Generated 2026-08-07 oleh Salsabila QA.
> Analisis tambahan alur paritas v1 vs v3 serta ide-ide improvement strategis untuk pengembangan v3 SIMRS.

---

## I. TAMBAHAN ALUR E2E PARITAS v1 YANG BELUM LENGKAP DI v3

### 1. Alur Kalkulasi Resep Racikan DTD (Doses Tales Dosis)
- **Alur v1**:
  Dokter menginput resep racikan bertipe DTD (contoh: *Paracetamol 100mg dtd No. X*). Sistem otomatis menghitung total tablet bahan baku yang harus diambil apoteker (`(Dosis Minta × Jumlah Puyer) / Dosis Sediaan`).
- **Kondisi v3**:
  Resep v3 baru menerima string `itemKind: 'racikan'` tanpa kalkulator penimbangan bahan baku & dosis DTD.
- **Dampak**: Apoteker harus menghitung manual jumlah tablet bahan baku di kertas sebelum meracik.

### 2. Alur Peringatan Alergi Obat Instan di Screen Dokter (Prescription Allergy Alert)
- **Alur v1**:
  Saat dokter mengetik nama obat di EMR, sistem mengecek `patient_allergies`. Jika obat mengandung zat aktif alergen pasien, layar dokter langsung memunculkan **Pop-Up Peringatan Merah** (*Hard-Stop Warning*).
- **Kondisi v3**:
  Review concern alergi baru ada di panggung Telaah Resep Farmasi (`ReviewPrescriptionSchema`), tetapi **belum memunculkan pop-up peringatan instan di layar Dokter** saat pengetikan resep di EMR.
- **Dampak**: Dokter bisa tidak sengaja meresepkan obat alergen pasien; baru ketahuan saat resep sampai di apotek.

### 3. Alur Retur & Pengembalian Dosis Harian Ranap (UDD - Unit Dose Dispensing)
- **Alur v1**:
  Memiliki pengembalian dosis harian ranap (UDD) per dosis yang belum diminum pasien (misal pasien pulang siang, dosis malam diretur).
- **Kondisi v3**:
  Retur obat v3 masih bertipe *header prescription level*, belum mendukung retur parsial per dosis harian UDD per-shift.
- **Dampak**: Kesulitan merekap retur obat ranap yang diberikan per-dosis harian.

### 4. Alur Tracer & Peminjaman Berkas Rekam Medis Fisik (`ARM / Tracer`)
- **Alur v1**:
  Memiliki modul cetak tracer kertas & status peminjaman berkas rekam medis fisik dari ruang penyimpanan (filing RM).
- **Kondisi v3**:
  v3 murni digital EMR, tetapi RS transisi masih membutuhkan cetak tracer kertas untuk berkas RM fisik lama.
- **Dampak**: Petugas filing RM kesulitan melacak berkas fisik lama pasien yang belum ter-digitasi penuh.

---

## II. IDE-IDE IMPROVEMENT STRATEGIS v3 (POTENSI KEUNGGULAN v3)

Berikut adalah fitur-fitur inovatif yang **harus dikembangkan di v3** agar v3 jauh lebih unggul, modern, dan efisien dibanding v1:

### 1. Smart Real-Time Cost Containment (Estimasi INA-CBG vs Billing)
- **Konsep**:
  Saat dokter/perawat menginput diagnosis, tindakan, dan resep pada pasien BPJS, widget di EMR menampilkan **Estimasi Tarif INA-CBG vs Akumulasi Tagihan Riil Pasien**.
- **Nilai Tambah**:
  Dokter mendapat peringatan visual (Hijau / Kuning / Merah) jika akumulasi biaya pelayanan sudah mendekati atau melebihi plafon klaim BPJS, mencegah RS mengalami kerugian klaim (*cost containment*).

### 2. Auto-Dispatch Housekeeping & Mobile Cleaning Ticket
- **Konsep**:
  Saat dokter/perawat memulangkan pasien (`dischargeEpisode`), sistem secara otomatis menerbitkan **Tiket Tugas Pembersihan** ke dashboard/aplikasi mobile staf Housekeeping. Staf klik "Selesai Pembersihan", status bed di Papan Bangsal otomatis berubah dari `CLEANING` menjadi `AVAILABLE`.
- **Nilai Tambah**:
  Menghilangkan bottleneck ketersediaan kamar inap dan otomatisasi alur pembersihan bed tanpa perlu input desktop manual.

### 3. Real-Time Drug-Drug Interaction & Max-Dose CDSS (Clinical Decision Support System)
- **Konsep**:
  Integrasikan form penulisan resep EMR dengan database interaksi obat (MIMS / Kemenkes). Saat dokter menulis 2 obat yang saling berinteraksi berbahaya (misal: *Warfarin + Aspirin*), sistem langsung memberi rekomendasi alternatif obat.
- **Nilai Tambah**:
  Meningkatkan keselamatan pasien (*Patient Safety*) dan mencegah kejadian tidak diharapkan (KTD) akibat kesalahan peresepan.

### 4. WhatsApp / SMS Notification Gateway Antrean & E-Prescription
- **Konsep**:
  - Pendaftaran Berhasil → Auto WhatsApp notifikasi nomor antrean + estimasi jam panggil.
  - Panggilan Poli → Notifikasi WA "Giliran Anda 2 antrean lagi".
  - Selesai Berobat → WA link E-Resep & Invoice Digital.
- **Nilai Tambah**:
  Mengurangi penumpukan pasien di ruang tunggu poli dan meningkatkan kepuasan pasien.

### 5. Automated SatuSehat Sync Dashboard & Validation Error Handler
- **Konsep**:
  Dashboard monitoring SatuSehat yang menampilkan status sinkronisasi per-resource (`Encounter`, `Condition`, `Observation`, `Procedure`). Jika terjadi gagal sync (misal NIK tidak ditemukan), sistem menyediakan tombol *Auto-Fix / Retry* sekali klik.
- **Nilai Tambah**:
  Memastikan kepatuhan RS terhadap regulasi Permenkes No. 24/2022 secara 100% transparan.

---

## III. RINGKASAN REKOMENDASI ROADMAP PENGEMBANGAN v3

```
[FASE 1: PARITAS CRITICAL & BUG FIX (1-2 Minggu)]
  ├── Fix 25 Defect / Blocker Kritis (Deposit, Unbilled Worklist, Bed Cleaning, Retur Leak, dll)
  ├── Tambah Pop-Up Alergi Obat Instan di EMR Dokter
  └── Buat Form Kalkulasi Racikan DTD

[FASE 2: PARITAS ADVANCED & INTEGRASI (2-4 Minggu)]
  ├── Integrasi VClaim BPJS Riil + Mobile JKN
  ├── Auto-Dispatch Housekeeping Bed Cleaning
  └── Module Supplier PO & Procurement Farmasi

[FASE 3: INNOVATION & IMPROVEMENT (Pasca Go-Live)]
  ├── Real-Time INA-CBG Cost Containment Widget
  ├── WhatsApp Antrean & E-Prescription Gateway
  └── CDSS Drug Interaction Engine
```
