"""Synthetic regression for native scope and three-group PDF pagination."""
from pathlib import Path
from unittest.mock import patch

from aegislog.product import check_computer

root = Path('report-layout-qa/native-print')
lines = [f'2026-10-05T10:{i % 60:02d}:00Z Netwtw06[1]: INFO Synthetic routine activity\n' for i in range(296)]
lines += [
    '2026-10-04T17:59:50Z Service Control Manager[7011]: ERROR A timeout (30000 milliseconds) was reached while waiting for a transaction response from the TrainingBackup service.\n',
    '2026-10-04T20:37:29Z Service Control Manager[7011]: ERROR A timeout (30000 milliseconds) was reached while waiting for a transaction response from the TrainingBackup service.\n',
    '2026-10-04T20:36:58Z Microsoft-Windows-DistributedCOM[10010]: ERROR The server {00000000-0000-0000-0000-000000000001} did not register with DCOM within the required timeout.\n',
    '2026-10-05T06:58:23Z Volsnap[36]: ERROR The shadow copies of volume C: were aborted because the shadow copy storage could not grow due to a user imposed limit.\n',
]
with patch('aegislog.product.collect', return_value=lines):
    result = check_computer('windows', 'System', 1440, 300, root)
assert len(result['findings']) == 4
assert len(result['triage_groups']) == 3
print(result['summary'])
