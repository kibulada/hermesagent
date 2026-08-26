# Alur Kerja E2E SIRS Kesia - INSTALASI GAWAT DARURAT (IGD)

Dokumen ini melengkapi seri analisis dengan merinci alur kerja end-to-end untuk modul IGD (Emergency Room), yang dirancang untuk menangani pasien dengan kondisi gawat darurat.

## A. Prinsip Utama & Aktor

-   **Prinsip Utama:** *Life-saving first, administration later*. Proses administrasi seringkali berjalan paralel atau bahkan setelah tindakan penyelamatan awal dilakukan.
-   **Aktor Utama:**
    -   **Petugas Pendaftaran IGD:** `er-registration`.
    -   **Perawat Triase & IGD:** `er-nurse`.
    -   **Dokter Jaga IGD:** `er-doctor`.
    -   **Apoteker IGD:** `er-pharmacy`.
    -   **Staf Billing & Kasir:** `billing-staff`, `cashier`.

## B. Alur Pendaftaran & Triase

Ini adalah tahap paling kritis dan berbeda dari unit lain.

### B.1. Kedatangan Pasien

1.  **Pasien Datang:** Pasien tiba di IGD, bisa diantar keluarga atau ambulans.
2.  **Triase oleh Perawat:** Pasien segera dibawa ke area triase. Perawat melakukan penilaian cepat untuk menentukan tingkat kegawatan.
    -   **FE:** `kesia-fe/src/pages/er-nurse/Triage`
    -   **Logika:** Sistem menggunakan skor (misalnya ATS - Australasian Triage Scale) berdasarkan vital sign, keluhan utama, dan mekanisme cedera untuk mengklasifikasikan pasien ke dalam beberapa level prioritas (misal: Merah, Kuning, Hijau, Hitam).
    -   **BE:** `sirs-emr-microservice` -> `TriageController.js` -> `POST /api/v1/emr/triage`.
    -   **Output:** Pasien langsung diarahkan ke zona perawatan yang sesuai (Resusitasi, Kritis, Non-Kritis) berdasarkan hasil triase.

### B.2. Pendaftaran Pasien (Paralel)

-   **Aktor:** Petugas Pendaftaran IGD di `er-registration`.
-   Pendaftaran seringkali dilakukan oleh keluarga pasien saat pasien sudah ditangani secara medis.
1.  **Pencarian Pasien:** Petugas mencari data pasien di sistem.
2.  **Pasien Tidak Dikenal/Mr. X:** Jika identitas pasien tidak diketahui (misal: pasien tidak sadar dan tanpa keluarga), sistem memungkinkan pendaftaran sebagai "Mr. X" atau "Mrs. Y" dengan data minimal. Data ini bisa dilengkapi atau digabungkan (`merge patient`) nanti.
3.  **Pendaftaran Normal:** Jika data bisa didapat, prosesnya mirip dengan pendaftaran Rajal: mengumpulkan data demografi dan penjamin.
    -   **FE:** `kesia-fe/src/pages/er-registration/add`
    -   **BE:** `sirs-emr-microservice` -> `ErController.js` -> `POST /api/v1/emr/er`.
4.  **Penjamin:**
    -   **BPJS:** Dalam kondisi darurat, pasien BPJS bisa langsung ke IGD rumah sakit tanpa rujukan FKTP. Petugas akan membuat SEP IGD.
    -   **Umum/Perusahaan:** Penjamin dicatat, namun fokus utama tetap pada penanganan medis. Verifikasi jaminan bisa menyusul.

## C. Alur Pelayanan Medis di IGD

### C.1. Asesmen Awal oleh Dokter & Perawat

-   **Aktor:** `er-doctor`, `er-nurse`.
-   Di zona perawatan, tim medis melakukan asesmen yang lebih mendalam (Primary & Secondary Survey).
-   **FE:** `.../er-doctor/InitialAssessmentDoctor`, `.../er-nurse/AssessmentEr`
-   Semua temuan, instruksi, dan tindakan dicatat secara real-time di CPPT versi IGD.
-   **BE:** `sirs-emr-microservice` -> `IntegratedNoteController.js`

