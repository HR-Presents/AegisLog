from dataclasses import replace
from pathlib import Path
from aegislog.dashboard import analyze_dashboard
from aegislog.reporting import build_summary_report, build_html_report
from aegislog.report_company import issue_name
from aegislog.engine import Finding


def test_specific_name_preserves_detector_and_evidence():
    finding = Finding('MEDIUM', 'error', 'Operational error detected', '2026-10-04T12:00:00Z Service Control Manager[7011]: ERROR timeout', 'Review service')
    assert issue_name(finding) == 'Service response timeout'
    assert finding.title == 'Operational error detected'


def test_summary_has_no_raw_json_and_full_preserves_it(tmp_path: Path):
    path = tmp_path / 'system.log'
    path.write_text('2026-10-04T12:00:00Z Service Control Manager[7011]: ERROR timeout | AEGIS_EVENT_DATA={"Computer":"host"}\n')
    data = analyze_dashboard(path)
    brief = build_summary_report(data, 'full.html')
    assert 'Service response timeout' in brief
    assert 'AEGIS_EVENT_DATA' not in brief
    assert 'AEGIS_EVENT_DATA' in build_html_report(data)
    assert 'MADE BY HR-PRESENTS' in brief
    assert 'Full evidence' in brief


def test_user_filename_does_not_label_demo_and_html_escapes(tmp_path: Path):
    path = tmp_path / 'demo.log'
    path.write_text('ERROR <script>alert(1)</script>\n')
    data = analyze_dashboard(path)
    brief = build_summary_report(data, 'full.html')
    assert 'SYNTHETIC DEMO DATA' not in brief
    assert '<script>alert(1)</script>' not in brief
    assert '&lt;script&gt;' in brief


def test_omissions_and_partial_coverage_remain_visible(tmp_path: Path):
    path = tmp_path / 'log.txt'
    path.write_text('ERROR service unavailable\n')
    data = replace(analyze_dashboard(path), dropped_findings=4, truncated_lines=2, invalid_records=1)
    brief = build_summary_report(data, 'full.html')
    assert '4 omitted findings' in brief
    assert '2 truncated lines' in brief
    assert '1 invalid records' in brief
    assert 'recognized records' in brief


def test_full_report_keeps_provenance_only_for_renamed_issue(tmp_path):
    path = tmp_path / 'system.log'
    path.write_text('2026-10-04T12:00:00Z Service Control Manager[7011]: ERROR timeout\n')
    html = build_html_report(analyze_dashboard(path))
    assert 'Rule: Operational error detected' in html
    path.write_text('2026-10-04T12:00:00Z api[1]: ERROR timeout\n')
    html = build_html_report(analyze_dashboard(path))
    assert 'Operational error detected' in html
    assert 'Rule: Operational error detected' not in html


def test_full_demo_notice_and_technical_appendix(tmp_path):
    from aegislog.commands_v12 import _DEMO_LOG
    path = tmp_path / 'input.log'
    path.write_text(_DEMO_LOG)
    data = analyze_dashboard(path)
    html = build_html_report(data)
    assert html.count('SYNTHETIC DEMO DATA') == 1
    assert 'Timestamp limitations:' in html
    assert 'does not guess' in html
    assert 'Technical appendix' in html
    assert data.source_sha256 in html and data.retention_note in html
    assert 'id="finding-001"' in html and 'id="finding-002"' in html
    assert '<div class="section-label">Executive summary</div>' not in html
