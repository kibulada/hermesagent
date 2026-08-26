# Kesia v3 — Critical Defects, Logic Bypasses & Operational Blockers Audit

> Generated 2026-08-07 oleh Salsabila QA.
> Audit berbasis penelusuran kode backend `E:\WORK KESIA\Project\kesiaV3\apps\api\src\modules` (commit `e89ab31`).

---

## 1. DAFTAR DEFECT & LOGIC BYPASS SANGAT KRITIS (CRITICAL / HIGH)

### 1. Dispense Resep Tanpa Cek Stok Cukup (`INSUFFICIENT_STOCK`)
- **Lokasi Kode**: `apps/api/src/modules/clinical/pharmacy.service.ts:deductFefo`
- **Kode Bermasalah**:
  ```ts
  let remaining = Math.ceil(qty);
  for (const b of batches) {
    if (remaining <= 0) break;
    const take = Math.min(remaining, b.qty as number);
    await db.update(B).set({ qty: (b.qty as number) - take }).where(eq(b.id, b.id));
    remaining -= take;
  }
  // Tidak ada pengecekan `if (remaining > 0) throw new DomainError('INSUFFICIENT_STOCK', ...)`
  ```
- **Bypass**: Jika stok obat di database hanya ada 5 tablet tetapi resep meminta 100 tablet, `deductFefo` akan menghabiskan 5 tablet tersebut lalu loop selesai tanpa melempar error.
- **Dampak**: Status resep berubah menjadi `completed` (diserahkan) meskipun stok obat fisik tidak mencukupi! Rekam medis dan stok sistem menjadi tidak sinkron.

---

### 2. Discharge Pasien Ranap Tanpa Cek Tagihan Lunas (`UNPAID_INVOICE`)
- **Lokasi Kode**: `apps/api/src/modules/clinical/registration.service.ts:dischargeEpisode`
- **Kode Bermasalah**: `dischargeEpisode` langsung mengubah status episode menjadi `closed`, membebaskan bed menjadi `CLEANING`, dan memanggil SEP return. Endpoint **SAMA SEKALI TIDAK mengecek apakah pasien masih memiliki invoice berstatus `draft` / belum dibayar**.
- **Dampak**: Pasien Rawat Inap bisa dipulangkan dari sistem (bed dibebaskan) tanpa kasir menerima pembayaran tagihan terlebih dahulu. Potensi kebocoran pendapatan RS (*financial loss*).

---

### 3. Pendaftaran Rajal Ganda di Poli & Tanggal Sama saat `INPROGRESS`
- **Lokasi Kode**: `apps/api/src/modules/clinical/registration.service.ts:createEpisode`
- **Kode Bermasalah**: Commit `ba2ab12` memasang guard `IGD_ALREADY_OPEN` untuk `emergency`, tetapi **belum dipasang untuk `outpatient`**.
- **Dampak**: Pasien yang sedang berada di dalam ruangan dokter poli (status `INPROGRESS`) bisa didaftarkan ulang ke poli yang sama pada hari yang sama, memicu antrean ganda & rekam medis terpisah.

---

### 4. Admisi Ranap Ganda (`admitToInpatient`) untuk Pasien yang Sudah Inpatient
- **Lokasi Kode**: `apps/api/src/modules/clinical/registration.service.ts:admitToInpatient`
- **Kode Bermasalah**: `admitToInpatient` tidak memverifikasi apakah pasien sudah memiliki episode `inpatient` aktif (`isNull(closedAt)`).
- **Dampak**: Pasien yang sudah tidur di Bed A bisa di-admit ulang ke episode `inpatient` kedua, menyebabkan ganda tagihan akomodasi kamar & kekacauan data BOR.

---

### 5. Duplikasi Visite Harian Dokter
- **Lokasi Kode**: `apps/api/src/modules/clinical/registration.service.ts:recordVisite`
- **Kode Bermasalah**: `recordVisite` tidak memvalidasi kombinasi unik `(episodeId, doctorId, visiteDate)`.
- **Dampak**: Jika dokter/perawat menglik simpan visite 3 kali, pasien akan ditagih biaya visite 3x lipat pada hari yang sama di `episodeCharges`.

---

### 6. Re-Issue SEP BPJS Tanpa Pembatalan SEP Lama
- **Lokasi Kode**: `apps/api/src/modules/clinical/sep.service.ts:issue`
- **Kode Bermasalah**: `issue` langsung memanggil API VClaim `insertSEP` meskipun `ep.bpjsSepNo` sudah terisi.
- **Dampak**: Terjadi pendaftaran klaim ganda di server BPJS (VClaim) untuk 1 episode kunjungan.

---

### 7. Penjualan OTC Farmasi (`createSale`) Tanpa Cek Stok Batch
- **Lokasi Kode**: `apps/api/src/modules/clinical/pharmacy.service.ts:createSale`
- **Kode Bermasalah**: `createSale` membuat penjualan obat bebas tanpa memvalidasi ketersediaan stok FEFO per batch sebelum melakukan pemotongan stok `applyStockMovement`.
- **Dampak**: Penjualan obat bebas bisa dilakukan meskipun stok di database nol/minus.

---

## 2. MATRIKS URGENSI DEFECT

| Defect / Bypass | Modul | Risk Level | Dampak Kerugian / Operasional |
|---|---|---|---|
| **1. Dispense Tanpa Cek Stok** | Farmasi | **CRITICAL** | Stok minus, resep dianggap lengkap padahal barang tidak ada. |
| **2. Discharge Pasien Unpaid** | Ranap / Kasir | **CRITICAL** | Pasien pulang tanpa bayar, kebocoran uang RS. |
| **3. Reg Rajal Ganda INPROGRESS** | Rajal / Reg | **HIGH** | Rekam medis ganda, antrean poli kacau. |
| **4. Reg Ranap Ganda (`admit`)** | Ranap | **HIGH** | Pasien terdaftar di 2 bed, double tagihan kamar. |
| **5. Duplikasi Visite Dokter** | Ranap / Dokter | **HIGH** | Overcharge tarif visite dokter 2x–3x lipat. |
| **6. Re-Issue SEP BPJS** | BPJS | **MEDIUM** | Duplicate SEP di VClaim BPJS. |
| **7. OTC Sale Overdraw** | Farmasi OTC | **MEDIUM** | Penjualan obat bebas melebihi stok fisik. |

---

## 3. RECOMMENDED FIXES FOR DEV TEAM

1. **Fix Dispense Stock Check (`deductFefo`)**:
   ```ts
   if (remaining > 0) {
     throw new DomainError('INSUFFICIENT_STOCK', `Stok obat tidak mencukupi (kurang ${remaining})`);
   }
   ```
2. **Fix Discharge Unpaid Check (`dischargeEpisode`)**:
   ```ts
   const [unpaid] = await db.select({ id: schema.invoices.id }).from(schema.invoices)
     .where(and(eq(schema.invoices.siteId, ctx.siteId), eq(schema.invoices.episodeId, episodeId), eq(schema.invoices.status, 'draft')));
   if (unpaid) {
     throw new DomainError('UNPAID_INVOICE_EXISTS', 'Pasien masih memiliki tagihan yang belum dilunasi');
   }
   ```
3. **Fix Rajal Already Open (`createEpisode`)**:
   Copy guard `IGD_ALREADY_OPEN` dari commit `ba2ab12` untuk `input.source === 'outpatient'`.
