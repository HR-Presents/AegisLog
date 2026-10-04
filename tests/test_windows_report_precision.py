import json
from aegislog.engine import analyze_lines
from aegislog.parsers import parse_line
from aegislog.incidents import correlate


def record(message, provider='Windows Error Reporting', level='INFO'):
    return f'2026-10-04T08:00:00.1234567Z {provider}[1001]: {level} {message}'


def test_provider_name_and_metadata_are_not_error_evidence():
    assert analyze_lines([record('ordinary activity', 'Error & Crash Provider')]) == []
    assert analyze_lines([record('ordinary activity | AEGIS_EVENT_DATA=' + json.dumps({'Computer': 'error-host'}), 'Vendor')]) == []
    assert analyze_lines([record('ordinary activity', 'Vendor', 'ERROR')])[0].severity == 'MEDIUM'


def test_known_diagnostic_types_have_specific_calibrated_findings():
    kernel = analyze_lines([record('Event Name: LiveKernelEvent P1: 141')])[0]
    assert kernel.title == 'Windows kernel live-dump report recorded'
    assert kernel.severity == 'MEDIUM'
    edge = analyze_lines([record('Event Name: crashpad_log P1: MicrosoftEdgeUpdate.exe')])[0]
    assert edge.title == 'Edge updater diagnostic report recorded'
    assert edge.severity == 'LOW'
    unknown = analyze_lines([record('ordinary diagnostic submission')])[0]
    assert unknown.category == 'diagnostic' and unknown.severity == 'INFO'
    assert analyze_lines([record('Event Name: APPCRASH')])[0].severity == 'MEDIUM'


def test_structured_event_names_support_localized_messages():
    line = record('localized message | AEGIS_EVENT_DATA=' + json.dumps({'EventName': 'LiveKernelEvent', 'P1': '141'}))
    assert analyze_lines([line])[0].title == 'Windows kernel live-dump report recorded'


def test_incident_rows_explain_provider_event_and_time():
    findings = analyze_lines([record('Event Name: LiveKernelEvent P1: 141')] * 2)
    incident = correlate(findings)[0]
    assert 'Windows Error Reporting' in incident.context
    assert '1001' in incident.context
    assert '08:00:00 UTC' in incident.context


def test_punctuated_native_provider_is_recognized():
    event = parse_line(record('ordinary activity', 'Vendor & Service'))
    assert event.source == 'windows'
