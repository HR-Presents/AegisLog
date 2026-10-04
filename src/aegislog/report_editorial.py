"""Editorial report presentation with evidence-backed activity, no new detections."""
from collections import Counter
from html import escape
from datetime import timezone


def activity_timeline(raw_lines, year_hint=None):
    from .engine import _parse_timestamp
    stamps = [_parse_timestamp(line, year_hint) for line in raw_lines]
    resolved = [stamp for stamp in stamps if stamp is not None]
    buckets = Counter(stamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M') for stamp in resolved)
    missing = len(stamps) - len(resolved)
    if len(buckets) < 2:
        reason = ('No resolved minute sequence is available.' if not resolved else
                  'Resolved excerpts occupy a single minute; no temporal trend is inferred.')
        return ('<div class="activity-note"><h3>Activity context</h3><p>' + reason +
                f' {len(resolved):,}/{len(stamps):,} retained excerpts have resolved timestamps.</p></div>')
    items = sorted(buckets.items())[-12:]
    maximum = max(value for _, value in items)
    rows = ''.join(
        f'<div class="timeline-row"><time>{escape(minute)} UTC</time><span class="timeline-track"><svg width="100%" height="12" role="img" aria-label="{value} excerpts"><rect width="100%" height="12" fill="#e2f2f4"/><rect width="{100 * value / maximum:.1f}%" height="12" fill="#299aa7"/></svg></span><strong>{value}</strong></div>'
        for minute, value in items
    )
    return ('<div class="activity-timeline"><h3>Retained activity by minute</h3>' + rows +
            f'<p class="caveat">Last {len(items)} occupied minute buckets · {sum(value for _, value in items):,} displayed excerpts · '
            f'{len(resolved):,} timestamped excerpts retained · {missing:,} unresolved. Gaps are not shown; this is sample activity, not a complete collection timeline.</p></div>')


def report_signature(case_id, version):
    return ('<div class="footer"><div class="maker-signature">MADE BY HR-PRESENTS</div>'
            '<p>AEGISLOG · DEFENSIVE LOG INVESTIGATION</p>'
            f'<small>Report {escape(case_id)} · AegisLog {escape(version)} · Generated locally</small></div>')


EDITORIAL_BRIEF_STYLE = """
.report{max-width:1040px;width:min(1040px,calc(100% - 64px));margin:36px auto}
.aegis-report-header{border:0;border-radius:0;padding:24px 0 20px;background:#fff;border-top:8px solid #b9e6ed;border-bottom:1px solid #bddce1}
.cover-background{height:8px;top:-8px;bottom:auto}
.header-layout{grid-template-columns:280px minmax(0,1fr);gap:36px}.cover-logo{width:260px}.cover-brand span{font-size:10px}
.cover-heading h1{font-size:36px;font-weight:700;letter-spacing:-.03em}.cover-subtitle{font-size:16px}.cover-kicker{font-size:11px;letter-spacing:.14em}
.cover-cards{grid-template-columns:repeat(4,minmax(0,1fr));gap:20px;margin:18px 0 0;padding-top:14px;border:0}.cover-cards dd{font-size:13px;font-weight:500}.cover-cards dt{font-size:10px}
.cover-footer{display:none}.cover-demo{font-size:12px;margin:12px 0 0;border-left:3px solid #299aa7;padding-left:10px}
.report .section,.report.summary .section,.report.summary #executive,.report.summary .summary-notes{border:0;border-radius:0;padding:24px 0;margin:0 0 12px;background:#fff}
.report .section-head{margin-bottom:16px}.report .section-head h2{font-size:27px;font-weight:700;letter-spacing:-.02em}
.report .section-label{font-size:11px}.report.summary #executive .section-head h2{font-size:18px}.report.summary #executive .hero h2{font-size:29px;line-height:1.25;margin:0 0 12px}
.report .assessment{background:transparent;border:0;border-radius:0;padding:0}.report.summary .assessment p{font-size:17px!important}
.report .review-priority{background:#eaf8fa;border:0;border-left:3px solid #299aa7;border-radius:0;padding:18px}
.report.summary .priority-lead{display:block!important;font-size:15px!important;margin:16px 0 0}.report.summary .priority-lead a{font-weight:600}
.report .priority-box{background:#eff9fa;border-radius:0;border:0;padding:18px}.report .decision{border:0;border-left:3px solid #299aa7;border-radius:0;margin:16px 0;padding:10px 14px;background:#eff9fa}
.report .metrics,.report.summary .metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:1px solid #bddce1;border-bottom:1px solid #bddce1;margin:12px 0}
.report .metric,.report.summary .metric{border:0;border-right:1px solid #bddce1;border-radius:0;background:#fff!important;min-height:0;padding:18px 20px}
.report .metric:last-child{border-right:0}.report .metric strong,.report.summary .metric strong{font-size:30px;margin-top:8px;line-height:1.2}.report .metric span{font-size:12px}
.count-key{font-size:13px;line-height:1.6;margin-bottom:18px}
.document-contents{border:0;border-radius:0;padding:10px 0 16px;border-bottom:1px solid #bddce1;margin:0 0 12px;gap:6px 18px}.document-contents h2{font-size:13px;flex-basis:auto;margin:0 8px 0 0}.document-contents a{font-size:12px;border:0}
.report .summary-finding,.report .finding-group,.report .finding-group:last-child{border:0!important;border-top:2px solid #299aa7!important;border-radius:0!important;background:#fff!important;margin:0 0 28px;padding:0!important}
.report .summary-finding .record-head{padding:16px 0 16px 76px;border-bottom:1px solid #d8e8eb}.report .finding-index{padding:20px 0 0;font-weight:700}
.report .finding-columns{padding:20px 0;gap:32px}.report .group-intro{padding:16px 0}.report .group-label{padding:12px 0 0}.report .finding-group .record-head strong{font-size:22px!important}
.report .summary-finding .record-head strong{font-size:22px!important}.report details.report-evidence{border:0;border-left:3px solid #c4e6eb;border-radius:0;background:#f2f9fa;padding:12px 16px}.report .report-evidence .evidence{font-size:14px!important}
.report .record-list{border:0;border-radius:0;padding:0}.report .observed-facts{font-size:16px;gap:8px 16px}.report .finding-columns .why{font-size:14px!important}
.report.summary .summary-notes{border-top:1px solid #bddce1}.report .context-notice{background:transparent;border:0;padding:0;font-size:14px!important;line-height:1.65!important}
.report.summary #scope{padding:20px 0;border-top:1px solid #bddce1}.report.summary #scope .scope p{font-size:14px!important;line-height:1.65!important}
.report .coverage-grid dt{font-size:12px}.report .coverage-grid dd{font-size:14px}.report .coverage-grid .fingerprint-row dd{font-size:12px!important}
.timeline-row{display:grid;grid-template-columns:190px minmax(0,1fr) 32px;gap:14px;align-items:center;margin:10px 0;font-size:13px}.timeline-track{display:block}.timeline-track svg{display:block}.activity-timeline{margin-bottom:24px}.activity-note p{font-size:15px!important}
.report .activity-counts{display:flex;flex-wrap:wrap;gap:8px 24px}.activity-counts span{font-size:15px}.report .summary-service-chart .activity-counts{margin-top:12px}
.report .footer{display:block!important;position:static;border-top:2px solid #299aa7;padding:24px 0 12px;margin:24px 0 0;text-align:center;break-inside:avoid}
.maker-signature{font-size:20px;font-weight:800;letter-spacing:.08em}.report .footer p{font-size:11px!important;letter-spacing:.12em;margin:9px 0}.report .footer small{font-size:11px}
@media(max-width:700px){
.report{width:calc(100% - 40px);margin:20px auto}.header-layout{grid-template-columns:1fr;gap:20px}.cover-logo{width:240px}.cover-heading h1{font-size:30px}.cover-cards{grid-template-columns:1fr 1fr;gap:14px}
.report .metrics,.report.summary .metrics{grid-template-columns:1fr 1fr}.report .metric{padding:14px;border-bottom:1px solid #bddce1}.report .metric:nth-child(2){border-right:0}.report .metric:nth-last-child(-n+2){border-bottom:0}.report .metric strong{font-size:26px}
.report .section,.report.summary .section,.report.summary #executive,.report.summary .summary-notes,.report.summary #scope{padding:20px 0}
.report .hero,.report .finding-columns{grid-template-columns:1fr}.report.summary .summary-finding .record-head{padding:12px 0}.report.summary .finding-index{padding:12px 0 0}.report .finding-columns{padding:16px 0;gap:20px}.report .observed-facts{gap:6px 10px}
.timeline-row{grid-template-columns:minmax(0,1fr) 90px 24px;gap:8px;font-size:11px}.maker-signature{font-size:17px}
}
@media print{
.report{width:auto;max-width:none;margin:0}.aegis-report-header{padding:12px 0 14px;margin:0 0 12px;border:0;border-top:6px solid #b9e6ed;border-bottom:1px solid #bddce1;break-inside:avoid}
.header-layout{grid-template-columns:235px minmax(0,1fr);gap:22px}.cover-logo{width:220px}.cover-heading h1{font-size:28px}.cover-subtitle{font-size:12px}.cover-cards{grid-template-columns:repeat(4,minmax(0,1fr));margin-top:12px;padding-top:0;gap:14px}.cover-cards dd{font-size:11px}.cover-cards dt{font-size:9px}.cover-demo{font-size:10px;margin-top:10px}
.report .section,.report.summary .section,.report.summary #executive,.report.summary .summary-notes{padding:14px 0;margin:0 0 12px;border:0;border-radius:0}
.report .section-head h2{font-size:23px}.report.summary #executive .section-head h2{font-size:16px}.report.summary #executive .hero h2{font-size:24px}.report.summary .assessment p{font-size:13px!important}.report .review-priority{padding:12px}.report.summary .priority-lead{font-size:12px!important;margin:10px 0 0}
.report .metrics,.report.summary .metrics{grid-template-columns:repeat(4,minmax(0,1fr));gap:0;margin:10px 0;break-inside:avoid}.report .metric,.report.summary .metric{min-height:0;padding:12px 14px}.report .metric strong,.report.summary .metric strong{font-size:25px}.report .metric span{font-size:10px}.report .count-key{font-size:10px;margin:0 0 12px}
.document-contents{padding:8px 0 12px;margin-bottom:12px;gap:4px 14px}.document-contents h2{font-size:11px;flex-basis:auto}.document-contents a{font-size:10px;padding:3px 0}
.report .summary-finding,.report .finding-group,.report .finding-group:last-child{margin-bottom:20px;break-inside:auto}.report.summary .compact-findings .record-head,.report .summary-finding .record-head{padding:12px 0 12px 62px}.report.summary .compact-findings .finding-index,.report .finding-index{padding:14px 0 0}
.report .finding-columns,.report.summary .compact-findings .finding-columns{padding:14px 0;gap:24px}.report .observed-facts{font-size:12px}.report .summary-finding .record-head strong,.report .finding-group .record-head strong{font-size:17px!important}
.report .group-intro{padding:12px 0}.report .finding-columns p,.report .finding-columns .why{font-size:14px!important;line-height:1.55!important}.report details.report-evidence,.report.summary .compact-findings details.report-evidence{padding:10px 12px;display:block}.report .report-evidence .evidence{font-size:13px!important;line-height:1.65}
.report.summary .summary-notes .context-notice,.report .context-notice,.report.summary #scope .scope p{font-size:14px!important;line-height:1.6!important}.report .summary-notes h2{font-size:23px}.report.summary #scope{padding:16px 0}.report .coverage-grid dt{font-size:10px}.report .coverage-grid dd{font-size:12px}
.timeline-row{grid-template-columns:155px minmax(0,1fr) 26px;font-size:11px;margin:7px 0}.activity-timeline{break-inside:avoid}.report .activity-counts span{font-size:12px}
.report.summary .section,.report.summary #executive,.report.summary .summary-notes{padding:10px 0;margin-bottom:8px}.report.summary #scope{padding:10px 0}.report.summary .activity-note h3{display:none}
.report .footer{padding:14px 0 0;margin:12px 0 0;display:block!important}.maker-signature{font-size:18px}.report .footer p,.report .footer small{font-size:9px!important}
}
"""
