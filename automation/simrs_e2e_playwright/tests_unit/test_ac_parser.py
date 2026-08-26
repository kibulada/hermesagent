import ac_parser


def test_detects_ui_keywords():
    r = ac_parser.parse_text('Perbaiki tombol simpan di form pasien', 123)
    assert r['ui_verify_required'] is True
    assert 'tombol' in r['matched_keywords'] and 'form' in r['matched_keywords']
    assert r['ticket_id'] == 123


def test_no_keyword_means_no_ui_verify():
    r = ac_parser.parse_text('Optimasi query agregasi di service billing')
    assert r['ui_verify_required'] is False
    assert r['matched_keywords'] == []


def test_uses_shared_token_resolver():
    """
    Regresi: ac_parser dulu baca os.environ langsung, mengabaikan hermes_config.
    Akibatnya subprocess dari check_ui_flag selalu gagal -> webhook inert.
    """
    src = (ac_parser.__file__)
    text = open(src, encoding='utf-8').read()
    assert 'get_token(' in text, 'ac_parser harus pakai hermes_config.get_token'
    assert "os.environ.get('OP_API_TOKEN')" not in text


def test_strip_html_removes_markup():
    """Nama class HTML tidak boleh dihitung sebagai keyword UI."""
    raw = '<figure class="table op-uc-figure"><table class="op-uc-table">'
    raw += '<tbody><tr class="op-uc-table--row"><td>Optimasi query billing</td></tr></tbody></table></figure>'
    clean = ac_parser.strip_html(raw)
    assert 'op-uc-table' not in clean
    assert 'Optimasi query billing' in clean
    assert ac_parser.parse_text(raw)['matched_keywords'] == [], \
        'markup tidak boleh memicu ui_verify_required'


def test_strip_html_keeps_real_ui_words():
    raw = '<p class="op-uc-p">Sesuaikan <strong>menu</strong> di detail pasien</p>'
    assert 'menu' in ac_parser.parse_text(raw)['matched_keywords']


def test_html_entities_decoded():
    raw = '<p>Section Tampilan &amp; Data -&gt; &quot;Custom Menu&quot;</p>'
    clean = ac_parser.strip_html(raw)
    assert '&amp;' not in clean and '&quot;' not in clean
    assert 'Tampilan & Data' in clean


def test_strip_html_handles_empty():
    assert ac_parser.strip_html('') == ''
    assert ac_parser.strip_html(None) == ''
