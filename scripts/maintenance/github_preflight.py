#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "trustinspect/cli.py",
    "trustinspect/core/models.py",
]

RECOMMENDED_PATHS = [
    ".gitignore",
    "SECURITY.md",
    "NOTICE",
    "docs/github-publication-checklist.md",
    "targets/builtin",
    "targets/local/.gitkeep",
    "targets/disabled/.gitkeep",
    "suites/owasp",
    "demos/trustinspect-demo-chatbot",
]

BAD_ROOT_PATTERNS = [
    "README_*_PATCH.md",
    "README_*BUGFIX*.md",
    "patch_*.py",
    "*_patch",
]

RUNTIME_DIRS = ["reports", "profiles", "generated_tests", ".venv", "trustinspect.egg-info", ".pytest_cache"]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for item in REQUIRED_PATHS:
        if not (ROOT / item).exists():
            errors.append(f"missing required path: {item}")

    for item in RECOMMENDED_PATHS:
        if not (ROOT / item).exists():
            warnings.append(f"missing recommended path: {item}")

    for pattern in BAD_ROOT_PATTERNS:
        for path in ROOT.glob(pattern):
            warnings.append(f"prototype artifact in repo root: {rel(path)}")

    for item in RUNTIME_DIRS:
        if (ROOT / item).exists():
            warnings.append(f"runtime/local artifact present: {item} (should be gitignored or archived before public release)")

    # Detect base64 report header in template files.
    template_dir = ROOT / "trustinspect" / "reporting" / "templates"
    if template_dir.exists():
        for path in template_dir.rglob("*.j2"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "data:image" in text or "base64," in text:
                errors.append(f"embedded base64 image marker found in report template: {rel(path)}")
            if "script-src 'none'" not in text and "Content-Security-Policy" in text:
                warnings.append(f"template has CSP but no script-src none: {rel(path)}")

    # Check target folder organization.
    if (ROOT / "examples" / "targets").exists():
        warnings.append("examples/targets exists; operational targets should live in targets/builtin")

    # Check suite files if the suites directory exists.
    suite_candidates = [
        "suites/owasp/llm-top10-2025-light.yaml",
        "suites/owasp/llm-top10-2025-full.yaml",
        "suites/owasp/aitg-light.yaml",
        "suites/owasp/aitg-full.yaml",
        "suites/trustinspect/baseline.yaml",
    ]
    existing_suite_count = sum(1 for p in suite_candidates if (ROOT / p).exists())
    if existing_suite_count == 0:
        warnings.append("no canonical suite files found under suites/")

    print("TrustInspect GitHub preflight")
    print("=" * 36)

    if errors:
        print("\nERRORS")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\nWARNINGS")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("OK: no issues detected")
    elif not errors:
        print("\nOK with warnings")
    else:
        print("\nFAILED")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
