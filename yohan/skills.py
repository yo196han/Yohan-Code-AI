"""
YOHAN CODE - Skills Manager
Skills live at: skills/<skill-name>/skill.md
"""

import os
import shutil
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def get_skill_dir(name: str) -> Path:
    return SKILLS_DIR / name


def get_skill_file(name: str) -> Path:
    return get_skill_dir(name) / "skill.md"


def install_skill(source_path: str) -> dict:
    """
    Install a skill from a .md file (drag & drop or path).
    The skill name = filename without extension.
    Places it at: skills/<name>/skill.md
    """
    src = Path(source_path.strip())

    if not src.exists():
        return {"ok": False, "error": f"File not found: {src}"}

    if src.suffix.lower() != ".md":
        return {"ok": False, "error": "Only .md files are supported"}

    skill_name = src.stem  # filename without extension
    skill_dir = get_skill_dir(skill_name)
    skill_file = skill_dir / "skill.md"

    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, skill_file)

    return {
        "ok": True,
        "name": skill_name,
        "path": str(skill_file),
        "overwritten": skill_file.exists(),
    }


def remove_skill(name: str) -> dict:
    """Remove a skill by name."""
    skill_dir = get_skill_dir(name)
    if not skill_dir.exists():
        return {"ok": False, "error": f"Skill '{name}' not found"}
    shutil.rmtree(skill_dir)
    return {"ok": True, "name": name}


def list_skills() -> list[dict]:
    """List all installed skills."""
    if not SKILLS_DIR.exists():
        return []
    skills = []
    for item in sorted(SKILLS_DIR.iterdir()):
        if item.is_dir():
            skill_file = item / "skill.md"
            if skill_file.exists():
                content = skill_file.read_text(encoding="utf-8")
                # Extract description from first non-empty line after frontmatter
                description = _extract_description(content)
                skills.append({
                    "name": item.name,
                    "path": str(skill_file),
                    "description": description,
                    "size": skill_file.stat().st_size,
                })
    return skills


def load_skill(name: str) -> str | None:
    """Load skill content by name."""
    skill_file = get_skill_file(name)
    if skill_file.exists():
        return skill_file.read_text(encoding="utf-8")
    return None


def load_all_skills() -> str:
    """Load all skills and combine them into a system prompt block."""
    skills = list_skills()
    if not skills:
        return ""

    blocks = []
    for skill in skills:
        content = load_skill(skill["name"])
        if content:
            blocks.append(
                f"<skill name=\"{skill['name']}\">\n{content}\n</skill>"
            )

    return "\n\n".join(blocks)


def skill_exists(name: str) -> bool:
    return get_skill_file(name).exists()


def _extract_description(content: str) -> str:
    """Extract a short description from skill.md content."""
    lines = content.splitlines()
    in_frontmatter = False
    frontmatter_done = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Handle YAML frontmatter
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and stripped == "---":
            in_frontmatter = False
            frontmatter_done = True
            continue
        if in_frontmatter:
            if stripped.startswith("description:"):
                return stripped[len("description:"):].strip().strip('"').strip("'")
            continue

        # After frontmatter, find first meaningful line
        if stripped and not stripped.startswith("#"):
            return stripped[:120]
        if stripped.startswith("#"):
            # Use heading text
            return stripped.lstrip("#").strip()[:120]

    return "No description"
