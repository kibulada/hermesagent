# Output Discipline

Dokumen ini adalah sumber otoritatif untuk **format output** agent ke user. Pair dengan `../AGENTS.md` §7 (4 kontrak: Output Gate, ZERO Progress, Failure Handling, Discipline Pointer).

## §-1 Scope (BACA DULU)

Aturan di dokumen ini berlaku untuk **output ke Discord** — tempat Kibul hanya ingin melihat hasil akhir, bukan proses.

**Tidak berlaku di CLI / Claude Code.** Di sana tool call memang tampil ke user secara desain, dan `user_profile.md` justru meminta *"tampilkan command / curl yang digunakan agar bisa diverifikasi ulang"*. Menyembunyikan command di CLI menghilangkan kemampuan Kibul memverifikasi ulang hasil kerja agent — itu kebalikan dari tujuan aturan ini.

Ringkasnya: **Discord → sembunyikan proses, tampilkan hasil. CLI → tampilkan command, tetap ringkas.**

## §0 Kontrak Output Discord (ATURAN OUTPUT) — HARD RULE

Kontrak ini paling tinggi **untuk output Discord**; meng-override allowance apa pun di dokumen lain pada konteks tersebut. Berasal dari instruksi eksplisit owner (Kibul):

1.  Boleh menggunakan tool sebanyak yang dibutuhkan untuk investigasi (baca file, jalankan terminal, grep, dsb).
2.  **JANGAN PERNAH** menampilkan, menuliskan, atau menyebutkan proses investigasi ke user — termasuk:
    - nama file yang sedang dibaca
    - command terminal yang dijalankan
    - progress/iterasi ("iteration X/150", "waiting for provider response", dsb)
    - status "Reading...", "Searching files for...", "terminal", "(×N)"
3.  Semua proses investigasi adalah **INTERNAL**. User hanya boleh melihat **HASIL AKHIR**.
4.  Setelah investigasi selesai, kirim **SATU output final** yang mengikuti format (T1/T2/T3 §2), **TANPA teks tambahan sebelum atau sesudahnya**.
5.  Jangan menjelaskan langkah-langkah yang diambil, jangan meminta maaf soal proses, jangan menambahkan komentar meta ("berikut hasil investigasi saya"). Langsung output sesuai format.

## §1 Anti-Frasa (HARD RULE)

**DILARANG** muncul di output Discord/channel user (kecuali di dalam tag `<system-reminder>` atau file `reports/<id>-notes.md`):

