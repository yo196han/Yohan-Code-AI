"""
YOHAN CODE - Agent Loop
Manages conversation, tool calls, and streaming responses.
"""

import json
import re
from typing import Iterator, Callable
from yohan.providers import get_provider, AllKeysExhausted
from yohan.streamfilter import ToolCallStreamFilter
from yohan.tools import ToolExecutor, TOOL_DEFINITIONS, format_tool_result
from yohan.skills import load_all_skills
from yohan.sandbox import init_sandbox
from yohan.config import PROVIDERS


SYSTEM_PROMPT = """You are YOHAN CODE, an expert AI coding assistant running in the terminal.

You have access to a sandbox environment where you can:
- Execute shell commands (bash tool)
- Read and write files (read_file, write_file tools)
- List and search files (list_files, search_files tools)

== TOOL CALL FORMAT (CRITICAL - MUST FOLLOW EXACTLY) ==
When you need a tool, use EXACTLY this format. No markdown fences. No extra text around the JSON.

<tool_call>
{"tool": "tool_name", "params": {"param1": "value1"}}
</tool_call>

Example - run a command:
<tool_call>
{"tool": "bash", "params": {"command": "ls -la"}}
</tool_call>

Example - write a file:
<tool_call>
{"tool": "write_file", "params": {"path": "main.py", "content": "print('hello')"}}
</tool_call>

Example - read a file:
<tool_call>
{"tool": "read_file", "params": {"path": "main.py"}}
</tool_call>

Example - list files:
<tool_call>
{"tool": "list_files", "params": {"path": "."}}
</tool_call>

For normal conversation (no tool needed), reply in plain text only.
NEVER use json blocks or markdown fences for tool calls.
CRITICAL: Emit exactly ONE <tool_call> per response. Never batch multiple tool
calls in a single reply — write files one at a time, waiting for each result.
Keep prose minimal: at most 1-2 short sentences before or after a tool call.

After each tool result, continue reasoning and either call another tool or give your final answer.

Guidelines:
- Be precise and concise
- Show code with syntax highlighting using markdown fences
- Explain what you are doing before running commands
- If something fails, debug it and try again
- Ask for clarification only when truly necessary
- ALWAYS use the <tool_call> format when you need to run commands or write files
- Do NOT describe what you would do — actually use the tools to do it

{skills_block}

{tools_block}
"""

TOOLS_BLOCK = """Available tools:
""" + "\n".join(
    f"- **{t['name']}**: {t['description']} | params: {list(t['parameters'].keys())}"
    for t in TOOL_DEFINITIONS
)


