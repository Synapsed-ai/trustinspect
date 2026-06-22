#!/usr/bin/env python3
"""TrustInspect repository cleanup / migration helper.

Safe by default: run with --dry-run first. Use --apply to change files.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path.cwd()

TEXT_PATCH_FILES = [
    "trustinspect/targets/registry.py",
    "trustinspect/interactive/launcher.py",
    "trustinspect/cli.py",
]

PATCH_PATTERNS = [
    "patch*.py",
    "patch_*.py",
    "*_patch.py",
]

PATCH_DIR_PATTERNS = [
    "*_patch",
    "ti_*",
    "trustinspect_*_patch",
]

CACHE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
]

BINARY_SUFFIXES_TO_REMOVE = {".pyc", ".pyo"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def log(message: str) -> None:
    print(message)


def ensure_dir(path: Path, apply: bool) -> None:
    if path.exists():
        return
    log(f"mkdir {rel(path)}")
    if apply:
        path.mkdir(parents=True, exist_ok=True)


def move_file(src: Path, dst: Path, apply: bool) -> None:
    if not src.exists():
        return
    ensure_dir(dst.parent, apply)
    final_dst = dst
    if final_dst.exists():
        stem, suffix = final_dst.stem, final_dst.suffix
        i = 2
        while final_dst.exists():
            final_dst = final_dst.with_name(f"{stem}_{i}{suffix}")
            i += 1
    log(f"move {rel(src)} -> {rel(final_dst)}")
    if apply:
        shutil.move(str(src), str(final_dst))


def move_dir(src: Path, dst: Path, apply: bool) -> None:
    if not src.exists() or not src.is_dir():
        return
    ensure_dir(dst.parent, apply)
    final_dst = dst
    if final_dst.exists():
        i = 2
        while final_dst.exists():
            final_dst = dst.with_name(f"{dst.name}_{i}")
            i += 1
    log(f"move {rel(src)} -> {rel(final_dst)}")
    if apply:
        shutil.move(str(src), str(final_dst))


def write_text(path: Path, text: str, apply: bool) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    log(f"write {rel(path)}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def migrate_targets(apply: bool) -> None:
    builtin = ROOT / "targets" / "builtin"
    local = ROOT / "targets" / "local"
    disabled = ROOT / "targets" / "disabled"
    for d in (builtin, local, disabled):
        ensure_dir(d, apply)

    examples_targets = ROOT / "examples" / "targets"
    if examples_targets.exists():
        for yml in sorted(list(examples_targets.glob("*.yaml")) + list(examples_targets.glob("*.yml"))):
            move_file(yml, builtin / yml.name, apply)
        # Remove empty examples/targets directory if empty after move.
        if apply and examples_targets.exists():
            try:
                examples_targets.rmdir()
                log(f"removed empty {rel(examples_targets)}")
            except OSError:
                pass
        elif not apply:
            log(f"would remove {rel(examples_targets)} if empty")

    write_text(ROOT / "targets" / "README.md", """# TrustInspect Targets\n\nTarget profiles are organized as follows:\n\n- `builtin/`: official target profiles shipped with TrustInspect.\n- `local/`: target profiles calibrated locally by the tester. This folder should normally be gitignored.\n- `disabled/`: profiles intentionally removed from the interactive launcher but kept for traceability.\n\nDo not place target profiles under `examples/targets`; that path is deprecated.\n""", apply)


def patch_hardcoded_paths(apply: bool) -> None:
    replacements = {
        "examples/targets": "targets/builtin",
        "examples\\targets": "targets\\builtin",
    }
    for rel_path in TEXT_PATCH_FILES:
        path = ROOT / rel_path
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != original:
            log(f"patch target path references in {rel(path)}")
            if apply:
                path.write_text(updated, encoding="utf-8")


def archive_patch_scripts(apply: bool) -> None:
    archive_root = ROOT / "tools" / "migrations" / "archive" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    ensure_dir(archive_root, apply)

    # Root-level patch scripts
    candidates: set[Path] = set()
    for pattern in PATCH_PATTERNS:
        candidates.update(ROOT.glob(pattern))

    for src in sorted(candidates):
        if src.is_file() and src.name != Path(__file__).name:
            move_file(src, archive_root / "root" / src.name, apply)

    # One-off patch folders in root and Downloads-style copied dirs inside project.
    dir_candidates: set[Path] = set()
    for pattern in PATCH_DIR_PATTERNS:
        dir_candidates.update(ROOT.glob(pattern))
    for src in sorted(dir_candidates):
        if not src.is_dir():
            continue
        # Do not move core project dirs.
        if src.name in {"trustinspect", "targets", "examples", "docs", "scripts", "tools", "tests", "reports", "assets", "demos"}:
            continue
        move_dir(src, archive_root / "dirs" / src.name, apply)

    # scripts/patch*.py -> archive
    scripts_dir = ROOT / "scripts"
    if scripts_dir.exists():
        for pattern in PATCH_PATTERNS:
            for src in sorted(scripts_dir.glob(pattern)):
                if src.is_file():
                    move_file(src, archive_root / "scripts" / src.name, apply)


def clean_cache(apply: bool) -> None:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        path = Path(dirpath)
        # Skip virtualenv and reports to avoid expensive walk.
        if any(part in {".venv", "reports"} for part in path.parts):
            dirnames[:] = []
            continue
        for dirname in list(dirnames):
            if dirname in CACHE_PATTERNS:
                target = path / dirname
                log(f"remove cache dir {rel(target)}")
                if apply:
                    shutil.rmtree(target, ignore_errors=True)
                dirnames.remove(dirname)
        for filename in filenames:
            p = path / filename
            if filename == ".DS_Store" or p.suffix in BINARY_SUFFIXES_TO_REMOVE:
                log(f"remove cache file {rel(p)}")
                if apply:
                    try:
                        p.unlink()
                    except FileNotFoundError:
                        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Reorganize TrustInspect project structure professionally.")
    parser.add_argument("--apply", action="store_true", help="Actually modify files. Without this, dry-run only.")
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry run.")
    parser.add_argument("--skip-archive-patches", action="store_true", help="Do not archive patch scripts/folders.")
    parser.add_argument("--skip-cache-clean", action="store_true", help="Do not remove cache files.")
    args = parser.parse_args()

    apply = bool(args.apply)
    if not apply:
        log("[DRY RUN] No files will be changed. Use --apply to modify the project.\n")

    migrate_targets(apply)
    patch_hardcoded_paths(apply)
    if not args.skip_archive_patches:
        archive_patch_scripts(apply)
    if not args.skip_cache_clean:
        clean_cache(apply)

    if apply:
        log("\nCleanup complete.")
    else:
        log("\nDry run complete. Re-run with --apply when ready.")


if __name__ == "__main__":
    main()
