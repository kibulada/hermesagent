#!/usr/bin/env python3
"""
webhook_server.py — listen webhook OpenProject, trigger pipeline UI Verify.
Sesuai AGENTS.md §9.2 (entrypoint).

Konfigurasi webhook di OP:
    URL:    https://<host>/webhook/openproject
    Events: work_package:updated (status transitions)
    Trigger: status berubah ke "In Review" (atau flag ui_verify_required)

Usage:
    python scripts/webhook_server.py --port 9090
    python scripts/webhook_server.py --config webhook.json

Env:
    WEBHOOK_SECRET: shared secret antara OP dan runner (opsional)
    OP_API_TOKEN: untuk fetch AC
    KIBUL_DISCORD_ID: 394740825260556288 (untuk tag @)
"""
import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNNER = REPO / 'scripts' / 'runner.py'
AC_PARSER = REPO / 'scripts' / 'ac_parser.py'
SECRET = os.environ.get('WEBHOOK_SECRET', '')
sys.path.insert(0, str(REPO / 'scripts'))
from lock import TicketLock  # noqa: E402
from hermes_config import get_token  # noqa: E402


def verify_signature(body: bytes, signature: str) -> bool:
    if not SECRET:
        return True
    expected = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def fetch_ac(ticket_id: int) -> str:
    import urllib.request
    import urllib.error
    import base64

    base = get_token('OP_BASE_URL') or os.environ.get('OP_BASE_URL', 'https://project.kesia.id')
    token = os.environ.get('OP_API_TOKEN') or get_token('OP_API_TOKEN')
    if not token:
        raise RuntimeError('OP_API_TOKEN missing')

    auth_header = f'Basic {base64.b64encode(f"apikey:{token}".encode()).decode()}'
    url = f'{base}/api/v3/work_packages/{ticket_id}'
    req = urllib.request.Request(url, headers={'Authorization': auth_header})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError('Token invalid (401).')
        raise

    desc = data.get('description', {}) or {}
    return desc.get('raw', '') or desc.get('html', '') or ''


def slugify(text: str) -> str:
    import re
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s[:50] or 'untitled'


def check_ui_flag(ticket_id: int) -> bool:
    """Return True kalau AC mengandung keyword UI."""
    try:
        proc = subprocess.run(
            ['python', str(AC_PARSER), '--openproject', '--id', str(ticket_id)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(f'ac_parser gagal (rc={proc.returncode}): {proc.stderr.strip()[-300:]}')
        data = json.loads(proc.stdout)
        return data.get('ui_verify_required', False)
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        raise RuntimeError(f'ac_parser tidak bisa dijalankan: {e}') from e


def trigger_pipeline(ticket_id: int, subject: str) -> dict:
    slug = slugify(subject)
    ac = fetch_ac(ticket_id)
    if not ac:
        return {'ok': False, 'reason': 'AC kosong'}

    proc = subprocess.run(
        ['python', str(RUNNER), '--id', str(ticket_id), '--slug', slug, '--ac-text', ac],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {
        'ok': proc.returncode == 0,
        'stdout_tail': proc.stdout[-500:],
        'stderr_tail': proc.stderr[-500:],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length)
        sig = self.headers.get('X-Hub-Signature-256', '').replace('sha256=', '')

        if not verify_signature(body, sig):
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

        if not wp_id:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true,"skipped":"no-id"}')
            return

        if action in ('work_package:updated', 'work_package:created'):
            if not check_ui_flag(int(wp_id)):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ok":true,"skipped":"no-ui-keyword"}')
                return

            with TicketLock(int(wp_id)) as lock:
                if not lock.acquired:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'{"ok":true,"skipped":"in-flight"}')
                    return

                result = trigger_pipeline(int(wp_id), subject)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok":true,"skipped":"event"}')


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=9090)
    args = p.parse_args()

    server = HTTPServer(('0.0.0.0', args.port), Handler)
    print(f'webhook listening on :{args.port}', file=sys.stderr)
    server.serve_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main())
