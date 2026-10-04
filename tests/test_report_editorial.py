from aegislog.report_editorial import activity_timeline, report_signature


def test_timeline_uses_resolved_utc_minutes_and_states_missing_excerpts():
    html = activity_timeline([
        '2026-10-04T12:00:00+02:00 app: hello',
        '2026-10-04T10:01:00Z app: hello',
        'unknown clock app: hello',
    ])
    assert '2026-10-04 10:00 UTC' in html
    assert '2026-10-04 10:01 UTC' in html
    assert '2 displayed excerpts' in html and '1 unresolved' in html
    assert 'Gaps are not shown' in html


def test_undated_sample_does_not_invent_a_timeline():
    html = activity_timeline(['Aug 29 12:00:00 demo app: hello'])
    assert 'No resolved minute sequence' in html
    assert '0/1 retained excerpts' in html and '<svg' not in html


def test_timeline_is_bounded_and_does_not_call_single_minute_a_trend():
    lines = [f'2026-10-04T10:{minute:02d}:00Z app: hello' for minute in range(20)]
    html = activity_timeline(lines)
    assert 'Last 12 occupied minute buckets' in html and '20 timestamped excerpts retained' in html
    assert '2026-10-04 10:00 UTC' not in html
    assert 'single minute' in activity_timeline([lines[0], lines[0]])


def test_signature_is_visible_text_and_escapes_metadata():
    html = report_signature('<case>', '<version>')
    assert 'MADE BY HR-PRESENTS' in html
    assert '&lt;case&gt;' in html and '<version>' not in html
