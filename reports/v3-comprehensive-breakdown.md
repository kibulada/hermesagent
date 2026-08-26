# Kesia v3 — Comprehensive Audit Breakdown (Mandatory, Blockers, Suggestions, Feedbacks)

> Generated 2026-08-07 oleh Salsabila QA.
> Berdasarkan audit mendalam pada codebase `E:\WORK KESIA\Project\kesiaV3` (commit `869afa1`), `PARITY-BACKLOG.md`, `PARITY-DEPTH-GAPS.md`, serta penelusuran kata kunci `TODO` / komentar arsitektur di seluruh modul API & FE.

---

## 1. MANDATORY (Wajib Ada & Diperbaiki Sebelum Go-Live / Pilot RS Rujukan)

Berikut adalah poin-poin fitur & fungsionalitas yang **hukumnya wajib** ada sebelum aplikasi v3 dilepas ke produksi / pilot RS Rujukan:

- **1.1 SMTP Reset Password & Email Gateway**
  - **Kondisi**: In-code TODO di `auth.service.ts:101`: "sampai SMTP siap, dev mengembalikan token di response".
  - **Risiko**: Token reset password bocor di JSON response API jika endpoint `/forgot-password` dipanggil di produksi.
  - **Aksi Wajib**: Integrasikan SMTP server / Mailgun / AWS SES nyata agar token hanya dikirim via email, bukan dikembalikan di response HTTP.

- **1.2 Integrasi Jalur Riúil BPJS VClaim & Mobile JKN**
  - **Kondisi**: Seluruh method di `bpjs.service.ts` dan `bpjs-vclaim.client.ts` menggunakan data tiruan (`mock-first`).
  - **Risiko**: Aplikasi tidak bisa mencetak SEP asli, tidak bisa mengirim task antrean ke Mobile JKN, dan tidak bisa mengecek kepesertaan BPJS riil.
  - **Aksi Wajib**: Konfigurasi per-site kredensial BPJS (`consID`, `secretKey`, `userKey`, `serviceUrl`) via database masterdata, bukan environment variable global.

- **1.3 Integrasi Jalur Riil SatuSehat (Kemenkes)**
  - **Kondisi**: In-code TODO di `satusehat.service.ts:64`: "OAuth2 + GET {baseUrl}/Patient?identifier=...". Saat ini NIK diubah jadi IHS tiruan (`mockIhs`).
  - **Risiko**: Data pelayanan pasien tidak tersinkronisasi ke Kemenkes (pelanggaran regulasi Permenkes No. 24 Tahun 2022).
  - **Aksi Wajib**: Hubungkan OAuth2 token Kemenkes + push resource FHIR R4 (`Encounter`, `Condition`, `Observation`, `Procedure`, `MedicationRequest`).

- **1.4 Integrasi Jalur Riil Disdukcapil**
  - **Kondisi**: In-code TODO di `dukcapil.service.ts:65`: "panggil ${cfg.baseUrl} dgn userId/password/ipUser". Saat ini verifikasi NIK bersifat mock echo.
  - **Risiko**: Pendaftaran pasien tidak tervalidasi ke server kependudukan nasional.
  - **Aksi Wajib**: Sambungkan Web Service resmi Disdukcapil sesuai IP User & Kuota RS.