| Kategori | Frasa Terlarang |
|----------|-----------------|
| Narasi coba-coba | "Coba:", "Pakai:", "Gunakan:", "Mungkin bisa pakai", "Solusi:", "Strategi:" |
| Narasi tool | "Tool X gagal", "Token invalid", "Truncated", "Running code #", "Output di atas", "Berikut hasilnya" |
| Narasi kegagalan | "Tapi X nggak bisa", "Tapi Y juga gagal", "Mungkin Z", "Saya sudah coba" |
| Narasi self-correction | "Saya kira", "Ternyata", "Maaf", "Saya kurang yakin", "Saya sudah cukup bukti" |
| Narasi ref/branch | "Ref develop", "Branch sudah merged", "Branch sudah merged/deleted", "Saya akan clone", "Cek lewat X" |
| Narasi proses | "Step 1", "Step 2", "Lalu saya", "Setelah itu", "Sekarang saya" |
| Narasi status internal | "Investigasi sedang berjalan", "Saya masih mencari", "Tunggu sebentar" |
| **Tool prefix (HARD)** | `⚙️`, `📚`, `📄`, `💻`, `🐍`, `📖`, `🔎` — emoji prefix dari jejak tool-call internal handler (MCP, file read, grep, terminal, python exec, skill read, URL fetch). **DILARANG** masuk output user. Simpan ke `reports/<id>-notes.md` jika perlu audit. |
| **Handler trace (HARD)** | "Token invalid", "Pakai MCP", "Project path salah", "Cari project", "Cari project FE", "Pakai offset", "Tapi X nggak bisa", "Coba X", "Cek lewat X", "Token mati", "MCP bisa", "Tapi ini", "Tapi Y", "Tapi get_merge_request", "Lihat commit", "Search commits", "Redirect ke login", "Pakai web_extract", "Cek apa yang sudah kelihatan", "Lebih baik", "Cek apakah ada", "Strategi final", "Cek lewat read_file", "Branch sudah merged/deleted", "Diff MR hanya", "0 perubahan terkait" — semua narasi yang menjelaskan langkah handler/orchestrator. |
| **Handler echo command (HARD)** | `python -c "`, `python -m pip`, `pip install`, `pwd &&`, `cd "D:/`, `cd "`, `&& echo`, `&& ls`, `&& ls -la`, `ls sourcecode/`, `ls ke...` — substring command terminal yang echo ke output. **DILARANG**. |
| **Narasi investigasi (HARD)** | `Kode L<num> cocok dengan klaim sheet`, `Model confirmed:`, `L<num> confirmed:`, `Cek destroy() site`, `Cek getActionPrice`, `getActionPrice Panggil`, `Bug #<n> fix valid`, `Bug #<n> fix assume`, `Sheet clue:`, `Cek ActionPriceService`, `Setelah paranoid=true`, `lanjut cek`, `lanjut cek helper`, `cek helper & model`, `3 destroy() sites confirmed`, `Bukti: diff MR hanya`, `0 perubahan terkait`, `Cek L<num>`, `Model confirmed` — semua kalimat progress/progress-check/verify-step. **DILARANG**. |
| **ZERO progress (HARD)** | `⏳ Investigasi…`, `Reading...`, `Searching files for...`, `terminal`, `(×N)`, `iteration N/`, `waiting for provider response`, `berikut hasil investigasi saya`, `oke saya cek dulu`, `sudah selesai`, `tunggu sebentar`, `saya cek dulu` — status tool, progress counter, polling status, atau teks transisi apa pun sebelum output final. **DILARANG** (lihat §0 & §6.2). |

**Yang BOLEH** muncul di output user:
- Fakta, bukti, path:line, verdict, blocker ringkas.
- Tag `<system-reminder>` untuk warning internal (mis. tool unavailable).
- Emoji fungsional (✅, ⚠️, ❌) sesuai konvensi QA. **⏳ HANYA** sebagai label status di pesan final (mis. "Status: ⏳"), bukan pesan progress terpisah.

## §2 Output Templates (Standar)

### T1 — Cek Tiket (default query)

```
**PP#<id> — <judul singkat>**
- Hipotesis: <1 kalimat>
- Bukti: <path:line atau log singkat>
- Verdict: <PASS|FAIL|BLOCKED|DEPENDENCY> — <1 kalimat>
```

Max 8 baris. Contoh real-case lihat §4.

### T2 — Code Review MR

```
**MR**: !<id> — <judul> (<branch> → <target>)
---
**Temuan:**
1. [✅/⚠️/❌] — <deskripsi>
   File: `path/to/file.js:<line>`
2. ...
---
**Verdict**: <LULUS|PERLU PERBAIKAN|BLOCKER>
**Catatan**: <1 kalimat untuk developer>
```

### T3 — Laporan Bug / Repro

```
**Bug**: PP#<id> — <judul>
**Severity**: <Critical|Major|Minor>
**Repro**: <langkah 1-3, maks 4 baris>
**Ekspektasi**: <apa yang seharusnya>
**Aktual**: <apa yang terjadi>
**Bukti**: <path:line, log, screenshot ref>
```

## §3 Noise Budget

| Tipe Query | Baris Maks User-Facing | Catatan |
|------------|----------------------|---------|
| Instruksi umum (bukan tiket) | 0 pesan sementara, 1 pesan final | §0; tanpa ⏳/status tool/teks transisi |
| Cek tiket | 8 | Default; lebih panjang hanya kalau user bilang "detail" |
| Code review MR | 25 | T2 template |
| Laporan bug / repro | 30 | T3 template |
| Status polling | 1 | Cuma "Status: <state>" |
| Pertanyaan status tiket | 5 | Boleh singkat dengan 1 referensi |

**Aturan keras**: kalau output > budget → agent WAJIB trim sebelum emit. Investigasi yang lebih panjang ditulis ke `reports/<id>-notes.md`.

