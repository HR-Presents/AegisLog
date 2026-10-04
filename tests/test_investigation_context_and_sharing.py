import json
from types import SimpleNamespace
import pytest
from aegislog.activity_review import save_activity, compare_activity, share_activity
from aegislog.engine import analyze_lines
from aegislog.incidents import correlate
from aegislog.reporting import _summary_service_chart


def error(stamp, event_id=7011, host='pc-a', account='alice'):
    return (f'{stamp} Service Control Manager[{event_id}]: ERROR timeout | AEGIS_EVENT_DATA='
            + json.dumps({'Computer': host, 'SubjectUserName': account}))


def test_windows_context_survives_truncated_evidence():
    line = error('2026-10-04T08:00:00Z').replace('ERROR timeout', 'ERROR timeout ' + 'x' * 1000)
    finding = analyze_lines([line])[0]
    assert len(finding.evidence) == 500
    assert dict(finding.context)['host'] == 'pc-a'
    assert dict(finding.context)['account'] == 'alice'


def test_windows_groups_require_matching_host_account_event_id_and_time():
    first = error('2026-10-04T08:00:00Z')
    close = error('2026-10-04T08:04:00Z')
    separated = [error('2026-10-04T08:01:00Z', host='pc-b'),
                 error('2026-10-04T08:01:00Z', account='bob'),
                 error('2026-10-04T08:01:00Z', event_id=7000),
                 error('2026-10-04T08:06:00Z')]
    findings = analyze_lines([first, close] + separated)
    groups = correlate(findings)
    assert len(groups) == 1 and groups[0].count == 2
    assert '08:04:00' in groups[0].evidence[1]
    assert correlate(list(reversed(findings))) == groups


def test_windows_unknown_timezone_does_not_imply_timed_incident():
    assert correlate(analyze_lines([error('2026-10-04T08:00:00')] * 2)) == []


def test_provider_chart_preserves_full_names_and_escapes_html():
    name = 'Microsoft-Windows-DistributedCOM <script>'
    html = _summary_service_chart({name: 4})
    assert 'Microsoft-Windows-DistributedCOM &lt;script&gt;' in html
    assert 'Microsoft-Windo...' not in html


def data(records, services):
    return SimpleNamespace(source='windows-System-1440min.log', records=records, recognized_records=records,
                           services=services, levels={'ERROR':records}, severities={'MEDIUM':2}, incidents=[1])


def test_local_comparison_normalizes_sample_sizes(tmp_path):
    a,b = tmp_path/'a', tmp_path/'b'
    a.mkdir();b.mkdir()
    first = save_activity(data(100, {'private-host':50}), a, 'scope')
    second = save_activity(data(200, {'private-host':100}), b, 'scope')
    changes = compare_activity(first, second)
    assert changes[0]['change_percentage_points'] == 0
    assert changes[0]['previous_percent'] == changes[0]['current_percent'] == 50


def test_share_export_omits_identifiers_and_refuses_overwrite(tmp_path):
    private = save_activity(data(100, {'alice@203.0.113.7/C:/Users/Alice':50}), tmp_path, 'private path')
    output = tmp_path/'share.json'
    share_activity(private, output)
    text = output.read_text()
    for secret in ['alice', '203.0.113.7', 'C:/Users', 'windows-System', 'private path']:
        assert secret not in text
    assert json.loads(text)['provider_counts'][0]['records'] == 50
    with pytest.raises(FileExistsError):share_activity(private, output)
    with pytest.raises(ValueError):share_activity(private, private)


def test_invalid_or_incomparable_baselines_are_rejected(tmp_path):
    first = save_activity(data(100, {'app':50}), tmp_path, 'scope')
    other = tmp_path/'other';other.mkdir()
    changed = data(100, {'app':50});changed.source='windows-Application-1440min.log'
    second = save_activity(changed, other, 'scope')
    with pytest.raises(ValueError):compare_activity(first, second)
    obj=json.loads(second.read_text());obj['records']=True;second.write_text(json.dumps(obj))
    with pytest.raises(ValueError):compare_activity(first, second)
