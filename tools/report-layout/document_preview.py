"""Reviewable document-layout prototype; does not change production reporting."""
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from html import escape as e
from pathlib import Path

from aegislog import __version__
from aegislog.brand_logo import report_logo_uri
from aegislog.dashboard import analyze_dashboard
from aegislog.engine import _parse_timestamp, _auth_event
from aegislog.report_company import brief_review, issue_name
from aegislog.reporting import _case_id, _finding_groups, _recommendation, _ordered_findings
from aegislog.report_design import observed_facts


STYLE = """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#e9f2f4;color:#000;font:16px/1.55 Arial,Helvetica,sans-serif}a{color:#000;text-underline-offset:3px}button{font:inherit;cursor:pointer;color:#000;background:#d5eef2;border:1px solid #83bdc8;padding:8px 16px}p{margin:0 0 12px}h1,h2,h3{margin:0;color:#000}h1{font-size:38px;line-height:1.1;letter-spacing:-1.1px}h2{font-size:28px;line-height:1.2;letter-spacing:-.5px}h3{font-size:19px;line-height:1.3}small{font-size:12px}.reader-tools{max-width:1100px;margin:20px auto;display:flex;align-items:center;gap:22px;padding:0 14px;flex-wrap:wrap;font-size:13px}.reader-tools span{margin-left:auto}.document{max-width:1100px;margin:auto}.sheet{background:#fff;padding:42px 58px 35px;margin-bottom:26px;box-shadow:0 3px 20px #16364512}.masthead{display:grid;grid-template-columns:240px 1fr;gap:42px;align-items:center;border-top:5px solid #90ccd7;padding:20px 0 23px}.logo{width:235px;height:155px}.kicker{font-size:11px;font-weight:bold;letter-spacing:1.9px;text-transform:uppercase;margin-bottom:10px}.masthead .subtitle{margin:14px 0 0;font-size:14px}.metadata{display:grid;grid-template-columns:1.5fr 1fr 1.1fr;gap:24px;border-block:1px solid #c5dfe4;padding:15px 0;font-size:13px}.label{display:block;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}.metadata strong{display:block;font-weight:500;overflow-wrap:anywhere}.sample-notice{border-left:3px solid #74bdcb;background:#eff9fb;font-size:12px;padding:9px 12px;margin:18px 0}.summary{margin:23px 0}.summary h2{font-size:29px;margin:6px 0 12px}.summary p{max-width:88ch}.priority{display:flex;align-items:center;gap:12px;font-size:12px;font-weight:bold;letter-spacing:.6px}.priority i{width:9px;height:9px;border-radius:50%;background:#a63832}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border-block:1px solid #c5dfe4;padding:17px 0;margin:23px 0;gap:20px}.metrics strong{font-size:31px;line-height:1.2;font-weight:600;display:block}.section-heading{display:flex;gap:15px;align-items:baseline;margin:26px 0 12px}.section-heading>span{font-size:12px;color:#000;font-weight:bold}.section-heading h2{font-size:24px}.note{font-size:12px;line-height:1.5;margin:7px 0 14px}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:14px;line-height:1.5}th{font-size:10px;letter-spacing:.7px;text-transform:uppercase;background:#e8f6f8;font-weight:700}th,td{padding:12px 10px;border-bottom:1px solid #cfdee2;text-align:left;vertical-align:top;overflow-wrap:anywhere}th:first-child,td:first-child{padding-left:0}th:first-child{padding-left:10px}.finding-register th:nth-child(1){width:9%}.finding-register th:nth-child(2){width:13%}.finding-register th:nth-child(3){width:33%}.finding-register th:nth-child(4){width:9%}.finding-register th:nth-child(5){width:36%}.sev{font-size:11px;font-weight:700;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}.sev:before{content:'';width:5px;height:5px;border-radius:50%;background:#947216}.sev.high:before,.sev.critical:before{background:#a63832}.sev.info:before,.sev.low:before{background:#36818f}.finding-register a{text-decoration:none;font-weight:600}.finding-register td small{display:block;margin-top:5px}.footer{border-top:1px solid #a9cbd3;padding-top:14px;margin-top:28px;display:flex;justify-content:space-between;gap:16px;font-size:10px;letter-spacing:.8px}.footer strong{letter-spacing:1px}.continuation{display:flex;justify-content:space-between;gap:20px;font-size:11px;border-top:5px solid #90ccd7;border-bottom:1px solid #cfdee2;padding:14px 0;margin-bottom:22px;letter-spacing:.8px}.evidence-record{margin:20px 0 28px;break-inside:avoid}.evidence-heading{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;border-bottom:1px solid #cfdee2;padding-bottom:9px;margin-bottom:13px}.evidence-heading .ref{font-size:12px;font-weight:bold}.evidence-heading h3{flex:1}.evidence-heading small{font-size:11px}.evidence-columns{display:grid;grid-template-columns:1fr 1.25fr;gap:30px;margin-bottom:12px}.evidence-columns p{font-size:14px;margin-bottom:0}.facts{display:grid;grid-template-columns:95px 1fr;gap:3px 12px;font-size:13px;margin:0}.facts dt{font-weight:500}.facts dd{margin:0;overflow-wrap:anywhere}.excerpt{display:grid;grid-template-columns:55px 1fr;gap:14px;margin:7px 0;break-inside:avoid}.excerpt>a{font:11px/1.6 Arial,sans-serif;padding-top:8px}.excerpt pre{font:12px/1.65 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;background:#f3f9fa;border-left:2px solid #a6d2dc;padding:10px 13px;color:#000}.evidence-record .note{margin-bottom:6px}.interpretation{font-size:13px;border-left:2px solid #a6d2dc;padding-left:14px;margin-top:16px}.charts{display:grid;grid-template-columns:1fr 1fr 1.35fr;gap:28px;margin:22px 0}.chart h3{margin-bottom:14px}.distribution{font-size:12px;display:block;margin-bottom:12px}.distribution-label{display:flex;justify-content:space-between;gap:12px;margin-bottom:4px}.distribution span{overflow-wrap:anywhere}.distribution strong{text-align:right}.track{grid-column:1/-1;width:100%;height:4px;display:block}.track i{display:block;height:4px;border-top:4px solid #6db6c6}.timeline{margin:18px 0}.minute-bars{display:flex;gap:10px;align-items:end;height:130px}.minute{flex:1;text-align:center;min-width:0}.minute svg{width:100%;height:95px;display:block}.minute span,.minute strong{font-size:10px}.incident-register th:first-child{width:19%}.incident-register th:nth-child(2){width:12%}.incident-register th:nth-child(3){width:52%}.incident-register th:last-child{width:17%}.scope{display:grid;grid-template-columns:1fr 1fr;gap:30px;margin:18px 0}.scope h3{font-size:16px;margin-bottom:9px}.scope p{font-size:13px}.appendix th{width:25%;background:none;text-transform:none;letter-spacing:0;font-size:12px;padding-left:0}.appendix td{font-size:12px}.end-signature{text-align:center;border-top:2px solid #8bc7d3;padding:23px 0 0;margin-top:25px}.end-signature strong{font-size:19px;letter-spacing:1.5px}.end-signature p{font-size:10px;letter-spacing:1.5px;margin:7px 0 0}.rarity{font-size:12px}.rare-line{display:flex;gap:16px;margin:5px 0}.hash{font-family:Consolas,monospace;font-size:10px}.page-note{font-size:12px;margin-top:18px}
@media screen and (max-width:760px){body{font-size:15px}.sheet{padding:24px;margin-bottom:12px}.masthead{grid-template-columns:1fr;gap:12px}.logo{width:220px;height:146px}.metadata{grid-template-columns:1fr;gap:12px}.metrics{grid-template-columns:1fr 1fr}.finding-register{font-size:12px}.finding-register th,.finding-register td{padding:8px 5px}.finding-register th:last-child,.finding-register td:last-child{display:none}.finding-register th:nth-child(1){width:13%}.finding-register th:nth-child(2){width:18%}.finding-register th:nth-child(3){width:54%}.finding-register th:nth-child(4){width:15%}.evidence-columns,.scope,.charts{grid-template-columns:1fr}.evidence-heading h3{flex-basis:100%}.excerpt{grid-template-columns:1fr;gap:0}.continuation,.footer{flex-wrap:wrap}.reader-tools span{margin-left:0}.incident-register{font-size:12px}.minute-bars{gap:3px}h1{font-size:32px}}
@page{size:A4;margin:14mm 17mm 16mm;@bottom-left{content:'AEGISLOG / INVESTIGATION RECORD';font:8px Arial,sans-serif;color:#000}@bottom-right{content:counter(page) ' / ' counter(pages);font:9px Arial,sans-serif;color:#000}}
@media print{body{background:#fff;font-size:11pt;line-height:1.5}.reader-tools{display:none}.document{max-width:none}.sheet{padding:0;box-shadow:none;margin:0;break-before:page}.sheet:first-child{break-before:auto}.masthead{grid-template-columns:185px 1fr;gap:25px;padding:12px 0 16px}.logo{width:185px;height:123px}h1{font-size:27px}.masthead .subtitle{font-size:11px}.metadata{font-size:10px;padding:10px 0}.sample-notice{font-size:9px;margin:12px 0;padding:6px 10px}.summary{margin:17px 0}.summary h2{font-size:24px}.summary p{font-size:11px}.metrics{margin:17px 0;padding:12px 0}.metrics strong{font-size:25px}.section-heading{margin:19px 0 10px;break-after:avoid}.section-heading h2{font-size:20px}.finding-register{font-size:10px}.finding-register th,.finding-register td{padding:9px 7px}.note,.page-note{font-size:9px}.continuation{padding:10px 0;margin-bottom:15px}.evidence-record{margin:14px 0 21px}.evidence-heading h3{font-size:15px}.evidence-heading{padding-bottom:8px;margin-bottom:10px}.evidence-columns{gap:22px}.evidence-columns p,.facts{font-size:10px}.excerpt pre{font-size:9px;padding:8px 11px}.excerpt>a{font-size:9px}.interpretation{font-size:10px}.charts{gap:20px;margin:18px 0}.chart h3{font-size:14px}.distribution{font-size:10px;margin-bottom:10px}.timeline{margin:12px 0}.minute-bars{height:107px}.minute svg{height:76px}.incident-register{font-size:10px}.incident-register th,.incident-register td{padding:8px}.scope p{font-size:10px}.scope h3{font-size:13px}.appendix th,.appendix td{font-size:9px;padding:7px}.appendix th{padding-left:0}.footer{font-size:8px;margin-top:18px;padding-top:10px}.end-signature{margin-top:18px;padding-top:17px}.end-signature strong{font-size:16px}.rarity{font-size:10px}thead{display:table-header-group}tr{break-inside:avoid}p{orphans:3;widows:3}.sheet,.sample-notice,th,.excerpt pre{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
"""


