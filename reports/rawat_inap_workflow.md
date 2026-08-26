# Alur Kerja E2E SIRS Kesia - RAWAT INAP

Dokumen ini adalah kelanjutan dari analisis sebelumnya, berfokus pada alur kerja end-to-end untuk modul Rawat Inap (Ranap) di SIRS Kesia.

## A. Titik Masuk & Aktor Utama

-   **Pendaftaran (Admission):** `inpatient/new` (Admisi Ranap).
-   **Perawat Ruangan (Ward Nurse):** `inpatient-nurse`.
-   **Dokter Penanggung Jawab Pelayanan (DPJP):** `inpatient/doctor`.
-   **Farmasi (Pharmacy):** `inpatient-pharmacy`.
-   **Kasir & Staf Billing:** `cashier`, `billing-staff`.
-   **Manajemen Bed:** `bed-management`.

## B. Alur Pendaftaran (Admisi Rawat Inap)

Pendaftaran rawat inap memiliki tiga sumber utama: dari Rawat Jalan (Rajal), dari IGD, atau pendaftaran langsung (planned admission).

### B.1. Sumber Pendaftaran

1.  **Dari Rajal/IGD (via SPRI/Pengantar Rawat Inap):**
    -   Dokter di Rajal (`outpatient-doctor`) atau IGD (`er-doctor`) merekomendasikan rawat inap.
    -   Dokter membuat "Pengantar Rawat Inap" atau SPRI (Surat Perintah Rawat Inap) untuk pasien BPJS.
    -   **FE:** `.../outpatient-doctor/opname-introduction`
    -   **BE:** `sirs-emr-microservice` -> `OpnameIntroductionController.js` -> `POST /api/v1/emr/opname-introduction`
    -   Data pengantar ini akan muncul di loket pendaftaran rawat inap sebagai "pasien rujukan internal".

2.  **Pendaftaran Langsung (Direct/Planned Admission):**
    -   Pasien datang langsung ke loket pendaftaran rawat inap dengan surat pengantar dari dokter luar atau untuk prosedur elektif.
    -   Petugas langsung membuka form pendaftaran di `inpatient/new`.

### B.2. Proses di Loket Admisi Rawat Inap

-   **Aktor:** Petugas Admisi di `kesia-fe/src/pages/inpatient`.
-   **Tampilan:** `InpatientListView.js` menampilkan daftar pasien yang sedang dirawat dan juga daftar antrian dari SPRI/Pengantar.

1.  **Pemilihan Pasien:** Petugas memilih pasien dari daftar antrian atau mencari pasien secara manual.
2.  **Form Pendaftaran (`InPatientDataForm.js`):**
    -   **Verifikasi Data Pasien:** Data demografi dari pendaftaran awal (Rajal/IGD) akan terisi otomatis.
    -   **Pemilihan Penjamin:** Sama seperti Rajal, ini adalah titik krusial.
        -   **Umum:** Pasien membayar deposit.
        -   **Perusahaan:** Verifikasi surat jaminan dari perusahaan.
        -   **BPJS:** Memerlukan SEP Rawat Inap. Petugas akan membuat SEP baru berdasarkan SPRI yang sudah ada.
            -   **BE Bridging:** `sirs-bpjs-microservice` -> `POST /vclaim/sep/insert`.
    -   **Pemilihan Kamar (Bed):**
        -   Petugas mencari dan memilih kamar yang tersedia berdasarkan kelas perawatan yang hak pasien.
        -   **FE:** `kesia-fe/src/pages/bed-management`
        -   **BE:** `sirs-emr-microservice` -> `BedTransactionController.js` -> `POST /api/v1/emr/bed-transaction`. Bed yang dipilih akan di-lock statusnya menjadi "On Administration".
    -   **Input DPJP:** Memilih Dokter Penanggung Jawab Pelayanan.
3.  **Konfirmasi & Check-in:**
    -   Setelah semua data lengkap dan deposit/SEP terverifikasi, pasien di-check-in-kan.
    -   **BE:** `sirs-emr-microservice` -> `InpatientController.js` -> `POST /api/v1/emr/inpatient`.
    -   Status bed berubah dari "On Administration" menjadi "In Bed". Pasien secara resmi masuk ke dalam daftar pasien rawat inap.

## C. Alur Pelayanan di Ruang Perawatan

### C.1. Asesmen dan Perawatan oleh Perawat

