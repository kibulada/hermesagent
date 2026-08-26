#!/usr/bin/env python3
"""
discord_bot.py — single-process: slash command + prefix handler + webhook server.
Sesuai AGENTS.md §9.

Slash:
    /automation ui ticket:<id> [action:verify|status|cleanup]

Prefix:
    !ui <id> [action]

Approval (reactive):
    Kibul balas 'lanjut' / 'reject' di thread existing → agent transisi/hold.

Run:
    python scripts/discord_bot.py
    python scripts/discord_bot.py --webhook-port 9090 (default)

Env:
    DISCORD_TOKEN           — bot token
    OP_API_TOKEN            — OpenProject
    OP_BASE_URL             — default https://tracker.kesia.id
    WEBHOOK_SECRET          — shared secret OP webhook
    KIBUL_DISCORD_ID        — 394740825260556288
    STAGING_BASE_URL        — wajib di .env.staging (sudah ada)
"""
import argparse
import asyncio
import base64
import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
RUNNER = REPO / 'scripts' / 'runner.py'
AC_PARSER = REPO / 'scripts' / 'ac_parser.py'
CLEANUP = REPO / 'scripts' / 'cleanup.py'
sys.path.insert(0, str(REPO / 'scripts'))
from lock import TicketLock  # noqa: E402
from hermes_config import get_token  # noqa: E402

try:
    import discord
    from discord import app_commands
except ImportError:
    print('discord.py belum terinstall. pip install discord.py', file=sys.stderr)
    sys.exit(1)

DISCORD_TOKEN = get_token('DISCORD_TOKEN') or os.environ.get('DISCORD_TOKEN')
KIBUL_ID = os.environ.get('KIBUL_DISCORD_ID', '394740825260556288')
OP_BASE_URL = get_token('OP_BASE_URL') or os.environ.get('OP_BASE_URL', 'https://tracker.kesia.id')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')

# Status ID QA — sumber tunggal: memory/openproject_api.md "Status ID Mapping".
# 14 = Rejected, 12 = Closed: KEDUANYA bukan langkah QA, jangan dipakai di sini.
STATUS_TEST_FAILED = '11'
STATUS_ON_HOLD = '13'
STATUS_TESTED_DEV = '16'
STATUS_TESTED_STAGING = '17'
ALLOWED_STATUS_IDS = {STATUS_TEST_FAILED, STATUS_ON_HOLD, STATUS_TESTED_DEV, STATUS_TESTED_STAGING}

PP_REGEX = re.compile(r'PP#(\d+)')
APPROVE_REGEX = re.compile(r'^\s*(lanjut|reject)\s*$', re.IGNORECASE)


def env_required(name: str) -> str:
    val = os.environ.get(name) or get_token(name)
    if not val:
        raise SystemExit(f'Environment {name} missing')
    return val


def get_op_auth_header(token: str) -> str:
    if token.startswith('Basic ') or token.startswith('Bearer '):
        return token
    auth_str = base64.b64encode(f'apikey:{token}'.encode()).decode()
    return f'Basic {auth_str}'


