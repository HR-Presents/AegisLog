"""Presentation of observed fields; never infer missing evidence or new detections."""
import re
from html import escape


def observed_facts(item, year_hint=None):
    from .engine import _auth_event
    event = _auth_event(item.evidence, year_hint)
    facts = []
    failures = re.match(r'^(\d+) authentication failures\b', item.evidence)
    if failures:
        facts.append(('Failures', failures.group(1)))
    for label, value in (('Account', event.account), ('Source address', event.source_ip), ('Host', event.host)):
        if value:
            facts.append((label, value))
    service = re.search(r'\b([\w.-]+)\[(\d+)\]:', item.evidence)
    if service:
        facts.extend([('Service', service.group(1)), ('Process', service.group(2))])
    windows_id = re.search(r'\bEvent ID\s+(\d+)\b', item.evidence)
    if windows_id:
        facts.append(('Event ID', windows_id.group(1)))
    facts.append(('Timestamp', event.timestamp.isoformat() if event.timestamp else 'Unresolved'))
    return '<dl class="observed-facts">' + ''.join(
        f'<dt>{escape(label)}</dt><dd>{escape(str(value))}</dd>' for label, value in facts
    ) + '</dl>'


def why_it_matters(category):
    return {
        'authentication': 'Repeated failures need account and login-outcome context; they can reflect probing or legitimate errors.',
        'privilege': 'Privilege activity needs validation against the account, session and authorized administrative work.',
        'web': 'Check the requested endpoint and response before treating a request as a successful exploit.',
        'network': 'Blocked traffic needs exposure and source context; a block alone does not establish compromise.',
        'error': 'An operational error may affect service availability. Establish the cause and user impact.',
        'service': 'Service failures may affect availability. Correlate resource pressure and surrounding events.',
    }.get(category, 'Validate this signal against original telemetry and the affected component before escalation.')


