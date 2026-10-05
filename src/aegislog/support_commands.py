"""Explicit local investigation, support and opt-in release discovery commands."""
import json
import platform
import re
import sys
from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .report_paths import report_search_roots


def review(path: Path = typer.Argument(..., exists=True, dir_okay=False), limit: int = 20):
    """Grouped evidence, next steps and retained Windows session context."""
    from .dashboard import analyze_dashboard
    from .triage import finding_groups, windows_session_context
    if not 1 <= limit <= 100:
        raise typer.BadParameter('limit must be between 1 and 100')
    console = Console()
    try:
        data = analyze_dashboard(path)
    except (OSError, ValueError) as exc:
        typer.echo(f'Review failed: {exc}')
        raise typer.Exit(1) from exc
    console.print(data.coverage_note, markup=False)
    groups = finding_groups(data.findings, data.timestamp_year_hint)
    for row in groups[:limit]:
        explanation = row['explanation']
        console.print(f'{row["severity"]} / {row["title"]} / {row["count"]} occurrence(s) / {row["provider"] or "unknown provider"}', markup=False)
        console.print(f'First: {row["first"] or "unresolved"} / Last: {row["last"] or "unresolved"} / {row["unresolved_timestamps"]} unresolved timestamps', markup=False)
        console.print(f'Why: {explanation["impact"]}\nAlternative: {explanation["alternative"]}\nNext: {explanation["next_step"]}', markup=False)
    console.print(f'Showing {min(limit, len(groups))}/{len(groups)} presentation groups; grouping does not establish shared cause.', markup=False)
    links = windows_session_context(data.raw_lines)
    for link in links[:limit]:
        console.print(f'Windows context: {link["host"]} / session {link["logon_id"]} / retained logon record {link["logon_record"]} → {link["related_records"]}', markup=False)
    console.print('Context covers retained records only. Session links are investigation aids, not confirmed attacks.', markup=False)


def cases(query: str = '', severity: str = '', since: str = '', limit: int = 100,
          open_number: int = 0):
    """Search saved case metadata; optionally open a displayed result number."""
    from .case_catalog import search_cases
    from .commands_security import open_report
    try:
        rows = search_cases(report_search_roots(), query=query, severity=severity, since=since, limit=limit)
        if open_number and not 1 <= open_number <= len(rows):
            raise ValueError('Open number must refer to a displayed result.')
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    for index, row in enumerate(rows, 1):
        typer.echo(f'{index}. {row["generated"]} / {row["source"]}\n   {row["path"]}')
    if not rows:
        typer.echo('No matching indexed cases. Existing HTML reports remain available through R Reports.')
    if open_number:
        open_report(Path(rows[open_number-1]['path']))


def diagnostics(output: Path = typer.Option(..., help='New JSON file; existing files are never overwritten.')):
    """Export allowlisted runtime diagnostics without paths, logs or host names."""
    payload = dict(schema='aegislog-support-1', tool_version=__version__, python=platform.python_version(),
                   os=platform.system(), architecture=platform.machine(), frozen=bool(getattr(sys, 'frozen', False)),
                   included=['tool version', 'Python version', 'OS family', 'architecture', 'packaging mode'],
                   omitted=['user and host names', 'paths', 'environment variables', 'configuration', 'raw logs', 'evidence', 'credentials'])
    try:
        with output.open('x', encoding='utf-8') as stream:
            json.dump(payload, stream, indent=2)
    except OSError as exc:
        typer.echo(f'Could not write diagnostics: {exc}')
        raise typer.Exit(1) from exc
    typer.echo(f'Diagnostics saved: {output}. No source logs or configuration included.')


def fetch_latest_release():
    # Only this explicitly invoked command accesses the network. No installation
    # or shell execution; keep the endpoint fixed and the response bounded.
    from .providers import fetch_public_release
    raw = fetch_public_release()
    if len(raw) > 1_000_000:
        raise ValueError('Release response exceeds the size limit.')
    obj = json.loads(raw)
    tag = obj.get('tag_name') if isinstance(obj, dict) else None
    if not isinstance(tag, str) or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Unexpected release metadata.')
    if obj.get('draft') is not False or obj.get('prerelease') is not False:
        raise ValueError('Expected a published stable release.')
    return tag


def update_check():
    """Contact GitHub on request and show the latest stable release; never install."""
    try:
        tag = fetch_latest_release()
    except (OSError, ValueError) as exc:
        typer.echo(f'Update check unavailable: {exc}. Installed version: {__version__}.')
        raise typer.Exit(1) from exc
    current = tuple(int(x) for x in __version__.split('.'))
    latest = tuple(int(x) for x in tag[1:].split('.'))
    typer.echo(f'Installed: {__version__} / latest published: {tag}')
    typer.echo('Newer release available.' if latest > current else 'No newer stable release found.')
    typer.echo(f'https://github.com/HR-Presents/AegisLog/releases/tag/{tag}')
    typer.echo('Use the matching release checksum before installing. Nothing was downloaded for installation or changed.')


def register(app):
    app.command('review')(review)
    app.command('cases')(cases)
    app.command('diagnostics')(diagnostics)
    app.command('update-check')(update_check)
