from __future__ import annotations

from .report_paths import default_report_dir

import html
import json
import tempfile
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

from .dashboard_v213 import render_dashboard
from .navigation import KeyboardReader, Prompt, WorkspaceBack, shell_navigation, wait_for_navigation
from .realtime import RealtimeState
from .command_center_ui import render_realtime_command_center
from .reporting import write_html_report
from .sanitize import redact_sensitive, terminal_safe
from .security_workbench import Filters, Tuning, check_integrity, export_evidence, investigate_file, load_watchlist, record_integrity
from .terminal_charts import TerminalPanel
from .theme import ACCENT, ACCENT_SOFT, MUTED, NEUTRAL, SUCCESS, SURFACE, WARNING

console = Console()


def timeline_view(records):
    table = Table(expand=True, box=None, padding=(0, 1))
    table.add_column("TIME / LINE", ratio=2)
    table.add_column("LOG ACCOUNT / SOURCE", ratio=2)
    table.add_column("OBSERVATION", ratio=2)
    timeline = sorted((r for r in records if r.action), key=lambda r: (r.timestamp or "9999", r.line))
    for r in timeline[-30:]:
        table.add_row(Text(f"{r.timestamp or 'unknown time'} / {r.line}", style=MUTED),
                      Text(f"{r.account or 'unknown'} / {r.source_ip or r.host or 'unknown'}", style=NEUTRAL), Text(r.action, style=ACCENT))
    if not timeline:
        table.add_row("-", "-", "No supported account/privilege observations")
    return TerminalPanel(Group(table, Text(f"Showing last {min(30, len(timeline))}/{len(timeline)} observations. Log account fields may identify actor or target; validate source evidence. Unknown times sort last.", style=MUTED)),
                         title=" ACCOUNT & PRIVILEGE TIMELINE ", border_style=ACCENT_SOFT, style=f"{NEUTRAL} on {SURFACE}")


def workbench_view(investigation, filters):
    return Group(render_dashboard(investigation.dashboard(filters), screen_width=console.size.width),
                 Text("[F Filters] [X Clear filters] [O Open report] [E Export evidence] [T Timeline]\n"
                      "[W Watchlist] [C Detection tuning] [I Integrity] [P Demo replay] [R Refresh] [V Scope] [D Details]\n[B Back] [Q Quit]", style=ACCENT))


def finding_details(investigation, filters):
    records, signals = investigation.select(filters)
    by_line = {record.line: record for record in records}
    panels = []
    for signal in signals[:20]:
        finding = signal.finding
        body = Text(f"Trigger / evidence: {finding.evidence}\nNext investigation: {finding.recommendation}\nSource line references: {', '.join(map(str, signal.lines)) or 'not resolved'}", style=NEUTRAL)
        if signal.suppression_reason:
            body.append(f"\nSuppressed: {signal.suppression_reason}", style=WARNING)
        for number in signal.lines[-5:]:
            record = by_line.get(number)
            if record:
                body.append(f"\nLine {number}: {record.evidence[:500]}", style=MUTED)
        panels.append(TerminalPanel(body, title=Text(f" {finding.severity} / {finding.title} ", style=ACCENT),
                                    border_style=ACCENT_SOFT, style=f"{NEUTRAL} on {SURFACE}"))
    return Group(Text(f"FINDING DETAILS: showing {min(20, len(signals))}/{len(signals)} selected signals. Up to five selected source excerpts per finding; export retains available references.", style=MUTED),
                 *panels, *([Text("No findings match the current filters.", style=MUTED)] if not signals else []))


