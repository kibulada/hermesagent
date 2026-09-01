## 6. Protokol Review Tiket (QA / Code Review)
   ├── 6.1. Metodologi CRUD per Tiket
   ├── 6.2. Wajib Pull Develop Terbaru Sebelum Review Tiket
   ├── 6.3. Stock Item — Arsitektur Cache Redis
   └── 6.4. ICU Transfer In/Out Form — Catatan Arsitektur

---

## 8. Environment matrix testing

Testing scope per environment. Selalu **konfirmasi build/branch yang di-test** sebelum reporting hasil.

### 8.1. Dev EKS (kesia-staging)

| Aspek | Detail |
|-------|--------|
| Cluster | `kesia-staging` (AWS EKS, region `ap-southeast-3`) |
| Namespace utama | `development` |
| URL FE | `https://dev.kesia.id` (verify aktual URL) |
| Odoo backend | `https://odoo-dev.kesia.id` (verify aktual URL) |
| Metabase | `https://dashboard.staging.kesia.id` |
| Data | Boleh di-modifikasi untuk testing; tidak boleh data pasien real |
| Cara akses | `kubectl` context dev EKS, credentials di team vault |

### 8.2. Staging per RS (on-prem)

Setiap RS punya staging namespace `<nama>-staging` di cluster on-prem-nya. Detail cluster + credential ada di §1 KNOWLEDGE.md.

| RS | Staging URL Odoo | Staging URL FE | Metabase |
|----|------------------|----------------|----------|
| RS ABK | (isi manual saat setup) | | `https://dashboard.rsabk.kesia.id` |
| RS Avisena | | | `https://dashboard.rsavisena.kesia.id` |
| RS Tasik | | | `https://dashboard.jhc-tasik.kesia.id` |
| ... | | | (referensi lengkap di §1.C) |

**Convention testing per site**:
- Test data pasien: pakai prefix `TEST-` di nama, `1900-01-01` di tanggal lahir supaya mudah di-filter.
- Test user role: pakai user `qa_<initial>` (mis. `qa_kb`) — kalau belum ada, minta dev buat.
- Setiap bug report **wajib** sebut RS + build/tag yang aktif saat test.

### 8.3. Production per RS

- **Write op: dilarang total.** Daftar lengkap larangan ada di
  `memory/operational_rules.md` → "Batasan Write Operation" (sumber tunggal).
  Jangan tulis ulang daftarnya di sini.
- Read-only diperbolehkan (verifikasi bug user report, cek log, SELECT query non-PII).
- **Data pasien real** — masking wajib, lihat `memory/operational_rules.md` → "Penanganan PII".
- Kalau perlu reproduksi bug dari data prod: minta dev copy sanitized subset ke staging.

## 9. Regression checklist per module

> **Versi machine-readable: [`regression_map.yaml`](regression_map.yaml).** Subagent `qa-analyst` membaca file itu untuk memetakan diff MR -> modul terdampak. Kalau menambah dependency baru, tambahkan di **kedua** tempat, atau cukup di YAML dan biarkan tabel di bawah jadi ringkasan bacaan manusia.

Kalau QA test area X, checklist related area yang WAJIB regression retest.

### 9.1. Bed management
- Change di bed status → retest: pre-checkout flow, ICU transfer in/out, admission via IGD, rawat gabung bayi (perinatologi ↔ ranap ibu).
- Related tables: `emr_beds`, `emr_bed_transactions`, `emr_episodes`.
- Related repo: `sirs-odoo-modules/emr_bed`, `kesia-fe` bed management page.

### 9.2. Prescription (peresepan obat)
- Change di prescription → retest: pharmacy dispensing, tarikan BPJS iDRG, config racikan (obat racikan BPJS), voucher depo farmasi, prescription tindakan.
- Related tables: `emr_prescriptions`, `emr_prescription_lines`, `pharmacy_orders`.
- Related repo: `sirs-odoo-modules/emr_prescription`, `sirs-odoo-modules/pharmacy_*`.

### 9.3. Discharge resume + resume medis
- Change di discharge → retest: ICD9 mandatory validation, resume medis endpoint (BE), print PDF, tarikan data lab/rad ke resume, transfer pasien.
- Related tables: `emr_discharge_summaries`, `emr_resume_medis`.

### 9.4. Registration + episode
- Change di registration → retest: sequence register_no (race condition duplicate), rollback rawat inap → rajal, cancel booking, MJKN cancel handling.
- Related tables: `emr_episodes`, `emr_registrations`.
- Known issue: duplicate `register_no` di `emr_episodes` (race condition).

### 9.5. BPJS / iDRG / Casemix
- Change di BPJS module → retest: KRIS info + Total Claim IDRG Casemix, KSO template tindakan medis, penggabungan tagihan IGD+Rawat Inap, cancel BPJS on MJKN, tarif kelas.
- Related tables: `bpjs_claims`, `bpjs_diagnoses`, `bpjs_procedures`.

### 9.6. Satu Sehat integration
- Change di Satu Sehat → retest: encounter role migration, trigger ICD10 update sync, FHIR R4 push (patient/encounter/observation), retry failed sync.
- Related repo: `khanza-connector`.

### 9.7. Reporting / Metabase
- Change di report → retest: SIRS RL 3.6–3.17, dashboard drilldown, tarikan data lintas modul (EMR ↔ billing ↔ pharmacy).

### 9.8. Marketing / Broadcast
- Change di marketing module → retest: template message, contact segmentation, broadcast delivery status.

## 10. Test data & seed convention

### 10.1. Konvensi naming test data

- Pasien test: nama diawali `TEST-<initial>-<incremental>` (mis. `TEST-KB-001`), tanggal lahir `1900-01-01`.
- Dokter test: `dr_test_<initial>`.
- Obat/tindakan test: prefix `[TEST]`.
- Payer test: `TEST-INSURANCE`.

### 10.2. Cara reset data test (via dev, bukan QA sendiri)

- QA **tidak boleh** langsung `DELETE`/`TRUNCATE`.
- Buat rencana + list target row → eskalasi ke @Tech dev untuk eksekusi.
- Alternatif: minta dev buat seed script yang idempotent (di repo `sirs-server-definitions` atau tools/).

### 10.3. Cara verify state data setelah testing

- Pakai `kubectl exec ... psql` dengan SELECT (read-only). Contoh:
  ```bash
  kubectl exec -n <ns> <postgres-pod> -- psql -U <user> -d <db> -c \
    "SELECT id, name, updated_at FROM emr_prescriptions WHERE patient_id = X AND created_at > NOW() - INTERVAL '1 hour';"
  ```
- Untuk verifikasi via UI: catat URL + user role + step yang dipakai.
- Untuk verifikasi via API: capture request + response, attach di test report.

### 10.4. Sanitasi output — jangan paste PII

> Aturan dan format kanonik: `memory/operational_rules.md` → "Penanganan PII".
> Bagian ini hanya menambahkan konteks data test, bukan mendefinisikan ulang formatnya.

- QA sering deal dengan data pasien saat verifikasi. **Jangan paste** ke output/log/report:
  nama pasien, NIK, alamat, no HP, email, diagnosa spesifik.
- Format masking: ikuti `memory/operational_rules.md` (`<PATIENT_123>`, `<NIK_MASKED>`).
  Jangan bikin varian sendiri — `<PATIENT_<id>>` dan `<PATIENT_id_123>` sudah dihapus.
- Diagnosa spesifik → sebut kategori, bukan detail.