## §4 Contoh Real-Case: PP#7486 (Inspect AllComponents.js)

### ❌ BAD (output asli — JANGAN ditiru)

```
⏳ Working — 2 min — iteration 22/150, waiting for provider response (streaming)
Token invalid. Pakai MCP get_file saja. Ref develop, tapi size 128K truncated di 97K. 
Pakai offset: read_file punya offset/limit. Tapi ini file GitLab, bukan lokal. 
Pakai mcp__gitlab__get_file dengan ref spesifik, lalu baca kelanjutannya via search.

Lebih baik: cari fungsi spesifik via MCP search_commits? Tidak bisa grep isi. 
Pakai mcp__gitlab__get_file lalu mcp__gitlab__get_commit_diff mencari file di commit lain. 
Atau clone repo.
Token mati. Tapi MCP bisa (lihat commit). MCP GitLab server punya scope sendiri. 
Strategi: pakai MCP get_file ref develop dan baca sebagian (sudah dapat 97KB). 
Cari loadInpatientBilling dll di output yg sudah ada. Itu file 128K, output truncated 97K. 
Saya lihat getFileContent truncated. Pakai web_extract ke GitLab blob page (HTML)?
📄 Reading https://gitlab.com/kesiaid/kesia-fe/-...
💻 terminal
curl -sL "https://gitlab.com/kesiaid/...
curl -sLI "https://gitlab.com/kesiaid...
⚙️ mcpgitlabsearch_commits: "AllComponents loadInpatientBilling" 
Redirect ke login (private). Pakai MCP get_file dengan byte range/partial? Tidak bisa. 
Tapi get_merge_request kasih diffs lengkap per file. Liat MR 7301 punya 3 file diff. 
Lihat commit lainnya untuk AllComponents history:
Branch sudah merged/deleted. Cek lewat read_file (tool baca file lokal)? Itu nggak ada. 
Strategi final: pakai mcp__gitlab__compare_refs untuk diff branch feature/7486-develop 
vs develop di file AllComponents.js — dapet diff, bukan full. Tapi utk verifikasi 
source loadInpatientBilling kita butuh full.

Coba: mcp__gitlab__get_file di ref develop (sudah dapat 97K). File 128K. 
Yang ke-trim ekor, biasanya tempat loadInpatientBilling dkk. Cek apa yang sudah kelihatan:
⚙️ mcpgitlabget_file: "src/components/billing/AllComponents.js"
🐍 Running code # Simulasikan: dari output get_file r...
🐍 Running code # Cek file AllBillingProceedForm.js (...
⚙️ mcpgitlabsearch_commits: "loadErBilling" 
Cari cara MCP server bisa expose dataEr/dataOutpatient source. 
Cek apakah ada MR/commit lain yg nyentuh AllComponents.js dan reveal assignment.
Search commits hanya judul, tidak bisa grep. Cek MR lain yg nyentuh AllComponents.
⚙️ mcpgitlabsearch_commits: "dataEr dataOutpatient"
⚙️ mcpgitlablist_merge_requests...
⚙️ mcpgitlablist_merge_requests...
⚙️ mcpgitlablist_commits... 
Saya sudah punya cukup bukti. Diff MR 7301 jelas. 
Tapi pertanyaan user spesifik: untuk invoice RANAP, tanggal masuk RS sudah ngambil 
dari unit asal (IGD/rajal) belum?
```

**Kenapa bad**:
- 50+ baris proses, bukan jawaban.
- Frasa terlarang: "Coba:", "Pakai:", "Tapi X nggak bisa", "Strategi:", "Token invalid", "Truncated", "Saya sudah cukup bukti", "Saya lihat", "Saya sudah punya".
- Tool call log bocor ke user.
- Tidak ada verdict final terstruktur.
- Loop retry 5+ tanpa progress.

### ✅ GOOD (output target — template T1)