def scope_view(investigation, filters):
    records, signals = investigation.select(filters)
    active = [s for s in signals if not s.suppression_reason]
    suppressed = [s for s in signals if s.suppression_reason]
    summary = Text(f"SECURITY WORKBENCH / SAVED FILE\nSource: {terminal_safe(str(investigation.path))}\n"
                   f"Selected {len(records):,} retained events / {investigation.total_lines:,} source lines; "
                   f"{len(active)} active findings; {len(suppressed)} suppressed\n"
                   f"Retention: {investigation.sampled_lines:,} lines outside sample; {investigation.truncated_lines:,} lines truncated at 16 KiB; {investigation.omitted_signals:,} signals omitted by limits\n"
                   f"Filters: {', '.join(f'{k}={v}' for k,v in asdict(filters).items() if v) or 'all retained evidence'}\n"
                   f"Login rule: {investigation.tuning.login_failure_threshold} preceding failures / {investigation.tuning.login_window_seconds}s",
                   style=NEUTRAL)
    suppression = Text("SUPPRESSED FINDINGS (still exported)\n", style=WARNING)
    for signal in suppressed[:8]:
        suppression.append(f"{signal.finding.title}: {signal.suppression_reason}\n", style=MUTED)
    return Group(TerminalPanel(summary, border_style=ACCENT, style=f"{NEUTRAL} on {SURFACE}"), suppression)


def write_security_report(investigation, filters, output_dir: Path | None = None):
    root = output_dir or default_report_dir()
    root.mkdir(parents=True, exist_ok=True)
    target = root / "security-workbench-report.html"
    if target.resolve() == investigation.path.resolve():
        raise ValueError("Report cannot overwrite source")
    records, signals = investigation.select(filters)
    def esc(value):
        return html.escape(str(value))
    rows = "".join(f"<tr><td>{esc(r.timestamp or 'unknown')}</td><td>{r.line}</td><td>{esc(r.account or 'unknown')}</td><td>{esc(r.action)}</td></tr>" for r in records if r.action)
    suppressed = "".join(f"<li>{esc(s.finding.title)} — {esc(s.suppression_reason)}</li>" for s in signals if s.suppression_reason)
    extra = f"<h2>Workbench scope</h2><p>Selected {len(records)} events from {len(investigation.records)} retained / {investigation.total_lines} source lines. {investigation.sampled_lines} lines outside sample; {investigation.truncated_lines} lines truncated. Filters: {esc(json.dumps(asdict(filters)))}. Login threshold: {investigation.tuning.login_failure_threshold} failures within {investigation.tuning.login_window_seconds}s.</p><h2>Account and privilege timeline</h2><p>Account fields can describe actors or targets; validate original evidence.</p><table><tr><th>Time</th><th>Source line</th><th>Log account</th><th>Observation</th></tr>{rows}</table><h2>Documented suppressions</h2><ul>{suppressed}</ul>"
    return write_html_report(investigation.dashboard(filters), root,
                             filename=target.name, appendix_extra=extra)


def open_report(path: Path):
    if not webbrowser.open(path.resolve().as_uri()):
        console.print(Text(f"Browser did not open. Open this file manually: {path}", style=WARNING))


