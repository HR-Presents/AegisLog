"""Repeatable synthetic static-investigation measurements; no host log access."""
import argparse
import json
import platform
import tempfile
import time
import tracemalloc
from pathlib import Path

from aegislog import __version__
from aegislog.dashboard import analyze_dashboard
from aegislog.triage import finding_groups, windows_session_context


def measure(records):
    if not 1 <= records <= 1_000_000:
        raise ValueError('Choose 1–1,000,000 synthetic records.')
    with tempfile.TemporaryDirectory(prefix='aegislog-benchmark-') as directory:
        source = Path(directory) / 'synthetic.log'
        with source.open('w', encoding='utf-8') as stream:
            for index in range(records):
                message = 'ERROR timeout' if index % 100 == 0 else 'INFO request completed'
                stream.write(f'2026-10-04T08:00:00Z benchmark[1]: {message}\n')
        tracemalloc.start()
        started = time.perf_counter()
        try:
            data = analyze_dashboard(source)
            groups = finding_groups(data.findings)
            links = windows_session_context(data.raw_lines)
            elapsed = time.perf_counter()-started
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
    assert data.records == records
    assert len(data.raw_lines) <= 10000
    return dict(schema='aegislog-investigation-benchmark-1', synthetic=True, tool_version=__version__,
                python=platform.python_version(), os=platform.system(), records=records,
                retained_records=len(data.raw_lines), findings=len(data.findings), dropped_findings=data.dropped_findings,
                triage_groups=len(groups), windows_context_links=len(links), elapsed_seconds=round(elapsed, 3),
                records_per_second=round(records/elapsed), peak_python_bytes=peak,
                note='One synthetic run; Python allocations exclude process/native RSS. Not a performance SLA or real-world accuracy evaluation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=int, default=10000)
    args = parser.parse_args()
    print(json.dumps(measure(args.records), indent=2))
