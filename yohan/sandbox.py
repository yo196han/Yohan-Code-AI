"""
YOHAN CODE - Sandbox Manager
Per-chat isolated filesystem.
Structure: <script_dir>/sandbox-<chat_id>/mnt/sandbox-files/
"""

import os
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).parent.parent.resolve()


def get_sandbox_root(chat_id: str) -> Path:
    return SCRIPT_DIR / f"sandbox-{chat_id}"


def get_sandbox_mnt(chat_id: str) -> Path:
    return get_sandbox_root(chat_id) / "mnt"


def get_sandbox_files(chat_id: str) -> Path:
    return get_sandbox_root(chat_id) / "mnt" / "sandbox-files"


def init_sandbox(chat_id: str) -> dict:
    root = get_sandbox_root(chat_id)
    mnt = get_sandbox_mnt(chat_id)
    files = get_sandbox_files(chat_id)
    created = not root.exists()

    files.mkdir(parents=True, exist_ok=True)

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")

    meta = root / ".sandbox_meta"
    if not meta.exists():
        meta.write_text(json.dumps({
            "chat_id": chat_id,
            "created_at": time.time(),
            "version": "1.0",
        }, indent=2))

    return {
        "chat_id": chat_id,
        "root": str(root),
        "mnt": str(mnt),
        "files": str(files),
        "created": created,
    }


def destroy_sandbox(chat_id: str, confirm: bool = False) -> bool:
    if not confirm:
        return False
    root = get_sandbox_root(chat_id)
    if root.exists():
        shutil.rmtree(root)
        return True
    return False


def list_sandboxes() -> list[dict]:
    sandboxes = []
    if not SCRIPT_DIR.exists():
        return sandboxes
    for item in SCRIPT_DIR.iterdir():
        if item.is_dir() and item.name.startswith("sandbox-"):
            chat_id = item.name[len("sandbox-"):]
            meta_file = item / ".sandbox_meta"
            meta = {}
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text())
                except Exception:
                    pass
            sandboxes.append({
                "chat_id": chat_id,
                "path": str(item),
                "meta": meta,
            })
    return sandboxes


def sandbox_exec(chat_id: str, command: str, timeout: int = 30) -> dict:
    files_dir = get_sandbox_files(chat_id)
    if not files_dir.exists():
        init_sandbox(chat_id)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(files_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                **os.environ,
                "SANDBOX_ROOT": str(get_sandbox_root(chat_id)),
                "SANDBOX_MNT": str(get_sandbox_mnt(chat_id)),
                "SANDBOX_FILES": str(files_dir),
                "HOME": str(files_dir),
            },
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "cwd": str(files_dir),
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": -1, "cwd": str(files_dir)}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "cwd": str(files_dir)}


def sandbox_write(chat_id: str, relative_path: str, content: str) -> Path:
    target = resolve_sandbox_path(chat_id, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def sandbox_append(chat_id: str, relative_path: str, content: str) -> Path:
    target = resolve_sandbox_path(chat_id, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(content)
    return target


def sandbox_read(chat_id: str, relative_path: str) -> Optional[str]:
    target = resolve_sandbox_path(chat_id, relative_path)
    if target.exists():
        return target.read_text(encoding="utf-8")
    return None


def sandbox_ls(chat_id: str, relative_path: str = ".") -> list[str]:
    files_dir = get_sandbox_files(chat_id)
    target = resolve_sandbox_path(chat_id, relative_path)
    if not target.exists():
        return []
    return [str(p.relative_to(files_dir)) for p in sorted(target.rglob("*")) if p.is_file()]


def resolve_sandbox_path(chat_id: str, relative_path: str) -> Path:
    files_dir = get_sandbox_files(chat_id)
    resolved = (files_dir / relative_path).resolve()
    if not str(resolved).startswith(str(files_dir)):
        raise PermissionError(f"Path traversal detected: {relative_path}")
    return resolved
