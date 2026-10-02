from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from rich.console import Group
from rich.text import Text

from .sanitize import redact_sensitive
from .terminal_charts import TerminalPanel
from .theme import ACCENT_SOFT, MUTED, NEUTRAL, SUCCESS, SURFACE, WARNING


@dataclass
class CollectorHealth:
    status: str = "NOT POLLED"
    last_success: str | None = None
    last_failure: str | None = None
    failures: int = 0
    polls: int = 0
    events: int = 0
    detail: str = ""
    last_count: int | None = None

    def success(self, count: int):
        self.status = "AVAILABLE"
        self.last_success = datetime.now(timezone.utc).isoformat()
        self.polls += 1
        self.events += count
        self.last_count = count
        self.detail = ""

    def failure(self, error):
        self.status = "UNAVAILABLE"
        self.last_failure = datetime.now(timezone.utc).isoformat()
        self.failures += 1
        self.detail = redact_sensitive(str(error))[:256]


def render_collector_health(health, *, dropped=0, truncated=0):
    rows = []
    for source, item in health.items():
        activity = ("events returned" if item.last_count else "no events returned") if item.status == "AVAILABLE" else "collection unavailable" if item.status == "UNAVAILABLE" else "waiting for first poll"
        rows.append(Text(f"{redact_sensitive(str(source))}: {item.status} / {activity}\n"
                         f"Last successful collection: {item.last_success or 'never'}; polls {item.polls}; events {item.events}; failures {item.failures}\n"
                         f"Last failure: {item.last_failure or 'none'} {item.detail}",
                         style=SUCCESS if item.status == "AVAILABLE" else WARNING))
    rows.append(Text(f"Rolling retention evictions: {dropped}; oversized lines truncated: {truncated}. Empty successful polls do not establish complete collection coverage.", style=MUTED))
    return TerminalPanel(Group(*rows), title=" COLLECTOR HEALTH ", border_style=ACCENT_SOFT, style=f"{NEUTRAL} on {SURFACE}")
