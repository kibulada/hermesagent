# Kesia v3 — Final Comprehensive Zero-Mistake Audit: Menu, Flow, UI/UX, Gaps & Defects (v3 vs v1)

> Generated 2026-08-12 oleh Salsabila QA.
> Audit final komprehensif zero-mistake pada codebase terbaru Kesia v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `5300cb6`) disandingkan dengan v1 (`D:\Hermes-QA\sourcecode\kesia-fe`). Laporan ini membedah setiap menu per-role, menganalisis alur end-to-end, mengevaluasi perbedaan UI/UX & form data, serta mengidentifikasi seluruh defect/blocker yang tersisa dengan tingkat akurasi tertinggi.

---

## BAB I: REGISTRASI, ADMISI & LOKET (ROLE: `pendaftaran`)

### MENU: `/registrasi/pasien` (Registrasi Pasien Baru/Lama)
- **(+) PLUS v3**: Form registrasi terintegrasi dengan pencarian data pasien MPI (Master Patient Index), mengurangi duplikasi data.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Form Alamat**: Alamat di v3 masih berupa text field bebas. v1 memiliki dropdown terstruktur Provinsi, Kabupaten/Kota, Kecamatan, dan Kelurahan yang ditarik dari master Wilayah Kemenkes.
  2. **Kontak Darurat**: Form v3 tidak mewajibkan/memvalidasi field Penanggung Jawab Pasien (`companionName`, `companionPhone`, `companionRelation`).
- **DEFECT / BLOCKER v3**:
  - **No. Rujukan BPJS Tidak Tervalidasi**: Pendaftaran BPJS di `createEpisode` tidak memanggil API VClaim `checkRujukan` secara online. Nomor rujukan palsu/kadaluarsa lolos.
  - **Kuota MJKN Belum Terpisah Penuh**: Meskipun DB sudah punya `quota_mjkn` (fix `b516cc7`), alokasi antrean di UI belum 100% memisahkan slot MJKN vs Onsite.

### MENU: `/igd/registrasi` (Registrasi Pasien IGD)
- **(+) PLUS v3**: Pendaftaran IGD mendukung mode "Pasien Temporary" jika identitas pasien tidak diketahui (Mr. X/Mrs. Y).
- **(-) MINUS v3 (Paritas v1)**:
  - **Dropdown Penjamin**: Dropdown penjamin menampilkan seluruh penjamin RS, bukan menyaring berdasarkan kartu peserta milik pasien (Fix `fbda030` sudah ada, tetapi belum di-deploy ke semua environment).
- **DEFECT / BLOCKER v3**:
  - **Tidak Ada Cetak Gelang Identitas IGD**: Setelah registrasi, tidak ada trigger cetak gelang identitas IGD (merah/kuning) otomatis.

---

## BAB II: PELAYANAN MEDIS & EMR (ROLE: `perawat`, `dokter`)

### MENU: `/perawat/station` (Stasiun Perawat Poli) & `/dokter/worklist` (EMR)
- **(+) PLUS v3**: EMR v3 bersifat unified dalam 1 tab episode, lebih modern dari tab-tab SOAP terpisah di v1. Dilengkapi fitur salin resep & template paket obat.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Peringatan Alergi Obat Instan**: EMR v3 tidak memunculkan pop-up warning alergi instan di layar dokter saat mengetik resep.
  2. **Kalkulator Resep Racikan DTD**: Form resep racikan v3 belum memiliki kalkulator penimbangan bahan puyer DTD.
- **DEFECT / BLOCKER v3**:
  - **Konsul Inter-Spesialis Tanpa Worklist Target**: Rujukan konsul dari Dokter A ke Dokter B (`createCarePlan`) tidak membentuk episode/Worklist baru di Dokter B.
  - **Golongan Darah & Rhesus Tidak Tampil di Header EMR**: Informasi vital Golongan Darah & Rhesus tidak tercantum di header EMR, memperlambat respon darurat.

---

## BAB III: FARMASI & DEPO (ROLE: `apoteker`)

### MENU: `/farmasi/rajal`, `/farmasi/ranap`, `/farmasi/stok`
- **(+) PLUS v3**: Memiliki dashboard antrean farmasi terpusat & histori penyerahan obat yang lebih detail.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Aturan Pakai Standar**: v1 memiliki dropdown aturan pakai standar (`3x1 ac`, `2x1 pc`); v3 masih berupa text input bebas.
  2. **Rute Obat Spesifik**: v3 kurang sub-rute spesifik (Tetes Mata vs Tetes Telinga vs Rektal/Vaginal).
