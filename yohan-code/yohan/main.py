"""
YOHAN CODE - Main CLI Entry Point
Claude Code style REPL interface.
"""

import sys
import uuid
import signal
import argparse
from pathlib import Path

# ─── Graceful ctrl+c ─────────────────────────────────────────────────────────
_current_stream = None

def _sigint_handler(sig, frame):
    global _current_stream
    if _current_stream:
        _current_stream = None
        print("\n")
    else:
        print("\n  (Press Ctrl+C again or type /exit to quit)")

signal.signal(signal.SIGINT, _sigint_handler)


# ─── Imports (after signal setup) ────────────────────────────────────────────
from yohan import __version__, __app_name__
from yohan.config import get_default_provider, get_all_available_providers, PROVIDERS
from yohan.agent import Agent
from yohan.commands import handle_command, CommandResult
from yohan.sandbox import init_sandbox
from yohan import display


def generate_chat_id() -> str:
    return str(uuid.uuid4())[:8]


def make_agent(chat_id: str, provider_id: str, model: str | None) -> Agent:
    """Create agent with display callbacks."""
    response_buffer = []

    def on_token(token: str):
        global _current_stream
        _current_stream = True
        print(token, end="", flush=True)
        response_buffer.append(token)

    def on_tool_call(name: str, params: dict):
        print()  # newline after streaming
        display.print_tool_call(name, params)

    def on_tool_result(name: str, result: dict):
        from yohan.tools import format_tool_result
        output = format_tool_result(name, result)
        display.print_tool_result(name, result, output)

    def on_key_rotate(provider: str, remaining: int):
        display.print_key_rotate(provider, remaining)

    return Agent(
        chat_id=chat_id,
        provider_id=provider_id,
        model=model,
        on_token=on_token,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_key_rotate=on_key_rotate,
    )


def run_repl(provider_id: str, model: str | None, chat_id: str | None = None):
    """Main REPL loop."""
    global _current_stream

    chat_id = chat_id or generate_chat_id()
    available = get_all_available_providers()

    if not available:
        display.print_error(
            "No API keys configured. Copy .env.example to .env and add your keys."
        )
        sys.exit(1)

    if provider_id not in available:
        # Fall back to first available
        provider_id = list(available.keys())[0]

    effective_model = model or PROVIDERS[provider_id]["default_model"]
    agent = make_agent(chat_id, provider_id, model)

    display.print_banner(__version__, PROVIDERS[provider_id]["name"], agent.model, chat_id)

    # REPL
    while True:
        try:
            display.console.print()
            user_input = display.console.input("[bold #10B981]  ◆ [/]").strip()
        except (EOFError, KeyboardInterrupt):
            display.print_info("Goodbye!")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────────────────────────────
        if user_input.startswith("/"):
            result = handle_command(user_input, agent)

            if result.action == "exit":
                break

            elif result.action == "reset":
                chat_id = generate_chat_id()
                agent = make_agent(chat_id, agent.provider_id, agent.model)
                display.print_success(f"New session: {chat_id}")

            elif result.action == "switch_provider":
                pid = result.data["provider_id"]
                m = result.data.get("model")
                agent.switch_provider(pid, m)
                display.print_success(
                    f"Switched to {PROVIDERS[pid]['name']} / {agent.model}"
                )

            elif result.action == "switch_model":
                agent.switch_model(result.data["model"])
                display.print_success(f"Switched to model: {agent.model}")

            continue

        # ── AI message ────────────────────────────────────────────────────────
        display.print_assistant_prefix(agent.provider_id, agent.model)
        print("  ", end="", flush=True)

        try:
            _current_stream = True
            agent.chat(user_input)
            _current_stream = None
            print()  # newline after stream ends
        except KeyboardInterrupt:
            _current_stream = None
            print("\n")
            display.print_warning("Interrupted.")
        except Exception as e:
            _current_stream = None
            display.print_error(str(e))


def main():
    parser = argparse.ArgumentParser(
        prog="yohan",
        description="YOHAN CODE - AI Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  yohan                          Start with default provider
  yohan --provider groq          Start with Groq
  yohan --provider gemini --model gemini-1.5-pro
  yohan --chat-id abc123         Resume a session
  yohan --list-providers         Show available providers
  yohan --list-models groq       Show models for a provider
        """,
    )

    parser.add_argument(
        "--provider", "-p",
        help="AI provider to use (groq, gemini, cloudflare, openrouter, openai, anthropic, mistral, cohere)",
    )
    parser.add_argument(
        "--model", "-m",
        help="Model to use (depends on provider)",
    )
    parser.add_argument(
        "--chat-id", "-c",
        help="Resume an existing chat session by ID",
    )
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List all configured providers and exit",
    )
    parser.add_argument(
        "--list-models",
        metavar="PROVIDER",
        help="List models for a provider and exit",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args()

    if args.version:
        print(f"{__app_name__} v{__version__}")
        sys.exit(0)

    if args.list_providers:
        available = get_all_available_providers()
        if not available:
            print("No providers configured.")
        else:
            display.print_providers_table(available)
        sys.exit(0)

    if args.list_models:
        pid = args.list_models.lower()
        if pid not in PROVIDERS:
            print(f"Unknown provider: {pid}")
            sys.exit(1)
        models = PROVIDERS[pid]["models"]
        print(f"\nModels for {pid}:")
        for m in models:
            print(f"  {m}")
        print()
        sys.exit(0)

    provider_id = (args.provider or get_default_provider() or "groq").lower()
    run_repl(
        provider_id=provider_id,
        model=args.model,
        chat_id=args.chat_id,
    )


if __name__ == "__main__":
    main()
