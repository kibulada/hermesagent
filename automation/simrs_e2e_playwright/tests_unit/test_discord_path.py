"""
Kunci: jalur Discord harus lewat runner.py, bukan salinan logikanya sendiri.

Dulu `run_action()` memakai `step_run_spec()` inline dan menyimpulkan verdict dari
`returncode == 0` saja. Akibatnya semua guard di runner.py — retry satu lapisan,
parse results.json, guard NOT_VERIFIED, history.jsonl — TIDAK berlaku justru di
jalur yang paling sering dipakai.
"""
import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
SRC = (SCRIPTS / 'discord_bot.py').read_text(encoding='utf-8')


def _load():
    spec = importlib.util.spec_from_file_location('discord_bot_under_test', SCRIPTS / 'discord_bot.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_inline_runner_duplicate():
    assert 'def step_run_spec' not in SRC, 'logika run Playwright tidak boleh diduplikasi di discord_bot'


def test_run_action_invokes_runner():
    assert 'str(RUNNER)' in SRC, 'run_action harus memanggil runner.py'
    assert "'--skip-generate'" in SRC
    assert "'--no-comment'" in SRC, 'runner tidak boleh ikut posting - discord_bot yang posting'


def test_runner_supports_no_comment():
    """Tanpa flag ini runner dan discord_bot akan double-post ke tiket."""
    runner_src = (SCRIPTS / 'runner.py').read_text(encoding='utf-8')
    assert "'--no-comment'" in runner_src
    assert 'args.no_comment' in runner_src


@pytest.mark.parametrize('status,expected_ok', [
    ('PASS', True),
    ('PASS_FLAKY', True),
    ('FAIL', False),
    ('NOT_VERIFIED', False),
])
def test_only_pass_reaches_approval_gate(status, expected_ok):
    """NOT_VERIFIED bukan lulus. Replikasi aturan di run_action()."""
    assert (status in ('PASS', 'PASS_FLAKY')) is expected_ok


def test_fmt_result_distinguishes_not_verified_from_fail():
    m = _load()
    not_verified = m.fmt_result(7489, {'status': 'NOT_VERIFIED', 'failed_ac': [], 'flaky_note': ''})
    fail = m.fmt_result(7489, {'status': 'FAIL', 'failed_ac': ['AC2'], 'flaky_note': ''})

    assert 'NOT_VERIFIED' in not_verified
    assert 'BUKAN lulus' in not_verified, 'harus eksplisit bahwa ini bukan lulus'
    assert 'FAIL' in fail and 'AC2' in fail
    assert not_verified != fail


def test_fmt_result_reports_failed_ac():
    m = _load()
    out = m.fmt_result(7489, {'status': 'FAIL', 'failed_ac': ['AC1', 'AC3'], 'flaky_note': ''})
    assert 'AC1' in out and 'AC3' in out, 'laporan harus menyebut AC mana yang gagal'


def test_fmt_result_flaky_is_not_silently_a_pass():
    m = _load()
    out = m.fmt_result(7489, {'status': 'PASS_FLAKY', 'failed_ac': [], 'flaky_note': 'flaky detected'})
    assert 'flaky' in out.lower(), 'PASS_FLAKY tidak boleh dibulatkan jadi PASS polos'
