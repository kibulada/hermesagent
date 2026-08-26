# Kesia v3 — Deep Role-by-Role Defect, Blocker & Form Value Comparison Matrix (v3 vs v1)

> Generated 2026-08-07 oleh Salsabila QA.
> Audit mendalam untuk 14 Role/Peran di Kesia v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `426bf91`) disandingkan dengan v1 (`D:\Hermes-QA\sourcecode\kesia-fe`). Zero-mistake: Setiap role dianalisis dari ketersediaan menu, defect/blocker fungsional, serta perbedaan field/form data.

---

## 1. PETUGAS PENDAFTARAN (`pendaftaran`)

### A. Menu & Fitur
- **Menu v3**: `Registrasi Pasien` (`/registrasi/pasien`), `Data Pasien Rajal` (`/registrasi/data`), `Jadwal Dokter` (`/jadwal/dokter`), `Waitlist` (`/registrasi/waitlist`), `Verifikasi Online` (`/verifikasi/online`), `IGD Registrasi` (`/igd/registrasi`).
- **Defect & Blocker v3**:
  1. **Validasi VClaim BPJS Missing**: `createEpisode` tidak memvalidasi `bpjsNoRujukan` ke VClaim BPJS online.
  2. **Quota Onsite vs Online Lockout**: Kuota pendaftaran tidak memisahkan antrean onsite vs online (Mobile JKN).
- **Perbedaan Form & Value Data vs v1**:
  - *Suku/Etnis*: v1 memiliki 80+ dropdown suku resmi; v3 berupa text field bebas.
  - *Agama*: v1 memuat `Konghucu` & `Lainnya`; v3 baru memuat 5 agama resmi dasar.
  - *Pendidikan*: v1 menggunakan string `Diploma-I`; v3 menggunakan `D1`.

---

## 2. KASIR / BILLING (`kasir`)

### A. Menu & Fitur
- **Menu v3**: `Kasir & Deposit` (`/kasir`), `Billing / Invoice` (`/kasir/billing`), `Treasury Report` (`/keuangan/treasury`), `Outstanding` (`/keuangan/outstanding`).
- **Defect & Blocker v3**:
  1. **Deposit Disconnect**: Saldo deposit (`depositPayments`) tidak memotong total invoice secara otomatis di `createBillingIntent`.
  2. **Retur Obat Invoice Leak**: Retur obat di apotek mengembalikan stok, tapi tidak menghapus/meng-update baris `invoiceLines` DRAFT.
- **Perbedaan Form & Value Data vs v1**:
  - *Split Invoice*: v1 memiliki form split invoice fisik terpisah pasien vs penjamin (`SplitInvoiceForm`); v3 menggunakan 1 invoice gabungan dengan field `coverages`.
  - *Margin Harga*: v1 mendukung margin markup/diskon penjamin (`margin-price`); v3 baru mendukung diskon nominal global.

---

## 3. PERAWAT (`perawat`)

### A. Menu & Fitur
- **Menu v3**: `Stasiun Perawat` (`/perawat/station`), `IGD Triase` (`/igd/triase`), `Papan Bangsal` (`/ranap/board`), `Manajemen Bed` (`/ranap/bed`).
- **Defect & Blocker v3**:
  1. **Bed Lockout Status CLEANING**: Pasien discharge mengubah bed jadi `CLEANING`. Tidak ada UI Housekeeping di v3 untuk mengubah kembali ke `AVAILABLE`.
  2. **Critical Lab Value Unblocked Discharge**: Alert nilai kritis lab tidak memblokir tombol `dischargeEpisode`.
- **Perbedaan Form & Value Data vs v1**:
  - *Form TTV*: v3 menggunakan Ajv Form Engine (`vital-sign@v1`) dengan min/max validation; v1 menggunakan komponen AntD Form biasa.
  - *Skrining Jatuh*: v1 memisahkan Skrining Humpty Dumpty (Anak) vs Morse Fall Scale (Dewasa) secara terpisah; v3 disatukan di form EMR.

---

## 4. DOKTER (`dokter`)

