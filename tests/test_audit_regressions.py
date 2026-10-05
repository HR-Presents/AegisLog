import json
import os
from pathlib import Path

import pytest

from aegislog.dashboard import analyze_dashboard
from aegislog.investigation import load_investigation
from aegislog.multisource import MultiSourceState
from aegislog.product import finish_investigation
from aegislog.security_workbench import investigate_file
from aegislog.streaming import analyze_stream


def test_sidecar_collision_preserves_source_before_report_write(tmp_path):
    source = tmp_path / 'activity-baseline.json'
    original = '{"message":"INFO benign"}'
    source.write_text(original)
    with pytest.raises(ValueError, match='overwrite source'):
        finish_investigation(analyze_dashboard(source), tmp_path)
    assert source.read_text() == original
    assert not list(tmp_path.glob('*.html'))


def test_hardlinked_case_sidecar_preserves_source(tmp_path):
    source = tmp_path / 'original.log'
    source.write_text('2026-10-04T10:00:00Z app: ERROR timeout\n')
    os.link(source, tmp_path / 'original-aegislog-report-case.json')
    with pytest.raises(ValueError):
        finish_investigation(analyze_dashboard(source), tmp_path)
    assert 'ERROR timeout' in source.read_text()
    assert not list(tmp_path.glob('*.html'))


def test_report_incident_can_be_opened_by_cli_identity():
    source = Path('docs/demo/first-investigation.log')
    data = analyze_dashboard(source)
    _, incidents, _ = load_investigation(source)
    assert {f'INC-{i.id[:8].upper()}' for i in data.incidents} == {i.id for i in incidents}


def test_same_basename_sources_remain_distinct(tmp_path):
    paths = (tmp_path / 'a' / 'app.log', tmp_path / 'b' / 'app.log')
    state = MultiSourceState(paths)
    for path in paths:
        state.ingest(path, ['INFO normal'])
    assert len(state.source_counts) == 2
    assert list(state.source_counts.values()) == [1, 1]


def test_suricata_alert_consistent_across_analysis_surfaces(tmp_path):
    source = tmp_path / 'eve.jsonl'
    source.write_text(json.dumps(dict(timestamp='2026-10-04T10:00:00Z', event_type='alert',
                                    src_ip='203.0.113.5', dest_ip='203.0.113.6',
                                    alert=dict(severity=1, signature='Synthetic alert'))) + '\n')
    assert any(f.severity == 'HIGH' for f in analyze_dashboard(source).findings)
    assert any(s.finding.severity == 'HIGH' for s in investigate_file(source).signals)
    assert any(f.severity == 'HIGH' for f in analyze_stream(source).findings)


def test_custom_rule_is_in_generated_report(tmp_path, monkeypatch):
    import re
    from typer.testing import CliRunner
    from aegislog import commands_v11
    from aegislog.cli import app
    from aegislog.plugins import PluginRule
    source = tmp_path / 'custom.log'
    source.write_text('INFO custom-marker\n')
    rule = PluginRule('local-test', 'CRITICAL', 'custom', 'Unique audit rule',
                      re.compile('custom-marker'), 'Review test evidence', 'test.json')
    monkeypatch.setattr(commands_v11, 'load_rules', lambda: ([rule], []))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ['analyze', str(source)])
    assert result.exit_code == 0, result.output
    assert commands_v11.last_report is not None
    html = commands_v11.last_report.read_text()
    assert 'Unique audit rule' in html
    assert 'CRITICAL' in html
