# 📋 AUDIT DEFECT & BLOCKER KESIA V3 — LAPORAN LENGKAP PER MODUL & ROLE
**HEAD**: `11a0d9a` (main) · **Tanggal**: 2026-08-20 · **Repo**: `E:\WORK KESIA\Project\kesiaV3`
**Total Temuan OPEN: 42 defect** — 4 CRITICAL, 21 HIGH, 12 MEDIUM, 5 LOW
*Catatan: 18 item FB19 + batch billing/Odoo sebelumnya SUDAH FIXED dan tidak dimasukkan di sini.*

---

# MODUL A — PENDAFTARAN & ANTRIAN

## A1. Role: Petugas Pendaftaran

### Menu `/registrasi/pasien` (Daftar Kunjungan Rajal)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-002 | MED | Ganti penjamin saat episode `INPROGRESS` tanpa void order lama | Login REG → buka kunjungan aktif → edit → ganti penjamin → simpan. Order resep/lab lama tetap tarif penjamin lama; invoice ditarik pakai penjamin baru → selisih klaim | `registration.service.ts:973` | Blok edit insurerId jika ada order/invoice aktif |
| NEW-003 | MED | Wizard "Lanjut" skip validasi field wajib | Buka form daftar → isi Nama saja → klik "Lanjut" → pindah step tanpa Penjamin/Jadwal → error muncul belakangan di step akhir | `RegistrationFormPage.tsx:559` | `await form.validateFields()` per-step |

### Menu `/registrasi/verifikasi-online` (Verifikasi Pendaftaran Online)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-001 | **HIGH** | Endpoint call butuh permission perawat | Login REG → buka Verifikasi Online → pilih pasien → klik "Verifikasi & Aktifkan" → **HTTP 403 Forbidden** | `clinical.controller.ts:359` | Tambah `'verifikasi/online:verify'` ke decorator |

### Menu `/kiosk` (Anjungan Mandiri)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-035 | MED | Endpoint check-in WRITE diproteksi permission view-only | Login akun read-only (mis. petugas laporan) → akses kiosk → klik Check-in → status antrean BPJS berubah `sent→checkedin` padahal cuma punya izin view | `kiosk.controller.ts:17` | Permission khusus `kiosk:checkin` |

---

# MODUL B — KASIR / BILLING / KEUANGAN

## B1. Role: Kasir / Billing

### Menu `/kasir/billing` (Billing & Invoice)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-005 | **HIGH** | `cancelInvoice` tidak hapus alokasi coverage klaim | Buat invoice dengan cover penjamin → Batalkan invoice → buka menu Klaim Perusahaan → nilai klaim invoice void MASIH terhitung | `billing.service.ts:160-190` | Delete `invoiceCoverages` saat cancel |
| NEW-006 | **HIGH** | Query cek order lintas-tenant tanpa siteId | (Backend) Saga/check order memanggil select prescriptions/supportOrders by ID tanpa filter site → tebakan UUID bisa baca data RS lain | `billing.service.ts:653-654` | Tambah `eq(siteId)` |

### Menu `/kasir/corporate-claims` (Tagihan Perusahaan)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-004 | **HIGH** | Ringkasan klaim perusahaan hitung 0 | Buat invoice draft dengan coverage COMPANY → buka Tagihan Perusahaan → jumlah klaim tampil **0** walau ada baris coverage | `corporate-claim.service.ts:45` | `count(c.id) filter (where i.id is not null)` |

### Menu `/kasir/deposit` (Deposit Pasien)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-007 | MED | Modal bayar deposit: nama payor tidak reset | Bayar deposit Pasien A → tutup modal → bayar deposit Pasien B → nama payor masih "Pasien A" | `DepositListPage.tsx:96` | `form.setFieldsValue` via useEffect |

---

# MODUL C — FARMASI

## C1. Role: Apoteker

### Menu `/farmasi/penjualan-bebas` (OTC)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-014 | **HIGH** | Void sale tidak restore stok FEFO | Jual OTC 10 tablet → Void penjualan → cek stok: ledger naik tapi `item_stocks` TIDAK naik → kasir berikutnya lihat stok salah | `pharmacy.service.ts:262-281` | Increment `item_stocks` + restore batch |
| NEW-017 | LOW | Dropdown obat tak reset pencarian | Cari "paracetamol" → tambah ke keranjang → cari obat lain → term lama masih nempel | `PenjualanBebasPage.tsx:108` | Reset `term` on change |

