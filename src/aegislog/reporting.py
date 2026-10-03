from __future__ import annotations

from .report_paths import default_report_dir

import hashlib
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from . import __version__
from .dashboard import DashboardData

_SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

_REPORT_STYLE = """
:root{--ink:#141c30;--ink-soft:#283244;--muted:#596375;--paper:#fff;--line:#d3def0;--line-soft:#d3def0;--accent:#287bff;--mono:#fff}
*{box-sizing:border-box}html{color-scheme:light;scroll-behavior:smooth}
body{margin:0;background:#fff;color:var(--ink);font:16px/1.65 "Segoe UI",Arial,sans-serif}
.report{width:min(1060px,calc(100% - 48px));margin:32px auto;background:#fff}
.masthead{padding:32px 32px 38px;background:#fff}.brand{display:flex;align-items:center;gap:10px}.brand-mark{width:28px;height:32px}.brand-mark svg{width:28px;height:32px}.brand-name{font-size:28px;font-weight:800;letter-spacing:-.04em}.brand-name span{color:inherit}.brand-sub{font-size:10px;letter-spacing:.2em;font-weight:800;margin-top:5px;color:var(--muted)}.brandline{margin-bottom:42px}.classification,.eyebrow,.posture,.section-label{display:none}
h1{font-size:38px;line-height:1.2;letter-spacing:-.02em;margin:0 0 12px}h2{font-size:23px;line-height:1.3;margin:0}h3{font-size:17px;margin:0 0 12px}.subtitle{margin:0;color:var(--muted)}.cover-meta{font-size:13px;color:var(--muted);margin-top:18px}
.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:0 0 20px;padding:12px;border:1px solid var(--line);border-radius:12px}.toolbar a{color:#245ea8;text-decoration:none;font-size:13px}.toolbar a:hover{text-decoration:underline}.spacer{flex:1}.local-note{font-size:10px;color:var(--muted)}button{background:#287bff;border:0;border-radius:6px;padding:9px 14px;color:white;font:inherit;font-size:13px;cursor:pointer}.print-help{font-size:12px;color:var(--muted);margin-bottom:22px}
.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-bottom:24px}.metric{border:1px solid var(--line);border-radius:16px;padding:22px;min-height:120px}.metric span{display:block;font-size:13px}.metric strong{display:block;margin-top:14px;font-size:30px;line-height:1.2}.metric.danger strong{color:#b91c1c}.metric.warning strong{color:#855400}.metric.good strong{color:#166348}
.section{border:1px solid var(--line);border-radius:16px;padding:26px;margin:0 0 20px}.section-head{margin-bottom:20px}.section-note{font-size:12px;color:var(--muted);margin-top:8px}.case-strip{display:block}.case-strip>div{display:grid;grid-template-columns:30% minmax(0,1fr);gap:12px;padding:13px 10px;border-bottom:1px solid var(--line)}.case-strip>div:last-child{border:0}.case-strip small{font-size:13px;font-weight:600}.case-strip strong{font-size:15px;font-weight:400;overflow-wrap:anywhere}
.executive-grid{display:block}.assessment>p:first-of-type{border-left:4px solid var(--accent);border-radius:10px;padding:14px 18px;margin:0}.assessment h3{display:none}.assessment .caveat{margin:16px 0}.priority-box{margin-top:24px}.triage-item{padding:14px 0;border-top:1px solid var(--line);display:grid;grid-template-columns:80px minmax(0,1fr);gap:12px}.triage-item strong{display:block;font-size:14px}.triage-item a{display:block;margin-top:5px;font-size:12px;color:#245ea8}.triage-item p{margin:5px 0 0;font-size:13px}.decision{border:1px solid var(--line);border-radius:12px;padding:16px;margin:18px 0}.decision-head{display:flex;justify-content:space-between;gap:12px}.decision-kicker{font-size:12px;font-weight:600}.lead{font-weight:700;margin:8px 0}.action,.meta{font-size:13px}.meta{margin-top:8px;color:var(--muted)}.caveat{font-size:12px;color:var(--muted)}
.pill{display:inline-block;font-size:10px;font-weight:700;border:1px solid var(--line);border-radius:6px;padding:3px 7px;white-space:nowrap}.pill.danger{color:#b91c1c}.pill.warning{color:#855400}.pill.good{color:#166348}.pill.neutral{color:#334155}
.finding-group{margin-bottom:22px;padding-bottom:18px;border-bottom:1px solid var(--line)}.finding-group:last-child{margin:0;padding:0;border:0}.group-intro{margin-bottom:10px}.group-evidence{display:grid;grid-template-columns:50px minmax(0,1fr);gap:10px;padding:10px 0;border-top:1px solid var(--line)}.group-evidence .evidence{font-size:13px}.group-intro .action-text{margin:6px 0 12px}.report-button{font-weight:700}.summary-brand{display:flex;align-items:center;gap:12px}.summary-logo{width:50px;height:54px}.summary-wordmark{font-size:30px;font-weight:800;color:#14233d}.summary-wordmark span{color:#287bff}.summary-tagline{font-size:9px;letter-spacing:.15em;color:#47658a}.masthead{border-bottom:3px solid #287bff;margin-bottom:20px}.section-head h2{border-left:4px solid #287bff;padding-left:12px}.record-list{border:1px solid var(--line);border-radius:12px;padding:18px}.record{padding:0 0 20px;margin:0 0 20px;border-bottom:1px solid var(--line)}.record:last-child{padding-bottom:0;margin-bottom:0;border:0}.record-head{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:10px}.record-id{font:12px Consolas,monospace}.record-title{font-size:15px;font-weight:700}.record-meta{font-size:12px}.record-body{display:block}.record-cell+.record-cell{margin-top:12px}.cell-label{display:block;font-size:11px;font-weight:600;color:var(--muted);margin-bottom:5px}.evidence{display:block;color:var(--ink);font:12px/1.65 Consolas,"Cascadia Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere}.action-text{margin:0;font-size:13px}.empty{padding:18px;border:1px solid var(--line);border-radius:12px;font:12px Consolas,monospace}.table-wrap{width:100%;overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{padding:13px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13px;overflow-wrap:anywhere}tr:last-child td,tr:last-child th{border:0}thead th{font-size:11px;color:var(--muted)}td a{color:#245ea8}.chart{display:block;width:100%;height:auto;max-width:650px}.chart text{fill:#283244}.chips>.chart,.chips>.caveat{flex-basis:100%;width:100%}.incident-table th:first-child{width:20%}.incident-table th:nth-child(2){width:15%}.incident-table th:nth-child(4){width:9%}.incident-table thead th{white-space:nowrap}.severity-block{margin-top:14px}.severity-row{display:grid;grid-template-columns:90px 35px minmax(0,1fr);gap:12px;align-items:center;margin:9px 0}.severity-row small{font-size:11px}.track{height:6px;background:#e8eef8;border-radius:4px;overflow:hidden}.track i{display:block;height:100%;background:#397dcc}.assessment h3.severity-heading{display:block;margin-top:20px}.triage-item .pill{align-self:start;justify-self:start}.metric.danger strong,.metric.warning strong,.metric.good strong{font-size:22px}.telemetry-grid,.method-grid{display:block}.telemetry-card,.method-card{margin-top:20px}.telemetry-card:first-child,.method-card:first-child{margin-top:0}.method-card p{margin:0;font-size:13px}.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{font-size:12px;border:1px solid var(--line);border-radius:6px;padding:5px 9px}.footer{font-size:11px;text-align:center;margin:28px 0;color:var(--muted)}
@media(max-width:600px){.report{width:calc(100% - 24px);margin:12px auto}.masthead{padding:20px 12px 28px}.section{padding:18px}.case-strip>div{grid-template-columns:1fr;gap:4px}.metric{padding:18px;min-height:110px}.triage-item{grid-template-columns:1fr}.local-note{display:none}}
@media print{
@page{size:A4;margin:12mm}
body{font-size:12px;line-height:1.6;background:#fff}.report{width:100%;margin:0}.masthead{padding:24px 30px 32px;background:#fff!important}.brandline{margin-bottom:34px}.brand-name{font-size:26px}h1{font-size:32px}.subtitle{font-size:14px}.cover-meta{font-size:11px}.toolbar,.print-help{display:none}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px}.metric{padding:18px;min-height:90px}.metric strong{font-size:27px}.metric span{font-size:11px}.section{padding:20px;margin-bottom:16px;box-decoration-break:clone}.section-head{break-after:avoid;margin-bottom:14px}.section-note{break-after:avoid}.incident-table td{padding:7px 6px;line-height:1.4}.incident-table td .pill{font-size:8px}.group-intro{break-inside:avoid;break-after:avoid}.group-evidence{break-inside:avoid;padding:8px 0}.group-evidence .evidence{font-size:11px}.finding-group{break-inside:auto}.group-evidence .record-id{font-size:10px}.masthead{border-bottom:3px solid #287bff}.metric strong{color:#245ea8!important}.metric.danger strong{color:#a62b38!important}h2{font-size:20px}h3{font-size:15px}.section-note{font-size:11px}.case-strip>div{padding:11px 8px}.case-strip small{font-size:11px}.case-strip strong{font-size:13px}.record-list{padding:16px}.record{break-inside:avoid;padding-bottom:16px;margin-bottom:16px}.record-title{font-size:13px}.record-meta{font-size:11px}.evidence{font-size:11px}.action-text,.method-card p{font-size:12px}.record-cell+.record-cell{margin-top:8px}.caveat{font-size:11px}.decision,.metric,.triage-item,.telemetry-card{break-inside:avoid}.table-wrap{overflow:visible}th,td{padding:10px 8px;font-size:11px}thead{display:table-header-group}tr{break-inside:avoid}.chart{break-inside:avoid;max-width:510px}#method{break-inside:avoid}.footer{position:static;font-size:9px;margin:24px 0 0}.content *, .case-strip *{color:#1f2937!important}.content .pill.danger{color:#b91c1c!important}.content .pill.warning{color:#855400!important}.content .pill.good{color:#166348!important}.content a{color:#245ea8!important}
}
"""

