from aegislog.report_reference import document_cover, document_contents


def test_cover_uses_aegislog_brand_and_true_source_fields():
    html = document_cover('source.log', 'AL-CASE', 'windows', '2026-10-04 UTC', 'data:image/png;base64,AAAA')
    assert 'alt="AegisLog terminal mark logo"' in html
    assert 'PRESENTED BY HR-PRESENTS' in html
    assert 'Security Investigation Report' in html
    assert 'Record formats' in html and '<dd>windows</dd>' in html
    assert 'Language' not in html and 'authenticated' not in html
    assert 'cover-background' in html and 'linearGradient' in html


def test_cover_escapes_user_controlled_metadata_and_marks_demo():
    html = document_cover('<script>source</script>', 'AL-CASE', '<windows>', 'UTC', 'logo.png', summary=True, demo=True)
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert 'Investigation Summary' in html and 'SYNTHETIC DEMO DATA' in html


def test_contents_preserves_safe_targets():
    html = document_contents([('#findings', 'Findings & actions'), ('report.html?x="', '<evidence>')])
    assert 'href="#findings"' in html
    assert 'Findings &amp; actions' in html
    assert '&lt;evidence&gt;' in html and '&quot;' in html
