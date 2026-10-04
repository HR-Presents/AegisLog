"""Document presentation adapted from the supplied HR-Presents Sentrix report."""
from html import escape


def document_cover(source, case_id, formats, generated, logo_uri, *, summary=False, demo=False):
    title = 'Investigation Summary' if summary else 'Log Investigation Report'
    subtitle = ('Findings, incidents, activity and collection coverage for ' + source + '.')
    cards = ''.join(f'<div><dt>{label}</dt><dd>{escape(str(value))}</dd></div>' for label, value in (
        ('Source', source), ('Report ID', case_id), ('Record formats', formats), ('Generated', generated)))
    return (
        '<header class="sentrix-cover" id="cover">'
        '<svg class="cover-background" aria-hidden="true" viewBox="0 0 100 100" preserveAspectRatio="none">'
        '<defs><linearGradient id="cover-gradient" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#071221"/><stop offset=".55" stop-color="#142f54"/>'
        '<stop offset="1" stop-color="#176fff"/></linearGradient></defs>'
        '<rect width="100" height="100" fill="url(#cover-gradient)"/></svg>'
        '<div class="cover-brand">'
        f'<img class="cover-logo" src="{escape(logo_uri)}" alt="AegisLog terminal mark logo">'
        '<div><strong>AegisLog</strong><span>PRESENTED BY HR-PRESENTS</span></div></div>'
        '<div class="cover-heading"><p class="cover-kicker">DEFENSIVE LOG INVESTIGATION</p>'
        f'<h1>{title}</h1><p class="cover-subtitle">{escape(subtitle)}</p></div>'
        f'<dl class="cover-cards">{cards}</dl>'
        + ('<p class="cover-demo">SYNTHETIC DEMO DATA · Training signals, not findings about your computer.</p>' if demo else '')
        + '<p class="cover-footer">Local investigation output · Read-only sources · Deterministic analysis</p></header>'
    )


def document_contents(entries):
    links = ''.join(f'<a href="{escape(target)}">{escape(label)}</a>' for target, label in entries)
    return '<nav class="document-contents" aria-label="Document contents"><p class="document-label">DOCUMENT NAVIGATION</p><h2>Contents</h2>' + links + '</nav>'


