import json

from aegislog.dashboard import analyze_dashboard


def analyze(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return analyze_dashboard(path)


def test_csv_header_and_multiline_record_counts(tmp_path):
    data = analyze(tmp_path, 'events.csv', 'timestamp,service,level,message\n2026-10-03T00:00:00Z,app,ERROR,"failure\nwith detail"\n')
    assert data.lines == 3 and data.records == 1 and data.recognized_records == 1
    assert len(data.findings) == 1


def test_json_array_counts_records_and_preserves_original_fields(tmp_path):
    data = analyze(tmp_path, 'events.json', json.dumps([{'timestamp':'2026-10-03T00:00:00Z','message':'ERROR timeout','extra':'evidence'}, {'message':'healthy'}], indent=2))
    assert data.lines > 2 and data.records == data.recognized_records == 2
    assert len(data.findings) == 1 and 'evidence' in data.raw_lines[0]


def test_unknown_schema_is_not_clean_claim(tmp_path):
    data = analyze(tmp_path, 'business.json', '[{"name":"sample","score":0.9}]')
    assert data.records == 1 and data.recognized_records == 0
    assert not data.findings and 'Unrecognized' in data.coverage_status
    assert 'does not establish a clean system' in data.coverage_note


def test_zeek_metadata_excluded_and_connections_not_attack(tmp_path):
    data = analyze(tmp_path, 'conn.log', '#separator \\x09\n#path\tconn\n#open\t2026\n#fields\tts\tid.orig_h\tid.resp_h\tconn_state\n1750000000\t10.0.0.1\t10.0.0.2\tS0\n#close\t2026\n')
    assert data.lines == 6 and data.records == data.recognized_records == 1
    assert not data.findings


def test_suricata_upstream_alert_and_flow(tmp_path):
    rows = [{'timestamp':'2026-10-03T00:00:00Z','event_type':'alert','src_ip':'10.0.0.1','alert':{'signature':'Test signature','severity':1}}, {'event_type':'flow','src_ip':'10.0.0.1','dest_ip':'10.0.0.2'}]
    data = analyze(tmp_path, 'eve.jsonl', '\n'.join(map(json.dumps, rows)))
    assert data.records == data.recognized_records == 2
    assert len(data.findings) == 1 and data.findings[0].severity == 'HIGH'
    assert 'upstream' in data.findings[0].recommendation.lower()


def test_invalid_records_make_coverage_partial(tmp_path):
    data = analyze(tmp_path, 'mixed.jsonl', '{"message":"healthy"}\n{broken}\n')
    assert data.records == 2 and data.invalid_records == 1 and data.recognized_records == 1
    assert data.coverage_status == 'Partial format coverage'
