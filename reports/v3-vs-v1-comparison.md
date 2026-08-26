# Kesia v1 vs v3 — Perbandingan Menu per Unit & Rekomendasi

> Generated 2026-08-07 oleh Salsabila QA.
> Sumber:
> - **v1** = `D:\Hermes-QA\sourcecode\kesia-fe` (branch `develop`, commit `5efa585ad`).
>   Detail menu per unit = `src/router/detail-routers/{unit}-details.js` (pageTitle + hideFromSidebar=false).
>   Global = `src/components/NavSidebar/index.js` + `src/constants/sidebar-menu.js`.
> - **v3** = `E:\WORK KESIA\Project\kesiaV3` (commit `869afa1`).
>   Global menu = `apps/web-clinic/src/app/nav.tsx` (MENU_TREE, 14 group, 140 leaf).
>   Form-engine = `db/seed/*.sql` + `db/migrations/0***.sql` (form_code registered).
>
> **Catatan penting**: v3 ≠ upgrade v1. Ini **green-field rebuild** (`apps/web-clinic` Vite+React18+AntD5, monorepo `libs/*`, mikro-service `apps/api` NestJS, BFF `apps/bff`, db per-tenant + RLS, transactional outbox → NATS → saga → Odoo). Pertanyaan "menu compare v3 vs v1" lebih tepat dibaca sebagai **feature parity**.

---

## 1. Struktur global (sidebar root)

| v1 role-routers (44 file)             | v3 group (nav.tsx)                          | Catatan v3 |
|---------------------------------------|---------------------------------------------|------------|
| `outpatient`, `outpatient-doctor`, `outpatient-doctor-new` | **Rawat Jalan** (17 leaf)                   | Kiosk + antrean online + verifikasi disatukan ke sini |
| `er-registration`, `er-doctor`, `er-nurse` | **IGD / Gawat Darurat** (8 leaf)            | |
| `inpatient`, `inpatient-doctor`, `inpatient-nurse` | **Rawat Inap** (8 leaf)                     | Tambah admisi, board, bed-mgmt, transfer, clinical-pathway |
| `doctor`, `doctor-remuneration`, `doctor-external` | (sebagian) **Rawat Jalan → Dokter Jaga** + Remunerasi di Keuangan | Form eksternal hilang |
| `pharmacy-staff`                      | **Farmasi** (9 leaf) + **Penunjang Medis**   | Worklist per unit (rajal/ranap/igd/ok) digabung jadi 1 |
| `mcu-doctor`, `mcu-registration`, `mcuInputData` | **Penunjang → MCU** (2 leaf)                | |
| `cath-lab-input-data`                 | **Penunjang → Cathlab**                     | |
| `physiotherapy`                       | **Penunjang → Fisioterapi / Rehab Medik**   | |
| `hemodialysis`                        | **Penunjang → Hemodialisa** (2 leaf: catatan + kerja) | |
| `medical-support-doctor`, `medicalSupportInput`, `medical-support-registration` | **Penunjang Medis** | Lab/rad disatukan (bukan terpisah per-role) |
| `lab-online`                          | **Penunjang → Lab Online**                  | |
| `billing-staff`                       | **Keuangan** (Kasir + Billing + Deposit + Treasury + Outstanding + Remunerasi + Accrual + Admedika + Tagihan Perusahaan + Odoo) | Pecah jadi 10 halaman, halaman IGD/Ranap terpisah |
| `casemix`                             | **BPJS → Casemix + Casemix Monitoring**     | |
| `adminBpjs`                           | **BPJS & Casemix** (config + SEP + Surat Kontrol + Rujukan + Antrean + Fingerprint + Pasien + Casemix + Monitoring) | Sekarang 9 leaf, tadinya 1 menu utama |
| `emrStaff`                            | **RM → EMR Staff**                          | |
| `arm`                                 | **RM → Tracer & Peminjaman**                | |
| `incidentReport`                      | **RM → Incident**                           | |
| `mpp`, `fsu-staff`                    | **RM → MPP + FSU + Monitoring Gizi**        | |
| `adminRs`                             | tersebar ke **Rekam Medis** + **Laporan** + **Keuangan** (tidak 1 halaman) | Audit Billing → `/rm/audit` |
| `admedika`, `accrual`, `treasury`, `doctor-remuneration` | **Keuangan** (semua di sini)                | |
| `profile`, `app-version`              | **Settings** + **Admin → Sistem**           | Versi tidak di-sidebar, ganti-password di TopBar |
| `adminRsOnline`                       | **Admin → Online (Lab Online, Home Swab & Queue TV)** | |
| `supervisor`                          | (tidak ada grup khusus)                     | RBAC role viewer |

