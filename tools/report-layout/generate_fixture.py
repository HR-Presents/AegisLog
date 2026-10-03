from pathlib import Path
from aegislog.commands_v12 import _DEMO_LOG
from aegislog.dashboard import analyze_dashboard
from aegislog.reporting import write_html_report
from aegislog.folder_scan import write_batch
root=Path('report-layout-qa');root.mkdir(exist_ok=True)
rows=[]
for i in range(145):
 n=65 if i<14 else 28 if i==14 else 0
 rows.append(dict(source=f'Documents/Virtual Machines/Windows lab training folder/source-{i:03d}-application-observations-and-supporting-evidence.log',status='complete',lines=3000+i,records=3000+i,recognized=0,coverage='Unrecognized format / generic fallback only',findings=n,report=f'{i:03d}/report.html',groups=[dict(severity='MEDIUM',category='error',title='Operational error detected',recommendation='Review surrounding evidence.',count=n)] if n else []))
rows[15]['findings']=1;rows[15]['groups']=[dict(severity='MEDIUM',category='network',title='Firewall blocked inbound activity',recommendation='Review the source and destination.',count=1)]
for i in range(16):
 rows.append(dict(source=f'Documents/Other course folders/duplicate-copy-{i:03d}.log',status='duplicate',duplicate_of=rows[i]['source'],report=rows[i]['report']))
print(write_batch(root,Path('C:/Users/Demo/Documents'),rows,scan_mode='Other text/configuration included'))

source=root/'demo_auth.log';source.write_text(_DEMO_LOG)
write_html_report(analyze_dashboard(source),root)
