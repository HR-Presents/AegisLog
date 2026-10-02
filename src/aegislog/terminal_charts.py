"""Responsive, Windows-safe charts drawn from actual retained telemetry."""
from __future__ import annotations

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .theme import ACCENT, ACCENT_SOFT, MUTED, NEUTRAL, SUCCESS, severity_style, SURFACE, TRACK


class TerminalPanel(Panel):
    """Thin reference borders with an ASCII fallback for legacy Windows consoles."""

    def __rich_console__(self, console, options):
        from copy import copy
        view = copy(self)
        unicode = console.color_system is not None and not console.legacy_windows and console.encoding.lower().replace('-', '') == 'utf8'
        view.box = box.SQUARE if unicode else box.ASCII
        yield from Panel.__rich_console__(view, console, options)


class DistributionChart:
    def __init__(self, title, values, *, semantic=False, limit=6, chronological=False):
        self.title = title
        self.values = values
        self.semantic = semantic
        self.limit = limit
        self.chronological = chronological

    def __rich_console__(self, console, options):
        items = sorted(self.values.items(), key=lambda item: item[0])[-self.limit:] if self.chronological else sorted(self.values.items(), key=lambda item: -item[1])[:self.limit]
        if not items or not any(value > 0 for _, value in items):
            body = Text("No matching activity in this sample.", style=SUCCESS)
        else:
            width = options.max_width
            bar_width = max(3, min(28, width - 30))
            maximum = max(value for _, value in items)
            total = sum(self.values.values())
            table = Table.grid(expand=True, padding=(0, 1))
            table.add_column(width=max(4, min(30, width - bar_width - 14)), overflow="ellipsis", no_wrap=True)
            table.add_column(ratio=1, no_wrap=True)
            table.add_column(justify="right", no_wrap=True)
            for label, count in items:
                length = max(1, round(count / maximum * bar_width)) if count else 0
                glyph = "█" if console.color_system is not None and console.encoding.lower().replace("-", "") == "utf8" else "#"
                bar = Text(glyph * length, style=severity_style(str(label)) if self.semantic else ACCENT)
                bar.append((" " if glyph == "█" else ".") * (bar_width - length), style=f"{MUTED} on {TRACK}")
                table.add_row(Text(str(label).upper(), style=NEUTRAL), bar, Text(f"{count:,}", style=NEUTRAL))
            legend = f"Total: {total:,}\nScale: largest bar = {maximum:,}" if width < 64 else f"Scale: largest bar = {maximum:,}  |  Total: {total:,}"
            body = Group(table, Text(legend, style=MUTED))
        yield TerminalPanel(body, style=f"{NEUTRAL} on {SURFACE}", title=Text(f" {self.title} ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1))


class ActivityChart:
    """Vertical bars, a compact sparkline, and a dot plot over actual minute buckets."""

    def __init__(self, values, title="EVENT ACTIVITY / RECENT MINUTE BUCKETS"):
        self.values = values
        self.title = title

    def __rich_console__(self, console, options):
        from .theme import HIGH, SUCCESS
        items = sorted(self.values.items())[-min(12, max(1, (options.max_width - 12) // 5)):]
        if not items:
            yield TerminalPanel(Text("No timestamped activity in retained telemetry.", style=MUTED), title=self.title,
                        box=box.ASCII, border_style=ACCENT_SOFT, style=f"{NEUTRAL} on {SURFACE}")
            return
        maximum = max(value for _, value in items) or 1
        unicode = console.color_system is not None and console.encoding.lower().replace('-', '') == 'utf8'
        height = 5
        rows = []
        for y in range(height, 0, -1):
            row = Text(f"{maximum * y / height:>5.0f} | ", style=MUTED)
            for _, value in items:
                filled = value > 0 and max(1, round(value / maximum * height)) >= y
                row.append(("███" if unicode else "###") if filled else "   ", style=SUCCESS)
                row.append("  ")
            rows.append(row)
        labels = Text("      + " + "-----" * len(items), style=ACCENT_SOFT)
        rows.append(labels)
        rows.append(Text("        " + "  ".join(label[-5:] for label, _ in items), style=ACCENT))
        blocks = "▁▂▃▄▅▆▇█" if unicode else "._-:=+*#"
        spark = Text("Trend   ", style=MUTED)
        for _, value in items:
            spark.append(blocks[min(7, round(value / maximum * 7))], style=HIGH)
        rows.append(spark)
        rows.append(Text(f"UTC: {items[0][0]} to {items[-1][0]}", style=MUTED))
        dot_rows = []
        for y in range(3, -1, -1):
            row = Text("        ")
            for _, value in items:
                row.append(("  •  " if unicode else "  *  ") if round(value / maximum * 3) == y else "     ", style=ACCENT)
            dot_rows.append(row)
        rows.append(Text("Dot plot / same minute counts", style=MUTED))
        rows.extend(dot_rows)
        rows.append(Text(f"Total: {sum(self.values.values()):,} | retained timestamped events; peak {maximum:,}/minute", style=MUTED))
        yield TerminalPanel(Group(*rows), title=Text(f" {self.title} ", style=f"bold {ACCENT}"), title_align="left",
                    box=box.ASCII, border_style=ACCENT_SOFT, style=f"{NEUTRAL} on {SURFACE}", padding=(0, 1))


def minute_activity(lines, timestamp_year_hint=None):
    """Normalize timestamp offsets before grouping and sorting minute buckets."""
    from collections import Counter
    from datetime import timezone
    from .engine import _parse_timestamp
    buckets = Counter()
    for line in lines:
        stamp = _parse_timestamp(line, timestamp_year_hint)
        if stamp is not None:
            buckets[stamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")] += 1
    return buckets


class Gauge:
    """A labelled fraction, never an invented risk or confidence score."""

    def __init__(self, label, value, total, *, style=ACCENT):
        self.label, self.value, self.total, self.style = label, value, total, style

    def __rich_console__(self, console, options):
        ratio = min(1.0, max(0.0, self.value / self.total)) if self.total else 0.0
        width = max(3, min(40, options.max_width - 18))
        filled = round(width * ratio)
        unicode = console.color_system is not None and console.encoding.lower().replace('-', '') == 'utf8'
        line = Text(("█" if unicode else "#") * filled, style=self.style)
        line.append((" " if unicode else ".") * (width - filled), style=f"{MUTED} on {TRACK}")
        line.append(f"  {ratio:.0%}  ({self.value:,}/{self.total:,})" if self.total else "  N/A (no sample)", style=NEUTRAL)
        yield TerminalPanel(line, title=Text(f" {self.label} ", style=f"bold {ACCENT}"), title_align='left',
                    box=box.ASCII, border_style=ACCENT_SOFT, style=f"{NEUTRAL} on {SURFACE}", padding=(0, 1))


class Sparkline:
    def __init__(self, label, values, *, style=ACCENT):
        self.label, self.values, self.style = label, tuple(values), style

    def __rich_console__(self, console, options):
        values = self.values[-max(1, options.max_width - 4):]
        if not values:
            yield Text(f"{self.label}: no retained history", style=MUTED)
            return
        maximum = max(values) or 1
        blocks = "▁▂▃▄▅▆▇█" if console.color_system is not None and console.encoding.lower().replace('-', '') == 'utf8' else "._-:=+*#"
        line = Text(self.label + "\n", style=MUTED)
        for value in values:
            line.append(blocks[min(7, round(value / maximum * 7))], style=self.style)
        line.append(f"  peak {max(values):,}/bucket", style=MUTED)
        yield line