REFINEMENT_STYLE = """
.decision-notes{padding-left:20px;margin:14px 0;font-size:14px;line-height:1.6}.decision-notes li{margin:5px 0}.decision-notes a{text-decoration:none}.priority-meaning{font-size:12px!important;max-width:none!important}.chronology th:first-child{width:24%}.chronology th:last-child{width:13%}.subheading{margin:20px 0 9px;font-size:17px}.supporting{margin:18px 0;border-block:1px solid #cfdee2;padding:13px 0;font-size:13px}.supporting summary{cursor:pointer;font-weight:bold}.collection-note{font-size:14px;margin-bottom:10px}.end-signature{padding-top:18px;margin-top:18px}
@media print{.summary p{font-size:13px}.decision-notes{font-size:11px;line-height:1.5;margin:10px 0}.decision-notes li{margin:4px 0}.priority-meaning{font-size:10px!important}.finding-register{font-size:11px}.finding-register th,.finding-register td{padding:9px 7px}.evidence-columns p,.facts{font-size:12px;line-height:1.4}.facts{gap:2px 12px}.excerpt pre{font-size:11px;line-height:1.5;padding:7px 10px}.evidence-record{margin:12px 0 18px}.evidence-heading{margin-bottom:8px;padding-bottom:7px}.interpretation{font-size:11px;margin-top:10px}.collection-note{font-size:11px}.supporting{display:none}.chronology,.incident-register{font-size:11px}.chronology td,.incident-register td{padding:8px}.subheading{font-size:15px;margin:17px 0 8px}.appendix th,.appendix td{font-size:10px;padding:7px}.end-signature{padding-top:13px;margin-top:15px}.section-heading{margin:17px 0 10px}.summary{margin:15px 0}.metrics{margin:15px 0;padding:11px 0}}
"""


