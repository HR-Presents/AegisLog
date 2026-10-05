"""Local synthetic streaming benchmark; no remote telemetry or user logs."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import statistics
import tempfile
import time
import tracemalloc
from pathlib import Path

from aegislog import __version__
from aegislog.streaming import analyze_stream


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def benchmark(records=100_000, repeats=3, max_findings=100):
    if not 1 <= records <= 1_000_000 or not 1 <= repeats <= 5 or not 1 <= max_findings <= 5000:
        raise ValueError('Records must be 1..1000000, repeats 1..5 and retained findings 1..5000.')
    samples = []
    with tempfile.TemporaryDirectory(prefix='aegislog-benchmark-') as temporary:
        path = Path(temporary) / 'synthetic.log'
        with path.open('w', encoding='utf-8', newline='\n') as stream:
            for index in range(records):
                level = 'ERROR synthetic timeout' if index % 100 == 0 else 'INFO synthetic normal event'
                stream.write(f'2026-01-01T00:00:00Z benchmark[1]: {level} {index}\n')
        original_digest = digest(path)
        size = path.stat().st_size
        for _ in range(repeats):
            gc.collect()
            tracemalloc.start()
            try:
                start = time.perf_counter()
                summary = analyze_stream(path, max_findings=max_findings)
                elapsed = time.perf_counter() - start
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            if summary.lines != records or len(summary.findings) > max_findings:
                raise RuntimeError('Streaming processing or retention invariant failed.')
            if digest(path) != original_digest:
                raise RuntimeError('Synthetic input changed during read-only analysis.')
            samples.append(dict(seconds=round(elapsed, 6), records_per_second=round(records / elapsed, 2),
                                peak_python_allocated_bytes=peak, processed_records=summary.lines,
                                retained_findings=len(summary.findings), omitted_findings=summary.dropped_findings,
                                truncated_lines=summary.truncated_lines, source_unchanged=True))
    return dict(schema='aegislog-streaming-benchmark-1', tool_version=__version__,
                environment=dict(python=platform.python_version(), os_family=platform.system(), architecture=platform.machine()),
                workload=dict(kind='synthetic', records=records, bytes=size, error_every_records=100,
                              retained_finding_limit=max_findings, repeats=repeats, input_sha256=original_digest),
                samples=samples, median_records_per_second=statistics.median(s['records_per_second'] for s in samples),
                limitations='Streaming engine only; excludes HTML rendering, native collection and live polling. '
                'tracemalloc adds overhead and measures Python allocations, not whole-process RSS. '
                'Synthetic local timings are environment-specific, not production performance or detection-accuracy claims.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=int, default=100_000)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--max-findings', type=int, default=100)
    args = parser.parse_args()
    try:
        report = benchmark(args.records, args.repeats, args.max_findings)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
