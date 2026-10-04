from __future__ import annotations

from .cli import app
from .commands import register_commands, start
from .console_pages import system_check
from .product import guided_check
from .support_commands import register as register_support


def _remove_ai_surface() -> None:
    """Remove legacy AI/provider commands from the public executable surface."""
    retained = []
    for command in app.registered_commands:
        callback = getattr(command, "callback", None)
        callback_name = getattr(callback, "__name__", "")
        if callback_name in {"ask_log", "config", "doctor"}:
            continue
        retained.append(command)
    app.registered_commands = retained


_remove_ai_surface()
register_commands(app)
app.command("doctor")(system_check)


def check_computer_command():
    """Discover native logs and perform a guided read-only check."""
    from rich.console import Console
    from .navigation import WorkspaceBack, WorkspaceQuit, shell_navigation
    try:
        with shell_navigation():
            guided_check(Console())
    except (WorkspaceBack, WorkspaceQuit):
        return


app.command("check-computer")(check_computer_command)
register_support(app)

__all__ = ["app", "start"]
