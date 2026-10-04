"""Company-facing presentation. This module does not create detection findings."""
from collections import Counter
import re
from datetime import datetime, timezone
from html import escape


def issue_name(item):
    from .parsers import WINDOWS_EVENT
    context = dict(item.context)
    match = WINDOWS_EVENT.match(item.evidence.strip())
    if match:
        context.setdefault('provider', match.group('provider').strip())
        context.setdefault('event_id', match.group('event_id'))
    provider = context.get('provider', '').casefold()
    evidence = item.evidence.casefold()
    event_id = context.get('event_id', '')
    if provider == 'microsoft-windows-distributedcom' and event_id == '10010':
        return 'DCOM application registration timeout'
    if provider == 'service control manager' and event_id == '7011':
        return 'Service response timeout'
    if provider == 'microsoft-windows-windowsupdateclient' and event_id == '20' and 'installation failure' in evidence:
        return 'Windows update installation failure'
    return item.title


def brief_evidence(item, limit=210):
    """Keep a bounded representative excerpt; original evidence stays in appendix."""
    text = item.evidence.split(' | AEGIS_EVENT_DATA=', 1)[0]
    text = re.sub(r'^\S+\s+[^\n]+?\[\d+\]:\s+(?:ERROR|WARNING|INFO|CRITICAL)\s+', '', text)
    if len(text) > limit:
        return text[:limit].rsplit(' ', 1)[0] + '…'
    return text


def brief_review(item, fallback):
    name = issue_name(item)
    if name == 'DCOM application registration timeout':
        return 'Identify the recorded CLSID’s application; check startup logs and user impact. Do not change permissions based on this timeout alone.'
    if name == 'Service response timeout':
        return 'Review the named service’s logs, dependencies, restart history and resource pressure. Validate the cause before changing settings.'
    return fallback


def assessment(data, groups):
    if not groups:
        return ('No rule-backed findings recorded',
                'No matching detections were recorded in the supplied evidence. This is not a clean-system verdict. Review collection and parser coverage before drawing a conclusion about the host.')
    categories = {key[1] for key, _ in groups}
    if categories <= {'error', 'service'}:
        names = list(dict.fromkeys(issue_name(members[0][1]) for _, members in groups))
        return ('Operational issues need validation',
                f'{len(data.findings):,} retained findings across {len(groups)} review groups. Observed: ' + '; '.join(names[:3]) + '. Confirm user impact; these observations alone do not establish compromise.')
    return ('Security investigation leads require review',
            f'{len(data.findings):,} retained findings across {len(groups)} review groups. Start with {issue_name(groups[0][1][0][1])}. Validate the evidence, identity, and surrounding activity before escalation.')


