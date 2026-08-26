# Kesia v3 — State Machine & Business Logic Flow Audit (Pendaftaran Ganda, Order Zombie, & State Leaks)

> Generated 2026-08-07 oleh Salsabila QA.
> Audit berbasis penelusuran kode backend `E:\WORK KESIA\Project\kesiaV3\apps\api\src\modules\clinical` (commit `869afa1`).

---

## 1. TEMUAN KUNCI: ANOMALI ALUR STATE MACHINE

### Case 1: Pendaftaran Ganda Rajal pada Unit & Tanggal Sama saat Status `INPROGRESS` (Konfirmasi Kibul)
- **Lokasi Kode**: `registration.service.ts:925 createEpisode` & `registration.service.ts:522 registerWalkin`.
- **Anomali**: `createEpisode` hanya menghitung kuota jadwal dokter (bila ada) dan hak akses unit operator. **Sama sekali TIDAK ADA query/guard** yang mengecek apakah pasien (`patientId`) tersebut sedang memiliki episode aktif (`status != 'closed' AND status != 'cancelled'`) di poli (`unitId`) yang sama pada tanggal tersebut (`treatmentDate`).
- **Dampak**: Pasien yang sedang di dalam ruangan dokter (status `INPROGRESS`) dapat didaftarkan ulang berulang kali. Ini menghasilkan nomor antrean ganda, rekam medis terpisah, dan kebingungan antrean di TTV perawat.
- **Rekomendasi Guard**:
  ```ts
  const [active] = await db.select({ id: schema.emrEpisodes.id })
    .from(schema.emrEpisodes)
    .where(and(
      eq(schema.emrEpisodes.siteId, ctx.siteId),
      eq(schema.emrEpisodes.patientId, input.patientId),
      eq(schema.emrEpisodes.unitId, unitId),
      eq(schema.emrEpisodes.treatmentDate, treatmentDate),
      inArray(schema.emrEpisodes.status, ['registered', 'calling', 'in_progress', 'INPROGRESS', 'waitlist'])
    )).limit(1);
  if (active) throw new DomainError('ACTIVE_EPISODE_EXISTS', 'Pasien masih memiliki kunjungan aktif di poli ini pada tanggal tersebut');
  ```

---

### Case 2: Order Resep & Penunjang Zombie pada Episode yang Sudah Discharged / Cancelled
- **Lokasi Kode**: `order.service.ts:13 createPrescription` & `order.service.ts:121 createSupportOrder`.
- **Anomali**: `createPrescription` hanya membaca `reference` episode untuk menentukan kanal apotek (`online` vs `onsite`). Endpoint **TIDAK mengecek field `status` pada episode**.
- **Dampak**: Dokter atau user yang memiliki episodeId lama yang sudah `closed` atau `cancelled` masih bisa mengirimkan Order Resep (Obat) dan Order Support (Lab/Radiologi) baru. Order ini masuk ke worklist farmasi/lab dan membentuk tagihan `EpisodeCharges` pada episode yang sudah ditutup!
- **Rekomendasi Guard**:
  ```ts
  if (ep.status === 'closed' || ep.status === 'cancelled') {
    throw new DomainError('EPISODE_NOT_ACTIVE', 'Tidak dapat membuat order pada kunjungan yang sudah selesai atau dibatalkan');
  }
  ```

---

### Case 3: Admisi Ganda Rawat Inap (`admitToInpatient`) untuk Pasien yang Sudah Inpatient
- **Lokasi Kode**: `registration.service.ts:480 admitToInpatient`.
- **Anomali**: Function mengecek ketersediaan `carePlans` bertipe `inpatient` pada `episodeId` asal. Jika dokter membuat SPRI baru (`order-inpatient`), `admitToInpatient` dapat dipanggil kembali untuk menghasilkan `emrEpisodes` bertipe `inpatient` kedua.
- **Dampak**: Pasien yang sudah tidur di bed Ranap A bisa memiliki 2 episode `inpatient` aktif sekaligus, menyebabkan ganda tagihan kamar (akomodasi) dan kekacauan BOR pada Papan Bangsal.
- **Rekomendasi Guard**:
  ```ts
  const [existingInp] = await db.select({ id: schema.emrEpisodes.id })
    .from(schema.emrEpisodes)
    .where(and(
      eq(schema.emrEpisodes.siteId, ctx.siteId),
      eq(schema.emrEpisodes.patientId, src.patientId),
      eq(schema.emrEpisodes.source, 'inpatient'),
      ne(schema.emrEpisodes.status, 'closed'),
      ne(schema.emrEpisodes.status, 'cancelled')
    )).limit(1);
  if (existingInp) throw new DomainError('ALREADY_INPATIENT', 'Pasien masih dalam status Rawat Inap aktif');
  ```

