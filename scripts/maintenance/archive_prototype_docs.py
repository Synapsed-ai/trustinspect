#!/usr/bin/env python3
"""Archive prototype patch readmes and patch scripts from the repository root."""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

PATTERNS = [
    "README_*_PATCH.md",
    "README_*BUGFIX*.md",
    "README_*FIX*.md",
    "patch_*.py",
    "*_patch",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive prototype patch files from the repo root.")
    parser.add_argument("--apply", action="store_true", help="Actually move files. Default is dry-run.")
    args = parser.parse_args()

    root = Path.cwd()
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    archive = root / "_archive" / "prototype-patches" / stamp
    candidates = []
    for pattern in PATTERNS:
        candidates.extend(root.glob(pattern))
    candidates = sorted({p for p in candidates if p.name != "_archive" and p.exists()})

    if not candidates:
        print("[+] No prototype patch docs/scripts found in repository root.")
        return 0

    print(("[apply]" if args.apply else "[dry-run]"), "archive root:", archive)
    for path in candidates:
        dest = archive / path.name
        print(("[apply]" if args.apply else "[dry-run]"), "move", path, "->", dest)
        if args.apply:
            archive.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(path), str(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
