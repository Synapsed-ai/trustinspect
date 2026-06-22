#!/usr/bin/env python3
"""
TrustInspect repository cleanup utility.

Purpose:
- Move target YAML files from examples/targets/ into targets/builtin/.
- Keep user-calibrated targets under targets/local/.
- Move static suites out of examples/ into test_suites/.
- Move dynamic templates into test_templates/dynamic/.
- Archive patch scripts/folders from the root into _archive/patches/.
- Remove transient Python/macOS artifacts.

Default mode is dry-run. Use --apply to perform changes.
"""
from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PATCH_NAME_PATTERNS = (
    "patch*.py",
    "*_patch.py",
    "trustinspect_*_patch",
    "ti_*_patch",
    "*_fix_patch",
    "*_runtime_patch",
    "*_quality_patch",
    "*_hardening_patch",
)

TRANSIENT_PATTERNS = (
    "**/__pycache__",
    "**/.DS_Store",
    "**/*.pyc",
)


@dataclass
class MovePlan:
    src: Path
    dst: Path
    kind: str = "move"


class Cleaner:
    def __init__(self, root: Path, apply: bool = False, keep_legacy_examples: bool = False):
        self.root = root.resolve()
        self.apply = apply
        self.keep_legacy_examples = keep_legacy_examples
        self.archive = self.root / "_archive" / "patches"
        self.moves: list[MovePlan] = []
        self.removes: list[Path] = []

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def ensure_dir(self, path: Path) -> None:
        if self.apply:
            path.mkdir(parents=True, exist_ok=True)
        print(f"[dir]  {self.rel(path)}")

    def plan_move_file(self, src: Path, dst: Path) -> None:
        if not src.exists() or not src.is_file():
            return
        self.moves.append(MovePlan(src, dst))

    def plan_move_dir_contents(self, src_dir: Path, dst_dir: Path, suffixes: tuple[str, ...] | None = None) -> None:
        if not src_dir.exists() or not src_dir.is_dir():
            return
        for item in sorted(src_dir.iterdir()):
            if item.name.startswith("."):
                continue
            if suffixes and item.is_file() and item.suffix not in suffixes:
                continue
            self.moves.append(MovePlan(item, dst_dir / item.name))

    def plan_remove_transients(self) -> None:
        for pattern in TRANSIENT_PATTERNS:
            for path in self.root.glob(pattern):
                self.removes.append(path)

    def plan_archive_patches(self) -> None:
        for pattern in PATCH_NAME_PATTERNS:
            for path in self.root.glob(pattern):
                if path.parts and "_archive" in path.parts:
                    continue
                if path.name in {"trustinspect_repo_cleanup_patch"}:
                    continue
                self.moves.append(MovePlan(path, self.archive / path.name, kind="archive"))

        # Also archive patch scripts inside scripts/ while keeping utility scripts.
        scripts_dir = self.root / "scripts"
        if scripts_dir.exists():
            for path in scripts_dir.glob("patch*.py"):
                self.moves.append(MovePlan(path, self.archive / "scripts" / path.name, kind="archive"))

    def build_plan(self) -> None:
        # Professional top-level directories.
        for d in [
            self.root / "targets" / "builtin",
            self.root / "targets" / "local",
            self.root / "targets" / "_disabled",
            self.root / "test_suites" / "static",
            self.root / "test_templates" / "dynamic",
            self.root / "assets" / "report",
            self.root / "generated" / "profiles",
            self.root / "generated" / "test_cases",
            self.root / "reports",
            self.archive,
        ]:
            self.ensure_dir(d)

        # Targets.
        self.plan_move_dir_contents(self.root / "examples" / "targets", self.root / "targets" / "builtin", suffixes=(".yaml", ".yml"))

        # Static suites / catalogues.
        self.plan_move_dir_contents(self.root / "examples" / "test_suites", self.root / "test_suites" / "static", suffixes=(".yaml", ".yml"))
        self.plan_move_dir_contents(self.root / "examples" / "test_cases", self.root / "test_suites" / "static", suffixes=(".yaml", ".yml"))

        # Dynamic templates.
        self.plan_move_dir_contents(self.root / "examples" / "dynamic_templates", self.root / "test_templates" / "dynamic", suffixes=(".yaml", ".yml"))
        self.plan_move_dir_contents(self.root / "examples" / "test_templates", self.root / "test_templates" / "dynamic", suffixes=(".yaml", ".yml"))

        # Report assets.
        for candidate in [
            self.root / "assets" / "trustinspect_report_header.png",
            self.root / "assets" / "cyberpunk_ai_testing_interface_banner.png",
        ]:
            if candidate.exists():
                self.plan_move_file(candidate, self.root / "assets" / "report" / candidate.name)

        self.plan_archive_patches()
        self.plan_remove_transients()

    def _move(self, src: Path, dst: Path) -> None:
        if not src.exists():
            return
        if dst.exists():
            # Avoid overwriting; keep deterministic archive/copy suffix.
            base = dst
            n = 2
            while dst.exists():
                dst = base.with_name(f"{base.stem}-{n}{base.suffix}")
                n += 1
        if self.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        print(f"[{ 'archive' if '_archive' in str(dst) else 'move' }] {self.rel(src)} -> {self.rel(dst)}")

    def _remove(self, path: Path) -> None:
        if not path.exists():
            return
        if self.apply:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        print(f"[rm]   {self.rel(path)}")

    def execute(self) -> None:
        print(f"TrustInspect repo cleanup at: {self.root}")
        print("Mode:", "APPLY" if self.apply else "DRY-RUN")
        self.build_plan()
        print("\nPlanned moves/archive:")
        for move in self.moves:
            self._move(move.src, move.dst)

        print("\nTransient cleanup:")
        for path in self.removes:
            self._remove(path)

        if not self.keep_legacy_examples:
            self.cleanup_empty_legacy_dirs()

        print("\nDone.")
        if not self.apply:
            print("Dry-run only. Re-run with --apply to perform changes.")

    def cleanup_empty_legacy_dirs(self) -> None:
        for d in [
            self.root / "examples" / "targets",
            self.root / "examples" / "test_suites",
            self.root / "examples" / "test_cases",
            self.root / "examples" / "dynamic_templates",
            self.root / "examples" / "test_templates",
        ]:
            if d.exists() and d.is_dir() and not any(d.iterdir()):
                if self.apply:
                    d.rmdir()
                print(f"[rmdir-empty] {self.rel(d)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and professionalize TrustInspect repository layout.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this flag, performs dry-run.")
    parser.add_argument("--keep-legacy-examples", action="store_true", help="Keep empty legacy example directories.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    Cleaner(root=root, apply=args.apply, keep_legacy_examples=args.keep_legacy_examples).execute()


if __name__ == "__main__":
    main()
