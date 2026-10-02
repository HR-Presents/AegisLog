"""Keyboard navigation without blocking live rendering or changing source data."""
from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar

from rich.prompt import Prompt as RichPrompt


class WorkspaceBack(BaseException):
    """Unwind the current workspace to the menu."""


class WorkspaceQuit(SystemExit):
    def __init__(self):
        super().__init__(0)


_interactive_shell = ContextVar("aegislog_interactive_shell", default=False)


@contextmanager
def shell_navigation():
    token = _interactive_shell.set(True)
    try:
        yield
    finally:
        _interactive_shell.reset(token)


class Prompt(RichPrompt):
    @classmethod
    def ask(cls, prompt="", **kwargs):
        if not _interactive_shell.get():
            return super().ask(prompt, **kwargs)
        choices = kwargs.pop("choices", None)
        while True:
            value = super().ask(f"{prompt}  [dim][B Back] [Q Quit][/dim]", **kwargs)
            if value.strip().lower() in {"q", "quit", "exit"}:
                raise WorkspaceQuit()
            if value.strip().lower() in {"b", "back", "cancel"}:
                raise WorkspaceBack()
            if choices is None:
                return value
            selected = next((choice for choice in choices if choice.casefold() == value.casefold()), None)
            if selected is not None:
                return selected
            target = kwargs.get("console")
            if target is None:
                from rich import get_console
                target = get_console()
            target.print("Choose: " + ", ".join(choices), style="yellow")


class KeyboardReader:
    """Poll a real terminal, restoring POSIX terminal settings on every exit."""
    def __enter__(self):
        self.enabled = False
        self.saved = None
        if not sys.stdin.isatty():
            return self
        try:
            if os.name == "nt":
                import msvcrt
                self.windows = msvcrt
            else:
                import termios
                import tty
                self.fd = sys.stdin.fileno()
                self.saved = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
            self.enabled = True
        except (OSError, ValueError, ImportError):
            pass
        return self

    def __exit__(self, *args):
        if self.saved is not None:
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)

    def poll(self):
        if not self.enabled:
            return None
        if os.name == "nt":
            if not self.windows.kbhit():
                return None
            char = self.windows.getwch()
            if char in {"\x00", "\xe0"}:
                self.windows.getwch()
                return None
            return char
        import select
        if select.select([self.fd], [], [], 0)[0]:
            return os.read(self.fd, 1).decode("utf-8", errors="replace")
        return None


def wait_for_navigation(reader, seconds, *, sleep=time.sleep):
    if not reader.enabled:
        sleep(seconds)
        return
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        key = reader.poll()
        if key and key.lower() in {"q", "\x04"}:
            raise WorkspaceQuit()
        if key and key.lower() in {"b", "\x1b", "\x03"}:
            raise KeyboardInterrupt()
        sleep(min(0.05, max(0, deadline - time.monotonic())))