### C.2. Tindakan dan Terapi Darurat

-   Dokter memberikan instruksi untuk tindakan penyelamatan, pemberian obat darurat, pemasangan infus, dll.
-   **FE:** `.../er-doctor/OrderAction`
-   Perawat mengeksekusi instruksi dan mencatatnya.
-   Biaya tindakan dan obat/alkes secara otomatis ditambahkan ke tagihan sementara (`temporary billing`) pasien.
-   **Permintaan Penunjang:** Order CITO (segera) untuk Lab atau Radiologi dapat dibuat.
    -   `.../er-doctor/medical-support`. Hasil akan muncul di EMR IGD setelah selesai.

## D. Alur Farmasi IGD

-   Farmasi IGD atau depo farmasi darurat melayani permintaan obat CITO.
-   Obat dan alkes yang digunakan langsung dipotong dari stok darurat dan dibebankan ke pasien.
-   **FE:** `er-pharmacy`.

## E. Alur Disposisi Pasien (Penentuan Nasib Pasien)

Setelah stabilisasi dan observasi, Dokter Jaga IGD akan menentukan langkah selanjutnya:

1.  **Boleh Pulang (Discharged):**
    -   Kondisi pasien tidak memerlukan rawat inap.
    -   Dokter memberikan resep obat pulang dan surat keterangan sakit jika perlu.
    -   Pasien/keluarga menyelesaikan administrasi di kasir.
    -   **FE:** `.../er-doctor/DischargeResume`.

2.  **Rawat Inap (Admitted):**
    -   Kondisi pasien memerlukan perawatan lebih lanjut.
    -   Dokter membuat "Pengantar Rawat Inap" dari IGD.
    -   **Proses ini sama seperti alur pendaftaran rawat inap dari Rajal:** `OpnameIntroductionController.js` diaktifkan, dan pasien masuk ke antrian pendaftaran ranap. Keluarga pasien akan mengurus administrasi di loket rawat inap.
    -   **Billing:** Tagihan IGD akan digabungkan (`merge billing`) dengan tagihan rawat inap nantinya. Ini penting untuk pasien BPJS agar menjadi satu episode perawatan.

3.  **Dirujuk (Referred):**
    -   Pasien memerlukan penanganan yang tidak dapat disediakan oleh rumah sakit (misal: perlu spesialis/alat yang tidak ada).
    -   Dokter membuat surat rujukan ke rumah sakit lain.
    -   Pasien/keluarga menyelesaikan administrasi untuk perawatan yang telah diberikan di IGD sebelum ditransfer.

## F. Alur Administrasi & Pembayaran IGD

-   Prinsipnya sama dengan unit lain, namun seringkali diselesaikan setelah disposisi pasien jelas.
-   **Tagihan:** Di-generate oleh `sirs-emr-microservice` -> `InvoiceController.js`, seringkali dengan flag `is_er_invoice=true`.
-   **Pembayaran:**
    -   **Jika pasien pulang:** Keluarga menyelesaikan tagihan di kasir.
    -   **Jika pasien rawat inap:** Tagihan IGD "ditahan" dan akan digabungkan dengan tagihan rawat inap oleh `billing-staff`.
        -   **BE:** Ada logika di `InvoiceController.js` atau proses billing yang mencari `opname_introduction` untuk menarik `er_episode_id` dan menggabungkan biayanya.
    -   **Klaim BPJS:** Episode IGD dan Rawat Inap harus dijadikan satu kesatuan klaim agar terbayar oleh BPJS. Jika dipisah, kemungkinan besar klaim IGD akan ditolak.

---
Analisis alur IGD telah selesai. Dengan ini, ketiga alur utama (Rajal, Ranap, IGD) telah dipetakan. Langkah terakhir adalah menyusun laporan gabungan.