def slugify(text: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s[:50] or 'untitled'


def call_hermes_api(prompt: str) -> str:
    """
    Call hermes AI via local OpenAI-compatible API.
    Returns generated test code as string.
    """
    import urllib.request
    import urllib.error
    
    api_url = get_token('HERMES_API_URL') or 'http://localhost:20128/v1/chat/completions'
    api_key = get_token('HERMES_API_KEY')
    if not api_key:
        raise RuntimeError('HERMES_API_KEY missing (set env atau config/.env). Tidak ada fallback hardcode.')
    
    payload = json.dumps({
        'model': 'hermes',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7,
        'max_tokens': 2000,
        'stream': False
    })
    
    req = urllib.request.Request(
        api_url,
        data=payload.encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise RuntimeError(f'Hermes API error: {e.code} - {error_body}')
    except Exception as e:
        raise RuntimeError(f'Failed to call Hermes API: {e}')


def generate_ai_test_code(ticket_id: int, subject: str, ac_text: str) -> str:
    """
    Generate Playwright test code using Hermes AI.
    Returns TypeScript test code.
    """
    prompt = f"""You are an expert QA automation engineer. Generate Playwright test code to verify the following Acceptance Criteria.

**Ticket**: PP#{ticket_id}
**Subject**: {subject}

**Acceptance Criteria**:
```
{ac_text}
```

**Your Task**: Generate a COMPLETE Playwright test function that verifies EACH AC point with specific assertions.

**Selector Hints** (Common UI Elements in SIMRS):
- Patient signature: .signature-patient, .ttd-pasien
- Doctor signature: .signature-doctor, .ttd-dokter
- Print button: button:has-text('Cetak'), .print-btn
- Save button: button:has-text('Simpan'), button[type="submit"]
- Forms: form[name="..."], .form-control

**CRUD Pattern Recognition**:
- Hapus/Remove → await expect(page.locator('...')).toBeHidden();
- Tampil/Muncul → await expect(page.locator('...')).toBeVisible();
- Simpan/Save → await page.click('button:has-text("Simpan")');

**Output Format** (CRITICAL):
Return ONLY the test function wrapped in ```typescript and ```. NO other text before or after.

Example:
```typescript
test('PP#{ticket_id} - [descriptive name]', async ({{ page }}) => {{
  await page.goto('/relevant-path');
  
  // AC#1: [description]
  await expect(page.locator('.selector')).toBeVisible();
  
  // AC#2: [description]
  await page.click('button.action');
}});
```

**Rules**:
- NO placeholder comments like "TODO"
- EACH AC point must have executable assertion
- Add explicit waits for dynamic content
- Return ONLY TypeScript code, no explanation"""

    return call_hermes_api(prompt)


def fetch_ac(ticket_id: int) -> str:
    import urllib.request
    import urllib.error
    token = env_required('OP_API_TOKEN')
    url = f'{OP_BASE_URL}/api/v3/work_packages/{ticket_id}'
    req = urllib.request.Request(url, headers={'Authorization': get_op_auth_header(token)})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError('Token invalid (401). Minta token baru.')
        raise
    desc = data.get('description', {}) or {}
    return desc.get('raw', '') or desc.get('html', '') or ''


def fetch_subject(ticket_id: int) -> str:
    import urllib.request
    import urllib.error
    token = env_required('OP_API_TOKEN')
    url = f'{OP_BASE_URL}/api/v3/work_packages/{ticket_id}'
    req = urllib.request.Request(url, headers={'Authorization': get_op_auth_header(token)})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError('Token invalid (401). Minta token baru.')
        raise
    return data.get('subject', f'wp-{ticket_id}')


def check_ui_flag(ticket_id: int) -> bool:
    try:
        proc = subprocess.run(
            ['python', str(AC_PARSER), '--openproject', '--id', str(ticket_id)],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(f'ac_parser gagal (rc={proc.returncode}): {proc.stderr.strip()[-300:]}')
        return json.loads(proc.stdout).get('ui_verify_required', False)
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        raise RuntimeError(f'ac_parser tidak bisa dijalankan: {e}') from e


def fmt_result(ticket_id: int, result: dict) -> str:
    """Ringkas hasil run untuk Discord. Bedakan FAIL (ada AC gagal) dari NOT_VERIFIED."""
    status = result.get('status', 'FAIL')
    failed_ac = result.get('failed_ac') or []
    note = result.get('flaky_note', '')

    if status == 'NOT_VERIFIED':
        head = (f'⚠️ PP#{ticket_id} **NOT_VERIFIED** - spec tidak menghasilkan test '
                f'yang berjalan. Ini BUKAN lulus dan BUKAN gagal: belum ada yang diverifikasi.')
    elif status == 'PASS_FLAKY':
        head = f'✅ PP#{ticket_id} **PASS (flaky)** - lulus setelah retry.'
    elif status == 'PASS':
        head = f'✅ PP#{ticket_id} **PASS**.'
    else:
        head = f'❌ PP#{ticket_id} **FAIL**.'

    if failed_ac:
        head += f'\nAC gagal: {", ".join(failed_ac)}'
    if note:
        head += f'\nCatatan: {note}'
    return head


def run_action(ticket_id: int, action: str, token: str) -> dict:
    if action == 'cleanup':
        proc = subprocess.run(
            ['python', str(CLEANUP), '--id', str(ticket_id)],
            cwd=REPO, capture_output=True, text=True, timeout=60,
        )
        return {'ok': proc.returncode == 0, 'stdout': proc.stdout[-500:], 'stderr': proc.stderr[-500:]}

    if action == 'status':
        report_path = REPO.parent / 'reports' / f'wp-{ticket_id}-ui-verify.json'
        if not report_path.exists():
            return {'ok': False, 'stdout': f'Tidak ada report untuk PP#{ticket_id}.'}
        return {'ok': True, 'stdout': report_path.read_text(encoding='utf-8')}

    subject = fetch_subject(ticket_id)
    slug = slugify(subject)
    ac = fetch_ac(ticket_id)
    if not ac:
        return {'ok': False, 'stdout': 'AC kosong, tidak bisa generate spec.'}

    # Generate test code using AI
    try:
        ai_response = generate_ai_test_code(ticket_id, subject, ac)
        test_code = parse_ai_test_code(ai_response)
    except Exception as e:
        return {'ok': False, 'stdout': f'AI generation failed: {e}'}
    
    # Save generated spec
    spec_name = f'wp-{ticket_id}-{slug}.spec.ts'
    spec_path = REPO / 'specs' / 'generated' / spec_name
    
    # Remove imports from AI response if any
    test_code_body = "\n".join([line for line in test_code.split("\n") if not line.lstrip().startswith('import ')])
    
    full_spec = f"""import {{ test, expect }} from '@playwright/test';
import {{ loginAsTimMedinesia }} from '../../utils/loginUtils';

test.describe('PP#{ticket_id} - AI Generated', () => {{
  test.beforeEach(async ({{ page }}) => {{
    await loginAsTimMedinesia(page);
  }});

{test_code_body}
}});
"""
    spec_path.write_text(full_spec, encoding='utf-8')

    # Eksekusi lewat runner.py, JANGAN duplikasi logikanya di sini.
    # runner.py yang memegang: retry satu lapisan, parse results.json (AC mana yang gagal),
    # guard NOT_VERIFIED kalau tidak ada test yang jalan, tulis report + history.jsonl.
    # Sebelumnya jalur Discord memakai step_run_spec() inline, jadi semua guard itu
    # TIDAK berlaku justru di jalur yang paling sering dipakai.
    proc = subprocess.run(
        ['python', str(RUNNER), '--id', str(ticket_id), '--slug', slug,
         '--skip-generate', '--no-comment'],
        cwd=REPO, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=300,
    )

    try:
        report = json.loads(proc.stdout)
    except ValueError:
        return {
            'ok': False,
            'stdout': f'runner.py tidak mengembalikan JSON (rc={proc.returncode}).',
            'stderr': proc.stderr[-800:],
            'spec_name': spec_name,
            'screenshot_path': None,
        }

    status = report.get('final_status', 'FAIL')
    results = report.get('results') or {}

    screenshot_path = None
    if status != 'PASS':
        test_results_dir = REPO / 'test-results'
        if test_results_dir.exists():
            screenshots = list(test_results_dir.glob(f'**/wp-{ticket_id}-*.png'))
            if screenshots:
                screenshot_path = str(screenshots[0])

    # Hanya PASS dan PASS_FLAKY yang boleh lanjut ke approval gate.
    # NOT_VERIFIED (spec tidak menghasilkan test) bukan lulus.
    return {
        'ok': status in ('PASS', 'PASS_FLAKY'),
        'status': status,
        'stdout': json.dumps(report, indent=2, ensure_ascii=False)[:1800],
        'stderr': proc.stderr[-800:],
        'spec_name': spec_name,
        'screenshot_path': screenshot_path,
        'failed_ac': results.get('failed_ac', []),
        'flaky_note': report.get('flaky_note', ''),
    }


def post_draft_to_op(ticket_id: int, report_text: str, screenshot_path: str = None) -> None:
    import urllib.request
    import urllib.error
    token = env_required('OP_API_TOKEN')
    body = (
        f"**UI Verify (auto bot)** — PP#{ticket_id}\n\n"
        f"```json\n{report_text[:1500]}\n```\n"
    )
    if screenshot_path:
        body += f"\n📸 Screenshot: `{screenshot_path}`\n"
    body += f"\n<@{KIBUL_ID}> — reply `lanjut` / `reject` di thread ini."
    url = f'{OP_BASE_URL}/api/v3/work_packages/{ticket_id}/activities'
    req = urllib.request.Request(
        url,
        data=json.dumps({'comment': {'raw': body}}).encode('utf-8'),
        headers={'Authorization': get_op_auth_header(token), 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        urllib.request.urlopen(req, timeout=15).read()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError('Token invalid (401). Minta token baru.')


class TransitionError(Exception):
    """Custom exception for transition failures."""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

def transition_ticket(ticket_id: int, new_status_id: str) -> None:
    import urllib.request
    import urllib.error
    if str(new_status_id) not in ALLOWED_STATUS_IDS:
        raise TransitionError(
            f'Status id {new_status_id} di luar whitelist QA {sorted(ALLOWED_STATUS_IDS)}. '
            f'Transisi ditolak (14=Rejected / 12=Closed bukan wewenang QA).'
        )
    token = env_required('OP_API_TOKEN')
    url = f'{OP_BASE_URL}/api/v3/work_packages/{ticket_id}'
    
    # Fetch current lockVersion
    req_get = urllib.request.Request(url, headers={'Authorization': get_op_auth_header(token)})
    try:
        with urllib.request.urlopen(req_get, timeout=15) as resp:
            wp_data = json.loads(resp.read())
            lock_version = wp_data.get('lockVersion', 0)
    except urllib.error.HTTPError as e:
        raise TransitionError(f"Gagal GET lockVersion: {e.read().decode('utf-8')}", code=e.code)

    payload = json.dumps({'lockVersion': lock_version, '_links': {'status': {'href': f'/api/v3/statuses/{new_status_id}'}}}).encode('utf-8')
    req = urllib.request.Request(
        url, data=payload,
        headers={'Authorization': get_op_auth_header(token), 'Content-Type': 'application/json'},
        method='PATCH',
    )
    try:
        urllib.request.urlopen(req, timeout=15).read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        if e.code == 401:
            raise TransitionError('Token invalid (401). Minta token baru.', code=401)
        elif e.code in (409, 422):
            raise TransitionError(f"Gagal transisi (kemungkinan race condition/validation): {error_body}", code=e.code)
        else:
            raise TransitionError(f"Error HTTP tidak diketahui: {error_body}", code=e.code)



class BotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f'✅ bot ready: {self.user} (ID: {self.user.id})', file=sys.stderr)
        for guild in self.guilds:
            await self.tree.sync(guild=guild)
            print(f'  guild: {guild.name} ({guild.id})', file=sys.stderr)
        print(f'✅ slash synced ke {len(self.guilds)} guild + global', file=sys.stderr)


bot = BotClient()


@bot.tree.command(name='automation', description='Trigger UI verify, status, atau cleanup tiket')
@app_commands.describe(
    ticket='Nomor tiket OpenProject (mis. 7434)',
    action='verify (default), status, cleanup',
)
async def automation_cmd(interaction: discord.Interaction, ticket: int, action: str = 'verify'):
    if action not in ('verify', 'status', 'cleanup'):
        await interaction.response.send_message(
            f'Action tidak valid: {action}. Gunakan verify/status/cleanup.', ephemeral=True
        )
        return

    with TicketLock(ticket) as lock:
        if not lock.acquired:
            await interaction.response.send_message(
                f'⏳ Pipeline PP#{ticket} sedang berjalan, skip duplicate trigger.',
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)
        token = env_required('OP_API_TOKEN')
        result = await asyncio.to_thread(run_action, ticket, action, token)

        if action == 'verify' and result['ok']:
            try:
                post_draft_to_op(ticket, result['stdout'], result.get('screenshot_path'))
                await interaction.followup.send(
                    f'✅ PP#{ticket} verify selesai. Draft komentar posted. Tag <@{KIBUL_ID}>.'
                )
            except Exception as e:
                await interaction.followup.send(f'Run selesai tapi post OP gagal: {e}')
        elif action == 'verify' and not result['ok']:
            files = []
            if result.get('screenshot_path') and Path(result['screenshot_path']).exists():
                files.append(discord.File(result['screenshot_path']))
            await interaction.followup.send(fmt_result(ticket, result), files=files)
        elif action == 'cleanup':
            try:
                cleanup_data = json.loads(result['stdout'])
                total_files = (
                    len(cleanup_data.get('specs', [])) +
                    len(cleanup_data.get('reports', [])) +
                    len(cleanup_data.get('screenshots', []))
                )
                await interaction.followup.send(
                    f'🧹 Cleanup PP#{ticket} selesai. {total_files} files deleted:\n'
                    f"```json\n{result['stdout']}\n```"
                )
            except Exception:
                await interaction.followup.send(f'Cleanup PP#{ticket}:\n{result["stdout"]}')
        else:
            await interaction.followup.send(
                f'❌ PP#{ticket} {action} gagal.\n```\n{result["stderr"][-500:]}\n```'
            )


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.content.startswith('!ui '):
        parts = message.content[4:].strip().split()
        if not parts or not parts[0].isdigit():
            return
        ticket_id = int(parts[0])
        action = parts[1] if len(parts) > 1 else 'verify'

        with TicketLock(ticket_id) as lock:
            if not lock.acquired:
                await message.channel.send(
                    f'⏳ Pipeline PP#{ticket_id} sedang berjalan, skip duplicate trigger.'
                )
                return

            await message.channel.send(f'⏳ PP#{ticket_id} {action} mulai...')
            token = env_required('OP_API_TOKEN')
            result = await asyncio.to_thread(run_action, ticket_id, action, token)
            if action == 'verify' and result['ok']:
                try:
                    post_draft_to_op(ticket_id, result['stdout'], result.get('screenshot_path'))
                    await message.channel.send(
                        f'✅ PP#{ticket_id} done. Draft posted. Tag <@{KIBUL_ID}>.'
                    )
                except Exception as e:
                    await message.channel.send(f'Run ok tapi post OP gagal: {e}')
            elif action == 'verify' and not result['ok']:
                files = []
                if result.get('screenshot_path') and Path(result['screenshot_path']).exists():
                    files.append(discord.File(result['screenshot_path']))
                await message.channel.send(fmt_result(ticket_id, result), files=files)
            elif action == 'cleanup':
                try:
                    cleanup_data = json.loads(result['stdout'])
                    total_files = (
                        len(cleanup_data.get('specs', [])) +
                        len(cleanup_data.get('reports', [])) +
                        len(cleanup_data.get('screenshots', []))
                    )
                    await message.channel.send(
                        f'🧹 Cleanup PP#{ticket_id} selesai. {total_files} files deleted:\n'
                        f"```json\n{result['stdout']}\n```"
                    )
                except Exception:
                    await message.channel.send(f'Cleanup PP#{ticket_id}:\n{result["stdout"]}')
            else:
                await message.channel.send(
                    f'❌ PP#{ticket_id} {action}: {result["stdout"][-500:] or result["stderr"][-500:]}'
                )
        return

    pp_match = PP_REGEX.search(message.content)
    if not pp_match:
        return
    approve_match = APPROVE_REGEX.match(message.content.strip())
    if not approve_match:
        return

    if str(message.author.id) != KIBUL_ID:
        return

    decision = approve_match.group(1).lower()
    ticket_id = int(pp_match.group(1))

    if decision == 'lanjut':
        try:
            target = os.environ.get('OP_PASS_STATUS_ID', STATUS_TESTED_DEV)
            transition_ticket(ticket_id, target)
            await message.channel.send(
                f'✅ PP#{ticket_id} transisi ke status {target} (Tested Dev) — approved by Kibul.'
            )
        except TransitionError as e:
            if e.code in (409, 422):
                await message.channel.send(
                    f'⚠️ Transisi PP#{ticket_id} gagal (kemungkinan sudah diupdate atau ada validasi). '
                    f'Cek manual di OpenProject.'
                )
            else:
                await message.channel.send(f'❌ Transisi PP#{ticket_id} gagal: {e}')
        except Exception as e:
            await message.channel.send(f'❌ Transisi PP#{ticket_id} gagal (error tidak diketahui): {e}')
    else:
        # AGENTS.md 9.3: reject = TIDAK ada transisi status, hanya hold + alasan.
        await message.channel.send(
            f'⏸ PP#{ticket_id} hold per Kibul — tidak ada transisi status. '
            f'Tambahkan alasan di tiket bila perlu.'
        )


def parse_ai_test_code(message_content: str) -> str:
    """
    Extract TypeScript test code from AI response.
    Expects format: ```typescript ... ```
    """
    import re
    pattern = r'```(?:typescript|ts)\n(.*?)\n```'
    match = re.search(pattern, message_content, re.DOTALL)
    if not match:
        raise ValueError('No TypeScript code block found in AI response')
    return match.group(1).strip()

# step_run_spec() dihapus: duplikat dari runner.py step_run().
# Jalur Discord sekarang memanggil runner.py supaya retry policy, parse results.json,
# guard NOT_VERIFIED, dan history.jsonl berlaku sama di semua jalur.

# handle_ai_response() dihapus: dead code (tidak pernah dipanggil), duplikat dari
# run_action(), dan mengandung `else:` nyasar yang mematikan cabang reject.
# Alur AI-generate sekarang: run_action() -> generate_ai_test_code() -> runner.py.

# ---------- Webhook server (embedded) ----------

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        import hmac
        import hashlib

        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length)
        sig = self.headers.get('X-Hub-Signature-256', '').replace('sha256=', '')

        if WEBHOOK_SECRET:
            expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig):
                self.send_response(401)
                self.end_headers()
                return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        action = payload.get('action') or payload.get('event', '')
        wp = payload.get('work_package') or {}
        wp_id = wp.get('id') or payload.get('id')
        subject = wp.get('subject') or payload.get('subject', '')

        if not wp_id or action not in ('work_package:updated', 'work_package:created'):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true,"skipped":"no-id-or-event"}')
            return

        ticket_id = int(wp_id)
        try:
            ui_required = check_ui_flag(ticket_id)
        except RuntimeError as e:
            # Gagal cek != tidak ada keyword UI. Jangan diam-diam skip.
            print(f'[webhook] PP#{ticket_id} ac_parser error: {e}', file=sys.stderr)
            self.send_response(503)
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': 'ac_parser_failed'}).encode('utf-8'))
            return
        if not ui_required:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true,"skipped":"no-ui-keyword"}')
            return

        with TicketLock(ticket_id) as lock:
            if not lock.acquired:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok":true,"skipped":"in-flight"}')
                return

            result = run_action(ticket_id, 'verify', env_required('OP_API_TOKEN'))
            posted = None
            if result['ok']:
                try:
                    post_draft_to_op(ticket_id, result['stdout'])
                    posted = True
                except Exception as e:
                    posted = False
                    print(f'[webhook] PP#{ticket_id} post_draft_to_op gagal: {e}', file=sys.stderr)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'ok': result['ok'], 'posted': posted}).encode('utf-8'))


def start_webhook(port: int) -> None:
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    print(f'webhook listening on :{port}', file=sys.stderr)
    server.serve_forever()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--webhook-port', type=int, default=9090)
    args = p.parse_args()

    if not DISCORD_TOKEN:
        raise SystemExit('DISCORD_TOKEN missing')

    t = threading.Thread(target=start_webhook, args=(args.webhook_port,), daemon=True)
    t.start()

    bot.run(DISCORD_TOKEN)
    return 0


if __name__ == '__main__':
    sys.exit(main())
