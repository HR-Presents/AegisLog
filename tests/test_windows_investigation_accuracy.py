import json
from pathlib import Path

from aegislog.engine import AnalysisState, Finding, analyze_file, analyze_lines
from aegislog.incidents import correlate
from aegislog.report_design import observed_facts
from aegislog.windows_security import parse_windows_security_line, signal_for_event


def finding(provider, event_id):
    return Finding('MEDIUM', 'error', 'Operational error detected',
                   f'2026-10-04T08:00:00Z {provider}[{event_id}]: ERROR timeout', 'review')


def test_windows_report_does_not_confuse_event_id_and_pid():
    html = observed_facts(finding('Service Control Manager', 7011))
    assert '<dd>Service Control Manager</dd>' in html
    assert '<dt>Provider</dt>' in html and '<dt>Event ID</dt><dd>7011</dd>' in html
    assert '<dt>Process</dt>' not in html
    linux = Finding('MEDIUM', 'error', 'Error', 'Oct 4 08:00:00 host api[212]: ERROR timeout', 'review')
    assert '<dt>Process</dt><dd>212</dd>' in observed_facts(linux)


def test_windows_incidents_preserve_provider_boundaries():
    first = finding('Service Control Manager', 7011)
    second = finding('Microsoft-Windows-DistributedCOM', 10010)
    assert correlate([first, second]) == []
    incidents = correlate([first, second, second])
    assert len(incidents) == 1 and incidents[0].count == 2
    assert all('DistributedCOM' in evidence for evidence in incidents[0].evidence)


def test_structured_security_fields_override_localized_and_ambiguous_message():
    fields = dict(SubjectUserName='administrator', TargetUserName='new-account',
                  SubjectUserSid='S-1-5-21-123', IpAddress='203.0.113.7')
    line = ('2026-10-04T08:00:00Z Microsoft-Windows-Security-Auditing[4720]: INFO '
            'Account Name: misleading | AEGIS_EVENT_DATA=' + json.dumps(fields))
    event = parse_windows_security_line(line)
    assert event.account == 'new-account' and event.actor_account == 'administrator'
    assert event.source_ip == '203.0.113.7'
    signal = signal_for_event(event)
    assert 'account=new-account' in signal.evidence and 'actor_account=administrator' in signal.evidence
    assert signal.evidence.startswith('2026-10-04T08:00:00Z')
    assert '<dt>Event ID</dt><dd>4720</dd>' in observed_facts(
        Finding(signal.severity, signal.category, signal.title, signal.evidence, signal.recommendation))


def test_structured_missing_target_does_not_guess_actor():
    line = ('2026-10-04T08:00:00Z Microsoft-Windows-Security-Auditing[4720]: INFO '
            'Account Name: administrator | AEGIS_EVENT_DATA={"SubjectUserName":"administrator"}')
    assert parse_windows_security_line(line).account is None


def test_native_collector_uses_numeric_levels_and_named_xml_fields(monkeypatch):
    from aegislog import native_collectors as nc
    monkeypatch.setattr(nc.os, 'name', 'nt')
    payload = dict(TimeCreated='2026-10-04T08:00:00Z', Id=4625, Level=3,
                   LevelDisplayName='localized warning', ProviderName='Microsoft-Windows-Security-Auditing',
                   Message='localized logon failure', EventData={'TargetUserName':'alice', 'IpAddress':'203.0.113.7'})
    commands = []
    def run(command, timeout=15):
        commands.append(command)
        return json.dumps(payload)
    monkeypatch.setattr(nc, '_run', run)
    line = nc.windows_event_logs(channel='Security')[0]
    assert ': WARNING ' in line
    event = parse_windows_security_line(line)
    assert event.account == 'alice' and event.source_ip == '203.0.113.7'
    assert 'ToXml()' in commands[0][-1] and 'Sort-Object TimeCreated' in commands[0][-1]
    assert '-MaxEvents 300' in commands[0][-1]


def test_static_file_retains_earlier_authentication_peak(tmp_path: Path):
    early = '2026-10-04T08:00:00Z sshd[1]: Failed password for alice from 203.0.113.7'
    late = '2026-10-04T10:00:00Z sshd[1]: Failed password for alice from 203.0.113.7'
    path = tmp_path / 'auth.log'
    path.write_text('\n'.join([early] * 6 + [late]))
    findings = analyze_file(path)[1]
    assert len(findings) == 1 and findings[0].severity == 'HIGH'
    assert '6 authentication failures' in findings[0].evidence
    # Rolling consumers retain their existing current-window contract.
    assert analyze_lines([early] * 6 + [late])[0].severity == 'LOW'


def test_static_peaks_are_bounded_and_dropped_results_are_counted():
    state = AnalysisState(preserve_auth_bursts=True, max_findings=2)
    for i in range(5):
        state.process(f'2026-10-04T08:00:00Z sshd[1]: Failed password for alice from 203.0.113.{i+1}')
    assert len(state.findings()) == 2
    assert state.dropped_findings == 3
