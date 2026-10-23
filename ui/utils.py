"""Helpers for the Streamlit UI."""
from __future__ import annotations

import re
from pathlib import Path

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def count_jsonl_lines(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return None


def describe_output(path: Path, kind: str) -> dict[str, str]:
    rel = _try_relative(path)
    if kind == "dir":
        exists = path.is_dir()
        extra = ""
        if exists:
            try:
                n = sum(1 for _ in path.iterdir())
                extra = f"{n} item(s)"
            except OSError:
                extra = "—"
        return {
            "path": rel,
            "exists": "yes" if exists else "no",
            "detail": extra or ("folder" if exists else "missing"),
        }

    exists = path.is_file()
    detail = ""
    if exists and path.suffix.lower() == ".jsonl":
        n = count_jsonl_lines(path)
        detail = f"{n} lines" if n is not None else "—"
    elif exists:
        try:
            detail = f"{path.stat().st_size:,} bytes"
        except OSError:
            detail = "—"
    else:
        detail = "missing"

    return {"path": rel, "exists": "yes" if exists else "no", "detail": detail}


def _try_relative(path: Path) -> str:
    try:
        from sources import PROJECT_ROOT

        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)
