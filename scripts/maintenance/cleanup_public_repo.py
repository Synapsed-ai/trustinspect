#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PATCH_PATTERNS = [
    "README_*_PATCH.md",
    "README_*BUGFIX*.md",
    "patch_*.py",
    "*_patch",
]

CACHE_PATTERNS = [
    "**/__pycache__",
    "**/*.pyc",
    ".pytest_cache",
    "trustinspect.egg-info",
    "__MACOSX",
    "**/.DS_Store",
]

RUNTIME_DIRS = ["reports", "profiles", "generated_tests"]


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def archive_path(kind: str) -> Path:
    return ROOT / "_archive" / kind / timestamp()


def move_path(path: Path, dst_root: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    rel = path.relative_to(ROOT)
    dst = dst_root / rel
    print(f"archive {rel} -> {dst.relative_to(ROOT)}")
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    shutil.move(str(path), str(dst))


def remove_path(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    print(f"remove {path.relative_to(ROOT)}")
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def normalize_targets(dry_run: bool) -> None:
    builtin = ROOT / "targets" / "builtin"
    local = ROOT / "targets" / "local"
    disabled = ROOT / "targets" / "disabled"
    for d in [builtin, local, disabled]:
        if not d.exists():
            print(f"create {d.relative_to(ROOT)}/")
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
    for keep in [local / ".gitkeep", disabled / ".gitkeep"]:
        if not keep.exists():
            print(f"create {keep.relative_to(ROOT)}")
            if not dry_run:
                keep.parent.mkdir(parents=True, exist_ok=True)
                keep.write_text("", encoding="utf-8")

    old_examples = ROOT / "examples" / "targets"
    if old_examples.exists():
        for src in sorted(old_examples.glob("*.y*ml")):
            dst = builtin / src.name
            print(f"move target {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
            if not dry_run:
                builtin.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    # Keep existing builtin as authoritative, archive duplicate.
                    arch = archive_path("duplicate-targets") / src.relative_to(ROOT)
                    arch.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(arch))
                else:
                    shutil.move(str(src), str(dst))
        # Remove empty dir tree if possible.
        if not dry_run:
            try:
                old_examples.rmdir()
            except OSError:
                pass


def archive_prototype_artifacts(dry_run: bool) -> None:
    dst_root = archive_path("prototype-artifacts")
    seen: set[Path] = set()
    for pattern in PATCH_PATTERNS:
        for path in ROOT.glob(pattern):
            if path.name == "_archive":
                continue
            if path in seen:
                continue
            seen.add(path)
            move_path(path, dst_root, dry_run)


def archive_runtime_artifacts(dry_run: bool) -> None:
    dst_root = archive_path("runtime-artifacts")
    for item in RUNTIME_DIRS:
        path = ROOT / item
        if path.exists():
            move_path(path, dst_root, dry_run)


def remove_caches(dry_run: bool) -> None:
    seen: set[Path] = set()
    for pattern in CACHE_PATTERNS:
        for path in ROOT.glob(pattern):
            if path in seen:
                continue
            seen.add(path)
            remove_path(path, dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare TrustInspect repository for public GitHub release.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without changing files.")
    parser.add_argument("--apply", action="store_true", help="Apply changes.")
    parser.add_argument("--archive-runtime", action="store_true", help="Archive reports/profiles/generated_tests.")
    parser.add_argument("--remove-caches", action="store_true", default=True)
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error("Use --dry-run or --apply")

    dry_run = args.dry_run
    print(f"TrustInspect public repo cleanup ({'dry-run' if dry_run else 'apply'})")
    print("=" * 56)

    normalize_targets(dry_run)
    archive_prototype_artifacts(dry_run)
    if args.archive_runtime:
        archive_runtime_artifacts(dry_run)
    if args.remove_caches:
        remove_caches(dry_run)

    print("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