def severity(value):
    return f'<span class="sev {e(value.lower())}">{e(value)}</span>'


def distributions(values):
    items = sorted(values.items(), key=lambda item: (-item[1], item[0]))[:5]
    peak = max((v for _, v in items), default=1) or 1
    return ''.join(f'<div class="distribution"><div class="distribution-label"><span>{e(str(k))}</span><strong>{v:,}</strong></div><svg class="track" viewBox="0 0 300 4" preserveAspectRatio="none" aria-hidden="true"><rect width="300" height="4" fill="#eaf2f4"/><rect width="{300*v/peak:.2f}" height="4" fill="#6db6c6"/></svg></div>' for k, v in items) or '<p class="note">No observations available.</p>'


def build_document(data):
    groups = _finding_groups(data)
    ref = _case_id(data)
    generated = datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')
    authentication = [f for f in data.findings if f.category == 'authentication']
    if authentication:
        lead = authentication[0]
        match = re.match(r'^(\d+) authentication failures?\b', lead.evidence)
        failures = int(match.group(1)) if match else None
        event = _auth_event(lead.evidence.split('; latest=', 1)[-1], data.timestamp_year_hint)
        headline = f'{failures} failed logins need account review' if failures else 'Authentication activity needs review'
        conclusion = 'The retained detector evidence records ' + (f'{failures} failed authentication attempts' if failures else 'failed authentication activity')
        if event.account:
            conclusion += f' for {event.account}'
        if event.source_ip:
            conclusion += f' from {event.source_ip}'
        conclusion += '. This is a review lead; it does not establish a successful intrusion.'
    elif groups:
        headline = issue_name(groups[0][1][0][1]) + ' requires review'
        conclusion = f'{len(data.findings)} retained detector findings across {len(groups)} review groups. Validate component impact and surrounding telemetry before escalation.'
    else:
        headline = 'No matching detector findings'
        conclusion = 'No matching rules were recorded in the supplied sample. Review coverage before drawing conclusions about the host.'
    observations = []
    for number, ((_, category, _, _), members) in enumerate(groups, 1):
        name = issue_name(members[0][1])
        if category == 'authentication':
            text = 'First review account ownership, successful logons, MFA and the source address.'
        elif name == 'Service response timeout':
            text = f'{len(members)} service timeout record(s); establish availability impact and service dependencies.'
        elif name == 'DCOM application registration timeout':
            text = f'{len(members)} DCOM timeout record(s); validate application startup and user impact.'
        else:
            text = f'{len(members)} finding(s): {name}. Validate the affected component.'
        observations.append(f'<li><a href="#group-{number:03d}">{e(text)}</a></li>')
    observation_html = '<ul class="decision-notes">' + ''.join(observations[:3]) + '</ul>'
    register, evidence = [], []
    for number, ((sev, category, _, _), members) in enumerate(groups, 1):
        index, item = members[0]
        action = brief_review(item, _recommendation(item))
        quick_action = ('Check successful logons, account and source.' if category == 'authentication' else 'Check service logs, dependencies and impact.' if issue_name(item) == 'Service response timeout' else 'Check application startup and user impact.' if issue_name(item) == 'DCOM application registration timeout' else 'Review retained evidence and affected component.')
        register.append(f'<tr><td><a href="#group-{number:03d}">G-{number:03d}</a></td><td>{severity(sev)}</td><td><a href="#group-{number:03d}">{e(issue_name(item))}</a><small>{e(category)}</small></td><td>{len(members)}</td><td>{e(quick_action)}</td></tr>')
        facts = observed_facts(item, data.timestamp_year_hint).replace('observed-facts', 'facts')
        original_rule = f'<p class="note">Detector rule: {e(item.title)}</p>' if issue_name(item) != item.title else ''
        excerpts = ''.join(f'<div class="excerpt" id="finding-{i:03d}"><a href="#group-{number:03d}">F-{i:03d}</a><pre>{e(f.evidence)}</pre></div>' for i, f in members)
        evidence.append(f'<article class="evidence-record" id="group-{number:03d}"><div class="evidence-heading"><span class="ref">G-{number:03d}</span><h3>{e(issue_name(item))}</h3>{severity(sev)}<small>{len(members)} occurrence(s)</small></div>{original_rule}<div class="evidence-columns"><div><span class="label">Observed context</span>{facts}</div><div><span class="label">Recommended review</span><p>{e(action)}</p></div></div><p class="note">Retained detector evidence</p>{excerpts}</article>')
    metrics = ''.join(f'<div><span class="label">{label}</span><strong>{value}</strong></div>' for label, value in [('Records processed', f'{data.records:,}'), ('Finding occurrences', len(data.findings)), ('Review groups', len(groups)), ('Recognized records', f'{data.recognized_records:,}/{data.records:,}')])
    rows = []
    for incident in data.incidents:
        references = [f'F-{i:03d}' for i, f in enumerate(_ordered_findings(data), 1) if f.evidence in incident.evidence]
        refs = ' '.join(f'<a href="#finding-{r[2:]}">{r}</a>' for r in references) or 'No exact retained excerpt match'
        rows.append(f'<tr><td>INC-{e(incident.id.upper()[:8])}</td><td>{severity(incident.severity)}</td><td>{e(incident.title)}<br><small>{e(incident.context)}</small></td><td>{incident.count} signal(s)<br>{refs}</td></tr>')
    sequence = []
    for number, (_, members) in enumerate(groups, 1):
        timestamps = [_parse_timestamp(f.evidence.split('; latest=', 1)[-1], data.timestamp_year_hint) for _, f in members]
        resolved = sorted(t for t in timestamps if t is not None)
        time = resolved[0].strftime('%H:%M:%S') if resolved else 'Unresolved'
        if len(resolved) > 1 and resolved[-1] != resolved[0]:
            time += ' - ' + resolved[-1].strftime('%H:%M:%S')
        sequence.append((resolved[0].isoformat() if resolved else 'z', f'<tr><td>{e(time)}</td><td><a href="#group-{number:03d}">{e(issue_name(members[0][1]))}</a></td><td>G-{number:03d}</td></tr>'))
    chronology = ''.join(row for _, row in sorted(sequence))
    anomaly = ''.join(f'<div class="rare-line"><strong>{a.score:.1f}/100</strong><span>{e(a.key)} - {e(a.reason)}</span></div>' for a in data.anomalies[:5]) or '<p>No rare concerning event classes were recorded.</p>'
    footer = f'<footer class="footer"><strong>MADE BY HR-PRESENTS</strong><span>{e(ref)} / LOCAL / READ-ONLY / DETERMINISTIC</span></footer>'
    def continuation(name):
        return f'<header class="continuation"><strong>AEGISLOG</strong><span>{e(name)} / {e(ref)}</span></header>'
    identity = [('Source SHA-256', data.source_sha256), ('Processed / retained records', f'{data.records:,} / {len(data.raw_lines):,}'), ('Recognized formats', ', '.join(sorted(data.format_counts or {}))), ('Invalid / truncated / omitted findings / auth evictions', f'{data.invalid_records} / {data.truncated_lines} / {data.dropped_findings} / {data.dropped_auth_events}'), ('Analysis engine', f'AegisLog {__version__} / deterministic local processing')]
    appendix = ''.join(f'<tr><th>{e(k)}</th><td class="{ "hash" if k == "Source SHA-256" else ""}">{e(str(v))}</td></tr>' for k, v in identity)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>AegisLog - Document Report Design Preview</title><style>{STYLE}{REFINEMENT_STYLE}</style></head><body><nav class="reader-tools"><a href="#overview">Overview</a><a href="#evidence">Evidence</a><a href="#activity">Activity</a><a href="#method">Method</a><span>Design preview / synthetic evidence</span><button onclick="window.print()">Print / Save PDF</button></nav><main class="document">
