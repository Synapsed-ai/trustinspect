#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path.cwd()

SECTIONS = {
    "Root patch scripts": ["patch*.py", "*_patch.py"],
    "Patch folders": ["*_patch", "ti_*", "trustinspect_*_patch"],
    "Legacy target folders": ["examples/targets"],
    "Legacy suite folders": ["examples/test_suites", "examples/test_cases"],
    "Legacy dynamic template folders": ["examples/dynamic_templates", "examples/test_templates"],
    "Generated artifacts": ["reports", "generated_tests", "profiles"],
}


def matches(pattern: str):
    return sorted(ROOT.glob(pattern))


def print_section(title: str, paths: list[Path]) -> None:
    print(f"\n## {title}")
    if not paths:
        print("  - none")
        return
    for p in paths:
        kind = "dir " if p.is_dir() else "file"
        print(f"  - {kind}: {p.relative_to(ROOT)}")


def main() -> int:
    print("TrustInspect repository layout audit")
    print(f"Root: {ROOT}")

    for title, patterns in SECTIONS.items():
        found: list[Path] = []
        for pattern in patterns:
            found.extend(matches(pattern))
        # avoid duplicates and hidden .venv content
        unique = []
        seen = set()
        for p in found:
            if ".venv" in p.parts:
                continue
            if p not in seen:
                seen.add(p)
                unique.append(p)
        print_section(title, unique)

    print("\nRecommended layout:")
    for d in ["assets", "suites", "dynamic_templates", "targets/builtin", "targets/local", "targets/disabled", "tools/maintenance"]:
        print(f"  - {d}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
