#!/usr/bin/env python3
"""
Audit: fail if Cyrillic user-facing text exists outside messages.py.
Fail if any COPY_ID referenced in FSM (SPEC 03, 04) does not exist in messages.py.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
MESSAGES_PY = SRC / "bot" / "messages.py"
SPEC = REPO_ROOT / "SPEC.md"

CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]+")


def get_copy_ids_from_spec() -> set[str]:
    copy_ids = set()
    if not SPEC.exists():
        return copy_ids
    content = SPEC.read_text(encoding="utf-8")
    for m in re.finditer(r"\[([A-Z_][A-Z0-9_]*)\]\s*\n\s*text\s*=", content):
        copy_ids.add(m.group(1))
    for m in re.finditer(r"copy_id[:\s]+([A-Z_][A-Z0-9_]*)", content, re.IGNORECASE):
        copy_ids.add(m.group(1).upper())
    for m in re.finditer(r"get_copy\(\s*[\"']([A-Z_][A-Z0-9_]*)[\"']\s*\)", content):
        copy_ids.add(m.group(1))
    return copy_ids


def get_copy_ids_from_messages_py() -> set[str]:
    ids = set()
    if not MESSAGES_PY.exists():
        return ids
    content = MESSAGES_PY.read_text(encoding="utf-8")
    in_copy_ids = False
    for line in content.splitlines():
        if "COPY_IDS = [" in line:
            in_copy_ids = True
            continue
        if in_copy_ids:
            if line.strip() == "]":
                break
            m = re.search(r'"([A-Z][A-Z0-9_]*)"', line)
            if m:
                ids.add(m.group(1))
    if not ids:
        for m in re.finditer(r"^([A-Z][A-Z0-9_]*)\s*=\s*(\"\"\"|''')", content, re.MULTILINE):
            ids.add(m.group(1))
    return ids


def get_fsm_referenced_copy_ids() -> set[str]:
    """COPY_IDs referenced in handlers (get_copy('X'))."""
    ids = set()
    for py in SRC.rglob("*.py"):
        if "messages.py" in str(py):
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in re.finditer(r"get_copy\s*\(\s*[\"']([A-Z_][A-Z0-9_]*)[\"']\s*\)", text):
            ids.add(m.group(1))
    return ids


CYRILLIC_EXCLUDE_FILES = {"matching.py", "editor_schema.py"}  # STOP_WORDS / block/field labels (structural)


def files_with_cyrillic_outside_messages() -> list[tuple[Path, int, str]]:
    bad = []
    for py in SRC.rglob("*.py"):
        if py == MESSAGES_PY or py.name in CYRILLIC_EXCLUDE_FILES:
            continue
        try:
            lines = py.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if "#" in line:
                code, _, comment = line.partition("#")
                if CYRILLIC_PATTERN.search(comment):
                    continue
                line = code
            if CYRILLIC_PATTERN.search(line):
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                if "get_copy(" in line or "messages." in line or "messages import" in line:
                    continue
                bad.append((py, i, line.strip()[:80]))
    return bad


def main() -> int:
    errors = []

    fsm_ids = get_fsm_referenced_copy_ids()
    msg_ids = get_copy_ids_from_messages_py()
    for cid in fsm_ids:
        if cid not in msg_ids:
            errors.append(f"COPY_ID referenced in code but missing in messages.py: {cid}")

    bad_cyrillic = files_with_cyrillic_outside_messages()
    for path, line_no, snippet in bad_cyrillic:
        rel = path.relative_to(REPO_ROOT)
        errors.append(f"Cyrillic outside messages.py: {rel}:{line_no} -> {snippet!r}")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
