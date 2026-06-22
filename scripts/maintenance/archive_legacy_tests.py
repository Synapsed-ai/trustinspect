#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

LEGACY_TESTS = [
    "tests/test_analyzer_engine.py",
    "tests/test_demo_target_quality.py",
    "tests/test_reporting_timestamps.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive legacy patch-era tests that are no longer compatible with the public v0.3 test suite.")
    parser.add_argument("--apply", action="store_true", help="Actually move files. Without this flag, only prints the planned actions.")
    parser.add_argument("--archive-dir", default=None, help="Override archive destination.")
    args = parser.parse_args()

    root = Path.cwd()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive = Path(args.archive_dir) if args.archive_dir else root / "_archive" / "legacy-tests" / ts

    found = []
    for rel in LEGACY_TESTS:
        src = root / rel
        if src.exists():
            found.append((rel, src, archive / rel))

    if not found:
        print("[+] No legacy patch-era tests found. Nothing to archive.")
        return 0

    print("[+] Legacy patch-era tests detected:")
    for rel, src, dst in found:
        print(f"    {rel} -> {dst.relative_to(root) if dst.is_relative_to(root) else dst}")

    if not args.apply:
        print("\nDry run only. Re-run with --apply to archive these files.")
        return 0

    for rel, src, dst in found:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"[+] Archived {rel}")

    print(f"[+] Archived legacy tests under: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
