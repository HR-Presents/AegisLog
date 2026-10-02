from __future__ import annotations

from rich.text import Text

# Reference terminal palette: cyan headings, mint status, neutral borders and
# warm severity accents. All panels paint a dark surface independent of terminal defaults.
ACCENT = "#22C5DA"
ACCENT_SOFT = "#A0A0A0"
MUTED = "#A6A6A6"
SUCCESS = "#64FFDA"
INFO = "#22C5DA"
WARNING = "#FF981F"
HIGH = "#FF6268"
CRITICAL = "bold #FF3030"
INCIDENT = "#E5E5E5"
ANOMALY = "#FF981F"
NEUTRAL = "#E5E5E5"
DIM = "#454545"
SURFACE = "#080808"
TRACK = "#173F35"

SEVERITY_STYLES = {
    "CRITICAL": CRITICAL,
    "HIGH": HIGH,
    "MEDIUM": WARNING,
    "LOW": INFO,
    "INFO": MUTED,
}

RISK_STYLES = {
    "CRITICAL": CRITICAL,
    "HIGH": HIGH,
    "REVIEW": WARNING,
    "CLEAR": SUCCESS,
}


def severity_style(value: str) -> str:
    return SEVERITY_STYLES.get(value.upper(), NEUTRAL)


def risk_style(value: str) -> str:
    return RISK_STYLES.get(value.upper(), NEUTRAL)


def severity_text(value: str) -> Text:
    return Text(value, style=severity_style(value))


def risk_text(value: str) -> Text:
    return Text(value, style=f"bold {risk_style(value)}")
