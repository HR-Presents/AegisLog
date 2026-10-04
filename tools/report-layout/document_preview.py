"""Generate the approved layout fixture through the production renderer."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from aegislog.dashboard import analyze_dashboard
from aegislog.reporting import build_html_report, _finding_groups


def build_document(data):
    return build_html_report(data).replace('<section class="summary">', '<p class="sample-notice"><strong>SYNTHETIC DEMO DATA</strong> — Training fixture; these results do not describe your computer.</p><section class="summary">', 1)


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
