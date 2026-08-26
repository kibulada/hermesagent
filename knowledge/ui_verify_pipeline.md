# UI Verify Pipeline — Spesifikasi Teknis

Pipeline otomatis untuk verifikasi UI tiket FE berbasis Playwright. Spec penuh: `AGENTS.md` §9.

## Arsitektur

```
OpenProject webhook
    ↓
webhook_server.py (port 9090)
    ↓ trigger kalau AC match UI keyword
ac_parser.py  → ui_verify_required: bool
    ↓ true
spec_generator.ts  → specs/generated/wp-<id>-<slug>.spec.ts
    ↓
runner.py  → npx playwright test (chromium, staging)
    ↓ result
post draft komentar OpenProject + tag @Kibul
    ↓ approval command
agent transisi status tiket
    ↓ Closed
cleanup.py  → hapus generated spec
```

## Komponen

| File | Tanggung jawab |
|---|---|
| `scripts/ac_parser.py` | Scan AC, regex keyword UI (§9.1) |
| `scripts/spec_generator.ts` | Generate Playwright spec skeleton |
| `scripts/runner.py` | Orchestrator: run + retry + post komentar |
| `scripts/cleanup.py` | Hapus spec saat tiket Closed |
| `scripts/webhook_server.py` | Listen webhook OP, trigger pipeline |
| `playwright.config.ts` | baseURL + chromium project, baca `.env.staging` |
| `utils/loginUtils.ts` | Login helper, baca dari env |
| `.env.staging.example` | Template credentials (commit-safe) |
| `.env.staging` | Actual credentials (gitignored) |

## Credentials Contract

4 variable wajib ada di `.env.staging`:
- `STAGING_BASE_URL` — base URL staging
- `STAGING_TEST_USERNAME` — user test
- `STAGING_TEST_PASSWORD` — password test
- `STAGING_TEST_TENANT` — nama tenant

`utils/loginUtils.ts` baca via `process.env`. **Hardcoded fallback = error**.

## Trigger Keyword (case-insensitive, whole word)

`button|tombol|form|input|modal|popup|page|halaman|tab|menu|dropdown|tabel|table|render|tampilan|layout|loading|empty state|validation|klik|click|submit|select|datepicker|autocomplete`

## Retry Policy

| Run 1 | Run 2 | Final | Aksi |
|---|---|---|---|
| Pass | — | PASS | Draft komentar, approval gate |
| Fail | Pass | PASS_FLAKY | Draft + note "flaky detected", approval |
| Fail | Fail | FAIL | Komentar blocker, tag @Kibul, no transisi |
| Timeout >120s | — | FAIL | Retry sesuai tabel |

**Satu lapisan retry saja.** Playwright dipanggil dengan `--retries=0`; retry ditangani `scripts/runner.py`.
Sebelumnya `runner.py` menyetel `CI=1`, yang mengaktifkan `retries: 2` di `playwright.config.ts` — total
hingga 6 percobaan, dan label `PASS_FLAKY` jadi menyesatkan karena Playwright sudah retry diam-diam duluan.

## Approval Gate

- Agent **tidak** auto-update status tiket.
- Agent hanya post komentar draft.
- Kibul balas `lanjut` / `reject` di thread Discord existing.
- Tanpa approval → tiket tetap di status `In Review`.

## Spec Lifecycle

1. Generate saat run pertama → file di `specs/generated/wp-<id>-<slug>.spec.ts`.
2. **Ephemeral dan gitignored** — jangan di-commit (`automation/simrs_e2e_playwright/.gitignore` mengabaikan `specs/generated/wp-*.spec.ts`).
3. Auto-delete saat tiket Closed (via `cleanup.py`).
4. History permanen di komentar tiket OpenProject — itulah audit trail-nya, bukan git.

## Test Constraints

- Read-only: tidak INSERT/UPDATE/DELETE via UI.
- Staging only: baseURL wajib staging.
- Chromium only: `--project=chromium`.
- No PII: assertion tidak expect/print identitas pasien.
- Test account/fixture, bukan data klinis real.

## Credentials Audit

> **Koreksi 2026-08-26.** Audit versi sebelumnya menyatakan `.env.staging.example` "template, commit-safe".
> Itu **salah**: file tersebut berisi kredensial staging asli (username + password) tepat di bawah header
> "DO NOT commit real values". Sudah diganti placeholder. **Password staging tetap harus dirotasi** —
> menghapus dari file tidak membatalkan kredensial yang sudah tersebar.

Status sekarang:
- ✅ `.env.staging.example` hanya placeholder.
- ✅ Kredensial asli hanya di `.env.staging` (gitignored).
- ✅ Tidak ada di `tests/`, `utils/`, `scripts/`, `playwright.config.ts`.

Cara verifikasi ulang:
```bash
grep -rn "pass4medinesia\|timmedinesia" automation/simrs_e2e_playwright --include=*.ts --include=*.py --include=*.example
```

## Out of Scope

- Visual regression (pixel diff).
- Mobile viewport.
- Production verify.
- Auto-heal flaky test.
- Cross-browser (firefox/webkit).

