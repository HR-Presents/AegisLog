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
        "Investigation Report", "Report reference", "Executive summary",
        "DETECTOR REVIEW PRIORITY", "HIGH", "Repeated &lt;script&gt;alert(1)&lt;/script&gt; failures",
        "Recommended review", "Incident groups", "Findings register",
        "Finding details &amp; evidence", "Collection record", "Technical appendix",
        "LOCAL / READ-ONLY / DETERMINISTIC", "Print / Save PDF",
    ):
        assert text in html
    for anchor in ("#overview", "#evidence", "#activity", "#method"):
        assert anchor in html
    assert 'class="charts"' in html
    assert 'aria-label="AegisLog logo"' in html
    assert 'content="light"' in html
    assert 'body,body *{color:#000!important}' in html
    assert 'border-left:4px solid #82c0cf' in html
    assert 'grid-template-columns:repeat(4,1fr)' in html
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

    assert "DETECTOR REVIEW PRIORITY" in html
    assert ">HIGH<" in html
    assert "DETECTOR REVIEW PRIORITY / HIGH" in html
    assert "INC-DEADBEEF" in html
    assert "Correlated authentication activity" in html
    assert "Incident evidence requires review" in html
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

    assert "DETECTOR REVIEW PRIORITY" in html
    assert "DETECTOR REVIEW PRIORITY / ROUTINE REVIEW" in html
    assert "ROUTINE REVIEW" in html
    assert "No correlated incidents were recorded." in html
    assert "No rule-backed findings were recorded." in html
    assert "No rare concerning event classes were recorded." in html
    assert "No matching detections were recorded in the supplied evidence" in html
    assert "not a clean-system verdict" in html


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
    queue = html.split('Incident groups</h3>', 1)[1].split('<details class="supporting">', 1)[0]
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
    assert summary.count('class="issue"') == 1
    assert '44 occurrence(s)' in summary
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
    assert summary.count('class="issue"') == 6
    assert 'Showing 6 of 9 presentation groups' in summary
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
    assert 'alt="AegisLog terminal mark logo"' in html
    assert 'data:image/png;base64,' in html
    assert 'color:#000' in html and '#b9e6ed' in html
    assert 'print-color-adjust:exact' in html
    assert 'class="provider-bar"' in html
    assert 'MADE BY HR-PRESENTS' in html


def test_full_evidence_groups_repeated_recommendations_without_losing_references():
    data = _data()
    findings = tuple(replace(data.findings[0], evidence=f"evidence {index}") for index in range(44))
    html = build_html_report(replace(data, findings=findings), summary_href='summary.html')
    findings_html = html.split('id="evidence"', 1)[1].split('id="activity"', 1)[0]
    assert findings_html.count('class="evidence-record"') == 1
    assert findings_html.count('Review authentication history &amp; rotate exposed credentials.') == 1
    assert findings_html.count('class="excerpt"') == 44
    for index in range(1, 45):
        assert f'id="finding-{index:03d}"' in findings_html
    assert 'href="summary.html">Back / Print Summary' in html
    assert 'Print / Save PDF' in html


def test_report_body_and_headings_have_separate_sizes():
    from aegislog.report_company import COMPANY_STYLE, COMPANY_FULL_STYLE
    assert '.issue-columns p{font-size:15px' in COMPANY_STYLE
    assert '.issue-heading h3{flex:1;margin:0;font-size:17px}' in COMPANY_STYLE
    assert '.finding-columns p{font-size:15px!important}' in COMPANY_FULL_STYLE
    assert '.issue-columns p{font-size:12px;line-height:1.35}' in COMPANY_STYLE


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
    assert ".support-page{break-before:page}" not in summary
    source.write_text("2026-10-03T12:00:00Z INFO app: real input")
    real = analyze_dashboard(source)
    assert "SYNTHETIC DEMO DATA" not in build_html_report(real)
    assert "Timestamp limitations:" not in build_html_report(real)


def test_summary_uses_sea_blue_brief_and_keeps_context_grouped():
    from aegislog.reporting import build_summary_report
    html = build_summary_report(_data(), 'full.html')
    assert 'class="company-header"' in html
    assert 'Report reference' in html and 'Generated' in html
    assert '#b9e6ed' in html and 'background:#eaf8fa' in html
    assert html.index('class="conclusion"') < html.index('class="metric-strip"') < html.index('class="issue"')
    assert html.index('Activity &amp; correlation') < html.index('Collection scope &amp; interpretation') < html.index('MADE BY HR-PRESENTS')
    assert 'SUMMARY ONLY' in html and 'width:250px' in html


def test_summary_keeps_readable_evidence_and_exposes_collection_limits():
    from html import escape
    from aegislog.reporting import build_summary_report
    evidence = 'Failed password for admin from 203.0.113.10; ' * 5 + 'session=complete <untrusted>'
    data = _data()
    data = replace(data, findings=(replace(data.findings[0], evidence=evidence),),
                   record_count=42, recognized_records=40, format_counts={'syslog': 40},
                   invalid_records=2, dropped_findings=3, dropped_auth_events=4, truncated_lines=1)
    html = build_summary_report(data, 'full.html')
    from aegislog.report_company import brief_evidence
    assert escape(brief_evidence(data.findings[0])) in html
    assert escape(evidence) in build_html_report(data)
    assert '<untrusted>' not in html
    assert '40 / 42' in html
    assert '2 invalid records' in html
    assert '3 omitted findings' in html
    assert '4 evicted authentication events' in html
    assert '1 truncated lines' in html
    assert 'Formats: {' not in html
    assert '#finding-001' in html


def test_report_observed_facts_do_not_invent_missing_fields():
    from aegislog.report_design import observed_facts
    finding = Finding('MEDIUM', 'error', 'Error', 'ERROR unstructured message <script>', 'Review')
    facts = observed_facts(finding)
    assert 'Unresolved' in facts
    assert 'Account' not in facts and 'Source address' not in facts
    assert '<script>' not in facts

def test_report_evidence_disclosure_keeps_print_and_anchor_support():
    html = build_html_report(_data())
    assert 'id="aegislog-report"' in html
    # Finding excerpts are always visible; direct anchors need no disclosure script.
    assert 'class="excerpt" id="finding-001"' in html
    assert 'Observed evidence' in html and 'Recommended review' in html
    assert 'body,body *{color:#000!important}' in html
    assert '.evidence-record{break-inside:auto}' in html


def test_summary_avoids_duplicate_disposition_and_bounds_excerpts():
    from aegislog.reporting import build_summary_report
    html = build_summary_report(_data(), 'appendix.html')
    assert html.count('IMMEDIATE REVIEW') == 1
    assert 'Recognized records' in html
    data = _data()
    long_finding = replace(data.findings[0], evidence='long evidence ' * 100)
    html = build_summary_report(replace(data, findings=(long_finding, data.findings[1])), 'appendix.html')
    assert long_finding.evidence not in html
    assert long_finding.evidence in build_html_report(replace(data, findings=(long_finding,)))
    assert '#finding-001' in html
