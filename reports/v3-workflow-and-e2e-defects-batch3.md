# Kesia v3 — Additional End-to-End Workflow Defects, Housekeeping Lockouts & Clinical Logic Bypasses (Batch 3 Audit)

> Generated 2026-08-07 oleh Salsabila QA.
> Audit berbasis penelusuran kode frontend & backend `E:\WORK KESIA\Project\kesiaV3` (commit `e89ab31`).

---

## 1. DAFTAR DEFECT & BLOCKER ALUR E2E BARU

### 1. Lockout Bed Ranap Terkunci Status `CLEANING` Tanpa Menu Housekeeping
- **Lokasi Kode**: `registration.service.ts:dischargeEpisode` & `ops.service.ts:setBedStatus`
- **Celah**: Saat pasien di-discharge (`dischargeEpisode`), status bed otomatis diubah menjadi `CLEANING`. Di backend API tersedia method `setBedStatus` untuk mengubah status bed kembali ke `AVAILABLE`. Namun di frontend `web-clinic`, **TIDAK ADA HALAMAN ATAU TOMBOL HOUSEKEEPING** untuk memanggil `setBedStatus`!
- **Dampak**: Semua bed yang pasiennya dipulangkan akan **terkunci selamanya di status `CLEANING` di Papan Bangsal Ranap**! Bed tersebut tidak bisa lagi di-assign (`assignBed`) ke pasien Ranap baru karena `assignBed` menolak bed yang berstatus bukan `AVAILABLE`/`WAITLIST`.

---

### 2. Konsul Inter-Spesialis / Konsul Poli Tanpa Worklist Target
- **Lokasi Kode**: `care-plan.service.ts:createCarePlan` & `care-plan.service.ts:respondConsult`
- **Celah**: Ketika Dokter Poli A membuat rujukan/konsul internal ke Dokter Poli B (`POST /care-plans` type=`consult`), record tersimpan dengan status `proposed`. Namun, sistem **TIDAK MEMBENTUK EPISODE BARU ATAU ENTRY WORKLIST** untuk Poli B!
- **Dampak**: Dokter Poli B tidak dapat melihat pasien rujukan konsul tersebut di menu Worklist (`/dokter/worklist` atau `/emr/worklist`). Pasien terpaksa harus mengantre dan didaftarkan ulang secara manual di loket registrasi untuk mendapat episode baru.

---

### 3. Logika Resep Iterasi (Iter / Pengulangan Resep) Tidak Berfungsi
- **Lokasi Kode**: `pharmacy.service.ts:dispense`
- **Celah**: Tabel `prescriptions` menyimpan field `isIter`, `iterValidUntil`, dan `iterMaxCount`. Namun saat farmasi melakukan penyerahan obat (`dispense`), **SAMA SEKALI TIDAK ADA LOGIKA COUNTER/SEQUENCE** yang melacak pengambilan resep iterasi ke-1, ke-2, atau ke-3.
- **Dampak**: Resep iterasi kronis (seperti obat Hipertensi / Diabetes) tidak dapat diulang pengambilannya di apotek tanpa membuat resep baru dari awal.

---

### 4. Batal Resep Pasca Paid Tanpa Auto-Refund / Credit Note Kasir
- **Lokasi Kode**: `clinical.controller.ts:454 cancelPrescription` & `billing.service.ts`
- **Celah**: Ketika resep berstatus `paid` (sudah dibayar di kasir) dibatalkan via `POST /prescriptions/:id/cancel`, status resep berubah menjadi `cancelled`. Namun, **SAMA SEKALI TIDAK ADA INTEGRASI KE MODUL BILLING/KASIR** untuk membatalkan transaksi pembayaran atau menerbitkan Credit Note refund.
- **Dampak**: Pasien sudah membayar resep di kasir, tetapi ketika resep dibatalkan oleh dokter/apoteker, uang pasien menggantung di sistem tanpa ada jurnal pengembalian di kasir.

---

### 5. Pendaftaran BPJS Tanpa Validasi Rujukan Online VClaim
- **Lokasi Kode**: `registration.service.ts:1031 createEpisode`
- **Celah**: Pada pendaftaran BPJS, `createEpisode` hanya mengecek apakah string `bpjsNoRujukan` atau `bpjsNoSkdp` tidak kosong (`non-empty`). Server **SAMA SEKALI TIDAK MEMANGGIL API VClaim (`checkRujukan`)** untuk memverifikasi apakah rujukan tersebut valid, aktif, dan sesuai dengan Poli/DPJP tujuan.
- **Dampak**: Operator registrasi bisa memasukkan sembarang teks/nomor rujukan palsu saat pendaftaran. Klaim BPJS akan otomatis gugur/ditolak saat diajukan di akhir bulan.

---

## 2. REKAPITULASI MATRIKS 22 DEFECT & BLOCKER KRITIS TERIDENTIFIKASI DI v3

1. **Bed Lockout Status CLEANING** (Bed terkunci selamanya setelah discharge)
2. **Unbilled Worklist Missing** (Kasir tidak melihat daftar pasien belum ditagih)
3. **Deposit-Invoice Disconnect** (Uang deposit tidak memotong invoice kasir)
4. **Return Prescription Invoice Leak** (Obat diretur tapi tetap ditagih)
5. **Dispense Tanpa Cek Stok** (Stok minus / obat diserahkan tanpa barang)
6. **Discharge Pasien Unpaid** (Pasien inap dipulangkan tanpa lunas tagihan)
7. **Consul Inter-Spesialis No Worklist** (Konsul internal tidak muncul di dokter B)
8. **Iter Prescription Logic Dead** (Resep iterasi kronis tidak bisa diulang)
9. **Cancel Paid Prescription No Refund** (Resep batal tidak meretur uang kasir)
10. **BPJS No Rujukan Unvalidated VClaim** (Rujukan palsu lolos registrasi)
11. **Cancel Episode Cascade Missing** (Batal kunjungan tidak membatalkan order)
12. **Pendaftaran Rajal Ganda INPROGRESS** (Daftar berulang ke poli sama)
13. **Admisi Ranap Ganda** (Satu pasien punya 2 episode inpatient)
14. **Duplikasi Visite Dokter** (Ditagih visite 3x sehari)
15. **Transfer Bed Overcharge** (Kamar kelas lama ditagih tarif kelas baru)
16. **Quota Onsite vs Online Lockout** (Onsite menghabiskan kuota online)
17. **Racikan Overdose Risk** (Tanpa kontrol dosis maksimal)
18. **Re-Issue SEP BPJS Duplicate** (Duplicate claim VClaim)
19. **OTC Sale Overdraw** (Jual obat bebas tanpa stok)
20. **Sensus Ranap Transfer Glitch** (BOR/LOS RL rusak akibat transfer bed)
21. **Critical Lab Value Unblocked Discharge** (Pasien kritis ter-discharge)
22. **Zod Body siteId Leakage** (Potensi cross-tenant write)
