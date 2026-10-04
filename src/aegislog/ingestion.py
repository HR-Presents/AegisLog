"""Bounded binary line ingestion; oversized tails are discarded before decoding."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class InputLine:
    text: str
    truncated: bool


def iter_bounded_lines(path: Path, max_line_bytes: int = 1_000_000, *, on_bytes=None, cancel=None) -> Iterator[InputLine]:
    if max_line_bytes < 1:
        raise ValueError("max_line_bytes must be positive")
    with path.open("rb") as handle:
        while True:
            if cancel:
                cancel()
            raw = handle.readline(max_line_bytes + 2)
            if not raw:
                return
            if on_bytes:
                on_bytes(raw)
            content = raw.rstrip(b"\r\n")
            truncated = len(content) > max_line_bytes
            if not raw.endswith(b"\n") and len(raw) > max_line_bytes:
                truncated = True
                while True:
                    if cancel:
                        cancel()
                    tail = handle.readline(64 * 1024)
                    if on_bytes and tail:
                        on_bytes(tail)
                    if not tail or tail.endswith(b"\n"):
                        break
            text = content[:max_line_bytes].decode("utf-8", errors="replace")
            if truncated:
                text += " [TRUNCATED]"
            yield InputLine(text, truncated)
