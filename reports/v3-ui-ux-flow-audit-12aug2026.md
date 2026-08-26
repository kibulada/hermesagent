# Kesia v3 — Deep UI/UX, Cross-Unit Flow & Obscure Module Audit Register (12/08/2026)

> Generated 2026-08-12 oleh Salsabila QA.
> Audit UI/UX & alur end-to-end mendalam pada codebase terbaru Kesia v3 (`E:\WORK KESIA\Project\kesiaV3`, commit `5300cb6`), berfokus pada alur antar instalasi, pengalaman pengguna, dan modul sekunder.

---

## 🔴 KELOMPOK 1: CRITICAL UI/UX & FLOW BLOCKERS

### 1. Tombol 'Batalkan' & 'Ganti Jadwal' Operasi Elektif di Papan Slot OK Missing
- **File & Baris**: `apps/web-clinic/src/features/emr/SurgerySlotBoard.tsx`.
- **Bukti Kode**: Papan Slot OK (`SurgerySlotBoard`) hanya menampilkan visualisasi jadwal. Jika pasien batal operasi atau minta ganti hari, **TIDAK ADA TOMBOL "BATALKAN OPERASI" / "GANTI JADWAL"** di UI Papan Slot OK. Staf OK harus menghapus jadwal dari DB secara manual.
- **Dampak**: Staf OK tidak bisa membatalkan / reschedule jadwal operasi pasien dari Papan Slot OK.

### 2. Form Asesmen Pra-Anestesi & Pra-Induksi Missing
- **File & Baris**: `apps/web-clinic/src/features/emr/SurgeryAssessmentDrawer.tsx`.
- **Bukti Kode**: Form asesmen bedah v3 baru memuat WHO Surgical Safety Checklist (Sign-In, Time-Out, Sign-Out). Form Asesmen Pra-Anestesi (evaluasi oleh Dokter Anestesi H-1 operasi) & Pra-Induksi (evaluasi sesaat sebelum pembiusan) **BELUM ADA**.
- **Dampak**: Risiko keselamatan pasien. Dokter Anestesi tidak punya form terstruktur untuk mencatat evaluasi & persetujuan pre-op.

---

## 🟠 KELOMPOK 2: HIGH UI/UX DEFECTS & WORKFLOW GAPS

### 3. Informasi Golongan Darah & Rhesus Pasien Tidak Tampil di Header EMR
- **File & Baris**: `apps/web-clinic/src/app/shell/EpisodeTab.tsx`.
- **Bukti Kode**: Header EMR pasien menampilkan Nama, No RM, Umur, Jenis Kelamin, dan Penjamin. **TIDAK MENAMPILKAN INFORMASI VITAL GOLONGAN DARAH & RHESUS**.
- **Dampak**: Saat situasi darurat (misal butuh transfusi darah cito), perawat/dokter harus membuka tab demografi pasien terlebih dahulu, memperlambat respon.

### 4. Worklist Fisioterapi / Rehab Medik Tidak Terhubung ke EMR Dokter
- **File & Baris**: `apps/web-clinic/src/features/penunjang/FisioPage.tsx`.
- **Bukti Kode**: Staf Fisioterapi melihat worklist pasien, tetapi hasil catatan sesi terapi **TIDAK OTOMATIS MUNCUL SEBAGAI CPPT BARU** di EMR Dokter DPJP.
- **Dampak**: Dokter DPJP tidak bisa melihat progres sesi fisioterapi pasien kecuali jika diberitahu secara lisan.

### 5. Retur Darah dari Bangsal ke Bank Darah Missing
- **File & Baris**: `apps/api/src/modules/clinical/bloodbank.service.ts`.
- **Bukti Kode**: Service `bloodbank.service.ts` memiliki method `issueUnit` (penyerahan kantong darah). Namun **TIDAK ADA METHOD `returnUnit`** jika kantong darah tidak jadi ditransfusikan & dikembalikan dari bangsal ke Bank Darah.
- **Dampak**: Stok kantong darah di Bank Darah tidak akurat, kantong darah yang batal terpakai dianggap sudah ditransfusikan.

