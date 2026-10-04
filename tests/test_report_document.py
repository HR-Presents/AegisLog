"""Production document layout must preserve analysis truth and evidence links."""
from dataclasses import replace
from html.parser import HTMLParser

from aegislog.dashboard import analyze_dashboard
from aegislog.reporting import build_html_report, write_html_report


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.targets.append(attrs['href'][1:])


def test_document_links_and_all_retained_excerpts(tmp_path):
    source = tmp_path / 'large.log'
    source.write_text('\n'.join(f'2026-10-04T10:00:{i:02d}Z api[1]: ERROR unique evidence {i}' for i in range(40)))
    data = analyze_dashboard(source)
    html = build_html_report(data)
    parser = References()
    parser.feed(html)
    assert set(parser.targets) <= parser.ids
    assert html.count('class="excerpt"') == len(data.findings)
    for i in range(40):
        assert f'ERROR unique evidence {i}</pre>' in html
    assert 'break-inside:auto' in html
    target = write_html_report(data, tmp_path / 'reports', appendix_extra='<p>Additional verified evidence</p>')
    assert 'Additional verified evidence' in target.with_name(target.stem + '-appendix.html').read_text()
    assert 'Additional verified evidence' not in target.read_text()


def test_chronology_converts_offset_and_preserves_calendar_date(tmp_path):
    source = tmp_path / 'offset.log'
    source.write_text('2026-10-05T00:30:00+02:00 api[1]: ERROR failed operation\n')
    html = build_html_report(analyze_dashboard(source))
    chronology = html.split('class="chronology"', 1)[1].split('</table>', 1)[0]
    assert '2026-10-04 22:30:00' in chronology
    assert '2026-10-05 00:30:00' not in chronology


def test_executive_lead_follows_highest_finding_priority(tmp_path):
    source = tmp_path / 'lead.log'
    source.write_text('2026-10-04T10:00:00Z api[1]: ERROR failure\n')
    data = analyze_dashboard(source)
    low_auth = replace(data.findings[0], severity='LOW', category='authentication', title='Low authentication lead')
    critical = replace(data.findings[0], severity='CRITICAL', title='Critical review lead')
    html = build_html_report(replace(data, findings=(low_auth, critical)))
    executive = html.split('<section class="summary">', 1)[1].split('</section>', 1)[0]
    assert 'DETECTOR REVIEW PRIORITY / CRITICAL' in executive
    assert '<h2>Critical review lead requires review</h2>' in executive
    assert 'not a confirmed host security condition' in executive
