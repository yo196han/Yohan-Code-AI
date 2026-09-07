"""
YOHAN CODE - Terminal Display
Claude Code style UI using Rich.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from rich.theme import Theme

# ─── Theme ───────────────────────────────────────────────────────────────────

YOHAN_THEME = Theme({
    "yohan.primary":   "bold #A855F7",   # Purple - brand color
    "yohan.secondary": "dim #7C3AED",
    "yohan.success":   "bold green",
    "yohan.error":     "bold red",
    "yohan.warning":   "bold yellow",
    "yohan.info":      "cyan",
    "yohan.dim":       "dim white",
    "yohan.tool":      "bold #F59E0B",   # Amber for tool calls
    "yohan.user":      "bold #10B981",   # Green for user
    "yohan.model":     "bold #A855F7",   # Purple for AI
    "yohan.sandbox":   "bold #3B82F6",   # Blue for sandbox
    "yohan.skill":     "bold #EC4899",   # Pink for skills
    "yohan.key":       "bold #EF4444",   # Red for key errors
})

console = Console(theme=YOHAN_THEME)


# ─── Banner ──────────────────────────────────────────────────────────────────

def print_banner(version: str, provider: str, model: str, chat_id: str):
    banner = Text()
    banner.append("  ██╗   ██╗ ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗   ██████╗  ██████╗  ██████╗  ███████╗\n", style="bold #A855F7")
    banner.append("  ╚██╗ ██╔╝██╔═══██╗██║  ██║██╔══██╗████╗  ██║  ██╔════╝ ██╔═══██╗██╔══██╗ ██╔════╝\n", style="bold #9333EA")
    banner.append("   ╚████╔╝ ██║   ██║███████║███████║██╔██╗ ██║  ██║      ██║   ██║██║  ██║ █████╗  \n",  style="bold #7C3AED")
    banner.append("    ╚██╔╝  ██║   ██║██╔══██║██╔══██║██║╚██╗██║  ██║      ██║   ██║██║  ██║ ██╔══╝  \n",  style="bold #6D28D9")
    banner.append("     ██║   ╚██████╔╝██║  ██║██║  ██║██║ ╚████║  ╚██████╗ ╚██████╔╝██████╔╝ ███████╗\n", style="bold #5B21B6")
    banner.append("     ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═════╝  ╚═════╝ ╚═════╝  ╚══════╝\n", style="bold #4C1D95")
    banner.append(f"                                                                    v{version}\n", style="dim #6D28D9")

    info = Text()
    info.append(f"  Provider: ", style="dim")
    info.append(f"{provider}", style="yohan.primary")
    info.append(f"  │  Model: ", style="dim")
    info.append(f"{model}", style="yohan.info")
    info.append(f"\n  Session: ", style="dim")
    info.append(f"{chat_id}", style="yohan.sandbox")
    info.append(f"\n  Type ", style="dim")
    info.append("/help", style="yohan.primary")
    info.append(" for commands\n", style="dim")

    console.print()
    console.print(banner)
    console.print(info)
    console.print()


# ─── Prompts ─────────────────────────────────────────────────────────────────

def print_user_prefix():
    console.print()
    console.print(Text("  ◆ You", style="yohan.user"), end=" ")


def print_assistant_prefix(provider: str, model: str):
    console.print()
    label = Text()
    label.append("  ◈ YOHAN", style="yohan.model")
    label.append(f" [{model}]", style="dim")
    console.print(label)
    console.print()


def print_tool_call(tool_name: str, params: dict):
    console.print()
    label = Text()
    label.append("  ⚙  ", style="yohan.tool")
    label.append(f"{tool_name}", style="bold yohan.tool")

    # Show key params inline
    if params:
        short = ", ".join(
            f"{k}={repr(v)[:40]}" for k, v in list(params.items())[:2]
        )
        label.append(f"({short})", style="dim")

    console.print(label)


def print_action(verb: str, detail: str = "", note: str | None = None):
    """Claude Code style status line, e.g.:

        ⏺ Creating file src/App.tsx
        ⏺ Running command npm install
        ⏺ Updating file tailwind.config.js
    """
    line = Text()
    line.append("  ⏺ ", style="yohan.tool")
    line.append(verb, style="bold")
    if detail:
        line.append(f" {detail}", style="dim")
    if note:
        line.append(f"  {note}", style="yohan.success")
    console.print(line)


def print_tool_result(tool_name: str, result: dict, output: str):
    if not output or output == "[no output]":
        return
    lines = output.splitlines()
    if len(lines) > 20:
        preview = "\n".join(lines[:20]) + f"\n… ({len(lines) - 20} more lines)"
    else:
        preview = output

    console.print(
        Panel(
            Text(preview, style="dim"),
            title=Text(f"[{tool_name}]", style="yohan.tool"),
            border_style="dim #4B5563",
            padding=(0, 1),
        )
    )


def print_key_rotate(provider: str, remaining: int):
    console.print(
        Text(f"  ↻ Rotating API key ({remaining} remaining)…", style="dim yellow")
    )


def print_all_keys_exhausted(provider: str):
    console.print()
    console.print(
        Panel(
            Text(
                f"All API keys for {provider} are exhausted.\n"
                f"Add more keys to .env:  {provider.upper()}_API_N=your-key",
                style="yohan.key",
            ),
            border_style="red",
            title="[bold red]⚠  Rate Limit",
        )
    )


def print_response_stream(token: str):
    """Print a streaming token directly (no newline)."""
    console.print(f"  {token}", end="", markup=False)


def print_response_markdown(text: str):
    """Print full response as markdown."""
    try:
        md = Markdown(text)
        console.print(md, no_color=False)
    except Exception:
        console.print(text)


def print_error(msg: str):
    console.print(Text(f"\n  ✗ {msg}", style="yohan.error"))


def print_success(msg: str):
    console.print(Text(f"  ✓ {msg}", style="yohan.success"))


def print_info(msg: str):
    console.print(Text(f"  ℹ  {msg}", style="yohan.info"))


def print_warning(msg: str):
    console.print(Text(f"  ⚠  {msg}", style="yohan.warning"))


# ─── Help ────────────────────────────────────────────────────────────────────

def print_help():
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold #A855F7",
        border_style="dim",
        padding=(0, 2),
    )
    table.add_column("Command", style="yohan.primary", no_wrap=True)
    table.add_column("Description", style="white")

    commands = [
        ("/help",                     "Show this help"),
        ("/clear",                    "Clear conversation history"),
        ("/reset",                    "Reset session (new chat ID)"),
        ("/provider <name>",          "Switch AI provider"),
        ("/model <name>",             "Switch model"),
        ("/models",                   "List models for current provider"),
        ("/providers",                "List all available providers"),
        ("/skill add <path>",         "Install a skill from .md file"),
        ("/skill list",               "List installed skills"),
        ("/skill remove <name>",      "Remove a skill"),
        ("/skill show <name>",        "Show skill content"),
        ("/sandbox",                  "Show sandbox info"),
        ("/sandbox ls [path]",        "List sandbox files"),
        ("/sandbox exec <cmd>",       "Run command in sandbox"),
        ("/sandbox clear",            "Delete sandbox files (keep dir)"),
        ("/sandbox destroy",          "Delete entire sandbox"),
        ("/sandboxes",                "List all sandboxes"),
        ("/history",                  "Show conversation history"),
        ("/keys",                     "Show API key status"),
        ("/exit, /quit",              "Exit YOHAN CODE"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print()
    console.print(Panel(
        table,
        title="[bold #A855F7]YOHAN CODE — Commands",
        border_style="#A855F7",
        padding=(1, 2),
    ))
    console.print()


# ─── Skill display ───────────────────────────────────────────────────────────

def print_skills_table(skills: list[dict]):
    if not skills:
        print_info("No skills installed. Use /skill add <path> to install one.")
        return

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold #EC4899",
        border_style="dim",
        padding=(0, 2),
    )
    table.add_column("Name", style="yohan.skill", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Size", style="dim", justify="right")

    for s in skills:
        size = f"{s['size'] / 1024:.1f} KB"
        table.add_row(s["name"], s["description"][:60], size)

    console.print()
    console.print(Panel(
        table,
        title="[bold #EC4899]Installed Skills",
        border_style="#EC4899",
    ))
    console.print()


# ─── Provider/Model display ──────────────────────────────────────────────────

def print_providers_table(available: dict):
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold #A855F7",
        border_style="dim",
        padding=(0, 2),
    )
    table.add_column("ID", style="yohan.primary", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Keys", style="yohan.success", justify="right")
    table.add_column("Default Model", style="yohan.info")

    for pid, pconf in available.items():
        n_keys = len(pconf.get("keys", []))
        table.add_row(
            pid,
            pconf["name"],
            str(n_keys),
            pconf["default_model"],
        )

    console.print()
    console.print(Panel(
        table,
        title="[bold #A855F7]Available Providers",
        border_style="#A855F7",
    ))
    console.print()


def print_models_list(provider_id: str, models: list[str], current: str):
    console.print()
    console.print(Text(f"  Models for {provider_id}:", style="yohan.primary"))
    for m in models:
        if m == current:
            console.print(Text(f"  ● {m}", style="yohan.success"))
        else:
            console.print(Text(f"  ○ {m}", style="dim"))
    console.print()


# ─── Keys status ─────────────────────────────────────────────────────────────

def print_keys_status(provider_id: str, total: int, exhausted: int):
    available = total - exhausted
    status = "✓" if available > 0 else "✗"
    style = "yohan.success" if available > 0 else "yohan.error"
    console.print(
        Text(f"  {status} {provider_id}: {available}/{total} keys available", style=style)
    )


# ─── Sandbox info ────────────────────────────────────────────────────────────

def print_sandbox_info(info: dict):
    console.print()
    console.print(Panel(
        Text(
            f"Chat ID:  {info['chat_id']}\n"
            f"Root:     {info['root']}\n"
            f"Mnt:      {info['mnt']}\n"
            f"Files:    {info['files']}",
            style="yohan.sandbox",
        ),
        title="[bold #3B82F6]Sandbox",
        border_style="#3B82F6",
        padding=(1, 2),
    ))
    console.print()
