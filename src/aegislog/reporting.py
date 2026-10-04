from __future__ import annotations

from .report_paths import default_report_dir
from .report_design import REPORT_EVIDENCE_SCRIPT, observed_facts, why_it_matters
from .report_reference import document_cover, document_contents
from .report_styles import report_stylesheet
from .report_editorial import activity_timeline, report_signature

import hashlib
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from . import __version__
from .dashboard import DashboardData

_SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}








def _safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value)
    return cleaned.strip("-") or "analysis"


def _severity_rank(value: str) -> int:
    return _SEVERITY_RANK.get(value.upper(), 0)


def _risk(data: DashboardData) -> str:
    severities = set(data.severities)
    severities.update(item.severity for item in data.incidents)
    if "CRITICAL" in severities:
        return "CRITICAL"
    if "HIGH" in severities:
        return "HIGH"
    if "MEDIUM" in severities:
        return "REVIEW"
    return "CLEAR"


def _risk_class(value: str) -> str:
    return {
        "CRITICAL": "danger",
        "HIGH": "danger",
        "REVIEW": "warning",
        "MEDIUM": "warning",
        "CLEAR": "good",
        "LOW": "neutral",
        "INFO": "neutral",
    }.get(value, "neutral")


def _disposition(risk: str) -> str:
    return {
        "CRITICAL": "IMMEDIATE REVIEW",
        "HIGH": "IMMEDIATE REVIEW",
        "REVIEW": "ANALYST REVIEW",
        "CLEAR": "ROUTINE REVIEW",
    }[risk]


def _case_id(data: DashboardData) -> str:
    parts = [data.source, str(data.lines)]
    parts.extend(
        f"F|{i.severity}|{i.category}|{i.title}|{i.evidence}|{i.recommendation}"
        for i in data.findings
    )
    parts.extend(
        f"I|{i.id}|{i.severity}|{i.category}|{i.count}|{i.title}|{'|'.join(i.evidence)}"
        for i in data.incidents
    )
    parts.extend(f"A|{i.score:.6f}|{i.key}|{i.reason}" for i in data.anomalies)
    digest = hashlib.sha256("\x1e".join(parts).encode("utf-8", errors="replace")).hexdigest()[:10].upper()
    return f"AL-{digest}"


def _ordered_findings(data: DashboardData):
    return sorted(data.findings, key=lambda i: (-_severity_rank(i.severity), i.category, i.title))


def _ordered_incidents(data: DashboardData):
    return sorted(
        data.incidents,
        key=lambda i: (-_severity_rank(i.severity), -i.count, i.category, i.title),
    )


def _assessment(data: DashboardData, risk: str) -> str:
    if risk == "CRITICAL":
        return "Critical findings need prompt review. Check the evidence against the original logs and the affected system before taking action."
    if risk == "HIGH":
        return "High-severity findings need review. Verify the activity on the affected system before deciding whether to escalate."
    if risk == "REVIEW":
        return "Review the medium-severity findings. Check the affected component and surrounding logs before escalating."
    return "No elevated rule-backed findings were recorded in this input. Limited coverage means this is not a clean-system verdict."


def _metric(label: str, value: str, modifier: str = "") -> str:
    suffix = f" {modifier}" if modifier else ""
    return f'<article class="metric{suffix}"><span>{escape(label)}</span><strong>{escape(value)}</strong></article>'


def _severity_overview(data: DashboardData) -> str:
    total = max(sum(data.severities.values()), 1)
    if sum(data.severities.values()) < 10:
        counts = ''.join(f'<span><strong>{escape(str(name))}</strong> {count}</span>' for name, count in sorted(data.severities.items()))
        return '<div class="activity-counts">' + counts + '</div>' if counts else '<p class="caveat">No rule-backed severity counts in this input.</p>'
    rows = []
    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        count = data.severities.get(severity, 0)
        if not count:
            continue
        percent = min(100.0, (count / total) * 100.0)
        rows.append(
            f'<div class="severity-row {_risk_class(severity)}"><small>{severity}</small><strong>{count}</strong><svg width="100%" height="8" role="img" aria-label="{severity}: {count}"><rect width="100%" height="8" fill="#cbd5e1"/><rect width="{percent:.1f}%" height="8" fill="#299aa7"/></svg></div>'
        )
    return "".join(rows) or '<p class="caveat">No rule-backed severity counts in this input.</p>'


