"""Optional browser interface served only on authenticated IPv4 loopback."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import hmac
import json
import re
import secrets
import tempfile
import threading
from urllib.parse import parse_qs, urlparse
import webbrowser

from .native_collectors import CollectorError
from .product import check_computer, discover_sources, investigate_path
from .sanitize import redact_sensitive
from .reporting import _summary_brand

PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AegisLog Command Center</title>
<style>:root{font-size:18px;color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f3f7fd;color:#172b4d;font-family:system-ui,sans-serif;line-height:1.6}header{background:white;color:#172b4d;padding:24px;border-bottom:3px solid #287bff}.summary-brand{display:flex;align-items:center;gap:12px}.summary-logo{width:54px;height:58px}.summary-wordmark{font-size:32px;font-weight:800}.summary-wordmark span{color:#287bff}.summary-tagline{font-size:12px;color:#415675}.brand-sub{font-size:12px;color:#415675;margin-top:8px}progress{width:100%;height:18px;accent-color:#1258b5}main{max-width:1100px;margin:auto;padding:24px}h1{margin:0}h2{font-size:1.4rem}button,input,select{font:inherit;padding:10px;border:1px solid #7893b7;border-radius:8px}button{background:#1258b5;color:white;cursor:pointer}button:disabled{opacity:.6}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #e68a00;outline-offset:3px}section,article{background:white;border:1px solid #c4d6ef;border-radius:12px;padding:22px;margin:18px 0}label{display:inline-block;margin:8px 12px 8px 0}input{max-width:100%;width:440px}a{color:#1258b5}.muted{color:#415675}.badge{font-weight:bold}.HIGH,.CRITICAL{color:#a11b28}.MEDIUM{color:#805000}code,pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.9rem}.controls{display:flex;gap:12px;flex-wrap:wrap}main>.controls{position:sticky;top:0;z-index:2;background:#f3f7fd;padding:12px 0}.analyst{display:none}body.advanced .analyst{display:block}#status{white-space:pre-wrap}summary{cursor:pointer;font-weight:bold}@media(max-width:600px){main{padding:12px}section,article{padding:14px}input{width:100%}}@media print{header button,.controls,#setup{display:none}body{background:white}article{break-inside:avoid}}</style>
<header><h1>◈ AEGISLOG</h1><div>Local log investigation · Made by HR-Presents</div></header><main>
<p>AegisLog reads logs, explains findings and creates local reports. Choose a source or file below. Findings require validation; this tool does not change system settings.</p>
<div class="controls"><button id="back">Back to setup</button><button id="mode" aria-pressed="false">Switch to analyst view</button><label>Text size <select id="font"><option value="18">Standard</option><option value="21">Large</option><option value="24">Extra large</option></select></label><button id="quit">Quit AegisLog</button></div>
<div id="status" role="status" aria-live="polite">Ready. Sources are probed only when you choose Discover sources.</div>
<section id="setup"><h2>Check this computer</h2><p>Discover accessible native sources, then choose one and a bounded time window.</p><button id="discover">Discover sources</button><div id="sources"></div><label>Source <select id="source" aria-label="Native source"><option value="">Discover sources first</option></select></label><label>Window <select id="window"><option value="60">Last hour</option><option value="1440" selected>Last 24 hours</option><option value="10080">Last 7 days</option></select></label><label>Maximum events <select id="limit"><option>300</option><option>1000</option><option>2000</option></select></label><button id="check">Analyze selected source</button>
<h2>Investigate a log file</h2><label>Full local path <input id="path" placeholder="C:\Users\you\Downloads\server.log"></label><button id="analyze">Analyze file</button><p class="muted">UTF-8 text up to 100 MB. For folder discovery and live monitoring, use the terminal: aegislog start → F or 02/03/05.</p></section>
<section id="results" hidden><h2>Investigation overview</h2><p id="metrics"></p><p id="scope"></p><p id="coverage"></p><div id="severities" aria-label="Finding severity distribution"></div><div class="controls" id="downloads"></div><div class="controls"><label>Search findings <input id="filter" placeholder="Title or evidence"></label><label>Severity <select id="severityFilter"><option value="">All severities</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option><option>INFO</option></select></label><label><input id="allFindings" type="checkbox" style="width:auto"> Show all matching findings</label></div><p id="shown" role="status"></p><div id="findings"></div><details class="analyst"><summary>Structured evidence and incidents</summary><pre id="raw"></pre></details></section>
<section><h2>Help &amp; feedback</h2><p>Security leads are different from operational failures. Severity describes a rule's priority; it is not a measured probability of compromise. No findings does not establish a clean system.</p><p><a href="https://github.com/HR-Presents/AegisLog-AI/blob/codex/report-print-quality/docs/GETTING_STARTED.md" target="_blank" rel="noreferrer">Getting started</a> · <a href="https://github.com/HR-Presents/AegisLog-AI/issues/new" target="_blank" rel="noreferrer">Report an issue</a></p><p class="muted">Nothing is uploaded automatically. JSON exports redact common credentials; review usernames, IP addresses and paths before sharing. External help links open only when clicked.</p></section></main>
<script>
const token=location.hash.slice(1)||sessionStorage.getItem('aegis-session')||'';if(token)sessionStorage.setItem('aegis-session',token);history.replaceState(null,'',location.pathname);const $=id=>document.getElementById(id);let sources=[];let closed=false;let current=null;const rank={CRITICAL:5,HIGH:4,MEDIUM:3,LOW:2,INFO:1};
async function api(action,data={}){const r=await fetch('/api/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-Aegis-Token':token},body:JSON.stringify(data)});const payload=await r.json();if(!r.ok)throw Error(payload.error||'Request failed');return payload;}
async function run(button,fn){button.disabled=true;$('status').textContent='Working locally…';try{await fn();}catch(e){$('status').textContent=e.message;}finally{button.disabled=closed;}}
$('discover').onclick=()=>run($('discover'),async()=>{sources=await api('sources');$('sources').replaceChildren();$('source').replaceChildren();sources.forEach((row,i)=>{const p=document.createElement('p');p.textContent=row.label+' — '+row.status+': '+row.description+' '+row.detail;$('sources').append(p);if(row.status==='readable'){const o=document.createElement('option');o.value=i;o.textContent=row.label;$('source').append(o);}});$('source').dispatchEvent(new Event('change'));$('status').textContent=sources.length?'Source discovery complete.':'No native collector for this operating system. Choose a file.';});
function draw(result){const query=$('filter').value.toLowerCase();const severity=$('severityFilter').value;const matches=result.findings.filter(item=>(!severity||item.severity===severity)&&(!query||(item.title+' '+item.evidence).toLowerCase().includes(query))).sort((a,b)=>(rank[b.severity]||0)-(rank[a.severity]||0));const shown=$('allFindings').checked?matches:matches.slice(0,6);$('shown').textContent='Showing '+shown.length+' of '+matches.length+' matching findings; '+result.findings.length+' total. Full evidence is retained in the reports.';$('findings').replaceChildren();shown.forEach(item=>{const article=document.createElement('article');const heading=document.createElement('h3');heading.textContent=item.severity+' · '+item.title;heading.className=item.severity;article.append(heading);const e=item.explanation;for(const [label,text] of [['Type',e.classification],['Why it matters',e.impact],['Other possible explanation',e.alternative],['Next step',e.next_step]]){const p=document.createElement('p');const strong=document.createElement('strong');strong.textContent=label+': ';p.append(strong,document.createTextNode(text));article.append(p);}const d=document.createElement('details');const s=document.createElement('summary');s.textContent='View matching evidence';const pre=document.createElement('pre');pre.textContent=item.evidence;d.append(s,pre);article.append(d);const p=document.createElement('p');p.className='analyst';p.textContent=e.reason+' '+e.confidence;article.append(p);$('findings').append(article);});if(!matches.length)$('findings').textContent=result.findings.length?'No findings match these filters.':'No rules matched. Review coverage and source context before drawing conclusions.';}
function display(result){$('results').hidden=false;$('metrics').textContent=result.events+' events · '+result.findings.length+' findings · '+result.incidents.length+' incident groups';$('severities').replaceChildren();Object.entries(result.severities).sort((a,b)=>(rank[b[0]]||0)-(rank[a[0]]||0)).forEach(([label,count])=>{const p=document.createElement('p');p.textContent=label+': '+count+' findings';const bar=document.createElement('progress');bar.max=Math.max(1,result.findings.length);bar.value=count;bar.setAttribute('aria-label',label+' findings');p.append(bar);$('severities').append(p);});$('scope').textContent=result.coverage.scope;$('coverage').textContent=result.coverage.retention+' Retained formats: '+JSON.stringify(result.coverage.retained_formats)+'. Generic fallback: '+result.coverage.generic_retained+'. '+result.coverage.caveat;$('downloads').replaceChildren();Object.entries(result.downloads).forEach(([label,url])=>{const a=document.createElement('a');a.textContent=label;a.href=url+'?token='+encodeURIComponent(token);a.target='_blank';a.rel='noopener';if(label==='Redacted JSON')a.download='aegislog-evidence.json';$('downloads').append(a);});current=result;draw(result);$('raw').textContent=JSON.stringify(result,null,2);$('status').textContent='Analysis complete. Sources unchanged. Reports saved locally.';$('results').scrollIntoView({behavior:'smooth'});}
$('check').onclick=()=>run($('check'),async()=>{const row=sources[Number($('source').value)];if($('source').value===''||!row||row.status!=='readable')throw Error('Discover and choose a readable source first.');display(row.source==='file'?await api('analyze',{path:row.path}):await api('check',{source:row.source,channel:row.channel,minutes:Number($('window').value),limit:Number($('limit').value)}));});
$('source').onchange=()=>{const row=sources[Number($('source').value)];$('window').disabled=$('limit').disabled=!!row&&row.source==='file';};
$('analyze').onclick=()=>run($('analyze'),async()=>display(await api('analyze',{path:$('path').value})));
for(const id of ['filter','severityFilter','allFindings'])$(id).addEventListener('input',()=>{if(current)draw(current);});
$('font').onchange=()=>document.documentElement.style.fontSize=$('font').value+'px';$('mode').onclick=()=>{const advanced=document.body.classList.toggle('advanced');$('mode').setAttribute('aria-pressed',String(advanced));$('mode').textContent=advanced?'Switch to beginner view':'Switch to analyst view';};$('back').onclick=()=>{$('results').hidden=true;$('setup').scrollIntoView();$('discover').focus();};$('quit').onclick=()=>run($('quit'),async()=>{await api('quit');closed=true;sessionStorage.removeItem('aegis-session');$('status').textContent='AegisLog stopped. Return to your terminal; you can close this tab.';document.querySelectorAll('button').forEach(b=>b.disabled=true);});
</script></html>'''


PAGE = PAGE.replace('<h1>◈ AEGISLOG</h1>', _summary_brand().replace('<div class="summary-wordmark">AEGIS<span>LOG</span></div>', '<h1 class="summary-wordmark">AEGIS<span>LOG</span></h1>'))


def create_server(output_root, token=None):
    token = token or secrets.token_urlsafe(32)
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    reports = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # Do not log private paths, tokens or evidence.

        def send(self, status, content, kind='application/json'):
            body = content.encode('utf-8') if isinstance(content, str) else content
            self.send_response(status)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            parsed = urlparse(self.path)
            if not self.valid_host():
                self.send(403, '{}')
            elif parsed.path == '/':
                self.send(200, PAGE, 'text/html')
            elif parsed.path.startswith('/report/'):
                supplied = parse_qs(parsed.query).get('token', [''])[0]
                path = reports.get(parsed.path)
                if not hmac.compare_digest(supplied, token) or path is None:
                    self.send(403, '{}')
                else:
                    try:
                        content = path.read_bytes()
                        if path.suffix == '.html':
                            html = content.decode('utf-8')
                            for other in reports.values():
                                if other.parent == path.parent and other.suffix == '.html':
                                    html = re.sub(r'href="' + re.escape(other.name) + r'(?=[#"])', lambda _match: f'href="{other.name}?token={token}', html)
                            content = html.encode('utf-8')
                        self.send(200, content, 'application/json' if path.suffix == '.json' else 'text/html')
                    except OSError:
                        self.send(404, '{}')
            else:
                self.send(404, '{}')

        def do_POST(self):
            origin = self.headers.get('Origin')
            expected = f'http://127.0.0.1:{self.server.server_port}'
            if not self.valid_host() or (origin and origin != expected) or not hmac.compare_digest(self.headers.get('X-Aegis-Token', ''), token):
                self.send(403, json.dumps({'error': 'Invalid local session.'}))
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384:
                    raise ValueError('Request is too large or empty.')
                self.connection.settimeout(10)
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict):
                    raise ValueError('Expected an object.')
                if self.path == '/api/quit':
                    self.send(200, '{}')
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                if self.path == '/api/sources':
                    result = discover_sources()
                elif self.path in {'/api/analyze', '/api/check'}:
                    output = Path(tempfile.mkdtemp(prefix='case-', dir=root))
                    if self.path == '/api/analyze':
                        result = investigate_path(request.get('path', ''), output)
                    else:
                        result = check_computer(request.get('source'), request.get('channel', ''), int(request.get('minutes', 1440)), int(request.get('limit', 300)), output)
                    report_paths = {field: Path(result[field]) for field in ('summary', 'evidence_report', 'export')}
                    result = json.loads(redact_sensitive(json.dumps(result, default=str)))
                    result['downloads'] = {}
                    for label, field in [('Summary report', 'summary'), ('Full evidence report', 'evidence_report'), ('Redacted JSON', 'export')]:
                        result.pop(field)
                        path = report_paths[field]
                        # Stable relative routes preserve summary↔appendix links.
                        route = f'/report/{output.name}/{path.name}'
                        reports[route] = path
                        result['downloads'][label] = route
                else:
                    self.send(404, '{}')
                    return
                self.send(200, json.dumps(result, default=str))
            except (ValueError, TypeError, OSError, CollectorError) as error:
                self.send(400, json.dumps({'error': redact_sensitive(str(error))[:500]}))

    server = HTTPServer(('127.0.0.1', 0), Handler)
    server.session_token = token
    return server


def desktop():
    """Open the optional local graphical dashboard; Ctrl+C or Quit returns to the shell."""
    server = create_server(Path('aegislog-reports') / 'desktop')
    url = f'http://127.0.0.1:{server.server_port}/#{server.session_token}'
    print('AegisLog local dashboard. Ctrl+C or Quit stops it and returns to your shell.')
    print(url)
    webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
