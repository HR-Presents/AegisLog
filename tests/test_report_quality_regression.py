from aegislog.dashboard import analyze_dashboard
from aegislog.engine import Finding
from aegislog.incidents import correlate
from aegislog.parsers import parse_line


def test_iso_service_parser_retains_level_service_and_message():
    event = parse_line(
        "2026-09-02T12:00:18Z ERROR firewall[903]: blocked inbound connection from 203.0.113.77 port=22"
    )

    assert event.source == "iso-service"
    assert event.level == "error"
    assert event.service == "firewall"
    assert event.message == "blocked inbound connection from 203.0.113.77 port=22"


def test_report_telemetry_does_not_collapse_iso_services_to_unknown(tmp_path):
    source = tmp_path / "sample.log"
    source.write_text(
        "\n".join(
            [
                "2026-09-02T12:00:18Z ERROR firewall[903]: blocked inbound connection from 203.0.113.77 port=22",
                "2026-09-02T12:00:33Z ERROR app[774]: database connection timeout service=customer-api",
                "2026-09-02T12:00:59Z ERROR sudo[1820]: guest is not in the sudoers file",
                "2026-09-02T12:01:14Z ERROR backup[1990]: backup destination temporarily unavailable",
            ]
        ),
        encoding="utf-8",
    )

    data = analyze_dashboard(source)

    assert data.services == {"firewall": 1, "app": 1, "sudo": 1, "backup": 1}
    assert all(not anomaly.key.startswith("unknown:") for anomaly in data.anomalies)


def test_unrelated_operational_errors_are_not_one_correlated_incident():
    findings = [
        Finding(
            "MEDIUM",
            "error",
            "Operational error detected",
            "2026-09-02T12:00:33Z ERROR app[774]: database connection timeout service=customer-api",
            "review",
        ),
        Finding(
            "MEDIUM",
            "error",
            "Operational error detected",
            "2026-09-02T12:01:14Z ERROR backup[1990]: backup destination temporarily unavailable",
            "review",
        ),
    ]

    assert correlate(findings) == []


def test_repeated_same_service_and_source_can_correlate():
    findings = [
        Finding(
            "MEDIUM",
            "network",
            "Firewall blocked inbound activity",
            "2026-09-02T12:00:18Z ERROR firewall[903]: blocked inbound connection from 203.0.113.77 port=22",
            "review",
        ),
        Finding(
            "MEDIUM",
            "network",
            "Firewall blocked inbound activity",
            "2026-09-02T12:01:28Z ERROR firewall[903]: blocked inbound connection from 203.0.113.77 port=22",
            "review",
        ),
    ]

    incidents = correlate(findings)

    assert len(incidents) == 1
    assert incidents[0].count == 2
    assert incidents[0].category == "network"


def test_report_print_has_readable_charts_and_score_context(tmp_path):
    from aegislog.dashboard import analyze_dashboard
    from aegislog.reporting import build_html_report
    path = tmp_path / 'native.log'
    path.write_text('2026-10-02T15:04:18Z Service Control Manager[7011]: ERROR A timeout while waiting for BrYNSvc\n' * 2)
    html = build_html_report(analyze_dashboard(path))
    assert 'Rarity score / 100' in html and '100% attack probability' in html
    assert 'Grouping basis:' in html and 'no time-window constraint' in html
    assert "named service&#x27;s own logs" in html
    assert 'class="activity-counts"' in html and 'Small sample; direct observed counts.' in html
    assert 'class="chart"' not in html
    path.write_text('2026-10-02T15:04:18Z Service Control Manager[7011]: ERROR A timeout while waiting for BrYNSvc\n' * 30)
    large = build_html_report(analyze_dashboard(path))
    assert 'class="chart"' in large and 'retained total 30' in large
    assert 'color:#1f2937!important' in html
    assert 'Headers and footers' in html


def test_report_charts_escape_untrusted_service_names():
    from aegislog.reporting import _bar_chart
    html = _bar_chart({'<script>alert(1)</script>': 3}, 'Service activity')
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
