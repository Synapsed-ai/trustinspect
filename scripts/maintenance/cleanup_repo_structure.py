#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


class Cleaner:
    def __init__(self, apply: bool):
        self.apply = apply
        self.archive_root = ROOT / "_archive" / "prototype-patches" / ts()
        self.actions: list[str] = []

    def log(self, action: str) -> None:
        prefix = "APPLY" if self.apply else "DRY"
        print(f"[{prefix}] {action}")
        self.actions.append(action)

    def ensure_dir(self, path: Path) -> None:
        self.log(f"ensure dir {rel(path)}")
        if self.apply:
            path.mkdir(parents=True, exist_ok=True)

    def move(self, src: Path, dst: Path) -> None:
        self.log(f"move {rel(src)} -> {rel(dst)}")
        if self.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                dst = dst.with_name(dst.name + f".{ts()}")
            shutil.move(str(src), str(dst))

    def remove_file(self, path: Path) -> None:
        self.log(f"remove file {rel(path)}")
        if self.apply and path.exists():
            path.unlink()

    def remove_dir(self, path: Path) -> None:
        self.log(f"remove dir {rel(path)}")
        if self.apply and path.exists():
            shutil.rmtree(path)

    def archive(self, path: Path, label: str = "") -> None:
        if not path.exists():
            return
        dst = self.archive_root / (label or "misc") / rel(path)
        self.move(path, dst)


def iter_pycache(root: Path):
    for p in root.rglob("__pycache__"):
        if p.is_dir():
            yield p
    for p in root.rglob("*.pyc"):
        if p.is_file():
            yield p


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean TrustInspect repository structure.")
    ap.add_argument("--apply", action="store_true", help="Apply changes. Without this flag, runs in dry-run mode.")
    ap.add_argument("--dry-run", action="store_true", help="Explicit dry-run mode.")
    ap.add_argument("--purge-venv", action="store_true", help="Remove .venv. Default leaves it in place but .gitignore excludes it.")
    args = ap.parse_args()

    apply = bool(args.apply)
    c = Cleaner(apply=apply)

    print("TrustInspect professional cleanup")
    print("=" * 36)
    print(f"Root: {ROOT}")
    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
    print()

    # Ensure professional folder layout.
    for d in ["targets", "targets/builtin", "targets/local", "targets/disabled", "docs/development", "examples", "scripts/maintenance"]:
        c.ensure_dir(ROOT / d)

    # Move examples/targets to targets/builtin.
    examples_targets = ROOT / "examples" / "targets"
    builtin = ROOT / "targets" / "builtin"
    if examples_targets.exists():
        for p in sorted(examples_targets.glob("*.y*ml")):
            c.move(p, builtin / p.name)
        # remove empty examples/targets
        if apply:
            try:
                examples_targets.rmdir()
            except OSError:
                pass
        else:
            c.log("remove dir examples/targets if empty")

    # Rename legacy disabled folder.
    legacy_disabled = ROOT / "targets" / "_disabled"
    if legacy_disabled.exists():
        target_disabled = ROOT / "targets" / "disabled" / "legacy_disabled"
        c.move(legacy_disabled, target_disabled)

    # Archive prototype root files.
    archive_patterns = [
        "patch_*.py",
        "*_patch.py",
        "README_*_PATCH.md",
        "README_*PATCH*.md",
        "README_*BUGFIX*.md",
        "README_RUNTIME_BUGFIX.md",
        "README_PROFILE_OBJECT_FIX.md",
        "README_YAML_FIX.md",
        "README_GENERATED_DICT_FIX.md",
    ]
    seen: set[Path] = set()
    for pattern in archive_patterns:
        for p in ROOT.glob(pattern):
            if p.is_file() and p not in seen:
                seen.add(p)
                c.archive(p, "root-files")

    # Archive top-level patch folders only. Avoid archiving product folders.
    protected = {"trustinspect", "targets", "examples", "docs", "demos", "tests", "scripts", "tools", "reports", "profiles", "generated_tests", "assets", "schemas", "_archive"}
    for p in sorted(ROOT.iterdir()):
        if not p.is_dir() or p.name in protected:
            continue
        lname = p.name.lower()
        if lname.endswith("_patch") or "_patch" in lname or lname.startswith("ti_"):
            c.archive(p, "patch-directories")

    # Clean OS / cache artefacts.
    for p in [ROOT / ".DS_Store", ROOT / "__MACOSX", ROOT / ".pytest_cache", ROOT / "trustinspect.egg-info"]:
        if p.exists():
            if p.is_dir():
                c.remove_dir(p)
            else:
                c.remove_file(p)

    for p in iter_pycache(ROOT):
        # Do not recurse into .venv unless --purge-venv.
        if ".venv" in p.parts and not args.purge_venv:
            continue
        if p.is_dir():
            c.remove_dir(p)
        elif p.is_file():
            c.remove_file(p)

    if args.purge_venv and (ROOT / ".venv").exists():
        c.remove_dir(ROOT / ".venv")

    # Ensure local folder is keepable in git without committing local YAML.
    gitkeep = ROOT / "targets" / "local" / ".gitkeep"
    c.log("ensure targets/local/.gitkeep")
    if apply:
        gitkeep.parent.mkdir(parents=True, exist_ok=True)
        gitkeep.touch(exist_ok=True)

    print()
    print("Done." if apply else "Dry-run complete. Re-run with --apply to make changes.")


if __name__ == "__main__":
    main()
