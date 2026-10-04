import json
from io import StringIO
from types import SimpleNamespace

import pytest
from rich.console import Console
from typer.testing import CliRunner

from aegislog.activity_review import compare_signals, preview_share, save_activity
from aegislog.case_catalog import save_case, search_cases
from aegislog.dashboard import analyze_dashboard
from aegislog.entry import app
from aegislog.engine import Finding
from aegislog.structured_input import normalize_object
from aegislog.triage import finding_groups, windows_session_context


def windows(event_id, stamp='2026-10-04T08:00:00Z', host='pc-a', session='0x42'):
    fields = dict(Computer=host, SubjectLogonId=session, TargetLogonId=session,
                  SubjectUserName='alice', TargetUserName='alice')
    return f'{stamp} Microsoft-Windows-Security-Auditing[{event_id}]: INFO recorded | AEGIS_EVENT_DATA=' + json.dumps(fields)


def test_session_links_require_explicit_host_id_and_time():
    lines = [windows(4624), windows(4672, '2026-10-04T08:04:00Z'),
             windows(4688, '2026-10-04T08:06:00Z'), windows(4688, host='pc-b'),
             windows(4688, session='0x43'), windows(4688, stamp='unresolved')]
    links = windows_session_context(lines)
    assert len(links) == 1
    assert links[0]['related_records'] == [2]
    assert 'not proof' in links[0]['basis']
    assert windows_session_context([windows(4624, host=''), windows(4672, host='')]) == []
    assert windows_session_context([windows(4624, stamp='2026-10-04T08:00:00'),
                                    windows(4672, stamp='2026-10-04T08:01:00')]) == []


def test_context_caps_large_session_without_omitting_limit_notice():
    links = windows_session_context([windows(4624)] + [windows(4688)] * 1002)
    assert len(links[0]['related_records']) == 1000
    assert links[0]['omitted_context_records'] == 2


def test_successful_logon_is_information_not_security_escalation(tmp_path):
    path = tmp_path / 'auth.log'
    path.write_text(windows(4624))
    findings = analyze_dashboard(path).findings
    assert len(findings) == 1 and findings[0].severity == 'INFO'


def test_triage_does_not_merge_distinct_accounts_and_preserves_times():
    def finding(account, stamp):
        return Finding('MEDIUM', 'error', 'timeout', f'{stamp} app[1]: ERROR timeout', 'Review service',
                       (('account', account),))
    groups = finding_groups([finding('alice', '2026-10-04T08:00:00Z'),
                             finding('alice', '2026-10-04T08:02:00Z'),
                             finding('bob', '2026-10-04T08:01:00Z')])
    assert [group['count'] for group in groups] == [2, 1]
    assert '08:00:00' in groups[0]['first'] and '08:02:00' in groups[0]['last']
    assert groups[0]['references'] == ['F-001', 'F-002']


def test_new_formats_keep_unknown_structures_unrecognized(tmp_path):
    path = tmp_path / 'app.jsonl'
    rows = [dict(time='2026-10-04T08:00:00Z', stream='stderr', log='ERROR timeout'),
            {'@timestamp': '2026-10-04T08:01:00Z', 'message': 'ERROR exception',
             'service': {'name': 'api'}, 'log': {'level': 'error'}}, {'business': 123}]
    path.write_text('\n'.join(json.dumps(row) for row in rows))
    data = analyze_dashboard(path)
    assert data.records == 3 and data.recognized_records == 2
    assert data.format_counts == {'docker-json': 1, 'ecs-message': 1, 'unknown-json': 1}
    assert len(data.findings) == 2
    assert normalize_object({'log': 'business data'})[0] is None


def test_progress_reports_processed_records_and_cancellation_preserves_input(tmp_path):
    path = tmp_path / 'events.log'
    text = '\n'.join(['2026-10-04T08:00:00Z app[1]: INFO okay'] * 1000)
    path.write_text(text)
    updates = []
    data = analyze_dashboard(path, progress=lambda lines, records: updates.append((lines, records)))
    assert updates[0] == (0, 0) and updates[-1] == (1000, 1000)
    assert data.records == 1000
    polls = [0]
    def cancel():
        polls[0] += 1
        if polls[0] > 20:
            raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        analyze_dashboard(path, cancel=cancel)
    assert path.read_text() == text


