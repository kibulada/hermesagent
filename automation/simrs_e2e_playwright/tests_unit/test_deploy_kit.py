"""
Guard untuk deployment kit VPS (deploy/ + integrations/mcp-servers/).

Kelas bug yang ditangkap di sini adalah bug yang HANYA muncul di Linux dan
diam-diam lolos di Windows, jadi tidak akan ketahuan dari menjalankan agent
di mesin lokal:

  - env var dibaca kode tapi tidak didokumentasikan di env.example -> di VPS
    nilainya kosong, get_token() mengembalikan None, API balas kosong, dan
    hasilnya terbaca seolah tiket tidak ada (false-green)
  - PLAYWRIGHT_BROWSERS_PATH beda antara bootstrap dan env.example -> browser
    dipasang di satu tempat, dicari di tempat lain
  - file MCP yang di-vendor hilang/berganti nama -> mcp_launcher.py mati
  - dua unit systemd sama-sama bind :9090
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
DEPLOY = REPO / 'deploy'
SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
VENDORED = REPO / 'integrations' / 'mcp-servers'

ENV_EXAMPLE = DEPLOY / 'env.example'
BOOTSTRAP = DEPLOY / 'bootstrap_vps.sh'
PREFLIGHT = DEPLOY / 'preflight.sh'


def _env_example_keys() -> set:
    return {
        m.group(1)
        for m in re.finditer(r'^([A-Z][A-Z0-9_]*)=', ENV_EXAMPLE.read_text(encoding='utf-8'), re.M)
    }


# --- kelengkapan dokumentasi env --------------------------------------------

# Var yang sengaja TIDAK ada di env.example, dengan alasannya.
ENV_EXEMPT = {
    # dimuat playwright.config.ts lewat dotenv dari .env.staging, bukan systemd
    'STAGING_BASE_URL', 'STAGING_TEST_USERNAME',
    'STAGING_TEST_PASSWORD', 'STAGING_TEST_TENANT',
    # hanya ada di Windows; di Linux justru harus kosong
    'LOCALAPPDATA',
    # var standar POSIX, bukan konfigurasi agent
    'HOME', 'PATH', 'CI',
    # Disuntik mcp_launcher.py ke os.environ subprocess, BUKAN diisi operator.
    # TOKEN_MAP menerjemahkan OP_API_TOKEN -> OPENPROJECT_API_KEY dan
    # OP_BASE_URL -> OPENPROJECT_URL. Yang diisi di hermes-qa.env adalah nama
    # sisi kiri. GitLab tidak muncul di sini karena kebetulan memakai nama yang
    # sama di kedua sisi (GITLAB_TOKEN / GITLAB_URL).
    'OPENPROJECT_API_KEY', 'OPENPROJECT_URL',
}


def test_semua_env_var_terdokumentasi():
    """Tiap env var yang dibaca kode harus punya baris di env.example."""
    pola = re.compile(r"""(?:get_token|os\.environ\.get)\(\s*['"]([A-Z][A-Z0-9_]*)['"]""")
    dipakai = set()
    for src in list(SCRIPTS.glob('*.py')) + [REPO / 'integrations' / 'mcp_launcher.py'] + list(VENDORED.glob('*.py')):
        dipakai |= set(pola.findall(src.read_text(encoding='utf-8')))

    hilang = dipakai - _env_example_keys() - ENV_EXEMPT
    assert not hilang, (
        f'env var dibaca kode tapi tidak ada di deploy/env.example: {sorted(hilang)}. '
        'Di VPS nilainya akan kosong tanpa error.'
    )


def test_env_example_tidak_berisi_nilai_asli():
    """env.example wajib placeholder. Nilai asli di sini = insiden kredensial."""
    teks = ENV_EXAMPLE.read_text(encoding='utf-8')
    for pola in (r'glpat-[A-Za-z0-9_-]{8,}', r'sk-[A-Za-z0-9]{16,}', r'ghp_[A-Za-z0-9]{20,}'):
        assert not re.search(pola, teks), f'kredensial asli bocor ke env.example: pola {pola}'
    # token panjang di sisi kanan '=' juga mencurigakan
    for baris in teks.splitlines():
        m = re.match(r'^[A-Z][A-Z0-9_]*=(.+)$', baris)
        if m and not m.group(1).startswith(('http', '/', '<')):
            assert len(m.group(1)) < 25, f'nilai mencurigakan panjang di env.example: {baris.split("=")[0]}'


# --- konsistensi lintas file -------------------------------------------------

def test_playwright_browsers_path_konsisten():
    """Path browser di bootstrap harus sama dengan yang di env.example."""
    boot = BOOTSTRAP.read_text(encoding='utf-8')
    m = re.search(r'^PW_BROWSERS_REL="([^"]+)"', boot, re.M)
    assert m, 'PW_BROWSERS_REL tidak ditemukan di bootstrap_vps.sh'
    rel = m.group(1)

    m2 = re.search(r'^PLAYWRIGHT_BROWSERS_PATH=(\S+)', ENV_EXAMPLE.read_text(encoding='utf-8'), re.M)
    assert m2, 'PLAYWRIGHT_BROWSERS_PATH tidak ada di env.example'
    assert m2.group(1).endswith(rel), (
        f'env.example menunjuk {m2.group(1)} tapi bootstrap memasang ke .../{rel} — '
        'browser akan dipasang di satu tempat dan dicari di tempat lain'
    )


def test_browser_tidak_ditaruh_di_home():
    """ProtectHome=true bikin ~/.cache tidak terjangkau service."""
    m = re.search(r'^PLAYWRIGHT_BROWSERS_PATH=(\S+)', ENV_EXAMPLE.read_text(encoding='utf-8'), re.M)
    assert not m.group(1).startswith(('~', '/home', '/root')), (
        'browser tidak boleh di home directory: unit systemd memakai ProtectHome=true'
    )


# --- file MCP yang di-vendor -------------------------------------------------

def test_mcp_vendored_sesuai_ekspektasi_launcher():
    """Nama file di integrations/mcp-servers/ harus cocok dengan SERVERS spec."""
    launcher = (REPO / 'integrations' / 'mcp_launcher.py').read_text(encoding='utf-8')
    diminta = set(re.findall(r"'script'\s*:\s*'([^']+)'", launcher))
    assert diminta, 'tidak bisa membaca daftar script dari mcp_launcher.py'
    for nama in diminta:
        assert (VENDORED / nama).is_file(), (
            f'{nama} diminta mcp_launcher.py tapi tidak ada di integrations/mcp-servers/'
        )


@pytest.mark.parametrize('nama', sorted(p.name for p in VENDORED.glob('*.py')))
def test_mcp_vendored_bersih_dan_valid(nama):
    """Vendored script harus compile dan tidak membawa kredensial literal."""
    import py_compile
    src = VENDORED / nama
    py_compile.compile(str(src), doraise=True)
    teks = src.read_text(encoding='utf-8')
    for pola in (r'glpat-[A-Za-z0-9_-]{8,}', r'sk-[A-Za-z0-9]{16,}',
                 r'''(?i)(token|api_key|password)\s*=\s*["'][^"'\s]{12,}["']'''):
        assert not re.search(pola, teks), f'{nama}: kredensial literal, pola {pola}'


# --- unit systemd ------------------------------------------------------------

def test_hanya_satu_unit_boleh_bind_port_yang_sama():
    """discord_bot.py sudah menjalankan webhook di :9090 (discord_bot.py:689)."""
    units = sorted((DEPLOY / 'systemd').glob('*.service'))
    assert len(units) == 2, f'diharapkan 2 unit, ada {len(units)}'
    pemakai_9090 = [u for u in units if '9090' in u.read_text(encoding='utf-8')]
    assert len(pemakai_9090) == 2, 'asumsi berubah: tidak semua unit memakai :9090'
    gabungan = ' '.join(u.read_text(encoding='utf-8') for u in units)
    assert 'Conflicts=' in gabungan, (
        'dua unit sama-sama bind :9090 tapi tidak ada Conflicts= — '
        'mengaktifkan keduanya membuat salah satu gagal bind'
    )


@pytest.mark.parametrize('unit', sorted((DEPLOY / 'systemd').glob('*.service')))
def test_unit_systemd_valid(unit):
    """Section wajib ada, dan tidak jalan sebagai root."""
    import configparser
    c = configparser.ConfigParser(strict=False)
    c.optionxform = str
    c.read(unit, encoding='utf-8')
    assert {'Unit', 'Service', 'Install'} <= set(c.sections()), f'{unit.name}: section kurang'
    assert c['Service'].get('User') not in (None, 'root'), f'{unit.name}: tidak boleh jalan sebagai root'
    assert c['Service'].get('EnvironmentFile'), f'{unit.name}: EnvironmentFile wajib'
    # StartLimit* milik [Unit] sejak systemd 229; di [Service] diabaikan diam-diam.
    for k in ('StartLimitBurst', 'StartLimitIntervalSec'):
        assert k not in c['Service'], f'{unit.name}: {k} salah section, harus di [Unit]'


# --- script shell ------------------------------------------------------------

@pytest.mark.parametrize('sh', [BOOTSTRAP, PREFLIGHT])
def test_shell_script_punya_shebang_dan_strict_mode(sh):
    baris = sh.read_text(encoding='utf-8').splitlines()
    assert baris[0].startswith('#!'), f'{sh.name}: tidak ada shebang'
    isi = '\n'.join(baris)
    assert re.search(r'^set -[euo]', isi, re.M), f'{sh.name}: tidak memakai strict mode'


def test_bootstrap_tidak_menimpa_secret():
    """Idempoten: file kredensial yang sudah ada tidak boleh ditimpa."""
    isi = BOOTSTRAP.read_text(encoding='utf-8')
    assert 'sudah ada - TIDAK ditimpa' in isi, 'guard anti-timpa hermes-qa.env hilang'


def test_preflight_gagal_dengan_exit_nonzero():
    """Gate harus benar-benar memblokir, bukan sekadar mencetak peringatan."""
    isi = PREFLIGHT.read_text(encoding='utf-8')
    assert re.search(r'FAIL > 0', isi) and 'exit 1' in isi, (
        'preflight harus exit 1 kalau ada gate gagal'
    )
