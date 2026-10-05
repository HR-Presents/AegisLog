import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('streaming_benchmark', Path(__file__).resolve().parents[1] / 'tools/benchmark_streaming.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_benchmark_checks_processing_retention_and_source_integrity():
    report = module.benchmark(records=201, repeats=1, max_findings=1)
    sample = report['samples'][0]
    assert sample['processed_records'] == 201
    assert sample['retained_findings'] == 1
    assert sample['omitted_findings'] == 2
    assert sample['source_unchanged']
    assert sample['peak_python_allocated_bytes'] > 0
    assert 'not whole-process RSS' in report['limitations']
    assert report['workload']['kind'] == 'synthetic'


@pytest.mark.parametrize('records,repeats,limit', [(0, 1, 1), (1000001, 1, 1), (1, 0, 1),
                                                 (1, 6, 1), (1, 1, 0), (1, 1, 5001)])
def test_benchmark_rejects_unbounded_or_invalid_arguments(records, repeats, limit):
    with pytest.raises(ValueError):
        module.benchmark(records, repeats, limit)
