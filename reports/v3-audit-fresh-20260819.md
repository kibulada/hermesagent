# Laporan Audit Defect BARU — Kesia V3 (HEAD `20bfb0a`, 19-08-2026)

Repo: `E:\WORK KESIA\Project\kesiaV3`
HEAD: `20bfb0a FB batch billing/guard + Odoo payment F4/F6: InvoiceDetail delete/void/popup, cancel guards, dispense qty, SPRI idempoten`

---

## Ringkasan Verifikasi 12 Item Sebelumnya (100% SUDAH DIFIX di `20bfb0a`)

| # | Item | Status | Lokasi & Bukti Fix |
|---|------|--------|-------------------|
| 1 | Hapus cover & hapus diskon di Billing | **FIXED** | `BillingPage.tsx:449` (Hapus Diskon); `:467` (Hapus Cover per-row) |
| 2 | Tolak batal bila sudah diisi SOAP/Assesmen | **FIXED** | `registration.service.ts:931-936` (count integrated-note/cppt-sbar/assessment → throw `EPISODE_HAS_CLINICAL`) |
| 3 | Invoice ikut batal saat kunjungan dibatalkan | **FIXED** | `registration.service.ts:948-953` (`cancelEpisode` set `invoices.status = 'void'`) |
| 4 | List penjamin yang muncul = milik pasien | **FIXED** | `BillingPage.tsx:317,459` (`usePatientInsurers(selPatientId)`) |
| 5 | mergeInvoices pertahankan globalDiscount | **FIXED** | `billing.service.ts:375-378` (`mergedDiscC = srcs.reduce(...)`, dikurangkan dari gross) |
| 6 | Popup Bayar tampilkan sisa bayar (net) | **FIXED** | `BillingPage.tsx:201` (`description={`Sisa bayar ${rupiah(Number(r.amountDue ?? r.total))} ...`}`) |
| 7 | Invoice Detail Page tombol Batalkan & Popconfirm | **FIXED** | `InvoiceDetailPage.tsx:162,308` (tombol Batalkan + guard status); `:276,281` (Popconfirm) |
| 8 | Preview tarif tindakan sertakan insurerId | **FIXED** | `BillingPage.tsx:331` (`resolveActionPrice(..., { ..., insurerId: ep?.insurerId })`) |
| 9 | Integrasi Odoo payment F4 (invoice) & F6 (deposit) | **FIXED** | `post-payment-to-odoo.saga.ts` dipicu otomatis saat `payInvoice` & `payDeposit` |
| 10 | Item qty=0 / free-text tidak dispense unlimited | **FIXED** | `pharmacy.service.ts:362-366` (`if (qty <= 0) throw PRESC_ITEM_QTY_INVALID`) |
| 11 | onSubmit Form SOAP loading state | **FIXED** | `SoapForm.tsx:102` (`loading={saving}`) |
| 12 | orderInpatient cegah double SPRI | **FIXED** | `registration.service.ts:672-675` (pemeriksaan `dup` carePlan active sebelum insert) |
| UI | Alignment button aksi dalam border table | **FIXED** | `InvoiceDetailPage.tsx:269` (`width: 250` disesuaikan) |

---

## Daftar Defect BARU Teridentifikasi di HEAD `20bfb0a` (32 Item)

### A. CLINICAL & PENDAFTARAN (8 Item)

1. **[NEW-001] CRITICAL | BPJS / /bpjs/sep** — `issue()` SEP tidak idempoten: retry/double-click menghasilkan multiple row `issued`/`failed` di DB.
   - *File*: `apps/api/src/modules/clinical/sep.service.ts:91`
   - *Dampak*: Double SEP terbit untuk 1 kunjungan, klaim VClaim ditolak/ganda.
   - *Fix*: Guard check `select id from seps where episodeId = ? and status = 'issued'` sebelum insert.

2. **[NEW-002] HIGH | BPJS / /bpjs/sep** — `returnOnDischarge` retry gagal: baris `returnStatus = 'failed'` tertahan tanpa reset retry.
   - *File*: `apps/api/src/modules/clinical/sep.service.ts:231`
   - *Dampak*: SEP gagal di-update tgl pulangnya di VClaim, status klaim menggantung.
   - *Fix*: Izinkan retry jika `returnStatus === 'failed'`.

