"""AegisLog sea-blue investigation brief: results first, evidence below."""
from html import escape


def document_cover(source, case_id, formats, generated, logo_uri, *, summary=False, demo=False):
    title = 'Investigation Summary' if summary else 'Security Investigation Report'
    subtitle = (('' if summary else 'Full evidence · Investigation record. ') + 'Findings, incidents, activity and collection coverage for ' + source + '.')
    cards = ''.join(f'<div><dt>{label}</dt><dd>{escape(str(value))}</dd></div>' for label, value in (
        ('Source', source), ('Report ID', case_id), ('Record formats', formats), ('Generated', generated)))
    return (
        '<header class="aegis-report-header" id="cover">'
        '<svg class="cover-background" aria-hidden="true" viewBox="0 0 100 100" preserveAspectRatio="none">'
        '<defs><linearGradient id="cover-gradient" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#e3f7f8"/><stop offset=".55" stop-color="#d3eff3"/>'
        '<stop offset="1" stop-color="#b9e6ed"/></linearGradient></defs>'
        '<rect width="100" height="100" fill="url(#cover-gradient)"/></svg>'
        '<div class="header-layout"><div class="cover-brand">'
        f'<img class="cover-logo aegislog-report-logo" src="{escape(logo_uri)}" alt="AegisLog terminal mark logo" aria-label="AegisLog terminal mark logo">'
        '<div><strong>AegisLog</strong><span>PRESENTED BY HR-PRESENTS</span></div></div>'
        '<div class="cover-heading"><p class="cover-kicker">DEFENSIVE LOG INVESTIGATION</p>'
        f'<h1>{title}</h1><p class="cover-subtitle">{escape(subtitle)}</p>'
        '<a class="cover-results" href="#executive">View investigation results →</a></div></div>'
        f'<dl class="cover-cards">{cards}</dl>'
        + ('<p class="cover-demo">SYNTHETIC DEMO DATA · Training signals, not findings about your computer.</p>' if demo else '')
        + '<p class="cover-footer">Local investigation output · Read-only sources · Deterministic analysis</p></header>'
    )


def document_contents(entries):
    links = ''.join(f'<a href="{escape(target)}">{escape(label)}</a>' for target, label in entries)
    return '<nav class="document-contents" aria-label="Document contents"><p class="document-label">DOCUMENT NAVIGATION</p><h2>Contents</h2>' + links + '</nav>'