def _activity(data):
    from .engine import _parse_timestamp
    stamps = [_parse_timestamp(line, data.timestamp_year_hint) for line in data.raw_lines]
    buckets = Counter(s.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M') for s in stamps if s is not None)
    if len(buckets) < 2:
        return '<p>No timestamp-supported trend is shown. Retained excerpts do not provide two resolved minute buckets.</p>'
    items = sorted(buckets.items())[-12:]
    maximum = max(v for _, v in items)
    bars = ''.join(f'<div class="minute"><strong>{v}</strong><svg viewBox="0 0 30 70" role="img" aria-label="{escape(t)} UTC: {v} excerpts"><rect x="5" y="{70-65*v/maximum:.1f}" width="20" height="{65*v/maximum:.1f}" fill="#279aa7"/></svg><span>{t[11:]}</span></div>' for t, v in items)
    return f'<div class="minute-chart">{bars}</div><p class="small">Last {len(items)} occupied UTC minutes • {sum(v for _, v in items)} displayed / {len(stamps)} retained excerpts. Gaps are not shown. Dates: {items[0][0][:10]} to {items[-1][0][:10]}. Not a complete collection timeline.</p>'


def build_company_summary(data, appendix_href):
    from .reporting import _finding_groups, _case_id, _risk, _disposition, _recommendation, _report_context, _ordered_incidents
    from .brand_logo import report_logo_uri
    from . import __version__
    groups = _finding_groups(data)
    headline, conclusion = assessment(data, groups)
    generated = datetime.now(timezone.utc).strftime('%d %b %Y · %H:%M UTC')
    source = data.source_label or data.source.replace('\\', '/').rsplit('/', 1)[-1]
    rows = []
    seen_actions = {}
    for number, (key, members) in enumerate(groups[:6], 1):
        index, item = members[0]
        context = dict(item.context)
        facts = ' · '.join(v for v in [context.get('provider'), 'Event ' + context['event_id'] if context.get('event_id') else '', context.get('host')] if v)
        action = brief_review(item, _recommendation(item))
        if action in seen_actions:
            action_html = f'<a href="#action-{seen_actions[action]}">Same next action as group {seen_actions[action]}</a>'
        else:
            seen_actions[action] = number
            action_html = f'<span id="action-{number}">{escape(action)}</span>'
        rows.append(f'<article class="issue"><div class="issue-heading"><span class="ref">{number:02d}</span><h3>{escape(issue_name(item))}</h3><span class="severity">{escape(item.severity)}</span><strong>{len(members)} occurrence(s)</strong></div><p class="facts">{escape(facts or item.category)}</p><div class="issue-columns"><div><h4>Observed</h4><p>{escape(brief_evidence(item))}</p><a href="{escape(appendix_href)}#finding-{index:03d}">Full evidence · F-{index:03d}</a></div><div><h4>Recommended review</h4><p>{action_html}</p></div></div></article>')
    metrics = ''.join(f'<div><span>{label}</span><strong>{value}</strong></div>' for label, value in [('Records reviewed', f'{data.records:,}'), ('Finding occurrences', str(len(data.findings))), ('Review groups', str(len(groups))), ('Recognized records', f'{data.recognized_records:,} / {data.records:,}')])
    incidents = ''.join(f'<tr><td><a href="{escape(appendix_href)}#incident-{escape(i.id)}">INC-{escape(i.id.upper()[:8])}</a></td><td>{escape(i.severity)}</td><td>{escape(i.title)}<small>{escape(i.context)}</small></td><td>{i.count}</td></tr>' for i in _ordered_incidents(data)[:2])
    incident_table = f'<table><thead><tr><th>Reference</th><th>Severity</th><th>Observed group</th><th>Count</th></tr></thead><tbody>{incidents}</tbody></table>' if incidents else '<p>No correlated incidents were recorded.</p>'
    services = sorted(data.services.items(), key=lambda kv: -kv[1])[:5]
    maximum = max((v for _, v in services), default=1) or 1
    providers = ''.join(f'<div class="provider"><span>{escape(k)}</span><strong>{v}</strong><div class="provider-bar"><i style="width:{100*v/maximum:.1f}%"></i></div></div>' for k, v in services)

    limits = [f'{n} {label}' for n, label in [(data.invalid_records, 'invalid records'), (data.truncated_lines, 'truncated lines'), (data.dropped_findings, 'omitted findings'), (data.dropped_auth_events, 'evicted authentication events')] if n]
    preview = '<p class="preview">DESIGN PREVIEW · Reconstructed from the supplied PDF; original source logs are not available.</p>' if getattr(data, 'coverage_status', '') == 'PDF design preview' else ''
    demo = '<p class="preview"><strong>SYNTHETIC DEMO DATA</strong> · Training evidence, not observations about your computer.</p>' if 'SYNTHETIC DEMO DATA' in _report_context(data) else ''
    context_notes = re.sub(r'<p class="context-notice"><strong>SYNTHETIC DEMO DATA</strong>.*?</p>', '', _report_context(data))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AegisLog · Investigation Summary</title><style>{COMPANY_STYLE}</style></head><body><main class="company-report"><nav class="screen-tools"><a href="{escape(appendix_href)}">Complete evidence report</a><a href="{escape(appendix_href)}?print=1">Print complete report / Save PDF</a><button onclick="window.print()">Print / Save PDF</button><span>For PDF: A4, 100% scale, browser Headers and footers off.</span></nav>
<section class="brief-page"><header class="company-header"><img src="{report_logo_uri()}" alt="AegisLog terminal mark logo"><div><p class="eyebrow">DEFENSIVE LOG INVESTIGATION</p><h1>Investigation summary</h1><p class="subtitle">Evidence-led review · Local / Read-only / Deterministic</p></div></header>{preview}{demo}<div class="metadata"><div><span>Source</span><strong>{escape(source)}</strong></div><div><span>Report reference</span><strong>{escape(_case_id(data))}</strong></div><div><span>Generated</span><strong>{generated}</strong></div></div>
<section class="conclusion"><div class="assessment-label">ASSESSMENT <span>{escape(_disposition(_risk(data)))}</span></div><h2>{escape(headline)}</h2><p>{escape(conclusion)}</p></section><div class="metric-strip">{metrics}</div><div class="section-title"><span>01</span><h2>Findings &amp; recommended review</h2></div><p class="small">Showing {min(len(groups),6)} of {len(groups)} presentation groups. Occurrences are detector findings, not distinct confirmed failures.</p>{''.join(rows) or '<p>No finding groups to display. See coverage on the following page.</p>'}<p class="page-note">SUMMARY ONLY · The complete evidence report preserves original rule titles, retained excerpts, identifiers, and detailed interpretation.</p></section>
<section class="brief-page support-page"><div class="continuation"><strong>AEGISLOG</strong><span>INVESTIGATION SUMMARY / SUPPORTING CONTEXT</span></div><div class="section-title"><span>02</span><h2>Activity &amp; correlation</h2></div><div class="activity-grid"><section><h3>Retained activity</h3>{_activity(data)}</section><section><h3>Most active providers</h3>{providers or '<p>No provider observations available.</p>'}<p class="small">Top {len(services)} observed providers. Counts describe source records, not attacks.</p></section></div><h3>Incident groups</h3>{incident_table}<p class="small">Showing {min(2, len(data.incidents))} of {len(data.incidents)} incident groups. Groups organize related retained signals. Validate shared cause and timing before treating them as one incident.</p>
<div class="section-title"><span>03</span><h2>Collection scope &amp; interpretation</h2></div><div class="scope-grid"><div><h4>Collection</h4><p>{escape(data.collection_scope or 'Selected file analysis; retained evidence is bounded.')}</p></div><div><h4>Coverage</h4><p>{data.recognized_records:,} / {data.records:,} recognized records. Formats: {escape(', '.join(sorted(data.format_counts or {})) or 'generic / unresolved')}.</p><p>{len(data.raw_lines):,} / {data.records:,} excerpts available to this rendering. {escape('; '.join(limits)) if limits else 'No recorded truncation, omitted findings, or authentication evictions.'}</p></div></div><div class="interpretation"><strong>Read this result in context</strong>{context_notes}<p>Findings are investigation leads, not proof of compromise. No matching rule does not establish a clean system. Activity and rarity describe the retained sample. Preserve original logs and review surrounding events before taking action.</p><a href="{escape(appendix_href)}">Open complete investigation record →</a></div><footer><strong>MADE BY HR-PRESENTS</strong><span>AEGISLOG · DEFENSIVE LOG INVESTIGATION</span><small>{escape(_case_id(data))} · AegisLog {escape(__version__)} · Generated locally</small></footer></section></main></body></html>'''


COMPANY_STYLE = '''
*{box-sizing:border-box}body{margin:0;background:#edf5f6;color:#000;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5}a{color:#000;text-decoration:underline;text-underline-offset:3px}button{background:#c9edf1;border:0;padding:12px 18px;color:#000;font-weight:bold;cursor:pointer}.company-report{max-width:1060px;margin:28px auto}.brief-page{background:#fff;padding:38px 48px;margin:0 0 24px;box-shadow:0 3px 18px #19363c12}.screen-tools{display:flex;gap:20px;align-items:center;margin:20px}.screen-tools span{font-size:12px}.company-header{display:grid;grid-template-columns:260px 1fr;gap:38px;align-items:center;padding:14px 0 24px;border-top:7px solid #b9e6ed}.company-header img{width:250px;height:auto;background:transparent}.eyebrow{font-size:11px;letter-spacing:2px;margin:0 0 10px;font-weight:700}h1{font-size:38px;line-height:1.05;letter-spacing:-1px;margin:0 0 14px}h2,h3,h4,p{margin:0}h2{font-size:24px;line-height:1.2;letter-spacing:-.4px}h3{font-size:17px;margin:0 0 12px}h4{font-size:11px;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px}p{margin:6px 0 12px}.subtitle{font-size:13px}.metadata{display:grid;grid-template-columns:1.5fr 1fr 1.2fr;gap:20px;padding:18px 0;border-top:1px solid #bddce1;border-bottom:1px solid #bddce1;font-size:12px;overflow-wrap:anywhere}.metadata span{display:block;font-size:10px;margin-bottom:4px}.metadata strong{font-weight:500}.conclusion{margin:24px 0;background:#eaf8fa;border-left:4px solid #299aa7;padding:18px 22px}.assessment-label{font-size:10px;font-weight:bold;letter-spacing:1.3px;display:flex;justify-content:space-between;margin-bottom:8px}.assessment-label span{letter-spacing:.4px}.conclusion p{margin-bottom:0}.metric-strip{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #bddce1;padding:0 0 20px;gap:16px}.metric-strip span{display:block;font-size:11px}.metric-strip strong{font-size:27px;letter-spacing:-.8px}.section-title{display:grid;grid-template-columns:30px minmax(0,1fr);align-items:center;gap:12px;margin:24px 0 10px}.section-title>span{font-size:12px;font-weight:bold;background:#d9f1f4;padding:5px 9px}.section-title h2{font-size:21px}.small,.page-note{font-size:11px;line-height:1.5}.issue{padding:16px 0;border-bottom:1px solid #bddce1;break-inside:avoid}.issue-heading{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.issue-heading h3{flex:1;margin:0;font-size:17px}.issue-heading>strong{font-size:11px;white-space:nowrap}.ref{font-size:11px;font-weight:bold}.severity{font-size:10px;border:1px solid #a5d7df;background:#eff9fa;padding:2px 6px;font-weight:bold}.facts{font-size:10px;margin:4px 0 8px 25px;overflow-wrap:anywhere}.issue-columns{display:grid;grid-template-columns:1fr 1.15fr;gap:24px}.issue-columns p{font-size:15px;line-height:1.5;overflow-wrap:anywhere;margin:0 0 5px}.issue-columns a{font-size:10px}.page-note{margin:14px 0 0}.continuation{display:flex;justify-content:space-between;border-top:7px solid #b9e6ed;border-bottom:1px solid #bddce1;padding:16px 0;font-size:10px;letter-spacing:1px}.continuation strong{font-size:15px;letter-spacing:.5px}.activity-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:32px;padding:12px 0 18px}.minute-chart{display:flex;gap:6px;align-items:end;height:130px}.minute{flex:1;min-width:0;text-align:center}.minute strong{font-size:10px;display:block}.minute svg{display:block;width:100%;height:82px}.minute span{font-size:8px;display:block}.provider{display:grid;grid-template-columns:1fr 30px;gap:4px;font-size:11px;margin:9px 0}.provider span{overflow-wrap:anywhere}.provider strong{text-align:right}.provider-bar{height:5px;background:#e7f4f6}.provider-bar i{display:block;height:5px;border-top:5px solid #279aa7}.provider svg{grid-column:1/-1;width:100%;height:5px;display:block}.activity-grid p{font-size:12px}table{width:100%;border-collapse:collapse;font-size:11px;table-layout:fixed}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #bddce1;vertical-align:top;overflow-wrap:anywhere}th{background:#edf8fa;font-size:10px}th:nth-child(1){width:22%}th:nth-child(2){width:15%}th:last-child{width:10%}td small{display:block;font-size:10px;margin-top:4px}.scope-grid{display:grid;grid-template-columns:1.1fr 1fr;gap:30px;padding:12px 0}.scope-grid p{font-size:13px}.interpretation{padding:16px 20px;background:#edf8fa;font-size:13px;margin:16px 0}.interpretation strong{font-size:13px}.interpretation a{font-size:12px}footer{border-top:2px solid #299aa7;text-align:center;padding:20px 0 0;margin-top:24px;break-inside:avoid}footer strong{display:block;font-size:18px;letter-spacing:1px}footer span{display:block;font-size:9px;letter-spacing:1.3px;margin:7px 0}footer small{font-size:9px}.preview{font-size:10px;font-weight:bold;border-left:3px solid #299aa7;padding-left:10px;margin:0 0 12px}
@media(max-width:700px){.company-report{margin:0}.brief-page{padding:24px}.company-header{grid-template-columns:1fr;gap:20px}.metadata{grid-template-columns:1fr}.metric-strip{grid-template-columns:1fr 1fr}.issue-columns,.activity-grid,.scope-grid{grid-template-columns:1fr}.issue-heading h3{flex-basis:calc(100% - 25px)}.screen-tools{flex-wrap:wrap}.screen-tools span{flex-basis:100%}.continuation{gap:20px}.minute span{font-size:7px}}
@page{size:A4;margin:11mm 15mm 11mm;@bottom-right{content:counter(page) " / " counter(pages);font-size:9px;color:#000}}
@media print{body{background:#fff;font-size:11pt;line-height:1.45}.company-report{margin:0;max-width:none}.screen-tools{display:none}.brief-page{padding:0;margin:0;box-shadow:none}.support-page{break-before:page}.support-page p{margin-bottom:7px}.support-page .section-title{margin-top:10px}.support-page th,.support-page td{padding:7px 8px}.support-page .activity-grid{padding-bottom:8px}.support-page .interpretation{margin:10px 0;padding:12px 16px}.support-page footer{margin-top:10px;padding-top:10px}.support-page .minute-chart{height:108px}.company-header{padding:8px 0 14px;grid-template-columns:190px 1fr;gap:18px}.company-header img{width:160px}h1{font-size:26px}.conclusion{margin:14px 0;padding:12px 16px}.conclusion h2{font-size:21px}.conclusion p{font-size:12px}.metadata{padding:10px 0;font-size:11px}.metric-strip{padding-bottom:14px}.metric-strip strong{font-size:25px}.section-title{margin:14px 0 8px}.section-title h2{font-size:19px}.issue{padding:7px 0}.issue-heading h3{font-size:15px}.issue-columns p{font-size:12px;line-height:1.35}.facts{font-size:10px}.activity-grid{padding:8px 0 16px}.scope-grid p,.interpretation{font-size:12px}footer{margin-top:16px;padding-top:14px}.brief-page,.company-header,.activity-grid,table,.scope-grid,.interpretation{print-color-adjust:exact;-webkit-print-color-adjust:exact}.preview{font-size:9px}}
'''

COMPANY_FULL_STYLE = '''
.report:not(.summary){font-family:Arial,Helvetica,sans-serif;max-width:1060px;background:#fff;padding:34px 46px}
.report:not(.summary) .aegis-report-header{padding:12px 0 22px;border-top:7px solid #b9e6ed}.report:not(.summary) .cover-logo{width:250px}
.report:not(.summary) .header-layout{grid-template-columns:260px 1fr;gap:32px}.report:not(.summary) .cover-heading h1{font-size:34px}
.report:not(.summary) .section-head{align-items:start;gap:22px}.report:not(.summary) .section-head h2{font-size:24px}.report:not(.summary) .section-note{font-size:12px;max-width:450px}
.report:not(.summary) .finding-group{margin-bottom:26px}.report:not(.summary) .group-intro{padding:14px 0}.report:not(.summary) .group-label{font-size:10px;letter-spacing:1px}
.original-rule{font-size:11px;display:block;width:100%;font-weight:400}.report:not(.summary) .group-evidence{display:grid;grid-template-columns:60px 1fr;gap:12px;border-top:1px solid #d3e7eb;padding:12px 0;break-inside:avoid}
.report:not(.summary) .record-id{font-size:11px}.report:not(.summary) .report-evidence .evidence{font-size:12px!important;line-height:1.6!important}.report:not(.summary) .report-evidence{background:#f0f9fa;padding:14px 18px}
#aegislog-report .section-label{color:#000!important}.report:not(.summary) .finding-columns p{font-size:15px!important}.report:not(.summary) .observed-facts{font-size:14px}.report:not(.summary) .record-head{gap:12px}
.report:not(.summary) .method-grid{gap:24px}.report:not(.summary) .method-card{border:0;border-radius:0;background:#eff9fa}.report:not(.summary) .telemetry-card{border:0;border-radius:0;background:#fff}
@media(max-width:700px){.report:not(.summary){padding:20px;width:100%}.report:not(.summary) .header-layout{grid-template-columns:1fr}.report:not(.summary) .section-head{display:block}.report:not(.summary) .group-evidence{grid-template-columns:1fr}}
@media print{.report:not(.summary) .section-head{break-after:avoid;break-inside:avoid}.report:not(.summary){padding:0;margin:0;width:100%}.report:not(.summary) .header-layout{grid-template-columns:220px 1fr}.report:not(.summary) .cover-logo{width:210px}.report:not(.summary) .cover-heading h1{font-size:29px}.report:not(.summary) #findings{page-break-before:auto;break-before:auto}.report:not(.summary) .document-contents{display:none}.report:not(.summary) .section{padding:12px 0}.report:not(.summary) .section-head h2{font-size:21px}.report:not(.summary) .finding-columns p{font-size:12px!important}.report:not(.summary) .report-evidence .evidence{font-size:11px!important}.report:not(.summary) .finding-columns{padding:12px 0}.report:not(.summary) .finding-group{break-inside:auto}.report:not(.summary) .group-intro{break-inside:avoid}.report:not(.summary) .group-evidence{break-inside:avoid}.original-rule{font-size:10px}}
'''

COMPANY_FULL_STYLE += """
.report:not(.summary) .technical-appendix{margin-top:24px;border-top:2px solid #b9e6ed;padding-top:16px}
.report:not(.summary) .technical-appendix h3{font-size:18px;margin:0 0 6px}
.report:not(.summary) .technical-appendix p{font-size:12px}
.report:not(.summary) .technical-appendix th{width:25%;font-size:12px}
.report:not(.summary) .technical-appendix td{font-size:13px;line-height:1.5;overflow-wrap:anywhere}
.report:not(.summary) .technical-appendix table{table-layout:fixed;width:100%}
@media print{.report:not(.summary) .technical-appendix th,.report:not(.summary) .technical-appendix td{font-size:10px;padding:6px 8px}.report:not(.summary) .technical-appendix h3{break-after:avoid}}
"""

COMPANY_FULL_STYLE += """
@media print{.report:not(.summary){line-height:1.5}.report:not(.summary) .observed-facts{gap:3px 12px;line-height:1.4}.report:not(.summary) .finding-columns .why{font-size:12px!important;line-height:1.5!important;margin-top:8px}.report:not(.summary) .group-intro{padding:8px 0}.report:not(.summary) .finding-columns{padding:10px 0}.report:not(.summary) .finding-group{margin-bottom:14px}.report:not(.summary) .telemetry-grid{break-inside:avoid}}
"""