REPORT_DESIGN_STYLE = """
.report{--ink:#000;--ink-soft:#000;--muted:#000;max-width:1120px}
#aegislog-report,#aegislog-report *{color:#000!important}
#aegislog-report svg text{fill:#000!important}
.report .masthead{padding:8px 0 12px;margin-bottom:12px}
.report .summary-header{grid-template-columns:100px minmax(0,1fr);gap:20px}
.report .summary-header .aegislog-report-logo{width:100px}
.report .summary-header h1{font-size:25px}
.report .summary-meta{margin-top:8px;padding-top:8px}
.report .summary-kicker{margin-bottom:4px}
.report .summary-status,.report .summary-demo-label{font-size:12px}
.report .summary-demo-label{margin-top:5px}
.report .hero{display:grid;grid-template-columns:minmax(0,1.8fr) minmax(180px,1fr);gap:26px;align-items:start}
.report.summary #executive .hero h2{text-transform:none;font-size:32px;line-height:1.2;border:0;padding:0;letter-spacing:-.025em}
.report .hero .assessment p{font-size:17px!important;line-height:1.6;margin-top:12px;font-weight:400}
.report .review-priority{padding:16px 18px;background:#f5f8fc;border-radius:8px}
.report .review-priority strong{display:block;font-size:20px;margin:4px 0 8px}
.report.summary #executive{border:0;background:none;padding:8px 0 20px;margin-bottom:10px}
.report .review-priority .caveat{font-size:13px!important;line-height:1.6;margin:0}
.report .summary-finding,.report .finding-group{border:1px solid #dfe6ef;border-radius:10px;padding:0!important;display:block!important;margin:0 0 20px;overflow:visible}
.report .finding-group:last-child{border:1px solid #dfe6ef;margin-bottom:20px}
.report .finding-content{padding:0}
.report .finding-index{float:left;padding:20px 0 0 20px;font-size:12px}
.report .summary-finding .record-head{padding:18px 20px 16px 76px;border-bottom:1px solid #dfe6ef;margin:0;min-height:70px}
.report .summary-finding .record-head strong,.report .finding-group .record-head strong{font-size:21px!important;line-height:1.4}
.report .finding-columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px;padding:18px 20px}
.report .finding-columns .cell-label{font-size:12px!important;letter-spacing:.05em;text-transform:uppercase;margin:0 0 10px}
.report .observed-facts{display:grid;grid-template-columns:auto minmax(0,1fr);gap:6px 16px;font-size:15px;margin:0}
.report .observed-facts dd{margin:0;font-weight:600;overflow-wrap:anywhere}
.report .finding-columns p{font-size:16px!important;line-height:1.6}
.report .finding-columns .why{font-size:13px!important;margin-top:12px}
.report details.report-evidence{border-top:1px solid #dfe6ef;padding:12px 20px;background:#f5f8fc;border-radius:0 0 10px 10px}
.report details.report-evidence summary{font-size:14px;font-weight:600;cursor:pointer;min-height:24px}
.report .report-evidence .evidence{font-size:14px!important;line-height:1.65;padding:10px 0!important;border:0!important;background:none!important}
.report .report-evidence .evidence-link{display:inline-block;font-size:13px;margin-top:8px}
.report .group-intro{background:none;border:0;padding:18px 20px;margin:0}
.report .group-evidence{padding:10px 0}
.report .section-head h2{border:0;padding:0;font-size:22px}
.report .summary-notes{border-radius:0}
.report .distribution-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;margin:10px 0;font-size:14px}
.report .distribution-row span{overflow-wrap:anywhere}
.report .distribution-track{grid-column:1/-1;background:#e8eef8;height:7px;border-radius:3px;overflow:hidden}
.report .distribution-track i{display:block;height:0;border-top:7px solid #397dcc;box-sizing:border-box}
@media(max-width:700px){.report .hero,.report .finding-columns{grid-template-columns:1fr}.report.summary #executive .hero h2{font-size:27px}}
@media print{
@page{size:A4;margin:14mm 13mm 16mm;@bottom-left{content:"AEGISLOG / HR-PRESENTS";font:9px Arial;color:#000}@bottom-right{content:counter(page) " / " counter(pages);font:9px Arial;color:#000}}
.report .summary-header{grid-template-columns:90px minmax(0,1fr)}
.report .summary-header .aegislog-report-logo{width:90px}
.report .summary-header h1{font-size:23px}
.report .hero{grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:18px}
.report.summary #executive .hero h2{font-size:21px;letter-spacing:-.025em}
.report .hero .assessment p{font-size:13px!important}
.report .review-priority{padding:10px 12px}
.report .review-priority strong{font-size:16px}
.report .review-priority .caveat{font-size:11px!important}
.report.summary .summary-finding,.report .finding-group{break-inside:auto;margin-bottom:14px}
.report .summary-finding .record-head,.report .group-intro{break-after:avoid;break-inside:avoid}
.report .summary-finding .record-head{padding:12px 14px 10px 65px}
.report .summary-finding .record-head strong,.report .finding-group .record-head strong{font-size:16px!important}
.report .finding-index{padding:14px 0 0 14px}
.report .finding-columns{padding:12px 14px;gap:18px;break-inside:avoid}
.report .observed-facts{font-size:12px}
.report .finding-columns p{font-size:13px!important}
.report .finding-columns .why{font-size:11px!important}
.report details.report-evidence{padding:10px 14px;break-inside:auto}
.report details.report-evidence summary{font-size:11px;break-after:avoid}
.report .report-evidence .evidence{font-size:12px!important;line-height:1.5;white-space:pre-wrap}
.report .group-evidence{break-inside:auto}
.report.summary .section{padding:8px 0;margin-bottom:4px}
.report.summary #executive{padding:6px 0 12px;margin-bottom:4px}
.report.summary .summary-notes{padding:8px 0;margin:4px 0}
.report.summary .context-notice{padding:6px 0;margin:6px 0}
.report .observed-facts{grid-template-columns:auto minmax(0,1fr) auto minmax(0,1fr);gap:3px 8px}
.report.summary .priority-lead{display:none}
.report.summary #scope{padding:6px 0;margin:0}

.report .finding-columns{padding:10px 14px}
.report .report-evidence .evidence{padding:6px 0!important}
.report #incidents,.report #anomalies{break-inside:avoid}
.report #incidents p,.report #anomalies p{break-inside:avoid}
.report #method{break-inside:auto}
.report .telemetry-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.report .telemetry-card{margin-top:0}
.report.summary .record-head{min-height:0;padding-top:8px;padding-bottom:8px}
.report.summary .finding-columns{padding:8px 12px;gap:12px}
.report.summary .finding-columns p{line-height:1.45;margin:4px 0}
.report.summary .finding-columns .cell-label{margin-bottom:6px}
.report.summary details.report-evidence{padding:6px 12px}
.report.summary .report-evidence .evidence{margin:0;padding:4px 0!important}
.report.summary .report-evidence .evidence-link{margin-top:4px}
.report.summary .section-head{margin-bottom:6px}
.report.summary .section-note{margin-bottom:6px}
.report.summary th,.report.summary td{padding:6px}
.report.summary .summary-chart-grid h3{margin:4px 0}
.report.summary #scope .scope>a{display:none}
.report .distribution-row{font-size:12px;margin:6px 0}
.report .footer{display:none}
}
"""

REPORT_EVIDENCE_SCRIPT = """<script>
(() => {
 const evidence = [...document.querySelectorAll('details.report-evidence')];
 evidence.forEach(item => item.open = false);
 const revealAnchor = () => {
  let anchor; try { anchor = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  const target = document.getElementById(anchor);
  if (target) { const parent = target.closest('details'); if (parent) parent.open = true; }
 };
 let before = null;
 window.addEventListener('beforeprint', () => {
  if (before === null) before = evidence.map(item => item.open);
  evidence.forEach(item => item.open = true);
 });
 window.addEventListener('afterprint', () => {
  if (before) evidence.forEach((item, index) => item.open = before[index]);
  before = null;
 });
 window.addEventListener('hashchange', revealAnchor);
 revealAnchor();
})();
</script>"""