- **DEFECT / BLOCKER v3**:
  - **Counter Resep Iterasi Mati**: Logic `dispense` tidak memiliki counter/sequence untuk resep ulangan. Pasien kronis tidak bisa mengambil resep iterasi.
  - **Retur Obat UDD Harian Ranap Missing**: Alur retur obat per-dosis harian ranap (UDD) yang belum terpakai belum ada.

---

## BAB IV: PENUNJANG MEDIS (ROLE: `lab`, `radiologi`, `cathlab`)

### MENU: `/penunjang/lab`, `/penunjang/radiologi`, `/penunjang/bank-darah`
- **(+) PLUS v3**: Viewer DICOM Radiologi terintegrasi, LIS menerima hasil via Webhook, dan manajemen stok kantong darah di Bank Darah lebih modern.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Integrasi LIS MLLP**: v3 belum memiliki adapter socket MLLP TCP untuk membaca data langsung dari analyzer lab tua.
  2. **Alur Darah Cito**: Belum ada alur permintaan darah darurat/cito dengan notifikasi prioritas tinggi ke Petugas Bank Darah.
- **DEFECT / BLOCKER v3**:
  - **Hasil Lab Critical Value Tidak Memblokir Discharge**: Alert nilai kritis lab tidak memblokir tombol `dischargeEpisode` di bangsal.
  - **Retur Darah dari Bangsal ke Bank Darah Missing**: Tidak ada method `returnUnit` jika kantong darah tidak jadi ditransfusikan.

---

## BAB V: KASIR, BILLING & KEUANGAN (ROLE: `kasir`)

### MENU: `/kasir/billing` (Billing / Invoice)
- **(+) PLUS v3**: Arsitektur billing lebih modern dengan `createBillingIntent` on-demand dan integrasi Saga Outbox ke Odoo.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Split Invoice Pasien vs Penjamin**: v1 memiliki form split invoice fisik; v3 baru memiliki 1 invoice gabungan.
  2. **Engine Margin Harga Asuransi**: v3 belum memiliki engine `margin-price` otomatis per-penjamin asuransi seperti v1.
- **DEFECT / BLOCKER v3**:
  - **Discharge Ranap Tanpa Cek Lunas Billing**: Pasien Ranap bisa dipulangkan (`dischargeEpisode`) tanpa melunasi tagihan invoice (`status = 'paid'`).
  - **Batal Invoice Paid Tanpa Persetujuan Supervisor**: API void invoice bisa dipanggil kasir biasa tanpa validasi role `supervisor`.

---

## BAB VI: REKAM MEDIS & CASEMIX (ROLE: `rekammedis`, `bpjs`)

### MENU: `/rm/coding` & `/bpjs/casemix`
- **(+) PLUS v3**: Memiliki dashboard monitoring sync SatuSehat.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Module Casemix & Grouper INA-CBG Missing**: File `schema/casemix.ts` masih di-comment out. v3 belum bisa trigger Grouper E-Klaim & Bundle PDF Klaim. **BLOCKER UTAMA BPJS**.
  2. **Pengodean ICD-9-CM Tanpa Validasi Gender**: Koder RM bisa memasukkan kode tindakan persalinan/Sectio Caesarea pada pasien Laki-laki.
- **DEFECT / BLOCKER v3**:
  - **Rekonsiliasi Klaim BPJS Missing**: Belum ada fitur upload file FPK (Form Pengajuan Klaim) dari BPJS untuk rekonsiliasi klaim dibayar vs dikembalikan.

---

## BAB VII: MASTER DATA & SETTINGS (ROLE: `admin`)

### MENU: `/master`, `/pengaturan`
- **(+) PLUS v3**: Manajemen master data lebih terstruktur di bawah grup `/master/*` dengan Form Builder Ajv yang modern.
- **(-) MINUS v3 (Paritas v1)**:
  1. **Remunerasi Jasa Medis Dokter**: Modul pembagian JM Dokter belum ada.
  2. **Supplier & Procurement PO Farmasi**: Modul PO & Faktur Supplier belum ada.
  3. **Jadwal Shift Perawat Bangsal**: Modul manajemen shift Pagi/Siang/Malam perawat belum ada.
- **DEFECT / BLOCKER v3**:
  - **Audit Logs UI Missing**: Backend mencatat log aktivitas di `audit_logs`, tetapi **tidak ada UI di frontend** untuk administrator melihatnya.

---

MEDIA:D:\Hermes-QAeports3-final-zero-mistake-audit-register.md
