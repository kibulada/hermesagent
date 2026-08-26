# Laporan Audit Defect & Blocker BARU — Kesia V3 (HEAD `11a0d9a`, 20-08-2026)

Repo: `E:\WORK KESIA\Project\kesiaV3`
HEAD: `11a0d9a feat(odoo18): F3 income_mapping/posting-rule per-tenant — akun income per (kategori×penjamin)`

*Catatan: Seluruh 18 item FB19 sebelumnya SUDAH FIXED 100%. File ini HANYA berisi 33 temuan defect/blocker BARU yang masih OPEN.*

---

## 1. Petugas Pendaftaran
- **[NEW-001] HIGH | /registrasi/verifikasi-online** — Endpoint `POST /clinical/episodes/:id/call` diproteksi `@RequirePermission('perawat/station:call')`. Role Pendaftaran (`REG`) yang punya izin `verifikasi/online` tidak punya permission perawat ini.
  - *File:Line*: `apps/api/src/modules/clinical/clinical.controller.ts:359`
  - *Dampak*: Petugas Pendaftaran gagal memverifikasi & mengaktifkan pendaftaran online ke antrean (HTTP 403 Forbidden).
  - *Fix*: Tambahkan `'verifikasi/online:verify'` dan `'registrasi/waitlist:call'` ke `@RequirePermission` di `episodes/:id/call`.
- **[NEW-002] MEDIUM | /registrasi/pasien** — `editEpisode` melegalkan pengubahan `insurerId` (penjamin) pada episode `INPROGRESS` tanpa membatalkan order yang sudah terbit dengan tarif penjamin lama.
  - *File:Line*: `apps/api/src/modules/clinical/registration.service.ts:973`
  - *Dampak*: Order lama (resep/lab) terbit dengan tarif penjamin A, invoice ditarik dengan penjamin B → selisih klaim.
  - *Fix*: Minta kasir membatalkan/void order & invoice lama sebelum mengubah penjamin episode aktif.
- **[NEW-003] MEDIUM | /registrasi/pasien** — Tombol "Lanjut" pada wizard registrasi tidak memanggil `form.validateFields()` sebelum berpindah langkah.
  - *File:Line*: `apps/web-clinic/src/features/registration/RegistrationFormPage.tsx:559`
  - *Dampak*: Pasien bisa terdaftar tanpa penjamin/data wajib jika pengguna melewatinya via tombol "Lanjut".
  - *Fix*: Panggil `await form.validateFields()` sebelum `setStep`.

---

## 2. Kasir / Billing
- **[NEW-004] HIGH | /kasir/corporate-claims** — Query `listCompanySummaries` menggunakan `count(distinct i.id)` dengan `left join invoices i`.
  - *File:Line*: `apps/api/src/modules/billing/corporate-claim.service.ts:45`
  - *Dampak*: Ringkasan tagihan perusahaan menampilkan hitungan 0 jika invoice berstatus draft/null.
  - *Fix*: Gunakan `count(c.id)::int` dengan `filter (where i.id is not null)`.
- **[NEW-005] HIGH | /kasir/billing & /kasir/invoices** — `cancelInvoice` tidak membatalkan alokasi `invoice_coverages` pada piutang penjamin yang berstatus `draft`.
  - *File:Line*: `apps/api/src/modules/billing/billing.service.ts:160-190`
  - *Dampak*: Nilai klaim pada `listClaims` tetap menghitung invoice yang sudah di-void.
  - *Fix*: Tambahkan `db.delete(schema.invoiceCoverages).where(eq(invoiceId, id))` di `cancelInvoice`.
- **[NEW-006] HIGH | Multi-Tenant Security** — `billing.service.ts` mengecek keterkaitan `prescriptions` dan `supportOrders` ke invoice tanpa memfilter `siteId`.
  - *File:Line*: `apps/api/src/modules/billing/billing.service.ts:653-654`
  - *Dampak*: Berisiko membaca/mencocokkan data resep & order milik tenant/site lain.
  - *Fix*: Tambahkan `eq(schema.prescriptions.siteId, ctx.siteId)` pada query `where`.
