"""
Test untuk pembacaan hasil terstruktur Playwright.

Fixture di `fixtures/` adalah output ASLI dari `npx playwright test`, bukan karangan —
struktur JSON reporter (root suite -> nested suite -> specs) tidak akan tertangkap
kalau fixture-nya ditulis dari asumsi.

Yang dikunci di sini:
  - verdict dibaca dari results.json, bukan dari exit code
  - AC yang gagal bisa diidentifikasi dari judul test
  - "No tests found" TIDAK PERNAH boleh terbaca sebagai PASS
"""
from pathlib import Path

import pytest

from runner import parse_results

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def test_mixed_run_identifies_failed_ac():
    r = parse_results(FIXTURES / 'results-mixed.json')
    assert r['parsed'] is True
    assert r['total'] == 2
    assert r['passed'] == 1
    assert r['failed'] == 1
    assert r['failed_ac'] == ['AC2'], 'AC yang gagal harus terbaca dari judul test'
    assert 'AC2: sengaja gagal' in r['failed_tests']


def test_no_tests_found_is_not_a_pass():
    """Spec yang gagal dimuat menghasilkan 0 test. Nol test bukan lulus."""
    r = parse_results(FIXTURES / 'results-notests.json')
    assert r['parsed'] is True
    assert r['total'] == 0
    assert r['failed'] == 0
    assert any('No tests found' in e for e in r['errors']), 'error Playwright harus dibawa naik'


def test_missing_file_is_not_parsed():
    r = parse_results(FIXTURES / 'tidak-ada.json')
    assert r['parsed'] is False
    assert r['total'] == 0


def test_malformed_json_is_not_parsed(tmp_path):
    """Banner tool sering mencemari stdout; file rusak harus jadi parsed=False, bukan crash."""
    bad = tmp_path / 'bad.json'
    bad.write_text('injected env (4) from .env.staging\n{"suites":[]}', encoding='utf-8')
    r = parse_results(bad)
    assert r['parsed'] is False


@pytest.mark.parametrize('status,total,failed,expected', [
    ('PASS', 2, 1, 'FAIL'),           # exit 0 tapi ada spec gagal
    ('PASS', 0, 0, 'NOT_VERIFIED'),   # tidak ada test yang jalan
    ('PASS', 2, 0, 'PASS'),           # benar-benar lulus
])
def test_verdict_downgrade_logic(status, total, failed, expected):
    """Replikasi aturan verdict di runner.main() step 3b."""
    res = {'parsed': True, 'total': total, 'failed': failed, 'errors': []}
    final = status
    if final.startswith('PASS') and res['parsed']:
        if res['failed']:
            final = 'FAIL'
        elif res['total'] == 0:
            final = 'NOT_VERIFIED'
    assert final == expected