def run_workbench(path: Path, filters=None, tuning=None, indicators=None, year=None):
    filters, tuning = filters or Filters(), tuning or Tuning()
    indicators = indicators or set()
    while True:
        try:
            investigation = investigate_file(path, tuning, indicators, year=year)
        except (OSError, ValueError) as exc:
            console.print(Text(redact_sensitive(str(exc)), style=WARNING))
            Prompt.ask("R Retry / B Back / Q Quit", choices=["r"], default="b")
            continue
        while True:
            console.clear()
            console.print(workbench_view(investigation, filters))
            action = Prompt.ask("Action", choices=["f", "x", "o", "e", "t", "w", "c", "i", "p", "r", "v", "d"], default="r")
            try:
                if action == "r":
                    break
                if action == "x":
                    filters = Filters()
                elif action == "f":
                    values = {name: Prompt.ask(label, default=getattr(filters, name)) for name, label in [
                        ("severity", "Severity (blank = all)"), ("category", "Category (blank = all)"),
                        ("service", "Service (exact; blank = all)"), ("source", "Source format or filename (blank = all)"),
                        ("since", "Since ISO time with timezone (blank = all)"), ("until", "Until ISO time with timezone (blank = all)")]}
                    selected = Filters(**values)
                    selected.validate()
                    filters = selected
                elif action == "o":
                    open_report(write_security_report(investigation, filters))
                elif action == "e":
                    output = Path(Prompt.ask("New JSON export path", default=f"aegislog-evidence-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json").strip('"'))
                    export_evidence(investigation, filters, output)
                    console.print(Text(f"Exported: {output}", style=SUCCESS))
                elif action == "d":
                    console.print(finding_details(investigation, filters))
                elif action == "v":
                    console.print(scope_view(investigation, filters))
                elif action == "t":
                    console.print(timeline_view(investigation.select(filters)[0]))
                elif action == "w":
                    value = Prompt.ask("Watchlist file (blank clears indicators)", default="").strip('"')
                    indicators = load_watchlist(Path(value) if value else None)
                    break
                elif action == "c":
                    value = Prompt.ask("Tuning JSON file (blank restores defaults)", default="").strip('"')
                    tuning = Tuning.load(Path(value) if value else None)
                    break
                elif action == "i":
                    mode = Prompt.ask("Integrity", choices=["record", "check"], default="check")
                    baseline = Path(Prompt.ask("Baseline JSON path", default=path.name + ".sha256.json").strip('"'))
                    result = record_integrity(path, baseline) if mode == "record" else check_integrity(path, baseline)
                    console.print(Text(json.dumps(result, indent=2), style=SUCCESS))
                elif action == "p":
                    replay_file(path, interval=0.2, limit=150)
            except (OSError, ValueError) as exc:
                console.print(Text(redact_sensitive(str(exc)), style=WARNING))
                Prompt.ask("Enter to continue", default="")
                continue
            if action in {"e", "t", "i", "p", "o", "v", "d"}:
                Prompt.ask("Enter to continue", default="")


def security(
    path: Path = typer.Argument(..., exists=True, dir_okay=False),
    severity: str = typer.Option(""), category: str = typer.Option(""), service: str = typer.Option(""),
    source: str = typer.Option(""), since: str = typer.Option(""), until: str = typer.Option(""),
    watchlist: Path | None = typer.Option(None, exists=True, dir_okay=False),
    tuning: Path | None = typer.Option(None, exists=True, dir_okay=False),
    export: Path | None = typer.Option(None, help="Create a new redacted JSON evidence export."),
    open_html: bool = typer.Option(False, "--open-report"),
    interactive: bool = typer.Option(False, "--interactive"),
    timestamp_year: int | None = typer.Option(None, min=1970, max=9999),
):
    """Filter retained evidence, correlate security sequences, and export findings."""
    try:
        filters = Filters(severity, category, service, source, since, until)
        filters.validate()
        selected_tuning, selected_indicators = Tuning.load(tuning), load_watchlist(watchlist)
        if interactive:
            with shell_navigation():
                try:
                    run_workbench(path, filters, selected_tuning, selected_indicators, timestamp_year)
                except WorkspaceBack:
                    return
            return
        investigation = investigate_file(path, selected_tuning, selected_indicators, year=timestamp_year)
        console.print(workbench_view(investigation, filters))
        console.print(scope_view(investigation, filters))
        console.print(timeline_view(investigation.select(filters)[0]))
        report = write_security_report(investigation, filters)
        console.print(Text(f"Report: {report}", style=SUCCESS))
        if export:
            export_evidence(investigation, filters, export)
        if open_html:
            open_report(report)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(redact_sensitive(str(exc))) from exc


