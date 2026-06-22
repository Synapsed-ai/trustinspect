#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import time
from pathlib import Path

ROOT = Path.cwd()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] mkdir -p {rel(path)}")
    else:
        path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path, dry_run: bool) -> None:
    if not src.exists():
        return
    ensure_dir(dst.parent, dry_run)
    if dst.exists():
        print(f"[skip] exists: {rel(dst)}")
        return
    if dry_run:
        print(f"[dry-run] copy {rel(src)} -> {rel(dst)}")
    else:
        shutil.copy2(src, dst)
        print(f"[copy] {rel(src)} -> {rel(dst)}")


def copy_tree_yaml(src_dir: Path, dst_dir: Path, dry_run: bool) -> None:
    if not src_dir.exists() or not src_dir.is_dir():
        return
    for src in sorted(src_dir.glob("*.yaml")):
        copy_file(src, dst_dir / src.name, dry_run)
    for src in sorted(src_dir.glob("*.yml")):
        copy_file(src, dst_dir / src.name, dry_run)


def move_to_archive(path: Path, archive_dir: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    ensure_dir(archive_dir, dry_run)
    dst = archive_dir / path.name
    if dst.exists():
        suffix = int(time.time())
        dst = archive_dir / f"{path.name}.{suffix}"
    if dry_run:
        print(f"[dry-run] archive {rel(path)} -> {rel(dst)}")
    else:
        shutil.move(str(path), str(dst))
        print(f"[archive] {rel(path)} -> {rel(dst)}")


def archive_patch_artifacts(dry_run: bool) -> None:
    ts = time.strftime("%Y%m%d-%H%M%S")
    archive_dir = ROOT / "tools" / "maintenance" / "_archive" / ts

    candidates: list[Path] = []

    for pattern in ["patch*.py", "patch_*.py", "*_patch.py"]:
        candidates.extend(ROOT.glob(pattern))

    for pattern in ["*_patch", "trustinspect_*_patch", "ti_*"]:
        for p in ROOT.glob(pattern):
            if p.is_dir() and p.name not in {"tools", "trustinspect"}:
                candidates.append(p)

    # Avoid moving the currently copied cleanup folder if user applied it inside root using a descriptive name.
    candidates = [p for p in candidates if "tools" not in p.parts and p.exists()]

    seen = set()
    for p in sorted(candidates):
        if p in seen:
            continue
        seen.add(p)
        move_to_archive(p, archive_dir, dry_run)


def write_gitkeep(path: Path, dry_run: bool) -> None:
    ensure_dir(path, dry_run)
    gitkeep = path / ".gitkeep"
    if gitkeep.exists():
        return
    if dry_run:
        print(f"[dry-run] touch {rel(gitkeep)}")
    else:
        gitkeep.write_text("", encoding="utf-8")


def migrate(dry_run: bool, archive_patches: bool) -> int:
    print("TrustInspect layout migration")
    print(f"Root: {ROOT}")
    print(f"Mode: {'dry-run' if dry_run else 'apply'}")

    # Create canonical directories.
    for d in [
        "assets",
        "suites",
        "dynamic_templates",
        "targets/builtin",
        "targets/local",
        "targets/disabled",
        "reports",
        "generated_tests",
        "profiles",
        "tools/maintenance",
    ]:
        ensure_dir(ROOT / d, dry_run)

    # Copy built-in targets from examples/targets to targets/builtin.
    copy_tree_yaml(ROOT / "examples" / "targets", ROOT / "targets" / "builtin", dry_run)

    # Copy static suites into suites/.
    copy_tree_yaml(ROOT / "examples" / "test_suites", ROOT / "suites", dry_run)

    # Copy trustinspect baseline if present.
    for src in [
        ROOT / "examples" / "test_cases" / "trustinspect_baseline.yaml",
        ROOT / "examples" / "test_cases" / "owasp_light_full.yaml",
        ROOT / "examples" / "test_cases" / "owasp_llm_top10_2025_light.yaml",
        ROOT / "examples" / "test_cases" / "owasp_llm_top10_2025_full.yaml",
    ]:
        if src.exists():
            copy_file(src, ROOT / "suites" / src.name, dry_run)

    # Copy dynamic templates.
    copy_tree_yaml(ROOT / "examples" / "dynamic_templates", ROOT / "dynamic_templates", dry_run)
    copy_tree_yaml(ROOT / "examples" / "test_templates", ROOT / "dynamic_templates", dry_run)

    # Keep generated/local dirs in git with .gitkeep only if desired.
    for d in [ROOT / "targets" / "local", ROOT / "targets" / "disabled"]:
        write_gitkeep(d, dry_run)

    if archive_patches:
        archive_patch_artifacts(dry_run)

    print("\nMigration complete." if not dry_run else "\nDry-run complete. Re-run with --apply to execute.")
    print("Next: adjust runtime defaults to prefer targets/builtin, suites, and dynamic_templates if not already done.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate TrustInspect to a cleaner repository layout.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Show planned changes without applying them.")
    group.add_argument("--apply", action="store_true", help="Apply changes.")
    parser.add_argument("--no-archive-patches", action="store_true", help="Do not archive root patch files/folders.")
    args = parser.parse_args()
    return migrate(dry_run=args.dry_run, archive_patches=not args.no_archive_patches)


if __name__ == "__main__":
    raise SystemExit(main())
