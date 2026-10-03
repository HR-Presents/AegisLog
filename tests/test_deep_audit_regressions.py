import json
import os
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from aegislog.dashboard import analyze_dashboard
from aegislog.entry import app
from aegislog.product import investigate_path
from aegislog.reporting import write_html_report
from aegislog.sanitize import redact_sensitive


def test_deep_json_is_flagged_without_crashing_or_exposing_password(tmp_path):
    raw = '[' * 1500 + '{"password":"private-audit-value"}' + ']' * 1500
    path = tmp_path / 'deep.json'
    path.write_text(raw)
    data = analyze_dashboard(path)
    assert data.invalid_records == 1 and data.recognized_records == 0
    assert 'private-audit-value' not in redact_sensitive(raw)
    assert 'private-audit-value' not in data.raw_lines[0]


def test_large_csv_field_does_not_hide_later_findings(tmp_path):
    path = tmp_path / 'large.csv'
    path.write_text('message\n' + 'x' * 150000 + '\nERROR timeout\n')
    data = analyze_dashboard(path)
    assert data.lines == 3 and data.records == 2 and len(data.findings) == 1


def test_invalid_csv_row_preserves_extra_evidence(tmp_path):
    path = tmp_path / 'invalid.csv'
    path.write_text('message\nhealthy,extra-evidence\n')
    data = analyze_dashboard(path)
    assert data.invalid_records == 1 and 'extra-evidence' in data.raw_lines[0]


def test_csv_parse_error_continues_to_later_record(tmp_path):
    path = tmp_path / 'invalid.csv'
    path.write_text('message\n"healthy"bad\nERROR timeout\n')
    data = analyze_dashboard(path)
    assert data.lines == 3 and data.records == 2 and data.invalid_records == 1
    assert len(data.findings) == 1


def test_guided_json_export_cannot_overwrite_input(tmp_path):
    path = tmp_path / 'evidence.json'
    original = '{"message":"ERROR timeout"}'
    path.write_text(original)
    with pytest.raises(ValueError, match='overwrite source'):
        investigate_path(path, tmp_path)
    assert path.read_text() == original


def test_report_hardlink_cannot_overwrite_source(tmp_path):
    path = tmp_path / 'input.log'
    original = 'ERROR timeout'
    path.write_text(original)
    target = tmp_path / 'input-aegislog-report.html'
    try:
        os.link(path, target)
    except OSError:
        pytest.skip('Hardlinks unavailable')
    with pytest.raises(ValueError, match='overwrite source'):
        write_html_report(analyze_dashboard(path), tmp_path)
    assert path.read_text() == original


def test_cli_report_preserves_input_and_uses_structured_counts(tmp_path):
    path = tmp_path / 'records.csv'
    path.write_text('message\nERROR timeout\n')
    runner = CliRunner()
    denied = runner.invoke(app, ['report', str(path), '--output', str(path)])
    assert denied.exit_code == 1 and 'overwrite source' in denied.stdout
    output = tmp_path / 'output.json'
    result = runner.invoke(app, ['report', str(path), '--output', str(output)])
    assert result.exit_code == 0
    payload = json.loads(output.read_text())
    assert payload['lines'] == 2 and payload['records'] == 1 and len(payload['findings']) == 1


def test_docker_reads_stderr_and_rejects_option_names(monkeypatch):
    from aegislog import native_collectors as nc
    monkeypatch.setattr(nc.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=0, stdout='healthy\n', stderr='ERROR timeout\n'))
    assert len(nc.docker_logs('app')) == 2
    for invalid in ('--since=1m', '-f', 'app container'):
        with pytest.raises(nc.CollectorError):
            nc.docker_logs(invalid)


def test_structured_timeline_uses_normalized_timestamps(tmp_path):
    from aegislog.terminal_charts import minute_activity
    path = tmp_path / 'conn.json'
    path.write_text(json.dumps([{'ts':1750000000,'id.orig_h':'10.0.0.1','id.resp_h':'10.0.0.2'}]))
    data = analyze_dashboard(path)
    assert sum(minute_activity(event.raw for event in data.events).values()) == 1


def test_json_service_is_retained_without_timestamp(tmp_path):
    path = tmp_path / 'message.json'
    path.write_text('{"service":"my-service","message":"ERROR timeout"}')
    data = analyze_dashboard(path)
    assert data.services == {'my-service': 1}
    assert data.recognized_records == 1 and len(data.findings) == 1


def test_event_parser_removes_terminal_control_sequences():
    from aegislog.parsers import parse_line
    event = parse_line('ERROR \x1b]0;injected-title\x07timeout')
    assert '\x1b' not in event.raw and '\x07' not in event.message


def test_journald_short_iso_record_is_recognized(tmp_path):
    path = tmp_path / 'journal.log'
    path.write_text('2026-10-03T09:00:00+0000 host api[123]: ERROR timeout\n')
    data = analyze_dashboard(path)
    assert data.recognized_records == 1 and data.services == {'api': 1}
    assert data.levels == {'ERROR': 1} and len(data.findings) == 1