```
**PP#7486 — Invoice RANAP, tanggal masuk dari unit asal**
- Hipotesis: Belum ter-take dari unit asal (IGD/rajal); AllComponents.js lihat baris X-Y assign hardcoded `dataInpatient`.
- Bukti: `kesia-fe/src/components/billing/AllComponents.js:312` (assignment `dataEr` & `dataOutpatient` tidak dipakai di komponen invoice RANAP).
- Verdict: **FAIL** — perlu wiring `dataUnitAsal` ke komponen invoice rawat inap.

Eskalasi: mohon developer cross-check `AllBillingProceedForm.js` apakah juga ter-impact.
```

**Kenapa good**:
- 8 baris, sesuai budget T1.
- Struktur Hipotesis → Bukti → Verdict.
- Tidak ada narasi proses, tidak ada tool log.
- Hanya 1 eskalasi spesifik (1 saran) sesuai §7.2 failure handling.

## §5 Checklist Sebelum Emit Output

Sebelum kirim respon ke user, agent **wajib** self-check:

1. [ ] Apakah ada frasa terlarang (§1) di output? → trim/rewrite.
2. [ ] Apakah ada tool-call reasoning bocor? → hapus.
3. [ ] Apakah ada "Coba X. Tapi X gagal. Coba Y..." loop? → pilih SATU fallback, tulis blocker ringkas.
4. [ ] Apakah baris output > noise budget (§3)? → trim ke max budget, sisanya ke `reports/<id>-notes.md`.
5. [ ] Apakah ada `<system-reminder>` bocor? → pastikan tag tertutup rapi.
6. [ ] Apakah ada verdict final? → kalau tidak, emit blocker spesifik.
7. [ ] Apakah ada prefix tool (`⚙️`/`📚`/`📄`/`💻`/`🐍`/`📖`/`🔎`) atau narasi handler (Token invalid, Ref develop, Branch sudah merged, Pakai MCP, dst)? → **strip sebelum emit**; pindahkan log ke `reports/<id>-notes.md` jika perlu audit.
8. [ ] Scan output untuk substring: `python -c|pip install|pwd &&|cd "D:/|&& echo|&& ls|Kode L|cocok dengan klaim sheet|Cek destroy|Cek getActionPrice|Model confirmed|L<num> confirmed|Bug #<n> fix|Sheet clue|Setelah paranoid`. Strip semua → log audit ke `reports/<id>-notes.md`.

Kalau ada 1 saja gagal → **JANGAN emit**, fix dulu.

## §6 Handler/Trace Discipline (HARD RULE)

**Definisi**: emoji tool-prefix (`⚙️`, `📚`, `📄`, `💻`, `🐍`) + narasi handler ("Token invalid", "Ref develop", "Pakai MCP", dst) adalah **jejak internal handler/orchestrator** — BUKAN output user-facing.

**Aturan emit**:
1. Handler **wajib strip** semua prefix tool + narasi handler sebelum emit ke channel user (Discord).
2. Output user-facing **hanya**: fakta, bukti (`path:line`), verdict, blocker ringkas, emoji fungsional (`✅`, `⚠️`, `❌`).
3. **ZERO progress** (lihat §0 & §6.2): dilarang emit `⏳ Investigasi…`, status tool, atau teks transisi apa pun sebelum output final.
4. Investigasi sepanjang apa pun → **tetap diam** sampai hasil final siap; narasi ditahan internal, audit log → `reports/<id>-notes.md`.
5. Loop retry/coba-coba → **pilih SATU** fallback silent, tulis blocker ringkas. Dilarang emit narasi "Tapi X gagal, coba Y, Z…".
6. Audit log (tool calls, error raw, partial diff) → tulis ke `reports/<id>-notes.md`, **JANGAN** emit ke channel.

**Contoh emisi benar vs salah**:

| ❌ Salah (handler trace bocor) | ✅ Benar (user-facing only) |
|-------------------------------|----------------------------|
| `⚙️ mcpgitlabget_merge_request...` | (di-strip; log ke notes) |
| `Project path salah. Cari project FE.` | (di-strip; emit hanya hasil akhir) |
| `Branch sudah merged/deleted. Ambil diff langsung dari MR.` | (di-strip; emit hanya bukti path:line) |
| `Token invalid. Pakai MCP get_file saja.` | (di-strip; emit blocker: "Token API invalid, mohon rotate") |
| `⏳ Investigasi…` / `Reading...` / `(×N)` / `iteration 3/150` | (di-strip total; ZERO pesan sementara, langsung output final) |