_BODY_TEXT_STYLE = """
/* Body copy grows independently of report titles and section headings. */
.content p,.content td,.content th,.content .action-text,.content .section-note,.content .caveat,.content .record-meta,.content .scope,.content .scope li,.content .triage-item a,.content .decision .action,.content .decision .meta{font-size:16px!important;line-height:1.65}
.content code,.content .evidence,.content .group-evidence .evidence{font-size:15px!important;line-height:1.7}
.content .record-title,.content .record-head strong,.content .triage-item strong{font-size:16px!important}
.content .record-id,.content .cell-label,.content .pill,.content .chip{font-size:13px!important}
@media print{
.content p,.content td,.content th,.content .action-text,.content .section-note,.content .caveat,.content .record-meta,.content .scope,.content .scope li,.content .triage-item a,.content .decision .action,.content .decision .meta{font-size:13px!important;line-height:1.55}
.content code,.content .evidence,.content .group-evidence .evidence{font-size:13px!important;line-height:1.6}
.content .record-title,.content .record-head strong,.content .triage-item strong{font-size:14px!important}
.content .record-id,.content .cell-label,.content .pill,.content .chip{font-size:11px!important}
.incident-table thead th{white-space:normal}.group-evidence{grid-template-columns:58px minmax(0,1fr)}
}
"""


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
        return "Critical defensive activity was retained. Prioritize correlated incident evidence and critical findings, then validate them against original telemetry and asset context."
    if risk == "HIGH":
        return "High-severity defensive signals were retained. Immediate analyst review is recommended before normal operational follow-up."
    if risk == "REVIEW":
        return "Medium-severity signals warrant analyst review. Validate source, identity, host, and network context before escalation."
    return "No critical, high, or medium rule-backed findings were retained. This does not prove malicious activity is absent; review coverage and preserve original telemetry as needed."


