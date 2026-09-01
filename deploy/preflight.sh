#!/usr/bin/env bash
#
# preflight.sh — gate verifikasi sebelum layanan boleh start.
#
# Prinsip CLAUDE.md: default stance FAIL sampai ada bukti cukup untuk PASS.
# Script ini TIDAK pernah mencetak nilai kredensial, hanya panjangnya.
#
# Exit 0 = semua gate lulus. Exit 1 = ada yang gagal, JANGAN start layanan.
#
set -uo pipefail

APP_DIR="${APP_DIR:-/opt/hermes-qa}"
ENV_FILE="${ENV_FILE:-/etc/hermes-qa/hermes-qa.env}"
PY="$APP_DIR/.venv/bin/python"

PASS=0; FAIL=0
ok()   { printf '  \033[1;32mPASS\033[0m  %s\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '  \033[1;31mFAIL\033[0m  %s\n' "$*"; FAIL=$((FAIL+1)); }
head_() { printf '\n\033[1;34m== %s\033[0m\n' "$*"; }

[[ -f "$ENV_FILE" ]] && set -a && . "$ENV_FILE" && set +a

head_ "1. Interpreter & dependensi"
if [[ -x "$PY" ]]; then ok "venv ada: $("$PY" --version 2>&1)"; else bad "venv tidak ada di $PY"; fi
for m in discord yaml pytest openpyxl mcp; do
    "$PY" -c "import $m" 2>/dev/null && ok "modul $m" || bad "modul $m tidak terpasang"
done

head_ "2. Env var wajib"
# OP_API_TOKEN lewat env_required() - kosong = bot mati saat start.
for v in OP_API_TOKEN OP_BASE_URL DISCORD_TOKEN HERMES_CONFIG_PATH HERMES_CUSTOM_ENV HERMES_MCP_DIR; do
    val="${!v:-}"
    if [[ -n "$val" ]]; then
        case "$v" in
            *_URL|*_PATH|*_DIR) ok "$v = $val" ;;
            *)                  ok "$v = <ter-set, ${#val} char>" ;;
        esac
    else
        bad "$v kosong"
    fi
done

if [[ -z "${WEBHOOK_SECRET:-}" ]]; then
    bad "WEBHOOK_SECRET kosong - verify_signature() akan melewatkan verifikasi, endpoint terbuka"
else
    ok "WEBHOOK_SECRET = <ter-set, ${#WEBHOOK_SECRET} char>"
fi

# Guardrail: status ID di luar 11/13/16/17 bukan wewenang QA.
case "${OP_PASS_STATUS_ID:-16}" in
    11|13|16|17) ok "OP_PASS_STATUS_ID = ${OP_PASS_STATUS_ID:-16} (valid untuk QA)" ;;
    *)           bad "OP_PASS_STATUS_ID = ${OP_PASS_STATUS_ID} DILARANG - hanya 11/13/16/17" ;;
esac

head_ "3. Resolusi kredensial MCP"
for s in openproject gitlab; do
    if "$PY" "$APP_DIR/integrations/mcp_launcher.py" "$s" --selftest >/dev/null 2>&1; then
        ok "mcp_launcher $s --selftest"
    else
        bad "mcp_launcher $s --selftest gagal - jalankan manual untuk lihat blocker"
    fi
done

head_ "4. Konektivitas Hermes LLM gateway"
HURL="${HERMES_API_URL:-http://127.0.0.1:20128/v1/chat/completions}"
BASE="${HURL%/chat/completions}"
if curl -fsS --max-time 5 -o /dev/null "$BASE/models" 2>/dev/null; then
    ok "gateway hidup di $BASE"
else
    bad "gateway TIDAK merespons di $BASE - generate test code akan gagal"
fi

head_ "5. Kredensial staging Playwright"
STG="$APP_DIR/automation/simrs_e2e_playwright/.env.staging"
if [[ -f "$STG" ]]; then
    ok ".env.staging ada"
    for k in STAGING_BASE_URL STAGING_TEST_USERNAME STAGING_TEST_PASSWORD STAGING_TEST_TENANT; do
        grep -q "^${k}=." "$STG" && ok "  $k terisi" || bad "  $k kosong/hilang"
    done
    perm=$(stat -c '%a' "$STG")
    [[ "$perm" == "600" || "$perm" == "640" ]] && ok "  permission $perm" || bad "  permission $perm terlalu longgar (harus 600/640)"
else
    bad ".env.staging tidak ada - playwright.config.ts:9 akan throw"
fi

head_ "6. Browser Playwright"
(cd "$APP_DIR/automation/simrs_e2e_playwright" && npx playwright --version >/dev/null 2>&1) \
    && ok "playwright CLI siap" || bad "playwright CLI tidak jalan"
# Jangan cek $HOME: sudo -u tidak selalu mengganti HOME, dan browser sengaja
# tidak ditaruh di sana (ProtectHome=true memblokirnya).
PWDIR="${PLAYWRIGHT_BROWSERS_PATH:-}"
if [[ -z "$PWDIR" ]]; then
    bad "PLAYWRIGHT_BROWSERS_PATH kosong - runtime akan mencari browser di ~ dan tidak ketemu"
elif compgen -G "$PWDIR/chromium-*" >/dev/null 2>&1; then
    ok "browser chromium ada di $PWDIR"
else
    bad "chromium tidak ada di $PWDIR - jalankan ulang bootstrap langkah 5"
fi

head_ "7. Unit test kode agent"
if (cd "$APP_DIR" && "$PY" -m pytest automation/simrs_e2e_playwright/tests_unit/ -q >/tmp/pf-pytest.log 2>&1); then
    ok "pytest tests_unit lulus"
else
    bad "pytest tests_unit GAGAL - lihat /tmp/pf-pytest.log"
fi

head_ "8. Port 9090"
# discord_bot.py menjalankan webhook di thread daemon pada port yang sama.
# Kalau hermes-qa-webhook juga aktif, salah satu akan gagal bind.
if ss -ltn 2>/dev/null | grep -q ':9090 '; then
    bad "port 9090 sudah dipakai - cek bentrok bot vs webhook standalone"
else
    ok "port 9090 bebas"
fi

printf '\n\033[1m== HASIL: %d pass, %d fail\033[0m\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
    printf '\033[1;31mBLOCKED\033[0m - jangan start layanan sampai semua gate lulus.\n'
    exit 1
fi
printf '\033[1;32mSIAP\033[0m - boleh: systemctl enable --now hermes-qa-bot\n'
