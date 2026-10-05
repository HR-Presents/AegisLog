import json
from pathlib import Path

import pytest

from aegislog.engine import Finding
from aegislog.native_collectors import CollectorError
from aegislog.product import check_computer, discover_sources, explain_finding, investigate_path


def test_discovery_reports_actual_access(monkeypatch):
    monkeypatch.setattr('aegislog.product.platform.system', lambda: 'Windows')
    def probe(source, **kwargs):
        if kwargs['channel'] == 'Security':
            raise CollectorError('access denied')
        return []
    monkeypatch.setattr('aegislog.product.collect', probe)
    rows = discover_sources()
    assert [row['status'] for row in rows] == ['readable', 'readable', 'unavailable']
    assert 'access denied' in rows[-1]['detail']


def test_native_snapshot_scope_cleanup_and_export(tmp_path, monkeypatch):
    monkeypatch.setattr('aegislog.product.collect', lambda *a, **kw: ['2026-10-03T00:00:00Z ERROR app: timeout token=abcdef\n'])
    result = check_computer('windows', 'System', 60, 300, tmp_path)
    assert result['events'] == 1
    assert 'Latest 300' in result['coverage']['scope']
    assert 'abcdef' not in Path(result['export']).read_text()
    assert Path(result['summary']).is_file()
    assert 'windows-System' in result['source']
    for name in ('summary', 'evidence_report'):
        html = Path(result[name]).read_text()
        assert result['coverage']['scope'] in html
        assert 'Selected file analysis' not in html
    for source, minutes, limit in [('docker', 60, 300), ('windows', 2, 300), ('windows', 60, 2001)]:
        with pytest.raises(ValueError):
            check_computer(source, 'System', minutes, limit, tmp_path)


def test_native_count_limit_scope_reaches_both_reports(tmp_path, monkeypatch):
    monkeypatch.setattr('aegislog.product.collect', lambda *a, **kw: ['2026-10-05T00:00:00Z Volsnap[36]: ERROR shadow copies aborted due to a user imposed limit\n'])
    result = check_computer('windows', 'System', 1440, 1, tmp_path)
    for name in ('summary', 'evidence_report'):
        html = Path(result[name]).read_text()
        assert 'within 1440 minutes' in html
        assert 'Count limit reached' in html
        assert 'Returned 1 events' in html


def test_file_restrictions_source_preservation_coverage(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_text('hello world\n2026-10-03T00:00:00Z INFO app: healthy\n')
    before = path.read_bytes()
    result = investigate_path(path, tmp_path / 'reports')
    assert path.read_bytes() == before
    assert result['coverage']['generic_retained'] == 1
    assert json.loads(Path(result['export']).read_text())['events'] == 2
    binary = tmp_path / 'binary.log'
    binary.write_bytes(b'a\x00b')
    for bad in [binary, tmp_path / 'missing', Path('//server/share/log')]:
        with pytest.raises(ValueError):
            investigate_path(bad, tmp_path / 'reports')


def test_explanations_do_not_equate_priority_with_compromise():
    finding = Finding('MEDIUM', 'error', 'Operational error', 'timeout', 'Review nearby events')
    explanation = explain_finding(finding)
    assert explanation['classification'] == 'Operational issue'
    assert 'maintenance' in explanation['alternative']
    assert 'no measured probability' in explanation['confidence']


def test_bounded_native_time_arguments(monkeypatch):
    from aegislog import native_collectors as native
    calls = []
    monkeypatch.setattr(native.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(native, '_run', lambda cmd, **kw: calls.append(cmd) or '')
    assert native.journald_logs(300, since_minutes=60) == []
    assert calls[0][-2:] == ['--since', '60 minutes ago']
    with pytest.raises(CollectorError):
        native.journald_logs(since_minutes=123)
    monkeypatch.setattr(native.os, 'name', 'nt')
    assert native.windows_event_logs(since_minutes=1440) == []
    assert 'StartTime=(Get-Date).AddMinutes(-1440)' in calls[-1][-1]
    with pytest.raises(CollectorError):
        native.windows_event_logs(channel="System';bad")


def test_known_log_discovery_checks_encoding_and_access(tmp_path, monkeypatch):
    monkeypatch.setattr('aegislog.product.platform.system', lambda: 'Windows')
    monkeypatch.setattr('aegislog.product.collect', lambda *a, **kw: [])
    monkeypatch.setenv('SystemRoot', str(tmp_path))
    dism = tmp_path / 'Logs' / 'DISM' / 'dism.log'
    dism.parent.mkdir(parents=True)
    dism.write_text('servicing operation complete\n')
    cbs = tmp_path / 'Logs' / 'CBS' / 'CBS.log'
    cbs.parent.mkdir(parents=True)
    cbs.write_bytes(b'\xff\xfea\x00')
    files = [row for row in discover_sources() if row['source'] == 'file']
    assert [row['status'] for row in files] == ['readable', 'unavailable']
    assert files[0]['path'] == str(dism)


def test_native_empty_time_window_is_not_access_failure(monkeypatch):
    from aegislog import native_collectors as native
    monkeypatch.setattr(native.os, 'name', 'nt')
    def empty(*a, **kw):
        raise CollectorError('NoMatchingEventsFound: No events were found')
    monkeypatch.setattr(native, '_run', empty)
    assert native.windows_event_logs(since_minutes=60) == []
    with pytest.raises(CollectorError):
        native.windows_event_logs()
