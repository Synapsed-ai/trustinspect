#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path.cwd()

NOISY_DIRS = {".venv", "__pycache__", ".pytest_cache", "trustinspect.egg-info", "__MACOSX"}
GENERATED_DIRS = {"reports", "generated_tests", "profiles"}


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def exists(path: str) -> str:
    return "yes" if (ROOT / path).exists() else "no"


def main() -> None:
    print("TrustInspect repository audit")
    print("=" * 34)
    print(f"Root: {ROOT}")
    print()

    print("Core folders")
    for folder in ["trustinspect", "targets", "targets/builtin", "targets/local", "examples", "docs", "demos", "tests"]:
        print(f"  {folder:<24} {exists(folder):<3} files={count_files(ROOT / folder)}")
    print()

    print("Runtime/generated folders")
    for folder in sorted(GENERATED_DIRS):
        print(f"  {folder:<24} {exists(folder):<3} files={count_files(ROOT / folder)}")
    print()

    print("Prototype/noisy artefacts")
    root_patch_files = sorted([p.name for p in ROOT.glob("patch_*.py")])
    root_readme_patch = sorted([p.name for p in ROOT.glob("README_*PATCH*.md")]) + sorted([p.name for p in ROOT.glob("README_*BUGFIX*.md")])
    patch_dirs = sorted([p.name for p in ROOT.iterdir() if p.is_dir() and (p.name.endswith("_patch") or "_patch" in p.name.lower())])
    for item_name, items in [
        ("root patch_*.py", root_patch_files),
        ("root README_*PATCH*.md", root_readme_patch),
        ("patch directories", patch_dirs),
    ]:
        print(f"  {item_name:<28} {len(items)}")
        for i in items[:12]:
            print(f"    - {i}")
        if len(items) > 12:
            print(f"    ... +{len(items)-12} more")
    print()

    print("Targets")
    for folder in ["examples/targets", "targets/builtin", "targets/local", "targets/disabled", "targets/_disabled"]:
        yaml_count = len(list((ROOT / folder).glob("*.y*ml"))) if (ROOT / folder).exists() else 0
        print(f"  {folder:<24} {exists(folder):<3} yaml={yaml_count}")
    print()

    print("Recommendation")
    if (ROOT / "examples/targets").exists():
        print("  - Move examples/targets to targets/builtin")
    if root_patch_files or root_readme_patch or patch_dirs:
        print("  - Archive prototype patch files/directories")
    if (ROOT / ".venv").exists():
        print("  - Keep .venv locally, but do not commit it")
    print("  - Run cleanup_repo_structure.py --dry-run before applying changes")


if __name__ == "__main__":
    main()