### Menu `/farmasi/verifikasi-resep` (Telaah Resep)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-015 | **HIGH** | Resep flagged tetap di antrean verifikasi | Dokter kirim resep → Apoteker flag (tolak telaah) → dokter belum revisi → apoteker lain buka antrean → resep flagged TETAP muncul tanpa tanda → bisa diloloskan | `VerifikasiResepPage.tsx:36` | Filter `reviewResult !== 'flagged'` + badge visual |

### Menu `/farmasi/stok` (Stok Obat)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-016 | MED | Param `expiringDays` tanpa guard NaN | Buka Stok → filter "Kadaluarsa ≤ abc" → server balas 500 Internal Server Error | `clinical.controller.ts:504,521` | Guard isNaN |

---

# MODUL D — LABORATORIUM

## D1. Role: Petugas Laboratorium

### Menu `/penunjang/lab` (Worklist Lab)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-018 | **HIGH** | Ambil spesimen order verified | Hasil lab sudah diverifikasi DPJP → petugas klik "Collect" spesimen lagi → LOLOS padahal seharusnya ditolak | `specimen.service.ts:40` | Guard status ordered/in_progress |

### Integrasi LIS (background)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-019 | **HIGH** | HL7 multi-OBR saling timpa orderId | Mesin analyzer kirim hasil 2 panel dalam 1 pesan HL7 → OBX panel kedua menimpa orderId panel pertama → hasil analyte tercampur antar-panel | `lis.service.ts:22` | Grouping OBX per-OBR |

---

# MODUL E — RADIOLOGI & IMAGING

## E1. Role: Petugas Radiologi

### Menu `/penunjang/radiologi` (Worklist Rad)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-020 | 🔴 **CRITICAL** | Upload DICOM cross-patient | Radiografer upload citra dari modalitas → pilih order pasien A → payload bawa patientId pasien B → SISTEM TERIMA → citra B nempel di rekam medis A | `imaging.service.ts:27-48` | Cocokkan `order.patientId === input.patientId` |
| NEW-021 | MED | Upload tanpa orderId lewati guard cancelled | Upload citra langsung by episodeId (tanpa orderId) pada episode yang ordernya dibatalkan → LOLOS | `imaging.service.ts:33-36` | Cek status episode juga |

---

# MODUL F — CATHLAB & PENUNJANG LAIN

## F1. Role: Petugas Cathlab

### Menu `/penunjang/cathlab` (Laporan Cathlab)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-022 | **HIGH** | Laporan tersimpan tanwa operator | Isi laporan cathlab tanpa mengisi operator → SIMPAN LOLOS → laporan final tanpa jejak DPJP pelaksana | `order.service.ts:728-782` | Wajibkan `operatorId` di DTO |

---

# MODUL G — BPJS & CASEMIX

## G1. Role: Petugas BPJS

### Menu `/bpjs/sep` (Surat Eligibilitas Peserta)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-037 | 🔴 **CRITICAL** | Terbitkan SEP non-idempoten (SEP ganda) | Petugas klik "Terbitkan" 2x cepat ATAU retry setelah timeout ATAU buka 2 tab → backend `issue()` TIDAK cek SEP existing → **2 SEP terbit di VClaim untuk 1 kunjungan** → klaim BPJS ditolak duplikasi | `sep.service.ts:91-160` | Cek SEP issued existing dulu / unique partial index |
| NEW-038 | **HIGH** | tglSep pakai UTC bukan WIB | Daftarkan pasien jam 01:00 WIB (18:00 UTC hari sebelumnya) → tglSep terisi tanggal kemarin → VClaim tolak (tanggal layanan beda) | `sep.service.ts:123` | Helper tanggal lokal WIB |

## G2. Role: Petugas BPJS / Casemix

### Menu `/bpjs/casemix` (Klaim & Grouping)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-023 | 🔴 **CRITICAL** | Fallback tarif CBG hardcoded Rp 1.5jt | WS Grouper BPJS timeout/null saat saveCasemix → sistem diam-diam pakai tarif Rp 1.500.000 → klaim masif salah nominal | `ops.service.ts:223` | Throw error, jangan fallback angka |

---

# MODUL H — REKAM MEDIS

## H1. Role: Rekam Medis (Koder)

### Menu `/rm/coding` (Koding ICD)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-024 | **HIGH** | Edit ICD di episode closed/sudah ditagih | Episode sudah closed + invoice paid + klaim terkirim → koder ubah ICD primary → data klaim BPJS yang sudah diajukan tidak sinkron dengan RM | `registration.service.ts:893` | Guard status closed/cancelled |

---

# MODUL I — KAMAR OPERASI