def _primary_decision(data: DashboardData) -> str:
    findings = _ordered_findings(data)
    incidents = _ordered_incidents(data)
    top_finding = findings[0] if findings else None
    top_incident = incidents[0] if incidents else None
    if top_incident and (
        top_finding is None
        or _severity_rank(top_incident.severity) >= _severity_rank(top_finding.severity)
    ):
        iid = f"INC-{top_incident.id.upper()[:8]}"
        return f'<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill {_risk_class(top_incident.severity)}">{escape(top_incident.severity)}</span></div><div class="lead">{escape(iid)} · {escape(top_incident.title)}</div></div>'
    if top_finding:
        return f'<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill {_risk_class(top_finding.severity)}">{escape(top_finding.severity)}</span></div><div class="lead">{escape(top_finding.title)}</div></div>'
    return '<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill good">NO MATCHES</span></div><div class="lead">No elevated rule-backed finding requires immediate action</div></div>'


def _triage_actions(data: DashboardData) -> str:
    actions = []
    seen = set()
    for number, ((severity, _category, title, recommendation), _members) in enumerate(_finding_groups(data), 1):
        if not recommendation or recommendation in seen:
            continue
        seen.add(recommendation)
        actions.append(f'<div class="triage-item"><span class="pill {_risk_class(severity)}">{escape(severity)}</span>'
                       f'<div><strong>{escape(title)}</strong><a href="#full-action-{number}">Read recommended action and evidence</a></div></div>')
        if len(actions) == 3:
            break
    if not actions and data.incidents:
        return '<p>Validate the grouped evidence against original telemetry, source identity and time proximity before escalation.</p>'
    return "".join(actions) if actions else '<div class="empty">No immediate rule-backed remediation items were generated.</div>'


def _incident_records(data: DashboardData) -> str:
    rows = []
    findings = _ordered_findings(data)
    for item in _ordered_incidents(data):
        references = []
        unmatched = []
        for evidence in item.evidence:
            matches = [index for index, finding in enumerate(findings, 1)
                       if finding.evidence == evidence]
            if matches:
                references.extend(matches)
            else:
                unmatched.append(evidence)
        links = " ".join(f'<a href="#finding-{index:03d}">F-{index:03d}</a>'
                         for index in dict.fromkeys(references))
        extra = "".join(f'<code class="evidence">{escape(value)}</code>'
                        for value in unmatched)
        rows.append(
            f'<tr id="incident-{escape(item.id)}"><td><strong>INC-{escape(item.id.upper()[:8])}</strong></td>'
            f'<td><span class="pill {_risk_class(item.severity)}">{escape(item.severity)}</span></td>'
            f'<td><strong>{escape(item.title)}</strong><small class="incident-context">{escape(item.context)}</small></td>'
            f'<td>{item.count}</td><td>{links}{extra}</td></tr>'
        )
    if not rows:
        return '<div class="empty">No correlated incidents were recorded.</div>'
    return ('<p class="caveat">Grouping basis: detector category/title and extracted service or source context '
            'where available. Windows groups also use Event ID, observed host/account, and a maximum five-minute span. '
            'Legacy generic grouping has no time-window constraint '
            'and does not establish a common cause. Single-signal entries are leads, not corroborated sequences. '
            'Evidence references below point to the retained excerpts in Findings; counts may exceed retained excerpts.</p>'
            '<div class="table-wrap"><table class="incident-table"><thead><tr><th>Incident</th><th>Severity</th><th>Signal / interpretation</th>'
            '<th>Count</th><th>Retained evidence</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>')


def _recommendation(item) -> str:
    evidence = item.evidence.lower()
    if item.category == "error" and "service control manager[7011]" in evidence:
        return "Check the named service's own logs and dependencies around this timeout; compare restart history, CPU, memory and disk pressure. Validate the cause before changing service settings."
    if item.category == "error" and "distributedcom[10010]" in evidence:
        return "Identify the application associated with the recorded CLSID, check its startup and related service logs, and establish user impact. This timeout alone does not justify changing DCOM permissions."
    return item.recommendation


