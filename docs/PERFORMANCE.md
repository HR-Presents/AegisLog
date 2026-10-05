# Local performance measurement

Run the standard-library streaming benchmark from a source checkout with AegisLog installed:

```text
python tools/benchmark_streaming.py --records 100000 --repeats 3 --max-findings 100
```

The tool generates its own temporary synthetic input and removes it afterward. No user logs, host names, paths, network services or paid tools are needed. JSON output includes workload bytes, input hash, Python/OS family/architecture, each run's duration and throughput, median throughput, peak tracked Python allocation, retained/omitted findings and source-integrity checks.

The workload has one operational-error line per 100 records; other records are informational. It exercises streaming ingestion and bounded non-authentication finding retention. It does not exercise diverse authentication correlation, structured adapters, report generation, native collectors or live polling. Existing context and live-state tests cover different invariants; benchmark output does not replace them.

`tracemalloc` adds measurement overhead. Its peak tracks Python allocations during analysis and is not whole-process resident memory. Temporary input generation and hashing are outside the timed section. Keep hardware, runtime, workload and limits consistent when comparing measurements. Use all samples rather than selecting only the fastest run. OS caches can affect repeated reads. No timing threshold is imposed in CI because shared-runner speeds vary.

The command bounds record count to one million, repeats to five and retained findings to 5,000. Its normal defaults are 100,000 records, three repeats and 100 retained findings. A failed processed-count, retention or read-only hash invariant raises an error. Synthetic timings are local engineering measurements, not production throughput guarantees or detection-effectiveness evidence.