- **1.5 Hard-Gate Tanda Tangan Dokter (PP#7485)**
  - **Kondisi**: v3 memiliki tabel `doctor_signatures` (`migrasi 0075`), tetapi pada `POST /clinical/episodes/:id/finish`, TTD dokter tidak memblokir alur (*default: catat tanpa blokir*).
  - **Risiko**: Dokter bisa menyelesaikan pelayanan/discharge pasien tanpa menandatangani rekam medis (potensi masalah hukum/klaim BPJS ditolak).
  - **Aksi Wajib**: Buat konfigurasi per-site `enforceDoctorSignatureOnFinish = true/false` agar RS bisa mengaktifkan pemblokiran keras sebelum finish.

- **1.6 Penanganan Penjualan Bebas Farmasi (Walk-in OTC / Uang Tunai)**
  - **Kondisi**: Di-flag di `PARITY-DEPTH-GAPS.md` sebagai *money-code* (`migrasi 0097`).
  - **Risiko**: Penjualan obat bebas di apotek tanpa episode registrasi berpotensi tidak tercatat di kasir / jurnal Odoo jika tidak diuji E2E.
  - **Aksi Wajib**: Pastikan transaksi `POST /clinical/pharmacy/sales` memotong stok FEFO batch dan membentuk jurnal pendapatan di Odoo.

- **1.7 Pendaftaran Master Dokter Eksternal (`DoctorExternal`)**
  - **Kondisi**: v1 punya modul pendaftaran dokter eksternal; v3 punya halaman verifikasi telemedicine tetapi **pendaftaran master dokter eksternal nol**.
  - **Risiko**: Telemedicine tidak bisa digunakan jika dokter penanggung jawab berasal dari luar faskes.
  - **Aksi Wajib**: Tambahkan ResourceTab / Form Master Dokter Eksternal di `/master/sdm`.

---

## 2. BLOCKERS (Penghambat Operasional, Rawan Bug, & Blocker QA)

Poin-poin teknis yang berpotensi memicu **bug fatal, kebocoran data, atau kegagalan transaksi** di lingkungan produksi:

- **2.1 Anti-Replay Nonce via Redis (Tenant Middleware)**
  - **Kondisi**: In-code TODO di `tenant.middleware.ts:49`: "TODO prod: nonceSeen via Redis (anti-replay)".
  - **Dampak**: Request HMAC/JWKS yang ditangkap peretas dapat dikirim ulang (*replay attack*) untuk memanipulasi data tenant.
  - **Solusi**: Aktifkan Redis store untuk mencatat `nonce` request yang sudah pernah diproses selama 60 detik.

- **2.2 Server-Side Re-computation pada Form-Engine (Anti-Tamper)**
  - **Kondisi**: In-code TODO di `ajv-form-validator.ts:43`: "TODO spec-04: recompute computed fields server-side (anti-tamper)".
  - **Dampak**: Field kalkulasi otomatis di frontend (seperti *Skor IMT*, *Skor Downe*, *Total Skor Morse*, *Triage Priority*) bisa diubah secara manual lewat payload JSON (`curl/Postman`) sebelum dikirim ke server.
  - **Solusi**: Server wajib menghitung ulang seluruh `def.computeSpec` di `ClinicalObservationService` sebelum disimpan ke database.

- **2.3 Penanganan Inisialisasi OpenTelemetry (Observability)**
  - **Kondisi**: In-code TODO di `apps/api/src/main.ts:10`: "inisialisasi OpenTelemetry SDK SEBELUM import lain".
  - **Dampak**: Tracing HTTP request / database query terputus atau tidak tercatat jika OpenTelemetry di-import terlambat.
  - **Solusi**: Buat file entry-point `instrumentation.ts` yang di-require pertama kali via Node.js `--import` flag.

- **2.4 CORS Allowlist Dynamic Config**
  - **Kondisi**: In-code TODO di `apps/api/src/main.ts:21`: "CORS allowlist per-environment... TODO: dari config".
  - **Dampak**: Kerentanan keamanan jika CORS di-set terlalu permisif atau aplikasi gagal diakses dari domain frontend baru.
  - **Solusi**: Tarik allowlist CORS dari environment variable `CORS_ALLOWED_ORIGINS` (comma-separated).

- **2.5 Posting Account Resolver Odoo (Saga Multi-Company)**
  - **Kondisi**: In-code TODO di `odoo12.adapter.ts:58, 69`: "TODO spec-03 §5 (resolvePostingAccount) & TODO multi-company".
  - **Dampak**: Transaksi invoice dari RS cabang (multi-site/multi-company) akan terposting ke COA / ID company default di Odoo 12, menyebabkan ketidakselarasan laporan keuangan.
  - **Solusi**: Petakan `siteCompanyRef` -> `res.company.id` dan `posting_rule` -> `account_id` secara dinamis dari database `site_coa_mappings`.

- **2.6 Penanganan Session Multi-Role / Role-Switching**
  - **Kondisi**: User context hanya menyimpan 1 active role (`roleKey`).
  - **Dampak**: Pengguna yang memiliki peran ganda (contoh: *Dokter* sekaligus *Kepala Ruangan*) harus melakukan *logout-login* ulang untuk berpindah akses.
  - **Solusi**: Sediakan menu *Switch Active Role* di TopBar yang memperbarui token JWT tanpa mengharuskan input password ulang.

---

## 3. SUGGESTIONS (Peningkatan Arsitektur, Keamanan, & Kepatuhan Regulasi)

Rekomendasi strategis untuk meningkatkan kualitas arsitektur v3 jangka panjang:

- **3.1 Fine-Grained Authorization via Casbin Enforcer Event-Driven**
  - **Kondisi**: In-code TODO di `enforcer.ts:11`: "invalidasi via event identity.policy.changed".
  - **Manfaat**: Perubahan hak akses (privilege) pengguna langsung berdampak detik itu juga tanpa perlu restart service API atau menunggu cache expired.

- **3.2 Custom Menu Order per-Site (Fitur Flag v1 PP#7487/PP#7489)**
  - **Kondisi**: v1 dapat mengubah urutan menu sidebar per RS/site; v3 urutan menu-nya masih statis di `nav.tsx`.
  - **Manfaat**: Memudahkan penyesuaian UX untuk RS yang memiliki alur kerja spesifik tanpa perlu mengubah kode sumber FE.

- **3.3 LIS Analyzer Socket MLLP TCP Bridge**
  - **Kondisi**: `/penunjang/lis` saat ini menerima HL7 ORU^R01 via HTTP POST.
  - **Manfaat**: Sebagian besar mesin analyzer lab tua menggunakan protokol MLLP over TCP (Port 2575). Menyediakan adapter MLLP -> HTTP POST akan mempermudah integrasi laboratorium di lapangan.

- **3.4 DICOM Viewer Advanced (OHIF / Cornerstone.js)**
  - **Kondisi**: Viewer v3 saat ini mengurai biner DICOM pure-JS untuk MONOCHROME 8/16 bit. File terkompresi (JPEG-LS / JPEG2000) dialihkan ke tombol unduh.
  - **Manfaat**: Mampu menampilkan rontgen/CT-Scan terkompresi, Multi-Planar Reconstruction (MPR), dan pengukuran jarak/sudut langsung di browser.

- **3.5 EKG Waveform Drawing Canvas**
  - **Kondisi**: Form `ecg-interpretation` v3 saat ini menginput nilai angka/skalar (Heart Rate, PR Interval, QTc, Aksis).
  - **Manfaat**: Menambahkan kanvas interaktif / penempelan citra grafik strip EKG akan melengkapi kebutuhan rekam medis spesialis jantung.

---

## 4. FEEDBACKS & TECHNICAL DEBT (Temuan Hasil Audit Codebase)

Catatan teknis dari hasil pemindaian kode untuk dirapikan oleh tim developer:

- **4.1 Schema Patient `mobile_no / priority / is_vip`**
  - **Temuan**: Tercatat di `apps/web-clinic/README.md:23`: "kolom `mobile_no/priority/is_vip` belum ada di `patients` (default+TODO spec-02 §5.1)".
  - **Tindakan**: Tambahkan kolom ini di Drizzle schema `patients` dan jalankan DB migration agar data VIP/Prioritas pasien tercatat resmi di database.

- **4.2 Agregasi Demografi Server-Side**
  - **Temuan**: Tercatat di `LaporanDemografiPage.tsx:59`: "Batas ambil untuk agregasi demografi. TODO(follow-up): pindah agregasi ke endpoint server".
  - **Tindakan**: Buat endpoint `/reports/demographics` di `reports.module.ts` agar frontend tidak perlu menarik ribuan row pasien ke browser untuk menghitung grafik umur/gender.

- **4.3 Form-Engine Remote Enum Fetching**
  - **Temuan**: Tercatat di `form-engine/types.ts:32`: "enumSource -> masterdata API; TODO remote fetch".
  - **Tindakan**: Sambungkan UI `FormRenderer` agar field bertipe `enumSource` (seperti dropdown ICD-10, Unit, Standards) menarik opsi secara otomatis dari API backend secara asynchronous.

- **4.4 Sinkronisasi SatuSehat Resource Lanjutan (Condition & Observation)**
  - **Temuan**: `satusehat.service.ts` baru mempublikasikan resource `Encounter`.
  - **Tindakan**: Tambahkan pemeta data dari `integrated_note` ke FHIR `Condition` (Diagnosa) dan FHIR `Observation` (Tanda-tanda Vital) untuk memenuhi standar Kemenkes.

- **4.5 Modul Radioterapi (RT) & Clinical Pathway Implementation**
  - **Temuan**: 7 rute di `nav.tsx` masih berstatus `StubPage` (`/ranap/clinical-pathway`, `/laporan/flow-dashboard`, `/rt/jadwal`, `/rt/course`, `/rt/mesin`, `/rt/ruleset`).
  - **Tindakan**: Lengkapi controller & UI untuk 7 rute ini sebelum modul Radioterapi & Clinical Pathway dipromosikan sebagai fitur siap pakai.

---

## Ringkasan Matriks Prioritas

| Kategori | Jumlah Poin | Dampak Utama | Penanggung Jawab |
|---|---|---|---|
| **1. Mandatory** | 7 Poin | Legalitas, Kepatuhan Regulasi, Validitas Transaksi | Lead Dev / DevOps / Product |
| **2. Blockers** | 6 Poin | Keamanan (Security), Integritas Data, Stabilitas System | Backend Engineer / DBA |
| **3. Suggestions** | 5 Poin | Fleksibilitas UX, Peningkatan Kapabilitas Klinis | Frontend Engineer / Architect |
| **4. Feedbacks / Tech Debt** | 5 Poin | Performa Laporan, Kebersihan Kode (Clean Code) | Core Dev Team |