def _bar_chart(values: dict[str, int], label: str) -> str:
    items = sorted(values.items(), key=lambda pair: (-pair[1], str(pair[0])))[:8]
    if not items:
        return '<p class="empty">No retained observations.</p>'
    if sum(values.values()) < 20:
        counts = ''.join(f'<span><strong>{escape(str(name))}</strong> {value:,}</span>' for name, value in items)
        return '<div class="activity-counts">' + counts + '</div><p class="caveat">Small sample; direct observed counts.</p>'
    maximum = max(value for _, value in items) or 1
    rows = []
    for name, value in items:
        width = min(100.0, max(0.0, 100 * value / maximum))
        rows.append(f'<div class="distribution-row"><span>{escape(str(name))}</span><strong>{value:,}</strong><div class="distribution-track"><i style="width:{width:.1f}%"></i></div></div>')
    return f'<div class="chart" role="img" aria-label="{escape(label)}">{"".join(rows)}</div><p class="caveat">Top {len(items)} of {len(values)} classes; retained total {sum(values.values()):,}. Largest bar = {maximum:,}.</p>'



def _finding_records(data: DashboardData) -> str:
    records = []
    seen_actions = {}
    for group_number, ((severity, category, title, recommendation), members) in enumerate(_finding_groups(data), 1):
        if recommendation in seen_actions:
            action = f'<a href="#full-action-{seen_actions[recommendation]}">See recommended action for group {seen_actions[recommendation]}</a>'
        else:
            seen_actions[recommendation] = group_number
            action = f'<span id="full-action-{group_number}">{escape(recommendation)}</span>'
        evidence = "".join(
            f'<div class="group-evidence" id="finding-{index:03d}"><span class="record-id">F-{index:03d}<small class="evidence-group">Group G-{group_number:03d}</small></span>'
            f'<code class="evidence">{escape(item.evidence)}</code></div>'
            for index, item in members
        )
        records.append(
            f'<article class="finding-group"><div class="group-intro"><div class="group-label">Presentation group G-{group_number:03d}</div><div class="record-head">'
            f'<span class="pill {_risk_class(severity)}">{escape(severity)}</span><strong>{escape(title)}</strong>'
            f'<span class="record-meta">{len(members)} finding(s) · {escape(category)}</span></div>'
            f'<div class="finding-columns"><div><span class="cell-label">Observed evidence · first retained excerpt</span>{observed_facts(members[0][1], data.timestamp_year_hint)}</div>'
            f'<div><span class="cell-label">Next step</span><p class="action-text">{action}</p><p class="why"><strong>Why it matters:</strong> {escape(why_it_matters(category))}</p></div></div></div>'
            f'<details class="report-evidence" open><summary>Inspect all retained evidence · {len(members)} finding(s)</summary>{evidence}</details></article>' 
        )
    return "".join(records) if records else '<div class="empty">No rule-backed findings were recorded.</div>'


def _anomaly_rows(data: DashboardData) -> str:
    rows = "".join(
        f'<tr><td><strong>{i.score:.1f}</strong></td><td><code>{escape(i.key)}</code></td><td>{escape(i.reason)}</td></tr>'
        for i in data.anomalies
    )
    return rows or '<tr><td colspan="3" class="empty">No rare concerning event classes were recorded.</td></tr>'


def _telemetry_chips(values: dict[str, int]) -> str:
    if not values:
        return '<span class="chip">none</span>'
    return "".join(
        f'<span class="chip">{escape(str(k))} <strong>{v}</strong></span>'
        for k, v in sorted(values.items(), key=lambda p: (-p[1], p[0]))
    )


def _report_context(data: DashboardData) -> str:
    # Match retained content, never a user-controlled filename, to identify the built-in fixture.
    from .commands_v12 import _DEMO_LOG
    is_demo = tuple(line.rstrip() for line in data.raw_lines) == tuple(_DEMO_LOG.splitlines())
    demo = ('<p class="context-notice"><strong>SYNTHETIC DEMO DATA</strong> '
            'Training signals only. Review priorities apply to this fixture, not your computer.</p>') if is_demo else ''
    from .engine import _parse_timestamp
    missing = sum(_parse_timestamp(line, data.timestamp_year_hint) is None for line in data.raw_lines)
    timing = (f'<p class="context-notice"><strong>Timestamp limitations:</strong> {missing} retained record(s) lack a resolved timestamp. '
              'Traditional syslog may omit the year; AegisLog does not guess it. '
              'Use an explicit timestamp year when known. Event-order correlation does not establish elapsed time or a time-window attack.</p>') if missing else ''
    diagnostics = ('<p class="context-notice"><strong>Windows diagnostic reports:</strong> '
                   'Repeated report records are not counts of unique failures. The record timestamp can describe report submission; '
                   'check the original dump or application log for the failure time.</p>') if any(
                       dict(f.context).get('provider', '').casefold() == 'windows error reporting'
                       for f in data.findings) else ''
    return demo + timing + diagnostics


