"""
Regresi paling berbahaya: approval `lanjut` dulu transisi ke status 14.
Status 14 = Rejected (lihat parse_sync.py), bukan Closed, dan bukan langkah QA.
Alur QA yang benar (memory/openproject_api.md): 16 Tested Dev / 17 Tested Staging / 11 Test failed.
"""
import sys
from pathlib import Path

import pytest

SRC = (Path(__file__).resolve().parent.parent / 'scripts' / 'discord_bot.py').read_text(encoding='utf-8')


def test_status_14_and_12_not_used_as_target():
    assert "OP_CLOSED_STATUS_ID" not in SRC, 'jangan transisi ke Closed/Rejected dari jalur QA'
    assert "'14'" not in SRC.replace("STATUS_", ""), 'status 14 (Rejected) tidak boleh jadi target'


def test_whitelist_constants_present():
    for const in ('STATUS_TEST_FAILED', 'STATUS_ON_HOLD', 'STATUS_TESTED_DEV', 'STATUS_TESTED_STAGING'):
        assert const in SRC, f'{const} hilang'
    assert 'ALLOWED_STATUS_IDS' in SRC


def test_transition_guard_rejects_illegal_status():
    """Guard harus menolak status di luar whitelist sebelum menyentuh jaringan."""
    ns = {}
    # Ambil hanya potongan yang dibutuhkan supaya tidak perlu discord.py terinstall.
    exec(compile(_extract(SRC), '<guard>', 'exec'), ns)
    with pytest.raises(ns['TransitionError']):
        ns['guard']('14')
    with pytest.raises(ns['TransitionError']):
        ns['guard']('12')
    for ok in ('11', '13', '16', '17'):
        ns['guard'](ok)  # tidak boleh raise


def _extract(src: str) -> str:
    """Rekonstruksi guard dari konstanta asli di discord_bot.py."""
    lines = [l for l in src.split('\n')
             if l.startswith('STATUS_') or l.startswith('ALLOWED_STATUS_IDS')]
    assert lines, 'konstanta status tidak ditemukan'
    return '\n'.join(lines) + '''

class TransitionError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

def guard(new_status_id):
    if str(new_status_id) not in ALLOWED_STATUS_IDS:
        raise TransitionError(f'Status id {new_status_id} di luar whitelist QA.')
'''


def test_reject_branch_exists():
    """Balas `reject` dulu senyap total karena `else:` nyantol ke blok yang salah."""
    assert "if decision == 'lanjut':" in SRC
    idx = SRC.index("if decision == 'lanjut':")
    tail = SRC[idx:idx + 2000]
    assert '\n    else:' in tail, 'cabang reject tidak ada di handler approval'
    assert 'hold per Kibul' in tail


def test_no_dead_handle_ai_response():
    assert 'async def handle_ai_response' not in SRC
