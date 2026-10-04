"""Shared report components and print rules, separate from evidence generation."""
_REPORT_STYLE = """
:root{--ink:#141c30;--ink-soft:#283244;--muted:#596375;--paper:#fff;--line:#d3def0;--line-soft:#d3def0;--accent:#287bff;--mono:#fff}
*{box-sizing:border-box}html{color-scheme:light;scroll-behavior:smooth}
body{margin:0;background:#fff;color:var(--ink);font:16px/1.65 "Segoe UI",Arial,sans-serif}
.report{width:min(1060px,calc(100% - 48px));margin:32px auto;background:#fff}
.masthead{padding:32px 32px 38px;background:#fff}.brand{display:flex;align-items:center;gap:10px}.brand-mark{width:28px;height:32px}.brand-mark svg{width:28px;height:32px}.brand-name{font-size:28px;font-weight:800;letter-spacing:-.04em}.brand-name span{color:inherit}.brand-sub{font-size:10px;letter-spacing:.2em;font-weight:800;margin-top:5px;color:var(--muted)}.brandline{margin-bottom:42px}.classification,.eyebrow,.posture,.section-label{display:none}
h1{font-size:38px;line-height:1.2;letter-spacing:-.02em;margin:0 0 12px}h2{font-size:23px;line-height:1.3;margin:0}h3{font-size:17px;margin:0 0 12px}.subtitle{margin:0;color:var(--muted)}.cover-meta{font-size:13px;color:var(--muted);margin-top:18px}
.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:0 0 20px;padding:12px;border:1px solid var(--line);border-radius:12px}.toolbar a{color:#245ea8;text-decoration:none;font-size:13px}.toolbar a:hover{text-decoration:underline}.spacer{flex:1}.local-note{font-size:10px;color:var(--muted)}button{background:#287bff;border:0;border-radius:6px;padding:9px 14px;color:white;font:inherit;font-size:13px;cursor:pointer}.context-notice{font-size:13px;line-height:1.5;padding:10px 12px;border-left:3px solid #287bff;background:#f8fbff;color:#172b4d}.print-help{font-size:12px;color:var(--muted);margin-bottom:22px}
.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-bottom:24px}.metric{border:1px solid var(--line);border-radius:16px;padding:22px;min-height:120px}.metric span{display:block;font-size:13px}.metric strong{display:block;margin-top:14px;font-size:30px;line-height:1.2}.metric.danger strong{color:#b91c1c}.metric.warning strong{color:#855400}.metric.good strong{color:#166348}
.section{border:1px solid var(--line);border-radius:16px;padding:26px;margin:0 0 20px}.section-head{margin-bottom:20px}.section-note{font-size:12px;color:var(--muted);margin-top:8px}.case-strip{display:block}.case-strip>div{display:grid;grid-template-columns:30% minmax(0,1fr);gap:12px;padding:13px 10px;border-bottom:1px solid var(--line)}.case-strip>div:last-child{border:0}.case-strip small{font-size:13px;font-weight:600}.case-strip strong{font-size:15px;font-weight:400;overflow-wrap:anywhere}
.executive-grid{display:block}.assessment>p:first-of-type{border-left:4px solid var(--accent);border-radius:10px;padding:14px 18px;margin:0}.assessment h3{display:none}.assessment .caveat{margin:16px 0}.priority-box{margin-top:24px}.triage-item{padding:14px 0;border-top:1px solid var(--line);display:grid;grid-template-columns:80px minmax(0,1fr);gap:12px}.triage-item strong{display:block;font-size:14px}.triage-item a{display:block;margin-top:5px;font-size:12px;color:#245ea8}.triage-item p{margin:5px 0 0;font-size:13px}.decision{border:1px solid var(--line);border-radius:12px;padding:16px;margin:18px 0}.decision-head{display:flex;justify-content:space-between;gap:12px}.decision-kicker{font-size:12px;font-weight:600}.lead{font-weight:700;margin:8px 0}.action,.meta{font-size:13px}.meta{margin-top:8px;color:var(--muted)}.caveat{font-size:12px;color:var(--muted)}
.pill{display:inline-block;font-size:10px;font-weight:700;border:1px solid var(--line);border-radius:6px;padding:3px 7px;white-space:nowrap}.pill.danger{color:#b91c1c}.pill.warning{color:#855400}.pill.good{color:#166348}.pill.neutral{color:#334155}
.finding-group{margin-bottom:22px;padding-bottom:18px;border-bottom:1px solid var(--line)}.finding-group:last-child{margin:0;padding:0;border:0}.group-intro{margin-bottom:10px}.group-evidence{display:grid;grid-template-columns:50px minmax(0,1fr);gap:10px;padding:10px 0;border-top:1px solid var(--line)}.group-evidence .evidence{font-size:13px}.group-intro .action-text{margin:6px 0 12px}.report-button{font-weight:700}.summary-brand{display:flex;align-items:center;gap:12px}.summary-logo{width:50px;height:54px}.summary-wordmark{font-size:30px;font-weight:800;color:#14233d}.summary-wordmark span{color:#287bff}.summary-tagline{font-size:9px;letter-spacing:.15em;color:#47658a}.masthead{border-bottom:3px solid #287bff;margin-bottom:20px}.section-head h2{border-left:4px solid #287bff;padding-left:12px}.record-list{border:1px solid var(--line);border-radius:12px;padding:18px}.record{padding:0 0 20px;margin:0 0 20px;border-bottom:1px solid var(--line)}.record:last-child{padding-bottom:0;margin-bottom:0;border:0}.record-head{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:10px}.record-id{font:12px Consolas,monospace}.record-title{font-size:15px;font-weight:700}.record-meta{font-size:12px}.record-body{display:block}.record-cell+.record-cell{margin-top:12px}.cell-label{display:block;font-size:11px;font-weight:600;color:var(--muted);margin-bottom:5px}.evidence{display:block;color:var(--ink);font:12px/1.65 Consolas,"Cascadia Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere}.action-text{margin:0;font-size:13px}.empty{padding:18px;border:1px solid var(--line);border-radius:12px;font:12px Consolas,monospace}.table-wrap{width:100%;overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{padding:13px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13px;overflow-wrap:anywhere}tr:last-child td,tr:last-child th{border:0}thead th{font-size:11px;color:var(--muted)}td a{color:#245ea8}.chart{display:block;width:100%;height:auto;max-width:650px}.chart text{fill:#283244}.chips>.chart,.chips>.caveat{flex-basis:100%;width:100%}.incident-table th:first-child{width:20%}.incident-table th:nth-child(2){width:15%}.incident-table th:nth-child(4){width:9%}.incident-table thead th{white-space:nowrap}.severity-block{margin-top:14px}.severity-row{display:grid;grid-template-columns:90px 35px minmax(0,1fr);gap:12px;align-items:center;margin:9px 0}.severity-row small{font-size:11px}.track{height:6px;background:#e8eef8;border-radius:4px;overflow:hidden}.track i{display:block;height:100%;background:#397dcc}.assessment h3.severity-heading{display:block;margin-top:20px}.triage-item .pill{align-self:start;justify-self:start}.metric.danger strong,.metric.warning strong,.metric.good strong{font-size:22px}.telemetry-grid,.method-grid{display:block}.telemetry-card,.method-card{margin-top:20px}.telemetry-card:first-child,.method-card:first-child{margin-top:0}.method-card p{margin:0;font-size:13px}.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{font-size:12px;border:1px solid var(--line);border-radius:6px;padding:5px 9px}.footer{font-size:11px;text-align:center;margin:28px 0;color:var(--muted)}
@media(max-width:600px){.report{width:calc(100% - 24px);margin:12px auto}.masthead{padding:20px 12px 28px}.section{padding:18px}.case-strip>div{grid-template-columns:1fr;gap:4px}.metric{padding:18px;min-height:110px}.triage-item{grid-template-columns:1fr}.local-note{display:none}}
@media print{
@page{size:A4;margin:12mm}
body{font-size:12px;line-height:1.6;background:#fff}.report{width:100%;margin:0}.masthead{padding:24px 30px 32px;background:#fff!important}.brandline{margin-bottom:34px}.brand-name{font-size:26px}h1{font-size:32px}.subtitle{font-size:14px}.cover-meta{font-size:11px}.toolbar,.print-help{display:none}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px}.metric{padding:18px;min-height:90px}.metric strong{font-size:27px}.metric span{font-size:11px}.section{padding:20px;margin-bottom:16px;box-decoration-break:clone;break-inside:avoid}.section-head{break-after:avoid;margin-bottom:14px}.section-note{break-after:avoid}.incident-table td{padding:7px 6px;line-height:1.4}.incident-table td .pill{font-size:8px}.group-intro{break-inside:avoid;break-after:avoid}.group-evidence{break-inside:avoid;padding:8px 0}.group-evidence .evidence{font-size:11px}.finding-group{break-inside:auto}.group-evidence .record-id{font-size:10px}.masthead{border-bottom:3px solid #287bff}.metric strong{color:#245ea8!important}.metric.danger strong{color:#a62b38!important}h2{font-size:20px}h3{font-size:15px}.section-note{font-size:11px}.case-strip>div{padding:11px 8px}.case-strip small{font-size:11px}.case-strip strong{font-size:13px}.record-list{padding:16px}.record{break-inside:avoid;padding-bottom:16px;margin-bottom:16px}.record-title{font-size:13px}.record-meta{font-size:11px}.evidence{font-size:11px}.action-text,.method-card p{font-size:12px}.record-cell+.record-cell{margin-top:8px}.caveat{font-size:11px}.decision,.metric,.triage-item,.telemetry-card{break-inside:avoid}.table-wrap{overflow:visible}th,td{padding:10px 8px;font-size:11px}thead{display:table-header-group}tr{break-inside:avoid}.chart{break-inside:avoid;max-width:510px}#method{break-inside:avoid}.footer{position:static;font-size:9px;margin:24px 0 0}.content *, .case-strip *{color:#1f2937!important}.content .pill.danger{color:#b91c1c!important}.content .pill.warning{color:#855400!important}.content .pill.good{color:#166348!important}.content a{color:#245ea8!important}
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

_SUMMARY_OPENING_STYLE = """
.summary .masthead{padding:24px 26px 18px;margin-bottom:18px}
.summary-header{display:grid;grid-template-columns:150px minmax(0,1fr);align-items:center;gap:24px}
.summary .summary-header .brandline{margin:0}
.summary .summary-header .aegislog-report-logo{width:150px}
.summary .summary-header .brand-sub{font-size:9px;letter-spacing:.02em;margin-top:6px;white-space:nowrap}
.summary .summary-header h1{margin:0 0 8px;font-size:32px;line-height:1.15}
.summary-kicker{font-size:11px;font-weight:700;letter-spacing:.12em;color:#245ea8;margin:0 0 8px}
.summary-status{font-size:12px;color:#47658a;margin:0}
.summary-demo-label{display:inline-block;font-size:11px;font-weight:700;color:#245ea8;margin:8px 0 0}
.summary-meta{display:grid;grid-template-columns:1.2fr 1fr 1.2fr;gap:16px;margin-top:18px;padding-top:12px;border-top:1px solid #d3def0}
.summary-meta dt{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#47658a;margin:0 0 3px}
.summary-meta dd{font-size:13px;color:#172b4d;margin:0;overflow-wrap:anywhere}
.summary .summary-notes{border:1px solid #d3def0;border-left:3px solid #287bff;background:#f8fbff;border-radius:8px;padding:12px 16px;margin:0 0 18px;break-inside:avoid}
.summary .summary-notes h2{font-size:15px;margin:0 0 8px}
.summary .summary-notes .context-notice{border:0;background:none;padding:0;margin:6px 0;font-size:13px!important;line-height:1.5}
.summary .priority-lead{border-left:3px solid #287bff;padding-left:12px;margin:10px 0}
@media(max-width:600px){.summary-header{grid-template-columns:100px minmax(0,1fr);gap:14px}.summary .summary-header .aegislog-report-logo{width:100px}.summary .summary-header h1{font-size:25px}.summary-meta{grid-template-columns:1fr}.summary .summary-header .brand-sub{font-size:8px}}
@media print{
.summary .masthead{padding:10px 18px 14px;margin-bottom:14px}
.summary-header{grid-template-columns:110px minmax(0,1fr);gap:20px}
.summary .summary-header .aegislog-report-logo{width:110px}
.summary .summary-header h1{font-size:28px}
.summary .summary-header .brand-sub{font-size:7.5px}
.summary-kicker,.summary-status,.summary-demo-label{font-size:10px}
.summary-meta{grid-template-columns:1.2fr 1fr 1.2fr;gap:12px;margin:12px 0 0;padding-top:8px}
.summary-meta dd{font-size:11px}.summary-meta dt{font-size:9px}
.summary .summary-notes{padding:10px 12px;margin-bottom:14px;print-color-adjust:exact;-webkit-print-color-adjust:exact}
.summary .summary-notes .context-notice{font-size:11px!important;line-height:1.45;margin:5px 0}
.summary .priority-lead{margin:8px 0}
}
"""

_READING_LAYOUT_STYLE = """
/* Shared reading layout: results first, readable evidence, compact navigation. */
.report{width:min(1120px,calc(100% - 40px));margin:24px auto}
.report .masthead{padding:16px 0 18px;border-bottom:2px solid var(--accent);margin-bottom:16px}
.report .toolbar{padding:10px 0;border:0;border-bottom:1px solid var(--line);border-radius:0;gap:16px;margin-bottom:10px}
.report .print-help{margin:0 0 16px;font-size:12px;line-height:1.5}
.report .metrics{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:20px}
.report .metric{min-height:84px;padding:14px 16px;border-radius:8px;background:#f8fbff}
.report .metric strong{margin-top:6px;font-size:27px;line-height:1.25}
.report .metric.danger strong,.report .metric.warning strong,.report .metric.good strong{font-size:20px}
.report .section{border:0;border-top:1px solid var(--line);border-radius:0;padding:22px 0;margin-bottom:12px}
.report .section-head{margin-bottom:12px;gap:16px}
.report .section-head h2{border-left:3px solid var(--accent);padding-left:12px;font-size:22px}
.report .section-note{color:var(--muted);max-width:80ch}
.report .record-list{border:0;border-radius:0;padding:0}
.report .group-intro{padding:12px 16px;background:#f8fbff;border-left:3px solid var(--accent);border-radius:0 6px 6px 0}
.report .group-evidence{padding:14px 0;gap:14px}
.report .evidence{overflow-wrap:anywhere}
.report .executive-grid{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:28px}
.report .priority-box{align-self:start;background:#f8fbff;border:0;border-radius:8px;padding:18px}
.report .telemetry-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.report .telemetry-card{margin:0}
.report .summary-header{grid-template-columns:120px minmax(0,1fr);gap:22px}
.report .summary-header .aegislog-report-logo{width:120px}
.report .summary-header .brand-sub{white-space:nowrap;font-size:7.5px;line-height:1.4;letter-spacing:.01em;text-align:center}
.report .content .section-note{font-size:14px!important;line-height:1.5;max-width:none}
.report #executive p{margin-top:8px;margin-bottom:8px}
.report .summary-header h1{font-size:30px;margin-bottom:6px}
.report .summary-meta{margin:12px 0 0;padding-top:10px}
.report .summary-finding{padding:18px 0}
.report .summary-finding .record-head{gap:10px;margin-bottom:10px}
.report .summary-finding .evidence{border:0;border-left:2px solid #c5d8f3;border-radius:0;background:#f8fbff;padding:12px 14px;margin:10px 0}
.report .summary-finding .action-text{margin:8px 0}
.report .summary-notes{margin:12px 0 0}
.report .footer{border-top:1px solid var(--line);padding-top:14px;margin-top:22px}
.report:not(.summary) .masthead{display:grid;grid-template-columns:130px minmax(0,1fr);column-gap:22px;align-items:center}
.report:not(.summary) .masthead .brandline{grid-column:1;grid-row:1 / span 3;margin:0}
.report:not(.summary) .masthead .aegislog-report-logo{width:130px}
.report:not(.summary) .masthead h1{grid-column:2;font-size:30px;margin:0 0 6px}
.report:not(.summary) .masthead .subtitle,.report:not(.summary) .masthead .cover-meta{grid-column:2;margin:0;font-size:13px}
.report:not(.summary) .masthead .summary-demo-label{grid-column:2;font-size:11px;font-weight:700;color:#245ea8;margin:8px 0 0}
.report:not(.summary) .masthead .brand-sub{font-size:8px;letter-spacing:.02em;text-align:center}
.report:not(.summary) .masthead .context-notice{grid-column:1 / -1;margin:12px 0 0}
@media screen and (max-width:760px){
.report .metrics{grid-template-columns:repeat(2,minmax(0,1fr))}
.report .executive-grid,.report .telemetry-grid{grid-template-columns:1fr}
.report .summary-chart-grid{grid-template-columns:1fr}
.report.summary #incidents table{min-width:520px}
}
@media screen and (max-width:480px){
.report{width:calc(100% - 28px);margin:16px auto}
.report .summary-header,.report:not(.summary) .masthead{grid-template-columns:80px minmax(0,1fr);gap:14px}
.report .summary-header .aegislog-report-logo,.report:not(.summary) .masthead .aegislog-report-logo{width:80px}
.report .summary-header h1,.report:not(.summary) .masthead h1{font-size:24px}
.report .summary-header .brand-sub{white-space:normal;font-size:8px}
.report .metric{padding:12px;min-height:80px}
.report .summary-meta{grid-template-columns:1fr;gap:8px}
}
@media print{
.report{width:100%;margin:0}
.report .masthead{padding:8px 0 12px;margin-bottom:12px}
.report .toolbar,.report .print-help{display:none}
.report .metrics{grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:12px}
.report .metric{min-height:62px;padding:10px;border-radius:6px}
.report .metric strong{font-size:22px;margin-top:5px}
.report .metric.danger strong,.report .metric.warning strong,.report .metric.good strong{font-size:16px}
.report .section{padding:14px 0;margin-bottom:10px;break-inside:auto}
.report .section-head{break-after:avoid;margin-bottom:10px}
.report:not(.summary) #findings{page-break-before:always}
.report #source{break-inside:avoid}
.report .section-head h2{font-size:19px}
.report .content .section-note{font-size:12px!important}
.report .summary-header{grid-template-columns:110px minmax(0,1fr)}
.report .summary-header .aegislog-report-logo{width:110px}
.report .summary-header h1{font-size:26px}
.report .summary-header .brand-sub{font-size:7px}
.report .summary-chart-grid,.report .executive-grid{gap:18px}
.report .summary-finding{break-inside:avoid;padding:12px 0}
.report .summary-finding .evidence{padding:6px 10px;margin:6px 0}
.report .summary-finding .action-text{margin:6px 0}
.report .summary-notes{break-inside:auto}
.report .priority-box{padding:12px}
.report .group-intro{break-inside:avoid;break-after:avoid;padding:10px 12px}
.report .group-evidence{break-inside:avoid}
.report:not(.summary) .masthead{grid-template-columns:110px minmax(0,1fr)}
.report:not(.summary) .masthead .aegislog-report-logo{width:110px}
.report:not(.summary) .masthead h1{font-size:26px}
}
"""

_EDITORIAL_STYLE = """
.report.summary #executive{border:0;border-left:4px solid var(--accent);background:#f4f8ff;padding:18px 22px;margin-bottom:24px}
.report.summary #executive h2{border:0;padding:0;font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#245ea8}
.report.summary .assessment p{font-size:19px!important;line-height:1.45;font-weight:600;max-width:72ch}
.report.summary .priority-lead{border:0;padding:0;font-size:14px!important;color:#47658a}
.report.summary #executive .caveat{font-size:12px!important;margin-bottom:0}
.report.summary .summary-finding{display:grid;grid-template-columns:54px minmax(0,1fr);gap:18px;padding:22px 0;border-bottom:1px solid var(--line)}
.finding-index{font:12px/1.5 Consolas,monospace;color:#47658a;padding-top:5px}
.report.summary .finding-content .record-head strong{font-size:20px!important;line-height:1.4}
.report.summary .finding-content .record-meta{flex-basis:100%;font-size:12px!important;color:#596375}
.report.summary .finding-content .cell-label{margin-top:14px;font-size:11px!important;letter-spacing:.04em;text-transform:uppercase}
.report.summary .finding-content .evidence{font-size:14px!important;line-height:1.6;background:#f6f8fc;border:0;padding:14px 16px;margin:6px 0 14px}
.report.summary .finding-content .action-text{font-size:16px!important;line-height:1.6}
.report.summary #incidents,.report.summary #activity{padding-top:18px}
.report.summary #incidents .section-head h2,.report.summary #activity .section-head h2,.report.summary #scope .section-head h2{font-size:19px}
.report.summary .summary-notes{background:none;border:0;border-top:1px solid var(--line);padding:18px 0;margin:0}
.report.summary .summary-notes .context-notice{font-size:12px!important;color:#596375}
.coverage-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;margin:0 0 16px}
.coverage-grid dt{font-size:11px;color:#596375;margin-bottom:4px}
.coverage-grid dd{font-size:15px;margin:0;font-weight:600;overflow-wrap:anywhere}
.report.summary #scope p{font-size:13px!important;line-height:1.55;color:#596375}
.coverage-warning{border-left:3px solid #a62b38;padding-left:12px}
@media screen and (max-width:760px){.coverage-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media screen and (max-width:480px){.report.summary .summary-finding{grid-template-columns:1fr;gap:6px}.report.summary .finding-content .record-head strong{font-size:19px!important}}
@media print{
.report.summary #executive{padding:12px 16px;margin-bottom:14px;print-color-adjust:exact;-webkit-print-color-adjust:exact}
.report.summary .assessment p{font-size:15px!important}
.report.summary .priority-lead{font-size:11px!important}
.report.summary #executive .caveat{font-size:10px!important}
.report.summary .summary-finding{grid-template-columns:42px minmax(0,1fr);gap:12px;padding:14px 0;break-inside:avoid}
.report.summary .finding-content .record-head strong{font-size:16px!important}
.report.summary .finding-content .record-meta{font-size:10px!important}
.report.summary .finding-content .evidence{font-size:12px!important;line-height:1.5;padding:8px 10px;margin:4px 0 8px}
.report.summary .finding-content .action-text{font-size:13px!important;line-height:1.5}
.report.summary .finding-content .cell-label{font-size:9px!important;margin-top:8px}
.report.summary .summary-notes{padding:12px 0}
.report.summary .summary-notes .context-notice,.report.summary #scope p{font-size:10px!important;line-height:1.5}
.coverage-grid{gap:12px}.coverage-grid dd{font-size:11px}.coverage-grid dt{font-size:9px}
}
"""


_SUMMARY_STYLE = '.summary .section{padding:22px}.summary-finding{padding:14px 0;border-bottom:1px solid var(--line)}.summary-finding:last-child{border:0}.summary-finding .evidence{margin:6px 0 9px}.evidence-link{font-size:12px;color:#245ea8}.summary .section-note{margin-bottom:14px}.summary-chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.summary-chart-grid h3{font-size:15px}.summary .metric{min-height:100px;padding:18px}.summary .assessment h3{display:block}.summary .assessment p{border:0;padding:0}.summary .chart{max-width:510px}.summary .scope{font-size:12px}.context-notice{font-size:13px;line-height:1.5;padding:10px 12px;border-left:3px solid #287bff;background:#f8fbff;color:#172b4d}.summary ul{margin:8px 0;padding-left:18px}.summary h1{font-size:34px;color:#14233d}.summary .metric{background:#f8fbff;border-color:#c5d8f3}.summary .metric strong{color:#245ea8}.summary .metric.danger{background:#fff6f6;border-color:#f2cdcf}.summary .metric.danger strong{color:#a62b38}.summary .metric.warning strong{color:#855400}.summary .metric.good strong{color:#166348}.summary .section-head h2{border-left:4px solid #287bff;padding-left:12px}.summary .summary-service-chart{display:block;width:100%;height:auto}.summary .summary-service-chart text{fill:#18345b;font-family:"Segoe UI",Arial,sans-serif}.summary-finding .evidence{border:1px solid #d3def0;border-radius:6px;background:#f8fbff;padding:8px 10px}.summary .pill.danger{background:#fff1f2;border-color:#eab9c0}.summary .pill.warning{background:#fff7e6;border-color:#e8d2a3}\n@media(max-width:600px){.summary-chart-grid{grid-template-columns:1fr}}\n@media print{.summary .metrics{grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.summary .metric{min-height:58px;padding:10px}.summary .metric strong{font-size:21px;line-height:1.3;overflow-wrap:normal}.summary h1{font-size:28px}.summary .section{padding:16px;margin-bottom:14px}.summary-finding{break-inside:avoid;padding:6px 0}.summary-finding .evidence{padding:4px 8px;margin:4px 0 6px}.summary .section-note,.summary .scope{font-size:10px}.summary #incidents{break-inside:avoid}.summary .summary-chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.summary-chart-grid{break-inside:avoid}.summary #executive{break-inside:avoid}.summary .severity-row{grid-template-columns:65px 22px 1fr;gap:6px}.summary .chart text{font-size:12px}.summary .metric,.summary .pill,.summary-finding .evidence{print-color-adjust:exact;-webkit-print-color-adjust:exact}.summary .metric strong{color:#245ea8!important}.summary .metric.danger strong{color:#a62b38!important}.summary .metric.warning strong{color:#855400!important}.summary .metric.good strong{color:#166348!important}}\n'


def report_stylesheet(*, summary=False):
    """One shared presentation entry point; summary component rules precede document skin."""
    from .report_design import REPORT_DESIGN_STYLE
    from .report_reference import REFERENCE_STYLE
    from .report_editorial import EDITORIAL_BRIEF_STYLE
    components = _REPORT_STYLE + (_SUMMARY_STYLE + _SUMMARY_OPENING_STYLE if summary else '')
    stylesheet = components + _BODY_TEXT_STYLE + _READING_LAYOUT_STYLE + _EDITORIAL_STYLE + REPORT_DESIGN_STYLE + REFERENCE_STYLE
    for old, new in {'#287bff': '#43aebb', '#397dcc': '#299aa7', '#eaf2ff': '#eaf8fa', '#f8fbff': '#f1fafb', '#245ea8': '#126773', '#d3def0': '#c7e3e7'}.items():
        stylesheet = stylesheet.replace(old, new)
    return stylesheet + EDITORIAL_BRIEF_STYLE