def _identity_rows(data: DashboardData) -> str:
    digest = data.source_sha256 or 'Unavailable for this analysis'
    return ('<tr><th>Source SHA-256</th><td class="source-fingerprint">' + escape(digest) + '</td></tr>'
            '<tr><th>Identity scope</th><td>Report ID identifies analysis output, not source bytes. '
            'SHA-256 identifies bytes read during collection, including truncated tails; '
            'it does not certify an unchanged or complete live source.</td></tr>')


def _record_metrics(data: DashboardData, *, summary: bool) -> str:
    last = (_metric('Recognized records', f'{data.recognized_records:,} / {data.records:,}') if summary else
            _metric('Disposition', _disposition(_risk(data)), _risk_class(_risk(data))))
    return ('<section class="metrics" id="metrics">' + _metric('Records processed', f'{data.records:,}') +
            _metric('Finding occurrences', str(len(data.findings))) + _metric('Incident groups', str(len(data.incidents))) + last + '</section><p class="count-key">' + f'{len(_finding_groups(data))} finding presentation groups. Occurrences count retained detector findings; incident groups organize signals and are not confirmed incidents.' + '</p>')


def _document_opening(data: DashboardData, generated: str, *, summary: bool, appendix_href: str = '') -> str:
    from .brand_logo import report_logo_uri
    source = data.source_label or Path(data.source).name
    formats = ', '.join(sorted(data.format_counts or {})) or 'Generic / unresolved'
    cover = document_cover(source, _case_id(data), formats, generated, report_logo_uri(),
                           summary=summary, demo='SYNTHETIC DEMO DATA' in _report_context(data))
    return cover


def _report_navigation(*, summary: bool, appendix_href: str = '') -> str:
    entries = [('#executive', 'Executive Summary'), ('#metrics', 'Record Overview')]
    if summary:
        entries += [('#findings', 'Findings & Next Actions'), ('#incidents', 'Priority Incidents'),
                    ('#activity', 'Supporting Activity'), ('#interpretation', 'Interpretation Notes'),
                    ('#scope', 'Coverage'), (appendix_href, 'Complete Investigation Record')]
    else:
        entries += [('#findings', 'Findings'),
                    ('#incidents', 'Incident Queue'), ('#source', 'Investigation Information'), ('#telemetry', 'Observed Distribution'),
                    ('#anomalies', 'Anomaly Signals'), ('#method', 'Analysis Profile')]
    return document_contents(entries)


