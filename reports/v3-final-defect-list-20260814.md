# Laporan Final Defect & Blocker Kesia v3

- **HEAD**: `1ea94cd` (branch `main` — latest per 14 Agt 2026)
- **Total Defect Open**: 29
- **Prioritas**: 🔴 Kritis (7) | 🟡 Sedang (16) | 🟢 Rendah (6)

---

## 🔴 Defect Kritis (7)

### **Keuangan & Billing**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| K-01 | `/billing` (Kasir) | **Void Invoice `PAID` tanpa refund**. Kasir bisa void invoice lunas, stok obat kembali, tapi uang pasien tidak tercatat dikembalikan. | `BillingPage.tsx:182`<br>`billing.service.ts:144` |
| K-02 | `/billing` (Kasir) | **`payInvoice` tidak memvalidasi status**. Invoice `draft`/`void` dapat dipaksa jadi `paid`. | `billing.service.ts:385` |
| K-03 | `/kasir` (Kasir) | **Refund deposit setelah episode closed**. `refundDeposit` tidak mengecek status episode. | `queue.service.ts:72` |

### **Data & Relasi**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| R-01 | `/rm/merge` (Petugas RM) | **`mergePatient` TIDAK re-point 8 tabel finansial & operasional**. Tagihan, deposit, resep bebas, peminjaman RM, order gizi, antrean BPJS pasien sumber jadi **orphan**. | `registration.service.ts:466` |
| M-05 | `/masterdata/*` | **`resDelete` masterdata tanpa guard referensi FK**. Menghapus dokter/unit/tindakan yang dipakai di episode aktif trigger HTTP 500 error. | `masterdata.service.ts:507` |

### **Keamanan / Autentikasi**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| M-03 | Halaman Lupa Password | **Reset Password bocorkan `devResetToken`** di respons API non-production (staging). | `auth.service.ts:101` |
| M-04 | `/auth/dev-login` | **`dev-login` aktif di staging** & `KESIA_INTERNAL_JWT_SECRET` fallback hardcoded. | `dev-auth.controller.ts:45`<br>`auth.service.ts:70` |

---

## 🟡 Defect Sedang (16)

### **Farmasi & Logistik**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| F-01 | `/farmasi` | `deductFefo` tidak throw error saat stok batch kurang (silent negative stock). | `pharmacy.service.ts:556` |
| F-02 | `/stok/adjust` | `adjustStock` tanpa guard `qtyOnHand >= 0` (stok bisa jadi minus). | `pharmacy.service.ts:544,607` |
| F-03 | `/farmasi/penjualan-bebas` | `voidSale` restore stok tanpa mencatat refund & tanpa guard status lunas. | `pharmacy.service.ts:262` |

### **BPJS & Antrean**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| B-01 | `/bpjs/sep` | `issue` SEP tidak cek episode closed & tidak cek SEP existing (SEP ganda). | `sep.service.ts:91` |
| B-02 | `/bpjs/antrean` | `listBpjsQueue` & `sendBpjsQueue` menyajikan/mengirim episode closed & tanpa guard duplikasi. | `ops.service.ts:51,82` |
| B-03 | `/bpjs/antrean` | `advanceQueueTask` bisa dipanggil pada antrean `served`. | `ops.service.ts:136` |

### **EMR & Klinis**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| D-01 | `/emr` (Dokter) | `confirmObservation` CPPT/SOAP bisa di-approve pada episode closed. | `clinical-observation.service.ts:330` |
| D-02 | `/ranap` (Dokter Ranap) | `recordVisite` tanpa cek `ep.status === 'closed'` & tanpa deduplikasi per hari. | `order.service.ts:231` |
| D-03 | `/emr/konsul` (Dokter) | `respondConsult` bisa menimpa jawaban konsul berulang kali. | `care-plan.service.ts:177` |
| D-04 | `/emr/utd` (UTD) | `createRequest` Bank Darah tidak memvalidasi status episode. | `bloodbank.service.ts:106` |
| O-01 | `/ok` (Petugas OK) | `setSurgeryStatus` & `rescheduleSurgery` mengabaikan state machine & status episode. | `ops.service.ts:877,908` |
| K-04 | `/pendaftaran` | `cancelEpisode` tidak membatalkan `food_orders` & `invoices` terkait. | `registration.service.ts:920` |

### **Masterdata & RM**

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| R-02 | `/rm/tracer` | `setArm` terima status string bebas tanpa enum. | `ops.service.ts:462` |
| R-03 | `/rm/retensi` | `markArmInactive` tanpa cek status episode (berkas pasien aktif bisa diretensi). | `ops.service.ts:432` |
| M-01 | `/masterdata/unit` | `createUnit` tanpa unique check kode unit (poli duplikat). | `masterdata.service.ts:188` |
| M-06 | `/masterdata/schedules` | `deleteSchedule` tanpa cek episode/antrean aktif yang menggunakan jadwal tersebut. | `masterdata.service.ts:320` |

---

## 🟢 Defect Rendah (6)

| # | Menu UI | Defect | File Code |
|---|---|---|---|
| U-01 | `/gizi` | `setFoodOrderStatus` terima string bebas; `recordFoodDelivery` tanpa guard re-delivery. | `order.service.ts:830,841` |
| C-01 | `/bpjs/casemix` | `saveCasemix` tarif placeholder hardcode `1500000` & `INACBG-UNSPEC`. | `ops.service.ts:220` |
| M-07 | `/masterdata/employee` | `updateEmployee` unit via `unitIds` tidak hapus unit primer lama di tabel `employees` (hanya di pivot `employeeUnits`). | `masterdata.service.ts:251` |
| M-08 | `/form-builder` | `getEffectiveDef` form-engine tidak resolve versi semver, hanya `orderBy(createdAt)` (versi lama bisa jadi efektif). | `form-builder.service.ts:200` |
| K-05 | `/kasir/deposit` | `refundDeposit` tanpa idempotency token, rentan race-condition. | `queue.service.ts:72` |
| D-05 | `/emr` (Dokter) | `recordVisite` tanpa deduplikasi (bisa catat >1 visite per dokter per hari). | `order.service.ts:231` |
