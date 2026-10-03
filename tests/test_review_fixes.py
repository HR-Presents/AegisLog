from io import StringIO
from pathlib import Path

from rich.console import Console

from aegislog.dashboard import analyze_dashboard
from aegislog.dashboard_v213 import render_dashboard
from aegislog.folder_scan import write_batch
from aegislog.terminal_charts import ActivityChart


def test_builtin_sid_keeps_evidence_without_elevating_name_only(tmp_path):
    log = tmp_path / 'windows.log'
    messages = ['Security ID: S-1-5-18 Account Name: SYSTEM',
                'Security ID: S-1-5-21-123 Account Name: SYSTEM',
                'Account Name: SYSTEM',
                'Security ID: S-1-5-19 Account Name: LOCAL SERVICE']
    log.write_text('\n'.join(f'2026-10-03T10:00:0{i}Z Microsoft-Windows-Security-Auditing[4672]: INFO {m}' for i, m in enumerate(messages)))
    data = analyze_dashboard(log)
    assert len(data.findings) == 4
    assert data.severities == {'INFO': 2, 'MEDIUM': 2}
    assert 'subject_sid=S-1-5-18' in data.findings[0].evidence


def test_grouped_top_findings_and_wide_frame(tmp_path):
    log = tmp_path / 'same.log'
    log.write_text('\n'.join(f'2026-10-03T10:00:0{i}Z app: ERROR failed job' for i in range(4)))
    out = StringIO()
    console = Console(file=out, width=208)
    console.print(render_dashboard(analyze_dashboard(log), screen_width=208))
    text = out.getvalue()
    assert '4 occurrence(s)' in text
    assert text.count('[MEDIUM] Operational error detected') == 1
    assert 'NOT A COMPROMISE SCORE' in text
    assert max(map(len, text.splitlines())) == 206


def test_chart_uses_consecutive_retained_minutes_and_bounded_long_gaps():
    out = StringIO()
    console = Console(file=out, width=120)
    console.print(ActivityChart({'2026-10-03 10:00': 5, '2026-10-03 10:02': 7}))
    text = out.getvalue()
    assert '10:00  10:01  10:02' in text
    assert '12 events / 3 minute buckets' in text
    out = StringIO()
    Console(file=out, width=120).print(ActivityChart({'2001-01-01 00:00': 5, '2026-10-03 10:02': 7}))
    assert '7 events / 12 minute buckets' in out.getvalue()
    assert 'Retained total: 12' in out.getvalue()


def test_batch_explains_duplicates_coverage_and_generic_matches(tmp_path):
    rows = [dict(source='errors.log', status='complete', lines=10, records=10, recognized=0,
                 findings=2, coverage='Generic fallback', report='001/report.html',
                 groups=[dict(severity='MEDIUM', category='error', title='Operational error', recommendation='Review', count=2)]),
            dict(source='copy.log', status='duplicate', duplicate_of='errors.log', report='001/report.html')]
    index = write_batch(tmp_path, Path('/demo'), rows, scan_mode='Other text/configuration included')
    text = index.read_text()
    assert '1 unique sources analyzed + 1 duplicate copies' in text
    assert '2 operational issues; 0 security / other leads' in text
    assert '1 generic-only sources' in text
    assert 'Identical to errors.log' in text
    assert 'class="print-only"' in text and 'class="screen-only"' in text
    assert '1 occurrence</strong>' not in text


def test_pause_opens_current_report(monkeypatch, tmp_path):
    from aegislog import commands_v11, commands_v144, report_browser
    report = tmp_path / 'report.html'
    opened = []
    monkeypatch.setattr(commands_v11, 'last_report', report)
    monkeypatch.setattr(report_browser, 'report_actions', lambda console, path: opened.append(path))
    commands_v144._pause_for_menu()
    assert opened == [report]


def test_report_pause_back_and_quit_in_shell(monkeypatch, tmp_path):
    import pytest
    from aegislog import commands_v11, commands_v144, navigation
    monkeypatch.setattr(commands_v11, 'last_report', tmp_path / 'report.html')
    monkeypatch.setattr(navigation.RichPrompt, 'ask', lambda *a, **kw: 'b')
    with navigation.shell_navigation():
        commands_v144._pause_for_menu()
    monkeypatch.setattr(navigation.RichPrompt, 'ask', lambda *a, **kw: 'q')
    with navigation.shell_navigation(), pytest.raises(navigation.WorkspaceQuit):
        commands_v144._pause_for_menu()
