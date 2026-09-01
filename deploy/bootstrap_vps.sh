#!/usr/bin/env bash
#
# bootstrap_vps.sh — pasang Hermes QA di VPS Debian/Ubuntu. Idempoten:
# aman dijalankan ulang, tidak menimpa secret yang sudah ada.
#
# Script ini SENGAJA tidak menyentuh kredensial. Dia menyiapkan struktur dan
# dependensi; pengisian secret dilakukan manual (deploy/README.md langkah 3-4).
#
# Usage:
#     sudo ./deploy/bootstrap_vps.sh
#     sudo APP_DIR=/srv/hermes-qa ./deploy/bootstrap_vps.sh
#
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-qa}"
ETC_DIR="${ETC_DIR:-/etc/hermes-qa}"
RUN_USER="${RUN_USER:-hermesqa}"
AUTOMATION_DIR="$APP_DIR/automation/simrs_e2e_playwright"

log()  { printf '\033[1;34m[bootstrap]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[bootstrap] WARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[bootstrap] GAGAL:\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "jalankan sebagai root (sudo)."
[[ -f "$APP_DIR/CLAUDE.md" ]] || die "APP_DIR=$APP_DIR bukan checkout Hermes QA. Clone dulu reponya ke situ."

# --- 1. Paket sistem ---------------------------------------------------------
log "pasang paket sistem"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git curl ca-certificates

if ! command -v node >/dev/null 2>&1; then
    log "Node.js tidak ada - pasang Node 22 LTS dari NodeSource"
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y -qq nodejs
fi
log "node $(node --version) / npm $(npm --version) / $(python3 --version)"

# --- 2. User non-root --------------------------------------------------------
if ! id -u "$RUN_USER" >/dev/null 2>&1; then
    log "buat service user: $RUN_USER"
    useradd --system --create-home --shell /usr/sbin/nologin "$RUN_USER"
else
    log "service user $RUN_USER sudah ada - lewati"
fi

# --- 3. Struktur direktori ---------------------------------------------------
log "siapkan $ETC_DIR (mode 0750)"
install -d -m 0750 -o root -g "$RUN_USER" "$ETC_DIR"

# Direktori runtime yang gitignored, jadi tidak ikut clone.
for d in reports reports/locks reports/tmp logs \
         "$AUTOMATION_DIR/specs/generated" \
         "$AUTOMATION_DIR/test-results" \
         "$AUTOMATION_DIR/screenshots"; do
    install -d -m 0755 -o "$RUN_USER" -g "$RUN_USER" "${d#/}" 2>/dev/null || \
    install -d -m 0755 -o "$RUN_USER" -g "$RUN_USER" "$APP_DIR/$d" 2>/dev/null || true
done
install -d -m 0755 -o "$RUN_USER" -g "$RUN_USER" "$APP_DIR/reports/locks" "$APP_DIR/logs"

# --- 4. Python venv ----------------------------------------------------------
# Di Windows `python` resolve ke venv runtime Hermes (lihat requirements.txt).
# Di VPS itu tidak ada, jadi kita bikin venv eksplisit milik proyek.
log "buat venv $APP_DIR/.venv"
[[ -d "$APP_DIR/.venv" ]] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
# mcp tidak ada di requirements.txt karena di Windows disediakan runtime Hermes.
# Di VPS harus dipasang eksplisit atau mcp_launcher gagal import.
"$APP_DIR/.venv/bin/pip" install --quiet "mcp==1.26.0"
log "python deps terpasang"

# --- 5. Node deps + browser --------------------------------------------------
log "npm ci + playwright chromium (butuh beberapa menit)"
cd "$AUTOMATION_DIR"
[[ -f package-lock.json ]] && npm ci --silent || npm install --silent
npx playwright install --with-deps chromium
cd "$APP_DIR"

# --- 6. Template config ------------------------------------------------------
if [[ ! -f "$ETC_DIR/hermes-qa.env" ]]; then
    log "pasang template env -> $ETC_DIR/hermes-qa.env (WAJIB diisi manual)"
    install -m 0640 -o root -g "$RUN_USER" deploy/env.example "$ETC_DIR/hermes-qa.env"
else
    warn "$ETC_DIR/hermes-qa.env sudah ada - TIDAK ditimpa"
fi

for f in config.yaml custom.env; do
    [[ -f "$ETC_DIR/$f" ]] || { : > "$ETC_DIR/$f"; chmod 0640 "$ETC_DIR/$f"; chown root:"$RUN_USER" "$ETC_DIR/$f"; }
done

# --- 7. systemd --------------------------------------------------------------
log "pasang unit systemd"
install -m 0644 deploy/systemd/hermes-qa-bot.service /etc/systemd/system/
install -m 0644 deploy/systemd/hermes-qa-webhook.service /etc/systemd/system/
systemctl daemon-reload

chown -R "$RUN_USER":"$RUN_USER" "$APP_DIR"

cat <<'NEXT'

==============================================================================
Bootstrap selesai. Layanan BELUM dijalankan - itu disengaja.

Langkah berikutnya (manual, tidak diotomasi karena menyangkut kredensial):

  1. Isi  /etc/hermes-qa/hermes-qa.env      (semua field kosong)
  2. Isi  /etc/hermes-qa/config.yaml        (mcp_servers + custom_providers)
  3. Isi  /opt/hermes-qa/automation/simrs_e2e_playwright/.env.staging
  4. Jalankan gate verifikasi:
         sudo -u hermesqa /opt/hermes-qa/deploy/preflight.sh
  5. Baru start:
         systemctl enable --now hermes-qa-bot

JANGAN start layanan sebelum preflight lulus. Kredensial yang tidak ter-resolve
menghasilkan respons kosong yang terbaca seolah tiket tidak ada - itu persis
false-green yang dilarang CLAUDE.md.
==============================================================================
NEXT
