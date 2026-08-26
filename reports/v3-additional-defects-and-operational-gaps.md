# Kesia v3 — Additional Defects, Billing Integration Gaps & Operational Bypasses Audit

> Generated 2026-08-07 oleh Salsabila QA.
> Audit berbasis penelusuran kode backend `E:\WORK KESIA\Project\kesiaV3\apps\api\src\modules` (commit `e89ab31`).

---

## 1. TEMUAN UTAMA: GAP OPERASIONAL & LOGIKA KASIR/BILLING

### 1. Kunjungan Baru Daftar Rajal/IGD TIDAK MUNCUL di List Kasir (`Unbilled Worklist Missing`)
- **Penyebab**: `listInvoices` (`GET /billing/invoices`) hanya membaca dari tabel `invoices`. Tabel `invoices` **TIDAK dibentuk otomatis** saat pendaftaran Rajal/IGD/Ranap!
- **Dampak**: Pasien yang baru selesai mendaftar, diperiksa dokter, atau selesai IGD **SAMA SEKALI TIDAK MUNCUL** di daftar billing Kasir. Kasir terisolasi dan tidak tahu siapa saja pasien yang belum ditagih kecuali jika menginput `episodeId` secara manual.
- **Rekomendasi**: Buat endpoint `GET /billing/unbilled-episodes` yang menampilkan episode aktif berstatus non-closed yang belum memiliki invoice.

---

### 2. Uang Deposit Pasien TIDAK TERINTEGRASI dengan Invoice Kasir (`Deposit-Invoice Disconnect`)
- **Penyebab**: `billing.service.ts` **SAMA SEKALI TIDAK MEMBACA ATAU MEMOTONG SALDO DEPOSIT** (`depositPayments`).
- **Dampak**: Jika pasien telah membayar deposit sebesar Rp 500.000 saat registrasi (`POST /clinical/episodes/:id/deposit`), saldo tersebut **TIDAK OTOMATIS MEMOTONG** total tagihan pada invoice kasir saat `createBillingIntent` atau `payInvoice`! Kasir harus menghitung selisih deposit dan melakukan refund manual.

---

### 3. Retur Obat Farmasi TIDAK MERETUR BARIS INVOICE DRAFT (`Return Prescription Invoice Leak`)
- **Penyebab**: Saat `returnPrescription` dipanggil di farmasi, fungsi hanya menambah stok obat kembali ke inventaris. **SAMA SEKALI TIDAK memperbarui / menghapus baris obat** di tabel `invoiceLines` pada invoice DRAFT episode tersebut.
- **Dampak**: Pasien meretur obat ke apotek, tetapi saat kasir mencetak invoice, **harga obat yang diretur MASIH TERTAGIH di invoice pasien**!

---

### 4. Batal Kunjungan (`cancelEpisode`) TIDAK MEMBATALKAN ORDER & INVOICE
- **Penyebab**: Saat `POST /clinical/episodes/:id/cancel` dipanggil, status episode berubah jadi `cancelled`. Namun, order lab/radiologi/resep yang terlanjur dibuat di episode tersebut **tetap berstatus `ordered`/`draft`**, dan invoice draft-nya **tidak otomatis di-void**.
- **Dampak**: Order zombie tetap muncul di worklist lab/radiologi/farmasi dan invoice menggantung di billing.

---

### 5. Tidak Ada Guard Batas Maksimal Kuota Pasien Onsite vs Online
- **Penyebab**: Validation kuota di `registration.service.ts` hanya memisahkan kuota `quota` dan `quotaBpjs`. Tidak ada pembagian kuota untuk antrean `onsite` vs `online` (Mobile JKN / Web).
- **Dampak**: Pendaftaran onsite di RS bisa menghabiskan seluruh kuota antrean, menyebabkan pendaftaran online gagal/terunci, atau sebaliknya.

---

