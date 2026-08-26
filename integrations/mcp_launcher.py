#!/usr/bin/env python3
"""
mcp_launcher.py — jembatan kredensial untuk server MCP.

Masalah yang diselesaikan:
    `.mcp.json` hanya bisa melakukan substitusi env var (`${OPENPROJECT_API_KEY}`).
    Token Hermes tidak ada di environment — adanya di `config.yaml`. Akibatnya server
    MCP jalan tanpa auth dan setiap query balik kosong, tanpa error yang jelas.

Cara kerja:
    Resolve token lewat `hermes_config.get_token()` (satu sumber kebenaran:
    `%LOCALAPPDATA%\\hermes\\config.yaml`, lalu `config/.env`), set ke os.environ,
    baru jalankan server MCP aslinya. Rahasia tidak pernah disalin ke file mana pun.

Penting: server MCP membaca env di TOP-LEVEL module
    (openproject_mcp.py:21-22, gitlab_mcp.py:23-24), jadi env wajib di-set
    SEBELUM modulnya dijalankan. Itu sebabnya pakai runpy, bukan import biasa.

Usage:
    python integrations/mcp_launcher.py openproject
    python integrations/mcp_launcher.py gitlab
    python integrations/mcp_launcher.py openproject --selftest   # cek token, tidak jalankan server

Semua diagnostik ditulis ke stderr. stdout milik protokol MCP — mencemarinya
akan merusak koneksi (pelajaran dari banner env yang merusak JSON reporter Playwright).
"""
import argparse
import os
import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / 'automation' / 'simrs_e2e_playwright' / 'scripts'))
from hermes_config import get_token  # noqa: E402

DEFAULT_MCP_DIR = Path(os.environ.get('LOCALAPPDATA', '')) / 'hermes' / 'mcp-servers'

# nama server -> (file server, {env var yang dibaca server: nama di hermes_config}, default url)
SERVERS = {
    'openproject': {
        'script': 'openproject_mcp.py',
        'env': {
            'OPENPROJECT_API_KEY': 'OP_API_TOKEN',
            'OPENPROJECT_URL': 'OP_BASE_URL',
        },
        'required': ('OPENPROJECT_API_KEY',),
        'fallback': {'OPENPROJECT_URL': 'https://tracker.kesia.id'},
    },
    'gitlab': {
        'script': 'gitlab_mcp.py',
        'env': {
            'GITLAB_TOKEN': 'GITLAB_TOKEN',
            'GITLAB_URL': 'GITLAB_URL',
        },
        'required': ('GITLAB_TOKEN',),
        'fallback': {'GITLAB_URL': 'https://gitlab.com'},
    },
}


def log(msg: str) -> None:
    """stderr saja — stdout milik protokol MCP."""
    print(f'[mcp_launcher] {msg}', file=sys.stderr)


def server_path(spec: dict) -> Path:
    override = os.environ.get('HERMES_MCP_DIR')
    base = Path(override) if override else DEFAULT_MCP_DIR
    return base / spec['script']


def resolve_env(name: str, spec: dict) -> dict:
    """Kembalikan {env_var: value} untuk server ini. Nilai tidak pernah di-log."""
    resolved = {}
    missing = []
    for env_var, token_name in spec['env'].items():
        value = get_token(token_name) or spec['fallback'].get(env_var)
        if value:
            resolved[env_var] = value
        elif env_var in spec['required']:
            missing.append(f'{env_var} (via {token_name})')

    if missing:
        raise SystemExit(
            f'[mcp_launcher] BLOCKER: kredensial untuk MCP "{name}" tidak bisa di-resolve: '
            f'{", ".join(missing)}.\n'
            f'  Cek urutan resolusi: os.environ -> %LOCALAPPDATA%\\hermes\\config.yaml '
            f'-> D:/Hermes-QA/config/.env\n'
            f'  Server sengaja TIDAK dijalankan - MCP tanpa auth mengembalikan hasil kosong '
            f'yang terbaca seolah tiket tidak ada.'
        )
    return resolved


def main() -> int:
    p = argparse.ArgumentParser(description='Jalankan server MCP dengan kredensial dari Hermes config.')
    p.add_argument('server', choices=sorted(SERVERS), help='server MCP yang dijalankan')
    p.add_argument('--selftest', action='store_true',
                   help='Cek resolusi token dan keberadaan file server, lalu keluar. Tidak menjalankan server.')
    args = p.parse_args()

    spec = SERVERS[args.server]
    target = server_path(spec)
    env = resolve_env(args.server, spec)

    if not target.exists():
        raise SystemExit(
            f'[mcp_launcher] BLOCKER: server MCP tidak ditemukan: {target}\n'
            f'  Set HERMES_MCP_DIR kalau lokasinya berbeda.'
        )

    if args.selftest:
        for env_var in sorted(spec['env']):
            if env_var in env:
                value = env[env_var]
                # URL boleh ditampilkan; token tidak — hanya panjangnya.
                shown = value if env_var.endswith('_URL') else f'<resolved, {len(value)} char>'
                log(f'OK   {env_var} = {shown}')
            else:
                log(f'SKIP {env_var} (opsional, tidak ter-resolve)')
        log(f'OK   server = {target}')
        log('selftest lulus - kredensial siap, server tidak dijalankan.')
        return 0

    os.environ.update(env)
    log(f'menjalankan {target.name} ({len(env)} env var ter-set)')
    runpy.run_path(str(target), run_name='__main__')
    return 0


if __name__ == '__main__':
    sys.exit(main())