### 6. Alur Permintaan Darah Cito (Emergency Blood Request) Missing
- **File & Baris**: `apps/web-clinic/src/features/penunjang/BankDarahPage.tsx`.
- **Bukti Kode**: Alur permintaan darah saat ini masih via order `supportOrders`. Belum ada alur permintaan darurat/cito dengan notifikasi prioritas tinggi ke Petugas Bank Darah.
- **Dampak**: Permintaan darah cito untuk pasien pendarahan masif diperlakukan sama seperti permintaan darah rutin.

---

## 🟡 KELOMPOK 3: MEDIUM UI/UX DEFECTS & INCONSISTENCIES

### 7. Tombol 'Back' / Kembali Inkonsisten di Seluruh Halaman
- **File & Baris**: Berbagai file seperti `PatientDetailPage.tsx`, `InvoiceDetailPage.tsx`, `MasterDataPage.tsx`.
- **Bukti Kode**: Beberapa halaman detail memiliki tombol `<ArrowLeftOutlined /> Kembali`, sementara halaman lain tidak. Tidak ada standar UI/UX tombol kembali yang seragam.
- **Dampak**: Pengguna bingung saat navigasi, harus mengandalkan tombol Back browser.

### 8. Paging / Penomoran Halaman di Beberapa Tabel Master Data Missing
- **File & Baris**: `apps/web-clinic/src/features/master/MasterDataPage.tsx` (Tab Tindakan, Obat, dll).
- **Bukti Kode**: Tabel master data menampilkan ribuan item dalam 1 halaman tanpa penomoran halaman (pagination).
- **Dampak**: Browser menjadi lambat/hang saat membuka tabel master data yang berisi ribuan baris.

### 9. Notifikasi Real-Time Hasil Lab/Rad Cito di EMR Dokter Missing
- **File & Baris**: `apps/web-clinic/src/app/shell/EpisodeTab.tsx`.
- **Bukti Kode**: Jika hasil lab/rad cito sudah keluar, tidak ada notifikasi real-time (badge merah / pop-up) di layar EMR Dokter yang sedang terbuka.
- **Dampak**: Dokter tidak langsung tahu jika hasil penunjang cito sudah tersedia, harus me-refresh halaman manual.

### 10. Konfirmasi 'Anda Yakin?' saat Menghapus Data Inkonsisten
- **File & Baris**: Hampir semua tombol hapus (`<Button danger icon={<DeleteOutlined />} />`).
- **Bukti Kode**: Beberapa tombol hapus menggunakan `<Popconfirm>`, sementara yang lain langsung menghapus data tanpa konfirmasi.
- **Dampak**: Risiko operator tidak sengaja menghapus data penting.

---

## REKAPITULASI HOURLY REGISTER (UI/UX & CROSS-UNIT FLOW)

| # | Nama Defect / Blocker | Category | File Target |
|---|---|---|---|
| **1** | Tombol Batal/Ganti Jadwal Operasi di Papan OK Missing | **CRITICAL** | `SurgerySlotBoard.tsx` |
| **2** | Form Asesmen Pra-Anestesi & Pra-Induksi Missing | **CRITICAL** | `SurgeryAssessmentDrawer.tsx` |
| **3** | Golongan Darah & Rhesus Tidak Tampil di Header EMR | **HIGH** | `EpisodeTab.tsx` |
| **4** | Worklist Fisioterapi Tidak Terhubung ke EMR Dokter | **HIGH** | `FisioPage.tsx` |
| **5** | Retur Darah dari Bangsal ke Bank Darah Missing | **HIGH** | `bloodbank.service.ts` |
| **6** | Alur Permintaan Darah Cito (Emergency) Missing | **HIGH** | `BankDarahPage.tsx` |
| **7** | Tombol 'Back' / Kembali Inkonsisten di Halaman | **MEDIUM** | Seluruh UI |
| **8** | Paging / Penomoran Halaman di Tabel Master Data Missing | **MEDIUM** | `MasterDataPage.tsx` |
| **9** | Notifikasi Real-Time Hasil Cito di EMR Dokter Missing | **MEDIUM** | `EpisodeTab.tsx` |
| **10** | Konfirmasi 'Anda Yakin?' saat Menghapus Data Inkonsisten | **MEDIUM** | Seluruh UI |

MEDIA:D:\Hermes-QAeports3-ui-ux-flow-audit-12aug2026.md
