# Deploy Hermes QA ke VPS

Runbook untuk mereplikasi setup lokal (Windows) ke VPS Linux.

> **Repo ini bukan aplikasi yang berdiri sendiri.** Isinya "otak" agent —
> knowledge, rules, spec, scripts. Empat komponen yang membuatnya hidup ada di
> luar repo dan harus disiapkan terpisah. Lihat §1.

Asumsi: Debian 12 / Ubuntu 22.04+, akses root, systemd. Kalau distro kamu beda,
yang perlu disesuaikan hanya §2 langkah 1.

---

## 1. Apa yang tidak ada di repo ini

| # | Komponen | Lokasi di mesin lokal | Status |
|---|---|---|---|
| 1 | Runtime Hermes (`hermes-agent`) | `E:\HermesData\hermes\hermes-agent` | Repo terpisah: `github.com/NousResearch/hermes-agent` @ `55759cb` |
| 2 | `config.yaml` | `E:\HermesData\hermes\config.yaml` | Kredensial — sengaja tidak di-version |
| 3 | MCP server scripts | `E:\HermesData\hermes\mcp-servers\*.py` | **Sudah di-vendor** ke `integrations/mcp-servers/` |
| 4 | Secrets | `secrets/`, `config/.env`, `.env.staging` | Transfer manual, jangan lewat git |

Komponen 3 dulunya tidak ter-version di mana pun. `integrations/gitlab/server.py`
(75 baris) adalah file yang **berbeda** dari `gitlab_mcp.py` (207 baris) yang
benar-benar dijalankan `mcp_launcher.py`. Sekarang keduanya ada di
`integrations/mcp-servers/`, dan `HERMES_MCP_DIR` menunjuk ke sana.

### Portabilitas kode

Kode agent sudah portable — tidak ada `msvcrt`, `shell=True`, atau `.bat`, dan
`runner.py:123` sudah menangani `npx.cmd` vs `npx`. Yang perlu di-override di
Linux hanya tiga path default:

| Konstanta | Default (Windows) | Override |
|---|---|---|
| `hermes_config.py:24` `DEFAULT_CONFIG_PATH` | `%LOCALAPPDATA%\hermes\config.yaml` | `HERMES_CONFIG_PATH` |
| `hermes_config.py:25` `CUSTOM_ENV_PATH` | `D:/Hermes-QA/config/.env` | `HERMES_CUSTOM_ENV` |
| `mcp_launcher.py:37` `DEFAULT_MCP_DIR` | `%LOCALAPPDATA%\hermes\mcp-servers` | `HERMES_MCP_DIR` |

Di Linux `LOCALAPPDATA` tidak ada, sehingga path default menjadi **relatif** dan
diam-diam tidak ketemu. `_load_config()` mengembalikan `None` tanpa memunculkan
error. **Nol perubahan kode, tapi ketiga env var itu wajib di-set.**

---

## 2. Urutan pemasangan

### Langkah 1 — Runtime Hermes

Menyediakan LLM gateway di `:20128/v1` yang dipanggil
`discord_bot.py:call_hermes_api()` untuk generate test code.

```bash
git clone https://github.com/NousResearch/hermes-agent.git /opt/hermes-agent
cd /opt/hermes-agent
git checkout 55759cb          # pin ke versi yang dipakai di lokal
docker compose up -d
curl -fsS http://127.0.0.1:20128/v1/models    # harus 200
```

> **Cek dulu sebelum sewa VPS.** `custom_providers` di `config.yaml` berisi model
> `nvidia/…`, `mistral/…`, `kr/…`, `gemini/…` — indikasi gateway mem-*proxy* ke
> API remote, bukan inference lokal. Kalau benar, 2–4 vCPU tanpa GPU cukup.
> Kalau ternyata ada model yang di-load lokal, kebutuhannya beda total.

### Langkah 2 — Repo QA + bootstrap

```bash
git clone https://github.com/kibulada/hermesagent.git /opt/hermes-qa
cd /opt/hermes-qa
sudo ./deploy/bootstrap_vps.sh
```

Bootstrap memasang: paket sistem, Node 22, service user `hermesqa`, venv +
`requirements.txt` + `mcp==1.26.0`, `npm ci`, browser Chromium, direktori
runtime yang gitignored, template config, dan unit systemd. Idempoten — aman
diulang, tidak menimpa secret yang sudah ada. **Layanan sengaja tidak di-start.**