REFERENCE_STYLE = """
.report{width:min(960px,calc(100% - 48px));max-width:960px;margin:32px auto;font-family:"Segoe UI",Arial,sans-serif}
.sentrix-cover{position:relative;isolation:isolate;min-height:1120px;padding:64px 64px 120px;border-radius:2px;overflow:hidden;margin-bottom:28px}
.cover-background{position:absolute;inset:0;width:100%;height:100%;z-index:-1}
#aegislog-report .sentrix-cover,#aegislog-report .sentrix-cover *{color:#fff!important}
.cover-brand{display:flex;align-items:center;gap:28px}
.cover-logo{width:90px;height:auto;background:transparent;filter:brightness(0) invert(1)}
.cover-brand strong{display:block;font-size:36px;font-weight:800;line-height:1.25}
.cover-brand span{display:block;font-size:11px;font-weight:800;letter-spacing:.18em;margin-top:10px}
.cover-heading{margin-top:120px}
.cover-kicker{font-size:13px;font-weight:800;letter-spacing:.13em;margin:0 0 8px}
.sentrix-cover h1{font-size:48px;line-height:1.15;letter-spacing:-.025em;margin:0 0 22px}
.cover-subtitle{font-size:21px;line-height:1.6;margin:0 0 32px;overflow-wrap:anywhere}
.cover-cards{display:grid;gap:18px;margin:0}
.cover-cards>div{padding:19px 20px;border:1px solid #7290b4;border-radius:14px;background:rgba(255,255,255,.09)}
.cover-cards dt{font-size:13px;margin-bottom:6px;opacity:.8}
.cover-cards dd{font-size:16px;font-weight:700;margin:0;overflow-wrap:anywhere}
.cover-footer{position:absolute;bottom:48px;left:64px;right:64px;font-size:12px;opacity:.8;margin:0}
.cover-demo{font-size:12px;font-weight:700;margin-top:18px}
.document-contents,.report .section,.report.summary #executive,.report.summary .summary-notes{border:1px solid #d3def0;border-radius:16px;padding:28px;margin:0 0 24px;background:#fff}
.document-label,#aegislog-report .section-label{display:block;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin:0 0 6px}
#aegislog-report .document-label,#aegislog-report .section-label{color:#1152c3!important}
.document-contents h2{font-size:24px;margin:0 0 18px}
.document-contents a{display:block;font-size:16px;text-decoration:none;padding:14px 0;border-bottom:1px dashed #d3def0}
#aegislog-report .document-contents a{color:#0755d5!important}
.document-contents a:last-child{border-bottom:0}
.report .metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-bottom:24px}
.report .metric{border-radius:16px;padding:22px;min-height:112px;background:#fff}
.report .metric strong{font-size:30px;margin-top:14px}
.report .section-head{margin-bottom:20px}
.report .section-head h2{font-size:24px}
.report.summary #executive .hero h2{font-size:20px;letter-spacing:0}
.report .assessment{background:#eaf2ff;border-left:4px solid #287bff;border-radius:10px;padding:18px 20px}
.report .assessment p{margin:0 0 12px}
.report .assessment p:last-child{margin-bottom:0}
.report .review-priority{border:1px solid #d3def0;background:#f7f9fc}
.report .summary-finding,.report .finding-group{border-radius:12px;background:#f7f9fc}
.report .finding-columns{padding:18px 20px}
.report .observed-facts{font-size:16px}
.report .finding-columns p{font-size:16px!important}
.report .summary-notes h2{font-size:24px;margin-bottom:14px}
.report .context-notice{background:#eaf2ff;border-radius:8px}
.report .content{padding:0}
@media(max-width:700px){
.report{width:calc(100% - 28px);margin:16px auto}
.sentrix-cover{padding:30px 24px 90px;min-height:940px}
.cover-brand{gap:18px}.cover-logo{width:64px}.cover-brand strong{font-size:29px}.cover-brand span{font-size:9px;letter-spacing:.1em}
.cover-heading{margin-top:70px}.sentrix-cover h1{font-size:36px}.cover-subtitle{font-size:18px}
.cover-footer{left:24px;right:24px;bottom:30px}
.document-contents,.report .section,.report.summary #executive,.report.summary .summary-notes{padding:20px}
.report .hero,.report .finding-columns{grid-template-columns:1fr}
.report .metric strong{font-size:25px}
}
@media print{
.report{width:auto;max-width:none;margin:0;font-size:13px}
.sentrix-cover{height:267mm;min-height:0;padding:14mm 13mm 28mm;margin:0;break-after:page;break-inside:avoid;border-radius:0}
.cover-brand{gap:7mm}.cover-logo{width:22mm}.cover-brand strong{font-size:30px}.cover-brand span{font-size:9px}
.cover-heading{margin-top:28mm}.sentrix-cover h1{font-size:38px;margin-bottom:6mm}.cover-subtitle{font-size:18px;line-height:1.6;margin-bottom:8mm}
.cover-cards{gap:5mm}.cover-cards>div{padding:5mm;border-radius:12px}.cover-cards dt{font-size:12px}.cover-cards dd{font-size:14px}
.cover-footer{bottom:13mm;left:13mm;right:13mm;font-size:10px}.cover-demo{font-size:10px}
.document-contents{padding:18px 22px;margin:0 0 18px;break-inside:avoid}
.document-contents a{padding:9px 0;font-size:13px}.document-contents h2{font-size:22px;margin-bottom:12px}
.report .section,.report.summary #executive,.report.summary .summary-notes{padding:18px 22px;margin-bottom:18px;border:1px solid #d3def0;border-radius:14px}
.report .section-head h2,.report .summary-notes h2{font-size:22px}
.report .metrics,.report.summary .metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-bottom:18px}
.report .metric,.report.summary .metric{min-height:90px;padding:16px}.report .metric strong,.report.summary .metric strong{font-size:27px}
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