3. **[NEW-003] HIGH | BPJS / /bpjs/sep** — `tglSep` pakai `new Date().toISOString().slice(0, 10)` (UTC) bukan tanggal WIB.
   - *File*: `apps/api/src/modules/clinical/sep.service.ts:126`
   - *Dampak*: Registrasi malam hari WIB (setelah jam 18:00 UTC) buat `tglSep` mundur 1 hari.
   - *Fix*: Gunakan helper `localDateStr(new Date())`.

4. **[NEW-004] HIGH | Registrasi / Edit Episode** — `editEpisode` tanpa guard status episode (bisa edit penjamin/dokter saat pasien `INPROGRESS`).
   - *File*: `apps/api/src/modules/clinical/registration.service.ts:973`
   - *Dampak*: Ganti unit/dokter saat pelayanan berjalan mengacaukan tagihan dan rekam medis.
   - *Fix*: Tolak perubahan jika `status in ('closed', 'cancelled')`.

5. **[NEW-005] HIGH | Dokter / EMR Worklist** — `respondConsult` (jawab konsul) tidak idempoten & tanpa guard status `responded`.
   - *File*: `apps/api/src/modules/clinical/care-plan.service.ts:182-196`
   - *Dampak*: Jawaban DPJP konsulen bisa ditimpa ulang tanpa audit trail (jawaban awal hilang).
   - *Fix*: Guard status != 'responded' sebelum update.

6. **[NEW-006] MEDIUM | Dokter & Perawat / Visite** — `recordVisite` tanpa guard status episode (`closedAt`) & tanpa unique constraint `(episodeId, doctorId, visitDate)`.
   - *File*: `apps/api/src/modules/clinical/order.service.ts:231-246`
   - *Dampak*: Visite ganda per hari → tagihan visite dobel, atau visite dicatat setelah pasien pulang.
   - *Fix*: Cek status episode + unique index `(siteId, episodeId, doctorId, visitDate)`.

7. **[NEW-007] MEDIUM | Dokter & Perawat / Visite** — `deleteVisite` hard-delete tanpa cek apakah visite sudah masuk invoice paid.
   - *File*: `apps/api/src/modules/clinical/order.service.ts:262-269`
   - *Dampak*: Visite yang sudah dibayar pasien bisa dihapus → jejak kuitansi rompang.
   - *Fix*: Cek invoiceLines/sourceKind = 'visite' + ganti soft-delete.

8. **[NEW-008] MEDIUM | MCU / Walk-in** — Walk-in MCU `hasPaidDeposit=true` tanpa transaksi `deposit_payments` riil.
   - *File*: `apps/api/src/modules/clinical/registration.service.ts:558-595`
   - *Dampak*: Kasir tidak bisa klaim/refund deposit karena baris mutasi deposit tidak ada.
   - *Fix*: Buat baris `deposit_payments` atau beri flag `mcu_waived`.

---

### B. FARMASI & STOK (5 Item)

9. **[NEW-009] CRITICAL | Apoteker / Penjualan Bebas** — `createSale` OTC tidak pre-check on-hand stok sebelum transaksi.
   - *File*: `apps/api/src/modules/clinical/pharmacy.service.ts:237`
   - *Dampak*: Penjualan OTC sukses dan memotong stok jadi minus saat stok gudang 0.
   - *Fix*: Pre-check `qtyOnHand >= qty` sebelum pemotongan stok.

10. **[NEW-010] HIGH | Apoteker / Tebus Resep Iterasi** — `redeemIter` race condition counter `iterUsedCount`.
    - *File*: `apps/api/src/modules/clinical/order.service.ts:273-296`
    - *Dampak*: Dua klik tebus bersamaan baca `iterUsedCount` sama, tebusan melampaui `iterMaxCount`.
    - *Fix*: Row locking `.for('update')` atau atomic `UPDATE WHERE iter_used_count < iter_max_count`.

11. **[NEW-011] HIGH | Apoteker / Batal Resep** — `cancelPrescription` tidak tolak resep yang sudah ter-dispense sebagian (`dispensedAmount > 0`).
    - *File*: `apps/api/src/modules/clinical/pharmacy.service.ts:385-399`
    - *Dampak*: Resep UDD ranap yang sudah diserahkan sebagian bisa di-cancel tanpa retur → stok tidak konsisten.
    - *Fix*: Tolak jika `dispensedAmount > 0` (wajib lewat menu Retur).