---

### Case 4: Duplikasi Visite Harian Dokter pada Hari yang Sama
- **Lokasi Kode**: `registration.service.ts:recordVisite`.
- **Anomali**: `recordVisite` langsung memasukkan tarif visite ke `episodeCharges` (`source='visite'`). Tidak ada batasan unik `(episodeId, doctorId, visiteDate)`.
- **Dampak**: Jika dokter/perawat tidak sengaja menekan tombol "Simpan Visite" 3 kali (atau terjadi koneksi lambat), sistem akan mencatat 3 baris visite dan menagihkan tarif visite 3x lipat ke pasien pada hari tersebut.
- **Rekomendasi Guard**:
  ```ts
  const [visited] = await db.select({ id: schema.visites.id })
    .from(schema.visites)
    .where(and(
      eq(schema.visites.siteId, ctx.siteId),
      eq(schema.visites.episodeId, episodeId),
      eq(schema.visites.doctorId, ctx.userId),
      eq(schema.visites.visiteDate, localDate())
    )).limit(1);
  if (visited) throw new DomainError('VISITE_ALREADY_RECORDED', 'Visite dokter untuk hari ini sudah dicatat');
  ```

---

### Case 5: Re-Issue SEP BPJS Tanpa Pembatalan SEP Lama
- **Lokasi Kode**: `sep.service.ts:91 issue`.
- **Anomali**: `issue` langsung memanggil API VClaim `insertSEP`. Jika episode sudah memiliki nomor SEP sebelumnya (`bpjs_sep_no` tidak null), function tidak memblokir re-issue kecuali jika ditangani secara manual.
- **Dampak**: Terjadi pendaftaran klaim ganda di server BPJS (VClaim) untuk 1 episode kunjungan yang sama.
- **Rekomendasi Guard**: Cek ketersediaan `ep.bpjsSepNo`. Jika sudah ada, kembalikan response `ALREADY_ISSUED` atau instruksikan user untuk melakukan Delete SEP terlebih dahulu.

---

### Case 6: Pendaftaran Pasien Temporary IGD Ganda
- **Lokasi Kode**: `registration.service.ts:389 registerTemporary`.
- **Anomali**: `registerTemporary` langsung membuat record `patients` baru dengan `is_temporary=true` tanpa melakukan fuzzy check nama / gender.
- **Dampak**: Penumpukan data pasien temporary ganda di masterdata jika petugas registrasi IGD melakukan klik ganda.

---

## 2. MATRIKS METRIK & DERAJAT RISIKO

| Case | Lokasi Kode | Derajat Risiko | Dampak Operasional / Keuangan |
|---|---|---|---|
| **Case 1: Reg Rajal Ganda `INPROGRESS`** | `registration.service.ts:925` | **HIGH (Blocker QA)** | Antrean ganda, rekam medis ganda di poli sama. |
| **Case 2: Order Zombie Episode Closed** | `order.service.ts:13, 121` | **CRITICAL (Blocker Kasir)** | Tagihan siluman muncul di episode yang sudah dipulangkan. |
| **Case 3: Reg Ranap Ganda (`admit`)** | `registration.service.ts:480` | **HIGH (Blocker Ranap)** | Pasien terdaftar di 2 bed, double tagihan akomodasi. |
| **Case 4: Visite Harian Ganda** | `registration.service.ts` | **HIGH (Loss / Overcharge)** | Pasien ditagih biaya visite dokter 2x–3x lipat sehari. |
| **Case 5: Re-Issue SEP BPJS** | `sep.service.ts:91` | **MEDIUM (Klaim BPJS)** | Klaim BPJS terduplikasi di VClaim. |
| **Case 6: Pasien Temp IGD Ganda** | `registration.service.ts:389` | **LOW (Data Garbage)** | Penumpukan record pasien temporary tidak terverifikasi. |

---

## 3. SARAN RENCANA PERBAIKAN (ACTION PLAN FOR DEV)

1. **Pasang Constraint `active_episode_guard`** di `createEpisode` & `registerWalkin` untuk memblokir pendaftaran ke `unitId` yang sama jika pasien memiliki status `registered`, `calling`, `in_progress`, atau `waitlist`.
2. **Tambahkan Validasi Status Episode (`status === 'in_progress' || status === 'registered'`)** pada `createPrescription` dan `createSupportOrder` sebelum menyimpan header order.
3. **Pasang Checking `existingInpatientEpisode`** di `admitToInpatient` agar pasien tidak bisa di-admit ke Ranap jika masih memiliki episode `inpatient` berstatus non-closed.
4. **Tambahkan Check Duplicate Visite** per `(episodeId, doctorId, visiteDate)` di method `recordVisite`.