## I1. Role: Petugas OK

### Menu `/ok/jadwal` (Jadwal Operasi)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-025 | **HIGH** | Status operasi tanpa validasi enum | API PATCH status dengan string `"selesai kok"` → LOLOS → state machine jadwal OK rusak, worklist OK tampil anomali | `ops.schemas.ts:115-117`, `ops.controller.ts:86` | Zod enum whitelist |

---

# MODUL J — MCU

## J1. Role: Petugas MCU

### Menu `/mcu/cetak` (Cetak Sertifikat)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-026 | LOW | recordedAt null → TypeError | Buka cetak sertifikat MCU yang recordedAt-nya kosong → halaman crash (blank) | `CetakMcuPage.tsx:126` | Optional chaining |

---

# MODUL K — RADIOTERAPI / ONKOLOGI

## K1. Role: Dokter Onkologi Radiasi, Fisikawan Medis, Radioterapis (RTT)

### Menu `/rt/courses` & `/rt/deliver` (Course & Deliver Fraksi)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-034 | **HIGH** | Fraksi DONE bisa deliver ulang | RTT deliver fraksi #3 → klik deliver lagi (double-click/retry) → fraksi sama tercatat DONE 2x → total fraksi melebihi plan, OTT & progres salah | `rt.courses.service.ts:257-283` | Guard `frac.status === 'DONE'` |
| NEW-027 | **HIGH** | Eksekusi tanpa approval dose plan | Fisikawan belum approve plan → RTT coba deliver → (untuk course non-fraksi-1) LOLOS karena gate check hanya untuk fraction #1 | `order.service.ts:650-710` | Gate semua fraksi selama plan belum approved |

---

# MODUL L — EMR KLINIS

## L1. Role: Perawat

### Menu `/emr/worklist` (Workspace Perawat)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-008 | **HIGH** | Confirm TTV di episode closed | Pasien pulang (closed) → perawat buka riwayat → konfirmasi TTV tambahan → LOLOS → data klinis berubah pasca-pulang | `clinical-observation.service.ts:330` | Guard episode open |
| NEW-009 | **HIGH** | nurse-done ditolak walau TTV ada | Perawat isi TTV via form Asesmen Awal (bukan VITAL_SIGN_DEF) → klik "Serah ke Dokter" → ditolak "TTV belum diisi" padahal datanya ada | `NurseWorkspacePage.tsx:99` | Flexibilkan deteksi vital-sign |

### Menu `/emr/igd` (Form IGD)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-010 | MED | Operan jaga input manual | Buka form Operan Jaga → kolom perawat penyerah/penerima = text bebas → ketik sembarang nama → lolos tanpa validasi master pegawai | `igdForms.ts:124` | Ubah jadi select enumSource staff |

## L2. Role: Dokter

### Menu `/dokter/konsul` (Konsul Internal)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-011 | **HIGH** | Jawaban konsul bisa tertimpa | DPJP jawab konsul → konsulen buka lagi & submit jawaban kedua → jawaban pertama HILANG tanpa audit trail | `care-plan.service.ts:182` | Tolak jika sudah responded |

### Menu `/emr/worklist` (Workspace Dokter)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-012 | **HIGH** | Tombol Selesai terkunci stale state | Dokter isi rencana tindak lanjut → tombol "Selesai Pemeriksaan" TETAP disabled sampai refresh manual | `DoctorWorkspacePage.tsx:88` | Invalidate query care-plans |
| NEW-013 | LOW | Validasi iter tanpa highlight field | Centang resep Iterasi → kosongkan iterValidUntil → submit → error generik, field merah tidak muncul | `OrderSection.tsx:185` | Rules kondisional Form.Item |

---

# MODUL M — MASTERDATA & ADMINISTRATOR

## M1. Role: Administrator

### Menu `/master/jadwal-dokter` (Jadwal Dokter)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-041 | MED | Hard-delete jadwal tanpa cek referensi | Admin hapus jadwal dokter yang cuti → booking/kunjungan yang merujuk jadwal itu jadi dangling (kolom doctorScheduleId TANPA FK constraint) → antrean kehilangan konteks | `masterdata.service.ts:320-326`, schema `clinical.ts:151` | Soft-delete / blok jika direferensikan |

