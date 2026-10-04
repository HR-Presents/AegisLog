from pathlib import Path
from io import StringIO

import pytest
from rich.console import Console

from aegislog.report_paths import default_report_dir


def test_denied_current_folder_falls_back_and_browser_finds_report(tmp_path, monkeypatch):
    from aegislog.reporting import write_html_report
    from aegislog.dashboard import analyze_dashboard
    from aegislog.report_browser import open_saved_reports
    denied, user = tmp_path / 'protected' / 'reports', tmp_path / 'user' / 'reports'
    monkeypatch.setattr('aegislog.report_paths.report_search_roots', lambda: [denied, user])
    mkdir = Path.mkdir
    def guard(path, *args, **kwargs):
        if path == denied:
            raise PermissionError('simulated System32 write denied')
        return mkdir(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'mkdir', guard)
    assert default_report_dir() == user
    source = tmp_path / 'source.log'
    source.write_text('ERROR failure\n')
    report = write_html_report(analyze_dashboard(source))
    assert report.parent == user
    monkeypatch.setattr('aegislog.report_browser.report_search_roots', lambda: [denied, user])
    monkeypatch.setattr('aegislog.report_browser.Prompt.ask', lambda *a, **kw: '1')
    opened = []
    monkeypatch.setattr('aegislog.commands_security.open_report', opened.append)
    open_saved_reports(Console(file=StringIO()))
    assert opened == [report]


def test_both_locations_denied_report_clean_error(tmp_path, monkeypatch):
    monkeypatch.setattr('aegislog.report_paths.report_search_roots', lambda: [tmp_path])
    monkeypatch.setattr(Path, 'mkdir', lambda *a, **kw: (_ for _ in ()).throw(PermissionError('denied')))
    with pytest.raises(OSError, match='Cannot write reports'):
        default_report_dir()


def test_guided_check_handles_report_directory_failure(monkeypatch):
    from aegislog.product import guided_check
    monkeypatch.setattr('aegislog.product.discover_sources', lambda: [dict(label='System',status='readable',description='System events',detail='ready',source='windows',channel='System')])
    replies = iter(['1', '1440', '300'])
    monkeypatch.setattr('aegislog.navigation.Prompt.ask', lambda *a, **kw: next(replies))
    monkeypatch.setattr('aegislog.product.default_report_dir', lambda: (_ for _ in ()).throw(OSError('Cannot write reports')))
    stream = StringIO()
    guided_check(Console(file=stream))
    assert 'Cannot write reports' in stream.getvalue()


def test_existing_but_unwritable_directory_uses_probe_fallback(tmp_path, monkeypatch):
    denied, user = tmp_path / 'existing', tmp_path / 'user'
    denied.mkdir()
    monkeypatch.setattr('aegislog.report_paths.report_search_roots', lambda: [denied, user])
    from aegislog import report_paths
    original = report_paths.tempfile.TemporaryFile
    def probe(*args, **kwargs):
        if kwargs['dir'] == denied:
            raise PermissionError('write denied')
        return original(*args, **kwargs)
    monkeypatch.setattr(report_paths.tempfile, 'TemporaryFile', probe)
    assert default_report_dir() == user