v3 sama sekali TIDAK punya grup setara `Role Rawat Inap Dokter/Nurse` sebagai sidebar terpisah — semuannya **field** yang sama, gate via RBAC.

---

## 2. Menu per unit (pageTitle v1 yang visible, vs v3 yang ada)

### 2.1 Dokter Rawat Jalan (`/outpatientDoctor/*`)

v1 punya **28 menu visible** (hideFromSidebar=false) di `detail-routers/outpatient-doctor-details.js`:
`control-plan-letter, dashboard, doctor-initial-assessment, integrated-note-soap, integrated-note-all-unit, medical-resume, prescription-drugs-online, prescription-drugs-online-history, penunjang-medis-lab-radiologi, medical-support-expertise-input-form, onlineMedicalSupportExamination, riwayat-penunjang-medis-lab-radiologi, ekg, echo, eeg, konsultasi-dokter, introduction-to-hospitalization, telemedicine`.

v3 punya **satu halaman workspace** `DoctorWorkspacePage` dengan tab dinamis di `/dokter/worklist` dan `/emr/worklist`, lalu **5 halaman verifikasi/tindakan khusus** terpisah:
- `/verifikasi/ttd` (Tanda Tangan Dokter)
- `/dokter/konsul` (Konsul Internal)
- `/jadwal/operasi` (jadwal OK)
- `/registrasi/dibatalkan`
- `/verifikasi/resep`

| Item v1 | v3 ada? | Lokasi v3 | Catatan |
|---|---|---|---|
| dashboard (list kunjungan) | ✅ | `/dokter/worklist`, `/emr/worklist` | Rajal + ranap split Segmented (`a8a5d7b`) |
| initial-assessment doctor | ✅ | Form-engine `medical-assessment` (migrasi 0152) + tab di DoctorWorkspace | |
| integrated-note SOAP | ✅ | Form `integrated-note` + station di workspace | Ajv STRICT, ICD-10/9 enum, S/O/A/P wajib minLength |
| medical-resume | ✅ | `/rm/medical-resume` (WYSIWYG print) | Tulis + cetak |
| prescription-drugs-online | ✅ | Tab Resep di workspace | drugId round-trip, edit, telaah, FEFO batch |
| prescription-drugs-online-history | ✅ | CPPT timeline (tab "Riwayat Resep" di workspace) | |
| penunjang-medis-lab-radiologi | ✅ | OrderSection (multi-item Form.List) di workspace | qty-aware, source_order_id back-ref |
| medical-support-expertise-input-form | ✅ | `PenunjangPage` lewat FE `LabTab/RadTab` | Structured result + ekspertise doctor assignment (migrasi 0080) |
| onlineMedicalSupportExamination | ✅ | `/penunjang/lab-online` | Drive-thru |
| riwayat-penunjang-medis-lab-radiologi | ✅ | `/penunjang/riwayat` | `e7f9a94` quick-win |
| ekg | ✅ | Form `ecg-interpretation` (migrasi 0071) di DoctorWorkspace | Waveform-strip canvas masih TODO (perlu feed alat) |
| echo, eeg | ⚠️ partial | Echo/EKG di FormStation generik; EEG di NurseWorkspace | Belum dedicated workspace, tapi struktur bisa |
| konsultasi-dokter | ✅ | `/dokter/konsul` + tab Konsul di workspace | |
| introduction-to-hospitalization (SPRI) | ✅ | `CarePlanSection` tab + `/igd/order-ruang` | Cetak SPRI di `/cetak/spri` |
| telemedicine | ✅ | `/verifikasi/telemedicine` + `/emr/telemedicine/:episodeId` (Jitsi) | Iframe Jitsi publik utk dev, swap ke server+JWT prod |
| control-plan-letter | ✅ | Tab "Surat Kontrol" + `/bpjs/surat-kontrol` + `/bpjs/pasien` (operator) | Pick rujukan saat registrasi |
| invasive-procedure / cathlab-order | ✅ | OrderSection + OperasiPage | |
| medical-action-summary | ✅ | Drawer RL di workspace | |
| **medical-rehabilitation** | ✅ | `/penunjang/rehab-medik` | Tab NursingWorkspace generik |

