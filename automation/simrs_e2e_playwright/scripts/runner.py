#!/usr/bin/env python3
"""
runner.py — orchestrator Full-Auto UI Verify.
Sesuai AGENTS.md §9.2 [3]-[6].

Usage:
    python scripts/runner.py --id 7434 --slug fix-menu-perawat
    python scripts/runner.py --id 7434 --slug fix-menu-perawat --skip-generate

Output:
    JSON report ke stdout + tulis ke reports/wp-<id>-ui-verify.json
    Post komentar DRAFT ke OpenProject (tidak transition).
    Tag @Kibul, tunggu approval eksplisit.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GENERATED_DIR = REPO / 'specs' / 'generated'
REPORTS_DIR = REPO.parent / 'reports'
TIMEOUT = 120
RETRY_DELAY = 5

sys.path.insert(0, str(REPO / 'scripts'))
from hermes_config import get_token  # noqa: E402


def env(name: str) -> str:
    val = os.environ.get(name) or get_token(name)
    if not val:
        raise SystemExit(f'Environment {name} missing')
    return val


def run_subprocess(cmd: list, cwd: Path, timeout: int = TIMEOUT) -> dict:
    """Run shell command, return {returncode, stdout, stderr}. Silent on stdout to avoid log leak."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            env={**os.environ, 'CI': '1'},
        )
        return {
            'returncode': proc.returncode,
            'stdout': proc.stdout[-2000:],  # truncate tail
            'stderr': proc.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {'returncode': 124, 'stdout': '', 'stderr': f'Timeout after {timeout}s'}


def parse_results(results_path: Path) -> dict:
    """
    Baca test-results/results.json dari Playwright JSON reporter.
    Exit code cuma bilang "ada yang gagal"; ini bilang AC mana yang gagal.
    Return {'total','passed','failed','failed_tests':[...], 'failed_ac':[...]}.
    """
    summary = {'total': 0, 'passed': 0, 'failed': 0, 'failed_tests': [], 'failed_ac': [],
               'parsed': False, 'errors': []}
    if not results_path.exists():
        return summary

    try:
        data = json.loads(results_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return summary

    def walk(suite):
        for spec in suite.get('specs', []) or []:
            title = spec.get('title', '')
            ok = spec.get('ok', False)
            summary['total'] += 1
            if ok:
                summary['passed'] += 1
            else:
                summary['failed'] += 1
                summary['failed_tests'].append(title)
                for ac in re.findall(r'\bAC#?(\d+)', title):
                    summary['failed_ac'].append(f'AC{ac}')
        for child in suite.get('suites', []) or []:
            walk(child)

    for suite in data.get('suites', []) or []:
        walk(suite)
    summary['failed_ac'] = sorted(set(summary['failed_ac']))
    summary['errors'] = [e.get('message', '') for e in (data.get('errors') or [])]
    summary['parsed'] = True
    return summary


def append_history(report: dict, duration_s: float) -> None:
    """Satu baris per run di reports/history.jsonl -> bahan flake rate & metrik sprint."""
    entry = {
        'ticket_id': report['ticket_id'],
        'spec': report['spec_name'],
        'status': report['final_status'],
        'duration_s': round(duration_s, 1),
        'failed_ac': report.get('results', {}).get('failed_ac', []),
        'failed_tests': report.get('results', {}).get('failed_tests', []),
    }
    path = REPORTS_DIR / 'history.jsonl'
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def step_generate(ticket_id: int, slug: str, ac_text: str) -> str:
    """Generate Playwright spec skeleton via spec_generator.ts."""
    spec_path = GENERATED_DIR / f'wp-{ticket_id}-{slug}.spec.ts'
    if spec_path.exists():
        return str(spec_path)

    NPX = 'npx.cmd' if os.name == 'nt' else 'npx'
    cmd = [
        NPX, 'tsx',
        str(REPO / 'scripts' / 'spec_generator.ts'),
        '--id', str(ticket_id),
        '--slug', slug,
        '--ac-stdin',
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        input=ac_text,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f'spec_generator failed: {proc.stderr[-500:]}')
    return proc.stdout.strip()


def step_run(spec_name: str) -> dict:
    """Run Playwright test. Returns {returncode, stdout, stderr, summary}."""
    NPX = 'npx.cmd' if os.name == 'nt' else 'npx'
    spec_rel = f'specs/generated/{spec_name}'
    # --retries=0: retry ditangani di sini (step 3 main()), bukan oleh Playwright.
    # Tanpa ini CI=1 mengaktifkan retries:2 di playwright.config.ts -> total 6 percobaan
    # dan label PASS_FLAKY jadi menyesatkan.
    cmd = [NPX, 'playwright', 'test', '--project=chromium', '--retries=0', spec_rel]
    return run_subprocess(cmd, cwd=REPO)


def _fmt_failed(report: dict) -> str:
    res = report.get('results') or {}
    if not res.get('parsed'):
        return '- Hasil terstruktur: tidak tersedia (results.json tidak terbaca)\n'
    total, passed = res.get('total', 0), res.get('passed', 0)
    if not res.get('failed'):
        return f'- Test: {passed}/{total} lulus\n'
    parts = [f'- Test: {passed}/{total} lulus\n']
    if res.get('failed_ac'):
        parts.append('- AC gagal: ' + ', '.join(res['failed_ac']) + '\n')
    for t in res.get('failed_tests', [])[:5]:
        parts.append('  - ' + str(t) + '\n')
    return ''.join(parts)


def post_draft_comment(ticket_id: int, report: dict, token: str) -> None:
    """Post draft komentar ke OpenProject. TIDAK transisi status."""
    import urllib.request
    import urllib.error
    import base64

    base = get_token('OP_BASE_URL') or 'https://tracker.kesia.id'
    auth_header = f'Basic {base64.b64encode(f"apikey:{token}".encode()).decode()}'

    status = report['final_status']
    note = report.get('flaky_note', '')
    body = (
        f"**UI Verify (auto)** — PP#{ticket_id}\n\n"
        f"- Run 1: {report['run1']['returncode']}\n"
        f"- Run 2: {report['run2']['returncode'] if report['run2'] else 'skipped'}\n"
        f"- Final: **{status}**\n"
        f"- Spec: `specs/generated/{report['spec_name']}`\n"
        f"{_fmt_failed(report)}"
        f"{f'- Note: {note}' if note else ''}\n\n"
        f"@Kibul — reply `lanjut` untuk approve transisi, `reject` untuk hold."
    )

    url = f'{base}/api/v3/work_packages/{ticket_id}/activities'
    req = urllib.request.Request(
        url,
        data=json.dumps({'comment': {'raw': body}}).encode('utf-8'),
        headers={
            'Authorization': auth_header,
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        urllib.request.urlopen(req, timeout=15).read()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise SystemExit('Token invalid (401). Minta token baru.')
        raise


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--id', type=int, required=True, help='OpenProject work_package id')
    p.add_argument('--slug', required=True, help='kebab-case slug untuk spec filename')
    p.add_argument('--skip-generate', action='store_true', help='Skip jika spec sudah ada')
    p.add_argument('--ac-text', default='', help='AC text (opsional, kalau tidak di-generate dari OP)')
    p.add_argument('--no-comment', action='store_true',
                   help='Jalankan + tulis report, tapi JANGAN post komentar ke OpenProject. '
                        'Dipakai discord_bot.py yang posting sendiri (dengan screenshot + mention).')
    p.add_argument('--token', default='',
                   help='OpenProject API token. Kosongkan supaya diambil dari env/config '
                        '(argumen CLI terlihat di process table).')
    args = p.parse_args()

    token = '' if args.no_comment else (args.token or (get_token('OP_API_TOKEN') or ''))
    started = time.monotonic()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate spec
    spec_path = ''
    if not args.skip_generate:
        if not args.ac_text:
            raise SystemExit('--ac-text required kalau tidak --skip-generate')
        spec_path = step_generate(args.id, args.slug, args.ac_text)
    spec_name = f'wp-{args.id}-{args.slug}.spec.ts'

    # 2. Run 1
    run1 = step_run(spec_name)

    report = {
        'ticket_id': args.id,
        'spec_name': spec_name,
        'spec_path': spec_path,
        'run1': run1,
        'run2': None,
        'final_status': 'PASS',
        'flaky_note': '',
    }

    # 3. Retry policy
    if run1['returncode'] == 0:
        report['final_status'] = 'PASS'
    else:
        time.sleep(RETRY_DELAY)
        run2 = step_run(spec_name)
        report['run2'] = run2
        if run2['returncode'] == 0:
            report['final_status'] = 'PASS_FLAKY'
            report['flaky_note'] = 'flaky detected — pass setelah retry'
        else:
            report['final_status'] = 'FAIL'

    # 3b. Baca hasil terstruktur: AC mana yang gagal, bukan sekadar exit code
    res = parse_results(REPO / 'test-results' / 'results.json')
    report['results'] = res
    if report['final_status'].startswith('PASS') and res['parsed']:
        if res['failed']:
            # Exit code 0 tapi ada spec gagal -> jangan pernah lapor PASS.
            report['final_status'] = 'FAIL'
            report['flaky_note'] = 'exit code 0 tapi results.json melaporkan kegagalan'
        elif res['total'] == 0:
            # Spec tidak ter-load / tidak ada test yang jalan. Nol test != lulus.
            report['final_status'] = 'NOT_VERIFIED'
            detail = res['errors'][0][:200] if res['errors'] else 'tidak ada test yang dijalankan'
            report['flaky_note'] = f'spec tidak menghasilkan test: {detail}'
    elif report['final_status'].startswith('PASS') and not res['parsed']:
        report['final_status'] = 'NOT_VERIFIED'
        report['flaky_note'] = 'results.json tidak terbaca - hasil tidak bisa diverifikasi'

    # 3c. Catat ke history untuk flake rate & metrik sprint
    try:
        append_history(report, time.monotonic() - started)
    except OSError as e:
        print(f'Gagal tulis history: {e}', file=sys.stderr)

    # 4. Write report
    report_path = REPORTS_DIR / f'wp-{args.id}-ui-verify.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')

    # 5. Post draft komentar (agent tidak transition status)
    if token:
        try:
            post_draft_comment(args.id, report, token)
        except SystemExit:
            raise
        except Exception as e:
            print(f'Gagal post komentar: {e}', file=sys.stderr)

    # 6. Output final ke stdout (untuk orchestrator)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