- **[NEW-007] MEDIUM | /kasir/deposit** — Modal bayar deposit menggunakan `initialValues` statis pada Form AntD.
  - *File:Line*: `apps/web-clinic/src/features/kasir/DepositListPage.tsx:96`
  - *Dampak*: Nama pembayar (`payor`) tidak diperbarui otomatis saat berganti ke pasien lain.
  - *Fix*: Panggil `form.setFieldsValue({ payor: target?.patientName })` di `useEffect` saat `target` berubah.

---

## 3. Perawat
- **[NEW-008] HIGH | /emr/worklist** — `confirmObservation` (konfirmasi TTV / pengkajian) tidak mengecek status episode (`closed` / `cancelled`).
  - *File:Line*: `apps/api/src/modules/clinical/clinical-observation.service.ts:330`
  - *Dampak*: Perawat bisa mengonfirmasi/mengubah TTV pada pasien yang sudah pulang.
  - *Fix*: Tambahkan guard `assertEpisodeOpen(ep.status)`.
- **[NEW-009] HIGH | /emr/worklist** — Verifikasi `vital-sign` di backend menolak `nurse-done` jika TTV dicatat dari form non-standar.
  - *File:Line*: `apps/web-clinic/src/features/emr/NurseWorkspacePage.tsx:99`
  - *Dampak*: Perawat terblokir dan tidak dapat menyerahkan pasien ke antrean dokter meski TTV sudah dicatat.
  - *Fix*: Fleksibelkan backend check `hasVital` berdasarkan `formCode` atau payload TTV.
- **[NEW-010] MEDIUM | /emr/igd** — Field `submissionNurseId` & `receiptNurseId` di form Operan Jaga bertipe text manual.
  - *File:Line*: `apps/web-clinic/src/features/emr/igdForms.ts:124`
  - *Dampak*: Perawat mengetik nama/ID manual tanpa acuan master pegawai staf.
  - *Fix*: Ubah `type: 'text'` menjadi `type: 'select'` dengan `enumSource: 'staff'`.

---

## 4. Dokter
- **[NEW-011] HIGH | /emr/worklist & /dokter/konsul** — `respondConsult` (jawaban konsul DPJP) tidak idempoten dan tanpa audit trail perubahan.
  - *File:Line*: `apps/api/src/modules/clinical/care-plan.service.ts:182`
  - *Dampak*: Jawaban konsul awal DPJP bisa ditimpa ulang tanpa jejak histori.
  - *Fix*: Tolak jika status carePlan sudah `responded` atau simpan versi histori jawaban.
- **[NEW-012] HIGH | /emr/worklist** — State `hasCarePlan` stale dari React Query saat menambah rencana tindak lanjut.
  - *File:Line*: `apps/web-clinic/src/features/emr/DoctorWorkspacePage.tsx:88`
  - *Dampak*: Dokter telah mengisi rencana tindak lanjut tetapi tombol "Selesai Pemeriksaan" tetap terkunci (disabled).
  - *Fix*: Invalidate query `care-plans` saat care plan ditambah/diperbarui.
- **[NEW-013] LOW | /emr/worklist** — Dynamic validation rules `iterValidUntil` & `iterMaxCount` tidak terpasang di `Form.Item` resep iterasi.
  - *File:Line*: `apps/web-clinic/src/features/emr/OrderSection.tsx:185`
  - *Dampak*: Error validation resep iterasi tidak memberi highlight merah pada input spesifik.
  - *Fix*: Tambahkan `rules` kondisional pada `Form.Item` sesuai state `isIter`.

---

## 5. Apoteker / Farmasi
- **[NEW-014] HIGH | /farmasi/penjualan-bebas** — `voidSale` (pembatalan OTC) mengembalikan nilai ledger tetapi tidak mengembalikan stok pada `item_stocks` dan batch FEFO.
  - *File:Line*: `apps/api/src/modules/clinical/pharmacy.service.ts:262-281`
  - *Dampak*: Stok di ledger bertambah tetapi sisa stok fisik di `item_stocks` tidak naik → mismatch stok.
  - *Fix*: Panggil increment `item_stocks` + restore batch FEFO saat `voidSale`.
