from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from aegislog.command_center_ui import render_realtime_command_center
from aegislog.dashboard_v213 import analyze_dashboard, render_dashboard
from aegislog.realtime import RealtimeState
from aegislog.terminal_charts import DistributionChart


def plain(view, width):
    console = Console(file=StringIO(), width=width, record=True, color_system=None)
    console.print(view)
    return console.export_text()


@pytest.mark.parametrize("width", [40, 64, 80, 100, 120, 180])
def test_analysis_charts_resize_without_losing_counts(tmp_path: Path, width):
    path = tmp_path / "sample.log"
    path.write_text("2026-09-10T14:32:01Z INFO api: started\n" * 7)
    output = plain(render_dashboard(analyze_dashboard(path), screen_width=width), width)
    assert "API" in output
    assert "####" in output
    assert "Total: 7" in output
    assert max(map(len, output.splitlines())) <= width
    output.encode("ascii")


def test_empty_chart_does_not_invent_activity():
    output = plain(DistributionChart("ACTIVITY", {}), 80)
    assert "No matching activity" in output
    assert "#" not in output


def test_distribution_graph_preserves_relative_magnitude():
    output = plain(DistributionChart("ACTIVITY", {"api": 8, "web": 4}), 80)
    rows = [line for line in output.splitlines() if "API" in line or "WEB" in line]
    assert rows[0].count("#") == 2 * rows[1].count("#")
    assert "Total: 12" in output


@pytest.mark.parametrize("width", [40, 64, 80, 100, 120, 180])
def test_live_charts_resize_with_actual_telemetry(monkeypatch, width):
    monkeypatch.setattr("aegislog.command_center_ui.shutil.get_terminal_size", lambda fallback: type("S", (), {"columns": width})())
    state = RealtimeState(source="live.log", window_size=50, watch_profile="all")
    state.ingest(["2026-09-10T14:32:01Z INFO api: started\n"] * 7, now=10.0)
    output = plain(render_realtime_command_center(state), width)
    assert "API" in output
    assert "#" in output
    assert "Total: 7" in output
    assert max(map(len, output.splitlines())) <= width
