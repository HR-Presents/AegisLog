from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from aegislog.anomaly import Anomaly
from aegislog.dashboard import DashboardData
from aegislog.engine import Finding
from aegislog.incidents import Incident
from aegislog.reporting import build_html_report, write_html_report


def _data(source: str = "/tmp/prod-auth.log") -> DashboardData:
    return DashboardData(
        source=source,
        lines=42,
        findings=(
            Finding(
                "HIGH",
                "authentication",
                "Repeated <script>alert(1)</script> failures",
                "user=admin & source=203.0.113.10",
                "Review authentication history & rotate exposed credentials.",
            ),
            Finding(
                "MEDIUM",
                "network",
                "Firewall activity",
                'src="198.51.100.7" port=445',
                "Review repeated sources and destination ports.",
            ),
        ),
        anomalies=(Anomaly(74.2, "sshd:error", "Rare concerning event class: 1/42 total events"),),
        incidents=(
            Incident(
                id="abcdef123456",
                category="authentication",
                severity="HIGH",
                count=2,
                title="Authentication attack pattern",
                evidence=("failed <img src=x onerror=alert(1)>", "failed password for admin"),
            ),
        ),
        levels={"ERROR": 9, "WARNING": 3},
        services={"sshd": 10, "firewall": 2},
        categories={"authentication": 1, "network": 1},
        severities={"HIGH": 1, "MEDIUM": 1},
    )


def test_html_report_is_self_contained_and_analyst_oriented() -> None:
    html = build_html_report(_data())

    for text in (
        "Security Investigation Report",
        "Investigation record",
        "Case ID",
        "Executive summary",
        "What needs attention",
        "Assessment",
        "Disposition",
        "IMMEDIATE REVIEW",
        "Repeated &lt;script&gt;alert(1)&lt;/script&gt; failures",
        "Recommended triage",
        "Incident Queue",
        "Findings",
        "Anomaly Signals",
        "Observed Distribution",
        "Analysis Profile",
        "Evidence limitations",
        "LOCAL / READ-ONLY",
        "DETERMINISTIC ANALYSIS",
        "Print Full Evidence / Save PDF",
    ):
        assert text in html

    for anchor in (
        "#executive",
        "#incidents",
        "#findings",
        "#anomalies",
        "#telemetry",
        "#method",
    ):
        assert anchor in html

    assert 'class="telemetry-grid"' in html
    assert 'aria-label="AegisLog terminal mark logo"' in html
    assert "#287bff" in html
    assert 'content="light"' in html
    assert 'body{margin:0;background:#fff;color:var(--ink)' in html
    assert 'Investigation Information' in html
    assert 'PRESENTED BY HR-PRESENTS' in html
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in html
    assert "REMOTE AI" not in html
    assert "@media print" in html
    assert "break-inside:avoid" in html
    assert "window.print()" in html
    assert 'src="http://' not in html
    assert 'src="https://' not in html
    assert 'href="http://' not in html
    assert 'href="https://' not in html
    assert "@import" not in html
    assert "<script src=" not in html


def test_html_report_has_stable_case_reference_for_same_snapshot() -> None:
    first = build_html_report(_data())
    second = build_html_report(_data())
    pattern = re.compile(r"AL-[A-F0-9]{10}")
    first_ids = pattern.findall(first)
    second_ids = pattern.findall(second)
    assert first_ids
    assert first_ids[0] == second_ids[0]


def test_case_reference_changes_when_retained_evidence_changes() -> None:
    original = _data()
    changed_finding = replace(original.findings[0], evidence="different retained evidence")
    changed = replace(original, findings=(changed_finding, *original.findings[1:]))
    pattern = re.compile(r"AL-[A-F0-9]{10}")

    original_id = pattern.findall(build_html_report(original))[0]
    changed_id = pattern.findall(build_html_report(changed))[0]
    assert original_id != changed_id


def test_html_report_escapes_retained_evidence() -> None:
    html = build_html_report(_data("/tmp/prod<auth>.log"))

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "user=admin &amp; source=203.0.113.10" in html
    assert "prod&lt;auth&gt;.log" in html


def test_html_report_orders_triage_by_severity() -> None:
    html = build_html_report(_data())
    high_position = html.index("Review authentication history")
    medium_position = html.index("Review repeated sources")
    assert high_position < medium_position


