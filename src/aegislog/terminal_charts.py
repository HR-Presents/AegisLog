"""Responsive, Windows-safe charts drawn from actual retained telemetry."""
from __future__ import annotations

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .theme import ACCENT, ACCENT_SOFT, MUTED, NEUTRAL, SUCCESS, severity_style


class DistributionChart:
    def __init__(self, title, values, *, semantic=False, limit=6, chronological=False):
        self.title = title
        self.values = values
        self.semantic = semantic
        self.limit = limit
        self.chronological = chronological

    def __rich_console__(self, console, options):
        items = list(self.values.items())[-self.limit:] if self.chronological else sorted(self.values.items(), key=lambda item: -item[1])[:self.limit]
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
                bar = Text("#" * length, style=severity_style(str(label)) if self.semantic else ACCENT)
                bar.append("." * (bar_width - length), style=ACCENT_SOFT)
                table.add_row(Text(str(label).upper(), style=NEUTRAL), bar, Text(f"{count:,}", style=NEUTRAL))
            legend = f"Total: {total:,}\nScale: largest bar = {maximum:,}" if width < 64 else f"Scale: largest bar = {maximum:,}  |  Total: {total:,}"
            body = Group(table, Text(legend, style=MUTED))
        yield Panel(body, title=Text(f" {self.title} ", style=f"bold {ACCENT}"), title_align="left", box=box.ASCII, border_style=ACCENT_SOFT, padding=(1, 1))
