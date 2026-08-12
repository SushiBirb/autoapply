from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def info(msg: str) -> None:
    console.print(msg, style="cyan")


def success(msg: str) -> None:
    console.print(msg, style="green")


def warn(msg: str) -> None:
    console.print(msg, style="yellow")


def error(msg: str) -> None:
    console.print(msg, style="red bold")


def ask(prompt: str, default: str | None = None, password: bool = False) -> str:
    suffix = f" [dim]\\[{default}][/dim]" if default else ""
    value = Prompt.ask(f"{prompt}{suffix}", default=default or "", password=password)
    return value.strip()


def ask_multiline(prompt: str, default: str | None = None) -> str:
    console.print(f"[bold]{prompt}[/bold]")
    if default:
        console.print(f"[dim]default:\\n{default}\\n[/dim]")
    console.print("[dim](Enter=blank line, then type END on its own line to finish)[/dim]")
    lines: list[str] = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    text = "\\n".join(lines).strip()
    return text if text else (default or "")


def confirm(prompt: str, default: bool = True) -> bool:
    return Confirm.ask(prompt, default=default)


def section(title: str) -> None:
    console.rule(f"[bold blue]{title}")