class Agent:
    def __init__(
        self,
        chat_id: str,
        provider_id: str,
        model: str | None = None,
        on_token: Callable[[str], None] | None = None,
        on_tool_call: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, dict], None] | None = None,
        on_key_rotate: Callable[[str, int], None] | None = None,
    ):
        self.chat_id = chat_id
        self.provider_id = provider_id
        self.model = model or PROVIDERS[provider_id]["default_model"]
        self.history: list[dict] = []
        self.executor = ToolExecutor(chat_id)

        # Callbacks
        self.on_token = on_token or (lambda t: None)
        self.on_tool_call = on_tool_call or (lambda n, p: None)
        self.on_tool_result = on_tool_result or (lambda n, r: None)
        self.on_key_rotate = on_key_rotate or (lambda pid, n: None)

        # Init sandbox
        init_sandbox(chat_id)

    def _build_system(self) -> str:
        skills = load_all_skills()
        skills_block = f"<skills>\n{skills}\n</skills>" if skills else ""
        return (SYSTEM_PROMPT
                .replace("{skills_block}", skills_block)
                .replace("{tools_block}", TOOLS_BLOCK))

    def _extract_all_tool_calls(self, text: str) -> list[tuple[str, dict]]:
        """Extract ALL tool calls from a model response (handles batched calls).

        Models sometimes emit multiple tool calls in one response. We collect
        all of them so the loop can execute them sequentially before returning
        to the model.

        Formats handled (in priority order):
          1. <tool_call>...</tool_call>  tags  (preferred)
          2. ```json { "tool": ... } ```       (markdown fenced)
          3. Bare JSON blob with "tool" key    (llama-style fallback)
        """
        results: list[tuple[str, dict]] = []

        # ── 1. XML tags — find ALL occurrences ───────────────────────────────
        for match in re.finditer(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL):
            parsed = self._parse_tool_json(match.group(1))
            if parsed:
                results.append(parsed)
        if results:
            return results

        # ── 2. Markdown fenced JSON blocks ────────────────────────────────────
        for match in re.finditer(r"```(?:json)?[ \t]*\n?(\{.*?\})\n?```", text, re.DOTALL):
            parsed = self._parse_tool_json(match.group(1))
            if parsed:
                results.append(parsed)
        if results:
            return results

        # ── 3. Bare JSON blobs with "tool" key (llama-style) ─────────────────
        for match in re.finditer(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL):
            parsed = self._parse_tool_json(match.group(0))
            if parsed:
                results.append(parsed)

        return results

    def _has_incomplete_tool_call(self, text: str) -> bool:
        """Detect a truncated tool call — opening tag present but no closing tag.

        This happens when the model hits a token limit mid-JSON, leaving a
        dangling <tool_call> that _extract_all_tool_calls cannot parse.
        """
        open_tags  = len(re.findall(r"<tool_call>",  text))
        close_tags = len(re.findall(r"</tool_call>", text))
        if open_tags > close_tags:
            return True
        # Also catch a fenced block that opened but never closed
        open_fences  = len(re.findall(r"```(?:json)?[ \t]*\n", text))
        close_fences = len(re.findall(r"\n```", text))
        if open_fences > close_fences:
            return True
        return False

    @staticmethod
    def _looks_like_tool_attempt(text: str) -> bool:
        """Heuristic: the model TRIED to emit a tool call but the result was
        not parseable (bare/fenced JSON without XML tags, truncated blob...).
        Committing such garbage to history derails every later turn, so the
        caller treats it like a truncation and re-asks the model."""
        if re.search(r'"tool"\s*:', text):
            return True
        if "<tool" in text or "tool_call" in text:
            return True
        return False

    @staticmethod
    def _strip_partial_tool_call(text: str) -> str:
        """Remove a dangling partial tool call so broken JSON never enters
        conversation history. Complete responses pass through untouched."""
        if text.count("<tool_call>") > text.count("</tool_call>"):
            cut = text.rfind("<tool_call>")
            if cut != -1:
                return text[:cut]
        # Truncated bare/fenced JSON that mentions params — only cut when it
        # clearly never finished (no closing brace at the end), so a final
        # answer merely *discussing* tool syntax is left alone.
        if "</tool_call>" not in text:
            m = re.search(r'\{[^{}]*"tool"\s*:', text)
            if m and '"params"' in text[m.start():] \
                    and not text.rstrip().endswith("}"):
                return text[:m.start()]
        return text

    def _parse_tool_json(self, raw: str) -> tuple[str, dict] | None:
        """Parse a JSON blob into (tool_name, params), tolerating key variants."""
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            # Try stripping a leading/trailing markdown fence that slipped in
            cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
                return None

        if not isinstance(data, dict):
            return None

        # Accept "tool" or "name" as the tool-name key
        name = data.get("tool") or data.get("name")
        # Accept "params" or "parameters" as the params key
        params = data.get("params") or data.get("parameters") or data.get("arguments") or {}

        if not name:
            return None

        return name, params

    def chat(self, user_message: str, max_iterations: int = 10) -> str:
        """Process a user message, handle tool calls, return final response."""
        self.history.append({"role": "user", "content": user_message})

        provider     = get_provider(self.provider_id)
        full_response = ""
        iterations   = 0
        incomplete_retries = 0
        MAX_INCOMPLETE_RETRIES = 2

        while iterations < max_iterations:
            iterations += 1
            full_response = ""

            # ── Stream from provider ──────────────────────────────────────────
            stream_filter = ToolCallStreamFilter()
            try:
                for token in provider.chat(
                    messages=self.history,
                    model=self.model,
                    stream=True,
                    system=self._build_system(),
                ):
                    token = str(token)
                    full_response += token          # full text kept for parsing
                    visible = stream_filter.feed(token)
                    if visible:
                        self.on_token(visible)      # user never sees raw tool JSON
                tail = stream_filter.flush()
                if tail:
                    self.on_token(tail)

            except AllKeysExhausted as e:
                error_msg = str(e)
                self.on_token(f"\n\n⚠️  {error_msg}\n")
                return error_msg

            # ── Detect truncated / malformed tool call ────────────────────────
            extracted = self._extract_all_tool_calls(full_response)
            malformed = (
                self._has_incomplete_tool_call(full_response)
                or (not extracted
                    and self._looks_like_tool_attempt(full_response))
            )
            if malformed:
                if incomplete_retries < MAX_INCOMPLETE_RETRIES:
                    incomplete_retries += 1
                    self.on_token(
                        f"\n\n⚠️  [tool call cut off — re-asking model ({incomplete_retries}/{MAX_INCOMPLETE_RETRIES})]\n"
                    )
                    # Never commit a dangling partial tool call to history:
                    # the broken JSON derails every later turn (the model
                    # starts quoting/"fixing" its own garbage). Keep only
                    # clean prose and ask for a compact re-send — continuing
                    # mid-JSON does not work reliably, especially on Gemini.
                    clean = self._strip_partial_tool_call(full_response)
                    if clean.strip():
                        self.history.append({"role": "assistant", "content": clean})
                    self.history.append({
                        "role": "user",
                        "content": (
                            "Your tool call did not finish (output token "
                            "limit). Send the SAME tool call again, COMPLETE "
                            "and COMPACT, as one <tool_call>...</tool_call> "
                            "block with no prose before or after. If the file "
                            "content is long, write a shorter working version "
                            "instead of a truncated one."
                        ),
                    })
                    iterations -= 1  # Don't count this as a real iteration
                    continue
                else:
                    # Retries exhausted — keep history clean and stop.
                    self.on_token("\n\n⚠️  [tool call failed after retries — skipping]\n")
                    clean = self._strip_partial_tool_call(full_response)
                    if clean.strip():
                        self.history.append({"role": "assistant", "content": clean})
                    return full_response

            # Reset retry counter on a clean response
            incomplete_retries = 0

            # ── Tool calls extracted above ────────────────────────────────────
            tool_calls = extracted

            if tool_calls:
                # Record the assistant turn once (contains all tool call text)
                self.history.append({
                    "role": "assistant",
                    "content": full_response,
                })

                # Execute every tool call; bundle all results into one user message
                result_parts: list[str] = []
                for tool_name, tool_params in tool_calls:
                    self.on_tool_call(tool_name, tool_params)
                    result = self.executor.execute(tool_name, tool_params)
                    self.on_tool_result(tool_name, result)
                    formatted = format_tool_result(tool_name, result)
                    result_parts.append(
                        f"<tool_result tool=\"{tool_name}\">\n{formatted}\n</tool_result>"
                    )

                self.history.append({
                    "role": "user",
                    "content": "\n\n".join(result_parts),
                })
                continue  # Back to model with results

            else:
                # No tool calls → final response
                self.history.append({
                    "role": "assistant",
                    "content": full_response,
                })
                return full_response

        # Max iterations reached
        self.history.append({"role": "assistant", "content": full_response})
        return full_response

    def reset(self):
        """Clear conversation history."""
        self.history = []

    def switch_provider(self, provider_id: str, model: str | None = None):
        self.provider_id = provider_id
        self.model = model or PROVIDERS[provider_id]["default_model"]

    def switch_model(self, model: str):
        self.model = model