REFERENCE_STYLE = """
.report{width:min(960px,calc(100% - 48px));max-width:960px;margin:32px auto;font-family:"Segoe UI",Arial,sans-serif}
.aegis-report-header{position:relative;isolation:isolate;padding:32px;border:1px solid #abd8de;border-radius:12px;overflow:hidden;margin-bottom:24px}
.cover-background{position:absolute;inset:0;width:100%;height:100%;z-index:-1}
#aegislog-report .aegis-report-header,#aegislog-report .aegis-report-header *{color:#000!important}
.header-layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:32px;align-items:center}
.cover-brand{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
.cover-logo{width:200px;max-width:100%;height:auto;background:transparent;filter:none}
.cover-brand strong{display:block;font-size:28px;font-weight:800;line-height:1.2}
.cover-brand span{display:block;font-size:10px;letter-spacing:.12em;margin-top:6px}
.cover-heading{margin:0}.cover-kicker{font-size:12px;font-weight:700;letter-spacing:.1em;margin:0 0 10px}
.aegis-report-header h1{font-size:36px;line-height:1.15;letter-spacing:-.02em;margin:0 0 14px}
.cover-subtitle{font-size:16px;line-height:1.6;margin:0 0 16px;overflow-wrap:anywhere}
.cover-results{display:inline-block;padding:9px 14px;border:1px solid #70bcc7;border-radius:6px;background:#fff;font-weight:700;text-decoration:none}
.cover-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:24px 0 0;border-top:1px solid #abd8de;padding-top:18px}
.cover-cards>div{padding:0;background:transparent;border:0;min-width:0}
.cover-cards dt{font-size:11px;letter-spacing:.04em;margin-bottom:4px}.cover-cards dd{font-size:14px;font-weight:600;margin:0;overflow-wrap:anywhere}
.cover-footer{font-size:11px;margin:18px 0 0;position:static}.cover-demo{font-size:12px;font-weight:700;margin:16px 0 0}
.evidence-group{display:none}.group-label{padding:12px 20px 0;font-size:12px;font-weight:700}
.count-key{margin:0 0 24px;font-size:14px}.source-fingerprint,.coverage-grid dd{overflow-wrap:anywhere}.coverage-grid .fingerprint-row{grid-column:1/-1}.fingerprint-row dd{font-family:Consolas,monospace;font-weight:400!important;font-size:12px!important}
.document-contents,.report .section,.report.summary .section,.report.summary #executive,.report.summary .summary-notes{border:1px solid #c7e3e7;border-radius:8px;padding:24px;margin:0 0 24px;background:#fff}
.document-label,#aegislog-report .section-label{display:block;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin:0 0 6px}
#aegislog-report .document-label,#aegislog-report .section-label{color:#137c8a!important}
.document-contents h2{font-size:18px;margin:0 0 12px}
.document-contents{padding:16px 20px;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center}.document-contents .document-label{display:none}.document-contents h2{flex-basis:100%}
.document-contents a{display:inline-block;font-size:13px;text-decoration:none;padding:5px 0;border-bottom:1px solid #abd8de}
#aegislog-report .document-contents a{color:#126773!important}
.document-contents a:last-child{border-bottom:0}
.report .metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-bottom:24px}
.report .metric{border-radius:16px;padding:22px;min-height:112px;background:#fff}
.report .metric strong{font-size:30px;margin-top:14px}
.report .section-head{margin-bottom:20px}
.report .section-head h2{font-size:24px}
.report.summary #executive .hero h2{font-size:20px;letter-spacing:0}
.report.summary #executive .section-head h2{font-size:24px;letter-spacing:0;text-transform:none}
.report .assessment{background:#eaf8fa;border-left:4px solid #43aebb;border-radius:10px;padding:18px 20px}
.report .assessment p{margin:0 0 12px}
.report .assessment p:last-child{margin-bottom:0}
.report .review-priority{border:1px solid #d3def0;background:#f7f9fc}
.report .summary-finding,.report .finding-group{border-radius:12px;background:#f7f9fc}
.report .finding-columns{padding:18px 20px}
.report.summary #scope{padding:28px}
.report .observed-facts{font-size:16px}
.report .finding-columns p{font-size:16px!important}
.report .summary-notes h2{font-size:24px;margin-bottom:14px}
.report .context-notice{background:#eaf8fa;border-radius:8px}
.report .content{padding:0}
@media(max-width:700px){
.report{width:calc(100% - 28px);margin:16px auto}
.aegis-report-header{padding:24px}.header-layout{grid-template-columns:1fr;gap:20px}.cover-logo{width:180px}.cover-brand strong{font-size:26px}.aegis-report-header h1{font-size:30px}.cover-cards{grid-template-columns:1fr 1fr}.cover-subtitle{font-size:16px}
.document-contents,.report .section,.report.summary .section,.report.summary #executive,.report.summary .summary-notes{padding:20px}
.report .hero,.report .finding-columns{grid-template-columns:1fr}
.report.summary .summary-finding{display:block}.report.summary .finding-index{float:none;padding:12px 16px 0}.report.summary .summary-finding .record-head{padding:12px 16px}.report.summary .summary-finding .record-head strong{flex-basis:100%}.report.summary .finding-content{min-width:0}
.report.summary #scope{padding:20px}
.report .metric strong{font-size:25px}
}
@media print{
.report{width:auto;max-width:none;margin:0;font-size:13px}
.cover-results{display:none!important}
.evidence-group{display:block;font-size:9px;margin-top:5px;overflow-wrap:normal}.report .group-evidence{grid-template-columns:72px minmax(0,1fr)}
.report #executive,.report #source{break-inside:avoid;page-break-inside:avoid}
.report .finding-group{box-decoration-break:clone;-webkit-box-decoration-break:clone}
.report .group-intro{break-inside:avoid;break-after:avoid}
.report .count-key{font-size:11px;margin-bottom:18px}
.aegis-report-header{height:auto;min-height:0;padding:18px 22px;margin:0 0 16px;break-after:auto;break-inside:avoid;border-radius:8px}
.header-layout{grid-template-columns:150px minmax(0,1fr);gap:22px}.cover-logo{width:140px}.cover-brand strong{font-size:23px}.cover-brand span{font-size:8px}
.cover-heading{margin:0}.aegis-report-header h1{font-size:28px;margin-bottom:10px}.cover-subtitle{font-size:13px;margin:0;line-height:1.5}
.cover-cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 18px;margin-top:16px;padding-top:12px}.cover-cards>div{padding:0;border:0}.cover-cards dt{font-size:10px}.cover-cards dd{font-size:12px}
.cover-footer{font-size:9px;margin-top:12px}.cover-demo{font-size:10px;margin:10px 0 0}
.document-contents{padding:18px 22px;margin:0 0 18px;break-inside:avoid}
.document-contents a{padding:4px 0;font-size:11px}.document-contents h2{font-size:16px;margin:0}
.report .section,.report.summary .section,.report.summary #executive,.report.summary .summary-notes{padding:18px 22px;margin-bottom:18px;border:1px solid #c7e3e7;border-radius:8px}
.report .section-head h2,.report .summary-notes h2{font-size:22px}
.report.summary #executive .section-head h2{font-size:22px}
.report .metrics,.report.summary .metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-bottom:18px}
.report .metric,.report.summary .metric{min-height:90px;padding:16px}.report .metric strong,.report.summary .metric strong{font-size:27px}
.report.summary #scope{padding:18px 22px}
.report:not(.summary) #findings{page-break-before:auto;break-before:auto}
.report:not(.summary) #incidents{break-inside:avoid;page-break-inside:avoid}
.report .observed-facts{grid-template-columns:auto minmax(0,1fr);gap:3px 8px}
.report .assessment{padding:12px 14px}.report .finding-columns p{font-size:13px!important}.report .observed-facts{font-size:12px}
.report.summary .compact-findings{display:block}
.report.summary .compact-findings .record-head{display:flex;padding:12px 14px 12px 64px;min-height:0}
.report.summary .compact-findings .record-head strong{min-height:0}
.report.summary .compact-findings .finding-index{padding:14px 0 0 14px}
.report.summary .compact-findings .finding-columns{grid-template-columns:1fr 1fr;gap:14px}
.report.summary .compact-findings .finding-columns>div:first-child{min-height:0}
.report.summary .compact-findings details.report-evidence{display:block;padding:8px 14px}
.report.summary .summary-evidence-pointer,.report .summary-print-evidence{display:none}
.report.summary #incidents{break-inside:auto}
.report.summary #incidents tr{break-inside:avoid}
.report .summary-chart-grid{break-inside:avoid}
.report .section-head,.report .document-label{break-after:avoid}
}
"""
