from __future__ import annotations

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
.executive-grid{display:block}.assessment>p:first-of-type{border-left:4px solid var(--accent);border-radius:10px;padding:14px 18px;margin:0}.assessment h3{display:none}.assessment .caveat{margin:16px 0}.priority-box{margin-top:24px}.triage-item{padding:14px 0;border-top:1px solid var(--line);display:grid;grid-template-columns:80px minmax(0,1fr);gap:12px}.triage-item strong{font-size:14px}.triage-item p{margin:5px 0 0;font-size:13px}.decision{border:1px solid var(--line);border-radius:12px;padding:16px;margin:18px 0}.decision-head{display:flex;justify-content:space-between;gap:12px}.decision-kicker{font-size:12px;font-weight:600}.lead{font-weight:700;margin:8px 0}.action,.meta{font-size:13px}.meta{margin-top:8px;color:var(--muted)}.caveat{font-size:12px;color:var(--muted)}
.pill{display:inline-block;font-size:10px;font-weight:700;border:1px solid var(--line);border-radius:6px;padding:3px 7px;white-space:nowrap}.pill.danger{color:#b91c1c}.pill.warning{color:#855400}.pill.good{color:#166348}.pill.neutral{color:#334155}
.record-list{border:1px solid var(--line);border-radius:12px;padding:18px}.record{padding:0 0 20px;margin:0 0 20px;border-bottom:1px solid var(--line)}.record:last-child{padding-bottom:0;margin-bottom:0;border:0}.record-head{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:10px}.record-id{font:12px Consolas,monospace}.record-title{font-size:15px;font-weight:700}.record-meta{font-size:12px}.record-body{display:block}.record-cell+.record-cell{margin-top:12px}.cell-label{display:block;font-size:11px;font-weight:600;color:var(--muted);margin-bottom:5px}.evidence{display:block;color:var(--ink);font:12px/1.65 Consolas,"Cascadia Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere}.action-text{margin:0;font-size:13px}.empty{padding:18px;border:1px solid var(--line);border-radius:12px;font:12px Consolas,monospace}.table-wrap{width:100%;overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{padding:13px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13px;overflow-wrap:anywhere}tr:last-child td,tr:last-child th{border:0}thead th{font-size:11px;color:var(--muted)}td a{color:#245ea8}.chart{display:block;width:100%;height:auto;max-width:650px}.chart text{fill:#283244}.chips>.chart,.chips>.caveat{flex-basis:100%;width:100%}.incident-table th:first-child{width:17%}.incident-table th:nth-child(2){width:13%}.incident-table th:nth-child(4){width:9%}.incident-table thead th{white-space:nowrap}.severity-block{margin-top:14px}.severity-row{display:grid;grid-template-columns:90px 35px minmax(0,1fr);gap:12px;align-items:center;margin:9px 0}.severity-row small{font-size:11px}.track{height:6px;background:#e8eef8;border-radius:4px;overflow:hidden}.track i{display:block;height:100%;background:#397dcc}.assessment h3.severity-heading{display:block;margin-top:20px}.triage-item .pill{align-self:start;justify-self:start}.metric.danger strong,.metric.warning strong,.metric.good strong{font-size:22px}.telemetry-grid,.method-grid{display:block}.telemetry-card,.method-card{margin-top:20px}.telemetry-card:first-child,.method-card:first-child{margin-top:0}.method-card p{margin:0;font-size:13px}.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{font-size:12px;border:1px solid var(--line);border-radius:6px;padding:5px 9px}.footer{font-size:11px;text-align:center;margin:28px 0;color:var(--muted)}
@media(max-width:600px){.report{width:calc(100% - 24px);margin:12px auto}.masthead{padding:20px 12px 28px}.section{padding:18px}.case-strip>div{grid-template-columns:1fr;gap:4px}.metric{padding:18px;min-height:110px}.triage-item{grid-template-columns:1fr}.local-note{display:none}}
@media print{
@page{size:A4;margin:12mm}
body{font-size:12px;line-height:1.6;background:#fff}.report{width:100%;margin:0}.masthead{padding:24px 30px 32px;background:#fff!important}.brandline{margin-bottom:34px}.brand-name{font-size:26px}h1{font-size:32px}.subtitle{font-size:14px}.cover-meta{font-size:11px}.toolbar,.print-help{display:none}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px}.metric{padding:18px;min-height:90px}.metric strong{font-size:27px}.metric span{font-size:11px}.section{padding:20px;margin-bottom:16px;box-decoration-break:clone}.section-head{break-after:avoid;margin-bottom:14px}h2{font-size:20px}h3{font-size:15px}.section-note{font-size:11px}.case-strip>div{padding:11px 8px}.case-strip small{font-size:11px}.case-strip strong{font-size:13px}.record-list{padding:16px}.record{break-inside:avoid;padding-bottom:16px;margin-bottom:16px}.record-title{font-size:13px}.record-meta{font-size:11px}.evidence{font-size:11px}.action-text,.method-card p{font-size:12px}.record-cell+.record-cell{margin-top:8px}.caveat{font-size:11px}.decision,.metric,.triage-item,.telemetry-card{break-inside:avoid}.table-wrap{overflow:visible}th,td{padding:10px 8px;font-size:11px}thead{display:table-header-group}tr{break-inside:avoid}.chart{break-inside:avoid;max-width:510px}#method{break-inside:avoid}.footer{position:static;font-size:9px;margin:24px 0 0}.content *, .case-strip *{color:#1f2937!important}.content .pill.danger{color:#b91c1c!important}.content .pill.warning{color:#855400!important}.content .pill.good{color:#166348!important}.content a{color:#245ea8!important}
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
        return f'<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill {_risk_class(top_finding.severity)}">{escape(top_finding.severity)}</span></div><div class="lead">{escape(top_finding.title)}</div><div class="action">{escape(top_finding.recommendation)}</div><div class="meta">Rule-backed finding · {escape(top_finding.category)}</div></div>'
    return '<div class="decision"><div class="decision-head"><span class="decision-kicker">What needs attention</span><span class="pill good">CLEAR</span></div><div class="lead">No elevated rule-backed finding requires immediate action</div><div class="action">Review coverage and original telemetry before closing the investigation.</div></div>'


def _triage_actions(data: DashboardData) -> str:
    actions = []
    seen = set()
    for incident in _ordered_incidents(data)[:2]:
        key = f"incident:{incident.id}"
        seen.add(key)
        actions.append(
            f'<div class="triage-item"><span class="pill {_risk_class(incident.severity)}">{escape(incident.severity)}</span><div><strong>INC-{escape(incident.id.upper()[:8])} · {escape(incident.title)}</strong><p>Validate the grouped evidence and surrounding source, identity, host, and network context.</p></div></div>'
        )
    for item in _ordered_findings(data):
        rec = _recommendation(item).strip()
        if not rec or rec in seen:
            continue
        seen.add(rec)
        actions.append(
            f'<div class="triage-item"><span class="pill {_risk_class(item.severity)}">{escape(item.severity)}</span><div><strong>{escape(item.title)}</strong><p>{escape(rec)}</p></div></div>'
        )
        if len(actions) == 4:
            break
    return "".join(actions[:4]) if actions else '<div class="empty">No immediate rule-backed remediation items were generated.</div>'


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
        basis = "Single signal; validate context" if item.count == 1 else "Grouped signals; validate shared cause"
        rows.append(
            f'<tr><td><strong>INC-{escape(item.id.upper()[:8])}</strong></td>'
            f'<td><span class="pill {_risk_class(item.severity)}">{escape(item.severity)}</span></td>'
            f'<td><strong>{escape(item.title)}</strong><br>{escape(item.category)} · {basis}</td>'
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
    for index, item in enumerate(_ordered_findings(data), start=1):
        records.append(
            f'<article class="record" id="finding-{index:03d}"><div class="record-head"><span class="record-id">F-{index:03d}</span><span class="record-title">{escape(item.title)}</span><span class="record-meta"><span class="pill {_risk_class(item.severity)}">{escape(item.severity)}</span> &nbsp; {escape(item.category)}</span></div><div class="record-body"><div class="record-cell"><span class="cell-label">Retained evidence</span><code class="evidence">{escape(item.evidence)}</code></div><div class="record-cell"><span class="cell-label">Recommended action</span><p class="action-text">{escape(_recommendation(item))}</p></div></div></article>'
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


def build_html_report(data: DashboardData) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    source_name = Path(data.source).name
    risk = _risk(data)
    case_id = _case_id(data)
    brand_mark = '''<svg viewBox="0 0 46 52" aria-hidden="true"><path d="M23 2 42 9v14c0 13-7.3 22-19 27C11.3 45 4 36 4 23V9L23 2Z" fill="#eef4fb" stroke="#4C8DFF" stroke-width="2"/><path d="M12 27h7l3-8 4 13 3-6h5" fill="none" stroke="#245ea8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>AegisLog Investigation Report - {escape(source_name)}</title><style>{_REPORT_STYLE}</style></head><body><main class="report">
<header class="masthead" id="cover"><div class="brandline"><div class="brand"><div class="brand-mark">{brand_mark}</div><div><div class="brand-name">AEGIS<span>LOG</span></div><div class="brand-sub">PRESENTED BY HR-PRESENTS</div></div></div><div class="classification">Local-first · read-only<br>Investigation record</div></div><div class="title-grid"><div><div class="eyebrow">Case {escape(case_id)}</div><h1>Security Investigation Report</h1><p class="subtitle">{escape(source_name)} · Log investigation</p><div class="cover-meta">Case ID: {escape(case_id)}<br>Generated: {generated}</div></div><div class="posture {_risk_class(risk)}"><small>Current posture</small><strong>{escape(risk)}</strong></div></div></header>

<nav class="toolbar"><a href="#executive">Summary</a><a href="#incidents">Incidents</a><a href="#findings">Findings</a><a href="#telemetry">Telemetry</a><a href="#anomalies">Anomalies</a><a href="#method">Method</a><span class="spacer"></span><span class="local-note">DETERMINISTIC ANALYSIS</span><button type="button" onclick="window.print()">Print / Save PDF</button></nav>
<p class="print-help">PDF export: use A4 and turn off browser Headers and footers in the print dialog to remove the local file URL. Background graphics are optional; charts and evidence remain readable.</p><div class="content"><section class="metrics">{_metric("Events", f"{data.lines:,}")}{_metric("Findings", str(len(data.findings)))}{_metric("Incidents", str(len(data.incidents)))}{_metric("Disposition", _disposition(risk), _risk_class(risk))}</section>
<section class="section" id="source"><div class="section-head"><h2>Investigation Information</h2></div><div class="case-strip"><div><small>Source</small><strong>{escape(source_name)}</strong></div><div><small>Case ID</small><strong>{escape(case_id)}</strong></div><div><small>Status</small><strong>Analysis complete</strong></div><div><small>Generated</small><strong>{generated}</strong></div><div><small>Processing</small><strong>LOCAL / READ-ONLY / DETERMINISTIC</strong></div></div></section>
<section class="section" id="executive"><div class="section-head"><div><div class="section-label">Executive summary</div><h2>Analysis Summary</h2></div><div class="section-note">Start here. Supporting evidence follows below.</div></div><div class="executive-grid"><div class="assessment"><h3>Assessment</h3><p>{escape(_assessment(data, risk))}</p>{_primary_decision(data)}<p class="caveat">Analyzed <strong>{data.lines:,}</strong> event line(s), retained <strong>{len(data.findings)}</strong> finding(s), <strong>{len(data.incidents)}</strong> incident(s), and <strong>{len(data.anomalies)}</strong> anomaly signal(s). Findings are investigative evidence, not proof of compromise.</p><h3 class="severity-heading">Severity distribution</h3><div class="severity-block">{_severity_overview(data)}</div></div><div class="priority-box"><h3>Recommended triage</h3>{_triage_actions(data)}</div></div></section>
<section class="section" id="incidents"><div class="section-head"><div><div class="section-label">Correlation</div><h2>Incident Queue</h2></div><div class="section-note">Grouped signals; validate shared cause and timing.</div></div><div class="record-list">{_incident_records(data)}</div></section>
<section class="section" id="findings"><div class="section-head"><div><div class="section-label">Detection</div><h2>Findings</h2></div><div class="section-note">Rule-backed detections with retained evidence and next action.</div></div><div class="record-list">{_finding_records(data)}</div></section>
<section class="section" id="telemetry"><div class="section-head"><div><div class="section-label">Telemetry</div><h2>Observed Distribution</h2></div><div class="section-note">A compact view of the parsed source.</div></div><div class="telemetry-grid"><div class="telemetry-card"><h3>Categories</h3><div class="chips">{_telemetry_chips(data.categories)}</div></div><div class="telemetry-card"><h3>Log levels</h3><div class="chips">{_bar_chart(data.levels, "Log levels")}</div></div><div class="telemetry-card"><h3>Services</h3><div class="chips">{_bar_chart(data.services, "Service activity")}{_telemetry_chips(data.services)}</div></div></section>
<section class="section" id="anomalies"><div class="section-head"><div><div class="section-label">Behavior</div><h2>Anomaly Signals</h2></div><div class="section-note">Rarity scores (0-100), not attack probability.</div></div><p class="caveat">Scores describe rare concerning event classes within this retained sample. A score of 100 does not mean 100% attack probability, severity, or confidence. No trained machine-learning model is used.</p><div class="table-wrap"><table><thead><tr><th>Rarity score / 100</th><th>Event class</th><th>Reason</th></tr></thead><tbody>{_anomaly_rows(data)}</tbody></table></div></section>
<section class="section" id="method"><div class="section-head"><div><div class="section-label">Method and scope</div><h2>Analysis Profile</h2></div><div class="section-note">How the report was produced and how to interpret it.</div></div><div class="method-grid"><div class="method-card"><h3>Processing model</h3><p>AegisLog v{escape(__version__)} performed local deterministic detection, incident correlation, and anomaly scoring. The source was handled read-only.</p></div><div class="method-card"><h3>Evidence limitations</h3><p>{escape(data.retention_note)} This report contains retained derived evidence rather than a complete copy of the raw log. Missing detections do not prove malicious activity is absent. Preserve original telemetry when incident-response, retention, or chain-of-custody procedures require it.</p></div></div><div class="table-wrap" style="margin-top:14px"><table><tr><th>Source path</th><td>{escape(data.source)}</td></tr><tr><th>Source file</th><td>{escape(source_name)}</td></tr><tr><th>Event lines</th><td>{data.lines:,}</td></tr><tr><th>AegisLog version</th><td>{escape(__version__)}</td></tr><tr><th>Generated</th><td>{generated}</td></tr><tr><th>Analysis model</th><td>Deterministic local processing</td></tr></table></div></section>
<div class="footer">AEGISLOG v{escape(__version__)} · {escape(case_id)} · Defensive security analysis · Generated locally · Presented and maintained by HR-Presents</div></div></main></body></html>'''


def write_html_report(data: DashboardData, output_dir: Path | None = None) -> Path:
    destination = output_dir or (Path.cwd() / "aegislog-reports")
    destination.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(Path(data.source).stem)
    target = destination / f"{stem}-aegislog-report.html"
    target.write_text(build_html_report(data), encoding="utf-8")
    return target
