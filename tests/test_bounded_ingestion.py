from pathlib import Path
import tracemalloc

from aegislog.ingestion import iter_bounded_lines
from aegislog.dashboard import analyze_dashboard
from aegislog.streaming import analyze_stream
from aegislog.terminal_charts import minute_activity


def test_oversized_line_is_discarded_before_decoding(tmp_path: Path):
    path = tmp_path / 'long.log'
    with path.open('wb') as handle:
        for _ in range(128):
            handle.write(b'x' * 65536)
        handle.write(b'\nERROR timeout\n')
    tracemalloc.start()
    summary = analyze_stream(path, max_line_bytes=1024)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 1_000_000
    assert summary.lines == 2
    assert summary.truncated_lines == 1
    assert any(item.category == 'error' for item in summary.findings)


def test_bounded_lines_preserve_empty_crlf_and_eof(tmp_path: Path):
    path = tmp_path / 'lines.log'
    path.write_bytes(b'\r\nabc\r\nlast')
    assert [item.text for item in iter_bounded_lines(path, 16)] == ['', 'abc', 'last']


def test_dashboard_counts_all_lines_but_discloses_sampling(tmp_path: Path):
    path = tmp_path / 'sample.log'
    path.write_text('2026-10-02T10:00:00Z INFO api: healthy\n' * 100 + 'ERROR timeout\n')
    data = analyze_dashboard(path, max_retained_lines=5, max_retained_bytes=1024)
    assert data.lines == 101
    assert len(data.raw_lines) == 5
    assert data.sampled_lines == 96
    assert sum(data.services.values()) == 101
    assert any(item.category == 'error' for item in data.findings)
    assert '5/101' in data.retention_note


def test_minute_activity_normalizes_timezone_and_orders_out_of_order_input():
    values = minute_activity(['2026-10-02T12:02:00Z INFO api: x',
                             '2026-10-02T14:00:00+02:00 INFO api: x',
                             '2026-10-02T12:00:10Z INFO api: x'])
    assert values['2026-10-02 12:00'] == 2
    assert sorted(values) == ['2026-10-02 12:00', '2026-10-02 12:02']


def test_exact_byte_limit_does_not_truncate_crlf(tmp_path):
    path = tmp_path / 'exact.log'
    path.write_bytes(b'abcd\r\nnext')
    lines = list(iter_bounded_lines(path, 4))
    assert [line.text for line in lines] == ['abcd', 'next']
    assert not any(line.truncated for line in lines)


def test_structured_metadata_cannot_crash_service_counts(tmp_path):
    path = tmp_path / 'metadata.log'
    path.write_text('{"service":{"unexpected":"object"},"level":"info","message":"healthy"}\n')
    data = analyze_dashboard(path)
    assert data.lines == 1
    assert data.services == {'unknown': 1}


def test_large_identifiers_do_not_expand_retained_authentication_evidence():
    from aegislog.engine import AnalysisState
    state = AnalysisState()
    state.process('2026-10-02T10:00:00Z sshd: Failed password for ' + 'x' * 100_000 + ' from 203.0.113.1')
    event = state._auth['203.0.113.1'][0]
    assert len(event.account) <= 256
    assert len(event.evidence) <= 500
