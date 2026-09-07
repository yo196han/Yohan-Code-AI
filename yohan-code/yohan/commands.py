"""
YOHAN CODE - Commands Handler
Handles all /commands entered by the user.
"""

import shutil
import sys
from pathlib import Path
from yohan import display
from yohan.config import PROVIDERS, get_all_available_providers
from yohan.skills import install_skill, remove_skill, list_skills, load_skill, skill_exists
from yohan.sandbox import (
    init_sandbox, destroy_sandbox, list_sandboxes,
    sandbox_exec, sandbox_ls, get_sandbox_files
)


class CommandResult:
    def __init__(self, action: str = "none", data: dict = None):
        self.action = action   # none, exit, reset, switch_provider, switch_model, clear_history
        self.data = data or {}


def handle_command(cmd_line: str, agent) -> CommandResult:
    """Parse and handle a /command. Returns action for the CLI to act on."""
    parts = cmd_line.strip().split()
    if not parts:
        return CommandResult()

    cmd = parts[0].lower()
    args = parts[1:]

    # ── Exit ──────────────────────────────────────────────────────────────────
    if cmd in ("/exit", "/quit", "/q"):
        display.print_info("Goodbye!")
        return CommandResult("exit")

    # ── Help ──────────────────────────────────────────────────────────────────
    elif cmd == "/help":
        display.print_help()

    # ── Clear history ─────────────────────────────────────────────────────────
    elif cmd == "/clear":
        agent.reset()
        display.print_success("Conversation cleared.")

    # ── Reset session ─────────────────────────────────────────────────────────
    elif cmd == "/reset":
        return CommandResult("reset")

    # ── History ───────────────────────────────────────────────────────────────
    elif cmd == "/history":
        history = agent.history
        if not history:
            display.print_info("No history.")
        else:
            from rich.console import Console
            from rich.text import Text
            c = display.console
            c.print()
            for i, msg in enumerate(history):
                role_style = "yohan.user" if msg["role"] == "user" else "yohan.model"
                role_label = "You" if msg["role"] == "user" else "YOHAN"
                c.print(Text(f"  [{i+1}] {role_label}:", style=role_style))
                content = msg["content"][:300]
                if len(msg["content"]) > 300:
                    content += "…"
                c.print(f"  {content}")
                c.print()

    # ── Provider ──────────────────────────────────────────────────────────────
    elif cmd == "/provider":
        if not args:
            display.print_info(f"Current provider: {agent.provider_id}")
        else:
            pid = args[0].lower()
            available = get_all_available_providers()
            if pid not in PROVIDERS:
                display.print_error(f"Unknown provider: {pid}")
                display.print_info(f"Available: {', '.join(PROVIDERS.keys())}")
            elif pid not in available:
                display.print_error(f"No API keys found for: {pid}")
                display.print_info(f"Add {PROVIDERS[pid]['env_prefix']}_1=your-key to .env")
            else:
                return CommandResult("switch_provider", {"provider_id": pid, "model": None})

    # ── Providers list ────────────────────────────────────────────────────────
    elif cmd == "/providers":
        available = get_all_available_providers()
        if not available:
            display.print_error("No providers configured. Add API keys to .env")
        else:
            display.print_providers_table(available)

    # ── Model ─────────────────────────────────────────────────────────────────
    elif cmd == "/model":
        if not args:
            display.print_info(f"Current model: {agent.model}")
        else:
            model = args[0]
            return CommandResult("switch_model", {"model": model})

    # ── Models list ───────────────────────────────────────────────────────────
    elif cmd == "/models":
        pid = args[0].lower() if args else agent.provider_id
        if pid not in PROVIDERS:
            display.print_error(f"Unknown provider: {pid}")
        else:
            display.print_info(f"Fetching models from {PROVIDERS[pid]['name']} API...")
            from yohan.providers import fetch_models
            live_models = fetch_models(pid)
            if live_models:
                display.print_models_list(pid, live_models, agent.model)
            else:
                # Fallback to config
                models = PROVIDERS[pid]["models"]
                display.print_models_list(pid, models, agent.model)

    # ── Skills ────────────────────────────────────────────────────────────────
    elif cmd == "/skill":
        if not args:
            display.print_help()
            return CommandResult()

        sub = args[0].lower()

        if sub == "add":
            if not args[1:]:
                display.print_error("Usage: /skill add <path-to-skill.md>")
            else:
                path = " ".join(args[1:]).strip().strip("'\"")
                result = install_skill(path)
                if result["ok"]:
                    action = "overwritten" if result.get("overwritten") else "installed"
                    display.print_success(f"Skill '{result['name']}' {action} → {result['path']}")
                else:
                    display.print_error(result["error"])

        elif sub == "list":
            skills = list_skills()
            display.print_skills_table(skills)

        elif sub == "remove":
            if not args[1:]:
                display.print_error("Usage: /skill remove <name>")
            else:
                name = args[1]
                result = remove_skill(name)
                if result["ok"]:
                    display.print_success(f"Skill '{name}' removed.")
                else:
                    display.print_error(result["error"])

        elif sub == "show":
            if not args[1:]:
                display.print_error("Usage: /skill show <name>")
            else:
                name = args[1]
                content = load_skill(name)
                if content:
                    from rich.syntax import Syntax
                    display.console.print(Syntax(content, "markdown", theme="monokai"))
                else:
                    display.print_error(f"Skill '{name}' not found.")
        else:
            display.print_error(f"Unknown skill subcommand: {sub}")

    # ── Sandbox ───────────────────────────────────────────────────────────────
    elif cmd == "/sandbox":
        if not args:
            info = init_sandbox(agent.chat_id)
            display.print_sandbox_info(info)

        elif args[0].lower() == "ls":
            path = args[1] if len(args) > 1 else "."
            files = sandbox_ls(agent.chat_id, path)
            if not files:
                display.print_info("(empty)")
            else:
                for f in files:
                    display.console.print(f"  {f}", style="dim")

        elif args[0].lower() == "exec":
            if not args[1:]:
                display.print_error("Usage: /sandbox exec <command>")
            else:
                cmd_str = " ".join(args[1:])
                result = sandbox_exec(agent.chat_id, cmd_str)
                if result["stdout"]:
                    display.console.print(result["stdout"])
                if result["stderr"]:
                    display.console.print(result["stderr"], style="red")

        elif args[0].lower() == "clear":
            files_dir = get_sandbox_files(agent.chat_id)
            if files_dir.exists():
                for item in files_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            display.print_success("Sandbox files cleared.")

        elif args[0].lower() == "destroy":
            result = destroy_sandbox(agent.chat_id, confirm=True)
            if result:
                display.print_success(f"Sandbox {agent.chat_id} destroyed.")
                return CommandResult("reset")
            else:
                display.print_error("Failed to destroy sandbox.")
        else:
            display.print_error(f"Unknown sandbox subcommand: {args[0]}")

    # ── Sandboxes list ────────────────────────────────────────────────────────
    elif cmd == "/sandboxes":
        sandboxes = list_sandboxes()
        if not sandboxes:
            display.print_info("No sandboxes found.")
        else:
            display.console.print()
            for s in sandboxes:
                display.console.print(
                    f"  [bold #3B82F6]{s['chat_id']}[/]  →  {s['path']}",
                    highlight=False,
                )
            display.console.print()

    # ── Keys status ───────────────────────────────────────────────────────────
    elif cmd == "/keys":
        from yohan.providers import get_provider
        display.console.print()
        for pid in PROVIDERS:
            from yohan.config import load_keys
            keys = load_keys(pid)
            if keys:
                provider = get_provider(pid)
                exhausted = len(provider.rotator._exhausted)
                display.print_keys_status(pid, len(keys), exhausted)
        display.console.print()

    else:
        display.print_error(f"Unknown command: {cmd}  (type /help for commands)")

    return CommandResult()