-   **Aktor:** Perawat Ruangan di `inpatient-nurse`.
-   Pasien muncul di daftar pasien di unit/ruangan perawat.
-   **CPPT (Catatan Perkembangan Pasien Terintegrasi):** Perawat melakukan asesmen, memberikan obat, melakukan tindakan keperawatan, dan mencatat semuanya di CPPT. Ini adalah log utama selama perawatan.
    -   **FE:** `.../inpatient-nurse/integrated-note`
    -   **BE:** `sirs-emr-microservice` -> `IntegratedNoteController.js`
-   **Observasi TTV:** Pengukuran dan pencatatan tanda-tanda vital secara berkala.
-   **Manajemen Diet:** Berkoordinasi dengan unit gizi.

### C.2. Visite dan Instruksi oleh Dokter (DPJP)

-   **Aktor:** DPJP di `inpatient/doctor`.
-   DPJP melakukan visite harian, mereview perkembangan pasien melalui CPPT.
-   Memberikan instruksi medis baru, mengubah terapi, membuat resep tambahan, atau merencanakan tindakan lebih lanjut. Semua dicatat di CPPT.
-   **Order Penunjang/Konsul:** DPJP dapat membuat order Lab, Radiologi, atau konsul ke spesialis lain langsung dari sistem.

### C.3. Alur Farmasi Rawat Inap

-   **Aktor:** Farmasi di `inpatient-pharmacy`.
-   Resep dari DPJP masuk ke antrian farmasi.
-   Sistem UDD (Unit Dose Dispensing) sering digunakan, di mana farmasi menyiapkan obat per dosis untuk waktu tertentu (misal, 24 jam).
-   Biaya obat dan alkes (alat kesehatan) otomatis ditambahkan ke tagihan pasien.

## D. Alur Transfer dan Discharge

### D.1. Transfer Antar Ruangan

-   Jika kondisi pasien berubah, DPJP bisa menginstruksikan transfer (misal, dari ruang biasa ke ICU).
-   **FE:** `.../inpatient-nurse/transfer-between-room`
-   **BE:** `sirs-emr-microservice` -> `TransferBetweenRoomController.js`. Proses ini melibatkan update `bed_transaction` dan `inpatient` record.

### D.2. Perencanaan Pulang (Discharge Planning)

-   Ketika kondisi pasien membaik dan dinyatakan boleh pulang oleh DPJP.
-   DPJP menulis instruksi pulang di CPPT.
-   Perawat memulai proses perencanaan pulang.
    -   **FE:** `.../inpatient-nurse/discharge-planning`
    -   **BE:** `sirs-emr-microservice` -> `DischargePlanningController.js`.
-   Proses ini mencakup edukasi pasien, penyiapan obat pulang, dan pembuatan surat kontrol jika diperlukan.

### D.3. Proses Pre-Checkout & Finalisasi Billing

1.  **Pre-Checkout:** Perawat mengubah status pasien menjadi "Pre-Checkout".
    -   Ini adalah sinyal bagi `billing-staff` dan `cashier` bahwa pasien akan pulang dan tagihan harus segera diselesaikan.
2.  **Finalisasi Tagihan:** Staf billing mereview semua item tagihan, memastikan tidak ada yang terlewat.
    -   **FE:** `.../billing-staff/inpatient-billing`
3.  **Proses Klaim BPJS/Asuransi:**
    -   Untuk pasien BPJS, staf `casemix` akan melakukan grouping INA-CBG's. Prosesnya mirip dengan Rawat Jalan, namun dengan tarif dan kode yang spesifik untuk rawat inap.
    -   Untuk pasien Asuransi, laporan medis dan rincian tagihan disiapkan untuk proses klaim.
4.  **Pembayaran di Kasir:**
    -   Pasien/keluarga menuju kasir (`cashier`).
    -   **Umum:** Membayar sisa tagihan setelah dikurangi deposit.
    -   **Perusahaan/BPJS:** Membayar selisih/biaya pribadi jika ada. Jika tidak ada, kasir hanya menutup tagihan tanpa transaksi uang.
5.  **Discharge:** Setelah administrasi selesai, kasir mengubah status pasien menjadi "Checked-out".
    -   Perawat mendapat notifikasi dan memperbolehkan pasien pulang.
    -   Status bed di `bed-management` menjadi "dirty", menandakan perlu dibersihkan sebelum bisa diisi lagi.

---
Analisis alur Rawat Inap selesai. Selanjutnya, saya akan menganalisis alur IGD.