- **[NEW-015] HIGH | /farmasi/verifikasi-resep** — Resep `flagged` (ditolak telaah) tetap masuk daftar tunggu verifikasi tanpa filter `reviewResult`.
  - *File:Line*: `apps/web-clinic/src/features/farmasi/VerifikasiResepPage.tsx:36`
  - *Dampak*: Apoteker dapat tidak sengaja meloloskan resep bermasalah sebelum direvisi dokter.
  - *Fix*: Filter resep berstatus `flagged` dari daftar tunggu biasa & berikan indikator visual tegas.
- **[NEW-016] MEDIUM | /farmasi/stok** — Parameter Query `expiringDays` di-cast `Number(expiringDays)` tanpa pengecekan `isNaN`.
  - *File:Line*: `apps/api/src/modules/clinical/clinical.controller.ts:504, 521`
  - *Dampak*: Jika dikirim query `expiringDays=abc`, query Postgres melempar unhandled Exception 500 error.
  - *Fix*: Tambahkan guard `isNaN(Number(val))` atau bersihkan dengan helper Zod number.
- **[NEW-017] LOW | /farmasi/penjualan-bebas** — Dropdown `Select` cari obat mempertahankan term pencarian lama setelah obat ditambah ke keranjang.
  - *File:Line*: `apps/web-clinic/src/features/farmasi/PenjualanBebasPage.tsx:108`
  - *Dampak*: Apoteker harus menghapus teks pencarian manual saat menambah obat berikutnya.
  - *Fix*: Set `value={undefined}` & panggil `setTerm('')` saat `onChange`.

---

## 6. Petugas Laboratorium
- **[NEW-018] HIGH | /penunjang/lab** — `specimen.collect` mengizinkan pengambilan spesimen untuk order lab yang statusnya sudah `verified`.
  - *File:Line*: `apps/api/src/modules/clinical/specimen.service.ts:40`
  - *Dampak*: Spesimen lab bisa diambil ulang setelah hasil resmi diverifikasi DPJP.
  - *Fix*: Guard `where(inArray(status, ['ordered', 'in_progress']))`.
- **[NEW-019] HIGH | /penunjang/lab/lis** — `parseHl7Oru` mengevaluasi OBR-3 yang kosong menjadi string kosong `""` dan meng-overwrite `orderId` antar-OBX.
  - *File:Line*: `apps/api/src/modules/clinical/lis.service.ts:22`
  - *Dampak*: Pesanan LIS dengan banyak OBR saling menimpa hasil sampel.
  - *Fix*: Kelompokkan OBX di bawah OBR filler order number masing-masing.

---

## 7. Petugas Radiologi
- **[NEW-020] CRITICAL | /penunjang/radiologi** — `imaging.upload` tidak mengecek apakah `input.patientId` cocok dengan `supportOrders.patientId`.
  - *File:Line*: `apps/api/src/modules/clinical/imaging.service.ts:27-48`
  - *Dampak*: Citra Rontgen/CT-Scan pasien A ter-upload ke order pasien B.
  - *Fix*: Query `supportOrders` via `orderId` & throw error jika `order.patientId !== input.patientId`.
- **[NEW-021] MEDIUM | /penunjang/radiologi** — Upload DICOM tanpa `orderId` (langsung by `episodeId`) melewasi guard order dibatalkan (`cancelled`).
  - *File:Line*: `apps/api/src/modules/clinical/imaging.service.ts:33-36`
  - *Dampak*: Citra bisa ter-upload ke episode/order yang sudah dibatalkan.
  - *Fix*: Cek status episode jika `orderId` tidak dikirim.

---

## 8. Petugas Cathlab
- **[NEW-022] HIGH | /penunjang/cathlab** — `saveCathlabReport` tidak mengecek ketersediaan tim/dokter pelaksana operator.
  - *File:Line*: `apps/api/src/modules/clinical/order.service.ts:728-782`
  - *Dampak*: Laporan Cathlab tersimpan tanpa mencatat DPJP Operator Cathlab.
  - *Fix*: Wajibkan parameter `operatorId` pada DTO `saveCathlabReport`.

---

