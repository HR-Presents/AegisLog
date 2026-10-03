from __future__ import annotations

from datetime import datetime, timezone
import time

from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from .terminal_charts import TerminalPanel as Panel
from rich.table import Table
from rich.text import Text
from rich.segment import Segment
from rich.live import Live

from . import commands_v144 as legacy
from .config import CONFIG_DIR
from .report_browser import INTRODUCTION
from .navigation import KeyboardReader, shell_navigation
from .theme import SURFACE, ACCENT, ACCENT_SOFT, DIM, MUTED, NEUTRAL, SUCCESS

_LEGACY_INLINE_COMMAND = legacy._run_inline_command
_NARROW_BREAKPOINT = 72
_WIDE_BREAKPOINT = 96


def _screen_width(screen_width: int | None = None) -> int:
    width = legacy.console.size.width if screen_width is None else screen_width
    return max(1, width - 2)


def _frame_width(screen_width: int | None = None) -> int:
    return _screen_width(screen_width)


def _rule(width: int) -> Text:
    return Text("-" * max(16, width), style=DIM)


def _wordmark(compact: bool = False) -> Text:
    mark = Text(justify="center")
    if compact:
        mark.append("AEGISLOG", style=f"bold {ACCENT}")
        return mark
    lines = (
        r"    _    _____ ____ ___ ____  _     ___   ____ ",
        r"   / \  | ____/ ___|_ _/ ___|| |   / _ \ / ___|",
        r"  / _ \ |  _|| |  _ | |\___ \| |  | | | | |  _ ",
        r" / ___ \| |__| |_| || | ___) | |__| |_| | |_| |",
        r"/_/   \_\_____\____|___|____/|_____\___/ \____|",
    )
    for index, line in enumerate(lines):
        if index:
            mark.append("\n")
        mark.append(line, style=f"bold {ACCENT}")
    return mark


def _brand_lockup(compact: bool = False, *, screen_width: int | None = None) -> RenderableType:
    width = _frame_width(screen_width)
    if compact or width < _NARROW_BREAKPOINT:
        body = Text(justify="center")
        body.append("AEGISLOG\n", style=f"bold {ACCENT}")
        body.append("DEFENSIVE LOG INVESTIGATION\n", style=f"bold {NEUTRAL}")
        body.append("MADE BY HR-PRESENTS\n", style=f"bold {ACCENT}")
        body.append("LOCAL-FIRST  |  READ-ONLY  |  DETERMINISTIC", style=MUTED)
        body.append("\n" + datetime.now(timezone.utc).strftime("%H:%M:%S UTC  /  %d %b %Y"), style=SUCCESS)
        return body
    return Group(
        Align.center(_wordmark()),
        Align.center(Text("DEFENSIVE LOG INVESTIGATION", style=f"bold {NEUTRAL}")),
        Align.center(Text("MADE BY HR-PRESENTS", style=f"bold {ACCENT}")),
        Align.center(Text("LOCAL-FIRST  |  READ-ONLY  |  DETERMINISTIC", style=MUTED)),
        Align.center(Text(datetime.now(timezone.utc).strftime("%H:%M:%S UTC  /  %d %b %Y"), style=SUCCESS)),
    )


def _header(screen_width: int | None = None) -> RenderableType:
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=_brand_lockup(screen_width=screen_width), box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1), width=_frame_width(screen_width))


