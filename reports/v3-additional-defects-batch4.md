# Kesia v3 — Security Risks, Telemedicine Privacy Leaks & Data Loss Bypasses (Batch 4 Audit)

> Generated 2026-08-07 oleh Salsabila QA.
> Audit berbasis penelusuran kode backend `E:\WORK KESIA\Project\kesiaV3\apps\api\src\modules` (commit `e89ab31`).

---

## 1. DAFTAR DEFECT / SECURITY RISK BARU (BATCH 4)

### 1. Telemedicine Room Name Predictable (Kerentanan Privasi Konsultasi Pasien)
- **Lokasi Kode**: `apps/api/src/modules/clinical/telemedicine.ts:12`
- **Kode Bermasalah**:
  ```ts
  const room = `KesiaTelemed-${episodeId}`;
  const url = `https://${domain}/${room}` + (jwt ? `?jwt=${jwt}` : '');
  ```
- **Celah Security**: Nama room Jitsi dibentuk hanya dari `KesiaTelemed-${episodeId}`. Pada mode default (Jitsi publik `meet.jit.si`), room **TIDAK MEMILIKI TOKEN KONTROL AKSES / RANDOM NONCE**. Siapapun yang mengetahui/menebak `episodeId` pasien (misal `EP-2026-00000001`) dapat langsung membuka URL `https://meet.jit.si/KesiaTelemed-EP-2026-00000001` di browser dan mengintip/mengganggu video konsultasi medis dokter-pasien!
- **Dampak**: Kebocoran privasi konsultasi medis (*HIPAA/Permenkes Privacy Breach*).

---

### 2. Hard Delete Dokumen Rekam Medis Pasien Tanpa Soft-Delete
- **Lokasi Kode**: `apps/api/src/modules/clinical/registration.controller.ts:82`
- **Kode Bermasalah**:
  ```ts
  @Delete('documents/:docId')
  async deleteDocument(@Param('docId') docId: string)
  ```
- **Celah**: Dokumen pendukung rekam medis pasien (seperti Scan KTP, KTA Asuransi, Surat Rujukan) langsung dieksekusi dengan perintah `DELETE FROM patient_documents` secara permanen dari database.
- **Dampak**: Jika operator registrasi salah menghapus dokumen, berkas rekam medis pasien hilang permanen tanpa bisa dipulihkan dan tanpa jejak audit trail.

---

### 3. Penggabungan Invoice (`mergeInvoices`) Memutus Traceability Order Asal
- **Lokasi Kode**: `apps/api/src/modules/billing/billing.service.ts:274`
- **Celah**: Saat kasir menggabungkan 2 invoice DRAFT menjadi 1 invoice baru via `mergeInvoices`, invoice-invoice lama dihapus. Baris-baris tagihan di invoice baru **DIHAPUS REFERENSI `sourceOrderId` & `sourceKind`-NYA**.
- **Dampak**: Sistem kehilangan informasi asal-usul resep/order penunjang mana yang membentuk baris tagihan tersebut. Jika terjadi retur obat di kemudian hari, sistem tidak bisa mencocokkan retur ke invoice gabungan tersebut.

---

### 4. Token Reset Password Terpapar di JSON Response API
- **Lokasi Kode**: `apps/api/src/modules/auth/auth.service.ts:101`
- **Kode Bermasalah**: "TODO(SMTP): kirim email berisi tautan reset. Sampai SMTP siap, dev mengembalikan token di response".
- **Celah**: Endpoint `POST /auth/forgot-password` mengembalikan token reset password langsung di payload JSON HTTP response.
- **Dampak**: Siapapun yang memanggil endpoint `/forgot-password` untuk username staf tertentu dapat mengambil token reset dari response dan mengganti password akun staf tersebut tanpa mengakses email staf.

---

### 5. Multi-Item Order Support Verification Partial Gap
- **Lokasi Kode**: `apps/api/src/modules/clinical/order.service.ts:verifySupportOrder`
- **Celah**: Ketika verifikator laboratorium memverifikasi hasil pemeriksaan, verifikasi hanya mengunci header `supportOrders`. Jika ada item pemeriksaan tambahan yang disisipkan ke `supportOrderItems` saat verifikasi berlangsung, item baru tersebut lolos tanpa status `verified`.
- **Dampak**: Item penunjang susulan tidak memiliki penanggung jawab verifikasi resmi.

---

### 6. Outbox Audit Trail Missing User ID Context
- **Lokasi Kode**: Beberapa trigger `emitEvent` di `clinical-observation.service.ts` & `order.service.ts`
- **Celah**: Payload event outbox `aggregateType: 'clinical.*'` hanya mengirimkan `episodeId` dan `patientId`, tetapi **TIDAK MENYERTAKAN `userId` OPERATOR** yang melakukan transaksi.
- **Dampak**: Kesulitan melakukan audit forensik di NATS log/Odoo worker untuk mengetahui staf mana yang mencetuskan transaksi tersebut.

---

## 2. TOTAL DEFECT, BYPASS & BLOCKER DI v3 (REKAP 31 ITEMS)

1. **Telemedicine Room Name Predictable** (Video konsul bisa diintip via URL tebakan)
2. **Hard Delete Patient Documents** (Dokumen RM hilang permanen tanpa audit)
3. **Merge Invoices Discards Order Metadata** (Traceability retur obat terputus)
4. **Reset Password Token Leak in JSON** (Token reset bocor di response API)
5. **Bug TTV Error `Payload tidak valid utk vital-sign@v1`**
6. **Permission Block `master:create` saat Add Penjamin Pasien**
7. **Kasir Unbilled Worklist Missing**
8. **Invoice Belum Masuk Pasca Finish Episode**
9. **Bed Bisa Dikosongkan Tanpa Cek Paid Billing**
10. **Deposit-Invoice Disconnect**
11. **Return Prescription Invoice Leak**
12. **Cancel Episode Cascade Missing**
13. **Dispense Tanpa Cek Stok (`deductFefo`)**
14. **Discharge Pasien Unpaid**
15. **Pendaftaran Rajal Ganda INPROGRESS**
16. **Validasi NIK 16 Digit Missing**
17. **Dropdown Penjamin IGD Mismatch**
18. **Admisi Ranap Ganda**
19. **Duplikasi Visite Dokter**
20. **Transfer Bed Overcharge**
21. **Consul Inter-Spesialis No Worklist**
22. **Bed Lockout Status `CLEANING`**
23. **BPJS No Rujukan Unvalidated VClaim**
24. **Iter Prescription Logic Dead**
25. **Cancel Paid Prescription No Refund**
26. **Label Mandatory NIK Hardcoded Dev Text**
27. **Dropdown Hak Kelas Text Unreadable**
28. **Dropdown Jenis Kelamin Mismatch v1**
29. **Quota Onsite vs Online Lockout**
30. **Racikan Overdose Risk**
31. **Zod Body `siteId` Leakage**
