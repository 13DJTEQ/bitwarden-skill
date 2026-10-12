"""Tests for the bitwarden-skill repo.

Covers skill structure (frontmatter, file layout, script validity) without
any live `bw` calls or network access.
"""
import re
from pathlib import Path

import pytest
import hermes_yaml as yaml

REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO
SKILL_MD = SKILL_DIR / "SKILL.md"
SCRIPT = SKILL_DIR / "scripts" / "bw-unlock.sh"


def _frontmatter():
    content = SKILL_MD.read_text(encoding="utf-8")
    assert content.startswith("---"), "SKILL.md must start with ---"
    m = re.search(r"\n---\s*\n", content[3:])
    assert m, "unclosed frontmatter"
    fm = yaml.safe_load(content[3 : m.start() + 3])
    return fm, content


def test_skill_file_exists():
    assert SKILL_MD.is_file(), "SKILL.md must exist"


def test_frontmatter_required_fields():
    fm, _ = _frontmatter()
    for field in ("name", "description", "version", "author", "license", "platforms"):
        assert field in fm, f"missing frontmatter field: {field}"
    assert fm["name"] == "bitwarden"
    assert fm["platforms"] == ["linux", "macos", "windows"]


def test_description_hardline():
    fm, _ = _frontmatter()
    desc = str(fm.get("description") or "")
    assert len(desc) <= 60, f"description {len(desc)} chars (hardline 60)"
    assert desc.rstrip().endswith("."), "description must end with period"
    assert not re.search(
        r"\b(powerful|comprehensive|seamless|revolutionary|cutting-edge)\b",
        desc,
        re.IGNORECASE,
    ), "description contains marketing word"


def test_prerequisites_command():
    fm, _ = _frontmatter()
    prereqs = fm.get("prerequisites") or {}
    assert "bw" in (prereqs.get("commands") or []), "bw CLI must be a prerequisite"


def test_no_machine_local_paths():
    _, content = _frontmatter()
    assert not re.search(r"/home/(?!runner\b)[a-z0-9_-]+/", content), "machine-local path found"
    assert not re.search(r"[A-Z]:\\\\+Users\\\\+", content), "machine-local Windows path found"


def test_no_personal_data():
    """The repo is public-facing: no real emails, names, tokens, or IDs."""
    _, content = _frontmatter()
    for path in (SKILL_DIR / "references").glob("*.md"):
        content += "\n" + path.read_text(encoding="utf-8")
    content += "\n" + SCRIPT.read_text(encoding="utf-8")
    # real-email addresses (generic placeholders like user@example.com are fine)
    emails = [e for e in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content)
              if not e.endswith("@example.com") and not e.endswith("@example.org")]
    assert not emails, f"real email address found: {emails}"
    # token shapes
    assert not re.search(r"ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|ntn_[A-Za-z0-9]{20,}", content), "token found"


def test_references_exist():
    _, content = _frontmatter()
    refs = re.findall(r"references/([A-Za-z0-9_-]+)\.md", content)
    for ref in refs:
        path = SKILL_DIR / "references" / f"{ref}.md"
        assert path.is_file(), f"referenced file missing: references/{ref}.md"


def test_script_exists_and_is_bash():
    assert SCRIPT.is_file(), "bw-unlock.sh helper must exist"
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash"), "script must be a bash script"
    # bash syntax check (no network, no execution)
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-c", "import shutil; print(shutil.which('bash'))"],
        capture_output=True, text=True, check=True,
    )
    bash = result.stdout.strip()
    if bash:
        check = subprocess.run([bash, "-n", str(SCRIPT)], check=False, capture_output=True, text=True)
        assert check.returncode == 0, f"bash syntax error in bw-unlock.sh:\n{check.stderr}"


def test_unlock_pattern_documented():
    """The non-interactive unlock pattern must be present in the skill body."""
    _, content = _frontmatter()
    assert "BW_SESSION" in content, "BW_SESSION must be documented"
    assert "--passwordenv" in content, "non-interactive unlock via --passwordenv must be documented"


def test_keychain_standard_documented():
    """The Keychain credential standard must be documented."""
    _, content = _frontmatter()
    assert "Bitwarden-Master" in content, "Keychain master-password service must be documented"
    assert "security find-generic-password" in content, "Keychain retrieval command must be documented"