def test_incident_only_report_keeps_high_posture_and_primary_incident() -> None:
    incident = Incident(
        id="deadbeef1234",
        category="authentication",
        severity="HIGH",
        count=5,
        title="Correlated authentication activity",
        evidence=("failed password",),
    )
    data = DashboardData(
        source="/tmp/incident-only.log",
        lines=5,
        findings=(),
        anomalies=(),
        incidents=(incident,),
        levels={"ERROR": 5},
        services={"sshd": 5},
        categories={},
        severities={},
    )
    html = build_html_report(data)

    assert "Current posture" in html
    assert ">HIGH<" in html
    assert "IMMEDIATE REVIEW" in html
    assert "INC-DEADBEEF" in html
    assert "Correlated authentication activity" in html
    assert "Validate the grouped evidence" in html
    assert "No elevated rule-backed finding requires immediate action" not in html


def test_empty_report_has_clear_empty_states() -> None:
    data = DashboardData(
        source="/tmp/quiet.log",
        lines=0,
        findings=(),
        anomalies=(),
        incidents=(),
        levels={},
        services={},
        categories={},
        severities={},
    )
    html = build_html_report(data)

    assert "Current posture" in html
    assert ">CLEAR<" in html
    assert "ROUTINE REVIEW" in html
    assert "No immediate rule-backed remediation items were generated." in html
    assert "No correlated incidents were recorded." in html
    assert "No rule-backed findings were recorded." in html
    assert "No rare concerning event classes were recorded." in html
    assert "No critical, high, or medium rule-backed findings were retained" in html
    assert "No elevated rule-backed finding requires immediate action" in html


def test_write_html_report_uses_safe_predictable_filename(tmp_path: Path) -> None:
    target = write_html_report(_data("/tmp/prod auth?.log"), output_dir=tmp_path)

    assert target == tmp_path / "prod-auth-aegislog-report.html"
    assert target.is_file()
    html = target.read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "prod auth?.log" in html


def test_incident_queue_links_evidence_once_and_preserves_unmatched_excerpt():
    data = _data()
    incident = replace(data.incidents[0], evidence=(data.findings[0].evidence, "unique incident excerpt"))
    html = build_html_report(replace(data, incidents=(incident,)))
    queue = html.split('id="incidents"', 1)[1].split('id="findings"', 1)[0]
    assert 'href="#finding-001"' in queue
    assert 'id="finding-001"' in html
    assert "user=admin &amp; source=203.0.113.10" not in queue
    assert "unique incident excerpt" in queue
    assert html.count("Grouping basis:") == 1
    single = build_html_report(replace(data, incidents=(replace(incident, count=1),)))
    assert "Single-signal entries are leads" in single


def test_short_report_groups_repetitions_and_preserves_all_evidence_in_appendix(tmp_path):
    from aegislog.reporting import build_summary_report
    data = _data()
    findings = tuple(replace(data.findings[0], evidence=f"unique evidence {index}") for index in range(44))
    data = replace(data, findings=findings)
    summary = build_summary_report(data, "full-appendix.html")
    assert summary.count('class="summary-finding"') == 1
    assert '44 finding(s)' in summary
    assert summary.count('Review authentication history &amp; rotate exposed credentials.') == 1
    target = write_html_report(data, tmp_path)
    appendix = target.with_name(target.stem + '-appendix.html')
    assert appendix.name in target.read_text()
    text = appendix.read_text()
    assert target.name in text and 'Back / Print Summary' in text
    for index in range(44):
        assert f'unique evidence {index}<' in text
    assert text.count('id="finding-') == 44


def test_short_report_discloses_omitted_groups_and_links_to_full_incidents():
    from aegislog.reporting import build_summary_report
    data = _data()
    findings = tuple(replace(data.findings[0], title=f"Distinct finding {index}") for index in range(9))
    data = replace(data, findings=findings)
    summary = build_summary_report(data, "case-appendix.html")
    assert summary.count('class="summary-finding"') == 6
    assert 'Showing 6 highest-priority groups' in summary
    assert summary.count('Review authentication history &amp; rotate exposed credentials.') == 1
    assert 'Same next action as group 1' in summary
    assert '#incident-abcdef123456' in summary
    assert 'id="incident-abcdef123456"' in build_html_report(data)