12. **[NEW-012] HIGH | Apoteker / Void Penjualan** — `voidSale` kembalikan ledger stok tapi tidak restore `item_stocks` & FEFO.
    - *File*: `apps/api/src/modules/clinical/pharmacy.service.ts:262-281`
    - *Dampak*: Ledger naik tapi `item_stocks` (sumber truth kasir) tidak naik → stok fisik vs sistem mismatch.
    - *Fix*: Panggil restore FEFO / increment `item_stocks` di `voidSale`.

13. **[NEW-013] HIGH | Apoteker / Adjust Stok** — `adjustStock` tanpa guard saldo akhir (izinkan delta negatif besar).
    - *File*: `apps/api/src/modules/clinical/pharmacy.service.ts:606-616`
    - *Dampak*: Delta -999999 diterima → `qtyOnHand` jadi negatif.
    - *Fix*: Guard `qtyOnHand + delta >= 0`.

---

### C. PENUNJANG, RADIOLOGI, LAB, OK & MCU (11 Item)

14. **[NEW-014] CRITICAL | Radiologi / DICOM** — `imaging.upload` tidak validasi `orderId.patientId === input.patientId` (cross-patient).
    - *File*: `apps/api/src/modules/clinical/imaging.service.ts:27-48`
    - *Dampak*: DICOM pasien A ter-upload ke order pasien B → kesalahan rekam medis fatal.
    - *Fix*: Select `supportOrders.patientId` & throw jika `!= input.patientId`.

15. **[NEW-015] HIGH | Radiologi / DICOM** — `imaging.remove` hard-delete tanpa soft-delete/audit trail.
    - *File*: `apps/api/src/modules/clinical/imaging.service.ts:87-95`
    - *Dampak*: Berkas citra medis hilang permanen dari DB tanpa jejak audit.
    - *Fix*: Ganti dengan soft-delete `deletedAt` + emit audit event.

16. **[NEW-016] HIGH | Dokter & OK / Operasi** — `setSurgeryStatus` tanpa enum status validation (menerima string bebas).
    - *File*: `apps/api/src/modules/ops/ops.service.ts:912-919`
    - *Dampak*: Status operasi bisa diisi string sembarang → state machine OK rusak.
    - *Fix*: Whitelist `['scheduled', 'in_progress', 'completed', 'cancelled']`.

17. **[NEW-017] HIGH | Staf Penunjang / Cathlab** — `saveCathlabReport` tidak cek status order `cancelled` / `verified`.
    - *File*: `apps/api/src/modules/clinical/order.service.ts:728-782`
    - *Dampak*: Laporan Cathlab tetap bisa disimpan untuk order yang sudah dibatalkan/final.
    - *Fix*: Guard `ord.status === 'cancelled' || ord.status === 'verified'`.

18. **[NEW-018] HIGH | Staf Penunjang / Bank Darah** — `bloodbank.createRequest` tidak cek status episode EMR closed/cancelled.
    - *File*: `apps/api/src/modules/clinical/bloodbank.service.ts:106-123`
    - *Dampak*: Permintaan darah baru bisa dibuat untuk episode yang sudah selesai/batal.
    - *Fix*: Cek status episode EMR sebelum insert.

19. **[NEW-019] HIGH | Lab / LIS** — `lis.apply` / `resultSupport` menimpa hasil yang sudah status `verified`.
    - *File*: `apps/api/src/modules/clinical/lis.service.ts:62` & `order.service.ts:606`
    - *Dampak*: LIS re-ingest menimpa hasil lab yang sudah diverifikasi DPJP.
    - *Fix*: Tolak transisi jika status order `verified`.

20. **[NEW-020] HIGH | Lab / Spesimen** — `specimen.collect` izinkan pengambilan spesimen untuk order `verified`.
    - *File*: `apps/api/src/modules/clinical/specimen.service.ts:40`
    - *Dampak*: Spesimen bisa diambil ganda setelah hasil terbit.
    - *Fix*: Guard `ord.status in ('verified', 'resulted')`.

21. **[NEW-021] MEDIUM | Lab / Spesimen** — Transisi status custody spesimen `addEvent` bisa melompati urutan state (`collected` → `discarded` skip `received`).
    - *File*: `apps/api/src/modules/clinical/specimen.service.ts:52-67`
    - *Dampak*: Chain-of-custody spesimen tidak akurat.
    - *Fix*: Terapkan strict linear state machine.

22. **[NEW-022] MEDIUM | FE Penunjang / Lab** — FE PenunjangPage tidak disable tombol "Edit Hasil" saat status `verified`.
    - *File*: `apps/web-clinic/src/features/penunjang/PenunjangPage.tsx:181`
    - *Dampak*: User mencoba edit hasil final → memicu error API.
    - *Fix*: Sembunyikan/disable tombol jika status `verified`.