## Discord UX

### Entry Point

`scripts/discord_bot.py` — single process, jalan 2 worker:

- **Discord client** (thread utama) — listen slash / prefix / approval.
- **Webhook server** (thread daemon, port 9090) — listen OP webhook.

### Commands

Slash:
```
/automation ui ticket:<id> [action:verify|status|cleanup]
```

Default `action = verify`. Contoh:
- `/automation ui ticket:7434` → verify.
- `/automation ui ticket:7434 status` → cek report terakhir.
- `/automation ui ticket:7434 cleanup` → force delete spec.

Prefix (fallback, lebih cepat):
```
!ui 7434
!ui 7434 status
!ui 7434 cleanup
```

### Approval (Reactive)

Agent **tidak** auto-transisi. Bot listen message dari Kibul (`KIBUL_DISCORD_ID`) di thread Discord existing:

| Reply Kibul | Aksi agent |
|---|---|
| `lanjut` | Transisi tiket → Closed (status id dari `OP_CLOSED_STATUS_ID`) |
| `reject` | Tahan tiket, post komentar "Hold per Kibul" |

Pattern: message di thread existing yang mengandung `PP#<id>` + di awal message cuma `lanjut`/`reject`.

### Concurrency

- Lock per ticket: `reports/locks/<id>.lock`, TTL 5 menit.
- Trigger kedua saat lock aktif → reply `⏳ Pipeline PP#<id> sedang berjalan, skip duplicate.`
- Lock auto-release saat run selesai atau TTL expire.

### Flow Real

```
Normal (auto):
  OP update → webhook → ac_parser → lock acquire
    → spec_generator → runner.py (chromium, staging)
    → post draft komentar OP + lock release
        ↓
  Kibul balas 'lanjut' di thread
    → bot detect (PP#<id> + lanjut) → transition_ticket
    → post "Approved by Kibul, transitioned"

Manual:
  Kibul: /automation ui ticket:7434
    → bot: ⏳ mulai...
    → bot: ✅ PP#7434 done. Draft posted. Tag @Kibul.

Concurrency:
  Kibul: /automation ui ticket:7434 (lock aktif)
    → bot: ⏳ Pipeline PP#7434 sedang berjalan, skip duplicate.
```

### Deploy

```
pip install discord.py
python scripts/discord_bot.py --webhook-port 9090
```

Env wajib:
- `DISCORD_TOKEN`
- `OP_API_TOKEN`, `OP_BASE_URL`
- `WEBHOOK_SECRET` (untuk webhook OP)
- `KIBUL_DISCORD_ID` (default 394740825260556288)
- `STAGING_BASE_URL`, `STAGING_TEST_USERNAME`, `STAGING_TEST_PASSWORD`, `STAGING_TEST_TENANT` (di `.env.staging`)

Slash command register 1x via `bot.tree.sync()` saat startup.

## Token Resolution

Pipeline baca token via `scripts/hermes_config.py`. **Single source of truth = Hermes `config.yaml`**, fallback ke OS env kalau di-set manual.

### Priority
1. **OS env var** (override manual, e.g. saat run test).
2. **Hermes `config.yaml`** (default, lokasi di `C:\Users\ASUS\AppData\Local\hermes\config.yaml`).
3. Raise blocker kalau dua-duanya kosong.

### Mapping Table

| Pipeline env var | config.yaml path |
|---|---|
| `OP_API_TOKEN` | `mcp_servers.openproject.env.OPENPROJECT_API_KEY` |
| `OP_BASE_URL` | `mcp_servers.openproject.env.OPENPROJECT_URL` |
| `GITLAB_TOKEN` (opsional) | `mcp_servers.gitlab.env.GITLAB_TOKEN` |
| `GITLAB_URL` (opsional) | `mcp_servers.gitlab.env.GITLAB_URL` |

### Config Path

- Windows default: `%LOCALAPPDATA%\hermes\config.yaml` (otomatis).
- Override via `HERMES_CONFIG_PATH` env var (untuk deploy non-Windows atau path custom).

### Cache

`config.yaml` di-load 1x per process (lazy load + cache). Tidak re-read setiap call.

### Hardcode Compliance

> **Koreksi 2026-08-26.** Klaim versi sebelumnya — "tidak ada token hardcode di script" — **salah**.
> `scripts/discord_bot.py:91` berisi `api_key = 'sk-442a...'` literal, melanggar AGENTS.md §9.5.
> Sudah diganti `get_token('HERMES_API_KEY')`, yang resolve dari `custom_providers` di `config.yaml`.
> **API key tersebut tetap harus dicabut dan diterbitkan ulang.**

Status sekarang:
- ✅ Tidak ada token hardcode di script — ditegakkan oleh test `tests_unit/test_smoke_scripts.py::test_no_hardcoded_secrets`, bukan oleh audit manual.
- ✅ Tidak ada echo token ke stdout/log/Discord.
- ✅ Failure mode: config corrupt → fallback ke env → raise blocker eksplisit.

### Dependensi

```bash
pip install pyyaml
```
