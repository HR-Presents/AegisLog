from __future__ import annotations

from .report_paths import default_report_dir
from .report_design import observed_facts, why_it_matters
from .report_reference import document_cover, document_contents
from .report_editorial import activity_timeline
from .report_company import issue_name

import hashlib
import re
from html import escape
from pathlib import Path

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


def _original_rule(item, title):
    """Show detector provenance only when the presentation label differs."""
    if issue_name(item) == title:
        return ''
    return f'<small class="original-rule">Rule: {escape(title)}</small>'


def _method_context(data):
    # The cover already carries the content-grounded synthetic-data notice.
    return re.sub(r'<p class="context-notice"><strong>SYNTHETIC DEMO DATA</strong>.*?</p>', '', _report_context(data))


def _triage_actions(data: DashboardData) -> str:
    actions = []
    seen = set()
    for number, ((severity, _category, title, recommendation), _members) in enumerate(_finding_groups(data), 1):
        if not recommendation or recommendation in seen:
            continue
        seen.add(recommendation)
        actions.append(f'<div class="triage-item"><span class="pill {_risk_class(severity)}">{escape(severity)}</span>'
                       f'<div><strong>{escape(issue_name(_members[0][1]))}</strong>{_original_rule(_members[0][1], title)}<a href="#full-action-{number}">Read recommended action and evidence</a></div></div>')
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
            f'<span class="pill {_risk_class(severity)}">{escape(severity)}</span><strong>{escape(issue_name(members[0][1]))}</strong>{_original_rule(members[0][1], title)}'
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
    from .report_document import build_document
    return build_document(data, summary_href)


def _finding_groups(data: DashboardData):
    """Presentation groups only: no new incident or shared-cause inference."""
    groups = {}
    for index, item in enumerate(_ordered_findings(data), 1):
        context = dict(item.context)
        key = (item.severity, item.category, item.title, _recommendation(item),
               context.get('group_sid') or context.get('group_name'))
        groups.setdefault(key, []).append((index, item))
    # Renderers retain their four-field presentation interface; identity remains
    # part of the internal grouping key so distinct target groups stay separate.
    return [(key[:4], members) for key, members in groups.items()]


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
    from .report_company import assessment
    return assessment(data, _finding_groups(data))[1]


def _supporting_activity(data: DashboardData) -> str:
    timeline = activity_timeline(data.raw_lines, data.timestamp_year_hint)
    if data.records < 20:
        severity = ' · '.join(f'{escape(str(name))}: {count}' for name, count in sorted(data.severities.items())) or 'No rule-backed findings'
        services = ''.join(f'<span><strong>{escape(str(name))}</strong> {count:,}</span>' for name, count in sorted(data.services.items(), key=lambda pair: (-pair[1], str(pair[0])))[:6])
        return (timeline +
                '<div class="summary-service-chart"><h3>Observed source activity</h3><div class="activity-counts">' + services + '</div></div>'
                f'<p class="caveat">Finding severity · {severity}. Service counts describe processed records, not distinct incidents.</p>')
    return (timeline + '<div class="summary-chart-grid"><div><h3>Finding severity</h3>' + _severity_overview(data) +
            '</div><div><h3>Source activity</h3>' + _summary_service_chart(data.services) + '</div></div>')


def build_summary_report(data: DashboardData, appendix_href: str) -> str:
    from .report_company import build_company_summary
    return build_company_summary(data, appendix_href)


def write_html_report(data: DashboardData, output_dir: Path | None = None, *,
                      filename: str | None = None, appendix_extra: str = "") -> Path:
    destination = output_dir or default_report_dir()
    destination.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(Path(data.source).stem)
    target = destination / (filename or f"{stem}-aegislog-report.html")
    appendix = target.with_name(target.stem + "-appendix.html")
    from .output_safety import ensure_distinct_output
    ensure_distinct_output(data.source, target, appendix,
                           target.with_name(target.stem + "-case.json"),
                           destination / "activity-baseline.json", destination / "evidence.json")
    full = build_html_report(data, summary_href=target.name)
    if appendix_extra:
        full = full.replace('<div class="footer">', appendix_extra + '<div class="footer">')
    appendix.write_text(full, encoding="utf-8")
    target.write_text(build_summary_report(data, appendix.name), encoding="utf-8")
    return target
