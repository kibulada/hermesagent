# Kesia v3 — Daily Zero-Mistake Defect & Blocker Audit Register (12/08/2026)

> Generated 2026-08-12 oleh Salsabila QA.
> Audit harian mendalam berbasis penelusuran kode tingkat baris (source code line-trace) pada codebase terbaru Kesia v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `5300cb6`). Seluruh poin di bawah ini adalah DEFECT & BLOCKER BARU yang BELUM TER-COVER di commit perbaikan dev sebelumnya. Zero-mistake: Setiap poin diverifikasi langsung ke file & baris kode nyata.

---

## 🔴 KELOMPOK 1: CRITICAL BLOCKERS (Potensi Kebocoran Keuangan & Kegagalan Transaksi)

### 1. Discharge Pasien Ranap Tanpa Cek Pelunasan Tagihan Billing (`UNPAID_INVOICE`) — *CRITICAL BILLING*
- **File & Baris**: `apps/api/src/modules/clinical/registration.service.ts:665` (`dischargeEpisode`).
- **Bukti Kode**:
  ```ts
  async dischargeEpisode(episodeId: string, input: { method: string; condition?: string; note?: string }) {
    // ...
    if (ep.bedId) await db.update(B).set({ status: 'CLEANING' }).where(...);
    await db.update(E).set({ status: 'closed', closedAt: new Date(), slotStatus: 'FINISH', ... });
  ```
  `dischargeEpisode` **SAMA SEKALI TIDAK MENGECEK STATUS INVOICE** pasien! Pasien yang tagihannya masih `draft` / belum lunas (`unpaid`) bisa langsung dipulangkan dan bed-nya dibebaskan.
- **Dampak**: Pasien Rawat Inap bisa dipulangkan dari sistem tanpa kasir menerima pembayaran tagihan terlebih dahulu (*kebocoran keuangan RS / financial loss*).

### 2. Pindah Kamar Ranap Overcharge Tarif Kamar Baru (`transferBed`) — *CRITICAL BILLING*
- **File & Baris**: `apps/api/src/modules/clinical/order.service.ts:224` (`episodeCharges`).
- **Bukti Kode**: Kalkulator biaya akomodasi kamar menghitung selisih hari dikalikan `class` akhir episode.
- **Dampak**: Jika pasien dirawat 5 hari di Bed Kelas 3 lalu pindah 1 hari ke Bed Kelas 1 sebelum pulang, **seluruh 6 hari rawat inap ditagihkan dengan tarif Bed Kelas 1**!

### 3. Void Invoice DRAFT Mengabaikan Reversal Intent — *CRITICAL BILLING*
- **File & Baris**: `apps/api/src/modules/billing/billing.service.ts:340` (`replaceInvoice`).
- **Bukti Kode**: Saat invoice DRAFT di-replace / void, status invoice diubah jadi `void`, tetapi `sourceOrderId` pada baris-baris order **TIDAK MENGECUALIKAN REVERSAL STATE**.
- **Dampak**: Memicu duplikasi tagihan ganda (*double-billing*) saat `createBillingIntent` dipanggil ulang.

---

## 🟠 KELOMPOK 2: HIGH DEFECTS (Menghambat Alur Pelayanan Medis & Klaim BPJS)

### 4. Batal Resep Paid Tanpa Auto-Refund / Credit Note Kasir — *HIGH KASIR*
- **File & Baris**: `apps/api/src/modules/clinical/pharmacy.service.ts:350` (`cancelPrescription`).
- **Bukti Kode**: Ketika resep berstatus `paid` dibatalkan oleh dokter/apoteker, status resep berubah jadi `cancelled`, tetapi **SAMA SEKALI TIDAK TERHUBUNG KE MODUL BILLING/KASIR**.
- **Dampak**: Uang pembayaran resep pasien menggantung di sistem tanpa ada jurnal refund / Credit Note di kasir.

### 5. Re-Issue SEP BPJS Duplicate di VClaim Server — *HIGH BPJS*
- **File & Baris**: `apps/api/src/modules/clinical/sep.service.ts:91` (`issue`).
- **Bukti Kode**: Method `issue` langsung memanggil API VClaim `insertSEP` tanpa memblokir re-insert jika `ep.bpjsSepNo` sudah terisi.
- **Dampak**: Terjadi klaim ganda (*duplicate SEP*) di server BPJS VClaim untuk 1 episode kunjungan.

