from pathlib import Path

import pytest
from rich.console import Console

from aegislog.folder_scan import discover_logs, run_folder_scan, select_logs


def test_discovery_nested_binary_and_limits(tmp_path):
    (tmp_path / 'nested').mkdir()
    (tmp_path / 'nested' / 'app.log').write_text('ERROR failure\n')
    (tmp_path / 'binary.log').write_bytes(b'abc\x00def')
    (tmp_path / 'empty.txt').touch()
    (tmp_path / 'program.exe').write_text('ERROR')
    found, skipped, capped = discover_logs(tmp_path)
    assert [p.name for p in found] == ['app.log']
    assert skipped == 2 and not capped
    assert discover_logs(tmp_path, limit=1)[2]
    assert discover_logs(tmp_path, max_entries=1)[2]


def test_symlinks_are_not_followed(tmp_path):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'secret.log').write_text('ERROR failure')
    root = tmp_path / 'root'
    root.mkdir()
    try:
        (root / 'link').symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip('Symlink creation is unavailable on this platform')
    assert discover_logs(root)[0] == []


def test_selection_and_invalid_folder(tmp_path):
    files = [Path('a.log'), Path('b.log')]
    assert select_logs('2,1,2', files) == [files[1], files[0]]
    assert select_logs('ALL', files) == files
    for raw in ['0', '3', 'bad', '']:
        with pytest.raises(ValueError):
            select_logs(raw, files)
    with pytest.raises(ValueError):
        discover_logs(tmp_path / 'missing')


def test_batch_preserves_sources_and_report_links(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / 'sources'
    source.mkdir()
    original = b'2026-10-03T00:00:00Z app: ERROR operation failed\n'
    for name in ['a.log', 'b.log']:
        (source / name).write_bytes(original)
    replies = iter([str(source), 'no', 'ALL', 'analyze', 'b'])
    monkeypatch.setattr('aegislog.folder_scan.Prompt.ask', lambda *a, **kw: next(replies))
    run_folder_scan(Console(record=True))
    for path in source.glob('*'):
        assert path.read_bytes() == original
    reports = list((tmp_path / 'aegislog-reports' / 'folder-scan').glob('*/*/*-report.html'))
    assert len(reports) == 2
    from aegislog.report_browser import report_candidates
    assert len(report_candidates(tmp_path / 'aegislog-reports')) == 3


def test_default_duplicate_skip_keeps_all_locations(tmp_path, monkeypatch):
    import json
    monkeypatch.chdir(tmp_path)
    root = tmp_path / 'sources'
    root.mkdir()
    for name in ('a.log', 'b.log'):
        (root / name).write_text('ERROR failure\n')
    (root / 'README.txt').write_text('How to install this application.')
    assert len(discover_logs(root)[0]) == 2
    assert len(discover_logs(root, include_other=True)[0]) == 3
    replies = iter([str(root), 'no', 'ALL', 'skip', 'b'])
    monkeypatch.setattr('aegislog.folder_scan.Prompt.ask', lambda *a, **kw: next(replies))
    run_folder_scan(Console())
    manifest = next((tmp_path / 'aegislog-reports').glob('folder-scan/*/batch-manifest.json'))
    rows = json.loads(manifest.read_text())['sources']
    assert [row['source'] for row in rows] == ['a.log', 'b.log']
    assert [row['status'] for row in rows] == ['complete', 'duplicate']
    assert rows[0]['report'] == rows[1]['report']
    assert 'Identical to a.log' in manifest.with_name('batch-index.html').read_text()


def test_cancellation_preserves_completed_and_pending_sources(tmp_path, monkeypatch):
    import json
    from aegislog import folder_scan
    from aegislog.navigation import WorkspaceBack
    monkeypatch.chdir(tmp_path)
    root = tmp_path / 'sources'
    root.mkdir()
    for name in ('a.log', 'b.log', 'c.log'):
        (root / name).write_text('ERROR ' + name)
    replies = iter([str(root), 'no', 'ALL', 'analyze', 'b'])
    monkeypatch.setattr(folder_scan.Prompt, 'ask', lambda *a, **kw: next(replies))
    original = folder_scan.analyze_dashboard
    def cancel_second(path, **kwargs):
        if path.name == 'b.log':
            raise WorkspaceBack()
        return original(path, **kwargs)
    monkeypatch.setattr(folder_scan, 'analyze_dashboard', cancel_second)
    run_folder_scan(Console())
    manifest = next((tmp_path / 'aegislog-reports').glob('folder-scan/*/batch-manifest.json'))
    rows = json.loads(manifest.read_text())['sources']
    assert [row['status'] for row in rows] == ['complete', 'cancelled', 'pending']
    assert (manifest.parent / rows[0]['report']).is_file()
