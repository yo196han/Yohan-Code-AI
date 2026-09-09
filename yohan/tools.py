"""
YOHAN CODE - Built-in Tools
Tools the agent can call: bash, read, write, ls, glob, search.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any
from yohan.sandbox import sandbox_exec, sandbox_write, sandbox_append, sandbox_read, sandbox_ls, resolve_sandbox_path


TOOL_DEFINITIONS = [
    {
        "name": "bash",
        "description": "Execute a shell command in the sandbox. Use for running code, installing packages, building projects.",
        "parameters": {
            "command": "The shell command to execute",
            "timeout": "Optional timeout in seconds (default: 30)",
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file in the sandbox.",
        "parameters": {
            "path": "Relative path to the file within sandbox-files/",
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the sandbox. Creates parent directories automatically.",
        "parameters": {
            "path": "Relative path to the file within sandbox-files/",
            "content": "The content to write",
        },
    },
    {
        "name": "append_file",
        "description": "Append content to a sandbox file. Use this to build large files in small chunks after write_file.",
        "parameters": {
            "path": "Relative path to the file within sandbox-files/",
            "content": "The content to append",
        },
    },
    {
        "name": "list_files",
        "description": "List files in the sandbox or a subdirectory.",
        "parameters": {
            "path": "Optional relative path (default: '.' for root of sandbox-files/)",
        },
    },
    {
        "name": "search_files",
        "description": "Search for a pattern in files within the sandbox.",
        "parameters": {
            "pattern": "Search pattern (regex or plain text)",
            "path": "Optional directory to search in (default: root of sandbox-files/)",
        },
    },
]


TOOL_NAME_ALIASES = {
    "terminal": "bash",
    "shell": "bash",
    "run_command": "bash",
    "exec": "bash",
    "create_file": "write_file",
    "create_files": "write_file",
    "write": "write_file",
    "append": "append_file",
    "add_to_file": "append_file",
    "read": "read_file",
    "ls": "list_files",
    "list": "list_files",
    "grep": "search_files",
    "glob": "search_files",
    "find": "search_files",
}


class ToolExecutor:
    def __init__(self, chat_id: str):
        self.chat_id = chat_id

    @staticmethod
    def _normalize_tool_name(tool_name: str) -> str:
        return TOOL_NAME_ALIASES.get(tool_name, tool_name)

    def execute(self, tool_name: str, params: dict) -> dict:
        """Execute a tool and return result."""
        tool_name = self._normalize_tool_name(tool_name)
        try:
            if tool_name == "bash":
                return self._bash(params)
            elif tool_name == "read_file":
                return self._read_file(params)
            elif tool_name == "write_file":
                return self._write_file(params)
            elif tool_name == "append_file":
                return self._append_file(params)
            elif tool_name == "list_files":
                return self._list_files(params)
            elif tool_name == "search_files":
                return self._search_files(params)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def _bash(self, params: dict) -> dict:
        command = params.get("command", "")
        timeout = int(params.get("timeout", 30))
        result = sandbox_exec(self.chat_id, command, timeout=timeout)
        return {
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
            "cwd": result["cwd"],
        }

    def _read_file(self, params: dict) -> dict:
        path = params.get("path", "")
        content = sandbox_read(self.chat_id, path)
        if content is None:
            return {"error": f"File not found: {path}"}
        return {"content": content, "path": path}

    def _write_file(self, params: dict) -> dict:
        path = params.get("path", "")
        content = params.get("content", "")
        target = sandbox_write(self.chat_id, path, content)
        return {"ok": True, "path": str(target)}

    def _append_file(self, params: dict) -> dict:
        path = params.get("path", "")
        content = params.get("content", "")
        target = sandbox_append(self.chat_id, path, content)
        return {"ok": True, "path": str(target), "appended": len(content)}

    def _list_files(self, params: dict) -> dict:
        path = params.get("path", ".")
        files = sandbox_ls(self.chat_id, path)
        return {"files": files, "count": len(files)}

    def _search_files(self, params: dict) -> dict:
        pattern = params.get("pattern", "")
        search_path = params.get("path", ".")

        from yohan.sandbox import get_sandbox_files, resolve_sandbox_path
        base = resolve_sandbox_path(self.chat_id, search_path)

        matches = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        for filepath in sorted(base.rglob("*")):
            if filepath.is_file():
                try:
                    text = filepath.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(text.splitlines(), 1):
                        if regex.search(line):
                            rel = str(filepath.relative_to(get_sandbox_files(self.chat_id)))
                            matches.append({
                                "file": rel,
                                "line": i,
                                "content": line.strip(),
                            })
                except Exception:
                    continue

        return {"matches": matches, "count": len(matches)}


def format_tool_result(tool_name: str, result: dict) -> str:
    """Format tool result for display."""
    if "error" in result:
        return f"[tool:{tool_name}] Error: {result['error']}"

    if tool_name == "bash":
        out = []
        if result.get("stdout"):
            out.append(result["stdout"].rstrip())
        if result.get("stderr"):
            out.append(f"[stderr] {result['stderr'].rstrip()}")
        if result.get("returncode", 0) != 0:
            out.append(f"[exit code: {result['returncode']}]")
        return "\n".join(out) if out else "[no output]"

    if tool_name == "read_file":
        return result.get("content") or ""

    if tool_name == "write_file":
        return f"✓ Written to {result.get('path', '')}"

    if tool_name == "append_file":
        return f"✓ Appended to {result.get('path', '')} ({result.get('appended', 0)} chars)"

    if tool_name == "list_files":
        files = result.get("files", [])
        if not files:
            return "(empty)"
        return "\n".join(files)

    if tool_name == "search_files":
        matches = result.get("matches", [])
        if not matches:
            return "(no matches)"
        return "\n".join(f"{m['file']}:{m['line']}: {m['content']}" for m in matches)

    return str(result)