> `mcp==1.26.0` dipasang eksplisit karena di Windows paket itu disediakan runtime
> Hermes, dan karena itu di-comment out di `requirements.txt`. Di VPS tanpa
> pemasangan ini `mcp_launcher.py` gagal import.

### Langkah 3 — Kredensial

Tiga file, semuanya diisi manual. Jangan pernah lewat git.

**`/etc/hermes-qa/hermes-qa.env`** — template sudah ditaruh bootstrap dari
`deploy/env.example`. Isi semua field kosong. Generate webhook secret:

```bash
openssl rand -hex 32
```

**`/etc/hermes-qa/config.yaml`** — minimal, hanya bagian yang dibaca
`hermes_config.py`. Sisa key di `config.yaml` lokal (`agent`, `tts`, `browser`,
dll) milik runtime Hermes dan tidak relevan di sini:

```yaml
mcp_servers:
  openproject:
    env:
      OPENPROJECT_URL: https://tracker.kesia.id
      OPENPROJECT_API_KEY: "<isi>"
  gitlab:
    env:
      GITLAB_URL: https://gitlab.com
      GITLAB_TOKEN: "<isi>"

custom_providers:
  - name: hermes
    base_url: http://127.0.0.1:20128/v1
    api_key: "<isi>"
```

Transfer token dari mesin lokal lewat `scp`, atau — lebih baik — terbitkan token
baru khusus VPS supaya bisa dicabut terpisah kalau VPS bermasalah.

```bash
chmod 640 /etc/hermes-qa/config.yaml
chown root:hermesqa /etc/hermes-qa/config.yaml
```

### Langkah 4 — Kredensial staging Playwright

`playwright.config.ts:5` memuat file ini lewat dotenv dan **throw** di baris 9
kalau `STAGING_BASE_URL` kosong. Tidak bisa digantikan env var systemd.

```bash
cd /opt/hermes-qa/automation/simrs_e2e_playwright
cp .env.staging.example .env.staging
# isi: STAGING_BASE_URL / STAGING_TEST_USERNAME
#      STAGING_TEST_PASSWORD / STAGING_TEST_TENANT
chmod 600 .env.staging
chown hermesqa:hermesqa .env.staging
```

Staging only, read-only, chromium only.

### Langkah 5 — Preflight (gate, jangan dilewati)

```bash
sudo -u hermesqa /opt/hermes-qa/deploy/preflight.sh
```

Delapan gate: dependensi, env var, resolusi MCP, konektivitas gateway, kredensial
staging, browser, unit test, port. Exit 1 = jangan start.

Alasan gate ini keras: kredensial yang gagal resolve **tidak** memunculkan error.
`_load_config()` mengembalikan `None`, API membalas kosong, dan hasilnya terbaca
seolah tiket tidak ada. Itu false-green yang persis dilarang CLAUDE.md.

### Langkah 6 — Start

```bash
systemctl enable --now hermes-qa-bot
systemctl status hermes-qa-bot
journalctl -u hermes-qa-bot -f
```

> **Jalankan salah satu saja.** `discord_bot.py` sudah menjalankan webhook di
> thread daemon pada port 9090 (`discord_bot.py:689`). `hermes-qa-webhook.service`
> adalah **alternatif** untuk deploy tanpa Discord, dan sudah diberi
> `Conflicts=hermes-qa-bot.service`.

### Langkah 7 — Knowledge graph

`graphify-out/` gitignored, jadi tidak ikut clone. Hook `graphify hook-guard search`
di `.claude/settings.json` akan jalan tanpa graph sampai:

```bash
cd /opt/hermes-qa && graphify update .
```

Lewati kalau kamu tidak menjalankan Claude Code di VPS.

---

## 3. Ekspos webhook

OpenProject di `tracker.kesia.id` harus bisa menjangkau `:9090`. Jangan buka port
langsung — pakai reverse proxy + TLS. Contoh Caddy:

```
qa-hook.domain-kamu.id {
    reverse_proxy 127.0.0.1:9090
}
```

Lalu di OpenProject: Administration → Webhooks → URL di atas, secret **sama persis**
dengan `WEBHOOK_SECRET`, event `work_package:created` + `work_package:updated`.

`verify_signature()` memakai HMAC-SHA256. Kalau `WEBHOOK_SECRET` kosong,
verifikasi **dilewati** dan endpoint terbuka untuk siapa saja — di VPS ber-IP
publik itu tidak bisa diterima. Preflight gate 2 menolak kondisi ini.

