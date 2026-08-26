# Indeks Memori Hermes QA

Indeks file memori operasional. Muat sesuai kebutuhan — **jangan baca semuanya di awal**.

## Entry point per runtime

| Runtime | System prompt |
|---|---|
| Claude Code (CLI) | `../CLAUDE.md` — versi ramping, on-demand. Skill di `.claude/skills/`, subagent di `.claude/agents/` |
| Hermes harness + Discord bot | `../AGENTS.md` |

Keduanya berbagi sumber yang sama di `memory/` dan `knowledge/`. Kalau sebuah aturan ada di dua tempat, yang di `memory/`/`knowledge/` yang menang — `AGENTS.md` §4 dan §9 sengaja dijadikan pointer supaya tidak ada dua versi yang saling menjauh.

## Memori operasional

- [**Aturan Operasional**](operational_rules.md) — aturan keras, batasan write, protokol inti. **Sumber tunggal untuk batasan write op.**
- [**Alur Kerja & Pola Pikir QA**](qa_workflow.md) — verification-first, fact vs claim, format komentar `[QA-PASS]`/`[QA-FAIL]`, idempotency check, eskalasi.
- [**Referensi API OpenProject**](openproject_api.md) — endpoint, transisi status, board. **Status yang boleh dipakai QA: 11, 13, 16, 17 saja** — 12 (Closed) dan 14 (Rejected) di luar wewenang QA.
- [**Output Discipline**](output_discipline.md) — anti-frasa, template output, noise budget. **Scope: output Discord saja.** Di CLI, tampilkan command supaya bisa diverifikasi ulang (lihat `user_profile.md`).
- [**Profil Pengguna**](user_profile.md) — cara kerja dan preferensi Kibul.
- [**Token Management**](token_management.md) · [**Git Workflow**](git_workflow.md) · [**Struktur App**](app_structure.md) · [**Struktur Workspace**](workspace_structure.md)

## Knowledge base

Indeks: [`../knowledge/knowledge.md`](../knowledge/knowledge.md)

- `qa_standards.md` — checklist regresi per modul (§9), konvensi test data & masking PII (§10), matriks environment (§8).
- `ui_verify_pipeline.md` — **sumber tunggal spesifikasi pipeline UI verify.**
- `infrastructure.md` · `inventory.md` · `troubleshooting.md`

## Template output

`../templates/qa/README.md` — Template A (verifikasi test case), B (reproduksi bug), C (analisa risiko regresi).

## Thread Rename (Discord)

Hard rule: `[PP#ID] - Judul` (1 tiket) atau `[Multi-Ticket] - Ringkasan (PP#A, PP#B)` (>1 tiket). Pemicu: aksi aktif pertama (verifikasi / code review / repro bug), **bukan** `GET` status. Kalau `discord.rename_thread` tidak tersedia, skip tapi **log warning**. Detail & regex self-check: `../AGENTS.md` §8.
