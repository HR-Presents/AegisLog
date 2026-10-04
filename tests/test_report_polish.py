import hashlib
from html.parser import HTMLParser

from aegislog.dashboard import analyze_dashboard
from aegislog.ingestion import iter_bounded_lines
from aegislog.reporting import build_html_report, build_summary_report


class ContentsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_contents = False
        self.targets = []
        self.sections = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'nav' and attrs.get('class') == 'document-contents':
            self.in_contents = True
        if self.in_contents and tag == 'a':
            self.targets.append(attrs.get('href', '').removeprefix('#'))
        if tag == 'section' and 'id' in attrs:
            self.sections.append(attrs['id'])

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.in_contents = False


def test_digest_includes_original_bytes_and_discarded_tail(tmp_path):
    raw = b'ERROR ' + b'x' * 150000 + b'\r\n\xff next\nlast'
    source = tmp_path / 'input.log'
    source.write_bytes(raw)
    digest = hashlib.sha256()
    rows = list(iter_bounded_lines(source, 64, on_bytes=digest.update))
    assert rows[0].truncated
    assert digest.hexdigest() == hashlib.sha256(raw).hexdigest()
    data = analyze_dashboard(source, max_line_bytes=64, max_retained_lines=1)
    assert data.source_sha256 == digest.hexdigest()
    assert len(data.raw_lines) == 1


def test_report_contents_matches_actual_section_order(tmp_path):
    source = tmp_path / 'input.log'
    source.write_text('2026-10-04T10:00:00Z app: ERROR connection timeout\n')
    data = analyze_dashboard(source)
    parser = ContentsParser()
    html = build_html_report(data)
    parser.feed(html)
    assert parser.targets == parser.sections
    assert data.source_sha256 in html
    assert 'Report ID identifies analysis output, not source bytes' in html
    assert 'View investigation results' in html
    summary = build_summary_report(data, 'appendix.html')
    assert data.source_sha256 in summary
    assert 'Finding occurrences' in summary and 'Incident groups' in summary
    assert 'finding presentation groups' in summary


def test_empty_source_has_real_digest_but_manual_analysis_does_not(tmp_path):
    from dataclasses import replace
    source = tmp_path / 'empty.log'
    source.write_bytes(b'')
    data = analyze_dashboard(source)
    assert data.source_sha256 == hashlib.sha256(b'').hexdigest()
    manual = replace(data, source_sha256='')
    assert 'Unavailable for this analysis' in build_html_report(manual)


def test_structured_source_digest_covers_header_and_original_format(tmp_path):
    for name, raw in [('input.csv', b'timestamp,message\r\n2026-10-04T10:00:00Z,hello\r\n'),
                      ('input.json', b'[\n  {"message": "hello"}\n]\n')]:
        source = tmp_path / name
        source.write_bytes(raw)
        assert analyze_dashboard(source).source_sha256 == hashlib.sha256(raw).hexdigest()