**Flag**: v3 sitasi SOAP diperketat (periksa PP#6262 jika ada tiket tikus); residu `mcuPharmacyForm.js` v1 tidak ada → MCU dipakai Form generik.

### 2.2 Dokter IGD (`/erDoctor/*`)

v1 = 21 menu visible di `er-doctor-details.js`:
`erdoctor, dashboard, dischargeResume, integrated-note, triageMedical, prescription-drugs-online, medical-support-expertise-input-form, onlineMedicalSupportExamination, ekg, echo, eeg, doctor-consult, cathlab-order, invasive-procedure, sidebar.cathlabInputData`.

| Item v1 | v3 ada? | Lokasi v3 | Catatan |
|---|---|---|---|
| dashboard | ✅ | `/igd/board` (triase board) | Real-time queue |
| triage-medical-record | ✅ | `/igd/triase` | Form `triage-igd` (migrasi 0072 disposisi) |
| integrated-note SOAP | ✅ | Form `integrated-note` (sama dengan rajal) | |
| dischargeResume | ✅ | Cetak resume + tombol discharge | WYSIWYG |
| prescription-drugs-online | ✅ | `/igd/resep` + `/farmasi/igd` | |
| medical-support (lab/rad) | ✅ | `/penunjang/registrasi` | |
| onlineMedicalSupportExamination | ✅ | `/penunjang/lab-online` | |
| medical-support-expertise-input-form | ✅ | `/penunjang/lab` (assignment dokter `migrasi 0080`) | |
| ekg, echo, eeg | ✅ | `ObservationStationPage` + DoctorWorkspace | |
| doctor-consult | ✅ | `/dokter/konsul` | |
| cathlab-order | ✅ | OrderSection + OperasiPage | |
| **cathlab input data (CathLabInputData)** | ✅ | `/penunjang/cathlab` | ObservationStationPage + RBAC khusus |
| invasive-procedure (note tindakan) | ✅ | order tindakan medis station generik | |

### 2.3 Dokter Rawat Inap (`/inpatientDoctor/*`)

v1 = 19 menu di `inpatient-doctor-details.js`:
`inpatientDoctorDashboard, dashboard, dischargeResume, integrated-note, medicalNote, prescriptionDrugsOnline, onlineMedicalSupportExamination, ekg, echo, eeg, consult-take-care, konsultasi-dokter, control-plan-letter, cathlab-order`.

| Item v1 | v3 ada? | Lokasi v3 | Catatan |
|---|---|---|---|
| dashboard | ✅ | `/ranap/board` | `RanapBoardPage` (`a8a5d7b`) |
| medicalNote (SPRI/introduction) | ✅ | CarePlanSection + `/igd/order-ruang` → `/ranap/admisi` | SPRI + cetak |
| discharge-resume | ✅ | `/rm/medical-resume` + tab discharge di workspace | |
| integrated-note SOAP | ✅ | Form `integrated-note` (sama) | |
| prescriptionDrugsOnline | ✅ | `/ranap/resep` + FarmasiPage | |
| consult-take-care | ✅ | Tab "Konsultasi Take Care" di workspace | |
| control-plan-letter | ✅ | Sama dengan rajal | |
| **bed-management / transfer** | ✅ | `/ranap/bed` + `/ranap/transfer` | `OperasiPage` + ranap board |
| **visite harian** | ✅ | `migrasi 0082` `inpatient_visites` + EpisodeChargesPage tab | Tarif via resolveActionPrice/chargeAmount |
| clinical-pathway | ✅ | `/ranap/clinical-pathway` + `/master/clinical-pathway` | Migrasi 0159 |

### 2.4 Dokter Spesial (Bedah/Fisio/HD/MCU/KK/PPI)

v1 = `surgery-service.js` (28 item):
`surgery-assessment, surgery-report, perfusionist-form, pre-induction-assessment, sedation-assessment, assesment-pre-anesthetist, nursing-perioperative-notes, monitoring-anesthetist, monitoring-post-surgery-instruction, surgery-prescription, preop-preparation-record/documentation, cardiac-conference, patient-transfer-form, integrated-note, nursing-careplan, doctor-therapy-plan, postoperative-assessment`.

v3 form-engine form sete (migrasi 0083–0096):
- **Set Bedah (5 form)** di `OperasiPage.drawer tabbed`:
  - Asesmen Pra-Anestesi (0084)
  - Pasca-Anestesi Aldrete scored (0085)
  - WHO Perioperatif Checklist (0086)
  - Monitoring Anestesi intra-op objectArray (0087)
  - Asesmen Sedasi (0088)
- **Operative Report SOAP** di `OperativeReportForm` (migrasi 0059)
- **Fisioterapi** di `/penunjang/fisioterapi` (migrasi 0144 parity)
- **Hemodialisa catatan** di `/penunjang/hemodialisa-catatan`
- **Partus & Delivery Report** di form `partus-record` (migrasi 0155) + `delivery-report` (0083–0093 batch)
- **PPI Surveilans Infeksi** di `ppi-surveillance` (migrasi 0090) + Medical Devices (0150)
- **Asesmen Kebidanan Awal** + **Partus kala I–IV** + **Asesmen Nifas** (migrasi 0091–0093)
- **Neonatus + Downe Score + KPSP tumbuh-kembang** (migrasi 0094–0096)
- **Geriatri GDS-15** (migrasi 0089)

→ **v3 LEBIH LENGKAP** di sini (form-engine generic). Yang masih TODO:
- **Cardiac Conference** belum ada di v3 (perlu cek form).
- **Surgery-prescription (resep spesifik OK)** belum dipecah; pakai farmasi OK generik `/farmasi/ok`.

### 2.5 Perawat Rawat Jalan (`/outpatient-nurse*`)

v1 = 33 menu di `outpatient-nurse-details.js`: nurse-assessment, obstetri, ginekologi, integrated-note SOAP, EKG, vital-sign, medical-action, prescription, PRMRJ, NICU, legacy-archive, medical-resume.

| v1 | v3 | Catatan |
|---|---|---|
| nurse-assessment | ✅ | form-engine `nursing-assessment` + tab di NurseWorkspace (`mpp-evaluasi`/`mpp-implementation`/`mpp-screening` di seed) |
| nurse-assessment-obstetri | ✅ | `ObstetricForms.tsx` → `Obg-exam` + Asesmen Kebidanan (0091) + Asesmen Nifas (0093) + Partus (0092) |
| gynecology-checkup | ✅ | `ObgynForms.tsx` |
| integrated-note SOAP | ✅ | shared |
| ekg | ✅ | ecg-interpretation di workspace |
| legacy-archive | ✅ | Tab CPPT history |
| medical-action | ✅ | form-engine aksi medis |
| vital-sign | ✅ | form `vital-sign` (seed) + tab di NurseWorkspace |
| **PRMRJ (Pra Medik Rawat Jalan)** | ⚠️ tidak eksplisit | Tercakup di initial-assessment doctor perintegrasi |
| **NICU neonatus** | ✅ | PediatriForms + Asesmen Neonatus (0095) + Downe Score |
| medical-resume | ✅ | sama |
| medical-action-summary | ✅ | drawer RL |
| prescription-drugs-online | ✅ | tab Resep di NurseWorkspace |

### 2.6 Perawat IGD (`/er-nurse*`)

v1 = 21 menu di `er-nurse-details.js`:
`ernurse, dashboard, triageMedical, assessmentEr, nursing-careplan, nursing-care, nurse-implementation, integrated-note, vital-sign, vital-sign-ews-maternal, fluid-monitoring, prescription-drugs-online, medicine-therapy, educational-needs, care-plan-hemodialysis`.

| v1 | v3 | Catatan |
|---|---|---|
| triage-medical-record | ✅ | `/igd/triase` form `triage-igd` |
| assessment-ER | ✅ | form `nursing-assessment` + tab |
| nursing-careplan SDKI/SLKI/SIKI | ✅ | `NursingCarePlanSection` |
| nursing-care ( implementasi) | ✅ | nurse-implementation form + tab |
| integrated-note SOAP | ✅ | shared |
| vital-sign + ews maternal | ✅ | form `vital-sign` di NurseWorkspace |
| fluid-monitoring | ⚠️ tidak eksplisit | Harus cek di MedicalSupport/EWS khusus |
| medicine-therapy IGD | ⚠️ partial | medicine-therapy di farmasi/rajal generik |
| educational-needs | ✅ | form edukasi di NurseWorkspace |
| care-plan-hemodialysis | ✅ | `/penunjang/hemodialisa-catatan` |

### 2.7 Perawat Rawat Inap (`/inpatient-nurse*`)

v1 `inpatient-nurse.js` cuma 3 menu (lain tersebar di komponen). v3 di NurseWorkspacePage:
- Vital-sign / TTV (form `vital-sign`)
- Implementasi (migrasi 0156 `nursing_implementations`)
- Asesmen awal + Asesmen Lanjutan
- SDKI/SLKI/SIKI care-plan
- Edukasi
- Discharge Planning (form `discharge-planning`)
- EWS, Resep, Visite, CPPT history, Observasi lain
- **NEW**: Discharge Planning (0076), Braden & Morse (0060), Asesmen Alergi (0070)

### 2.8 Farmasi (rajal/ranap/igd/ok/online)

v1: 1 halaman generik `pages/pharmacy-staff/**`. v3: **6 worklist terpisahkan** (`/farmasi/rajal, /farmasi/ranap, /farmasi/igd, /farmasi/ok, /farmasi/apotek-online, /farmasi/stok`). Fitur v3 **LEBIH LENGKAP** dari v1: verifikasi resep, telaah, return, FEFO batch, label barcode ZPL, rekap penyerahan, penjualan bebas (0097, money-code).

### 2.9 Penunjang Medis

v3 **LEBIH LENGKAP**: lab + radiologi + LIS ingest HL7, DICOM viewer (parser pure-JS MONOCHROME8/16), Cathlab, Hemodialisa, Fisioterapi, Rehab Medik, MCU paket (12 exam + sertifikat), Bank Darah (crossmatch + 7 endpoint + scanner), Epidemiologi, Spesimen barcode + chain-of-custody (migrasi 0079), Critical Value alert (migrasi 0056), Specimen barcode.

### 2.10 Rekam Medis

v3: `/rm/{arm, coding, emr-staff, satusehat, medical-resume, audit, incident, mpp, fsu, fsu-monitoring, incident}`. Coding ICD multi-picker, SatuSehat konsol mock, audit, ARM, tracer. **Hilang**: `doctor-details/print-certificate` (v1 ada cetak surat rawat inap otomatis); `inpatient-audit` (v3 partisi ke `/rm/audit`).

### 2.11 BPJS

v3: 9 leaf (config, SEP, surat-kontrol, rujukan, antrean, fingerprint, pasien, casemix, casemix-monitoring). Mock-first; jalur riil butuh kredensial Kemenkes/BPJS.
**Hilang dari v3**:
- adminBpjs *sebagai konsolidator* — dipisah sesuai spec (oleh-design).
- CekPeserta + Rujukan VClaim (mock sudah ada, implementasi non-mock gated).

### 2.12 Keuangan / Kasir

v3: kasir deposit, billing/invoice, deposit list, outstanding, treasury, remunerasi, accrual, admedika, tagihan perusahaan, monitoring odoo (saga status).
**Persis dengan v1 + tambah**: Admedika, Tagihan Perusahaan (migrasi 0098 partner-breadth), Monitoring Odoo saga (idempotent retry).

---

## 3. Poin #2 — Flow setiap unit (bandingkan UX alur)

### 3.1 Rajal (pasien → selesai)
**v1**: registrasi → antrean → triage perawat poli → initial assessment → SOAP → order penunjang/resep → verifikasi → selesai → billing → kasir.
**v3**: registrasi (`/registrasi/pasien` stepper) → antrean station (`/perawat/station`) → workspace perawat (TTV/nurse done) → worklist dokter (`/dokter/worklist`) → DoctorWorkspace (Tabs: SOAP, Resep, OrderSection Penunjang, Visite, CarePlan, TTV, CPPT history) → order charge otomatis → `BillingPage` (`/kasir/billing`) → kasir.

**UX delta v3**:
- ✅ Klik kanan di worklist → langsung buka episode (drawer PatientTabs).
- ✅ Atur Tab per-user (migrasi 0158 menu_prefs_scope).
- ✅ Konsul & Visite dalam tab langsung tanpa pindah halaman.
- ✅ Finish gate (harus TTD dulu) configurable per site.
- ✅ Kiosk self-check-in top-level route.
- ⚠️ Initial assessment dokter v3 tidak ada step terpisah; menjadi tab di DoctorWorkspace.

### 3.2 IGD
**v1**: triase medis → order ruang → initial assessment ER → SOAP → order obat → rawat jalan/inap/pulang.
**v3**: `IgdBoardPage` (triase) → `ErRegistrationPage` → `IgdTriagePage` (form `triage-igd` + aksis 5 level) → `OrderInpatientPage` (SPRI → cetak + visit) → `IgdDataPage` history → Verifikasi Pasien Temporary (merge MR).

**UX delta v3**:
- ✅ Disposisi IGD enum (rawat-inap/jalan/observasi/rujuk/pulang-paksa/meninggal) di TRIAGE.
- ✅ Merge pasien temporary ke MR permanen.
- ✅ Cetak gelang barcode ZPL, kartu antrian ZPL.
- ⚠️ Belum ada medical-action-summary khusus IGD.

### 3.3 Ranap
**v1**: SPRI → admisi → bed-board → visite harian → integrasi SOAP/resep → discharge planning → discharge.
**v3**: SPRI (CarePlan) → `/ranap/admisi` → `RanapBoardPage` (board per-bangsal) → visite harian (`/ranap/visite` via VisiteSection di workspace `migrasi 0082`) → SOAP + Resep + Konsul ambilalih tab → Discharge Planning (form `discharge-planning`) → Sensus RL (`/laporan/sensus-ranap`).

**UX delta v3**:
- ✅ Visite harian otomatis terakomodasi ke `episodeCharges` (tarif resolve).
- ✅ Transfer bed + perpindahan ledger (migrasi 0053).
- ✅ Discharge Planning form wajib dischargeCondition enum.
- ✅ Resume medis WYSIWYG.
- ⚠️ SOAP visite Dokter Ranap v3 belum ada step terstruktur di workspace selain Visite tab.

### 3.4 BPJS / SEP
**v1**: seleksi poli → ambil nomor antrean → task WS.
**v3**: daftar pasien BPJS → konsol SEP (issued/return/failed) → rujukan picker saat registrasi → task antrean 7-step (migrasi 0054) + WS push (gate ke kredensial prod).

### 3.5 Penunjang
**v1**: order → spesimen → kerja → hasil → ekspertise → verifikasi.
**v3**: order (multi-item qty) → spesimen barcode + chain-of-custody (migrasi 0079) → kerja → hasil terstruktur (CBC analit / radiologi finding-impression) → ekspertise (assigned_doctor migrasi 0080) → verifikasi + stempel + kode-verifikasi offline → cetak dengan TTD + DRAFT watermark.

### 3.6 Kasir
**v1**: bikin invoice manual → edit harga → split coverage.
**v3**: **BillingPage** tarik charge otomatis per episode (`/episodeCharges` agregat dari obat/lab/rad/MCU/operasi/visite/akomodasi) → coverage self/BPJS/asuransi (matrix) → split → editable price + item discount + global discount → bill.

---

## 4. Poin #4 — Yang ADA di v1 tapi TIDAK ADA di v3 (kebalikannya)

| Item v1 | File v1 | Status v3 |
|---|---|---|
| `ResetPasswordPage` + `ForgotPasswordPage` berdiri | `login/forgot-password, reset-password` | ❌ v3 hanya `LoginPage` dev-mode (role picker). Migrasi 0151 `user_password` ada tabel tapi belum link reset flow. **TODO login ulang pakai Keycloak**. |
| `company-partner-site` (lokasi mitra per partner) | `pages/company-partner-site/` | ❌ |
| `ErpPoster` (stub modul sinkronisasi ke ERP/Odoo) | `pages/ErpPoster/ErpMainView.js` (stub) | Tidak ada FE — v3 saga PostBillingToOdooo `apps/relay`. |
| `bed-monitoring-tv` (TV per bangsal) | `pages/bed-monitoring-tv/` | ✅ built `BedMonitorTvPage` (`/ranap/bed-tv`) |
| `DoctorExternal` (enroll dokter eksternal + jadwal) | `pages/DoctorExternal/` | ❌ enrolment saja yang hilang; verif telemedicine ada. |
| `medical-support-history` per pasien | `pages/medical-support-history/` | ✅ `/penunjang/riwayat` |
| `supplier-item` (item-per-supplier + bulk import) | `pages/supplier-item/` | ✅ `MasterDataPage` ResourceTab supplier-items (3b20a44) |
| `forgot-password` (UI lupa password) | `pages/forgot-password/` | ❌ lihat di atas |
| `changelog` di /admin | `pages/changelog/` | partial — `release-notes` master resource, TIDAK ada feed versioning visible |
| `company-partner-group` (group multi tipe) | `pages/company-partner-group/` | ❌ insurer-groups ResourceTab ada, tapi vendor/contractor **tidak** |
| `constant/` (pusat konstanta klinis) | `pages/constant/` | (tidak kritis, pindah ke FE constants) |
| `incomeTax` berdiri | `pages/IncomeTax/` | ✅ di `/master/keuangan` ResourceTab |
| `home-dashboard` (dashboard role-spesifik) | `pages/home-dashboard/` | ❌ v3 hanya `/dashboard` generik |
| `OutPatient`/`DashboardComponent` | `pages/OutPatient/` | ✅ `/registrasi/data` (DataPasienPage) |

**Lebih spesifik hilang v3** (per `PARITY-DEPTH-GAPS.md`):
- ❌ **TV Display per bangsal terpisah** dari queue TV generik (DONE `bed-monitoring-tv`, tapi belum ada `/antrean/tv/:wardId`-style).
- ❌ **Forgot/Reset password flow** (perlu Keycloak integration).
- ❌ **DoctorExternal enrollment** + external schedule master full.
- ❌ **Company-partner CRUD vendor/contractor** (v3 narrow ke insurer).
- ❌ **Reset password workflow admin**.
- ❌ **Detail `inpatient-audit` standalone** (tersebar ke `/rm/audit` + `/keuangan/outstanding`).
- ❌ **Change-password form** di settings.
- ❌ **ActionRefsForm/View** untuk `other-medical-support` non-standar.

---

## 5. Poin #5 — Potensi fitur yang HARUS ADA di v3 (berdasarkan gap & best practice SIMRS modern)

### 5.1 WAJIB (krítikal klinis / belum implemented atau masih parcial)
1. **Forgot/Reset Password** end-to-end via Keycloak/passwordless (login re-implementation). Penting karena migrasi 0151 sudah siapkan kolom password tapi flow masih nol.
2. **DoctorExternal enrolment + external schedule master** (saat telemedicine butuh dokter eksternal; saat ini `/verifikasi/telemedicine` ada, tapi registrasinya nol).
3. **Hard-gate TTD sebelum finishDoctor** (PP#7485) — keputusan produk; saat ini default "catat tanpa blokir".
4. **VClaim/Antrean WS real** (kredensial Kemenkes/BPJS). Saat ini mock-first.
5. **EKG waveform-strip canvas** (form `ecg-interpretation` skalar sudah ada; butuh feed alat + drawing).
6. **INA-CBG grouper biner Kemenkes** (saat ini auto-grouper indikatif).
7. **DICOM viewer LENGKAP** (cornerstone.js/OHIF — saat ini MONOCHROME 8/16 only, terkompresi = unduh).
8. **LIS MLLP bridge** (saat ini butuh POST HL7 manual).
9. **TTD Gate (keputusan produk)**: hard-block finish tanpa TTD.

### 5.2 PENTING (gap depth yang berulang di banyak tiket)
10. **AdmissionDate resolver di PDF Invoice FE** (sudah selesai PP#7486 — verify regressions).
11. **Verifikasi Signature config-driven** (`getConfigSignatureType(configSignature, docType)` dari sitemanagement → 60+ page belum pakai).
12. **Print Sertifikat Rawat Inap otomatis** (cetak otomatis per discharge).
13. **Nursing Implementation report PDF/WYSIWYG** (form ada 0156).
14. **CCR/PARR rekap per unit (Print Certificate Rawat Inap)**.
15. **Resep OK (surgery)** spesifik surgery (saat ini generik `/farmasi/ok`).
16. **Inpatient Audit mendalam** (rawat inap audit form-driven dengan total billing recompute).
17. **Change password** form di Settings (migrasi 0151 landasan ada).
18. **Multi-role login** (login sebagai dokter+nurse sekaligus).
19. **Food Service Unit order diet realtime ke dapur** (saat ini CRUD; belum integrasi POS dapur).
20. **Mobile JKN Antrean realtime WS** (saat ini task-id saja; WS push butuh kredensial).
21. **Perpindahan bed-TV with kelas/tarif delta** (saat ini display only).
22. **Manajemen kamar bed real-time (BOR/LOS/TOI auto-recalc)**.
23. **Dashboard per-unit (Bed Board, Farmasi Queue Realtime, Map Poli)**.
24. **OneSehat Composition (Observation & Condition push)** (saat ini Encounter only).
25. **MCU Group Registration flow** (saat ini 1-form MCU exam saja).
26. **PPI surveillance dashboard + bundle**.
27. **Bundle operasi (template operasi paket)**.
28. **Resep Racikan kompilasinya** (saat ini item per-baris generik).
29. **Telemedicine consent form + signature sebelum video**.
30. **E-resep printed barcode** (untuk verifikasi cepat di farmasi).

### 5.3 NICE-TO-HAVE (UX modernization)
31. Dark mode (sebagian, m9263a4).
32. Form Builder UI drag-drop (migrasi 0083+ registry sudah ada).
33. Atur Tab per-user (DONE mig 0158).
34. Activity Rail timeline-aware (v3 sudah ada `ActivityRail.tsx`).
35. Realtime notifikasi di TopBar (DONE notifications mig 0062).
36. Filter site by `cross_site_read` + audit (per spec R3).
37. Status composite badge (R7 sudah implementasi parsial).
38. PHI masking di semua list yang menampilkan NIK (R9 server-side DONE).
39. **Audit log per role-action** (siapa-delete-what-when untuk transaksi uang).
40. **Offline mode** untuk workstation (saat ini always-online).
41. **Voice command SOAP** (saat ini mic STEP UI ada, integrasi Gemini partial).
42. **Tele-consult video multiparty** (saat ini 1 pasien : 1 dokter).
43. **Custom Menu per-role site** (CUSTOM_MENU_ORDER v1 ada, v3 belum feature flag).
44. **Notification per-event penting (SEP issued/failed, resep critical, hasil lab verified)**.
45. **Inbox universal cross-module** (clinical + billing + farmasi + casemix).
46. **Filter/search cross-episode patient EMR timeline aggregasi**.
47. **Aksesibilitas screen-reader verified (aria di tabel antrian)**.
48. **Export PDF RS-template (bukan raw HTML print)**.
49. **Bulk import Tarif ICD/Obat (CSV→preview→apply)**.
50. **Audit Trail uang (INV/PAY/VOID/ADJ)** di ledger-like view.

---

## 6. Ringkasan prioritas temuan

| # | Item | Risk | Effort | Sumber |
|---|---|---|---|---|
| 1 | v3 ≠ upgrade v1; ini green-field | Komunikasi | 0 | README v3 + PARITY-BACKLOG |
| 2 | Login/Reset Password flow masih stub | Keamanan | M | mig 0151 |
| 3 | DoctorExternal enrolment hilang | Operasional | M | tickets DPP# |
| 4 | v1 punya 44 role-routers, v3 punya 14 group flat + RBAC | UX nav | S | NavSidebar vs nav.tsx |
| 5 | Form-engine sudah 26+ form termasuk bedah-set 5; sisa banyak | Patch | L | PARITY-BACKLOG + DEPTH-GAPS |
| 6 | Custom menu order per-role per-site hilang (v1 feature) | UX | S | NavSidebar.js:27-94 |
| 7 | Hard-gate TTD belum on (keputusan produk) | Compliance | S | memo AGENTS |
| 8 | `dataHospital.additionalInfo.*` flags (configSignature, dll) belum propagate ke 60+ page | Klinis | M | memory BBRJ |

### Tabel ringkas MAPPING v3 leaf → v1 page folder
(Dipotong di laporan ini, tersedia sebagai `v3-vs-v1-mapping.csv` terlampir untuk referensi.)