def _operation_header(title: str, subtitle: str, accent: str = ACCENT, *, screen_width: int | None = None) -> RenderableType:
    width = _frame_width(screen_width)
    heading = Text()
    heading.append("AEGISLOG", style=f"bold {NEUTRAL}")
    heading.append("  //  ", style=MUTED)
    heading.append(title.upper(), style=f"bold {accent}")
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=Group(heading, Text(subtitle, style=NEUTRAL, overflow="fold"), Text("LOCAL / READ-ONLY / DETERMINISTIC", style=MUTED), Text("MADE BY HR-PRESENTS", style=f"bold {ACCENT}")), title=Text(" ACTIVE WORKSPACE ", style=f"bold {accent}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(0, 1), width=width)


def _input_panel(title: str, lines: list[tuple[str, str]], accent: str = ACCENT, *, screen_width: int | None = None, primary_label: str | None = None) -> RenderableType:
    width = _frame_width(screen_width)
    compact = width < _NARROW_BREAKPOINT
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(width=12 if compact else 16, no_wrap=True)
    grid.add_column(ratio=1, overflow="fold")
    for label, value in lines:
        primary = primary_label is not None and label == primary_label
        grid.add_row(Text(label.upper(), style=f"bold {accent}" if primary else MUTED), Text(value, style=NEUTRAL if primary else MUTED, overflow="fold"))
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=grid, title=Text(f" {title.upper()} ", style=f"bold {accent}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(0, 1), width=width)


def _action_line(key: str, label: str, description: str, *, primary: bool = False) -> Text:
    line = Text(overflow="fold")
    line.append(f"[{key}] ", style=f"bold {ACCENT}")
    line.append(f"{label:<16}", style=f"bold {NEUTRAL}")
    line.append(description, style=NEUTRAL if primary else MUTED)
    return line


def _primary_panel(width: int) -> Panel:
    body = Group(_action_line("01", "ANALYZE LOG", "Investigate a log file and create a report", primary=True), Text("     Deterministic findings, incidents and evidence", style=MUTED, no_wrap=True, overflow="crop"))
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=body, title=Text(" INVESTIGATE ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT, padding=(1, 1), width=width, height=8)


def _tools_panel(width: int) -> Panel:
    rows = (("02", "LIVE MONITOR", "Watch one log source"), ("03", "MULTI-SOURCE", "Correlate live sources"), ("04", "NATIVE LOGS", "Inspect native telemetry"), ("05", "NATIVE MONITOR", "Watch native telemetry"), ("06", "INCIDENTS", "Review evidence chains"))
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=Group(*[_action_line(*row) for row in rows]), title=Text(" MONITOR & INVESTIGATE ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1), width=width)


def _utility_panel(width: int) -> Panel:
    rows = (("07", "DEMO", "Quick start dataset"), ("08", "HEALTH", "Engine diagnostics"), ("09", "HELP", "Command reference"), ("C", "CHECK COMPUTER", "Guided native-log investigation"), ("F", "SCAN FOLDER", "Find and analyze local log files"), ("R", "REPORTS", "Open saved HTML reports"), ("A", "ABOUT / GUIDE", "What it does and how to use it"))
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=Group(*[_action_line(*row) for row in rows]), title=Text(" UTILITIES ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1), width=width)


def _status_panel(width: int) -> Panel:
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(width=9, no_wrap=True)
    grid.add_column(ratio=1, overflow="crop", no_wrap=True)
    grid.add_row(Text("STATUS", style=MUTED), Text("SYSTEM READY", style=f"bold {SUCCESS}"))
    grid.add_row(Text("MODE", style=MUTED), Text("LOCAL", style=NEUTRAL))
    grid.add_row(Text("DATA", style=MUTED), Text("READ-ONLY", style=NEUTRAL))
    grid.add_row(Text("ENGINE", style=MUTED), Text("DETERMINISTIC", style=NEUTRAL))
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=grid, title=Text(" SYSTEM ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1), width=width)


def _quick_info_panel(width: int) -> Panel:
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(width=9, no_wrap=True)
    grid.add_column(ratio=1, no_wrap=True, overflow="crop")
    for label, value in (("REPORTS", "R: local / user report folders"), ("CONFIG", str(CONFIG_DIR)), ("PROJECT", "HR-Presents/AegisLog-AI"), ("OWNER", "HR-PRESENTS")):
        grid.add_row(Text(label, style=MUTED), Text(value, style=ACCENT if label != "OWNER" else NEUTRAL, no_wrap=True, overflow="crop"))
    return Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=grid, title=Text(" QUICK INFO ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1), width=width, height=9)


def _menu(screen_width: int | None = None) -> RenderableType:
    width = _frame_width(screen_width)
    if width < _NARROW_BREAKPOINT:
        rows = [("01", "ANALYZE LOG", "Investigate a log"), ("02", "LIVE MONITOR", "Watch a source"), ("03", "MULTI-SOURCE", "Correlate sources"), ("04", "NATIVE LOGS", "Inspect telemetry"), ("05", "NATIVE MONITOR", "Watch telemetry"), ("06", "INCIDENTS", "Review evidence"), ("07", "DEMO", "Quick start"), ("08", "HEALTH", "Diagnostics"), ("09", "HELP", "Reference"), ("C", "CHECK COMPUTER", "Guided native logs"), ("F", "SCAN FOLDER", "Find local log files"), ("R", "REPORTS", "Open saved reports"), ("A", "ABOUT / GUIDE", "What it does / how to use")]
        return Group(_status_panel(width), Text(""), Panel(style=f"{NEUTRAL} on {SURFACE}", renderable=Group(*[_action_line(*row) for row in rows]), title=Text(" COMMAND CENTER ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1), width=width))

    if width >= _WIDE_BREAKPOINT:
        gap = 2
        # Use the real Windows terminal width instead of freezing the command
        # center at the old 112-column cap. Keep a 64/36 split so the primary
        # investigation area remains dominant while status/info fill the right.
        left_width = max(64, int((width - gap) * 0.64))
        right_width = width - gap - left_width
        layout = Table.grid(padding=0)
        layout.add_column(width=left_width)
        layout.add_column(width=gap)
        layout.add_column(width=right_width)
        # Separate rows prevent one tall column leaving an empty bottom quadrant.
        layout.add_row(_primary_panel(left_width), Text(""), _status_panel(right_width))
        layout.add_row(Text(""), Text(""), Text(""))
        layout.add_row(_tools_panel(left_width), Text(""), _quick_info_panel(right_width))
        return Group(layout, Text(""), _utility_panel(width))

    return Group(_primary_panel(width), Text(""), _tools_panel(width), Text(""), _utility_panel(width), Text(""), _status_panel(width))


def _footer(screen_width: int | None = None) -> Text:
    width = _frame_width(screen_width)
    footer = Text(overflow="crop", no_wrap=True)
    footer.append("[01-09]", style=f"bold {ACCENT}")
    footer.append(" Select", style=NEUTRAL)
    footer.append("   |   [Q Exit]", style=MUTED)
    if width >= 48:
        footer.append("   |   type a command / S tools / P replay", style=NEUTRAL)
    if width >= 100:
        footer.append("   |   Ctrl+C stops live views", style=MUTED)
    return footer


def _home(screen_width: int | None = None, screen_height: int | None = None) -> RenderableType:
    frame_width = _frame_width(screen_width)
    available = _screen_width(screen_width)
    header, menu = _header(screen_width), _menu(screen_width)
    dense = screen_height is not None and screen_height < 40
    if dense:
        def tighten(renderable):
            if isinstance(renderable, Panel):
                renderable.padding = (0, 1)
                renderable.height = None
            elif isinstance(renderable, Group):
                for child in renderable.renderables:
                    tighten(child)
            elif isinstance(renderable, Table):
                for column in renderable.columns:
                    for child in column._cells:
                        tighten(child)
        tighten(header)
        tighten(menu)
    spacer = [] if dense else [Text("")]
    intro = INTRODUCTION[:2] if dense else INTRODUCTION
    separator = [] if dense else [_rule(frame_width)]
    content = Group(header, *[Text(line, style=MUTED) for line in intro], *spacer, menu, *spacer, *separator, _footer(screen_width))
    return Align.center(content, width=available, pad=False)


def _run_inline_command(raw: str) -> None:
    if raw.strip().lower() in {"a", "ai", "ai-analyst", "ask"}:
        legacy.console.print("AI Analyst is not part of AegisLog. Use deterministic investigation commands instead.", style=MUTED)
        return
    _LEGACY_INLINE_COMMAND(raw)


class _HomeViewport:
    """Scroll the original home without replacing its panels or logo."""
    def __init__(self, width, height, offset=0):
        self.width, self.height, self.offset = width, max(1, height), offset

    def prepare(self, console, options):
        self.lines = console.render_lines(_home(self.width, self.height), options.update(width=self.width), pad=False)
        self.maximum = max(0, len(self.lines) - self.height)
        self.offset = min(max(0, self.offset), self.maximum)
        return self

    def __rich_console__(self, console, options):
        self.prepare(console, options)
        lines = self.lines
        start = self.offset
        for line in lines[start:start + self.height]:
            yield from line
            yield Segment.line()


def _read_home_choice() -> str:
    if legacy.console.is_terminal:
        # Clear the restored main buffer before entering the alternate home screen.
        legacy.console.clear()
    with KeyboardReader() as keys:
        if not keys.enabled or not legacy.console.is_terminal:
            legacy.console.print(_home(legacy.console.size.width))
            return legacy.console.input(f"[bold {ACCENT}]aegis@console > [/bold {ACCENT}]")
        value = ""
        offset = 0
        def frame():
            nonlocal offset
            size = legacy.console.size
            viewport = _HomeViewport(size.width, max(1, size.height - 3), offset)
            viewport.prepare(legacy.console, legacy.console.options)
            offset = viewport.offset
            if viewport.maximum:
                position = f"Rows {offset + 1}-{min(offset + viewport.height, len(viewport.lines))}/{len(viewport.lines)} | PgUp/PgDn | Home/End"
            else:
                position = "All panels visible"
            controls = Text(position + " | 09 Help | Q Quit", style=MUTED, no_wrap=True, overflow="crop")
            prompt = Text("aegis@console > ", style=f"bold {ACCENT}", no_wrap=True, overflow="crop")
            available = max(1, size.width - len(prompt.plain) - 1)
            prompt.append(value[-available:], style=NEUTRAL)
            shortcuts = Text('[C Check] [F Folder] [R Reports] [A Guide] [G Beginner] [Q Quit]' if size.width >= 80 else '[C] [F] [R] [A] [G] [Q Quit]', style=ACCENT, no_wrap=True, overflow="crop")
            return Group(viewport, controls, shortcuts, prompt)
        with Live(frame(), console=legacy.console, auto_refresh=False,
                  screen=True, transient=True, vertical_overflow="crop") as live:
            next_refresh = time.monotonic()
            previous_size = legacy.console.size
            while True:
                key = keys.poll()
                if key in {"UP", "PAGEUP", "HOME"}:
                    offset = 0 if key == "HOME" else max(0, offset - (1 if key == "UP" else max(1, legacy.console.size.height - 3)))
                elif key == "END":
                    offset = 1000000
                elif key in {"DOWN", "PAGEDOWN"}:
                    offset += 1 if key == "DOWN" else max(1, legacy.console.size.height - 3)
                elif key in {"\r", "\n"}:
                    return value
                if key in {"\x03", "\x04"}:
                    raise KeyboardInterrupt()
                if key in {"\x08", "\x7f"}:
                    value = value[:-1]
                elif key and len(key) == 1 and key.isprintable() and len(value) < 4096:
                    value += key
                size = legacy.console.size
                if key or time.monotonic() >= next_refresh or size != previous_size:
                    # Build a fresh clock while preserving the editable command.
                    live.update(frame(), refresh=True)
                    next_refresh = time.monotonic() + 1
                    previous_size = size
                time.sleep(0.05)


def start() -> None:
    """Run the responsive terminal shell over the deterministic investigation engine."""
    original_home = legacy._home
    original_inline = legacy._run_inline_command
    original_input_panel = legacy._input_panel
    original_operation_header = legacy._operation_header
    original_reader = legacy._read_home_choice
    try:
        legacy._home = _home
        legacy._run_inline_command = _run_inline_command
        legacy._input_panel = _input_panel
        legacy._operation_header = _operation_header
        legacy._read_home_choice = _read_home_choice
        with shell_navigation():
            legacy.start()
    finally:
        legacy._home = original_home
        legacy._run_inline_command = original_inline
        legacy._input_panel = original_input_panel
        legacy._operation_header = original_operation_header
        legacy._read_home_choice = original_reader


__all__ = ["start"]