def build_html_report(data: DashboardData, summary_href: str | None = None) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    source_name = data.source_label or Path(data.source).name
    risk = _risk(data)
    case_id = _case_id(data)
    summary_link = (f'<a class="report-button" href="{escape(summary_href)}">Back / Print Summary</a>'
                    if summary_href else '<a href="#executive">Back to overview</a>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>AegisLog Investigation Report - {escape(source_name)}</title><style>{report_stylesheet()}</style></head><body><main id="aegislog-report" class="report">
{_document_opening(data, generated, summary=False)}

<nav class="toolbar">{summary_link}<a href="#executive">Overview</a><a href="#incidents">Incidents</a><a href="#findings">Findings</a><a href="#telemetry">Telemetry</a><a href="#anomalies">Anomalies</a><a href="#method">Method</a><span class="spacer"></span><span class="local-note">DETERMINISTIC ANALYSIS</span><button type="button" onclick="window.print()">Print Full Evidence / Save PDF</button></nav>
<p class="print-help">PDF export: use A4 and turn off browser Headers and footers in the print dialog to remove the local file URL. Background graphics are optional; charts and evidence remain readable.</p><div class="content">
<section class="section" id="executive"><div class="section-head"><div><div class="section-label">Executive summary</div><h2>Executive Summary</h2></div><div class="section-note">Start here. Supporting evidence follows below.</div></div><div class="executive-grid"><div class="assessment"><h3>Assessment</h3><p class="posture-value">Current posture <strong>{escape(risk)}</strong></p><p>{escape(_lead_observation(data, risk))}</p>{_primary_decision(data)}<h3 class="severity-heading">Severity distribution</h3><div class="severity-block">{_severity_overview(data)}</div></div><div class="priority-box"><h3>Recommended triage</h3>{_triage_actions(data)}</div></div></section>
{_record_metrics(data, summary=False)}
{_report_navigation(summary=False)}
<section class="section" id="findings"><div class="section-head"><div><div class="section-label">Detection</div><h2>Findings</h2></div><div class="section-note">{len(data.findings)} retained findings in {len(_finding_groups(data))} presentation groups. Each excerpt keeps its F-reference. Grouping for readability does not establish a common cause.</div></div><div class="record-list">{_finding_records(data)}</div></section>
<section class="section" id="incidents"><div class="section-head"><div><div class="section-label">Correlation</div><h2>Incident Queue</h2></div><div class="section-note">Grouped signals; validate shared cause and timing.</div></div><div class="record-list">{_incident_records(data)}</div></section>
<section class="section" id="source"><div class="section-head"><h2>Investigation Information</h2></div><div class="case-strip"><div><small>Source</small><strong>{escape(source_name)}</strong></div><div><small>Case ID</small><strong>{escape(case_id)}</strong></div><div><small>Status</small><strong>Analysis complete</strong></div><div><small>Generated</small><strong>{generated}</strong></div><div><small>Processing</small><strong>LOCAL / READ-ONLY / DETERMINISTIC</strong></div></div></section>
<section class="section" id="telemetry"><div class="section-head"><div><div class="section-label">Telemetry</div><h2>Observed Distribution</h2></div><div class="section-note">A compact view of the parsed source.</div></div>{activity_timeline(data.raw_lines, data.timestamp_year_hint)}<div class="telemetry-grid"><div class="telemetry-card"><h3>Categories</h3><div class="chips">{_telemetry_chips(data.categories)}</div></div><div class="telemetry-card"><h3>Log levels</h3><div class="chips">{_bar_chart(data.levels, "Log levels")}</div></div><div class="telemetry-card"><h3>Services</h3><div class="chips">{_bar_chart(data.services, "Service activity")}</div></div></section>
<section class="section" id="anomalies"><div class="section-head"><div><div class="section-label">Behavior</div><h2>Anomaly Signals</h2></div><div class="section-note">Rarity scores (0-100), not attack probability.</div></div><p class="caveat">Scores describe rare concerning event classes within this retained sample. A score of 100 does not mean 100% attack probability, severity, or confidence. No trained machine-learning model is used.</p><div class="table-wrap"><table><thead><tr><th>Rarity score / 100</th><th>Event class</th><th>Reason</th></tr></thead><tbody>{_anomaly_rows(data)}</tbody></table></div></section>
<section class="section" id="method"><div class="section-head"><div><div class="section-label">Method and scope</div><h2>Analysis Profile</h2></div><div class="section-note">How the report was produced and how to interpret it.</div></div>{_report_context(data)}<div class="method-grid"><div class="method-card"><h3>Processing model</h3><p>AegisLog v{escape(__version__)} performed local deterministic detection, incident correlation, and anomaly scoring. The source was handled read-only.</p></div><div class="method-card"><h3>Evidence limitations</h3><p>{escape(data.collection_scope)} {escape(data.retention_note)} {escape(data.coverage_note)} This report contains retained derived evidence rather than a complete copy of the raw log. Missing detections do not prove malicious activity is absent. Preserve original telemetry when incident-response, retention, or chain-of-custody procedures require it.</p></div></div><div class="table-wrap" style="margin-top:14px"><table>{_identity_rows(data)}<tr><th>Source path</th><td>{escape(data.source)}</td></tr><tr><th>Source file</th><td>{escape(source_name)}</td></tr><tr><th>Physical lines</th><td>{data.lines:,}</td></tr><tr><th>AegisLog version</th><td>{escape(__version__)}</td></tr><tr><th>Generated</th><td>{generated}</td></tr><tr><th>Analysis model</th><td>Deterministic local processing</td></tr></table></div></section>
{report_signature(case_id, __version__)}</div></main>{REPORT_EVIDENCE_SCRIPT}<script>if(new URLSearchParams(location.search).get("print")==="1"){{window.addEventListener("load",()=>window.print());}}</script></body></html>'''


def _finding_groups(data: DashboardData):
    """Presentation groups only: no new incident or shared-cause inference."""
    groups = {}
    for index, item in enumerate(_ordered_findings(data), 1):
        key = (item.severity, item.category, item.title, _recommendation(item))
        groups.setdefault(key, []).append((index, item))
    return list(groups.items())


def _summary_brand() -> str:
    from .brand_logo import report_logo_uri
    return (
        '<style>.aegislog-report-logo{display:block;width:190px;max-width:100%;height:auto;'
        'background:transparent;print-color-adjust:exact;-webkit-print-color-adjust:exact}'
        '@media print{.aegislog-report-logo{width:110px}}</style>'
        '<div class="summary-brand"><img class="aegislog-report-logo" '
        'alt="AegisLog terminal mark logo" aria-label="AegisLog terminal mark logo" '
        f'src="{report_logo_uri()}"></div>'
        '<div class="brand-sub">PRESENTED BY HR-PRESENTS</div>'
    )


def _summary_service_chart(values: dict[str, int]) -> str:
    items = sorted(values.items(), key=lambda pair: (-pair[1], str(pair[0])))[:6]
    if not items:
        return '<p class="empty">No retained observations.</p>'
    maximum = max(value for _, value in items) or 1
    rows = []
    for name, value in items:
        width = 100 * value / maximum
        rows.append(f'<div class="distribution-row"><span>{escape(str(name))}</span><strong>{value:,}</strong><div class="distribution-track"><i style="width:{width:.1f}%"></i></div></div>')
    return f'<div class="summary-service-chart" role="img" aria-label="Service activity">{"".join(rows)}</div><p class="caveat">Top {len(items)} of {len(values)} services · {sum(values.values()):,} events.</p>'



def _lead_observation(data: DashboardData, risk: str) -> str:
    priority = _ordered_findings(data)
    if priority:
        burst = re.match(r'^(\d+) authentication failures\b', priority[0].evidence)
        if burst:
            return (f'Retained evidence includes {int(burst.group(1)):,} authentication failures in a detector-grouped burst. '
                    'Check the account, source, and successful login activity before escalating.')
        if dict(priority[0].context).get('provider', '').casefold() == 'windows error reporting':
            return ('Windows diagnostic report records need review. Repeated submissions do not establish separate failures; '
                    'compare original dump times and user impact.')
    return _assessment(data, risk)


def _supporting_activity(data: DashboardData) -> str:
    timeline = activity_timeline(data.raw_lines, data.timestamp_year_hint)
    if data.records < 20:
        severity = ' · '.join(f'{escape(str(name))}: {count}' for name, count in sorted(data.severities.items())) or 'No rule-backed findings'
        services = ''.join(f'<span><strong>{escape(str(name))}</strong> {count:,}</span>' for name, count in sorted(data.services.items(), key=lambda pair: (-pair[1], str(pair[0])))[:6])
        return (timeline + '<p class="activity-note">Small sample: direct counts below.</p>'
                '<div class="summary-service-chart"><h3>Observed source activity</h3><div class="activity-counts">' + services + '</div></div>'
                f'<p class="caveat">Finding severity · {severity}. Service counts describe processed records, not distinct incidents.</p>')
    return (timeline + '<div class="summary-chart-grid"><div><h3>Finding severity</h3>' + _severity_overview(data) +
            '</div><div><h3>Source activity</h3>' + _summary_service_chart(data.services) + '</div></div>')


def build_summary_report(data: DashboardData, appendix_href: str) -> str:
    groups = _finding_groups(data)
    compact = len(groups) == 2 and all(
        len(members[0][1].evidence) <= 600 and len(key[3]) <= 250 and len(key[2]) <= 100
        for key, members in groups
    )
    diagnostic_compact = compact and all(
        dict(members[0][1].context).get('provider', '').casefold() == 'windows error reporting'
        for _, members in groups
    )
    rows = []
    seen_actions = {}
    for group_number, ((severity, category, title, recommendation), members) in enumerate(groups[:6], 1):
        index, example = members[0]
        excerpt = example.evidence
        excerpt_label = 'Representative evidence'
        if len(excerpt) > 1200:
            excerpt = excerpt[:1200].rsplit(' ', 1)[0]
            excerpt_label = 'Evidence excerpt - continued in full report' 
        if recommendation in seen_actions:
            action = f'<a href="#action-{seen_actions[recommendation]}">Same next action as group {seen_actions[recommendation]}</a>'
        else:
            seen_actions[recommendation] = group_number
            action = f'<span id="action-{group_number}">{escape(recommendation)}</span>'
        rows.append(
            f'<article class="summary-finding"><div class="finding-index">F-{index:03d}</div><div class="finding-content"><div class="record-head"><span class="pill {_risk_class(severity)}">{escape(severity)}</span>'
            f'<strong>{escape(title)}</strong><span class="record-meta">{len(members)} finding(s) · {escape(category)}</span></div>'
            f'<div class="finding-columns"><div><span class="cell-label">Observed evidence</span>{observed_facts(example, data.timestamp_year_hint)}</div>'
            f'<div><span class="cell-label">Next step</span><p class="action-text">{action}</p><p class="why"><strong>Why it matters:</strong> {escape(why_it_matters(category))}</p></div></div>'
            f'<details class="report-evidence" open><summary>Inspect {escape(excerpt_label.lower())}</summary><code class="evidence">{escape(excerpt)}</code>' 
            f'<a class="evidence-link" href="{escape(appendix_href)}#finding-{index:03d}">View complete evidence → F-{index:03d}</a></details>'
            + (f'<p class="summary-evidence-pointer"><a href="{escape(appendix_href)}#finding-{index:03d}">Complete retained evidence: F-{index:03d} in the investigation record.</a></p>' if diagnostic_compact else '')
            + '</div></article>'
        )
    group_note = (f'Showing {min(6, len(groups))} highest-priority groups · '
                  f'{len(data.findings)} retained findings. Complete evidence is linked below.')
    incident_rows = "".join(
        f'<tr><td><a href="{escape(appendix_href)}#incident-{escape(item.id)}">INC-{escape(item.id.upper()[:8])}</a></td>'
        f'<td><span class="pill {_risk_class(item.severity)}">{escape(item.severity)}</span></td>'
        f'<td>{escape(item.title)}<small class="incident-context">{escape(item.context)}</small></td><td>{item.count}</td></tr>'
        for item in _ordered_incidents(data)[:5]
    )
    incident_content = ('<div class="table-wrap"><table><thead><tr><th>Incident</th><th>Severity</th><th>Signal</th><th>Count</th></tr></thead><tbody>'
                        + incident_rows + '</tbody></table></div>') if incident_rows else '<p>No correlated incidents were recorded.</p>'
    anomaly_content = "".join(f'<li><strong>{item.score:.1f}/100 sample rarity</strong> · {escape(item.key)} · {escape(item.reason)}. Not attack probability.</li>'
                              for item in sorted(data.anomalies, key=lambda item: -item.score)[:3])
    formats = ', '.join(sorted(data.format_counts or {})) or 'Unspecified'
    coverage_rows = ''.join(
        f'<div class="{"fingerprint-row" if label == "Source SHA-256" else ""}"><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'
        for label, value in (
            ('Recognized records', f'{data.recognized_records:,} / {data.records:,}'),
            ('Retained excerpts', f'{len(data.raw_lines):,} / {data.records:,}'),
            ('Formats', formats),
            ('Source handling', 'Read-only · local analysis'),
            ('Source SHA-256', data.source_sha256 or 'Unavailable for this analysis'),
        )
    )
    limits = []
    for count, label in ((data.invalid_records, 'invalid records'), (data.truncated_lines, 'oversized lines truncated'),
                         (data.dropped_findings, 'findings omitted'), (data.dropped_auth_events, 'authentication events evicted')):
        if count:
            limits.append(f'{count:,} {label}')
    limits_note = '<p class="coverage-warning">Collection limits: ' + escape('; '.join(limits)) + '.</p>' if limits else ''
    print_evidence = ''.join(
        f'<div class="summary-print-excerpt"><strong><a href="{escape(appendix_href)}#finding-{members[0][0]:03d}">F-{members[0][0]:03d}</a></strong><code class="evidence">{escape(members[0][1].evidence[:100])}{" … [excerpt; see complete report]" if len(members[0][1].evidence) > 100 else ""}</code></div>'
        for key, members in groups
    ) if compact and not diagnostic_compact else ''
    print_evidence = f'<section class="summary-print-evidence"><h2>Representative evidence</h2>{print_evidence}</section>' if print_evidence else ''
    risk = _risk(data)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    context = _report_context(data)
    priority = _ordered_findings(data)
    headline = ('Authentication activity requires review.' if priority and priority[0].category == 'authentication'
                else 'Findings require review.' if priority else 'No rule-backed findings recorded.')
    priority_lead = (f'<p class="priority-lead"><strong>Priority lead:</strong> <a href="#findings">{escape(priority[0].title)}</a> '
                     f'({escape(priority[0].severity)}). Validate the retained evidence before taking action.</p>') if priority else '' 
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>AegisLog Investigation Summary - {escape(Path(data.source).name)}</title><style>{report_stylesheet(summary=True)}</style></head><body><main id="aegislog-report" class="report summary{' has-findings' if data.findings else ''}">{_document_opening(data, generated, summary=True, appendix_href=appendix_href)}
<nav class="toolbar"><a href="#findings">Top findings</a><a href="#incidents">Incidents</a><a href="{escape(appendix_href)}?print=1">Print complete report / Save PDF</a><span class="spacer"></span><button type="button" onclick="window.print()">Print summary / Save PDF</button></nav><p class="print-help">This print button exports the short summary. Open the appendix to print full evidence separately. For PDF, turn off browser Headers and footers.</p><div class="content">
<section class="section" id="executive"><div class="section-head"><div><div class="section-label">Assessment</div><h2>Executive Summary</h2></div></div><div class="hero"><div><h2>{escape(headline)}</h2><div class="assessment"><p>{escape(_lead_observation(data, risk))}</p></div>{priority_lead}</div><aside class="review-priority"><span class="cell-label">Review priority</span><strong>{escape(_disposition(risk))}</strong><p class="caveat">Findings are investigation leads, not proof of compromise.</p></aside></div></section>
{_record_metrics(data, summary=True)}
{_report_navigation(summary=True, appendix_href=appendix_href)}
<section class="section" id="findings"><div class="section-head"><h2>Findings &amp; next actions</h2></div><p class="section-note">{escape(group_note)}</p><div class="summary-findings{' compact-findings' if compact else ''}">{"".join(rows) or '<p>No rule-backed findings were recorded.</p>'}</div></section>
{print_evidence}<section class="section" id="incidents"><div class="section-head"><h2>Priority incidents</h2></div><p class="section-note">Showing {min(5, len(data.incidents))} of {len(data.incidents)} incident groups. Verify timing and shared cause before treating signals as one incident.</p>{incident_content}</section>
<section class="section" id="activity"><div class="section-head"><h2>Supporting activity</h2></div>{_supporting_activity(data)}</section>
<aside class="summary-notes" id="interpretation" aria-label="Report context and limitations"><h2>Interpretation notes</h2>{context}<p class="context-notice"><strong>SUMMARY ONLY</strong> - Complete retained evidence is in the separate full report. Read collection limits below before drawing conclusions.</p></aside>
<section class="section" id="scope"><div class="section-head"><h2>Coverage</h2></div><div class="scope"><dl class="coverage-grid">{coverage_rows}</dl>{limits_note}{'<p>' + escape(data.collection_scope) + '</p>' if data.collection_scope else ''}{'<p>Top rarity signals:</p><ul>' + anomaly_content + '</ul>' if anomaly_content else ''}<p>No matching rules does not establish a clean system. Rarity describes this sample, not attack probability.</p><p class="identity-note">Report ID identifies the analysis output; it is not a source fingerprint. SHA-256 identifies bytes read during collection, including truncated tails; it does not certify an unchanged or complete live source. Preserve the original logs.</p><a href="{escape(appendix_href)}">Open the complete investigation record</a></div></section>
{report_signature(_case_id(data), __version__)}</div></main>{REPORT_EVIDENCE_SCRIPT}</body></html>'''


def write_html_report(data: DashboardData, output_dir: Path | None = None, *,
                      filename: str | None = None, appendix_extra: str = "") -> Path:
    destination = output_dir or default_report_dir()
    destination.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(Path(data.source).stem)
    target = destination / (filename or f"{stem}-aegislog-report.html")
    appendix = target.with_name(target.stem + "-appendix.html")
    from .output_safety import ensure_distinct_output
    ensure_distinct_output(data.source, target, appendix)
    full = build_html_report(data, summary_href=target.name)
    if appendix_extra:
        full = full.replace('<div class="footer">', appendix_extra + '<div class="footer">')
    appendix.write_text(full, encoding="utf-8")
    target.write_text(build_summary_report(data, appendix.name), encoding="utf-8")
    return target