def replay_file(path: Path, *, interval: float = 0.2, limit: int = 150):
    from .ingestion import iter_bounded_lines
    state = RealtimeState(source="DEMO REPLAY: " + str(path), window_size=500, watch_profile="all")
    banner = Text("DEMO REPLAY / RECORDED EVENTS / NOT A LIVE COLLECTOR\n[B Stop / Back] [Q Quit]", style=WARNING)
    def view():
        return Group(banner, render_realtime_command_center(state))
    with KeyboardReader() as keys, Live(view(), console=console, auto_refresh=False, screen=False) as live:
        for number, item in enumerate(iter_bounded_lines(path, 16384), 1):
            if number > limit:
                break
            state.ingest([redact_sensitive(item.text)])
            live.update(view(), refresh=True)
            wait_for_navigation(keys, interval, sleep=time.sleep)
    console.print(Text(f"Demo replay finished: {state.total_lines} recorded lines replayed; limit {limit}. Source unchanged.", style=SUCCESS))


def replay(
    path: Path | None = typer.Argument(None, exists=True, dir_okay=False),
    interval: float = typer.Option(0.2, min=0.05, max=5),
    limit: int = typer.Option(150, min=1, max=10000),
):
    """Replay recorded events into a labelled demo monitor; never writes to source."""
    try:
        if path is not None:
            replay_file(path, interval=interval, limit=limit)
        else:
            with tempfile.TemporaryDirectory(prefix="aegislog-replay-") as root:
                demo = Path(root) / "demo.log"
                demo.write_text(demo_events(), encoding="utf-8")
                replay_file(demo, interval=interval, limit=limit)
    except KeyboardInterrupt:
        console.print(Text("Demo replay stopped safely.", style=SUCCESS))


def demo_events():
    lines = [f"2026-10-02T12:00:{n:02d}Z INFO api: request completed status=200" for n in range(10)]
    lines += [f"2026-10-02T12:01:{n:02d}Z sshd: Failed password for demo-user from 203.0.113.88 host=demo01" for n in range(8)]
    lines += ["2026-10-02T12:01:20Z sshd: Accepted password for demo-user from 203.0.113.88 host=demo01",
              "2026-10-02T12:02:00Z Microsoft-Windows-Security-Auditing[4720]: INFO A user account was created. Account Name: demo-admin",
              "2026-10-02T12:02:01Z Microsoft-Windows-Security-Auditing[4732]: INFO A member was added to Administrators. Account Name: demo-admin",
              "2026-10-02T12:02:02Z Microsoft-Windows-Security-Auditing[4672]: INFO Special privileges assigned. Account Name: demo-admin",
              "2026-10-02T12:02:03Z Microsoft-Windows-Security-Auditing[4688]: INFO Account Name: demo-admin New Process Name: powershell.exe Command Line: powershell.exe -EncodedCommand DEMO_ONLY",
              "2026-10-02T12:02:04Z firewall: WARN firewall deny src=198.51.100.50 dst=192.0.2.10",
              "2026-10-02T12:03:00Z api: ERROR upstream timeout token=DEMO_ONLY",
              "2026-10-02T12:03:01Z Microsoft-Windows-Security-Auditing[1102]: INFO The audit log was cleared. Account Name: demo-admin"]
    return "\n".join(lines) + "\n"


def integrity_record(path: Path = typer.Argument(..., exists=True, dir_okay=False), baseline: Path = typer.Argument(...)):
    """Create a new SHA-256 baseline; refuses to overwrite existing files."""
    try:
        console.print(Text(json.dumps(record_integrity(path, baseline), indent=2)))
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(redact_sensitive(str(exc))) from exc


def integrity_check(path: Path = typer.Argument(..., exists=True, dir_okay=False), baseline: Path = typer.Argument(..., exists=True, dir_okay=False)):
    """Compare a stable source with its recorded SHA-256 fingerprint."""
    try:
        result = check_integrity(path, baseline)
        console.print(Text(json.dumps(result, indent=2)))
        if result["status"] == "CHANGED":
            raise typer.Exit(code=1)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(redact_sensitive(str(exc))) from exc
