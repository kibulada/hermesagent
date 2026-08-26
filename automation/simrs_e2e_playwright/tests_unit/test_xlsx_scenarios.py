"""
Test pembaca sheet skenario .xlsx.

Dua jebakan yang dikunci di sini:
  - merged cell: `No`/`Task` kosong berarti melanjutkan baris di atasnya, bukan benar-benar kosong
  - satu sel memuat "Positive Case:" DAN "Negative Case:" sekaligus; kalau tidak dipecah,
    dua kasus yang berlawanan akan tergabung jadi satu skenario
"""
from pathlib import Path

import pytest

openpyxl = pytest.importorskip('openpyxl')

import xlsx_scenarios  # noqa: E402

REAL_FILE = Path(__file__).resolve().parents[3] / 'SATUSEHAT_PARSIAL_TEST_SCENARIO_filled.xlsx'


@pytest.fixture
def sheet(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['No', 'Task', 'Module', 'Scenario', 'Expectation', 'Status'])
    ws.append([1, 'Encounter', 'Registrasi Rajal',
               'Positive Case:\n1. Login staff\n2. Pilih poli\nNegative Case:\n1. Poli kosong',
               'Positive Case:\n1. Encounter terbuat\nNegative Case:\n1. Muncul validasi', 'Passed'])
    ws.append([None, None, 'Registrasi via Chatbot', 'Positive Case:\n1. Kirim pesan',
               'Positive Case:\n1. Balasan terkirim', ''])
    ws.append([None, None, None, None, None, None])  # baris kosong, harus dilewati
    ws.append([2, 'Observation', 'Input TTV', 'Isi tensi lalu simpan', 'Data tersimpan', ''])
    path = tmp_path / 'skenario.xlsx'
    wb.save(path)
    return path


def test_forward_fills_merged_cells(sheet):
    rows = xlsx_scenarios.read_sheet(sheet)
    chatbot = next(r for r in rows if r['module'] == 'Registrasi via Chatbot')
    assert chatbot['task'] == 'Encounter', 'Task kosong harus mewarisi baris di atasnya'
    assert chatbot['no'] == '1'


def test_splits_positive_and_negative(sheet):
    rows = xlsx_scenarios.read_sheet(sheet)
    rajal = next(r for r in rows if r['module'] == 'Registrasi Rajal')
    kinds = {c['kind'] for c in rajal['cases']}
    assert kinds == {'positive', 'negative'}

    pos = next(c for c in rajal['cases'] if c['kind'] == 'positive')
    neg = next(c for c in rajal['cases'] if c['kind'] == 'negative')
    assert pos['steps'] == ['Login staff', 'Pilih poli']
    assert neg['steps'] == ['Poli kosong']
    assert 'Encounter terbuat' in pos['expected']
    assert 'validasi' in neg['expected']


def test_text_without_case_marker_is_general(sheet):
    rows = xlsx_scenarios.read_sheet(sheet)
    ttv = next(r for r in rows if r['module'] == 'Input TTV')
    assert [c['kind'] for c in ttv['cases']] == ['general']
    assert ttv['task'] == 'Observation', 'Task baru harus menggantikan carry sebelumnya'


def test_blank_rows_skipped(sheet):
    rows = xlsx_scenarios.read_sheet(sheet)
    assert len(rows) == 3
    assert all(r['module'] for r in rows)


def test_steps_of_prefers_numbering():
    assert xlsx_scenarios.steps_of('1. satu\n2. dua') == ['satu', 'dua']
    assert xlsx_scenarios.steps_of('baris a\nbaris b') == ['baris a', 'baris b']
    assert xlsx_scenarios.steps_of('') == []


@pytest.mark.skipif(not REAL_FILE.exists(), reason='sheet SATUSEHAT tidak ada')
def test_reads_real_satusehat_sheet():
    rows = xlsx_scenarios.read_sheet(REAL_FILE)
    assert rows, 'sheet asli harus menghasilkan skenario'
    assert any(r['task'] for r in rows), 'kolom Task harus terisi setelah forward-fill'
    assert any(c['kind'] in ('positive', 'negative') for r in rows for c in r['cases'])