## 9. Petugas BPJS / Casemix
- **[NEW-023] CRITICAL | /bpjs/casemix** — `saveCasemix` memiliki fallback tarif CBG hardcoded `cbgTariff ?? 1500000` bila respon grouper null.
  - *File:Line*: `apps/api/src/modules/ops/ops.service.ts:223`
  - *Dampak*: Jika WS Grouper timeout/null, klaim diajukan konstan sebesar Rp 1.500.000.
  - *Fix*: Ubah fallback ke 0 / throw error agar divalidasi manual.

---

## 10. Rekam Medis
- **[NEW-024] HIGH | /rm/coding** — `setEpisodeCoding` (pengkodean ICD-10 / ICD-9-CM) tidak mengecek status episode closed/cancelled.
  - *File:Line*: `apps/api/src/modules/clinical/registration.service.ts:893`
  - *Dampak*: Koder RM bisa mengganti kode diagnosis pada kunjungan yang sudah ditagihkan ke BPJS/pasien.
  - *Fix*: Guard `status !== 'closed' && status !== 'cancelled'`.

---

## 11. Petugas Kamar Operasi (OK)
- **[NEW-025] HIGH | /ok/jadwal** — `setSurgeryStatus` tidak memvalidasi enum status operasi (menerima string bebas).
  - *File:Line*: `apps/api/src/modules/ops/ops.service.ts:912`
  - *Dampak*: Status operasi bisa diisi string sembarang → state machine OK terganggu.
  - *Fix*: Whitelist `['scheduled', 'in_progress', 'completed', 'cancelled']`.

---

## 12. Petugas MCU
- **[NEW-026] LOW | /mcu/cetak** — Cetak sertifikat MCU memanggil `mcu.recordedAt.slice(0, 10)` tanpa null check.
  - *File:Line*: `apps/api/src/modules/clinical/clinical.controller.ts:126` / `CetakMcuPage.tsx:126`
  - *Dampak*: TypeError unhandled saat `recordedAt` kosong.
  - *Fix*: Gunakan optional chaining `mcu?.recordedAt ? ... : '-'`.

---

## 13. Dokter Onkologi Radiasi, Fisikawan Medis, Radioterapis (RTT)
- **[NEW-027] HIGH | /penunjang/radioterapi** — Order Radioterapi (Linac/Brachytherapy) pada `support_orders` tidak mencatat tahapan verifikasi konturing & kalkulasi dosis Fisikawan Medis sebelum RTT mengeksekusi penyinarannya.
  - *File:Line*: `apps/api/src/modules/clinical/order.service.ts:650-710`
  - *Dampak*: RTT dapat menandai order radioterapi 'completed' tanpa persetujuan perencanaan dosis dari Fisikawan Medis.
  - *Fix*: Wajibkan persetujuan dose plan (status `plan_approved`) sebelum status order radioterapi diubah ke `in_progress`/`completed`.

---

## 14. Administrator & Odoo Sync
- **[NEW-028] HIGH | Multi-Tenant Security / Odoo Saga** — Saga runner `post-billing-to-odoo.saga.ts` membaca `invoices`, `invoiceLines`, `invoiceCoverages`, dan `patients` tanpa `eq(siteId, ctx.siteId)`.
  - *File:Line*: `apps/api/src/modules/billing/saga/post-billing-to-odoo.saga.ts:26-38`
  - *Dampak*: Berpotensi terjadi kebocoran data antar-tenant jika ID saga dipicu secara langsung.
  - *Fix*: Wajibkan filter `siteId` pada semua query SELECT di dalam saga processor.
- **[NEW-029] MEDIUM | /keuangan/odoo-sync** — `post-billing-to-odoo.saga.ts` `resolveIncomeAccount` menggagalkan pencocokan rule jika `categId` null (mengubah null ke `''`).
  - *File:Line*: `apps/api/src/modules/billing/saga/post-billing-to-odoo.saga.ts:180`
  - *Dampak*: Pendapatan item tanpa kategori dicatat ke akun generic, bukan akun spesifik penjamin.
  - *Fix*: Jangan ubah `null` ke `''` saat matching score rule.