def _metric(label: str, value: str, modifier: str = "") -> str:
    suffix = f" {modifier}" if modifier else ""
    return f'<article class="metric{suffix}"><span>{escape(label)}</span><strong>{escape(value)}</strong></article>'


def _severity_overview(data: DashboardData) -> str:
    total = max(sum(data.severities.values()), 1)
    rows = []
    for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        count = data.severities.get(severity, 0)
        percent = min(100.0, (count / total) * 100.0)
        rows.append(
            f'<div class="severity-row {_risk_class(severity)}"><small>{severity}</small><strong>{count}</strong><svg width="100%" height="8" role="img" aria-label="{severity}: {count}"><rect width="100%" height="8" fill="#cbd5e1"/><rect width="{percent:.1f}%" height="8" fill="#397dcc"/></svg></div>'
        )
    return "".join(rows)


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
        return f'<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill {_risk_class(top_incident.severity)}">{escape(top_incident.severity)}</span></div><div class="lead">{escape(iid)} · {escape(top_incident.title)}</div><div class="action">Review the correlated evidence chain and validate the affected source, identity, host, and network context before escalation.</div><div class="meta">{top_incident.count} correlated signal(s) · {escape(top_incident.category)}</div></div>'
    if top_finding:
        return f'<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill {_risk_class(top_finding.severity)}">{escape(top_finding.severity)}</span></div><div class="lead">{escape(top_finding.title)}</div><div class="action">Review the retained excerpt and its recommended action before escalation.</div><div class="meta">Rule-backed finding · {escape(top_finding.category)}</div></div>'
    return '<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill good">CLEAR</span></div><div class="lead">No elevated rule-backed finding requires immediate action</div><div class="action">Review coverage and original telemetry before closing the investigation.</div></div>'


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
            f'<td><strong>{escape(item.title)}</strong></td>'
            f'<td>{item.count}</td><td>{links}{extra}</td></tr>'
        )
    if not rows:
        return '<div class="empty">No correlated incidents were recorded.</div>'
    return ('<p class="caveat">Grouping basis: detector category/title and extracted service or source context '
            'where available; category-level fallback when context is unresolved. Grouping has no time-window constraint '
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
    maximum = max(value for _, value in items) or 1
    rows = []
    for index, (name, value) in enumerate(items):
        y = index * 26 + 16
        short = str(name) if len(str(name)) < 39 else str(name)[:35] + "..."
        rows.append(f'<text x="0" y="{y}" font-size="11">{escape(short)}</text><rect x="260" y="{y-10}" width="{180*value/maximum:.1f}" height="12" fill="#397dcc"/><text x="452" y="{y}" font-size="11">{value:,}</text>')
    return f'<svg class="chart" width="510" height="{len(items)*26+8}" viewBox="0 0 510 {len(items)*26+8}" role="img" aria-label="{escape(label)}"><title>{escape(label)}; largest bar = {maximum}; top {len(items)} of {len(values)} classes</title>{"".join(rows)}</svg><p class="caveat">Top {len(items)} of {len(values)} classes; retained total {sum(values.values()):,}. Largest bar = {maximum:,}.</p>'


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
            f'<div class="group-evidence" id="finding-{index:03d}"><span class="record-id">F-{index:03d}</span>'
            f'<code class="evidence">{escape(item.evidence)}</code></div>'
            for index, item in members
        )
        records.append(
            f'<article class="finding-group"><div class="group-intro"><div class="record-head">'
            f'<span class="pill {_risk_class(severity)}">{escape(severity)}</span><strong>{escape(title)}</strong>'
            f'<span class="record-meta">{len(members)} finding(s) · {escape(category)}</span></div>'
            f'<p class="action-text"><strong>Recommended action:</strong> {action}</p></div>{evidence}</article>'
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


def build_html_report(data: DashboardData, summary_href: str | None = None) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    source_name = Path(data.source).name
    risk = _risk(data)
    case_id = _case_id(data)
    summary_link = (f'<a class="report-button" href="{escape(summary_href)}">Back / Print Summary</a>'
                    if summary_href else '<a href="#executive">Back to overview</a>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>AegisLog Investigation Report - {escape(source_name)}</title><style>{_REPORT_STYLE}{_BODY_TEXT_STYLE}</style></head><body><main class="report">
<header class="masthead" id="cover"><div class="brandline">{_summary_brand()}</div><h1>Security Investigation Report</h1><p class="subtitle">{escape(source_name)} · Full evidence · Investigation record</p><div class="cover-meta">Case ID: {escape(case_id)}<br>Generated: {generated}<br>LOCAL / READ-ONLY / DETERMINISTIC</div><div class="posture {_risk_class(risk)}"><small>Current posture</small><strong>{escape(risk)}</strong></div></header>

<nav class="toolbar">{summary_link}<a href="#executive">Overview</a><a href="#incidents">Incidents</a><a href="#findings">Findings</a><a href="#telemetry">Telemetry</a><a href="#anomalies">Anomalies</a><a href="#method">Method</a><span class="spacer"></span><span class="local-note">DETERMINISTIC ANALYSIS</span><button type="button" onclick="window.print()">Print Full Evidence / Save PDF</button></nav>
<p class="print-help">PDF export: use A4 and turn off browser Headers and footers in the print dialog to remove the local file URL. Background graphics are optional; charts and evidence remain readable.</p><div class="content"><section class="metrics">{_metric("Events", f"{data.lines:,}")}{_metric("Findings", str(len(data.findings)))}{_metric("Incidents", str(len(data.incidents)))}{_metric("Disposition", _disposition(risk), _risk_class(risk))}</section>
<section class="section" id="source"><div class="section-head"><h2>Investigation Information</h2></div><div class="case-strip"><div><small>Source</small><strong>{escape(source_name)}</strong></div><div><small>Case ID</small><strong>{escape(case_id)}</strong></div><div><small>Status</small><strong>Analysis complete</strong></div><div><small>Generated</small><strong>{generated}</strong></div><div><small>Processing</small><strong>LOCAL / READ-ONLY / DETERMINISTIC</strong></div></div></section>
<section class="section" id="executive"><div class="section-head"><div><div class="section-label">Executive summary</div><h2>Analysis Summary</h2></div><div class="section-note">Start here. Supporting evidence follows below.</div></div><div class="executive-grid"><div class="assessment"><h3>Assessment</h3><p>{escape(_assessment(data, risk))}</p>{_primary_decision(data)}<p class="caveat">Analyzed <strong>{data.lines:,}</strong> event line(s), retained <strong>{len(data.findings)}</strong> finding(s), <strong>{len(data.incidents)}</strong> incident(s), and <strong>{len(data.anomalies)}</strong> anomaly signal(s). Findings are investigative evidence, not proof of compromise.</p><h3 class="severity-heading">Severity distribution</h3><div class="severity-block">{_severity_overview(data)}</div></div><div class="priority-box"><h3>Recommended triage</h3>{_triage_actions(data)}</div></div></section>
<section class="section" id="incidents"><div class="section-head"><div><div class="section-label">Correlation</div><h2>Incident Queue</h2></div><div class="section-note">Grouped signals; validate shared cause and timing.</div></div><div class="record-list">{_incident_records(data)}</div></section>
<section class="section" id="findings"><div class="section-head"><div><div class="section-label">Detection</div><h2>Findings</h2></div><div class="section-note">{len(data.findings)} retained findings in {len(_finding_groups(data))} presentation groups. Each excerpt keeps its F-reference. Grouping for readability does not establish a common cause.</div></div><div class="record-list">{_finding_records(data)}</div></section>
<section class="section" id="telemetry"><div class="section-head"><div><div class="section-label">Telemetry</div><h2>Observed Distribution</h2></div><div class="section-note">A compact view of the parsed source.</div></div><div class="telemetry-grid"><div class="telemetry-card"><h3>Categories</h3><div class="chips">{_telemetry_chips(data.categories)}</div></div><div class="telemetry-card"><h3>Log levels</h3><div class="chips">{_bar_chart(data.levels, "Log levels")}</div></div><div class="telemetry-card"><h3>Services</h3><div class="chips">{_bar_chart(data.services, "Service activity")}{_telemetry_chips(data.services)}</div></div></section>
<section class="section" id="anomalies"><div class="section-head"><div><div class="section-label">Behavior</div><h2>Anomaly Signals</h2></div><div class="section-note">Rarity scores (0-100), not attack probability.</div></div><p class="caveat">Scores describe rare concerning event classes within this retained sample. A score of 100 does not mean 100% attack probability, severity, or confidence. No trained machine-learning model is used.</p><div class="table-wrap"><table><thead><tr><th>Rarity score / 100</th><th>Event class</th><th>Reason</th></tr></thead><tbody>{_anomaly_rows(data)}</tbody></table></div></section>
<section class="section" id="method"><div class="section-head"><div><div class="section-label">Method and scope</div><h2>Analysis Profile</h2></div><div class="section-note">How the report was produced and how to interpret it.</div></div><div class="method-grid"><div class="method-card"><h3>Processing model</h3><p>AegisLog v{escape(__version__)} performed local deterministic detection, incident correlation, and anomaly scoring. The source was handled read-only.</p></div><div class="method-card"><h3>Evidence limitations</h3><p>{escape(data.retention_note)} This report contains retained derived evidence rather than a complete copy of the raw log. Missing detections do not prove malicious activity is absent. Preserve original telemetry when incident-response, retention, or chain-of-custody procedures require it.</p></div></div><div class="table-wrap" style="margin-top:14px"><table><tr><th>Source path</th><td>{escape(data.source)}</td></tr><tr><th>Source file</th><td>{escape(source_name)}</td></tr><tr><th>Event lines</th><td>{data.lines:,}</td></tr><tr><th>AegisLog version</th><td>{escape(__version__)}</td></tr><tr><th>Generated</th><td>{generated}</td></tr><tr><th>Analysis model</th><td>Deterministic local processing</td></tr></table></div></section>
<div class="footer">AEGISLOG v{escape(__version__)} · {escape(case_id)} · Defensive security analysis · Generated locally · Presented and maintained by HR-Presents</div></div></main></body></html>'''


def _finding_groups(data: DashboardData):
    """Presentation groups only: no new incident or shared-cause inference."""
    groups = {}
    for index, item in enumerate(_ordered_findings(data), 1):
        key = (item.severity, item.category, item.title, _recommendation(item))
        groups.setdefault(key, []).append((index, item))
    return list(groups.items())


def _summary_brand() -> str:
    # Shield paths match docs/assets/aegislog-logo.svg, adapted for light paper.
    return '<div class="summary-brand"><svg class="summary-logo" viewBox="0 0 168 176" role="img" aria-label="AegisLog shield and telemetry logo"><title>AegisLog</title><path d="M84 0 154 27v49c0 45-27 76-70 94C41 152 14 121 14 76V27L84 0Z" fill="#eef5ff" stroke="#c5d8f3" stroke-width="3"/><path d="M84 18 137 38v38c0 33-18 57-53 73-35-16-53-40-53-73V38L84 18Z" fill="none" stroke="#287bff" stroke-width="5"/><path d="M48 88h19l9-28 16 56 11-36 8 8h13" fill="none" stroke="#18345b" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="124" cy="88" r="5" fill="#287bff"/></svg><div><div class="summary-wordmark">AEGIS<span>LOG</span></div><div class="summary-tagline">DEFENSIVE LOG INVESTIGATION</div></div></div><div class="brand-sub">PRESENTED BY HR-PRESENTS</div>'


def _summary_service_chart(values: dict[str, int]) -> str:
    items = sorted(values.items(), key=lambda pair: (-pair[1], str(pair[0])))[:6]
    if not items:
        return '<p class="empty">No retained observations.</p>'
    maximum = max(value for _, value in items) or 1
    rows = []
    for index, (name, value) in enumerate(items):
        y = index * 28 + 18
        short = str(name) if len(str(name)) <= 18 else str(name)[:15] + '...'
        rows.append(f'<text x="0" y="{y}" font-size="14">{escape(short)}</text><rect x="143" y="{y-11}" width="{104*value/maximum:.1f}" height="13" rx="2" fill="#287bff"/><text x="257" y="{y}" font-size="14">{value:,}</text>')
    return f'<svg class="summary-service-chart" viewBox="0 0 300 {len(items)*28+4}" role="img" aria-label="Service activity"><title>Top {len(items)} services; retained total {sum(values.values()):,}</title>{"".join(rows)}</svg><p class="caveat">Top {len(items)} of {len(values)} services · {sum(values.values()):,} events. Full distribution in appendix.</p>'


def build_summary_report(data: DashboardData, appendix_href: str) -> str:
    groups = _finding_groups(data)
    rows = []
    seen_actions = {}
    for group_number, ((severity, category, title, recommendation), members) in enumerate(groups[:6], 1):
        index, example = members[0]
        excerpt = example.evidence[:160]
        if len(example.evidence) > 160:
            excerpt += "..."
        if recommendation in seen_actions:
            action = f'<a href="#action-{seen_actions[recommendation]}">Same next action as group {seen_actions[recommendation]}</a>'
        else:
            seen_actions[recommendation] = group_number
            action = f'<span id="action-{group_number}">{escape(recommendation)}</span>'
        rows.append(
            f'<article class="summary-finding"><div class="record-head"><span class="pill {_risk_class(severity)}">{escape(severity)}</span>'
            f'<strong>{escape(title)}</strong><span class="record-meta">{len(members)} finding(s) · {escape(category)}</span></div>'
            f'<code class="evidence">{escape(excerpt)}</code><p class="action-text"><strong>Next action:</strong> {action}</p>'
            f'<a class="evidence-link" href="{escape(appendix_href)}#finding-{index:03d}">Full evidence in appendix → F-{index:03d}</a></article>'
        )
    group_note = (f'{len(data.findings)} retained findings in {len(groups)} presentation groups. '
                  f'Showing {min(6, len(groups))} highest-priority groups; every finding is in the appendix. '
                  'Matching labels and recommendations are grouped for readability, not proof of a common cause.')
    incident_rows = "".join(
        f'<tr><td><a href="{escape(appendix_href)}#incident-{escape(item.id)}">INC-{escape(item.id.upper()[:8])}</a></td>'
        f'<td><span class="pill {_risk_class(item.severity)}">{escape(item.severity)}</span></td>'
        f'<td>{escape(item.title)}</td><td>{item.count}</td></tr>'
        for item in _ordered_incidents(data)[:5]
    )
    incident_content = ('<table><thead><tr><th>Incident</th><th>Severity</th><th>Signal</th><th>Count</th></tr></thead><tbody>'
                        + incident_rows + '</tbody></table>') if incident_rows else '<p>No correlated incidents were recorded.</p>'
    anomaly_content = "".join(f'<li><strong>{item.score:.1f}/100</strong> · {escape(item.key)}</li>'
                              for item in sorted(data.anomalies, key=lambda item: -item.score)[:3])
    risk = _risk(data)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>AegisLog Investigation Summary - {escape(Path(data.source).name)}</title><style>{_REPORT_STYLE}
.summary .masthead{{padding:22px 26px 24px}}.summary .brandline{{margin-bottom:22px}}.summary .cover-meta{{margin-top:12px}}.summary .section{{padding:22px}}.summary-finding{{padding:14px 0;border-bottom:1px solid var(--line)}}.summary-finding:last-child{{border:0}}.summary-finding .evidence{{margin:6px 0 9px}}.evidence-link{{font-size:12px;color:#245ea8}}.summary .section-note{{margin-bottom:14px}}.summary-chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.summary-chart-grid h3{{font-size:15px}}.summary .metric{{min-height:100px;padding:18px}}.summary .assessment h3{{display:block}}.summary .assessment p{{border:0;padding:0}}.summary .chart{{max-width:510px}}.summary .scope{{font-size:12px}}.summary ul{{margin:8px 0;padding-left:18px}}
.summary-brand{{display:flex;align-items:center;gap:12px}}.summary-logo{{width:54px;height:58px;flex:none}}.summary-wordmark{{font-size:32px;font-weight:800;letter-spacing:-.03em;color:#14233d}}.summary-wordmark span{{color:#287bff}}.summary-tagline{{font-size:9px;font-weight:700;letter-spacing:.15em;color:#47658a}}.summary .brand-sub{{margin-top:10px;color:#47658a}}.summary .masthead{{border-bottom:3px solid #287bff;margin-bottom:20px}}.summary h1{{font-size:34px;color:#14233d}}.summary .metric{{background:#f8fbff;border-color:#c5d8f3}}.summary .metric strong{{color:#245ea8}}.summary .metric.danger{{background:#fff6f6;border-color:#f2cdcf}}.summary .metric.danger strong{{color:#a62b38}}.summary .metric.warning strong{{color:#855400}}.summary .metric.good strong{{color:#166348}}.summary .section-head h2{{border-left:4px solid #287bff;padding-left:12px}}.summary .summary-service-chart{{display:block;width:100%;height:auto}}.summary .summary-service-chart text{{fill:#18345b;font-family:"Segoe UI",Arial,sans-serif}}.summary-finding .evidence{{border:1px solid #d3def0;border-radius:6px;background:#f8fbff;padding:8px 10px}}.summary .pill.danger{{background:#fff1f2;border-color:#eab9c0}}.summary .pill.warning{{background:#fff7e6;border-color:#e8d2a3}}
@media(max-width:600px){{.summary-chart-grid{{grid-template-columns:1fr}}}}
@media print{{.summary .masthead{{padding:14px 18px 18px}}.summary .brandline{{margin-bottom:18px}}.summary h1{{font-size:28px}}.summary .metric{{min-height:74px;padding:14px}}.summary .section{{padding:16px;margin-bottom:14px}}.summary-finding{{break-inside:avoid;padding:6px 0}}.summary-finding .evidence{{padding:4px 8px;margin:4px 0 6px}}.summary .section-note,.summary .scope{{font-size:10px}}.summary #incidents{{break-inside:avoid}}.summary.has-findings #findings{{break-before:page}}.summary .summary-chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.summary-chart-grid{{break-inside:avoid}}.summary .severity-row{{grid-template-columns:65px 22px 1fr;gap:6px}}.summary .chart text{{font-size:12px}}.summary .masthead{{border-bottom:3px solid #287bff;margin-bottom:16px}}.summary .metric,.summary .pill,.summary-finding .evidence{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}.summary .metric strong{{color:#245ea8!important}}.summary .metric.danger strong{{color:#a62b38!important}}.summary .metric.warning strong{{color:#855400!important}}.summary .metric.good strong{{color:#166348!important}}.summary-logo{{width:48px;height:52px}}.summary .summary-wordmark{{font-size:30px}}}}
{_BODY_TEXT_STYLE}</style></head><body><main class="report summary{' has-findings' if data.findings else ''}"><header class="masthead"><div class="brandline">{_summary_brand()}</div><h1>Investigation Summary</h1><p class="subtitle">{escape(Path(data.source).name)}</p><div class="cover-meta">Case {_case_id(data)} · {generated}<br>LOCAL / READ-ONLY / DETERMINISTIC</div></header>
<nav class="toolbar"><a href="#findings">Top findings</a><a href="#incidents">Incidents</a><a href="{escape(appendix_href)}">Full Evidence / Print</a><span class="spacer"></span><button type="button" onclick="window.print()">Print summary / Save PDF</button></nav><p class="print-help">This print button exports the short summary. Open the appendix to print full evidence separately. For PDF, turn off browser Headers and footers.</p><div class="content"><section class="metrics">{_metric("Events", f"{data.lines:,}")}{_metric("Findings", str(len(data.findings)))}{_metric("Incidents", str(len(data.incidents)))}{_metric("Disposition", _disposition(risk), _risk_class(risk))}</section>
<section class="section" id="executive"><div class="section-head"><h2>What needs attention</h2></div><div class="assessment"><p>{escape(_assessment(data, risk))}</p></div><p class="caveat">Findings are investigation leads, not proof of compromise.</p><div class="summary-chart-grid"><div><h3>Severity distribution</h3>{_severity_overview(data)}</div><div><h3>Service activity</h3>{_summary_service_chart(data.services)}</div></div></section>
<section class="section" id="findings"><div class="section-head"><h2>Top findings &amp; next actions</h2></div><p class="section-note">{escape(group_note)}</p>{"".join(rows) or '<p>No rule-backed findings were recorded.</p>'}</section>
<section class="section" id="incidents"><div class="section-head"><h2>Priority incidents</h2></div><p class="section-note">Showing {min(5, len(data.incidents))} of {len(data.incidents)} retained incident(s). Single signals are leads; validate time proximity and shared cause. All groups are in the appendix.</p>{incident_content}</section>
<section class="section" id="scope"><div class="section-head"><h2>Scope &amp; evidence</h2></div><div class="scope"><p>{escape(data.retention_note)}</p>{'<p>Top rarity signals:</p><ul>' + anomaly_content + '</ul>' if anomaly_content else ''}<p>Rarity scores describe this sample, not attack probability. Analysis is deterministic and local. Original telemetry remains the authority.</p><a href="{escape(appendix_href)}">Open full evidence appendix: findings, incidents, anomalies, source details and method</a></div></section>
<div class="footer">AEGISLOG v{escape(__version__)} · {_case_id(data)} · Presented and maintained by HR-Presents</div></div></main></body></html>'''


def write_html_report(data: DashboardData, output_dir: Path | None = None, *,
                      filename: str | None = None, appendix_extra: str = "") -> Path:
    destination = output_dir or default_report_dir()
    destination.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(Path(data.source).stem)
    target = destination / (filename or f"{stem}-aegislog-report.html")
    appendix = target.with_name(target.stem + "-appendix.html")
    if Path(data.source).resolve() in {target.resolve(), appendix.resolve()}:
        raise ValueError("Report cannot overwrite source")
    full = build_html_report(data, summary_href=target.name)
    if appendix_extra:
        full = full.replace('<div class="footer">', appendix_extra + '<div class="footer">')
    appendix.write_text(full, encoding="utf-8")
    target.write_text(build_summary_report(data, appendix.name), encoding="utf-8")
    return target