### Menu `/master/masterdata` (res CRUD generik: beds/rooms/actions dll)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-042 | MED | Hapus kamar/bed yang sedang okupansi | Admin hapus kamar via res CRUD → kamar sedang dihuni pasien INBED → TERHAPUS → admisi pasien dangling | `masterdata.service.ts:513-521` | Blok delete jika ada episode aktif |
| NEW-039 | **HIGH** | Hapus tarif tindakan → charge Rp 0 | Admin hapus tarif action X → petugas poli tarik charge tindakan X ke invoice → harga resolve jadi Rp 0 → pendapatan bocor diam-diam | `masterdata.service.ts:390-391` → efek `:569` | Soft-delete / blok jika dipakai unit aktif |
| NEW-033 | MED | Harga jual 0 tanpa konfirmasi | Input harga item 0 → tersimpan diam-diam → billing tarik Rp 0 untuk item itu | `masterdata.service.ts:410` | Warning/konfirmasi eksplisit |

### Menu Keuangan — Odoo Sync (background saga)
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-028 | 🔴 **CRITICAL** | Saga Odoo SELECT tanpa siteId | (Backend) Saga processor baca invoices/lines/coverages/patients by ID tanpa filter tenant → potensi cross-tenant read | `post-billing-to-odoo.saga.ts:26-38` | Wajibkan eq(siteId) semua query |
| NEW-029 | MED | Income account match gagal utk categ null | Item tanpa kategori di-post ke Odoo → categId null diubah `''` → rule income_mapping spesifik-penjamin tidak match → masuk akun generic | `post-billing-to-odoo.saga.ts:180` | Perlakukan null ≠ '' saat scoring |
| NEW-030 | **HIGH** | Inventory sync menggantung | Produk baru tanpa kategori persediaan → trigger stock.quant sync → gagal diam-diam menggantung | `post-inventory-to-odoo.saga.ts:45` | Validasi kelengkapan kategori pre-sync |
| NEW-036 | LOW | Amount NaN ke XML-RPC | Payload saga korup (amount string rusak) → Number() jadi NaN → dikirim ke Odoo → jurnal gagal diam-diam | `odoo12.adapter.ts:98`, `odoo18.adapter.ts:179,244` | Guard Number.isFinite |

### Auth & RBAC
| ID | SEV | Defect | Repro Flow | Lokasi | Fix |
|----|-----|--------|-----------|--------|-----|
| NEW-040 | MED | Login tanpa rate-limit/lockout | Script brute-force POST /auth/login 1000x password berbeda → tidak ada blokir/throttle sama sekali | `auth.controller.ts:23-25`, auth.service | Throttle + lockout counter |
| NEW-031 | MED | devResetToken reusable | (Non-prod) Request reset token → pakai token → pakai LAGI → masih valid | `auth.service.ts:103` | Null-kan setelah pemakaian |
| NEW-032 | LOW | ROLE_PRIORITY kurang role baru | User multi-role bpjs/ok/rm/upm/mcu login → landing page salah (fallback default) | `rbac.service.ts:39-47` | Lengkapi array |

---

# RINGKASAN EKSEKUTIF

## Distribusi Severity
| Severity | Jumlah | Item |
|----------|--------|------|
| 🔴 CRITICAL | **4** | DICOM cross-patient (E1), SEP ganda (G1), Casemix Rp1.5jt (G2), Saga Odoo no-siteId (M1) |
| 🟠 HIGH | **21** | NEW-001, 004, 005, 006, 008, 009, 011, 012, 014, 015, 018, 019, 022, 024, 025, 027, 030, 034, 038, 039 |
| 🟡 MEDIUM | **12** | NEW-002, 003, 007, 010, 016, 021, 031, 033, 035, 040, 041, 042 |
| ⚪ LOW | **5** | NEW-013, 017, 026, 032, 036 |

## Top 4 Prioritas Patch (CRITICAL)
1. **NEW-020** DICOM cross-patient — risiko keselamatan pasien & hukum.
2. **NEW-037** SEP ganda — klaim BPJS massal ditolak.
3. **NEW-023** Casemix fallback Rp 1,5jt — potensi fraud audit klaim.
4. **NEW-028** Saga Odoo tanpa siteId — integritas multi-tenant.

## Modul Paling Rapuh
1. **BPJS/Casemix** (3 temuan, 2 CRITICAL) — alur klaim rawan salah uang.
2. **Farmasi** (4 temuan) — stok & verifikasi resep.
3. **Odoo Sync** (4 temuan) — posting keuangan eksternal.
4. **EMR Perawat/Dokter** (5 temuan) — guard status episode lemah di banyak titik.

---
*Laporan ini dihasilkan dari statis code review HEAD `11a0d9a` oleh agent QA Salsabila. Semua lokasi file:line terverifikasi langsung dari kode sumber.*