- **[NEW-030] HIGH | /keuangan/odoo-sync** — `post-inventory-to-odoo.saga.ts` tidak mengecek ketersediaan pasangan jurnal penyesuaian stok di Odoo saat sync `stock.quant`.
  - *File:Line*: `apps/api/src/modules/billing/saga/post-inventory-to-odoo.saga.ts:45`
  - *Dampak*: Sync inventori Odoo gagal menggantung saat ada produk baru tanpa kategori persediaan.
  - *Fix*: Tambahkan validasi kelengkapan kategori persediaan produk sebelum trigger `action_apply_inventory`.
- **[NEW-031] MEDIUM | /admin/users** — Invalidate token `devResetToken` di `auth.service.ts` tidak menghapus token dari memori jika dikirim berulang kali.
  - *File:Line*: `apps/api/src/modules/auth/auth.service.ts:103`
  - *Dampak*: Token reset password bypass dapat dipakai berulang di staging.
  - *Fix*: Hapus/set null token reset setelah sekali dipakai.
- **[NEW-032] LOW | /admin/rbac** — Array `ROLE_PRIORITY` di `rbac.service.ts` melewatkan peran `bpjs`, `ok`, `rekammedis`, `upm`, `mcu`.
  - *File:Line*: `apps/api/src/modules/rbac/rbac.service.ts:39`
  - *Dampak*: User multi-role dengan salah satu role tersebut salah mendarat ke default landing page.
  - *Fix*: Lengkapi daftar array `ROLE_PRIORITY`.
- **[NEW-033] MEDIUM | /admin/masterdata** — `item_prices` izinkan simpan harga jual 0 tanpa flag konfirmasi `isFree`.
  - *File:Line*: `apps/api/src/modules/masterdata/masterdata.service.ts:410`
  - *Dampak*: Obat/alkes bisa tidak sengaja diset gratis di master data sehingga billing menarik harga Rp 0.
  - *Fix*: Beri peringatan/persetujuan eksplisit jika `sellPrice === 0`.

---

## 15. Radioterapis (RTT) & Fisikawan Medis
- **[NEW-034] HIGH | /rt/deliver** — `deliverFraction` tidak menolak fraksi yang sudah berstatus `DONE` (tidak ada guard `frac.status` sebelum update).
  - *File:Line*: `apps/api/src/modules/rt/rt.courses.service.ts:257-283`
  - *Dampak*: Fraksi yang sama bisa ter-deliver 2x (double radiation record) → jumlah fraksi DONE melebihi `totalFractions`, progres course & kalkulasi OTT salah.
  - *Fix*: Guard awal `if (frac.status === 'DONE') throw new DomainError('FRACTION_ALREADY_DONE', ...)`.

## 16. Anjungan Mandiri (Kiosk)
- **[NEW-035] MEDIUM | /kiosk/checkin** — Endpoint `POST /kiosk/checkin/:episodeId` adalah aksi WRITE (ubah status antrean BPJS `sent` → `checkedin`) tapi hanya diproteksi permission view-only `registrasi/pasien:view`.
  - *File:Line*: `apps/api/src/modules/kiosk/kiosk.controller.ts:17`
  - *Dampak*: Akun dengan izin baca-saja (mis. petugas laporan) dapat mengubah status antrean pasien dari perangkat kiosk.
  - *Fix*: Gunakan permission khusus `kiosk:checkin` atau `registrasi/waitlist:call`.

## 17. Administrator / Odoo Sync (tambahan)
- **[NEW-036] LOW | /keuangan/odoo-sync** — Adapter Odoo melakukan cast `Number(input.amount)` / `Number(input.onHand)` tanpa guard NaN.
  - *File:Line*: `apps/api/src/modules/billing/odoo/odoo12.adapter.ts:98`, `odoo18.adapter.ts:179`, `odoo18.adapter.ts:244`
  - *Dampak*: Payload saga korup (amount string rusak) menghasilkan `NaN` yang dikirim ke XML-RPC Odoo → jurnal/payment gagal diam-diam di sisi Odoo.
  - *Fix*: Validasi `Number.isFinite()` sebelum kirim; throw `DomainError('ODOO_BAD_AMOUNT')`.