### A. Menu & Fitur
- **Menu v3**: `Worklist Dokter (EMR)` (`/dokter/worklist`), `Konsul Internal` (`/dokter/konsul`), `Jadwal Operasi` (`/jadwal/operasi`), `Verifikasi TTD` (`/verifikasi/ttd`).
- **Defect & Blocker v3**:
  1. **Consul Inter-Spesialis No Worklist**: Form konsul internal tidak membentuk episode/Worklist baru di Poli B.
  2. **Warning Alergi Obat Instan Missing**: EMR v3 tidak memunculkan pop-up warning alergi instan saat ngetik resep.
- **Perbedaan Form & Value Data vs v1**:
  - *SOAP Form*: v3 menggunakan form EMR unified dengan Draf Salin Resep Lalu & Template Paket Obat; v1 berupa tab SOAP terpisah.
  - *Resep Racikan DTD*: v1 memiliki kalkulator puyer DTD; v3 baru berupa input string `itemKind: 'racikan'`.

---

## 5. APOTEKER (`apoteker`)

### A. Menu & Fitur
- **Menu v3**: `Farmasi Rajal/Ranap/IGD` (`/farmasi/rajal`), `Farmasi OK` (`/farmasi/ok`), `Stok & Batch` (`/farmasi/stok`), `Penjualan Bebas` (`/farmasi/penjualan-bebas`).
- **Defect & Blocker v3**:
  1. **Overdraw Stok Obat (`deductFefo` Bug)**: `deductFefo` tidak melempar error `INSUFFICIENT_STOCK` jika stok di DB kurang dari qty resep.
  2. **Resep Iterasi Counter Dead**: `dispense` tidak memiliki counter/sequence untuk resep iterasi turunan.
- **Perbedaan Form & Value Data vs v1**:
  - *Rute Obat*: v1 memisahkan Tetes Mata vs Tetes Telinga vs Rektal/Vaginal; v3 baru memuat `oral`, `iv`, `im`, `sc`, `topikal`, `tetes`, `inhalasi`.
  - *Aturan Pakai*: v1 berupa dropdown aturan pakai standar (`3x1 ac`, `2x1 pc`); v3 berupa text input bebas.

---

## 6. STAF PENUNJANG (`penunjang`)

### A. Menu & Fitur
- **Menu v3**: `Registrasi Penunjang` (`/penunjang/registrasi`), `Fisioterapi` (`/penunjang/fisioterapi`), `Hemodialisa` (`/penunjang/hemodialisa`), `MCU` (`/penunjang/mcu`).
- **Defect & Blocker v3**:
  1. **Jadwal Dokter Eksternal Missing**: Master dokter luar ada, tetapi jadwal praktek per-harinya belum ada.
- **Perbedaan Form & Value Data vs v1**:
  - *MCU Certificate*: v3 dilengkapi template cetak sertifikat MCU V2 dinamis (Depnaker/Perusahaan); v1 berupa form cetak standar.

---

## 7. PETUGAS LABORATORIUM (`lab`)

### A. Menu & Fitur
- **Menu v3**: `Laboratorium` (`/penunjang/lab`), `Konsol LIS` (`/penunjang/lis`), `Bank Darah` (`/penunjang/bank-darah`).
- **Defect & Blocker v3**:
  1. **LIS MLLP Socket Adapter Missing**: Belum ada adapter socket MLLP TCP untuk membaca data langsung dari analyzer lab tua.
- **Perbedaan Form & Value Data vs v1**:
  - *Nilai Rujukan Lab*: v3 menyimpan nilai rujukan min/max per-gender & kelompok umur di DB JSON; v1 berupa text rujukan statis.

---

## 8. PETUGAS RADIOLOGI (`radiologi`)

### A. Menu & Fitur
- **Menu v3**: `Radiologi` (`/penunjang/radiologi`), `Penampil DICOM` (`/penunjang/dicom`).
- **Defect & Blocker v3**:
  1. **DICOM Compression Limit**: File DICOM terkompresi JPEG-LS / RLE sangat besar masih perlu ditangani via fallback tab baru.
- **Perbedaan Form & Value Data vs v1**:
  - *DICOM Viewer*: v3 menggunakan Canvas Render `dicomParse.ts` dengan kalkulasi WL/WW; v1 menggunakan library DWV / Cornerstone JS.

---

## 9. PETUGAS CATHLAB (`cathlab`)