---

## 4. Yang tidak ikut pindah

| Hal | Kenapa |
|---|---|
| `sourcecode/*` (5 repo) | Repo git masing-masing. Clone terpisah kalau butuh verifikasi selector FE. |
| `node_modules/`, `__pycache__/` | Di-install, bukan di-copy. |
| `test-results/`, `screenshots/`, `reports/*.log` | Artefak ephemeral. |
| `specs/generated/wp-*.spec.ts` | Ephemeral by design; histori permanen ada di komentar tiket. |
| `graphify-out/` | Regenerasi dengan `graphify update .` |

Tanpa `sourcecode/kesia-fe`, gate anti-false-green "tiap selector terbukti ada di
sourcecode" tidak bisa dijalankan. Kalau pipeline UI verify dipakai penuh di VPS,
`sourcecode/kesia-fe` wajib ikut di-clone.

---

## 5. Dua jebakan Linux yang sudah ditutup

Keduanya lolos di Windows dan hanya muncul di VPS. Sekarang dijaga
`tests_unit/test_deploy_kit.py` (14 test), jadi kalau ada yang mengubahnya
tanpa sadar, pytest yang menolak — bukan VPS yang mati diam-diam.

**Browser Playwright vs `ProtectHome=true`.** `npx playwright install`
dijalankan root, jadi browser mendarat di `/root/.cache/ms-playwright`. Service
jalan sebagai `hermesqa`, dan unit systemd memakai `ProtectHome=true` — jadi
`chown` pun tidak menyelesaikan, karena home di-mask untuk proses itu. Solusinya
`PLAYWRIGHT_BROWSERS_PATH=/opt/hermes-qa/.ms-playwright`, di-export bootstrap
saat install dan di-set lagi di `hermes-qa.env` saat runtime. Nilainya wajib
sama di dua tempat itu; ada test yang membandingkannya.

**Nama env var OpenProject diterjemahkan.** Yang diisi di `hermes-qa.env` adalah
nama sisi pipeline; `mcp_launcher.py` (`TOKEN_MAP`) menerjemahkan sebelum
menjalankan server MCP:

| Diisi operator | Dibaca server MCP |
|---|---|
| `OP_API_TOKEN` | `OPENPROJECT_API_KEY` |
| `OP_BASE_URL` | `OPENPROJECT_URL` |
| `GITLAB_TOKEN` | `GITLAB_TOKEN` (sama) |
| `GITLAB_URL` | `GITLAB_URL` (sama) |

Jangan mengisi `OPENPROJECT_*` di `hermes-qa.env` — launcher tidak membacanya.
Asimetri ini yang bikin GitLab kelihatan "jalan sendiri" dan OpenProject tidak.

---

## 6. Temuan yang perlu keputusan

**Default `OP_BASE_URL` tidak konsisten.** `webhook_server.py:54` memakai fallback
`https://project.kesia.id`, sedangkan `openproject_mcp.py` dan CLAUDE.md memakai
`https://tracker.kesia.id`. Fallback ini hanya terpakai kalau resolusi env dan
`config.yaml` dua-duanya gagal — persis skenario yang lebih mungkin terjadi di
VPS baru. Dampaknya: request ke host yang salah, respons kosong, terbaca sebagai
"tiket tidak ada".

Mitigasi sekarang: `OP_BASE_URL` di-set eksplisit di `hermes-qa.env` dan
diverifikasi preflight gate 2, sehingga fallback tidak pernah tercapai. Perbaikan
sebenarnya ada di kode dan butuh approval — belum dikerjakan.

---

## 7. Operasi harian

```bash
systemctl status hermes-qa-bot
journalctl -u hermes-qa-bot -f
journalctl -u hermes-qa-bot --since "1 hour ago" | grep -i error

# update
cd /opt/hermes-qa && sudo -u hermesqa git pull
sudo -u hermesqa .venv/bin/pip install -r requirements.txt
sudo -u hermesqa ./deploy/preflight.sh && systemctl restart hermes-qa-bot

# lock tersangkut (TTL 5 menit, biasanya bersih sendiri)
ls -la /opt/hermes-qa/reports/locks/
```

Rotasi kredensial: ubah `/etc/hermes-qa/config.yaml` atau `hermes-qa.env`, lalu
`systemctl restart hermes-qa-bot`. `config.yaml` di-cache sekali per proses
(`_load_config()`), jadi restart wajib — bukan opsional.