23. **[NEW-023] MEDIUM | MCU / Cetak** — `CetakMcuPage` tidak memfilter `formCode` (Depnaker vs Company vs Standar).
    - *File*: `apps/web-clinic/src/features/cetak/CetakMcuPage.tsx:39`
    - *Dampak*: Hasil cetak MCU mencampur form Depnaker & Standar.
    - *Fix*: Tambahkan parameter filter `formCode`.

24. **[NEW-024] MEDIUM | UPM / Gizi** — `recordFoodDelivery` tidak cek status order cancelled.
    - *File*: `apps/api/src/modules/clinical/order.service.ts:907`
    - *Dampak*: Makanan dari order batal tetap bisa dicatat terantar.
    - *Fix*: Guard `foodOrder.status !== 'cancelled'`.

---

### D. REKAM MEDIS, CASEMIX & RBAC (8 Item)

25. **[NEW-025] CRITICAL | Casemix & BPJS** — `saveCasemix` fallback tarif hardcoded `cbgTariff ?? 1500000`.
    - *File*: `apps/api/src/modules/ops/ops.service.ts:223`
    - *Dampak*: Jika tarif grouper null, klaim diajukan sebesar Rp 1.500.000 (salah klaim masif).
    - *Fix*: Ubah fallback ke 0 / throw error.

26. **[NEW-026] HIGH | Rekam Medis / Coding** — `setEpisodeCoding` tidak cek status episode closed/cancelled.
    - *File*: `apps/api/src/modules/clinical/registration.service.ts:893`
    - *Dampak*: Koder RM bisa mengubah ICD diagnosis pada kunjungan yang sudah ditutup dan ditagihkan.
    - *Fix*: Guard `status !== 'closed' && status !== 'cancelled'`.

27. **[NEW-027] HIGH | RBAC / Config** — `DEFAULT_ROLE_PAGES` melewatkan default pages untuk role `rekammedis` dan `upm`.
    - *File*: `apps/api/src/modules/rbac/rbac.service.ts:51-75`
    - *Dampak*: Role Rekam Medis & UPM yang baru diseed tidak punya permission awal → login tapi menu kosong.
    - *Fix*: Tambahkan `rekammedis: ['/rm/coding', ...]` & `upm: ['/rm/fsu', ...]`.

28. **[NEW-028] MEDIUM | Rekam Medis / ARM** — `setArm` (status berkas RM) diisi string bebas tanpa validasi enum.
    - *File*: `apps/api/src/modules/ops/ops.service.ts:462`
    - *Dampak*: Status berkas RM bisa diisi sembarang string (`borrow`, `dipinjam`, dll).
    - *Fix*: Validasi enum `['in_storage', 'borrowed', 'disposed', 'lost']`.

29. **[NEW-029] MEDIUM | Rekam Medis / ARM** — `markArmInactive` tidak mencatat `updatedBy` (audit trail hilang).
    - *File*: `apps/api/src/modules/ops/ops.service.ts:432`
    - *Dampak*: Tidak diketahui staf mana yang menonaktifkan berkas RM.
    - *Fix*: Tambahkan `updatedBy: ctx.userId`.

30. **[NEW-030] LOW | Auth / Security** — `devResetToken` berpotensi terakses di environment staging/test.
    - *File*: `apps/api/src/modules/auth/auth.service.ts:103`
    - *Dampak*: Token reset password bypass di staging.
    - *Fix*: Perketat guard khusus `process.env.NODE_ENV === 'development'`.

31. **[NEW-031] LOW | BPJS / VClaim** — `VClaimClient` fetch tanpa timeout / AbortController.
    - *File*: `apps/api/src/modules/clinical/bpjs-vclaim.client.ts:66`
    - *Dampak*: Request ke WS BPJS menggantung tanpa limit waktu saat BPJS down.
    - *Fix*: Tambahkan `signal: AbortSignal.timeout(10000)`.

32. **[NEW-032] LOW | Auth & RBAC** — `ROLE_PRIORITY` melewatkan `bpjs`, `ok`, `rekammedis`, `upm`, `mcu`.
    - *File*: `apps/api/src/modules/rbac/rbac.service.ts:39-47`
    - *Dampak*: User multi-role dengan salah satu role di atas landing ke home path yang salah.
    - *Fix*: Lengkapi array `ROLE_PRIORITY`.