def sample(findings):
    return SimpleNamespace(source='windows-System-1440min.log', records=10,
                           recognized_records=10, services={'private-host':10}, levels={'ERROR':10},
                           severities={'MEDIUM':len(findings)}, incidents=[], findings=findings)


def test_signal_comparison_and_sharing_omit_private_signal_titles(tmp_path):
    old_dir, new_dir = tmp_path / 'old', tmp_path / 'new'
    old_dir.mkdir();new_dir.mkdir()
    def finding(title):
        return Finding('MEDIUM', 'error', title, '', 'Review')
    before = save_activity(sample([finding('recurring'), finding('old')]), old_dir, 'scope')
    after = save_activity(sample([finding('recurring'), finding('private-alice-new')]), new_dir, 'scope')
    changes = {row['signal']: row['status'] for row in compare_signals(before, after)}
    assert changes['MEDIUM|error|recurring'] == 'recurring'
    assert changes['MEDIUM|error|old'] == 'not observed in current sample'
    assert changes['MEDIUM|error|private-alice-new'] == 'newly observed'
    shared = json.dumps(preview_share(after))
    assert 'private-alice' not in shared and 'private-host' not in shared and 'signals' not in shared


def test_catalog_filters_titles_dates_severity_and_rejects_path_traversal(tmp_path):
    report = tmp_path / 'report.html';report.write_text('report')
    data = sample([Finding('MEDIUM', 'error', 'Timeout on database', '', 'Review')])
    case = save_case(data, tmp_path, report, 'scope')
    assert len(search_cases([tmp_path], query='database', severity='medium', since='2020-01-01')) == 1
    assert search_cases([tmp_path], severity='HIGH') == []
    row = json.loads(case.read_text());row['report'] = '../outside.html';case.write_text(json.dumps(row))
    assert search_cases([tmp_path]) == []
    with pytest.raises(ValueError):search_cases([tmp_path], since='yesterday')


def test_diagnostics_allowlist_and_refuse_overwriting(tmp_path, monkeypatch):
    monkeypatch.setenv('SECRET_PASSWORD', 'do-not-export')
    output = tmp_path / 'support.json'
    runner = CliRunner()
    result = runner.invoke(app, ['diagnostics', '--output', str(output)])
    assert result.exit_code == 0
    payload = json.loads(output.read_text())
    assert payload['schema'] == 'aegislog-support-1'
    assert 'do-not-export' not in output.read_text() and str(tmp_path) not in output.read_text()
    assert runner.invoke(app, ['diagnostics', '--output', str(output)]).exit_code == 1


def test_update_check_offline_and_untrusted_metadata(monkeypatch):
    from aegislog import providers, support_commands
    runner = CliRunner()
    monkeypatch.setattr(providers, 'fetch_public_release', lambda: b'{"tag_name":"v9.1.2","draft":false,"prerelease":false}')
    result = runner.invoke(app, ['update-check'])
    assert result.exit_code == 0 and 'Newer release available' in result.output
    monkeypatch.setattr(providers, 'fetch_public_release', lambda: b'{"tag_name":"$(bad)"}')
    with pytest.raises(ValueError):support_commands.fetch_latest_release()
    def offline():
        raise OSError('offline')
    monkeypatch.setattr(providers, 'fetch_public_release', offline)
    assert runner.invoke(app, ['update-check']).exit_code == 1


def test_sharing_preview_decline_does_not_write(tmp_path, monkeypatch):
    from aegislog import report_browser
    save_activity(sample([]), tmp_path, 'scope')
    replies = iter(['s', 'no', 'b'])
    monkeypatch.setattr(report_browser.Prompt, 'ask', lambda *args, **kwargs: next(replies))
    stream = StringIO()
    report_browser.report_actions(Console(file=stream), tmp_path / 'report.html')
    assert 'complete sharing copy' in stream.getvalue()
    assert not (tmp_path / 'share-summary.json').exists()
