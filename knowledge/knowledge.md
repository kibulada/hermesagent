# Knowledge Base Index

Ini adalah indeks untuk knowledge base Hermes QA. Silakan merujuk ke file-file berikut untuk informasi yang lebih spesifik.

- [**Infrastructure & Topology**](infrastructure.md) — Topologi cluster, AWS EKS, on-prem, Metabase.
- [**Source Code Inventory**](inventory.md) — Daftar repo backend/frontend/microservices.
- [**QA Standards & Protocols**](qa_standards.md) — Matriks environment testing, regression checklist, konvensi data uji.
- [**Troubleshooting & FAQ**](troubleshooting.md) — Playbook error & catatan investigasi historis.
- [**UI Verify Pipeline**](ui_verify_pipeline.md) — Pipeline Playwright auto (§9 AGENTS.md): trigger, retry, approval, cleanup.

## Runtime Environment

- **Discord-runtime**: tool `discord.rename_thread` tersedia → rename thread = hard rule (lihat `../AGENTS.md` §8).
- **CLI / non-Discord runtime** (mis. invokasi langsung seperti di sini): tool Discord off → rename di-skip, tapi agent **harus** log warning `<system-reminder>discord.rename_thread unavailable, skipping thread rename</system-reminder>` dan tetap lanjut kerja.