### 6. Hasil Lab Critical Value Tidak Memblokir Discharge — *HIGH CLINICAL*
- **File & Baris**: `apps/api/src/modules/clinical/registration.service.ts:665` (`dischargeEpisode`).
- **Bukti Kode**: `dischargeEpisode` tidak memverifikasi apakah pasien memiliki hasil laboratorium berstatus `CRITICAL_VALUE` yang belum ditindaklanjuti.
- **Dampak**: Pasien dengan nilai laboratorium kritis (misal Hb 4.0 / Kalium 7.0) bisa dipulangkan secara tidak sengaja oleh perawat.

### 7. Hard Delete Dokumen Rekam Medis Pasien Tanpa Soft-Delete — *HIGH DATA LOSS*
- **File & Baris**: `apps/api/src/modules/clinical/registration.controller.ts:82` (`Delete('documents/:docId')`).
- **Bukti Kode**: API mengeksekusi `DELETE FROM patient_documents` secara permanen dari database.
- **Dampak**: Berkas scan rekam medis (KTP/Surat Rujukan) hilang permanen jika salah hapus tanpa audit trail.

---

## 🟡 KELOMPOK 3: MEDIUM DEFECTS & GAP PARITAS v1 (Fitur & Master Data)

### 8. Master Margin Price & Kontrak Asuransi Missing Engine — *MEDIUM BILLING*
- **File & Baris**: `apps/web-clinic/src/features/master/MasterDataPage.tsx` & `billing.service.ts`.
- **Bukti Kode**: Tab Margin Price di master data baru sebatas form input UI, belum terhubung ke kalkulator `episodeCharges` untuk memotong/menaikkan tarif otomatis per-penjamin.
- **Dampak**: Pasien Asuransi Swasta ditagih dengan tarif umum/flat.

### 9. LIS MLLP TCP Socket Adapter Missing — *MEDIUM LAB*
- **File & Baris**: `apps/api/src/modules/clinical/order.service.ts`.
- **Bukti Kode**: v3 baru menerima hasil lab via HTTP POST webhook JSON. Belum ada adapter socket MLLP TCP untuk membaca data langsung dari analyzer lab tua.
- **Dampak**: Mesin analyzer lab tua tidak bisa otomatis mengirim hasil tanpa middleware.

### 10. Audit Logs UI Missing untuk Administrator — *MEDIUM SECURITY*
- **File & Baris**: `apps/api/src/modules/platform/audit.service.ts`.
- **Bukti Kode**: Backend mencatat log aktivitas sensitif ke tabel `audit_logs`, tetapi **TIDAK ADA UI/HALAMAN DI FRONTEND** untuk administrator melihat log audit tersebut.
- **Dampak**: Administrator tidak bisa melacak rekam jejak aktivitas user jika terjadi manipulasi data.

---

## REKAPITULASI HOURLY REGISTER (COMMIT 5300cb6)

| # | Nama Defect / Blocker | Category | File Target |
|---|---|---|---|
| **1** | Discharge Ranap Unpaid (`UNPAID_INVOICE`) | **CRITICAL** | `registration.service.ts:665` |
| **2** | Transfer Bed Overcharge Tarif Kamar Baru | **CRITICAL** | `order.service.ts:224` |
| **3** | Void Invoice DRAFT Double-Billing Risk | **CRITICAL** | `billing.service.ts:340` |
| **4** | Batal Resep Paid Tanpa Refund Kasir | **HIGH** | `pharmacy.service.ts:350` |
| **5** | Re-Issue SEP BPJS Duplicate VClaim | **HIGH** | `sep.service.ts:91` |
| **6** | Critical Lab Value Unblocked Discharge | **HIGH** | `registration.service.ts:665` |
| **7** | Hard Delete Patient Documents | **HIGH** | `registration.controller.ts:82` |
| **8** | Master Margin Price Missing Engine | **MEDIUM** | `billing.service.ts` |
| **9** | LIS MLLP TCP Socket Adapter Missing | **MEDIUM** | `order.service.ts` |
| **10** | Audit Logs UI Missing untuk Admin | **MEDIUM** | `audit.service.ts` |

MEDIA:D:\Hermes-QAeports3-daily-defect-audit-12aug2026.md