<section class="sheet" id="overview"><header class="masthead"><svg class="logo" viewBox="210 180 1100 710" role="img" aria-label="AegisLog logo"><image href="{report_logo_uri()}" width="1519" height="1035"/></svg><div><p class="kicker">Defensive log investigation</p><h1>Security investigation<br>report</h1><p class="subtitle">Evidence, assessment and recommended review</p></div></header><div class="metadata"><div><span class="label">Source</span><strong>{e(data.source_label)}</strong></div><div><span class="label">Report reference</span><strong>{e(ref)}</strong></div><div><span class="label">Generated</span><strong>{generated}</strong></div></div><p class="sample-notice"><strong>SYNTHETIC DEMO DATA / DESIGN PREVIEW</strong> - A real AegisLog analysis of a training log. These results do not describe your computer.</p><section class="summary"><p class="kicker">Executive summary</p><div class="priority"><i></i>DETECTOR REVIEW PRIORITY / {e(groups[0][0][0] if groups else 'ROUTINE REVIEW')}</div><h2>{e(headline)}</h2><p>{e(conclusion)}</p>{observation_html}<p class="priority-meaning">Priority reflects the highest retained detector severity, not a confirmed host security condition.</p></section><div class="metrics">{metrics}</div><div class="section-heading"><span>01</span><h2>Findings register</h2></div><p class="note">All {len(groups)} review groups are shown. Occurrences count detector findings, not confirmed attacks or distinct failures.</p><table class="finding-register"><thead><tr><th>Ref.</th><th>Severity</th><th>Observation</th><th>Count</th><th>First check</th></tr></thead><tbody>{''.join(register)}</tbody></table><p class="page-note">Full review steps and all retained excerpts follow. Grouping supports review; it does not establish a shared cause.</p>{footer}</section>
<section class="sheet" id="evidence">{continuation('RETAINED EVIDENCE')}<div class="section-heading"><span>02</span><h2>Finding details &amp; evidence</h2></div><p class="note">Every retained detector finding has an F-reference. Review groups use G-references and do not create new detections.</p>{''.join(evidence)}<p class="interpretation">Findings are investigation leads, not proof of compromise. Original telemetry should be preserved for further analysis; this report is derived evidence.</p></section>
<section class="sheet" id="activity">{continuation('CORRELATION & COLLECTION RECORD')}<div class="section-heading"><span>03</span><h2>Finding chronology &amp; correlation</h2></div><p class="note">UTC times below come from retained detector excerpts. A burst time is its latest retained failure, not necessarily its start. Timing alone does not establish shared cause.</p><table class="chronology"><thead><tr><th>Observed UTC</th><th>Review lead</th><th>Ref.</th></tr></thead><tbody>{chronology}</tbody></table><h3 class="subheading">Incident groups</h3><p class="note">Groups organize signals, not confirmed incidents. Counts describe detector findings, not authentication attempts. Generic grouping may have no elapsed-time constraint.</p><table class="incident-register"><thead><tr><th>Reference</th><th>Severity</th><th>Observed signal</th><th>Count / evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table><details class="supporting"><summary>Supporting distributions &amp; rarity context</summary><div class="charts"><section class="chart"><h3>Finding categories</h3>{distributions(data.categories)}</section><section class="chart"><h3>Record log levels</h3>{distributions(data.levels)}</section><section class="chart"><h3>Active services</h3>{distributions(data.services)}</section></div><div class="rarity">{anomaly}</div><p class="note">Independent panel scales; source counts are not attacks. Rarity is a sample statistic, not attack probability or confidence. No trained ML model is used.</p></details><div id="method"><div class="section-heading"><span>04</span><h2>Collection record</h2></div><p class="collection-note">{e(data.collection_scope)}</p><p class="collection-note">{data.recognized_records}/{data.records} recognized records. Recognition does not guarantee detection coverage. Missing detections do not establish a clean system.</p><h3 class="subheading">Technical appendix</h3><table class="appendix"><tbody>{appendix}</tbody></table><p class="note">Local, read-only, deterministic analysis. Report reference identifies output; SHA-256 identifies bytes read, not a complete or unchanged live source. Preserve original telemetry. Additional distributions and rarity context are available in the browser version.</p></div><div class="end-signature"><strong>MADE BY HR-PRESENTS</strong><p>AEGISLOG / DEFENSIVE LOG INVESTIGATION</p></div><p class="note" style="text-align:center;margin-top:15px">{e(ref)} / Generated locally / Read-only source</p></section></main></body></html>'''


def generate(root):
    root.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 10, 4, 14, tzinfo=timezone.utc)
    rows = []
    for i in range(108):
        stamp = (start + timedelta(seconds=i*7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        service = ['api', 'scheduler', 'backup', 'sshd', 'worker'][i % 5]
        rows.append(f'{stamp} INFO {service}[{100+i}]: Completed routine training task\n')
    for i in range(6):
        stamp = (start + timedelta(seconds=120+i*8)).strftime('%Y-%m-%dT%H:%M:%SZ')
        rows.append(f'{stamp} WARNING sshd[2200]: Failed password for training-user from 203.0.113.7 port 52100 ssh2 host=training-lab\n')
    rows += ['2026-10-04T14:05:12Z Service Control Manager[7011]: ERROR A timeout (30000 milliseconds) was reached while waiting for a transaction response from the TrainingBackup service.\n', '2026-10-04T14:05:40Z Service Control Manager[7011]: ERROR A timeout (30000 milliseconds) was reached while waiting for a transaction response from the TrainingBackup service.\n', '2026-10-04T14:08:10Z Microsoft-Windows-DistributedCOM[10010]: ERROR The training application did not register with DCOM within the required timeout.\n']
    rows.sort()
    source = root / 'AegisLog-Report-Design-Synthetic.log'
    source.write_text(''.join(rows))
    data = replace(analyze_dashboard(source), source_label=source.name, collection_scope='Complete selected synthetic file: 04 Oct 2026, 14:00-14:12 UTC. This training fixture combines ISO application records and Windows-shaped operational events. No native host telemetry was collected.')
    target = root / 'AegisLog-Document-Report-Preview.html'
    target.write_text(build_document(data))
    print(f'{target}: {data.records} records, {len(data.findings)} findings, {len(_finding_groups(data))} groups')
    return target


if __name__ == '__main__':
    import sys
    generate(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('report-layout-qa/document-preview'))
