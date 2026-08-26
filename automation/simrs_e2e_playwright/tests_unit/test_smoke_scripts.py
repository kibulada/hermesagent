"""
Smoke test untuk kode agent sendiri (bukan test aplikasi SIMRS).

Menangkap kelas bug yang pernah lolos ke produksi:
  - cleanup.py: `sys.exit()` tanpa `import sys` -> NameError tiap dipanggil
  - ac_parser.py: token resolver salah -> jalur webhook mati diam-diam
  - discord_bot.py: kredensial hardcode, status transisi salah
"""
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
PY_SCRIPTS = sorted(p.name for p in SCRIPTS.glob('*.py'))
CLI_SCRIPTS = ['ac_parser.py', 'cleanup.py', 'runner.py', 'webhook_server.py']


@pytest.mark.parametrize('name', PY_SCRIPTS)
def test_compiles(name):
    py_compile.compile(str(SCRIPTS / name), doraise=True)


@pytest.mark.parametrize('name', CLI_SCRIPTS)
def test_cli_help_exits_clean(name):
    """`--help` harus exit 0. Ini yang menangkap NameError di cleanup.py."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / name), '--help'],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, f'{name} --help rc={proc.returncode}: {proc.stderr[-400:]}'


def test_no_hardcoded_secrets():
    """Tidak boleh ada API key / password literal di source. AGENTS.md 9.5."""
    import re
    patterns = [
        re.compile(r"""['"]sk-[A-Za-z0-9_-]{16,}['"]"""),
        re.compile(r"""api_key\s*=\s*['"][^'"]{12,}['"]"""),
        re.compile(r"""password\s*=\s*['"][^'"<]{6,}['"]""", re.I),
    ]
    offenders = []
    for f in SCRIPTS.glob('*.py'):
        text = f.read_text(encoding='utf-8')
        for pat in patterns:
            for m in pat.finditer(text):
                line = text[:m.start()].count('\n') + 1
                offenders.append(f'{f.name}:{line} {m.group(0)[:40]}')
    assert not offenders, 'Kredensial hardcode ditemukan:\n' + '\n'.join(offenders)


def test_cleanup_real_invocation_exits_clean(tmp_path):
    """
    Reproduksi persis kegagalan produksi: `cleanup.py --id <n>` dulu selalu
    NameError karena `sys.exit(main())` tanpa `import sys`.
    Tiket 999999 tidak ada -> tidak ada file yang dihapus, aman dijalankan.
    """
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / 'cleanup.py'), '--id', '999999'],
        capture_output=True, text=True, timeout=60,
    )
    assert 'NameError' not in proc.stderr, proc.stderr[-400:]
    assert proc.returncode == 0, f'rc={proc.returncode}: {proc.stderr[-400:]}'
