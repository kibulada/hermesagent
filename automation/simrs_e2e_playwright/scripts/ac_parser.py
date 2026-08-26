#!/usr/bin/env python3
"""
AC Parser — scan deskripsi tiket OpenProject untuk keyword UI.
Sesuai AGENTS.md §9.1.

Usage:
    python scripts/ac_parser.py --text "<deskripsi tiket>"
    python scripts/ac_parser.py --openproject --id 7434

Output JSON:
    {"ui_verify_required": bool, "matched_keywords": [...], "ticket_id": int|null}
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hermes_config import get_token  # noqa: E402

UI_KEYWORDS = (
    r'button|tombol|form|input|modal|popup|page|halaman|tab|menu|dropdown|'
    r'tabel|table|render|tampilan|layout|loading|empty state|validation|'
    r'klik|click|submit|select|datepicker|autocomplete'
)
UI_REGEX = re.compile(rf'\b({UI_KEYWORDS})\b', re.IGNORECASE)


def strip_html(text: str) -> str:
    """
    Buang markup sebelum matching keyword.

    Deskripsi OpenProject dikirim sebagai HTML. Tanpa ini, `class="op-uc-table"`
    menghasilkan match untuk keyword `table`, dan tiket tanpa elemen UI apa pun
    ikut lolos gate. Terukur di WP 7489: 9 dari 12 match `table` berasal dari
    nama class, bukan dari teks AC.
    """
    if not text:
        return ''
    # buang blok yang isinya bukan teks yang dibaca manusia
    text = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', text, flags=re.S | re.I)
    # buang seluruh tag beserta atributnya (class="op-uc-table" ikut hilang di sini)
    text = re.sub(r'<[^>]+>', ' ', text)
    # decode entity (&quot; &amp; &gt; &nbsp; dst)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_text(text: str, ticket_id: Optional[int] = None) -> dict:
    clean = strip_html(text)
    matches = sorted(set(m.group(0).lower() for m in UI_REGEX.finditer(clean)))
    return {
        'ui_verify_required': bool(matches),
        'matched_keywords': matches,
        'ticket_id': ticket_id,
    }


def fetch_openproject(ticket_id: int) -> str:
    """Fetch deskripsi tiket dari OpenProject. Memerlukan OP_API_TOKEN env."""
    import os
    import urllib.request
    import urllib.error
    import base64

    base = get_token('OP_BASE_URL') or 'https://tracker.kesia.id'
    token = get_token('OP_API_TOKEN')
    if not token:
        raise SystemExit('OP_API_TOKEN missing')

    auth_header = f'Basic {base64.b64encode(f"apikey:{token}".encode()).decode()}'
    url = f'{base}/api/v3/work_packages/{ticket_id}'
    req = urllib.request.Request(url, headers={'Authorization': auth_header})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise SystemExit('Token invalid (401). Minta token baru.')
        raise

    desc = data.get('description', {}) or {}
    if isinstance(desc, dict):
        return desc.get('raw', '') or desc.get('html', '')
    return str(desc)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--text', help='Deskripsi tiket langsung')
    p.add_argument('--openproject', action='store_true', help='Fetch dari OP')
    p.add_argument('--id', type=int, help='Work package ID')
    args = p.parse_args()

    if not args.text and not (args.openproject and args.id):
        p.error('Butuh --text atau --openproject --id <id>')

    if args.openproject:
        text = fetch_openproject(args.id)
        ticket_id = args.id
    else:
        text = args.text
        ticket_id = None

    result = parse_text(text, ticket_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