### A. Menu & Fitur
- **Menu v3**: `Cathlab` (`/penunjang/cathlab`).
- **Defect & Blocker v3**:
  1. **Integration to EMR Order**: Modul Cathlab berdiri sendiri, belum membaca order otomatis dari EMR Dokter Jantung.
- **Perbedaan Form & Value Data vs v1**:
  - *Cathlab Form*: v1 memiliki form tim kateterisasi & log pemakaian stent balun; v3 berupa form catatan tindakan.

---

## 10. PETUGAS BPJS (`bpjs`)

### A. Menu & Fitur
- **Menu v3**: `BPJS / SEP` (`/bpjs/sep`), `Surat Kontrol` (`/bpjs/surat-kontrol`), `Rujukan` (`/bpjs/rujukan`), `Casemix` (`/bpjs/casemix`).
- **Defect & Blocker v3**:
  1. **Module Casemix Unexported**: File `schema/casemix.ts` masih di-comment out. Belum ada trigger Grouper INA-CBG & Bundle PDF.
  2. **Re-Issue SEP Duplicate**: `issue` tidak memblokir re-insert jika `bpjsSepNo` sudah ada.
- **Perbedaan Form & Value Data vs v1**:
  - *Casemix Helper*: v1 memiliki `CasemixHelperV5.10.js` untuk E-Klaim Kemenkes; v3 belum terintegrasi E-Klaim.

---

## 11. REKAM MEDIS (`rekammedis`)

### A. Menu & Fitur
- **Menu v3**: `Tracer ARM` (`/rm/arm`), `ICD Coding` (`/rm/coding`), `Satu Sehat` (`/rm/satusehat`), `Medical Resume` (`/rm/medical-resume`).
- **Defect & Blocker v3**:
  1. **SatuSehat Auto-Retry Missing**: Belum ada tombol auto-retry & error handler sekali klik untuk resource gagal sync SatuSehat.
- **Perbedaan Form & Value Data vs v1**:
  - *Tracer RM*: v1 memiliki modul cetak tracer kertas & status peminjaman berkas fisik RM (`ARM`); v3 murni digital EMR.

---

## 12. UPM / GIZI (`upm`)

### A. Menu & Fitur
- **Menu v3**: `Food Service Unit` (`/rm/fsu`), `Monitoring Gizi` (`/rm/fsu-monitoring`).
- **Defect & Blocker v3**:
  1. **Integration to Kitchen Print Ticket**: Sudah di-fix di `fc1439f` dengan fitur e-Tiket & tanggal pemesanan.
- **Perbedaan Form & Value Data vs v1**:
  - *Order Diet*: v3 mendukung e-Tiket pengantaran gizi per-pasien; v1 berupa rekapitulasi sheet diet per-bangsal.

---

## 13. PETUGAS MCU (`mcu`)

### A. Menu & Fitur
- **Menu v3**: `MCU` (`/penunjang/mcu`), `Pemeriksaan MCU` (`/penunjang/mcu-pemeriksaan`).
- **Defect & Blocker v3**:
  1. **RBAC Scope Isolation**: Di-fix di `d50d265` & `b29b3e6` dengan pemisahan menu ke peran 'Petugas MCU'.
- **Perbedaan Form & Value Data vs v1**:
  - *MCU V2 Forms*: v3 memiliki form MCU V2 lengkap (Depnaker & Perusahaan) dengan cetak sertifikat dinamis; v1 berupa form cetak standar.

---

## 14. ADMINISTRATOR (`admin`)

### A. Menu & Fitur
- **Menu v3**: `ALL GROUPS` (`/master/*`, `/pengaturan`, `/laporan/*`).
- **Defect & Blocker v3**:
  1. **Master Margin Price Missing Engine**: Form margin price v3 belum memotong `episodeCharges` otomatis.
  2. **Audit Logs UI Missing**: Backend punya `audit_logs`, tapi UI admin belum ada.
- **Perbedaan Form & Value Data vs v1**:
  - *Form Builder*: v3 menggunakan Ajv Form Engine (`/master/forms`); v1 menggunakan form generator custom.

---

MEDIA:D:\Hermes-QAeports3-role-by-role-defect-and-form-matrix.md
