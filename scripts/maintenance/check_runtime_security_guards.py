#!/usr/bin/env python3
"""CI guards for TrustInspect runtime security hardening.

Checks:
- Chrome --no-sandbox is not added in runtime code unless guarded by an explicit opt-in variable/flag.
- DOM/page-source snapshots are not written as executable .html files.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_ROOTS = ["trustinspect", "demos", "scripts"]
EXCLUDED_PARTS = {"tests", ".venv", "_archive", ".git", "__pycache__"}
EXCLUDED_FILES = {"check_runtime_security_guards.py"}

NO_SANDBOX_ALLOWED_TOKENS = (
    "--chrome-no-sandbox",
    "chrome_no_sandbox",
    "allow_no_sandbox",
    "no_sandbox",
)

DOM_HTML_PATTERNS = (
    re.compile(r"_dom\.html(?!\.txt)"),
    re.compile(r"dom\.html(?!\.txt)"),
    re.compile(r"DOM_SNAPSHOT.*\.html(?!\.txt)", re.IGNORECASE),
)


def iter_py_files(root: Path):
    for base in DEFAULT_ROOTS:
        d = root / base
        if not d.exists():
            continue
        for path in d.rglob("*.py"):
            if path.name in EXCLUDED_FILES:
                continue
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            yield path


def line_is_guarded_no_sandbox(lines: list[str], idx: int) -> bool:
    line = lines[idx]
    # CLI flag declaration is allowed.
    if "--chrome-no-sandbox" in line:
        return True
    # Any direct Chrome option should be behind an explicit opt-in guard.
    window = "\n".join(lines[max(0, idx - 6): idx + 1])
    if "--no-sandbox" not in line:
        return True
    if any(tok in window for tok in NO_SANDBOX_ALLOWED_TOKENS) and re.search(r"\bif\b", window):
        return True
    return False


def check_no_sandbox(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_py_files(root):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines):
            if "--no-sandbox" in line and not line_is_guarded_no_sandbox(lines, i):
                findings.append(f"{path}:{i+1}: unguarded --no-sandbox: {line.strip()}")
    return findings


def check_dom_snapshot_extension(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_py_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(p.search(line) for p in DOM_HTML_PATTERNS):
                findings.append(f"{path}:{lineno}: DOM snapshot appears to use executable .html extension: {line.strip()}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args()

    findings = []
    findings.extend(check_no_sandbox(args.root))
    findings.extend(check_dom_snapshot_extension(args.root))

    if findings:
        print("[FAIL] Runtime security guard violations detected:")
        for f in findings:
            print(f"  - {f}")
        return 1

    print("[OK] Runtime security guards passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
