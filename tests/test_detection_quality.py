import json

import pytest

from aegislog.dashboard import analyze_dashboard
from aegislog.engine import AnalysisState
from aegislog.security_workbench import Tuning, extra_signals, make_record
from aegislog.triage import windows_session_context
from aegislog.windows_security import parse_windows_security_line, signal_for_event


def windows(kind, second=0, host='pc-a', account='alice', group=None, session='0x42', zone='Z'):
    fields = dict(Computer=host, SubjectUserName=account, TargetUserName=account,
                  IpAddress='203.0.113.9', WorkstationName='client', MemberName=account,
                  SubjectLogonId=session, TargetLogonId=session)
    if group:
        fields.update(TargetSid=group, TargetUserName='Localized group name')
    return f'2026-10-05T08:00:{second:02d}{zone} Microsoft-Windows-Security-Auditing[{kind}]: INFO localized | AEGIS_EVENT_DATA=' + json.dumps(fields)


@pytest.mark.parametrize('kind', [4728, 4732])
@pytest.mark.parametrize('sid,severity', [('S-1-5-32-544', 'HIGH'), ('S-1-5-32-545', 'INFO'),
                                        ('S-1-5-21-1-2-3-512', 'HIGH'), ('S-1-5-21-1-2-3-518', 'HIGH'),
                                        ('S-1-5-21-1-2-3-519', 'HIGH'), ('S-1-5-21-1-2-3-545', 'MEDIUM'),
                                        ('S-1-5-32-999', 'MEDIUM'), (None, 'MEDIUM')])
def test_group_change_classification_uses_sid_not_event_id(kind, sid, severity):
    event = parse_windows_security_line(windows(kind, group=sid))
    assert signal_for_event(event).severity == severity
    if sid:
        assert f'group_sid={sid}' in signal_for_event(event).evidence


def test_standard_group_evidence_is_retained(tmp_path):
    path = tmp_path / 'users.log'
    path.write_text(windows(4732, group='S-1-5-32-545'))
    data = analyze_dashboard(path)
    assert len(data.findings) == 1
    assert data.findings[0].severity == 'INFO'
    assert dict(data.findings[0].context)['group_sid'] == 'S-1-5-32-545'


def sequences(lines):
    return [s for s in extra_signals([make_record(n, line) for n, line in enumerate(lines, 1)], Tuning(), set())
            if s.finding.title == 'Successful login after repeated failures']


def test_windows_failure_success_sequence_requires_same_target_host():
    failures = [windows(4625, n) for n in range(5)]
    assert not sequences(failures + [windows(4624, 10, host='pc-b')])
    assert sequences(failures + [windows(4624, 10, host='PC-A', account='ALICE')])
    assert not sequences([windows(4625, n, host='') for n in range(5)] + [windows(4624, 10, host='')])
    assert not sequences([windows(4625, n, zone='') for n in range(5)] + [windows(4624, 10, zone='')])


def test_core_authentication_does_not_merge_distinct_target_hosts():
    state = AnalysisState()
    for n in range(3):
        state.process(windows(4625, n, host='pc-a'))
        state.process(windows(4625, n, host='pc-b'))
    assert not any(f.severity == 'HIGH' for f in state.findings())


def test_reused_session_id_context_stops_at_next_logon():
    lines = [windows(4624, 0), windows(4688, 5), windows(4624, 10, account='bob'), windows(4688, 15, account='bob')]
    links = windows_session_context(lines)
    assert [link['related_records'] for link in links] == [[2], [4]]


def test_ambiguous_same_time_session_anchors_do_not_link():
    assert windows_session_context([windows(4624), windows(4624, account='bob'), windows(4688, 5)]) == []