def test_report_pair_cannot_overwrite_source(tmp_path):
    import pytest
    source = tmp_path / 'prod-aegislog-report-appendix.html'
    source.write_text('original')
    with pytest.raises(ValueError, match='overwrite source'):
        write_html_report(_data(str(source)), tmp_path, filename='prod-aegislog-report.html')
    assert source.read_text() == 'original'


def test_summary_embeds_brand_logo_and_readable_print_colors():
    from aegislog.reporting import build_summary_report
    html = build_summary_report(_data(), "appendix.html")
    assert 'aria-label="AegisLog terminal mark logo"' in html
    assert 'data:image/png;base64,' in html
    assert 'aegislog-report-logo' in html
    assert 'color:#245ea8!important' in html
    assert 'color:#a62b38!important' in html
    assert 'print-color-adjust:exact' in html
    assert 'class="summary-service-chart"' in html
    assert 'font-size="14"' in html


def test_full_evidence_groups_repeated_recommendations_without_losing_references():
    data = _data()
    findings = tuple(replace(data.findings[0], evidence=f"evidence {index}") for index in range(44))
    html = build_html_report(replace(data, findings=findings), summary_href='summary.html')
    findings_html = html.split('id="findings"', 1)[1].split('id="telemetry"', 1)[0]
    assert findings_html.count('class="finding-group"') == 1
    assert findings_html.count('Review authentication history &amp; rotate exposed credentials.') == 1
    assert findings_html.count('class="group-evidence"') == 44
    for index in range(1, 45):
        assert f'id="finding-{index:03d}"' in findings_html
    assert 'href="summary.html">Back / Print Summary' in html
    assert 'Print Full Evidence / Save PDF' in html


def test_body_text_is_larger_without_resizing_headings():
    from aegislog.reporting import build_summary_report
    for html in [build_html_report(_data()), build_summary_report(_data(), 'appendix.html')]:
        assert 'font-size:16px!important;line-height:1.65' in html
        assert 'font-size:13px!important;line-height:1.6' in html
        assert 'h1{font-size:38px' in html
        assert 'h2{font-size:23px' in html


def test_demo_context_and_timestamp_limits_are_explicit(tmp_path):
    from aegislog.commands_v12 import _DEMO_LOG
    from aegislog.dashboard import analyze_dashboard
    from aegislog.reporting import build_summary_report
    source = tmp_path / "arbitrary-name.log"
    source.write_text(_DEMO_LOG)
    data = analyze_dashboard(source)
    for html in (build_html_report(data), build_summary_report(data, "full.html")):
        assert "SYNTHETIC DEMO DATA" in html
        assert "does not guess" in html
        assert "Event-order correlation does not establish elapsed time" in html
    summary = build_summary_report(data, "full.html")
    assert "SUMMARY ONLY" in summary
    assert 'href="full.html?print=1"' in summary
    assert "break-before:page" not in summary
    source.write_text("2026-10-03T12:00:00Z INFO app: real input")
    real = analyze_dashboard(source)
    assert "SYNTHETIC DEMO DATA" not in build_html_report(real)
    assert "Timestamp limitations:" not in build_html_report(real)


def test_summary_opens_with_results_and_keeps_context_grouped():
    from aegislog.reporting import build_summary_report
    html = build_summary_report(_data(), 'full.html')
    assert 'class="summary-header"' in html
    assert '<dt>Source</dt>' in html and '<dt>Case</dt>' in html and '<dt>Generated</dt>' in html
    header = html.split('<header class="masthead">', 1)[1].split('</header>', 1)[0]
    assert 'Investigation Summary' in header
    assert 'AegisLog terminal mark logo' in header
    assert 'context-notice' not in header
    assert html.index('<section class="metrics">') < html.index('id="executive"') < html.index('<aside class="summary-notes"')
    notes = html.split('<aside class="summary-notes"', 1)[1].split('</aside>', 1)[0]
    assert 'SUMMARY ONLY' in notes
    assert 'Complete retained evidence is in the separate full report' in notes
    assert 'Priority lead:' in html
    assert html.index('id="executive"') < html.index('id="findings"') < html.index('id="incidents"') < html.index('id="activity"') < html.index('<aside class="summary-notes"')
    assert 'width:110px' in html
