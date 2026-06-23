#!/usr/bin/env python3
"""Verify TrustInspect release artifacts and tracked files do not contain local/runtime data.

Usage:
  python scripts/maintenance/verify_release_artifact.py --git-tracked
  python scripts/maintenance/verify_release_artifact.py --artifact /tmp/trustinspect-release.zip
  python scripts/maintenance/verify_release_artifact.py --path . --allow-git
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

FORBIDDEN_PREFIXES = (
    ".git/",
    ".venv/",
    "venv/",
    "env/",
    "reports/",
    "profiles/",
    "generated_tests/",
    "_archive/",
    "trustinspect.egg-info/",
    ".pytest_cache/",
)

FORBIDDEN_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "reports",
    "profiles",
    "generated_tests",
    "_archive",
    "trustinspect.egg-info",
    ".pytest_cache",
}


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_forbidden(entry: str, *, allow_git: bool = False) -> bool:
    e = _norm(entry)
    parts = [p for p in e.split("/") if p]
    if allow_git and parts and parts[0] == ".git":
        return False
    if any(e == p.rstrip("/") or e.startswith(p) for p in FORBIDDEN_PREFIXES if not (allow_git and p == ".git/")):
        return True
    return any(part in FORBIDDEN_NAMES and not (allow_git and part == ".git") for part in parts)


def check_zip(path: Path) -> list[str]:
    bad: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if is_forbidden(name):
                bad.append(name)
    return bad


def check_path(path: Path, *, allow_git: bool) -> list[str]:
    bad: list[str] = []
    for p in path.rglob("*"):
        rel = p.relative_to(path).as_posix()
        if is_forbidden(rel, allow_git=allow_git):
            bad.append(rel)
    return bad


def check_git_tracked() -> list[str]:
    try:
        proc = subprocess.run(["git", "ls-files"], check=True, text=True, capture_output=True)
    except Exception as exc:  # pragma: no cover
        print(f"[!] Could not run git ls-files: {exc}", file=sys.stderr)
        return []
    return [line for line in proc.stdout.splitlines() if is_forbidden(line, allow_git=True)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", type=Path, help="Release zip artifact to inspect")
    ap.add_argument("--path", type=Path, help="Directory tree to inspect")
    ap.add_argument("--allow-git", action="store_true", help="Allow .git when checking a working tree")
    ap.add_argument("--git-tracked", action="store_true", help="Check tracked files with git ls-files")
    args = ap.parse_args()

    findings: list[str] = []
    if args.artifact:
        findings.extend([f"artifact:{p}" for p in check_zip(args.artifact)])
    if args.path:
        findings.extend([f"path:{p}" for p in check_path(args.path, allow_git=args.allow_git)])
    if args.git_tracked:
        findings.extend([f"git:{p}" for p in check_git_tracked()])

    if findings:
        print("[FAIL] Forbidden release/runtime artifacts detected:")
        for item in findings:
            print(f"  - {item}")
        return 1

    print("[OK] No forbidden release/runtime artifacts detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