### 6. Pindah Kamar Ranap (`transferBed`) TIDAK MEMPROTET RENTANG TANGGAL AKOMODASI
- **Penyebab**: Saat pasien pindah dari Bed Kelas 3 ke Bed Kelas 1 via `/ops/beds/transfer`, kalkulator `episodeCharges` memicu akomodasi kamar berdasarkan `class` akhir episode.
- **Dampak**: Hari-hari yang dihabiskan pasien di Bed Kelas 3 bisa ikut ditagihkan dengan tarif Bed Kelas 1 (*overcharging tarif kamar*).

---

### 7. Pembuat Resep Racikan Tanpa Dosis Maksimal (Overdose Risk)
- **Penyebab**: Form resep `createPrescription` menerima `itemKind: 'racikan'` tetapi tidak melakukan validasi Dosis Maksimal (DM) / Dosis Lazim (DL) zat aktif obat.
- **Dampak**: Resep racikan dengan akumulasi dosis berbahaya lolos ke apotek tanpa peringatan sistem.

---

### 8. Laporan Sensus Harian Ranap (RL 1.2) Tanpa Isolasi Patient Transfer
- **Penyebab**: Query sensus ranap menghitung BOR/LOS berdasarkan `checkInDate` dan `closedAt` episode.
- **Dampak**: Perpindahan bed antar ruangan (transfer) dihitung sebagai pasien keluar-masuk baru, merusak perhitungan Hari Perawatan (HP) resmi RL.

---

### 9. Hasil Lab Cito / Critical Value Alert TIDAK MEMBLOKIR DISCHARGE
- **Penyebab**: Jika hasil lab ber-status *Critical Value* (misal Hb 4.0), sistem mengirimkan alert ke notifications, tetapi **TIDAK MEMBLOKIR** proses `dischargeEpisode`.
- **Dampak**: Pasien dengan kondisi kritis yang belum ditangani dokter bisa secara tidak sengaja dipulangkan oleh perawat.

---

### 10. Multi-Tenant Data Leakage via Unvalidated Body `siteId`
- **Penyebab**: Beberapa schema Zod di `clinical.schemas.ts` menerima `siteId` opsional di body request.
- **Dampak**: Operator dari Site A dapat mencoba menyisipkan `siteId` Site B pada payload JSON untuk membaca/menulis data rumah sakit lain (pelanggaran RLS/Tenant isolation).

---

## 2. REKAPITULASI TOTAL DEFECT / GAP DI v3

Dengan temuan baru ini, total ada **17 Defect, Logic Bypass & Operational Gap Kritis** yang teridentifikasi di v3:

1. **Kasir Unbilled Worklist Missing** (Kasir tidak tahu siapa yang harus ditagih)
2. **Deposit-Invoice Disconnect** (Uang deposit tidak memotong invoice)
3. **Return Prescription Invoice Leak** (Obat diretur tapi tetap ditagih)
4. **Cancel Episode Cascade Missing** (Batal kunjungan tidak membatalkan order)
5. **Dispense Tanpa Cek Stok** (Stok minus / diserahkan tanpa barang)
6. **Discharge Pasien Unpaid** (Pasien pulang tanpa bayar)
7. **Pendaftaran Rajal Ganda INPROGRESS** (Daftar berulang ke poli sama)
8. **Admisi Ranap Ganda** (Satu pasien punya 2 episode inpatient)
9. **Duplikasi Visite Dokter** (Ditagih visite 3x sehari)
10. **Transfer Bed Overcharge** (Kamar kelas lama ditagih tarif kelas baru)
11. **Quota Onsite vs Online Lockout** (Onsite menghabiskan kuota online)
12. **Racikan Overdose Risk** (Tanpa kontrol dosis maksimal)
13. **Re-Issue SEP BPJS Duplicate** (Duplicate claim VClaim)
14. **OTC Sale Overdraw** (Jual obat bebas tanpa stok)
15. **Sensus Ranap Transfer Glitch** (BOR/LOS RL rusak akibat transfer bed)
16. **Critical Lab Value Unblocked Discharge** (Pasien kritis ter-discharge)
17. **Zod Body siteId Leakage** (Potensi cross-tenant write)