**Self-check**: sebelum emit, scan output untuk substring `⚙️`/`📚`/`📄`/`💻`/`🐍`/`📖`/`🔎`, kata "Token"/"Ref"/"Pakai MCP"/"Cari project", atau `⏳ Investigasi…`/`Reading...`/`(×N)`/`iteration`. Kalau ketemu → strip.

### §6.1 Hard Filter Contract (Agent Layer)

Karena handler upstream inject prefix + echo command sebelum agent emit final, agent **wajib** melakukan hard filter sebagai **lapis terakhir** sebelum output sampai ke user.

**Pattern blacklist (gabungan)**:
```
[⚙️📚📄💻🐍📖🔎] | python -c|python -m pip|pip install|pwd &&|cd "D:/|&& echo|&& ls
| Token invalid|Ref develop|Branch sudah merged|Pakai MCP|Project path salah
| Cari project|Coba X|Kode L<num>|Cocok dengan klaim sheet|Model confirmed
| L<num> confirmed|Cek destroy|Cek getActionPrice|getActionPrice Panggil
| Bug #<n> fix|Sheet clue|Setelah paranoid| lanjut cek| cek helper
| ⏳ Investigasi…|Reading...|Searching files for...|terminal|(×N)|iteration
| waiting for provider response|berikut hasil investigasi|oke saya cek dulu
```

**Aturan**:
1. Scan final output string untuk semua pattern di blacklist.
2. Match = hapus baris/kalimat tersebut. Jangan rewrite, langsung drop.
3. Kalau baris yang di-drop berisi informasi penting untuk user → pindahkan ke `reports/<id>-notes.md`, **emit** hanya ringkasan/skip.
4. Kalau 1 pattern pun lolos → **JANGAN emit**, fix dulu.

**Catatan limitasi**: filter ini hanya efektif untuk text yang di-emit oleh **agent**. Prefix/echo yang di-inject **setelah** agent emit (handler downstream) tidak bisa di-strip oleh agent. Itu eskalasi architectural, bukan tanggung jawab agent layer.

### §6.2 ZERO Progress Contract (Agent Layer)

Sinkron dengan `../AGENTS.md` §7.1 dan §0.

1. **TIDAK BOLEH** emit output sementara apa pun: `⏳ Investigasi…`, "Reading...", "Searching files for...", "terminal", `(×N)`, "iteration", polling status, teks transisi, preamble, postamble.
2. Semua narasi investigasi (tool call, retry, fallback, failure path, nama file dibaca) ditahan **internal** sampai hasil final siap. Audit log → `reports/<id>-notes.md`.
3. Exception satu-satunya: tag `<system-reminder>` untuk warning kritis (mis. tool unavailable) — tertutup rapi, tanpa teks tambahan.
4. Setelah investigasi selesai: kirim **SATU** pesan final berformat §2, TANPA teks sebelum atau sesudah.
5. Tool gagal → pilih **SATU**: retry silent (max 2×) / fallback silent / escalate blocker. Dilarang loop "Tapi X gagal, coba Y, Z…" di output.

## §7 Reports Notes Template

Audit log (tool calls, error, partial diff, narasi yang di-strip) ditulis ke `reports/<id>-notes.md` dengan template:

```
# <PP#id> — <judul tiket> — Investigation Notes
**Date**: <YYYY-MM-DD>
**Reviewer**: Salsabila QA

## Tool Calls (audit only, NOT for user)
- get_work_package(<id>)
- list_merge_requests(...)
- search_commits("<id>")
- get_file("path:line")
- ...

## Errors / Retries
- Token invalid (resolved via MCP fallback)
- File truncation >50% (escalated)

## Key Findings (raw, for cross-reference)
<path:line> — <code snippet> — <observation>

## Verdict (final, sama dengan output user)
PASS / FAIL / BLOCKED / DEPENDENCY

## Notes for Developer
<1 kalimat>
```

File ini untuk **audit trail** — owner Kibul bisa review kalau ada dispute. **Tidak boleh** di-quote ke user Discord.